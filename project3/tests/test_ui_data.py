"""Tests for the terminal dashboard's data readers and the per-test review request.
No terminal, LLM or Maven is needed."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from ui import data  # noqa: E402

SOURCE = """public class SeasonSwitch {
   public void cool() {
   }
   public void timerOff() {
   }
   public static void main(String[] args) {
   }
class Room {
   public void actionPerformed(ActionEvent ae) {
   }
}
}
"""
TESTS = """class T {
    // Partition: cool from OFF
    @Test
    void testEPCoolFromOff() {
        ss.cool();
        if (x) { y(); }
    }

    @Test
    void testBVATimerOffExact() {
        ss.timerOff();
    }
}
"""


class ParseTests(unittest.TestCase):
    def test_methods_skip_main_and_keep_inner_long_names(self):
        self.assertEqual(data.public_methods(SOURCE), ["cool", "timerOff", "actionPerformed"])

    def test_tests_are_split_with_kind_comment_and_method(self):
        tests = data.parse_tests(TESTS, ["cool", "timerOff"])
        self.assertEqual([t["name"] for t in tests], ["testEPCoolFromOff", "testBVATimerOffExact"])
        self.assertEqual([t["kind"] for t in tests], ["EP", "BVA"])
        self.assertEqual(tests[0]["comment"], "Partition: cool from OFF")
        self.assertIn("if (x) { y(); }", tests[0]["source"])
        self.assertEqual([t["method"] for t in tests], ["cool", "timerOff"])

    def test_changed_tests_marks_revised_and_new(self):
        old = data.parse_tests(TESTS, ["cool", "timerOff"])
        new = data.parse_tests(TESTS.replace("ss.timerOff();", "ss.timerOff(); z();")
                               .replace("}\n}\n", "}\n    @Test\n    void testEPNew() {\n    }\n}\n"), ["cool", "timerOff"])
        self.assertEqual(data.changed_tests(old, new), {"testBVATimerOffExact": "revised", "testEPNew": "new"})

    def test_new_file_diff_is_all_additions(self):
        diff = data.unified_diff("", "a\nb", "old", "new/State.java")
        self.assertEqual(diff[:3], ["--- (new file)", "+++ new/State.java", "@@ -0,0 +1,2 @@"])
        self.assertEqual(diff[3:], ["+a", "+b"])


class HumanRequestTests(unittest.TestCase):
    """Per-test comments from the dashboard reach only the generator that owns each test.
    review_tests is taken from main.py's source so no Bedrock client is started."""

    @classmethod
    def setUpClass(cls):
        import ast
        path = Path(__file__).resolve().parent.parent / "app" / "main.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "review_tests"]
        cls.code = compile(ast.Module(body=nodes, type_ignores=[]), "app/main.py", "exec")

    def reject(self, feedback, marks, **state):
        import datetime
        import logging
        env = {"AgentState": dict, "log": logging.getLogger("test-ui"), "datetime": datetime.datetime,
               "MAX_HUMAN_REJECTIONS": 3, "OUTPUT_DIR": Path("generated_tests"),
               "repair_log_entry": lambda *a, **k: {},
               "interrupt": lambda payload: {"approved": False, "feedback": feedback, "test_feedback": marks}}
        exec(self.code, env)
        return env["review_tests"]({"class_name": "SeasonSwitch", "phase": "original",
                                    "merged_tests": "@Test", **state})

    def test_each_generator_gets_only_its_own_tests(self):
        update = self.reject("", {"testEPCool": "fix the oracle", "testBVAEdge": ""})
        self.assertIn("- testEPCool: fix the oracle", update["ep_feedback"])
        self.assertNotIn("testBVAEdge", update["ep_feedback"])
        self.assertIn("- testBVAEdge: revise this test", update["bv_feedback"])
        self.assertEqual(update["human_test_feedback"], {"testEPCool": "fix the oracle", "testBVAEdge": ""})

    def test_generator_with_no_flagged_tests_keeps_its_tests(self):
        self.assertIn("unchanged", self.reject("", {"testEPCool": "x"})["bv_feedback"])

    def test_whole_suite_comment_goes_to_both(self):
        update = self.reject("rename everything", {})
        self.assertIn("rename everything", update["ep_feedback"])
        self.assertIn("rename everything", update["bv_feedback"])

    def test_marks_are_ignored_for_a_repair_proposal(self):
        update = self.reject("wrong fix", {"testEPCool": "x"}, review_context="repair",
                             pre_review_tests="@Test")
        self.assertEqual(update["human_test_feedback"], {})
        self.assertNotIn("ep_feedback", update)


class RepairListTests(unittest.TestCase):
    def test_rows_are_filtered_by_kind_and_phase(self):
        live = {"repair_log": [{"kind": "gap", "phase": "original", "outcome": "proposed"},
                               {"kind": "repair", "phase": "refactored", "outcome": "ai_error"}],
                "coverage_rounds_by_phase": {"original": 2}}
        rows, where, limits = data.repair_rows("gap", "original", live)
        self.assertEqual([r["outcome"] for r in rows], ["proposed"])
        self.assertEqual((where, limits), ("this run", {"used": 2}))
        self.assertEqual(data.repair_rows("repair", "original", live)[0], [])

    def test_diff_lines_number_the_new_file(self):
        lines = data.diff_lines("--- a\n+++ b\n@@ -10,2 +10,3 @@\n keep\n-old\n+new\n+more")
        self.assertEqual([(n, style) for n, _, style in lines],
                         [("", "file"), ("", "file"), ("", "hunk"), (10, "plain"), ("", "del"), (11, "add"), (12, "add")])

    def test_configured_scope_is_the_full_program(self):
        self.assertTrue(data.coverage_report("original")["same_scope"])


if __name__ == "__main__":
    unittest.main()
