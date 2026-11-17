"""Patch F: AI review handoff to the human review, and Java extraction from model replies.

main.py imports Bedrock at module load, so the pure functions are pulled out with ast,
the same way test_repair_nodes.HumanApprovalWiringTests does."""
import ast
import logging
import re
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAMES = {"extract_java", "route_ep_review", "route_bv_review", "review_ep_tests",
         "review_bv_tests", "review_tests"}


def load(**extra):
    tree = ast.parse((ROOT / "app/main.py").read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in NAMES]
    for n in nodes:
        n.decorator_list = []          # drop @traceable
    env = {"re": re, "AgentState": dict, "MAX_REVIEW_REJECTIONS": 3, "MAX_HUMAN_REJECTIONS": 3,
           "log": logging.getLogger("test-review-stage"), "datetime": datetime,
           "json": __import__("json"), "OUTPUT_DIR": ROOT / "generated_tests",
           "MODELS_USED": {"test_generator": "gen", "ai_reviewer": "rev", "refactor_repair_gap": "ref"},
           **extra}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "app/main.py", "exec"), env)
    return env


class FakeChain:
    def __init__(self, reply):
        self.reply = reply

    def invoke(self, _):
        return type("R", (), {"content": self.reply})()


class ExtractJavaTests(unittest.TestCase):
    def setUp(self):
        self.extract = load()["extract_java"]
        self.java = "package cse4392;\n\nclass T {\n}"

    def test_plain_java_unchanged(self):
        self.assertEqual(self.extract(self.java), self.java)

    def test_closed_fence(self):
        self.assertEqual(self.extract("Here:\n```java\n" + self.java + "\n```\nDone"), self.java)

    def test_unclosed_fence_and_prose(self):
        # The merge failure seen on 2026-11-16: a ``` line the old regex did not remove.
        out = self.extract("Sure, here are the tests.\n```java\n" + self.java)
        self.assertEqual(out, self.java)
        self.assertNotIn("`", out)

    def test_longest_block_wins(self):
        reply = "```\nnote\n```\n```java\n" + self.java + "\n```"
        self.assertEqual(self.extract(reply), self.java)


class ReviewHandoffTests(unittest.TestCase):
    def review(self, node, reply, **state):
        prompt = type("P", (), {"__or__": lambda self, model: FakeChain(reply)})()
        env = load(review_prompt=prompt, review_model=None, EP_CHECKS="", BV_CHECKS="")
        base = {"class_name": "SeasonSwitch", "source_code": "", "ep_tests": "", "bv_tests": "",
                "phase": "original"}
        return env[node]({**base, **state}), env

    def test_third_rejection_hands_off_to_human_instead_of_stopping(self):
        result, env = self.review("review_bv_tests", '{"approved": false, "feedback": "add N-1"}',
                                  bv_rejections=2)
        self.assertEqual(result["bv_ai_unresolved"], "add N-1")
        self.assertEqual(result["change_log"][0]["action"], "rejected_handed_to_human")
        self.assertEqual(env["route_bv_review"](result), "handoff")

    def test_earlier_rejection_still_regenerates(self):
        result, env = self.review("review_ep_tests", '{"approved": false, "feedback": "x"}')
        self.assertEqual(result["ep_ai_unresolved"], "")
        self.assertEqual(env["route_ep_review"](result), "regenerate")

    def test_approval_clears_unresolved_note(self):
        result, env = self.review("review_ep_tests", '{"approved": true, "feedback": ""}',
                                  ep_rejections=2, ep_ai_unresolved="old")
        self.assertEqual(result["ep_ai_unresolved"], "")
        self.assertEqual(env["route_ep_review"](result), "approved")

    def test_human_review_shows_the_unresolved_feedback(self):
        seen = {}
        env = load(interrupt=lambda payload: seen.update(payload) or {"approved": True, "feedback": ""},
                   repair_log_entry=lambda *a, **k: {})
        env["review_tests"]({"class_name": "SeasonSwitch", "phase": "original",
                             "merged_tests": "@Test", "bv_ai_unresolved": "add N-1",
                             "ep_ai_unresolved": ""})
        self.assertEqual(seen["ai_review_notes"], {"BVA": "add N-1"})

    def test_graph_routes_handoff_to_done_nodes(self):
        tree = ast.parse((ROOT / "app/main.py").read_text())
        graph = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "build_graph")
        maps = {c.args[0].value: ast.literal_eval(c.args[2]) for c in ast.walk(graph)
                if isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "add_conditional_edges"
                and isinstance(c.args[0], ast.Constant) and c.args[0].value in ("review_ep", "review_bva")}
        self.assertEqual(maps["review_ep"]["handoff"], "ep_done")
        self.assertEqual(maps["review_bva"]["handoff"], "bva_done")
        self.assertNotIn("max_attempts", maps["review_ep"])


if __name__ == "__main__":
    unittest.main()
