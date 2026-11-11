package cse4392;

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

public class SeasonSwitchMergedTest {

    SeasonSwitch ss;

    @BeforeEach
    void setUp() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss = new SeasonSwitch();
        // Stop the room timer to prevent background state changes
        ss.room.timer.stop();
        // Ensure timer is stopped before each test
        ss.timer.stop();
    }

    @AfterEach
    void tearDown() {
        ss.timer.stop();
        ss.room.timer.stop();
        SeasonSwitch.state = SeasonSwitch.OFF;
    }

    // Partition: cool() called when state == OFF -> AC turns on, state becomes COOL
    @Test
    void testCoolFromOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // Partition: cool() called when state == COOL -> no change (already cooling)
    @Test
    void testCoolFromCool() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
    }

    // Partition: cool() called when state == HEAT -> heater off, AC on, state becomes COOL
    @Test
    void testCoolFromHeat() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.ac.isOn = false;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // Partition: heat() called when state == OFF -> heater turns on, state becomes HEAT
    @Test
    void testHeatFromOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertFalse(ss.ac.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // Partition: heat() called when state == HEAT -> no change (already heating)
    @Test
    void testHeatFromHeat() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
    }

    // Partition: heat() called when state == COOL -> AC off, heater on, state becomes HEAT
    @Test
    void testHeatFromCool() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.heater.isOn = false;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertFalse(ss.ac.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // Partition: off() called when state == OFF -> no change
    @Test
    void testOffFromOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // Partition: off() called when state == HEAT -> heater off, timer stopped, state becomes OFF
    @Test
    void testOffFromHeat() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.timer.start();
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // Partition: off() called when state == COOL -> AC off, timer stopped, state becomes OFF
    @Test
    void testOffFromCool() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.timer.start();
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // Partition: timerOff() when state == OFF -> no device change
    @Test
    void testTimerOffWhenStateOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.ac.isOn = false;
        ss.heater.isOn = false;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
    }

    // Partition: timerOff() when state == COOL and room.temp > coolTemp (70 > 68) -> AC turns on
    @Test
    void testTimerOffCoolRoomTempAboveCoolTemp() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 72 > 68 (coolTemp)
        ss.room.temp = 72;
        ss.ac.isOn = false;
        ss.timerOff();
        assertTrue(ss.ac.isOn);
    }

    // Partition: timerOff() when state == COOL and room.temp <= coolTemp (65 <= 68) -> AC turns off
    @Test
    void testTimerOffCoolRoomTempAtOrBelowCoolTemp() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 65 <= 68 (coolTemp)
        ss.room.temp = 65;
        ss.ac.isOn = true;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // Partition: timerOff() when state == HEAT and room.temp < heatTemp (74 < 77) -> heater turns on
    @Test
    void testTimerOffHeatRoomTempBelowHeatTemp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 74 < 77 (heatTemp)
        ss.room.temp = 74;
        ss.heater.isOn = false;
        ss.timerOff();
        assertTrue(ss.heater.isOn);
    }

    // Partition: timerOff() when state == HEAT and room.temp >= heatTemp (80 >= 77) -> heater turns off
    @Test
    void testTimerOffHeatRoomTempAtOrAboveHeatTemp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 80 >= 77 (heatTemp)
        ss.room.temp = 80;
        ss.heater.isOn = true;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // Partition: actionPerformed() delegates to timerOff(); state == COOL, temp > coolTemp -> AC on
    @Test
    void testActionPerformedDelegatesToTimerOff() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 75 > 68 (coolTemp)
        ss.room.temp = 75;
        ss.ac.isOn = false;
        ss.actionPerformed(null);
        assertTrue(ss.ac.isOn);
    }

    // Partition: actionPerformed() delegates to timerOff(); state == HEAT, temp >= heatTemp -> heater off
    @Test
    void testActionPerformedDelegatesToTimerOffHeatSatisfied() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 79 >= 77 (heatTemp)
        ss.room.temp = 79;
        ss.heater.isOn = true;
        ss.actionPerformed(null);
        assertFalse(ss.heater.isOn);
    }

    @BeforeEach
    void setUpBVA() {
        // Reset static state before every test
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss = new SeasonSwitch();
        // Ensure timer is not running at start
        ss.timer.stop();
    }

    @AfterEach
    void tearDownBVA() {
        // Stop any timers that may have been started
        ss.timer.stop();
        ss.room.timer.stop();
    }

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
        // 3
        SeasonSwitch.state = SeasonSwitch.HEAT + 1;
        boolean acBefore = ss.ac.isOn;
        ss.cool();
        assertEquals(SeasonSwitch.HEAT + 1, SeasonSwitch.state);
        assertEquals(acBefore, ss.ac.isOn);
    }

    // set state = HEAT
    @Test
    void heat_fromStateOFF_startsHeaterAndSetsHeatState() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

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
        // 3
        SeasonSwitch.state = SeasonSwitch.HEAT + 1;
        boolean heaterBefore = ss.heater.isOn;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT + 1, SeasonSwitch.state);
        assertEquals(heaterBefore, ss.heater.isOn);
    }

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
        // 3
        SeasonSwitch.state = SeasonSwitch.HEAT + 1;
        ss.off();
        assertEquals(SeasonSwitch.HEAT + 1, SeasonSwitch.state);
    }

    // State = OFF: timerOff() is a no-op; AC and heater remain off
    @Test
    void timerOff_stateOFF_noEffect() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // temp = coolTemp - 1 = 67: condition (67 > 68) is FALSE → AC turns OFF
    @Test
    void timerOff_coolState_tempBelowCoolTemp_acTurnsOff() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        // 67
        ss.room.temp = ss.coolTemp - 1;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // temp = coolTemp = 68: condition (68 > 68) is FALSE → AC turns OFF
    @Test
    void timerOff_coolState_tempEqualCoolTemp_acTurnsOff() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        // 68
        ss.room.temp = ss.coolTemp;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // temp = coolTemp + 1 = 69: condition (69 > 68) is TRUE → AC turns ON
    @Test
    void timerOff_coolState_tempAboveCoolTemp_acTurnsOn() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = false;
        // 69
        ss.room.temp = ss.coolTemp + 1;
        ss.timerOff();
        assertTrue(ss.ac.isOn);
    }

    // temp = heatTemp - 1 = 76: condition (76 < 77) is TRUE → heater turns ON
    @Test
    void timerOff_heatState_tempBelowHeatTemp_heaterTurnsOn() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = false;
        // 76
        ss.room.temp = ss.heatTemp - 1;
        ss.timerOff();
        assertTrue(ss.heater.isOn);
    }

    // temp = heatTemp = 77: condition (77 < 77) is FALSE → heater turns OFF
    @Test
    void timerOff_heatState_tempEqualHeatTemp_heaterTurnsOff() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        // 77
        ss.room.temp = ss.heatTemp;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // temp = heatTemp + 1 = 78: condition (78 < 77) is FALSE → heater turns OFF
    @Test
    void timerOff_heatState_tempAboveHeatTemp_heaterTurnsOff() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        // 78
        ss.room.temp = ss.heatTemp + 1;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // State below valid range (state = -1): switch has no default, nothing happens.
    @Test
    void timerOff_stateMinusOne_noEffect() {
        SeasonSwitch.state = -1;
        // would trigger AC if state matched COOL
        ss.room.temp = ss.coolTemp + 1;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // State above valid range (state = 3): switch has no default, nothing happens.
    @Test
    void timerOff_stateThree_noEffect() {
        // 3
        SeasonSwitch.state = SeasonSwitch.HEAT + 1;
        // would trigger heater if state matched HEAT
        ss.room.temp = ss.heatTemp - 1;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

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
