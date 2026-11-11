"""Person 3 unit tests - no Maven, JDK or LangGraph needed.

    python -m unittest discover -s tests -v        (from repo root)
"""
import json
import shutil
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

import java_tools as jt          # noqa: E402
import testing_nodes as tn       # noqa: E402

FIX = ROOT / "fixtures"


class SurefireParserTest(unittest.TestCase):
    def _dir_with(self, *names):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d)
        for n in names:
            shutil.copy(FIX / n, d / f"TEST-{n}")
        return d

    def test_failing_fixture(self):
        r = jt.parse_surefire(self._dir_with("surefire-fail.xml"))
        self.assertEqual((r["total"], r["passed"], r["failed"], r["errors"]), (5, 2, 2, 1))
        self.assertFalse(r["all_passed"])
        names = [f["name"] for f in r["failures"]]
        self.assertIn("testTimerOffCoolAtThreshold68TurnsAcOff", names)
        err = next(f for f in r["failures"] if f["kind"] == "error")
        self.assertEqual(err["type"], "java.lang.NullPointerException")
        self.assertIn("SeasonSwitch.java:137", err["details"])

    def test_passing_fixture(self):
        r = jt.parse_surefire(self._dir_with("surefire-pass.xml"))
        self.assertEqual((r["total"], r["passed"]), (3, 3))
        self.assertTrue(r["all_passed"])

    def test_multiple_files_are_summed(self):
        r = jt.parse_surefire(self._dir_with("surefire-pass.xml", "surefire-fail.xml"))
        self.assertEqual(r["total"], 8)
        self.assertEqual(len(r["report_files"]), 2)

    def test_missing_dir_is_not_a_pass(self):
        r = jt.parse_surefire(Path("/nonexistent/surefire-reports"))
        self.assertFalse(r["reports_found"])
        self.assertFalse(r["all_passed"])

    def test_skipped_only_is_counted(self):
        d = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, d)
        (d / "TEST-x.xml").write_text(
            '<testsuite name="x" tests="1"><testcase name="a" classname="cse4392.X">'
            '<skipped/></testcase></testsuite>')
        r = jt.parse_surefire(d)
        self.assertEqual(r["skipped"], 1)
        self.assertFalse(r["all_passed"])   # zero executed tests is never a pass


class JacocoParserTest(unittest.TestCase):
    XML = FIX / "jacoco-partial.xml"

    def test_full_scope_totals(self):
        c = jt.parse_jacoco(self.XML)
        self.assertEqual(c["branch"], {"covered": 5, "missed": 31, "total": 36, "percent": 13.89})
        self.assertFalse(c["fully_covered"])
        self.assertEqual(c["classes"]["SeasonSwitch$Room"]["branch"]["total"], 8)
        self.assertEqual(c["classes"]["SeasonSwitch"]["branch"]["total"], 28)

    def test_missed_lines_map_to_methods(self):
        c = jt.parse_jacoco(self.XML)
        by_line = {m["line"]: m for m in c["missed_branches"]}
        self.assertEqual(by_line[77]["method"], "timerOff")
        self.assertEqual(by_line[77]["missed_branches"], 1)
        self.assertEqual(by_line[101]["method"], "main")
        self.assertEqual((by_line[137]["class"], by_line[137]["method"]),
                         ("SeasonSwitch$Room", "actionPerformed"))
        self.assertEqual(sum(m["missed_branches"] for m in c["missed_branches"]), 31)

    def test_excluding_main_is_explicit(self):
        c = jt.parse_jacoco(self.XML, {"exclude_methods": ["SeasonSwitch.main"]})
        self.assertEqual(c["branch"]["total"], 28)
        self.assertEqual(c["excluded_methods"], ["SeasonSwitch.main"])
        self.assertNotIn(101, [m["line"] for m in c["missed_branches"]])

    def test_include_classes(self):
        c = jt.parse_jacoco(self.XML, {"include_classes": ["SeasonSwitch$Room"]})
        self.assertEqual(c["branch"]["total"], 8)
        self.assertEqual({m["class"] for m in c["missed_branches"]}, {"SeasonSwitch$Room"})

    def test_100_percent_only_when_xml_says_so(self):
        d = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, d)
        full = self.XML.read_text().replace('mb="1" cb="1"', 'mb="0" cb="2"')
        p = d / "j.xml"; p.write_text(full)
        c = jt.parse_jacoco(p, {"include_classes": ["SeasonSwitch"],
                                "exclude_methods": ["SeasonSwitch.main"]})
        # method counters still report missed branches -> must NOT claim 100%
        self.assertFalse(c["fully_covered"])

    def test_missing_report(self):
        c = jt.parse_jacoco(Path("/nope/jacoco.xml"))
        self.assertFalse(c["report_found"])
        self.assertFalse(c["fully_covered"])


class WriteTestFileTest(unittest.TestCase):
    def setUp(self):
        self.proj = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.proj)

    def test_writes_into_package_dir(self):
        p = jt.write_test_file(self.proj, "package cse4392;\nclass SeasonSwitchMergedTest {}\n")
        self.assertEqual(p, (self.proj / "src/test/java/cse4392/SeasonSwitchMergedTest.java").resolve())

    def test_rejects_wrong_package(self):
        with self.assertRaises(ValueError):
            jt.write_test_file(self.proj, "package evil;\nclass X {}")

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            jt.write_test_file(self.proj, "   ")


class RunMavenTest(unittest.TestCase):
    """Uses a fake 'mvn' (python one-liner) so no Maven is needed."""

    def setUp(self):
        self.proj = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.proj)
        (self.proj / "pom.xml").write_text("<project/>")

    def test_success_and_args_are_a_list(self):
        fake = [sys.executable, "-c", "import sys; print('ARGS', sys.argv[1:])"]
        r = jt.run_maven(self.proj, test_class="SeasonSwitchMergedTest", mvn_cmd=fake)
        self.assertEqual(r["exit_code"], 0)
        self.assertIn("-Dtest=cse4392.SeasonSwitchMergedTest", r["stdout"])
        self.assertIn("-Djacoco.haltOnFailure=false", r["stdout"])
        self.assertTrue(Path(r["log_path"]).is_file())

    def test_compile_error_detected(self):
        fake = [sys.executable, "-c", "print('[ERROR] COMPILATION ERROR :'); raise SystemExit(1)"]
        r = jt.run_maven(self.proj, mvn_cmd=fake)
        self.assertTrue(r["compile_error"])

    def test_timeout_kills(self):
        fake = [sys.executable, "-c", "import time; time.sleep(30)"]
        r = jt.run_maven(self.proj, mvn_cmd=fake, timeout_s=1)
        self.assertTrue(r["timed_out"])
        self.assertLess(r["duration_s"], 10)

    def test_injection_in_test_selector_rejected(self):
        with self.assertRaises(ValueError):
            jt.run_maven(self.proj, test_class="X; rm -rf /", mvn_cmd=[sys.executable, "-c", "0"])

    def test_requires_pom(self):
        with self.assertRaises(FileNotFoundError):
            jt.run_maven(self.proj / "missing", mvn_cmd=[sys.executable, "-c", "0"])


class NodesTest(unittest.TestCase):
    """Drive the graph nodes with a mock state dict and a temp repo layout."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.root)
        proj = self.root / "java-original"
        (proj / "src/main/java/cse4392").mkdir(parents=True)
        (proj / "pom.xml").write_text("<project/>")
        (proj / "src/main/java/cse4392/SeasonSwitch.java").write_text("package cse4392; class SeasonSwitch {}")
        self.proj = proj
        self.patches = [mock.patch.object(jt, "REPO_ROOT", self.root),
                        mock.patch.object(tn, "REPO_ROOT", self.root),
                        mock.patch.object(tn, "java_project_dir", lambda ph: self.root / f"java-{ph}")]
        for p in self.patches:
            p.start(); self.addCleanup(p.stop)

    def _fake_maven(self, surefire_fixture, jacoco=True):
        def fake(project_dir, **kw):
            rep = Path(project_dir) / "target/surefire-reports"; rep.mkdir(parents=True, exist_ok=True)
            shutil.copy(FIX / surefire_fixture, rep / "TEST-cse4392.X.xml")
            if jacoco:
                jd = Path(project_dir) / "target/site/jacoco"; jd.mkdir(parents=True, exist_ok=True)
                shutil.copy(FIX / "jacoco-partial.xml", jd / "jacoco.xml")
                (jd / "index.html").write_text("<html/>")
            log = Path(project_dir) / "target/agent-maven.log"; log.write_text("log")
            return {"command": ["mvn"], "cwd": str(project_dir), "exit_code": 0, "timed_out": False,
                    "duration_s": 1.0, "compile_error": False, "stdout": "", "stderr": "",
                    "log_path": str(log), "test_class": kw.get("test_class")}
        return fake

    def test_failed_run_routes_to_repair(self):
        with mock.patch.object(tn, "run_maven", self._fake_maven("surefire-fail.xml")):
            out = tn.run_tests({"phase": "original",
                                "merged_tests": "package cse4392;\npublic class SeasonSwitchMergedTest {}"})
        self.assertEqual(out["workflow_status"], "tests_failed")
        self.assertEqual(out["test_report"]["test_class"], "SeasonSwitchMergedTest")
        self.assertEqual(tn.route_test_results(out), "failed")

    def test_passing_run_routes_to_coverage_then_saves(self):
        with mock.patch.object(tn, "run_maven", self._fake_maven("surefire-pass.xml")):
            state = {"phase": "original"}
            state.update(tn.run_tests(state))
        self.assertEqual(tn.route_test_results(state), "passed")

        state.update(tn.check_coverage(state))
        self.assertEqual(state["workflow_status"], "coverage_below_target")
        self.assertEqual(state["coverage"]["branch"]["total"], 36)

        state["change_log"] = [{"target": "test", "reason": "fixed oracle", "diff": "-a\n+b"}]
        state["tests"] = [{"id": "EP-01", "technique": "EP"}]
        state.update(tn.save_results(state))
        out = self.root / "artifacts/original"
        for f in ("SUMMARY.md", "test_report.json", "coverage.json", "tests.json", "change_log.md",
                  "maven.log", "jacoco/jacoco.xml", "jacoco/index.html", "surefire-reports",
                  "src/main/java/cse4392/SeasonSwitch.java"):
            self.assertTrue((out / f).exists(), f)
        self.assertEqual(json.loads((out / "coverage.json").read_text())["branch"]["covered"], 5)
        self.assertEqual(state["saved_artifacts"]["original"], str(out))

    def test_compile_error_is_failed_even_with_stale_reports(self):
        def broken(project_dir, **kw):
            r = self._fake_maven("surefire-pass.xml")(project_dir, **kw)
            r.update(exit_code=1, compile_error=True, stdout="COMPILATION ERROR")
            return r
        with mock.patch.object(tn, "run_maven", broken):
            out = tn.run_tests({"phase": "original"})
        self.assertEqual(out["workflow_status"], "build_failed")
        self.assertEqual(tn.route_test_results(out), "failed")
        self.assertIn("COMPILATION ERROR", out["test_report"]["build_output_tail"])


if __name__ == "__main__":
    unittest.main()
