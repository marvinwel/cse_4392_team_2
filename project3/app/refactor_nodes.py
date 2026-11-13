"""Person 5 LangGraph nodes for State-pattern refactoring and human review.

The nodes are created with :func:`build_refactor_nodes` so they can be tested
without Bedrock or LangGraph credentials. ``interrupt_fn`` should be
``langgraph.types.interrupt`` in the application and can be mocked in unit
tests.
"""
from __future__ import annotations

import difflib
import json
import re
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Callable


MAX_REFACTOR_REVISIONS = 3
MAIN_SOURCE_DIR = PurePosixPath("src/main/java/cse4392")
TEST_SOURCE_DIR = PurePosixPath("src/test/java/cse4392")

REFACTOR_PROMPT = """You are refactoring a Java class for a course assignment.

Refactor the supplied class to use the State design pattern. Return a JSON
object only, with exactly these keys:
{{
  "files": {{"relative/path/under/src/main/java/cse4392": "complete Java source"}},
  "adapted_tests": "complete JUnit 5 test source",
  "explanation": "brief design and adaptation notes"
}}

Requirements:
- Keep the main class name, package, public method names, parameter lists, and
  observable behavior unchanged.
- Use a State interface and concrete states for OFF, COOL, and HEAT. Put mode
  behavior and transitions in those states; do not retain a switch ladder for
  operating modes.
- Preserve all thresholds, strict comparison behavior, device effects, timer
  effects, messages, and room-temperature behavior.
- Adapt the approved JUnit suite only as required by the new implementation
  details. Keep every test method and all expected outcomes/assertions; do not
  weaken, remove, or silently change an oracle. Keep package cse4392 and JUnit 5.
- Include every Java source needed to compile the refactored project. The map
  keys must be file names or paths below src/main/java/cse4392.
- Return complete source files, not diffs. Do not include markdown fences.

Original Java source:
{source_code}

Approved JUnit suite (preserve scenarios and assertions):
{approved_tests}

Previous generated files:
{previous_files}

Previous adapted tests:
{previous_tests}

Human review feedback to address:
{feedback}
"""


def _response_text(response: Any) -> str:
    """Normalize LangChain string and content-block responses."""
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and isinstance(block.get("text", ""), str)
        ).strip()
    raise ValueError("Refactor model returned no textual content")


def _parse_refactor_result(raw: str) -> dict[str, Any]:
    text = raw.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("Refactor model response was not a JSON object")
        try:
            result = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Refactor model returned invalid JSON: {exc}") from exc
    if not isinstance(result, dict):
        raise ValueError("Refactor result must be a JSON object")
    return result


def _test_method_names(java: str) -> set[str]:
    return set(re.findall(
        r"@Test\s+(?:(?:@[\w.]+(?:\([^)]*\))?)\s*)*(?:public\s+)?void\s+(\w+)\s*\(",
        java,
    ))


def _assertion_count(java: str) -> int:
    return len(re.findall(
        r"\bassert(?:Equals|NotEquals|True|False|Null|NotNull|Same|NotSame|Throws|DoesNotThrow|ArrayEquals|IterableEquals|LinesMatch|All)\s*\(",
        java,
    ))


def _safe_source_path(path_text: str) -> PurePosixPath:
    normalized = path_text.replace("\\", "/").strip()
    path = PurePosixPath(normalized)
    if path.is_absolute() or not path.parts or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"Unsafe refactored source path: {path_text!r}")
    if path.parts[0] == "src":
        if path.parts[:4] != ("src", "main", "java", "cse4392"):
            raise ValueError(f"Source must be under {MAIN_SOURCE_DIR}: {path_text!r}")
        relative = PurePosixPath(*path.parts[4:])
    else:
        relative = path
    if not relative.parts or relative.suffix != ".java":
        raise ValueError(f"Expected a Java filename under {MAIN_SOURCE_DIR}: {path_text!r}")
    return MAIN_SOURCE_DIR / relative


def _validate_and_normalize_result(
    result: dict[str, Any],
    approved_tests: str,
    class_name: str,
) -> tuple[dict[str, str], str, str]:
    files = result.get("files")
    adapted_tests = result.get("adapted_tests")
    explanation = result.get("explanation", "")
    if not isinstance(files, dict) or not files:
        raise ValueError("Refactor result must contain a non-empty files map")
    if not isinstance(adapted_tests, str) or not adapted_tests.strip():
        raise ValueError("Refactor result must contain adapted JUnit source")
    if not isinstance(explanation, str):
        raise ValueError("Refactor explanation must be text")

    normalized_files: dict[str, str] = {}
    for path_text, code in files.items():
        if not isinstance(path_text, str) or not isinstance(code, str) or not code.strip():
            raise ValueError("Every refactored file needs a path and non-empty Java source")
        normalized_files[_safe_source_path(path_text).as_posix()] = code.strip() + "\n"

    expected_main = f"public class {class_name}"
    main_file = next((text for path, text in normalized_files.items()
                      if PurePosixPath(path).name == f"{class_name}.java"), None)
    if main_file is None or expected_main not in main_file:
        raise ValueError(f"Refactor files must include public class {class_name}")
    if not re.search(r"(?m)^\s*package\s+cse4392\s*;", main_file):
        raise ValueError("Refactored main class must remain in package cse4392")

    original_methods = _test_method_names(approved_tests)
    adapted_methods = _test_method_names(adapted_tests)
    if not original_methods:
        raise ValueError("Approved JUnit suite contains no recognizable @Test methods")
    missing_methods = sorted(original_methods - adapted_methods)
    if missing_methods:
        raise ValueError("Adapted suite removed approved test methods: " + ", ".join(missing_methods))
    old_assertions, new_assertions = _assertion_count(approved_tests), _assertion_count(adapted_tests)
    if new_assertions < old_assertions:
        raise ValueError(
            f"Adapted suite has fewer assertions ({new_assertions}) than approved suite ({old_assertions})"
        )
    if not re.search(r"(?m)^\s*package\s+cse4392\s*;", adapted_tests):
        raise ValueError("Adapted JUnit suite must remain in package cse4392")
    original_class = re.search(r"\bclass\s+(\w+)", approved_tests)
    adapted_class = re.search(r"\bclass\s+(\w+)", adapted_tests)
    if not adapted_class:
        raise ValueError("Could not find a Java test class declaration in adapted_tests")
    if not original_class or adapted_class.group(1) != original_class.group(1):
        raise ValueError("Adapted JUnit suite must keep the approved test class name")
    return normalized_files, adapted_tests.strip() + "\n", explanation.strip()


def _write_project_files(
    project_dir: Path,
    source_files: dict[str, str],
    test_file_name: str,
    adapted_tests: str,
) -> None:
    targets = [(project_dir / Path(*PurePosixPath(path).parts), code)
               for path, code in source_files.items()]
    test_path = PurePosixPath(test_file_name)
    if test_path.name != test_file_name or test_path.suffix != ".java":
        raise ValueError(f"Unsafe test filename: {test_file_name!r}")
    targets.append((project_dir / Path(*TEST_SOURCE_DIR.parts) / test_file_name, adapted_tests))

    root = project_dir.resolve()
    for target, _ in targets:
        if not target.resolve().is_relative_to(root):
            raise ValueError(f"Generated file escapes Java project directory: {target}")
    for target, content in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def _test_filename(approved_tests: str, class_name: str, state: dict[str, Any]) -> str:
    configured = state.get("test_filename")
    if configured:
        return Path(str(configured)).name
    class_match = re.search(r"\bclass\s+(\w+)", approved_tests)
    test_class = class_match.group(1) if class_match else f"{class_name}MergedTest"
    return f"{test_class}.java"


def _log_entry(state: dict[str, Any], action: str, reason: str, before: str, after: str) -> dict[str, Any]:
    diff = difflib.unified_diff(
        before.splitlines(), after.splitlines(),
        fromfile="before", tofile="after", lineterm="",
    )
    return {
        "time": datetime.now().isoformat(timespec="seconds"),
        "phase": "refactored",
        "node": "refactor_agent",
        "action": action,
        "reason": reason,
        "diff": "\n".join(diff),
    }


def build_refactor_nodes(
    model: Any,
    repo_root: str | Path,
    interrupt_fn: Callable[[dict[str, Any]], Any],
    *,
    max_revisions: int = MAX_REFACTOR_REVISIONS,
) -> tuple[Callable[[dict[str, Any]], dict[str, Any]], Callable[[dict[str, Any]], dict[str, Any]]]:
    """Create ``refactor_agent`` and ``review_refactor`` for graph registration."""
    root = Path(repo_root).resolve()

    def refactor_agent(state: dict[str, Any]) -> dict[str, Any]:
        source_code = state.get("source_code")
        approved_tests = state.get("merged_tests")
        if not isinstance(source_code, str) or not source_code.strip():
            raise ValueError("refactor_agent requires source_code")
        if not isinstance(approved_tests, str) or not approved_tests.strip():
            raise ValueError("refactor_agent requires the approved merged_tests suite")

        class_name = state.get("class_name", "SeasonSwitch")
        response = model.invoke(REFACTOR_PROMPT.format(
            source_code=source_code,
            approved_tests=approved_tests,
            previous_files=json.dumps(state.get("refactored_files", {}), indent=2),
            previous_tests=state.get("refactored_tests", ""),
            feedback=state.get("refactor_feedback", ""),
        ))
        parsed = _parse_refactor_result(_response_text(response))
        files, adapted_tests, explanation = _validate_and_normalize_result(
            parsed, approved_tests, class_name,
        )
        project_dir = Path(state.get("refactored_project_dir", root / "java-refactored")).resolve()
        if not project_dir.is_relative_to(root):
            raise ValueError("refactored_project_dir must remain inside the repository")
        filename = _test_filename(approved_tests, class_name, state)
        _write_project_files(project_dir, files, filename, adapted_tests)

        before = state.get("refactored_tests", "")
        revision = state.get("refactor_revision_count", 0)
        entry = _log_entry(
            state,
            "revised_refactor" if revision else "generated_refactor",
            state.get("refactor_feedback") or "initial generation",
            before,
            adapted_tests,
        )
        old_files = state.get("refactored_files", {})
        source_diffs = []
        for path, code in files.items():
            previous = old_files.get(path, "") if isinstance(old_files, dict) else ""
            diff = difflib.unified_diff(
                previous.splitlines(), code.splitlines(),
                fromfile=f"{path} (before)", tofile=f"{path} (after)", lineterm="",
            )
            rendered = "\n".join(diff)
            if rendered:
                source_diffs.append(rendered)
        if source_diffs:
            entry["source_diff"] = "\n".join(source_diffs)
        return {
            "phase": "refactored",
            "refactored_files": files,
            "refactored_tests": adapted_tests,
            "merged_tests": adapted_tests,
            "test_class": Path(filename).stem,
            "refactor_explanation": explanation,
            "refactor_status": "awaiting_review",
            "workflow_status": "awaiting_refactor_review",
            "change_log": [entry],
        }

    def review_refactor(state: dict[str, Any]) -> dict[str, Any]:
        files = state.get("refactored_files") or {}
        tests = state.get("refactored_tests") or state.get("merged_tests") or ""
        if not files or not tests:
            raise ValueError("review_refactor requires generated source files and adapted tests")

        review_payload = {
            "node": "review_refactor",
            "class_name": state.get("class_name", "SeasonSwitch"),
            "files": files,
            "adapted_tests": tests,
            "explanation": state.get("refactor_explanation", ""),
            "review_checklist": [
                "SeasonSwitch public API and package are preserved",
                "OFF, COOL, and HEAT behavior is delegated to concrete State objects",
                "Device, timer, temperature-threshold, and room-temperature behavior is preserved",
                "Every approved test method and at least the original assertion count remain",
                "Review code and tests before approving execution",
            ],
            "prior_feedback": state.get("refactor_feedback", ""),
            "review_number": state.get("refactor_review_count", 0) + 1,
        }
        decision = interrupt_fn(review_payload)
        if not isinstance(decision, dict) or not isinstance(decision.get("approved"), bool):
            raise ValueError("Resume review_refactor with {'approved': bool, 'feedback': str}")

        count = review_payload["review_number"]
        revisions = state.get("refactor_revision_count", 0)
        approved = decision["approved"]
        feedback = str(decision.get("feedback", "")).strip()
        status = "refactor_approved" if approved else "refactor_rejected"
        workflow_status = "refactor_approved" if approved else "refactor_revision_requested"
        if not approved:
            revisions += 1
            if revisions >= max_revisions:
                status = "refactor_review_exhausted"
                workflow_status = status
                feedback = feedback or "Maximum refactor review revisions reached; escalate to the team."

        change = {
            "time": datetime.now().isoformat(timespec="seconds"),
            "phase": "refactored",
            "node": "review_refactor",
            "action": "approved" if approved else "rejected",
            "review_number": count,
            "feedback": feedback,
        }
        return {
            "refactor_approved": approved,
            "refactor_feedback": "" if approved else feedback,
            "refactor_review_count": count,
            "refactor_revision_count": revisions,
            "refactor_status": status,
            "workflow_status": workflow_status,
            "change_log": [change],
        }

    return refactor_agent, review_refactor
