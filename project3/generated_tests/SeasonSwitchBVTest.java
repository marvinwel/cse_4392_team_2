package cse4392;

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Boundary Value Analysis tests for SeasonSwitch.
 *
 * Numeric comparisons found in the source:
 *   timerOff/COOL branch : room.temp > coolTemp  (coolTemp = 68)
 *     boundaries: temp = coolTemp-1 (67), temp = coolTemp (68), temp = coolTemp+1 (69)
 *     at exactly coolTemp (68): condition is FALSE (strict >)
 *   timerOff/HEAT branch : room.temp < heatTemp  (heatTemp = 77)
 *     boundaries: temp = heatTemp-1 (76), temp = heatTemp (77), temp = heatTemp+1 (78)
 *     at exactly heatTemp (77): condition is FALSE (strict <)
 *
 * State range: OFF=0, COOL=1, HEAT=2  (valid 0..2)
 *   Invalid state values (below 0, above 2) are tested via direct field assignment;
 *   switch has no default, so nothing happens.
 *
 * Public methods covered: cool(), heat(), off(), timerOff()
 * (main() is excluded per instructions)
 */
class SeasonSwitchBVTest {

    SeasonSwitch ss;

    @BeforeEach
    void setUp() {
        // Reset static state before every test
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss = new SeasonSwitch();
        // Ensure timer is not running at start
        ss.timer.stop();
    }

    @AfterEach
    void tearDown() {
        // Stop any timers that may have been started
        ss.timer.stop();
        ss.room.timer.stop();
    }

    // -----------------------------------------------------------------------
    // cool() — state boundary tests
    // -----------------------------------------------------------------------

    // State = OFF (valid lower bound of state range): cool() should turn AC on,
    // start timer, set state = COOL
    @Test
    void cool_fromStateOFF_startsACAndSetsCoolState() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // State = COOL (mid-range): cool() is a no-op; state and AC unchanged
    @Test
    void cool_fromStateCOOL_noChange() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.timer.start();
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
    }

    // State = HEAT (valid upper bound of state range): cool() should turn heater off,
    // turn AC on, start timer, set state = COOL
    @Test
    void cool_fromStateHEAT_switchesToCool() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // State = HEAT-1 = COOL (already covered above); test state = OFF+1 = COOL (same).
    // State below valid range (state = -1): switch has no default, nothing happens.
    @Test
    void cool_fromStateMinusOne_noEffect() {
        SeasonSwitch.state = -1;
        boolean acBefore = ss.ac.isOn;
        ss.cool();
        // No case matches; state unchanged, AC unchanged
        assertEquals(-1, SeasonSwitch.state);
        assertEquals(acBefore, ss.ac.isOn);
    }

    // State above valid range (state = HEAT+1 = 3): switch has no default, nothing happens.
    @Test
    void cool_fromStateThree_noEffect() {
        SeasonSwitch.state = SeasonSwitch.HEAT + 1; // 3
        boolean acBefore = ss.ac.isOn;
        ss.cool();
        assertEquals(SeasonSwitch.HEAT + 1, SeasonSwitch.state);
        assertEquals(acBefore, ss.ac.isOn);
    }

    // -----------------------------------------------------------------------
    // heat() — state boundary tests
    // -----------------------------------------------------------------------

    // State = OFF (valid lower bound): heat() should turn heater on, start timer,
    // set state = HEAT
    @Test
    void heat_fromStateOFF_startsHeaterAndSetsHeatState() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // State = COOL: heat() should turn AC off, turn heater on, start timer,
    // set state = HEAT
    @Test
    void heat_fromStateCOOL_switchesToHeat() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertFalse(ss.ac.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // State = HEAT (valid upper bound): heat() is a no-op
    @Test
    void heat_fromStateHEAT_noChange() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.timer.start();
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
    }

    // State below valid range (state = -1): switch has no default, nothing happens.
    @Test
    void heat_fromStateMinusOne_noEffect() {
        SeasonSwitch.state = -1;
        boolean heaterBefore = ss.heater.isOn;
        ss.heat();
        assertEquals(-1, SeasonSwitch.state);
        assertEquals(heaterBefore, ss.heater.isOn);
    }

    // State above valid range (state = 3): switch has no default, nothing happens.
    @Test
    void heat_fromStateThree_noEffect() {
        SeasonSwitch.state = SeasonSwitch.HEAT + 1; // 3
        boolean heaterBefore = ss.heater.isOn;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT + 1, SeasonSwitch.state);
        assertEquals(heaterBefore, ss.heater.isOn);
    }

    // -----------------------------------------------------------------------
    // off() — state boundary tests
    // -----------------------------------------------------------------------

    // State = OFF (lower bound): off() is a no-op
    @Test
    void off_fromStateOFF_noChange() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // State = COOL: off() should turn AC off, stop timer, set state = OFF
    @Test
    void off_fromStateCOOL_stopsACAndSetsOff() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.timer.start();
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // State = HEAT (upper bound): off() should turn heater off, stop timer,
    // set state = OFF
    @Test
    void off_fromStateHEAT_stopsHeaterAndSetsOff() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.timer.start();
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // State below valid range (state = -1): switch has no default, nothing happens.
    @Test
    void off_fromStateMinusOne_noEffect() {
        SeasonSwitch.state = -1;
        ss.off();
        assertEquals(-1, SeasonSwitch.state);
    }

    // State above valid range (state = 3): switch has no default, nothing happens.
    @Test
    void off_fromStateThree_noEffect() {
        SeasonSwitch.state = SeasonSwitch.HEAT + 1; // 3
        ss.off();
        assertEquals(SeasonSwitch.HEAT + 1, SeasonSwitch.state);
    }

    // -----------------------------------------------------------------------
    // timerOff() — state = OFF boundary
    // -----------------------------------------------------------------------

    // State = OFF: timerOff() is a no-op; AC and heater remain off
    @Test
    void timerOff_stateOFF_noEffect() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // -----------------------------------------------------------------------
    // timerOff() — COOL branch: room.temp > coolTemp  (coolTemp = 68)
    // Boundary at N = coolTemp (68): condition is FALSE (strict >)
    // -----------------------------------------------------------------------

    // temp = coolTemp - 1 = 67: condition (67 > 68) is FALSE → AC turns OFF
    @Test
    void timerOff_coolState_tempBelowCoolTemp_acTurnsOff() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.room.temp = ss.coolTemp - 1; // 67
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // temp = coolTemp = 68: condition (68 > 68) is FALSE → AC turns OFF
    @Test
    void timerOff_coolState_tempEqualCoolTemp_acTurnsOff() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.room.temp = ss.coolTemp; // 68
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // temp = coolTemp + 1 = 69: condition (69 > 68) is TRUE → AC turns ON
    @Test
    void timerOff_coolState_tempAboveCoolTemp_acTurnsOn() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = false;
        ss.room.temp = ss.coolTemp + 1; // 69
        ss.timerOff();
        assertTrue(ss.ac.isOn);
    }

    // -----------------------------------------------------------------------
    // timerOff() — HEAT branch: room.temp < heatTemp  (heatTemp = 77)
    // Boundary at N = heatTemp (77): condition is FALSE (strict <)
    // -----------------------------------------------------------------------

    // temp = heatTemp - 1 = 76: condition (76 < 77) is TRUE → heater turns ON
    @Test
    void timerOff_heatState_tempBelowHeatTemp_heaterTurnsOn() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = false;
        ss.room.temp = ss.heatTemp - 1; // 76
        ss.timerOff();
        assertTrue(ss.heater.isOn);
    }

    // temp = heatTemp = 77: condition (77 < 77) is FALSE → heater turns OFF
    @Test
    void timerOff_heatState_tempEqualHeatTemp_heaterTurnsOff() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.room.temp = ss.heatTemp; // 77
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // temp = heatTemp + 1 = 78: condition (78 < 77) is FALSE → heater turns OFF
    @Test
    void timerOff_heatState_tempAboveHeatTemp_heaterTurnsOff() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.room.temp = ss.heatTemp + 1; // 78
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // -----------------------------------------------------------------------
    // timerOff() — invalid state values (no default in switch)
    // -----------------------------------------------------------------------

    // State below valid range (state = -1): switch has no default, nothing happens.
    @Test
    void timerOff_stateMinusOne_noEffect() {
        SeasonSwitch.state = -1;
        ss.room.temp = ss.coolTemp + 1; // would trigger AC if state matched COOL
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // State above valid range (state = 3): switch has no default, nothing happens.
    @Test
    void timerOff_stateThree_noEffect() {
        SeasonSwitch.state = SeasonSwitch.HEAT + 1; // 3
        ss.room.temp = ss.heatTemp - 1; // would trigger heater if state matched HEAT
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // -----------------------------------------------------------------------
    // Transition sequences exercising state boundaries
    // -----------------------------------------------------------------------

    // cool() then off(): verifies full COOL→OFF transition at state boundary COOL
    @Test
    void coolThenOff_fullCycleFromOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // heat() then off(): verifies full HEAT→OFF transition at state boundary HEAT
    @Test
    void heatThenOff_fullCycleFromOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // cool() then heat(): COOL→HEAT transition (state boundary COOL→HEAT)
    @Test
    void coolThenHeat_transitionFromCoolToHeat() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertTrue(ss.heater.isOn);
    }

    // heat() then cool(): HEAT→COOL transition (state boundary HEAT→COOL)
    @Test
    void heatThenCool_transitionFromHeatToCool() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertTrue(ss.ac.isOn);
    }
}