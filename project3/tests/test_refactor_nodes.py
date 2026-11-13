"""Focused tests for Emily's refactor and human-review nodes."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.refactor_nodes import build_refactor_nodes


SOURCE = """package cse4392;
public class SeasonSwitch {
  public void cool() {}
}
"""

APPROVED_TESTS = """package cse4392;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
public class SeasonSwitchMergedTest {
  @Test void coolingStarts() { assertTrue(true); }
  @Test void heatingStops() { assertEquals(1, 1); }
}
"""

ADAPTED_TESTS = """package cse4392;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
public class SeasonSwitchMergedTest {
  @Test void coolingStarts() { assertTrue(true); }
  @Test void heatingStops() { assertEquals(1, 1); }
}
"""


def response(files=None, adapted_tests=ADAPTED_TESTS, explanation="State objects own mode behavior."):
    return SimpleNamespace(content=json.dumps({
        "files": files or {"SeasonSwitch.java": SOURCE},
        "adapted_tests": adapted_tests,
        "explanation": explanation,
    }))


class FakeModel:
    def __init__(self, result=None):
        self.result = result or response()
        self.prompts = []

    def invoke(self, prompt):
        self.prompts.append(prompt)
        return self.result


class RefactorAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.model = FakeModel()
        self.refactor_agent, self.review_refactor = build_refactor_nodes(
            self.model, self.root, lambda _: {"approved": True},
        )
        self.state = {"source_code": SOURCE, "merged_tests": APPROVED_TESTS,
                      "class_name": "SeasonSwitch"}

    def test_generates_safe_java_files_and_adapts_approved_suite(self):
        result = self.refactor_agent(self.state)
        main_path = self.root / "java-refactored/src/main/java/cse4392/SeasonSwitch.java"
        test_path = self.root / "java-refactored/src/test/java/cse4392/SeasonSwitchMergedTest.java"
        self.assertTrue(main_path.is_file())
        self.assertTrue(test_path.is_file())
        self.assertEqual(result["test_class"], "SeasonSwitchMergedTest")
        self.assertEqual(result["merged_tests"], ADAPTED_TESTS)
        self.assertEqual(result["refactor_status"], "awaiting_review")
        self.assertIn("Approved JUnit suite", self.model.prompts[0])

    def test_rejects_path_traversal(self):
        model = FakeModel(response(files={"../../outside.java": SOURCE}))
        refactor_agent, _ = build_refactor_nodes(model, self.root, lambda _: {"approved": True})
        with self.assertRaisesRegex(ValueError, "Unsafe refactored source path"):
            refactor_agent(self.state)
        self.assertFalse((self.root.parent / "outside.java").exists())

    def test_rejects_removed_approved_test(self):
        reduced = ADAPTED_TESTS.replace("  @Test void heatingStops() { assertEquals(1, 1); }\n", "")
        model = FakeModel(response(adapted_tests=reduced))
        refactor_agent, _ = build_refactor_nodes(model, self.root, lambda _: {"approved": True})
        with self.assertRaisesRegex(ValueError, "removed approved test methods"):
            refactor_agent(self.state)

    def test_rejects_reduced_assertion_count(self):
        reduced = ADAPTED_TESTS.replace("assertEquals(1, 1);", "")
        model = FakeModel(response(adapted_tests=reduced))
        refactor_agent, _ = build_refactor_nodes(model, self.root, lambda _: {"approved": True})
        with self.assertRaisesRegex(ValueError, "fewer assertions"):
            refactor_agent(self.state)

    def test_revision_prompt_includes_review_feedback(self):
        first = self.refactor_agent(self.state)
        _, reject_review = build_refactor_nodes(
            self.model, self.root,
            lambda _: {"approved": False, "feedback": "Move transitions into each state."},
        )
        rejected = reject_review({
            **self.state,
            **first,
            "refactor_review_count": 0,
            "refactor_revision_count": 0,
        })
        self.assertFalse(rejected["refactor_approved"])
        revised_state = {**self.state, **first, **rejected}
        self.refactor_agent(revised_state)
        self.assertIn("Move transitions into each state", self.model.prompts[-1])

    def test_rejects_missing_required_inputs(self):
        with self.assertRaisesRegex(ValueError, "requires source_code"):
            self.refactor_agent({"merged_tests": APPROVED_TESTS})
        with self.assertRaisesRegex(ValueError, "requires the approved merged_tests"):
            self.refactor_agent({"source_code": SOURCE})


class ReviewRefactorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.payloads = []

    def make_nodes(self, decision, max_revisions=3):
        def interrupt_fn(payload):
            self.payloads.append(payload)
            return decision
        return build_refactor_nodes(FakeModel(), self.temp.name, interrupt_fn,
                                   max_revisions=max_revisions)[1]

    def state(self):
        return {"class_name": "SeasonSwitch",
                "refactored_files": {"src/main/java/cse4392/SeasonSwitch.java": SOURCE},
                "refactored_tests": ADAPTED_TESTS,
                "refactor_explanation": "Concrete state classes handle transitions."}

    def test_approved_review_releases_suite_for_execution(self):
        result = self.make_nodes({"approved": True})(self.state())
        self.assertTrue(result["refactor_approved"])
        self.assertEqual(result["workflow_status"], "refactor_approved")
        self.assertEqual(result["refactor_review_count"], 1)
        self.assertIn("review_checklist", self.payloads[0])

    def test_rejection_returns_feedback_for_refactor_revision(self):
        result = self.make_nodes({"approved": False, "feedback": "Move transitions into each state."})(self.state())
        self.assertFalse(result["refactor_approved"])
        self.assertEqual(result["refactor_feedback"], "Move transitions into each state.")
        self.assertEqual(result["workflow_status"], "refactor_revision_requested")
        self.assertEqual(result["refactor_revision_count"], 1)

    def test_rejections_stop_at_retry_cap(self):
        state = self.state()
        state["refactor_revision_count"] = 2
        result = self.make_nodes({"approved": False}, max_revisions=3)(state)
        self.assertEqual(result["workflow_status"], "refactor_review_exhausted")
        self.assertEqual(result["refactor_revision_count"], 3)
        self.assertTrue(result["refactor_feedback"])

    def test_requires_explicit_boolean_decision(self):
        for invalid in (None, "approved", {"approved": "yes"}):
            with self.subTest(invalid=invalid):
                review = self.make_nodes(invalid)
                with self.assertRaisesRegex(ValueError, "Resume review_refactor"):
                    review(self.state())

    def test_requires_generated_artifacts(self):
        review = self.make_nodes({"approved": True})
        with self.assertRaisesRegex(ValueError, "requires generated source files"):
            review({})


if __name__ == "__main__":
    unittest.main()
