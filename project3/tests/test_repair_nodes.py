"""Person 4: mocks only the Bedrock model, not patch/coverage parsing logic."""
import ast
import json
import logging
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from java_tools import parse_jacoco, parse_surefire
from repair_nodes import (MAX_COVERAGE_ROUNDS, MAX_REPAIR_ATTEMPTS,
                          build_repair_nodes, route_after_gap, route_after_repair)

SOURCE = (ROOT / "app/SeasonSwitch.java").read_text(encoding="utf-8")
TESTS = """package cse4392;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
public class SeasonSwitchMergedTest {
    @Test void testCool() { assertTrue(true); }
    @Test void testOff() { assertEquals(0, 0); }
}
"""


class FakeModel:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.prompts = []

    def invoke(self, prompt):
        self.prompts.append(prompt)
        if not self.replies:
            raise AssertionError("Unexpected LLM call")
        result = self.replies.pop(0)
        if isinstance(result, BaseException):
            raise result
        return SimpleNamespace(content=result if isinstance(result, str) else json.dumps(result))


def patch(target="code", new=SOURCE, reason="Correct boundary comparison", path="SeasonSwitch.java"):
    return {"target": target, "path": path, "new_content": new, "reason": reason}


def add_test(method="@Test void testGap() { assertEquals(0, 0); }", *, gap=None, **extra):
    return {"id": "COV-01", "technique": "COVERAGE", "description": "Exercise uncovered switch case",
            "source_file": gap["source_file"], "class": gap["class"], "line": gap["line"],
            "method": method, **extra}


class Person4NodeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.original = self.root / "java-original"
        self.folder = self.original / "src/main/java/cse4392"
        self.folder.mkdir(parents=True)
        (self.original / "pom.xml").write_text("<project/>")
        self.working = self.folder / "SeasonSwitch.java"
        self.working.write_text(SOURCE)
        self.broken = SOURCE.replace("room.temp>coolTemp", "room.temp>=coolTemp")
        self.report = {"phase": "original", "all_passed": False, "failures": [
            {"test": "SeasonSwitchMergedTest.testBoundary", "message": "expected off at 68"}
        ], "build_output_tail": ""}
        self.coverage = parse_jacoco(ROOT / "fixtures/jacoco-partial.xml")
        self.coverage["phase"] = "original"
        self.gap = self.coverage["missed_branches"][0]
        self.state = {"phase": "original", "merged_tests": TESTS, "test_report": self.report,
                      "coverage": self.coverage}

    def nodes(self, *replies):
        model = FakeModel(*replies)
        return (*build_repair_nodes(model, self.root), model)

    def test_code_repair_updates_working_copy_and_state_not_original_fixture(self):
        self.working.write_text(self.broken)
        repair, _, model = self.nodes(patch())
        output = repair(self.state)
        self.assertEqual(route_after_repair(output), "run")
        self.assertEqual(output["workflow_status"], "code_repaired")
        self.assertEqual(output["repair_attempts_by_phase"]["original"], 1)
        self.assertEqual(self.working.read_text(), SOURCE)
        self.assertEqual(output["source_code"], SOURCE)
        self.assertIn("-            if (room.temp>=coolTemp)", output["change_log"][0]["diff"])
        self.assertIn("+            if (room.temp>coolTemp)", output["change_log"][0]["diff"])
        self.assertFalse((self.root / "app/SeasonSwitch.java").exists())
        self.assertIn("expected off at 68", model.prompts[0])

    def test_test_repair_requires_human_approval_and_does_not_write(self):
        revised = TESTS.replace("assertEquals(0, 0)", "assertEquals(0, 1)")
        repair, _, _ = self.nodes(patch("test", revised, path="SeasonSwitchMergedTest.java"))
        output = repair(self.state)
        self.assertEqual(route_after_repair(output), "review")
        self.assertEqual(output["review_context"], "repair")
        self.assertEqual(output["pre_review_tests"], TESTS)
        self.assertEqual(output["merged_tests"], revised)
        self.assertFalse(output["human_approved"])
        self.assertFalse((self.original / "src/test/java/cse4392/SeasonSwitchMergedTest.java").exists())
        self.assertEqual(self.working.read_text(), SOURCE)

    def test_removing_existing_test_is_rejected(self):
        reduced = TESTS.replace("    @Test void testOff() { assertEquals(0, 0); }\n", "")
        repair, _, _ = self.nodes(patch("test", reduced, path="SeasonSwitchMergedTest.java"))
        result = repair(self.state)
        self.assertEqual(result["workflow_status"], "repair_blocked")
        self.assertEqual(route_after_repair(result), "escalate")
        self.assertEqual(self.working.read_text(), SOURCE)

    def test_removing_assertion_is_rejected(self):
        reduced = TESTS.replace("assertTrue(true);", "System.out.println(0);")
        repair, _, _ = self.nodes(patch("test", reduced, path="SeasonSwitchMergedTest.java"))
        self.assertEqual(repair(self.state)["workflow_status"], "repair_blocked")

    def test_path_traversal_and_unknown_paths_are_rejected(self):
        for path in ("../../unsafe.java", "../SeasonSwitch.java", "src/main/java/other/SeasonSwitch.java",
                     "/tmp/SeasonSwitch.java", "Missing.java"):
            with self.subTest(path=path):
                repair, _, _ = self.nodes(patch(path=path, new=SOURCE.replace("OFF=0", "OFF=10")))
                result = repair(self.state)
                self.assertEqual(route_after_repair(result), "escalate")
                self.assertEqual(self.working.read_text(), SOURCE)

    def test_unchanged_patch_rejected(self):
        repair, _, _ = self.nodes(patch())
        self.assertEqual(repair(self.state)["workflow_status"], "repair_blocked")

    def test_wrong_package_rejected(self):
        repair, _, _ = self.nodes(patch(new=SOURCE.replace("package cse4392;", "package evil;")))
        self.assertEqual(repair(self.state)["workflow_status"], "repair_blocked")

    def test_invalid_json_and_llm_error_stop_safely(self):
        for reply in ("garbled model response", RuntimeError("unavailable")):
            with self.subTest(reply=reply):
                repair, _, _ = self.nodes(reply)
                result = repair(self.state)
                self.assertEqual(result["workflow_status"], "repair_blocked")
                self.assertEqual(route_after_repair(result), "escalate")

    def test_missing_report_or_wrong_phase_rejected_without_llm_call(self):
        repair, _, model = self.nodes()
        r = repair({**self.state, "test_report": {"phase": "refactored", "all_passed": False}})
        self.assertEqual(r["workflow_status"], "repair_blocked")
        self.assertEqual(model.prompts, [])

    def test_retry_cap_stops_without_model_call(self):
        repair, _, model = self.nodes()
        result = repair({**self.state, "repair_attempts_by_phase": {"original": MAX_REPAIR_ATTEMPTS}})
        self.assertEqual(result["workflow_status"], "repair_exhausted")
        self.assertEqual(model.prompts, [])

    def test_per_phase_counter_refactored_file_repaired(self):
        refactor = self.root / "java-refactored"
        source_dir = refactor / "src/main/java/cse4392"
        source_dir.mkdir(parents=True)
        (refactor / "pom.xml").write_text("<project/>")
        (source_dir / "SeasonSwitch.java").write_text(self.broken)
        repair, _, _ = self.nodes(patch())
        result = repair({**self.state, "phase": "refactored",
                         "test_report": {**self.report, "phase": "refactored"},
                         "repair_attempts_by_phase": {"original": 3},
                         "refactored_files": {"src/main/java/cse4392/SeasonSwitch.java": self.broken}})
        self.assertEqual(result["repair_attempts_by_phase"], {"original": 3, "refactored": 1})
        self.assertEqual((source_dir / "SeasonSwitch.java").read_text(), SOURCE)
        self.assertEqual(result["refactored_files"]["src/main/java/cse4392/SeasonSwitch.java"], SOURCE)
        self.assertNotIn("source_code", result)

    def test_gap_tests_append_after_existing_tests_with_evidence(self):
        _, generate, model = self.nodes({"tests": [add_test(gap=self.gap)]})
        result = generate(self.state)
        self.assertEqual(result["workflow_status"], "gap_tests_pending_review")
        self.assertEqual(route_after_gap(result), "review")
        self.assertEqual(result["review_context"], "gap")
        self.assertEqual(result["pre_review_tests"], TESTS)
        self.assertIn("@Test void testGap()", result["merged_tests"])
        self.assertIn("@Test void testOff()", result["merged_tests"])
        self.assertEqual(result["merged_tests"].count("@Test"), 3)
        self.assertEqual(result["gap_tests"][0]["technique"], "COVERAGE")
        self.assertEqual(result["gap_tests"][0]["line"], self.gap["line"])
        self.assertEqual(result["coverage_rounds_by_phase"], {"original": 1})
        self.assertIn('"missed_branches"', model.prompts[0])
        self.assertIn(self.gap["source_file"], model.prompts[0])

    @unittest.skipUnless(shutil.which("javac"), "Requires Java JDK")
    def test_coverage_method_compiles_in_existing_junit_class(self):
        """Use tiny JUnit signatures to verify Java syntax of the inserted suite."""
        method = ("@Test void testGap() { "
                  "SeasonSwitch ss = new SeasonSwitch(); "
                  "try { SeasonSwitch.state = SeasonSwitch.OFF; ss.cool(); "
                  "assertEquals(SeasonSwitch.COOL, SeasonSwitch.state); } "
                  "finally { ss.timer.stop(); ss.room.timer.stop(); } }")
        _, generate, _ = self.nodes({"tests": [add_test(method, gap=self.gap)]})
        output = generate(self.state)
        self.assertEqual(route_after_gap(output), "review")
        suite_dir = self.original / "src/test/java/cse4392"
        suite_dir.mkdir(parents=True)
        (suite_dir / "SeasonSwitchMergedTest.java").write_text(output["merged_tests"])
        stub = self.root / "stub/org/junit/jupiter/api"
        stub.mkdir(parents=True)
        (stub / "Test.java").write_text(
            "package org.junit.jupiter.api; public @interface Test {}")
        (stub / "Assertions.java").write_text(
            "package org.junit.jupiter.api; public class Assertions { "
            "public static void assertTrue(boolean v) {} "
            "public static void assertEquals(int x, int y) {} }")
        cmd = ["javac", "-d", str(self.root / "compiled"), str(self.working),
               str(stub / "Test.java"), str(stub / "Assertions.java"),
               str(suite_dir / "SeasonSwitchMergedTest.java")]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_gap_reference_is_rejected(self):
        item = add_test(gap=self.gap)
        item["line"] = 9999
        _, generate, _ = self.nodes({"tests": [item]})
        result = generate(self.state)
        self.assertEqual(result["workflow_status"], "gap_blocked")
        self.assertEqual(route_after_gap(result), "escalate")

    def test_duplicate_method_or_missing_assertion_is_rejected(self):
        for method in ("@Test void testCool() { assertTrue(true); }",
                       "@Test void emptyMethod() { System.out.println(0); }"):
            _, generate, _ = self.nodes({"tests": [add_test(method, gap=self.gap)]})
            self.assertEqual(generate(self.state)["workflow_status"], "gap_blocked")

    def test_empty_coverage_list_and_fake_100_percent_are_rejected(self):
        _, generate, model = self.nodes()
        result = generate({**self.state, "coverage": {**self.coverage, "missed_branches": []}})
        self.assertEqual(result["workflow_status"], "gap_blocked")
        self.assertEqual(model.prompts, [])
        self.assertEqual(generate({**self.state, "coverage": {**self.coverage,
                           "branch": {"missed": 0}}})["workflow_status"], "gap_blocked")

    def test_coverage_round_cap(self):
        _, generate, model = self.nodes()
        result = generate({**self.state, "coverage_rounds_by_phase": {"original": MAX_COVERAGE_ROUNDS}})
        self.assertEqual(result["workflow_status"], "gap_exhausted")
        self.assertEqual(model.prompts, [])

    def test_java_interface_patch_accepted(self):
        source_dir = self.root / "java-refactored/src/main/java/cse4392"
        source_dir.mkdir(parents=True)
        (source_dir.parents[3] / "pom.xml").write_text("<project/>")
        original = "package cse4392; interface State { void on(); }"
        fixed = "package cse4392; interface State { void on(); void off(); }"
        (source_dir / "State.java").write_text(original)
        (source_dir / "SeasonSwitch.java").write_text(SOURCE)
        repair, _, _ = self.nodes(patch(path="State.java", new=fixed))
        result = repair({**self.state, "phase": "refactored", "test_report": {**self.report, "phase": "refactored"}})
        self.assertEqual(route_after_repair(result), "run")
        self.assertEqual((source_dir / "State.java").read_text(), fixed)

    @unittest.skipUnless(shutil.which("javac") and shutil.which("java"), "Requires Java JDK")
    def test_seeded_java_defect_fails_then_model_patch_restores_behavior(self):
        """Compile and execute real SeasonSwitch bytecode, not a mocked Maven success."""
        checker = self.folder / "BoundaryCheck.java"
        checker.write_text('''package cse4392;
public class BoundaryCheck {
  public static void main(String[] args) {
    SeasonSwitch.state = SeasonSwitch.COOL;
    SeasonSwitch ss = new SeasonSwitch();
    try {
      ss.room.temp = 68;
      ss.ac.on();
      ss.timerOff();
      if (ss.ac.isOn) throw new AssertionError("AC must be off at 68");
    } finally { ss.timer.stop(); ss.room.timer.stop(); }
  }
}
''')
        def run():
            build = self.root / "compiled"
            build.mkdir(exist_ok=True)
            subprocess.run(["javac", "-d", str(build), str(self.working), str(checker)], check=True,
                           capture_output=True, text=True, timeout=25)
            return subprocess.run(["java", "-cp", str(build), "cse4392.BoundaryCheck"],
                                  capture_output=True, text=True, timeout=25)
        self.working.write_text(self.broken)
        before = run()
        self.assertNotEqual(before.returncode, 0)
        self.assertIn("AC must be off at 68", before.stderr)
        repair, _, _ = self.nodes(patch())
        updated = repair(self.state)
        self.assertEqual(updated["repair_action"], "run")
        after = run()
        self.assertEqual(after.returncode, 0, after.stderr)


class HumanApprovalWiringTests(unittest.TestCase):
    """Execute Ryan's actual review/router functions with mocked interrupt input.

    main.py imports Bedrock/LangGraph at module load, unavailable in CI without
    cloud credentials. Extracting these pure functions checks the real source
    while leaving all SDKs and unrelated team modules untouched.
    """
    @classmethod
    def setUpClass(cls):
        tree = ast.parse((ROOT / "app/main.py").read_text())
        names = {"review_tests", "route_test_review", "route_tests_by_phase", "route_coverage"}
        nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
        cls.functions = compile(ast.Module(body=nodes, type_ignores=[]), "app/main.py", "exec")

    def run_review(self, state, approved, feedback=""):
        env = {"AgentState": dict,
               "interrupt": lambda payload: {"approved": approved, "feedback": feedback},
               "log": logging.getLogger("test-review"), "datetime": __import__("datetime").datetime,
               "MAX_HUMAN_REJECTIONS": 3, "MAX_TEST_FIX_ROUNDS": 2,
               "OUTPUT_DIR": ROOT / "generated_tests", "MAX_REVIEW_REJECTIONS": 3,
               "route_test_results": lambda state: "passed" if state["test_report"]["all_passed"] else "failed"}
        exec(self.functions, env)
        state = {"class_name": "SeasonSwitch", "phase": "original", **state}
        return env["review_tests"](state), env

    def test_rejected_coverage_candidate_restores_approved_suite_and_retries_gap(self):
        state = {"merged_tests": TESTS + "\n// candidate", "pre_review_tests": TESTS,
                 "review_context": "gap", "human_approved": False,
                 "change_log": [{"diff": "+ candidate"}]}
        result, env = self.run_review(state, False, "Correct boundary value")
        self.assertEqual(result["merged_tests"], TESTS)
        self.assertEqual(result["human_feedback"], "Correct boundary value")
        self.assertEqual(env["route_test_review"]({**state, **result}), "retry_gap")

    def test_rejected_test_repair_retries_repair_not_generators(self):
        state = {"merged_tests": TESTS + "\n// candidate", "pre_review_tests": TESTS,
                 "review_context": "repair", "change_log": [{"diff": "+ candidate"}]}
        result, env = self.run_review(state, False, "Keep test oracle")
        self.assertEqual(env["route_test_review"]({**state, **result}), "retry_repair")
        self.assertEqual(result["merged_tests"], TESTS)

    def test_approved_candidate_runs_and_clears_pending_context(self):
        state = {"merged_tests": TESTS, "pre_review_tests": "old", "review_context": "gap"}
        result, env = self.run_review(state, True)
        self.assertEqual(env["route_test_review"]({**state, **result}), "approved")
        self.assertEqual(result["review_context"], "")
        self.assertEqual(result["pre_review_tests"], "")

    def test_review_rejections_are_bounded(self):
        state = {"merged_tests": TESTS, "pre_review_tests": TESTS, "review_context": "gap",
                 "human_rejections": 2}
        result, env = self.run_review(state, False, "Need more tests")
        self.assertEqual(env["route_test_review"]({**state, **result}), "max_attempts")

    def test_original_generator_review_still_routes_to_original_agents(self):
        state = {"merged_tests": TESTS, "review_context": ""}
        result, env = self.run_review(state, False, "More BVA tests")
        self.assertEqual(env["route_test_review"]({**state, **result}), ["ep_agent", "bva_agent"])

    def test_main_graph_has_no_unknown_edge_targets(self):
        """Catch typos that would prevent LangGraph compilation."""
        graph = next(n for n in ast.parse((ROOT / "app/main.py").read_text()).body
                     if isinstance(n, ast.FunctionDef) and n.name == "build_graph")
        calls = [n for n in ast.walk(graph) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute)]
        nodes = {c.args[0].value for c in calls if c.func.attr == "add_node"}
        allowed = nodes | {"START", "END"}
        for call in calls:
            if call.func.attr not in ("add_edge", "add_conditional_edges"):
                continue
            source = call.args[0]
            if isinstance(source, ast.List):
                sources = [x.value for x in source.elts]
            elif isinstance(source, ast.Constant):
                sources = [source.value]
            else:
                sources = [source.id]
            for name in sources:
                self.assertIn(name, allowed)
            targets = []
            if call.func.attr == "add_edge":
                targets.append(call.args[1])
            else:
                self.assertIsInstance(call.args[2], ast.Dict)
                targets.extend(call.args[2].values)
            for dest in targets:
                if isinstance(dest, ast.Constant):
                    self.assertIn(dest.value, allowed)
                elif isinstance(dest, ast.Name):
                    self.assertIn(dest.id, allowed)
                else:
                    self.fail(f"Unexpected graph target: {ast.dump(dest)}")

    def test_main_graph_registers_repair_and_gap_routing(self):
        tree = ast.parse((ROOT / "app/main.py").read_text())
        graphs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "build_graph"]
        self.assertEqual(len(graphs), 1)
        graph = graphs[0]
        calls = [n for n in ast.walk(graph) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
        node_names = [n.args[0].value for n in calls if n.func.attr == "add_node" and n.args and isinstance(n.args[0], ast.Constant)]
        self.assertIn("repair_agent", node_names)
        self.assertIn("generate_gap_tests", node_names)
        routing = {}
        for call in calls:
            if call.func.attr != "add_conditional_edges":
                continue
            name = call.args[0].value
            if name not in ("run_tests", "repair_agent", "generate_gap_tests", "review_tests"):
                continue
            mapping = ast.literal_eval(call.args[2])
            routing[name] = mapping
        self.assertEqual(routing["run_tests"]["failed"], "repair_agent")
        self.assertEqual(routing["repair_agent"], {"run": "run_tests", "review": "review_tests",
                                                   "escalate": "escalate_review"})
        self.assertEqual(routing["generate_gap_tests"], {"review": "review_tests",
                                                         "escalate": "escalate_review"})
        self.assertEqual(routing["review_tests"]["retry_gap"], "generate_gap_tests")
        self.assertEqual(routing["review_tests"]["retry_repair"], "repair_agent")


if __name__ == "__main__":
    unittest.main()
