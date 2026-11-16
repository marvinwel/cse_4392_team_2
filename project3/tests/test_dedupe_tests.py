"""Duplicate test-case removal in the merge step (assignment step 3)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from dedupe_tests import remove_duplicate_tests  # noqa: E402

HEADER = """package cse4392;

public class SeasonSwitchMergedTest {

    SeasonSwitch ss;

"""


def java(*methods):
    return HEADER + "\n".join(methods) + "}\n"


EP_COOL_FROM_OFF = """    // Partition: cool() from OFF
    @Test
    void testEPCoolFromOff() {
        ss.cool();
        assertTrue(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
    }
"""

BVA_COOL_FROM_OFF = """    // state = OFF (0): cool() from OFF
    @Test
    void testBVACoolFromOffStateMin() {
        // MIN valid boundary
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.timer.isRunning());
    }
"""


class RemoveDuplicateTests(unittest.TestCase):
    def test_same_setup_and_call_is_one_test_case(self):
        src, pairs = remove_duplicate_tests(java(EP_COOL_FROM_OFF, BVA_COOL_FROM_OFF))
        self.assertEqual(pairs, [{"kept": "testEPCoolFromOff",
                                  "removed": "testBVACoolFromOffStateMin",
                                  "assertions_added": 1}])
        self.assertEqual(src.count("@Test"), 1)
        self.assertNotIn("testBVACoolFromOffStateMin", src)
        self.assertNotIn("state = OFF (0)", src)   # its comment goes with it
        # The check only the removed test had is kept.
        self.assertIn("assertTrue(ss.timer.isRunning());", src)
        self.assertEqual(src.count("assertEquals(SeasonSwitch.COOL"), 1)

    def test_device_on_equals_setting_is_on(self):
        a = """    @Test
    void testA() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.on();
        ss.off();
        assertFalse(ss.ac.isOn);
    }
"""
        b = a.replace("testA", "testB").replace("ss.ac.on();", "ss.ac.isOn = true;")
        src, pairs = remove_duplicate_tests(java(a, b))
        self.assertEqual([p["removed"] for p in pairs], ["testB"])
        self.assertEqual(src.count("@Test"), 1)

    def test_different_inputs_are_kept(self):
        a = """    @Test
    void testAtBoundary() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.room.temp = ss.coolTemp;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }
"""
        b = a.replace("testAtBoundary", "testAbove").replace("ss.coolTemp;", "ss.coolTemp + 1;")
        src, pairs = remove_duplicate_tests(java(a, b))
        self.assertEqual(pairs, [])
        self.assertEqual(src, java(a, b))

    def test_different_starting_timer_is_kept(self):
        a = """    @Test
    void testA() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.on();
        ss.timer.start();
        ss.cool();
        assertTrue(ss.ac.isOn);
    }
"""
        b = a.replace("testA", "testB").replace("        ss.timer.start();\n", "")
        _, pairs = remove_duplicate_tests(java(a, b))
        self.assertEqual(pairs, [])

    def test_tests_with_blocks_are_never_removed(self):
        a = """    @Test
    void testA() {
        Thread t = new Thread(() -> SeasonSwitch.main(new String[0]));
        t.start();
        assertTrue(t.isAlive());
    }
"""
        b = a.replace("testA", "testB")
        _, pairs = remove_duplicate_tests(java(a, b))
        self.assertEqual(pairs, [])

    def test_real_merged_class_from_last_run(self):
        path = ROOT / "generated_tests/SeasonSwitchMergedTest.java"
        if not path.exists():
            self.skipTest("no merged test file")
        original = path.read_text(encoding="utf-8")
        src, pairs = remove_duplicate_tests(original)
        removed = {p["removed"] for p in pairs}
        self.assertEqual(src.count("@Test"), original.count("@Test") - len(pairs))
        for name in removed:
            self.assertNotIn(f"void {name}(", src)
        self.assertEqual(src.count("{"), src.count("}"))
        # Running it again finds nothing more.
        self.assertEqual(remove_duplicate_tests(src)[1], [])


if __name__ == "__main__":
    unittest.main()
