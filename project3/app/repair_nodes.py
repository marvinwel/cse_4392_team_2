"""Person 4 (Sarthak): bounded repair and missed-branch test generation.

Every proposed change (production code or tests) waits for the human review in
review_tests before it is written or run. An unusable model reply is retried with
the validation error until the per-phase cap is used up. Each step is recorded in
state["repair_log"] (see repair_log_entry) so the change log and UI can show it.

The existing Bedrock model is injected by main.py.  No additional agent, model,
package, or Maven runner is created here.  Both nodes write LangGraph state
updates; Joseph's run_tests/check_coverage remain the execution/evidence tools.
"""
from __future__ import annotations

import difflib
import json
import os
import re
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

MAX_REPAIR_ATTEMPTS = 3         # per phase; never unlimited LLM calls
MAX_COVERAGE_ROUNDS = 3         # per phase
SOURCE_DIR = PurePosixPath("src/main/java/cse4392")
_TEST_METHOD = re.compile(r"@Test\s+(?:public\s+)?void\s+(\w+)\s*\(")
_ASSERT = re.compile(r"\bassert[A-Z]\w*\s*\(")

REPAIR_PROMPT = """You are repairing a Java/JUnit failure, not redesigning the tests.
Use the actual failure report below. Return ONLY a JSON object:
{{"target":"code" or "test", "path":"SeasonSwitch.java or another existing .java source filename",
  "new_content":"complete replacement file content", "reason":"specific evidence-based reason"}}
For target=code, path MUST name one of the listed existing Java production files.
For target=test, path MUST be the existing approved JUnit test class filename.
Fix only the observed failure; preserve Java package, public class/method API,
all required behavior and all existing test scenarios. NEVER remove or weaken a
passing assertion to hide a code defect. Every code and test change requires human approval.
No shell commands, file deletion, or extra files. Do not alter the original fixture.

Phase: {phase}
Existing production files (path -> entire content):
{sources}
Approved tests (complete Java file):
{tests}
Surefire/Maven failure evidence:
{report}
Previous repair attempts for this phase: {attempts}
Human reviewer feedback on a prior proposed repair: {feedback}
Why your previous proposal was rejected by validation (fix this): {error}
"""

GAP_PROMPT = """You are writing JUnit 5 test METHODS for specifically measured JaCoCo
uncovered branches. Do NOT fabricate a branch or change any existing test.
Return ONLY a JSON object with this form:
{{"tests":[{{"id":"COV-01", "technique":"COVERAGE",
  "description":"what missing branch this reaches",
  "source_file":"SeasonSwitch.java", "class":"SeasonSwitch",
  "line":42, "method":"@Test\\nvoid newUniqueTest() {{ ... assertEquals(...); }}"}}]}}
Each test must match one actual missed source file, class and line below; use
exactly one full @Test method declaration with a new unique name and assertions.
Use the existing suite fixture, imports, package and style; do not repeat the
Java class wrapper or add imports. Avoid assumptions about expected results:
trace the Java behavior first. Preserve all existing tests and assertions.
A missed line inside an inner class (for example Room) is reached through the
fixture's fields, e.g. ss.room.actionPerformed(null).
NEVER call SeasonSwitch.main(...) directly: System.exit would stop the test run and
some paths never return. For any missed line in main(), use the ExitTrap helper that
is already in the test package (declare the method `throws Exception`):
  ExitTrap.Result r = ExitTrap.runMain("off");        // waits up to 3 s for exit
  assertTrue(r.exitedByItself); assertEquals(0, r.exitCode);
  ExitTrap.Result r = ExitTrap.runMain(1500, "cool"); // paths that keep running
  assertFalse(r.exitedByItself); assertTrue(r.output.contains("..."));
r.output holds everything main() printed.

Phase: {phase}
Production Java source files:
{sources}
Approved JUnit suite:
{tests}
JaCoCo missed-branch evidence (only these are eligible):
{gaps}
Human reviewer feedback on prior gap-test proposal: {feedback}
Why your previous proposal was rejected by validation (fix this): {error}
"""


def _model_json(model: Any, prompt: str) -> dict:
    try:
        response = model.invoke(prompt)
    except Exception as exc:
        raise ValueError(f"Model request failed ({type(exc).__name__}): {exc}") from exc
    content = getattr(response, "content", response)
    if isinstance(content, list):
        content = "".join(b["text"] for b in content
                          if isinstance(b, dict) and isinstance(b.get("text"), str))
    if not isinstance(content, str):
        raise ValueError("Model returned no text")
    text = content.strip()
    # Try the whole reply first. A fence search alone is wrong when the JSON
    # itself holds a ```java block inside a string: the search would grab that
    # inner block instead of the object. Fenced blocks are only a fallback.
    candidates = [text] + [m.group(1) for m in
                           re.finditer(r"```(?:json)?[ \t]*\n(.*?)\n?```", text, re.I | re.S)]
    # strict=False accepts raw newlines inside strings, which models often put in
    # multi-line Java code. raw_decode also skips any prose before or after the object.
    decoder = json.JSONDecoder(strict=False)
    first_error = None
    result = None
    for candidate in candidates:
        start = candidate.find("{")
        if start < 0:
            continue
        try:
            result, _ = decoder.raw_decode(candidate, start)
            break
        except json.JSONDecodeError as exc:
            first_error = first_error or exc
    if result is None:
        exc = first_error or json.JSONDecodeError("no JSON object found", text, 0)
        # The detail goes back to the model on the retry and into the change log.
        raise ValueError(f"Model returned invalid JSON ({exc.msg}, line {exc.lineno} "
                         f"column {exc.colno}). Reply began: {text[:160]!r}")
    if not isinstance(result, dict):
        raise ValueError("Expected a JSON object")
    return result


def _phase(state: dict) -> str:
    phase = state.get("phase", "original")
    if phase not in ("original", "refactored"):
        raise ValueError(f"Invalid project phase: {phase!r}")
    return phase


def _counts(state: dict, key: str) -> dict[str, int]:
    values = state.get(key) or {}
    if not isinstance(values, dict):
        raise ValueError(f"{key} must be a dictionary")
    return dict(values)


def _entry(phase: str, action: str, **details: Any) -> dict:
    return {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "phase": phase,
        "node": "repair_agent" if action.startswith("repair") else "generate_gap_tests",
        "action": action,
        **details,
    }


def repair_log_entry(kind: str, phase: str, outcome: str, **details: Any) -> dict:
    """One row of the repair list shown in the change log and the terminal UI.

    kind:    "repair" (failed test run) or "gap" (missed branches)
    outcome: "proposed", "ai_error", "human_rejected", "approved", "applied",
             "rerun_passed", "rerun_failed", "exhausted"
    """
    return {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "kind": kind, "phase": phase, "outcome": outcome, **details}


def _failing_tests(report: Any) -> list[str]:
    if not isinstance(report, dict):
        return []
    names = [str(f.get("test")) for f in report.get("failures") or [] if isinstance(f, dict)]
    if not names and (report.get("build") or {}).get("compile_error"):
        names = ["(compile error)"]
    return names


def _diff(path: str, before: str, after: str) -> str:
    return "\n".join(difflib.unified_diff(
        before.splitlines(), after.splitlines(),
        fromfile=f"{path} (before)", tofile=f"{path} (after)", lineterm="",
    ))


def _atomic_write(path: Path, new: str) -> None:
    """Replace a working Java source atomically; never leave a half-written file."""
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(new)
        os.chmod(temporary, stat.S_IMODE(path.stat().st_mode))
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _source_files(root: Path, phase: str) -> tuple[Path, dict[str, str]]:
    """Read the CURRENT working-phase copy; never patch app/SeasonSwitch.java."""
    project = (root / f"java-{phase}").resolve()
    if not project.is_relative_to(root) or not (project / "pom.xml").is_file():
        raise ValueError(f"Missing or unsafe java-{phase} Maven project")
    folder = project / Path(*SOURCE_DIR.parts)
    if not folder.resolve().is_relative_to(project):
        raise ValueError("Java source directory escapes the project")
    files: dict[str, str] = {}
    for path in sorted(folder.glob("*.java")):
        if not path.resolve().is_relative_to(folder.resolve()):
            raise ValueError(f"Unsafe source path: {path}")
        files[path.name] = path.read_text(encoding="utf-8")
    if not files:
        raise ValueError(f"No Java source files in {folder}")
    return folder, files


def _source_name(value: Any, files: dict[str, str]) -> str:
    if not isinstance(value, str):
        raise ValueError("Code patch must name an existing Java source file")
    # Full canonical src/main/java/cse4392/Foo.java is also accepted.
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("Unsafe source file path")
    if len(path.parts) == 1:
        name = path.name
    elif path.parts[:-1] == SOURCE_DIR.parts:
        name = path.name
    else:
        raise ValueError("Source patch is outside src/main/java/cse4392")
    if name not in files or not name.endswith(".java"):
        raise ValueError(f"Code patch references unknown source file: {name}")
    return name


def _validate_java_source(name: str, old: str, new: str) -> None:
    if not re.search(r"(?m)^\s*package\s+cse4392\s*;", new):
        raise ValueError("Java patch must retain package cse4392")
    if not re.search(rf"\b(?:class|interface|enum)\s+{re.escape(Path(name).stem)}\b", new):
        raise ValueError("Java patch must retain its class/interface name")
    public_method = re.compile(
        r"\bpublic\s+(?:(?:static|final|synchronized)\s+)*"
        r"[\w<>\[\],?]+\s+(\w+)\s*\(([^)]*)\)"
    )
    signatures = lambda code: {tuple(re.sub(r"\s+", " ", part).strip() for part in match)
                               for match in public_method.findall(code)}
    if not signatures(old).issubset(signatures(new)):
        raise ValueError("Java patch removed or changed an existing public method signature")


def _validate_test_replacement(old: str, new: str) -> None:
    if not re.search(r"(?m)^\s*package\s+cse4392\s*;", new):
        raise ValueError("Test patch must retain package cse4392")
    old_cls = re.search(r"\bclass\s+(\w+)", old)
    new_cls = re.search(r"\bclass\s+(\w+)", new)
    if not old_cls or not new_cls or old_cls.group(1) != new_cls.group(1):
        raise ValueError("Test patch must retain the approved test class")
    previous = set(_TEST_METHOD.findall(old))
    if not previous or not previous.issubset(set(_TEST_METHOD.findall(new))):
        raise ValueError("Test patch removed an approved @Test method")
    if len(_ASSERT.findall(new)) < len(_ASSERT.findall(old)):
        raise ValueError("Test patch removed an assertion")


def _result_error(phase: str, action: str, message: str, retry: bool = False,
                  **fields: Any) -> dict:
    """retry=True: the model's reply was unusable but attempts remain, so the
    router sends the node back to itself with the error as feedback."""
    return {
        "workflow_status": action.replace("_blocked", "_retry") if retry else action,
        "repair_action" if action.startswith("repair") else "gap_action":
            "retry" if retry else "escalate",
        "repair_error" if action.startswith("repair") else "gap_error": message,
        "change_log": [_entry(phase, action, reason=message)],
        **fields,
    }


def build_repair_nodes(model: Any, repo_root: str | Path):
    """Return the two LangGraph nodes, backed by the shared existing LLM."""
    root = Path(repo_root).resolve()

    def repair_agent(state: dict) -> dict:
        phase = _phase(state)
        attempts = _counts(state, "repair_attempts_by_phase")
        used = attempts.get(phase, 0)
        if used >= MAX_REPAIR_ATTEMPTS:
            return {**_result_error(phase, "repair_exhausted", "Maximum repair attempts reached"),
                    "repair_log": [repair_log_entry("repair", phase, "exhausted", attempt=used,
                                                    tests=_failing_tests(state.get("test_report")))]}
        attempts[phase] = used + 1
        model_called = False
        try:
            folder, files = _source_files(root, phase)
            tests = state.get("merged_tests")
            report = state.get("test_report")
            if not isinstance(tests, str) or not tests.strip():
                raise ValueError("No approved merged_tests available for repair")
            if not isinstance(report, dict) or report.get("all_passed") is not False:
                raise ValueError("No failing test report available for repair")
            if report.get("phase") != phase:
                raise ValueError("Failure report belongs to a different phase")
            model_called = True
            proposal = _model_json(model, REPAIR_PROMPT.format(
                phase=phase, sources=json.dumps(files, indent=2), tests=tests,
                report=json.dumps(report, indent=2, default=str), attempts=used,
                feedback=state.get("human_feedback", ""),
                error=state.get("repair_error", ""),
            ))
            target = proposal.get("target")
            new = proposal.get("new_content")
            reason = proposal.get("reason")
            if target not in ("code", "test") or not isinstance(new, str) or not new.strip():
                raise ValueError("Repair proposal needs target=code|test and complete new_content")
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError("Repair proposal must explain the observed defect")
            if target == "code":
                name = _source_name(proposal.get("path"), files)
                old = files[name]
                _validate_java_source(name, old, new)
                path = folder / name
            else:
                expected_name = re.search(r"\bclass\s+(\w+)", tests)
                if not expected_name:
                    raise ValueError("Approved test class cannot be identified")
                name = f"{expected_name.group(1)}.java"
                if proposal.get("path") not in (name, f"src/test/java/cse4392/{name}"):
                    raise ValueError("Test patch must target the approved JUnit suite")
                old = tests
                _validate_test_replacement(old, new)
            if old == new:
                raise ValueError("Repair proposal made no changes")
            change = _entry(phase, "repair_proposed", target=target, path=name,
                            reason=reason.strip(), diff=_diff(name, old, new), attempt=used + 1)
            update = {
                "repair_attempts_by_phase": attempts,
                "repair_error": "",
                "change_log": [change],
                "repair_log": [repair_log_entry(
                    "repair", phase, "proposed", attempt=used + 1,
                    tests=_failing_tests(report), diagnosis=reason.strip(),
                    target=target, path=name, diff=change["diff"])],
            }
            if target == "code":
                # No write yet. A person approves the code diff in review_tests
                # first; apply_code_repair writes it only after that approval.
                update.update({
                    "repair_action": "review", "workflow_status": "repair_pending_review",
                    "human_approved": False, "review_context": "repair",
                    "pre_review_tests": tests,
                    "pending_code_repair": {"phase": phase, "path": name,
                                            "old": old, "new": new},
                })
            else:
                # No write. Ryan's existing review_tests interrupt must approve
                # the changed suite before run_tests is allowed to write/execute it.
                update.update({
                    "repair_action": "review", "workflow_status": "repair_pending_review",
                    "merged_tests": new, "human_approved": False,
                    "review_context": "repair", "pre_review_tests": old,
                })
            return update
        except (ValueError, OSError, TypeError) as exc:
            result = _result_error(phase, "repair_blocked", str(exc),
                                   retry=model_called and attempts[phase] < MAX_REPAIR_ATTEMPTS,
                                   repair_attempts_by_phase=attempts)
            if model_called:
                result["repair_log"] = [repair_log_entry(
                    "repair", phase, "ai_error", attempt=used + 1, error=str(exc),
                    tests=_failing_tests(state.get("test_report")))]
            return result

    def generate_gap_tests(state: dict) -> dict:
        phase = _phase(state)
        rounds = _counts(state, "coverage_rounds_by_phase")
        used = rounds.get(phase, 0)
        if used >= MAX_COVERAGE_ROUNDS:
            return {**_result_error(phase, "gap_exhausted", "Maximum coverage rounds reached"),
                    "repair_log": [repair_log_entry("gap", phase, "exhausted", attempt=used)]}
        rounds[phase] = used + 1
        model_called = False
        try:
            _, files = _source_files(root, phase)
            cov = state.get("coverage")
            suite = state.get("merged_tests")
            if not isinstance(cov, dict) or cov.get("phase") != phase or not cov.get("report_found"):
                raise ValueError("A JaCoCo report for the current phase is required")
            branch = cov.get("branch") or {}
            if not isinstance(branch.get("missed"), int) or branch["missed"] <= 0:
                raise ValueError("No measured uncovered branches in JaCoCo")
            gaps = cov.get("missed_branches")
            if not isinstance(gaps, list) or not gaps:
                raise ValueError("JaCoCo did not identify any missed source lines")
            if not isinstance(suite, str) or not suite.strip() or not re.search(r"\}\s*$", suite):
                raise ValueError("Missing complete approved JUnit suite")
            model_called = True
            response = _model_json(model, GAP_PROMPT.format(
                phase=phase, sources=json.dumps(files, indent=2), tests=suite,
                gaps=json.dumps(gaps, indent=2),
                feedback=state.get("human_feedback", ""),
                error=state.get("gap_error", ""),
            ))
            additions = response.get("tests")
            if not isinstance(additions, list) or not additions:
                raise ValueError("Coverage proposal contains no new tests")
            allowed = {(g["source_file"], g["class"], g["line"]) for g in gaps}
            names = set(_TEST_METHOD.findall(suite))
            methods: list[str] = []
            evidence: list[dict] = []
            for item in additions:
                if not isinstance(item, dict) or item.get("technique") != "COVERAGE":
                    raise ValueError("Every gap test must be a COVERAGE record")
                line = item.get("line")
                if isinstance(line, str) and line.strip().isdigit():
                    line = int(line)   # models often send "42" instead of 42
                target = (item.get("source_file"), item.get("class"), line)
                method = item.get("method")
                if target not in allowed or not isinstance(method, str):
                    raise ValueError("Gap test does not match a measured JaCoCo line")
                found = _TEST_METHOD.findall(method)
                if len(found) != 1 or len(re.findall(r"@Test\b", method)) != 1:
                    raise ValueError("Each gap test must contain exactly one @Test method")
                if found[0] in names or not _ASSERT.search(method):
                    raise ValueError("Duplicate test name or missing JUnit assertion")
                if re.search(r"\b(?:package|import|class|interface)\b", method):
                    raise ValueError("Gap test must contain only a method, not a class/import")
                if not isinstance(item.get("description"), str) or not item["description"].strip():
                    raise ValueError("Gap test requires a description")
                if not isinstance(item.get("id"), str) or not item["id"].startswith("COV-"):
                    raise ValueError("Gap test id must begin with COV-")
                names.add(found[0])
                methods.append(method.strip())
                evidence.append({"id": item["id"], "technique": "COVERAGE",
                                 "description": item["description"], "source_file": target[0],
                                 "class": target[1], "line": target[2], "test_method": found[0]})
            # Insert only before the existing test class's final brace; do not
            # replace or weaken its previous tests or their expected results.
            position = re.search(r"\}\s*$", suite).start()
            revised = suite[:position].rstrip() + "\n\n    " + "\n\n    ".join(
                m.replace("\n", "\n    ") for m in methods
            ) + "\n" + suite[position:]
            change = _entry(phase, "coverage_tests_proposed", target="test",
                            path="approved merged JUnit suite",
                            reason=f"Target {len(additions)} measured missing branch line(s)",
                            diff=_diff("approved JUnit suite", suite, revised),
                            tests=evidence, round=used + 1)
            return {
                "repair_log": [repair_log_entry(
                    "gap", phase, "proposed", attempt=used + 1,
                    tests=[e["test_method"] for e in evidence],
                    diagnosis="; ".join(f"{e['class']} line {e['line']}: {e['description']}"
                                        for e in evidence),
                    target="test", path="approved merged JUnit suite", diff=change["diff"])],
                "coverage_rounds_by_phase": rounds, "gap_action": "review",
                "gap_error": "", "workflow_status": "gap_tests_pending_review",
                "gap_tests": list(state.get("gap_tests") or []) + evidence,
                "merged_tests": revised, "human_approved": False,
                "review_context": "gap", "pre_review_tests": suite,
                "change_log": [change],
            }
        except (ValueError, KeyError, OSError, TypeError) as exc:
            result = _result_error(phase, "gap_blocked", str(exc),
                                   retry=model_called and rounds[phase] < MAX_COVERAGE_ROUNDS,
                                   coverage_rounds_by_phase=rounds)
            if model_called:
                result["repair_log"] = [repair_log_entry("gap", phase, "ai_error",
                                                         attempt=used + 1, error=str(exc))]
            return result

    return repair_agent, generate_gap_tests


def build_apply_code_repair(repo_root: str | Path):
    """Return the node that writes a code repair AFTER a person approved its diff."""
    root = Path(repo_root).resolve()

    def apply_code_repair(state: dict) -> dict:
        pending = state.get("pending_code_repair") or {}
        phase = _phase(state)
        try:
            if pending.get("phase") != phase:
                raise ValueError("Approved code repair belongs to a different phase")
            folder, files = _source_files(root, phase)
            name = _source_name(pending.get("path"), files)
            if files[name] != pending.get("old"):
                raise ValueError(f"{name} changed after the repair was proposed")
            new = pending.get("new")
            _validate_java_source(name, files[name], new)
            _atomic_write(folder / name, new)
        except (ValueError, OSError, TypeError) as exc:
            return {**_result_error(phase, "repair_blocked", str(exc)),
                    "pending_code_repair": None}
        update = {
            "pending_code_repair": None, "repair_action": "run",
            "workflow_status": "code_repaired",
            "change_log": [_entry(phase, "repair_applied", target="code", path=name,
                                  reason="Human approved the proposed code diff")],
            "repair_log": [repair_log_entry("repair", phase, "applied", target="code", path=name)],
        }
        if phase == "original" and name == "SeasonSwitch.java":
            update["source_code"] = new
        if phase == "refactored":
            refactored = dict(state.get("refactored_files") or {})
            keys = [k for k in refactored if PurePosixPath(k).name == name]
            for key in keys or [(SOURCE_DIR / name).as_posix()]:
                refactored[key] = new
            update["refactored_files"] = refactored
        return update

    return apply_code_repair


def route_after_repair(state: dict) -> str:
    return {"run": "run", "review": "review", "retry": "retry"}.get(
        state.get("repair_action"), "escalate")


def route_after_apply(state: dict) -> str:
    return "run" if state.get("repair_action") == "run" else "escalate"


def route_after_gap(state: dict) -> str:
    return {"review": "review", "retry": "retry"}.get(state.get("gap_action"), "escalate")
