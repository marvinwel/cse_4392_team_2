"""Safeguards added after the Nova Micro run of 2026-11-16 ended `repair_exhausted`.

1. Every run starts from a clean java-original/SeasonSwitch.java (reset_original_project).
2. AUTO_APPROVE never approves an AI change to the original program (auto_review_answer).

main.py imports Bedrock at module load, so the functions are pulled out with ast,
the same way test_review_stage.py does."""
import ast
import logging
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
from repair_nodes import repair_log_entry  # noqa: E402

NAMES = {"reset_original_project", "is_original_code_repair", "auto_review_answer",
         "review_tests", "AUTO_CODE_REPAIR_FEEDBACK"}


def load(**extra):
    tree = ast.parse((ROOT / "app/main.py").read_text())
    nodes = [n for n in tree.body
             if (isinstance(n, ast.FunctionDef) and n.name in NAMES)
             or (isinstance(n, ast.Assign) and any(getattr(t, "id", "") in NAMES for t in n.targets))]
    env = {"Path": Path, "AgentState": dict, "log": logging.getLogger("test-safeguards"),
           "datetime": datetime, "MAX_HUMAN_REJECTIONS": 3, "repair_log_entry": repair_log_entry,
           "OUTPUT_DIR": ROOT / "generated_tests", **extra}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "app/main.py", "exec"), env)
    return env


class ResetOriginalProjectTests(unittest.TestCase):
    def setUp(self):
        self.reset = load()["reset_original_project"]
        self.dir = Path(tempfile.mkdtemp())
        self.source = self.dir / "SeasonSwitch.java"
        self.source.write_bytes(b"package cse4392;\r\nclass SeasonSwitch {}\r\n")
        self.target = self.dir / "java-original" / "src" / "SeasonSwitch.java"

    def test_changed_copy_is_restored(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_text("package cse4392;\nclass SeasonSwitch { String lastMessage; }\n")
        self.assertTrue(self.reset(self.source, self.target))
        self.assertEqual(self.target.read_bytes(), self.source.read_bytes())

    def test_same_program_with_other_line_endings_is_left_alone(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(b"package cse4392;\nclass SeasonSwitch {}\n")
        self.assertFalse(self.reset(self.source, self.target))
        self.assertEqual(self.target.read_bytes(), b"package cse4392;\nclass SeasonSwitch {}\n")

    def test_missing_copy_is_created(self):
        self.assertTrue(self.reset(self.source, self.target))
        self.assertEqual(self.target.read_bytes(), self.source.read_bytes())

    def test_committed_copy_matches_the_original_program(self):
        """The java-original copy in the repo must be the unmodified program."""
        committed = ROOT / "java-original/src/main/java/cse4392/SeasonSwitch.java"
        self.assertFalse(self.reset(ROOT / "app/SeasonSwitch.java", committed))


class AutoReviewAnswerTests(unittest.TestCase):
    def setUp(self):
        self.env = load()
        self.answer = self.env["auto_review_answer"]

    def test_code_repair_of_original_program_is_rejected_with_feedback(self):
        result = self.answer({"review_context": "repair", "phase": "original",
                              "proposed_target": "SeasonSwitch.java"})
        self.assertFalse(result["approved"])
        self.assertTrue(result["auto"])
        self.assertIn("Fix the TEST", result["feedback"])

    def test_test_repair_and_gap_tests_are_still_approved(self):
        for payload in ({"review_context": "repair", "phase": "original",
                         "proposed_target": "the merged JUnit tests"},
                        {"review_context": "gap", "phase": "original",
                         "proposed_target": "the merged JUnit tests"},
                        {"review_context": "", "phase": "original", "proposed_target": ""}):
            self.assertTrue(self.answer(payload)["approved"], payload)

    def test_code_repair_of_refactored_program_is_still_approved(self):
        result = self.answer({"review_context": "repair", "phase": "refactored",
                              "proposed_target": "CoolState.java"})
        self.assertTrue(result["approved"])

    def test_review_tests_logs_auto_rejection_and_sends_feedback_to_repair(self):
        seen = {}

        def interrupt(payload):
            seen.update(payload)
            return self.answer(payload)

        review = load(interrupt=interrupt)["review_tests"]
        state = {"class_name": "SeasonSwitch", "phase": "original", "review_context": "repair",
                 "merged_tests": "@Test void a() {}", "pre_review_tests": "@Test void a() {}",
                 "pending_code_repair": {"path": "SeasonSwitch.java"},
                 "change_log": [{"diff": "+ lastMessage"}]}
        update = review(state)
        self.assertEqual(seen["phase"], "original")
        self.assertFalse(update["human_approved"])
        self.assertIn("Fix the TEST", update["human_feedback"])
        self.assertIsNone(update["pending_code_repair"])
        self.assertEqual(update["change_log"][0]["action"], "auto_rejected_code_repair")
        self.assertEqual(update["repair_log"][0]["outcome"], "human_rejected")


if __name__ == "__main__":
    unittest.main()
