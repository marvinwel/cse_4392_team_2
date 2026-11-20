"""The BVA generator and the BVA reviewer must get the same rules.

Before this fix the generator was told to test the state range at OFF-1 and HEAT+1, and
the reviewer flipped between asking for those tests and calling them invented boundaries,
so the BVA tests were rejected 3 times in every run. The prompt strings are read with ast
because main.py imports Bedrock at module load."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def constants():
    tree = ast.parse((ROOT / "app/main.py").read_text(encoding="utf-8"))
    env = {}
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in {"BVA_RULES", "BV_METHOD", "BV_CHECKS"}):
            exec(compile(ast.Module(body=[node], type_ignores=[]), "app/main.py", "exec"), env)
    return env


class BvaRulesTests(unittest.TestCase):
    def setUp(self):
        self.c = constants()

    def test_generator_prompt_holds_the_shared_rules(self):
        method = self.c["BV_METHOD"].format(class_name="SeasonSwitch", bva_rules=self.c["BVA_RULES"])
        self.assertIn(self.c["BVA_RULES"], method)
        self.assertNotIn("{", method)

    def test_reviewer_checks_hold_the_same_rules(self):
        self.assertTrue(self.c["BV_CHECKS"].startswith(self.c["BVA_RULES"]))

    def test_state_range_boundaries_are_required_not_invented(self):
        rules = self.c["BVA_RULES"]
        self.assertIn("OFF - 1 and HEAT + 1", rules)
        self.assertIn("required boundaries, not invented", rules)


if __name__ == "__main__":
    unittest.main()
