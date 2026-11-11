"""
Person 3 (Joseph) - deterministic Java tooling for the TA3 LangGraph agent.

Pure Python, standard library only (no LangGraph import), so every function can be
unit-tested and called from any node.

    write_test_file(project_dir, java_code)   -> Path of src/test/java/cse4392/<Class>.java
    run_maven(project_dir, ...)               -> MavenResult dict (exit code, timeout, logs)
    parse_surefire(reports_dir)               -> test_report dict (counts + failure details)
    parse_jacoco(xml_path, scope)             -> coverage dict (branch counts + missed lines)

Quick manual run from the repo root:

    python app/java_tools.py original                 # run every test class
    python app/java_tools.py original --test-class SeasonSwitchSmokeTest
"""
from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
JAVA_PACKAGE = "cse4392"
PHASES = ("original", "refactored")

# Maven flags the agent always uses: finish the build even if tests fail or coverage
# is below 100%, so the reports exist and the graph decides from parsed evidence.
AGENT_MAVEN_PROPS = {
    "maven.test.failure.ignore": "true",
    "jacoco.haltOnFailure": "false",
    "surefire.failIfNoSpecifiedTests": "false",
}

# Coverage scope agreed by the team (see docs/coverage-scope.md).
# include_classes=None  -> every class in the JaCoCo report (SeasonSwitch + AC/Heater/Room).
# exclude_methods       -> "SimpleClass.method" names removed from the measured scope;
#                          anything listed here MUST be justified in docs/coverage-scope.md.
DEFAULT_COVERAGE_SCOPE = {
    "include_classes": None,
    "exclude_methods": [],
}


# --------------------------------------------------------------------------- paths
def java_project_dir(phase: str) -> Path:
    """java-original/ or java-refactored/ at the repo root."""
    if phase not in PHASES:
        raise ValueError(f"phase must be one of {PHASES}, got {phase!r}")
    return REPO_ROOT / f"java-{phase}"


def surefire_dir(project_dir: Path) -> Path:
    return Path(project_dir) / "target" / "surefire-reports"


def jacoco_xml_path(project_dir: Path) -> Path:
    return Path(project_dir) / "target" / "site" / "jacoco" / "jacoco.xml"


# --------------------------------------------------------------------------- test files
_CLASS_RE = re.compile(r"^\s*(?:public\s+)?(?:final\s+)?class\s+([A-Za-z_]\w*)", re.MULTILINE)
_PACKAGE_RE = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.MULTILINE)


def java_class_name(java_code: str) -> str:
    """First top-level class name declared in a Java source string."""
    m = _CLASS_RE.search(java_code)
    if not m:
        raise ValueError("No class declaration found in the test source.")
    return m.group(1)


def write_test_file(project_dir: Path, java_code: str, package: str = JAVA_PACKAGE) -> Path:
    """Write an approved JUnit suite to src/test/java/<package>/<Class>.java.

    Idempotent: rewriting identical content is harmless if a node is resumed after an
    interrupt. Refuses code whose package does not match, so a stray LLM output
    can't land outside the Maven test tree.
    """
    if not java_code or not java_code.strip():
        raise ValueError("Test source is empty.")
    pkg = _PACKAGE_RE.search(java_code)
    if not pkg or pkg.group(1) != package:
        found = pkg.group(1) if pkg else "none"
        raise ValueError(f"Test source must declare 'package {package};' (found: {found}).")
    name = java_class_name(java_code)
    test_dir = Path(project_dir) / "src" / "test" / "java" / Path(*package.split("."))
    test_dir.mkdir(parents=True, exist_ok=True)
    target = (test_dir / f"{name}.java").resolve()
    if test_dir.resolve() not in target.parents:
        raise ValueError(f"Refusing to write outside {test_dir}")
    target.write_text(java_code, encoding="utf-8")
    return target


# --------------------------------------------------------------------------- maven
def _find_mvn() -> str:
    for candidate in ("mvn", "mvn.cmd"):
        found = shutil.which(candidate)
        if found:
            return found
    raise FileNotFoundError("Maven not found on PATH (install Maven 3.9.x).")


def run_maven(
    project_dir: Path,
    goals: Iterable[str] = ("clean", "verify"),
    test_class: Optional[str] = None,
    props: Optional[dict] = None,
    timeout_s: int = 300,
    mvn_cmd: Optional[list] = None,
    log_name: str = "agent-maven.log",
) -> dict:
    """Run Maven as a subprocess with an argument list (no shell, no injection).

    test_class -> passed as -Dtest=<package>.<Class> so only the approved suite runs.
    props      -> extra -Dkey=value flags (merged over AGENT_MAVEN_PROPS).
    mvn_cmd    -> override the executable (tests use a fake script here).

    Returns a dict with command, cwd, exit_code, timed_out, duration_s, stdout, stderr,
    log_path and compile_error. On timeout the whole process group is killed so a
    hung forked test JVM does not linger.
    """
    project_dir = Path(project_dir).resolve()
    if not (project_dir / "pom.xml").is_file():
        raise FileNotFoundError(f"No pom.xml in {project_dir}")

    all_props = dict(AGENT_MAVEN_PROPS)
    all_props.update(props or {})
    if test_class:
        if not re.fullmatch(r"[A-Za-z_][\w.$#*,]*", test_class):
            raise ValueError(f"Suspicious test class selector: {test_class!r}")
        all_props["test"] = test_class if "." in test_class else f"{JAVA_PACKAGE}.{test_class}"

    cmd = list(mvn_cmd) if mvn_cmd else [_find_mvn(), "-B", "-ntp"]
    cmd += [f"-D{k}={v}" for k, v in all_props.items()]
    cmd += list(goals)

    popen_kwargs = {}
    if os.name == "posix":
        popen_kwargs["start_new_session"] = True          # own process group -> killpg
    else:
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]

    start = time.monotonic()
    proc = subprocess.Popen(
        cmd, cwd=project_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace", **popen_kwargs,
    )
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_tree(proc)
        stdout, stderr = proc.communicate()
    duration = round(time.monotonic() - start, 2)

    exit_code = proc.returncode
    compile_error = (exit_code != 0) and bool(
        re.search(r"COMPILATION ERROR|Compilation failure", stdout + stderr)
    )

    log_dir = project_dir / "target"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / log_name
    log_path.write_text(
        f"$ {' '.join(cmd)}\n(cwd: {project_dir})\n"
        f"exit_code={exit_code} timed_out={timed_out} duration_s={duration}\n\n"
        f"===== STDOUT =====\n{stdout}\n===== STDERR =====\n{stderr}\n",
        encoding="utf-8",
    )
    return {
        "command": cmd,
        "cwd": str(project_dir),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "duration_s": duration,
        "compile_error": compile_error,
        "stdout": stdout,
        "stderr": stderr,
        "log_path": str(log_path),
    }


def _kill_tree(proc: subprocess.Popen) -> None:
    try:
        if os.name == "posix":
            os.killpg(proc.pid, signal.SIGKILL)
        else:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           capture_output=True, check=False)
    except (ProcessLookupError, PermissionError):
        pass


# --------------------------------------------------------------------------- surefire
def parse_surefire(reports_dir: Path, max_detail_chars: int = 2000) -> dict:
    """Read every target/surefire-reports/TEST-*.xml.

    all_passed is True only if at least one test passed and none failed/errored.
    Failures keep the message, exception type and a trimmed stack trace for Sarthak's
    repair agent.
    """
    reports_dir = Path(reports_dir)
    files = sorted(reports_dir.glob("TEST-*.xml")) if reports_dir.is_dir() else []
    report = {
        "reports_found": bool(files),
        "report_files": [str(f) for f in files],
        "total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0,
        "time_s": 0.0,
        "all_passed": False,
        "failures": [],
        "tests": [],
    }
    for f in files:
        root = ET.parse(f).getroot()
        suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
        for suite in suites:
            for case in suite.findall("testcase"):
                name = case.get("name", "")
                cls = case.get("classname", suite.get("name", ""))
                status = "passed"
                problem = None
                for kind in ("failure", "error"):
                    el = case.find(kind)
                    if el is not None:
                        status = "failed" if kind == "failure" else "error"
                        problem = {
                            "test": f"{cls.split('.')[-1]}.{name}",
                            "classname": cls,
                            "name": name,
                            "kind": kind,
                            "type": el.get("type", ""),
                            "message": el.get("message", "") or "",
                            "details": (el.text or "").strip()[:max_detail_chars],
                        }
                        break
                if status == "passed" and case.find("skipped") is not None:
                    status = "skipped"

                report["total"] += 1
                report["time_s"] += float(case.get("time", 0) or 0)
                key = {"passed": "passed", "failed": "failed",
                       "error": "errors", "skipped": "skipped"}[status]
                report[key] += 1
                report["tests"].append({"test": f"{cls.split('.')[-1]}.{name}", "status": status})
                if problem:
                    report["failures"].append(problem)

    report["time_s"] = round(report["time_s"], 3)
    # At least one test must actually execute and pass; an all-skipped run is not a pass.
    report["all_passed"] = report["passed"] > 0 and report["failed"] == 0 and report["errors"] == 0
    return report


# --------------------------------------------------------------------------- jacoco
def _counter(el: ET.Element, ctype: str) -> tuple[int, int]:
    for c in el.findall("counter"):
        if c.get("type") == ctype:
            return int(c.get("missed", 0)), int(c.get("covered", 0))
    return 0, 0


def _simple(class_path: str) -> str:
    """'cse4392/SeasonSwitch$Room' -> 'SeasonSwitch$Room'."""
    return class_path.rsplit("/", 1)[-1]


def parse_jacoco(xml_path: Path, scope: Optional[dict] = None) -> dict:
    """Parse target/site/jacoco/jacoco.xml into branch-coverage evidence.

    scope = {"include_classes": [...] | None, "exclude_methods": ["SeasonSwitch.main", ...]}
    Class names are simple JaCoCo names: 'SeasonSwitch', 'SeasonSwitch$Room'.

    Totals are summed from METHOD-level BRANCH counters for the in-scope methods, so an
    exclusion is reflected exactly. 'fully_covered' is True only when the XML shows
    >0 branches and 0 missed in scope (never inferred).

    missed_branches lists every source line with mb>0 that falls in an in-scope method,
    which is exactly what gen_missing_branch_tests needs.
    """
    xml_path = Path(xml_path)
    scope = {**DEFAULT_COVERAGE_SCOPE, **(scope or {})}
    include = set(scope["include_classes"]) if scope["include_classes"] else None
    exclude = set(scope["exclude_methods"] or [])

    if not xml_path.is_file():
        return {"report_found": False, "xml_path": str(xml_path), "fully_covered": False,
                "branch": {"covered": 0, "missed": 0, "total": 0, "percent": 0.0},
                "missed_branches": [], "classes": {}, "scope": scope}

    root = ET.parse(xml_path).getroot()
    classes: dict = {}
    excluded_methods_found: list = []
    tot_b_missed = tot_b_cov = tot_l_missed = tot_l_cov = 0
    missed_branches: list = []

    for pkg in root.findall("package"):
        # method start lines per source file (all classes in that file), for line->method mapping
        starts_by_file: dict[str, list] = {}
        for cls in pkg.findall("class"):
            cname = _simple(cls.get("name", ""))
            src = cls.get("sourcefilename", "")
            for m in cls.findall("method"):
                if m.get("line"):
                    starts_by_file.setdefault(src, []).append(
                        (int(m.get("line")), cname, m.get("name"), m.get("desc", "")))
        for lst in starts_by_file.values():
            lst.sort()

        in_scope_methods: set = set()
        for cls in pkg.findall("class"):
            cname = _simple(cls.get("name", ""))
            if include is not None and cname not in include:
                continue
            c_bm = c_bc = c_lm = c_lc = 0
            for m in cls.findall("method"):
                mname = m.get("name", "")
                short = f"{cname}.{mname}"
                if short in exclude:
                    excluded_methods_found.append(short)
                    continue
                in_scope_methods.add((cname, mname, m.get("desc", "")))
                bm, bc = _counter(m, "BRANCH")
                lm, lc = _counter(m, "LINE")
                c_bm += bm; c_bc += bc; c_lm += lm; c_lc += lc
            classes[cname] = {
                "source_file": cls.get("sourcefilename", ""),
                "branch": {"missed": c_bm, "covered": c_bc, "total": c_bm + c_bc},
                "line": {"missed": c_lm, "covered": c_lc, "total": c_lm + c_lc},
            }
            tot_b_missed += c_bm; tot_b_cov += c_bc; tot_l_missed += c_lm; tot_l_cov += c_lc

        for sf in pkg.findall("sourcefile"):
            src = sf.get("name", "")
            starts = starts_by_file.get(src, [])
            for line in sf.findall("line"):
                mb = int(line.get("mb", 0))
                if mb <= 0:
                    continue
                nr = int(line.get("nr"))
                owner = None
                for start, cname, mname, desc in starts:
                    if start <= nr:
                        owner = (cname, mname, desc)
                    else:
                        break
                if owner is None or owner not in in_scope_methods:
                    continue
                missed_branches.append({
                    "source_file": src,
                    "class": owner[0],
                    "method": owner[1],
                    "line": nr,
                    "missed_branches": mb,
                    "covered_branches": int(line.get("cb", 0)),
                    "missed_instructions": int(line.get("mi", 0)),
                })

    b_total = tot_b_missed + tot_b_cov
    l_total = tot_l_missed + tot_l_cov
    missed_branches.sort(key=lambda d: (d["source_file"], d["line"]))
    return {
        "report_found": True,
        "xml_path": str(xml_path),
        "scope": scope,
        "excluded_methods": sorted(set(excluded_methods_found)),
        "branch": {
            "covered": tot_b_cov, "missed": tot_b_missed, "total": b_total,
            "percent": round(100.0 * tot_b_cov / b_total, 2) if b_total else 0.0,
        },
        "line": {
            "covered": tot_l_cov, "missed": tot_l_missed, "total": l_total,
            "percent": round(100.0 * tot_l_cov / l_total, 2) if l_total else 0.0,
        },
        "fully_covered": b_total > 0 and tot_b_missed == 0,
        "missed_branches": missed_branches,
        "classes": classes,
    }


# --------------------------------------------------------------------------- CLI
def _main(argv: list) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Run Maven for one phase and print parsed results.")
    ap.add_argument("phase", choices=PHASES)
    ap.add_argument("--test-class", help="e.g. SeasonSwitchMergedTest (default: all tests)")
    ap.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args(argv)

    project = java_project_dir(args.phase)
    build = run_maven(project, test_class=args.test_class, timeout_s=args.timeout)
    tests = parse_surefire(surefire_dir(project))
    cov = parse_jacoco(jacoco_xml_path(project))
    print(f"maven exit={build['exit_code']} timed_out={build['timed_out']} "
          f"compile_error={build['compile_error']} ({build['duration_s']}s) log={build['log_path']}")
    print(f"tests: {tests['passed']}/{tests['total']} passed, {tests['failed']} failed, "
          f"{tests['errors']} errors, {tests['skipped']} skipped")
    for f in tests["failures"]:
        print(f"  FAIL {f['test']}: {f['message'][:160]}")
    b = cov["branch"]
    print(f"branch coverage: {b['covered']}/{b['total']} = {b['percent']}%  "
          f"(fully_covered={cov['fully_covered']})")
    for mb in cov["missed_branches"]:
        print(f"  missed {mb['missed_branches']} branch(es) at {mb['source_file']}:{mb['line']} "
              f"in {mb['class']}.{mb['method']}")
    return 0 if (tests["all_passed"] and cov["fully_covered"]) else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
