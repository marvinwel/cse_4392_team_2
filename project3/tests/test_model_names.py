"""The log names the model each AI step really uses (read from the model objects, never typed)."""
import ast
import logging
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = (ROOT / "app/main.py").read_text()


def load(*names, **extra):
    tree = ast.parse(SOURCE)
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    env = {"AgentState": dict, **extra}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "app/main.py", "exec"), env)
    return env


class FakeBedrock:
    def __init__(self, model_id):
        self.model_id = model_id


class ModelNameTests(unittest.TestCase):
    def test_reads_the_bedrock_model_id(self):
        name = load("model_name")["model_name"]
        self.assertEqual(name(FakeBedrock("amazon.nova-micro-v1:0")), "amazon.nova-micro-v1:0")
        self.assertEqual(name(object()), "unknown model")

    def test_logged_node_writes_model_and_runs_the_node(self):
        logger = logging.getLogger("test-model-names")
        env = load("logged_node", log=logger,
                   MODELS_USED={"refactor_repair_gap": "us.anthropic.claude-sonnet-4-6"})
        node = env["logged_node"](lambda state: {"ran": state["phase"]}, "REPAIR", "proposing a fix")
        with self.assertLogs(logger, level="INFO") as seen:
            self.assertEqual(node({"phase": "refactored"}), {"ran": "refactored"})
        self.assertIn("[REPAIR] us.anthropic.claude-sonnet-4-6 proposing a fix (refactored phase)",
                      seen.output[0])

    def test_no_model_name_is_typed_into_a_log_line(self):
        for line in SOURCE.splitlines():
            if "log.info(" in line or "log.warning(" in line:
                for word in ("Claude", "Nova", "Gemma", "Qwen"):
                    self.assertNotIn(word, line, line.strip())


if __name__ == "__main__":
    unittest.main()
