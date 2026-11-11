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
    void cool_fromStateCOOL_isNoOp() {
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
    void cool_fromStateHEAT_turnsHeaterOffAndStartsAC() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // State = -1 (below valid minimum, MIN-1): switch has no default; nothing happens
    @Test
    void cool_fromStateMinusOne_noEffect() {
        SeasonSwitch.state = -1;
        ss.ac.isOn = false;
        ss.cool();
        // No case matches; state stays -1, AC stays off
        assertEquals(-1, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
    }

    // State = 3 (above valid maximum, MAX+1): switch has no default; nothing happens
    @Test
    void cool_fromStateThree_noEffect() {
        SeasonSwitch.state = 3;
        ss.ac.isOn = false;
        ss.cool();
        assertEquals(3, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
    }

    // -----------------------------------------------------------------------
    // heat() — state boundary tests
    // -----------------------------------------------------------------------

    // State = OFF (valid lower bound): heat() should turn heater on,
    // start timer, set state = HEAT
    @Test
    void heat_fromStateOFF_startsHeaterAndSetsHeatState() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // State = HEAT (mid-range): heat() is a no-op
    @Test
    void heat_fromStateHEAT_isNoOp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.timer.start();
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
    }

    // State = COOL (valid upper bound): heat() should turn AC off,
    // turn heater on, start timer, set state = HEAT
    @Test
    void heat_fromStateCOOL_turnsACOffAndStartsHeater() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertFalse(ss.ac.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // State = -1 (MIN-1): switch has no default; nothing happens
    @Test
    void heat_fromStateMinusOne_noEffect() {
        SeasonSwitch.state = -1;
        ss.heater.isOn = false;
        ss.heat();
        assertEquals(-1, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
    }

    // State = 3 (MAX+1): switch has no default; nothing happens
    @Test
    void heat_fromStateThree_noEffect() {
        SeasonSwitch.state = 3;
        ss.heater.isOn = false;
        ss.heat();
        assertEquals(3, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
    }

    // -----------------------------------------------------------------------
    // off() — state boundary tests
    // -----------------------------------------------------------------------

    // State = OFF (lower bound): off() is a no-op
    @Test
    void off_fromStateOFF_isNoOp() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
    }

    // State = HEAT: off() should turn heater off, stop timer, set state = OFF
    @Test
    void off_fromStateHEAT_stopsHeaterAndTimer() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.timer.start();
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // State = COOL (upper bound): off() should turn AC off, stop timer, set state = OFF
    @Test
    void off_fromStateCOOL_stopsACAndTimer() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.timer.start();
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // State = -1 (MIN-1): switch has no default; nothing happens
    @Test
    void off_fromStateMinusOne_noEffect() {
        SeasonSwitch.state = -1;
        ss.off();
        assertEquals(-1, SeasonSwitch.state);
    }

    // State = 3 (MAX+1): switch has no default; nothing happens
    @Test
    void off_fromStateThree_noEffect() {
        SeasonSwitch.state = 3;
        ss.off();
        assertEquals(3, SeasonSwitch.state);
    }

    // -----------------------------------------------------------------------
    // timerOff() — state = OFF boundary
    // -----------------------------------------------------------------------

    // State = OFF: timerOff() is a no-op; AC and heater unchanged
    @Test
    void timerOff_stateOFF_isNoOp() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.ac.isOn = false;
        ss.heater.isOn = false;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // -----------------------------------------------------------------------
    // timerOff() — COOL branch: room.temp > coolTemp  (coolTemp = 68)
    // Boundary at N = coolTemp (68): condition (temp > coolTemp) is FALSE at N
    // -----------------------------------------------------------------------

    // temp = coolTemp - 1 = 67: condition (67 > 68) is FALSE → AC turns off
    @Test
    void timerOff_coolState_tempBelowCoolTemp_ACTurnsOff() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.room.temp = ss.coolTemp - 1;   // 67
        ss.ac.isOn = true;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // temp = coolTemp = 68: condition (68 > 68) is FALSE → AC turns off
    @Test
    void timerOff_coolState_tempEqualCoolTemp_ACTurnsOff() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.room.temp = ss.coolTemp;       // 68
        ss.ac.isOn = true;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // temp = coolTemp + 1 = 69: condition (69 > 68) is TRUE → AC turns on
    @Test
    void timerOff_coolState_tempAboveCoolTemp_ACTurnsOn() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.room.temp = ss.coolTemp + 1;   // 69
        ss.ac.isOn = false;
        ss.timerOff();
        assertTrue(ss.ac.isOn);
    }

    // -----------------------------------------------------------------------
    // timerOff() — HEAT branch: room.temp < heatTemp  (heatTemp = 77)
    // Boundary at N = heatTemp (77): condition (temp < heatTemp) is FALSE at N
    // -----------------------------------------------------------------------

    // temp = heatTemp - 1 = 76: condition (76 < 77) is TRUE → heater turns on
    @Test
    void timerOff_heatState_tempBelowHeatTemp_HeaterTurnsOn() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.room.temp = ss.heatTemp - 1;   // 76
        ss.heater.isOn = false;
        ss.timerOff();
        assertTrue(ss.heater.isOn);
    }

    // temp = heatTemp = 77: condition (77 < 77) is FALSE → heater turns off
    @Test
    void timerOff_heatState_tempEqualHeatTemp_HeaterTurnsOff() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.room.temp = ss.heatTemp;       // 77
        ss.heater.isOn = true;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // temp = heatTemp + 1 = 78: condition (78 < 77) is FALSE → heater turns off
    @Test
    void timerOff_heatState_tempAboveHeatTemp_HeaterTurnsOff() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.room.temp = ss.heatTemp + 1;   // 78
        ss.heater.isOn = true;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // -----------------------------------------------------------------------
    // timerOff() — invalid state values (no default in switch)
    // -----------------------------------------------------------------------

    // State = -1 (MIN-1): switch has no default; nothing happens
    @Test
    void timerOff_stateMinusOne_noEffect() {
        SeasonSwitch.state = -1;
        ss.ac.isOn = false;
        ss.heater.isOn = false;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // State = 3 (MAX+1): switch has no default; nothing happens
    @Test
    void timerOff_stateThree_noEffect() {
        SeasonSwitch.state = 3;
        ss.ac.isOn = false;
        ss.heater.isOn = false;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // -----------------------------------------------------------------------
    // Transition: cool() then off() — verifies timer is stopped
    // -----------------------------------------------------------------------

    // cool() starts timer; off() from COOL must stop it (timer boundary: running → stopped)
    @Test
    void coolThenOff_timerStops() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.cool();
        assertTrue(ss.timer.isRunning());
        ss.off();
        assertFalse(ss.timer.isRunning());
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
    }

    // -----------------------------------------------------------------------
    // Transition: heat() then off() — verifies timer is stopped
    // -----------------------------------------------------------------------

    // heat() starts timer; off() from HEAT must stop it
    @Test
    void heatThenOff_timerStops() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.heat();
        assertTrue(ss.timer.isRunning());
        ss.off();
        assertFalse(ss.timer.isRunning());
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
    }
}