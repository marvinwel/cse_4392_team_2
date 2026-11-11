"""
Person 3 (Joseph) - LangGraph nodes + router for execution, coverage and evidence.

Matches the 12-node plan and Marvin's main.py naming:

    06 run_tests            run the approved JUnit suite via Maven for state["phase"]
    08 check_coverage       parse JaCoCo branch coverage for state["phase"]
    12 save_results         archive tests/reports/logs into artifacts/<phase>/
    R2 route_test_results   after run_tests: "passed" -> check_coverage, "failed" -> repair_agent

Wiring (Ryan, in build_graph):

    from testing_nodes import run_tests, check_coverage, save_results, route_test_results
    graph.add_node("run_tests", run_tests)
    graph.add_node("check_coverage", check_coverage)
    graph.add_node("save_results", save_results)
    graph.add_conditional_edges("run_tests", route_test_results,
                                {"passed": "check_coverage", "failed": "repair_agent"})

State keys READ:   phase ("original" | "refactored", default "original"),
                   merged_tests (approved JUnit source, Marvin), coverage_scope (optional),
                   tests (optional structured list), change_log (optional, Sarthak)
State keys WRITTEN: test_report, coverage, saved_artifacts, workflow_status
                   -> add these to AgentState (see STATE_KEYS_TO_ADD below).

One Maven run produces both Surefire and JaCoCo reports, so check_coverage only parses
what run_tests already produced; it never re-runs Maven.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

try:  # works both as `python app/main.py` (app on sys.path) and as package `app.`
    from java_tools import (REPO_ROOT, DEFAULT_COVERAGE_SCOPE, java_project_dir, write_test_file,
                            run_maven, parse_surefire, parse_jacoco, surefire_dir, jacoco_xml_path)
except ImportError:  # pragma: no cover
    from app.java_tools import (REPO_ROOT, DEFAULT_COVERAGE_SCOPE, java_project_dir, write_test_file,
                                run_maven, parse_surefire, parse_jacoco, surefire_dir, jacoco_xml_path)

MAVEN_TIMEOUT_S = 300

# Paste into AgentState (TypedDict, total=False):
STATE_KEYS_TO_ADD = """
    phase: str              # "original" | "refactored"
    test_report: dict       # run_tests output (Joseph)
    coverage: dict          # check_coverage output (Joseph)
    coverage_scope: dict    # optional override of DEFAULT_COVERAGE_SCOPE
    saved_artifacts: dict   # {"original": path, "refactored": path}
"""


def _phase(state: dict) -> str:
    return state.get("phase") or "original"


# --------------------------------------------------------------------------- node 06
def run_tests(state: dict) -> dict:
    """Write the approved suite into java-<phase>/ and run `mvn clean verify`.

    Only the approved suite is selected (-Dtest=<Class>), so hand-written smoke tests
    in the same folder don't inflate results. Output is the parsed Surefire report
    plus build metadata; the router decides from all_passed.
    """
    phase = _phase(state)
    project = java_project_dir(phase)

    test_class = state.get("test_class")
    suite_src = state.get("merged_tests")
    test_file = None
    if suite_src:
        test_file = write_test_file(project, suite_src)
        test_class = test_file.stem

    build = run_maven(project, test_class=test_class, timeout_s=MAVEN_TIMEOUT_S)
    report = parse_surefire(surefire_dir(project))

    # A compile error or timeout means no trustworthy results, even if old XML existed.
    build_ok = not build["compile_error"] and not build["timed_out"] and report["reports_found"]
    report.update({
        "phase": phase,
        "test_class": test_class,
        "test_file": str(test_file) if test_file else None,
        "build": {k: build[k] for k in
                  ("command", "cwd", "exit_code", "timed_out", "duration_s", "compile_error", "log_path")},
        # Tail of Maven output so the repair agent can see compiler errors without opening the log.
        "build_output_tail": (build["stdout"] + "\n" + build["stderr"])[-4000:] if not build_ok else "",
    })
    report["all_passed"] = bool(build_ok and report["all_passed"])

    if not build_ok:
        status = "build_failed"
    else:
        status = "tests_passed" if report["all_passed"] else "tests_failed"
    print(f"[run_tests:{phase}] {report['passed']}/{report['total']} passed, "
          f"{report['failed']} failed, {report['errors']} errors -> {status}")
    return {"test_report": report, "workflow_status": status}


# --------------------------------------------------------------------------- router R2
def route_test_results(state: dict) -> str:
    """R2: 'passed' -> check_coverage, anything else (failures, errors, compile error,
    timeout) -> 'failed' -> repair_agent. Retry caps live in Sarthak's repair loop."""
    report = state.get("test_report") or {}
    return "passed" if report.get("all_passed") else "failed"


# --------------------------------------------------------------------------- node 08
def check_coverage(state: dict) -> dict:
    """Parse JaCoCo XML for the current phase. fully_covered is only True when the XML
    itself shows 0 missed branches in the agreed scope."""
    phase = _phase(state)
    project = java_project_dir(phase)
    scope = state.get("coverage_scope") or DEFAULT_COVERAGE_SCOPE
    cov = parse_jacoco(jacoco_xml_path(project), scope)
    cov["phase"] = phase
    cov["html_report"] = str(jacoco_xml_path(project).with_name("index.html"))

    b = cov["branch"]
    status = "coverage_met" if cov["fully_covered"] else "coverage_below_target"
    print(f"[check_coverage:{phase}] branch {b['covered']}/{b['total']} = {b['percent']}% "
          f"({len(cov['missed_branches'])} line(s) with missed branches) -> {status}")
    return {"coverage": cov, "workflow_status": status}


# --------------------------------------------------------------------------- node 12
def save_results(state: dict) -> dict:
    """Copy evidence for the current phase into artifacts/<phase>/:

        surefire-reports/   TEST-*.xml + txt
        jacoco/             jacoco.xml, jacoco.csv, HTML site
        src/                the Java source and approved test suite that produced them
        test_report.json, coverage.json, tests.json (if structured tests exist),
        change_log.md (if any), maven.log, SUMMARY.md
    """
    phase = _phase(state)
    project = java_project_dir(phase)
    out = REPO_ROOT / "artifacts" / phase
    out.mkdir(parents=True, exist_ok=True)

    def copy_dir(src: Path, dst: Path):
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)

    copy_dir(surefire_dir(project), out / "surefire-reports")
    copy_dir(jacoco_xml_path(project).parent, out / "jacoco")
    copy_dir(project / "src", out / "src")
    log = project / "target" / "agent-maven.log"
    if log.is_file():
        shutil.copy2(log, out / "maven.log")

    report = state.get("test_report") or {}
    cov = state.get("coverage") or {}
    (out / "test_report.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    (out / "coverage.json").write_text(json.dumps(cov, indent=2, default=str), encoding="utf-8")

    tests = state.get("tests")
    if tests:
        serial = [t.model_dump() if hasattr(t, "model_dump") else t for t in tests]
        (out / "tests.json").write_text(json.dumps(serial, indent=2, default=str), encoding="utf-8")

    changes = state.get("change_log") or []
    if changes:
        lines = [f"# Change log — {phase}\n"]
        for i, c in enumerate(changes, 1):
            c = c if isinstance(c, dict) else {"entry": str(c)}
            lines.append(f"## {i}. {c.get('target', '')} — {c.get('reason', c.get('entry', ''))}\n")
            if c.get("diff"):
                lines.append(f"```diff\n{c['diff']}\n```\n")
        (out / "change_log.md").write_text("\n".join(lines), encoding="utf-8")

    b = cov.get("branch", {})
    summary = [
        f"# {phase.capitalize()} phase — test & coverage evidence",
        f"Saved: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        f"- Test class: `{report.get('test_class')}`",
        f"- Tests: {report.get('passed', 0)}/{report.get('total', 0)} passed, "
        f"{report.get('failed', 0)} failed, {report.get('errors', 0)} errors, {report.get('skipped', 0)} skipped",
        f"- Branch coverage: {b.get('covered', 0)}/{b.get('total', 0)} = {b.get('percent', 0)}% "
        f"(fully covered: {cov.get('fully_covered', False)})",
        f"- Line coverage: {cov.get('line', {}).get('percent', 0)}%",
        f"- Coverage scope: {json.dumps(cov.get('scope', DEFAULT_COVERAGE_SCOPE))}",
        f"- Maven command: `{' '.join(report.get('build', {}).get('command', []))}` "
        f"(exit {report.get('build', {}).get('exit_code')})",
        "",
        "Human-readable coverage: `jacoco/index.html`",
    ]
    if cov.get("missed_branches"):
        summary += ["", "## Missed branches"] + [
            f"- {m['source_file']}:{m['line']} ({m['class']}.{m['method']}): {m['missed_branches']} missed"
            for m in cov["missed_branches"]]
    (out / "SUMMARY.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    saved = dict(state.get("saved_artifacts") or {})
    saved[phase] = str(out)
    print(f"[save_results:{phase}] evidence saved to {out}")
    return {"saved_artifacts": saved, "workflow_status": f"{phase}_saved"}
