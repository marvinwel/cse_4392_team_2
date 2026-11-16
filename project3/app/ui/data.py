"""Read what the workflow and Maven already produced. Nothing here is made up:
when a file is missing the caller is told so and shows that, not a placeholder result."""
import difflib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import java_tools  # noqa: E402  (Joseph's Maven / Surefire / JaCoCo helpers, used read-only)

ROOT = java_tools.REPO_ROOT
GENERATED = ROOT / "generated_tests"
ORIGINAL_SOURCE = APP_DIR / "SeasonSwitch.java"
# Every class, nothing excluded. Always shown first on the coverage screens.
FULL_PROGRAM_SCOPE = {"include_classes": None, "exclude_methods": []}
# The scope the workflow and the make targets measure (the team's decision, docs/coverage-scope.md).
CONFIGURED_SCOPE = java_tools.DEFAULT_COVERAGE_SCOPE


def stamp(path):
    """'Nov 13, 5:02 PM' for a file's last change, or '' if it is missing."""
    path = Path(path)
    if not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%b %d, %I:%M %p").replace(" 0", " ")


def read(path):
    path = Path(path)
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


# --------------------------------------------------------------------------- generated tests
def public_methods(java_source, class_name="SeasonSwitch"):
    """Method names of the class under test, in source order: first the methods declared
    directly in the class (without main), then longer-named methods of its inner classes
    (such as actionPerformed), so tests that name them get their own group."""
    outer, inner, depth = [], [], 0
    for line in java_source.splitlines():
        match = re.search(r"(?:public|protected|private)?\s*(?:static\s+)?[\w<>\[\]]+\s+(\w+)\s*\([^;]*\)\s*(?:throws\s+[\w, ]+)?\s*\{", line)
        if match and match.group(1) not in ("main", "if", "for", "while", "switch", "catch", class_name):
            name = match.group(1)
            if depth == 1 and name not in outer:
                outer.append(name)
            elif depth > 1 and len(name) > 4 and name not in inner:
                inner.append(name)
        depth += line.count("{") - line.count("}")
    return outer + [name for name in inner if name not in outer]


def parse_tests(java_tests, methods):
    """Split a JUnit class into its @Test methods.

    Each item: name, kind (EP / BVA / TEST, from the testEP / testBVA name prefix),
    comment (the // lines the generator wrote above it), source (the whole method),
    method (the Java method it exercises, taken from the test name or the calls it makes).
    """
    tests = []
    lines = java_tests.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("@Test"):
            start = i
            comment = []
            j = i - 1
            while j >= 0 and lines[j].strip().startswith(("//", "*", "/*")):
                comment.insert(0, lines[j].strip().lstrip("/* ").rstrip("*/ "))
                j -= 1
            depth, seen_brace, k = 0, False, i
            while k < len(lines):
                depth += lines[k].count("{") - lines[k].count("}")
                seen_brace = seen_brace or "{" in lines[k]
                if seen_brace and depth <= 0:
                    break
                k += 1
            body = lines[start:k + 1]
            match = re.search(r"void\s+(\w+)\s*\(", "\n".join(body))
            name = match.group(1) if match else f"test at line {start + 1}"
            kind = "EP" if name.startswith("testEP") else "BVA" if name.startswith("testBVA") else "TEST"
            tests.append({
                "name": name, "kind": kind, "comment": " ".join(c for c in comment if c),
                "source": "\n".join(lines[j + 1:k + 1]), "line": start + 1,
                "method": _method_under_test(name, "\n".join(body), methods),
            })
            i = k
        i += 1
    return tests


def _method_under_test(name, body, methods):
    lowered = name.lower()
    hits = [(lowered.find(m.lower()), -len(m), m) for m in methods if m.lower() in lowered]
    if hits:
        return sorted(hits)[0][2]
    calls = [c for c in re.findall(r"\.(\w+)\s*\(", body) if c in methods]
    return calls[-1] if calls else "other"


def group_tests(tests, methods):
    """[(java method, [tests])] in the order the methods appear in the source."""
    order = [m for m in methods] + ["other"]
    groups = []
    for method in order:
        members = [t for t in tests if t["method"] == method]
        if members:
            groups.append((method, members))
    return groups


def changed_tests(old_tests, new_tests):
    """Names of tests whose source differs from the previous review round (or are new)."""
    before = {t["name"]: t["source"] for t in old_tests}
    return {t["name"]: ("new" if t["name"] not in before else "revised")
            for t in new_tests if before.get(t["name"]) != t["source"]}


# --------------------------------------------------------------------------- JUnit / JaCoCo reports
def junit_report(phase):
    """Surefire results on disk for a phase, plus where they came from."""
    folder = java_tools.surefire_dir(java_tools.java_project_dir(phase))
    report = java_tools.parse_surefire(folder)
    files = sorted(folder.glob("TEST-*.xml")) if folder.is_dir() else []
    report["source_note"] = f"Surefire report on disk, written {stamp(files[0])}" if files else ""
    report["written"] = files[0].stat().st_mtime if files else 0
    report["phase"] = phase
    return report


def coverage_report(phase, scope=None):
    """Full-program and configured-scope branch coverage, both read from the same JaCoCo XML.

    The full-program figure uses every class with nothing excluded. The configured scope is
    the one the workflow measures. When the two are the same (`same_scope`), the screens
    show one number. Neither changes what Maven measured.
    """
    xml = java_tools.jacoco_xml_path(java_tools.java_project_dir(phase))
    scope = {**FULL_PROGRAM_SCOPE, **(scope or CONFIGURED_SCOPE)}
    full = java_tools.parse_jacoco(xml, FULL_PROGRAM_SCOPE)
    scoped = java_tools.parse_jacoco(xml, scope)
    in_scope = {(m["class"], m["method"]) for m in scoped["missed_branches"]}
    missed = {}
    for m in full["missed_branches"]:
        key = (m["class"], m["method"])
        entry = missed.setdefault(key, {"class": m["class"], "method": m["method"], "missed": 0,
                                        "lines": [], "in_scope": key in in_scope})
        entry["missed"] += m["missed_branches"]
        entry["lines"].append(m["line"])
    return {"found": full["report_found"], "phase": phase, "xml": str(xml), "full": full["branch"],
            "scoped": scoped["branch"], "scope": scope,
            "same_scope": not scope["include_classes"] and not scope["exclude_methods"], "excluded": scoped.get("excluded_methods", []),
            "missed": list(missed.values()), "written": xml.stat().st_mtime if full["report_found"] else 0,
            "source_note": f"JaCoCo report on disk, written {stamp(xml)}" if full["report_found"] else ""}


# --------------------------------------------------------------------------- repair list
REPAIR_OUTCOME = {  # outcome written by the repair / gap agents -> words for the screen
    "proposed": "AI proposed a change", "ai_error": "AI reply could not be used",
    "human_rejected": "Reviewer rejected it", "approved": "Reviewer approved it",
    "applied": "Code fix written", "rerun_passed": "Rerun passed", "rerun_failed": "Rerun still failing",
    "exhausted": "Stopped: attempt limit reached",
}


def repair_rows(kind, phase, live_values=None):
    """Rows of the workflow's repair list for one kind ('repair' or 'gap') and phase.

    Taken from the running workflow when there is one, otherwise from the change log the
    last run saved (generated_tests/change_log_<phase>.json). Returns (rows, where, limits):
    `where` says which of the two it was ('' when neither has a repair list), and `limits`
    holds the attempt counters the workflow recorded.
    """
    source, where = None, ""
    if live_values and (live_values.get("repair_log") or live_values.get("repair_attempts_by_phase")
                        or live_values.get("coverage_rounds_by_phase")):
        source, where = live_values, "this run"
    else:
        for name in ("refactored", "original"):   # the later file holds the whole run
            path = GENERATED / f"change_log_{name}.json"
            try:
                saved = json.loads(read(path) or "null")
            except ValueError:
                saved = None
            if isinstance(saved, dict) and "repair_log" in saved:
                source, where = saved, f"change log saved {stamp(path)}"
                break
    if source is None:
        return [], "", {}
    rows = [row for row in source.get("repair_log") or []
            if isinstance(row, dict) and row.get("kind") == kind and row.get("phase") == phase]
    counters = source.get("repair_attempts_by_phase" if kind == "repair" else "coverage_rounds_by_phase") or {}
    return rows, where, {"used": counters.get(phase, 0)}


def diff_lines(diff_text):
    """A unified diff as (line number in the new file, text, style) rows for the code viewer."""
    lines, number = [], 0
    for line in str(diff_text or "").expandtabs(4).splitlines():
        if line.startswith(("---", "+++")):
            lines.append(("", line, "file"))
        elif line.startswith("@@"):
            found = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", line)
            number = int(found.group(1)) - 1 if found else number
            lines.append(("", line, "hunk"))
        else:
            number += 0 if line.startswith("-") else 1
            lines.append(("" if line.startswith("-") else number, line,
                          "add" if line.startswith("+") else "del" if line.startswith("-") else "plain"))
    return lines


def java_label(class_name, method):
    return f"{class_name.replace('$', '.')}.{method}()"


# --------------------------------------------------------------------------- refactored sources
def refactored_files():
    """{file name: source} for the Java the refactor agent last wrote to java-refactored/."""
    folder = ROOT / "java-refactored" / "src" / "main" / "java" / "cse4392"
    return {p.name: read(p) for p in sorted(folder.glob("*.java"))} if folder.is_dir() else {}


def file_order(names):
    """SeasonSwitch.java first, then State.java, then the concrete states."""
    rank = {"SeasonSwitch.java": 0, "State.java": 1, "OffState.java": 2, "CoolState.java": 3, "HeatState.java": 4}
    return sorted(names, key=lambda n: (rank.get(n, 9), n))


def unified_diff(old, new, old_name, new_name):
    old_lines, new_lines = old.splitlines(), new.splitlines()
    if not old_lines:
        return ([f"--- (new file)", f"+++ {new_name}", f"@@ -0,0 +1,{len(new_lines)} @@"]
                + ["+" + line for line in new_lines])
    return list(difflib.unified_diff(old_lines, new_lines, old_name, new_name, lineterm="", n=10 ** 6))


def method_signatures(java_source):
    """Method headers found in a Java file, for the signature check line."""
    found = re.findall(r"^\s*(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:void|int|boolean|String|State)\s+"
                       r"(\w+)\s*\(([^)]*)\)", java_source, flags=re.M)
    return [f"{name}({params.strip()})" for name, params in found]


# --------------------------------------------------------------------------- cleanup targets
def cleanup_targets(target):
    """Folders `make clean` / `make clean-all` would delete right now: (path, files, bytes)."""
    names = ["java-original/target", "java-refactored/target"]
    if target == "clean-all":
        names.append("junit-merger/target")
    found = []
    for name in names:
        folder = ROOT / name
        if folder.is_dir():
            files = [p for p in folder.rglob("*") if p.is_file()]
            found.append((f"{ROOT.name}/{name}/", len(files), sum(p.stat().st_size for p in files)))
    return found


def human_size(count):
    for unit in ("bytes", "KB", "MB", "GB"):
        if count < 1024 or unit == "GB":
            return f"{count:.0f} {unit}" if unit == "bytes" else f"{count:.1f} {unit}"
        count /= 1024
