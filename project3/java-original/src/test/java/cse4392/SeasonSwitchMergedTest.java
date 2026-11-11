package cse4392;

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

public class SeasonSwitchMergedTest {

    SeasonSwitch ss;

    @BeforeEach
    void setUp() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss = new SeasonSwitch();
        // Stop the room timer so it doesn't interfere with tests
        ss.room.timer.stop();
    }

    @AfterEach
    void tearDown() {
        ss.timer.stop();
        ss.room.timer.stop();
        SeasonSwitch.state = SeasonSwitch.OFF;
    }

    // Partition: cool() called when state == OFF -> AC turns on, timer starts, state becomes COOL
    @Test
    void testCoolFromOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // Partition: cool() called when state == COOL -> no change (already cooling)
    @Test
    void testCoolFromCool() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.on();
        ss.timer.start();
        ss.cool();
        // State remains COOL, AC still on
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
    }

    // Partition: cool() called when state == HEAT -> heater off, AC on, timer starts, state becomes COOL
    @Test
    void testCoolFromHeat() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.on();
        ss.timer.start();
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // Partition: heat() called when state == OFF -> heater turns on, timer starts, state becomes HEAT
    @Test
    void testHeatFromOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // Partition: heat() called when state == HEAT -> no change (already heating)
    @Test
    void testHeatFromHeat() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.on();
        ss.timer.start();
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
    }

    // Partition: heat() called when state == COOL -> AC off, heater on, timer starts, state becomes HEAT
    @Test
    void testHeatFromCool() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.on();
        ss.timer.start();
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
        assertFalse(ss.timer.isRunning());
    }

    // Partition: off() called when state == HEAT -> heater off, timer stops, state becomes OFF
    @Test
    void testOffFromHeat() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.on();
        ss.timer.start();
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // Partition: off() called when state == COOL -> AC off, timer stops, state becomes OFF
    @Test
    void testOffFromCool() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.on();
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
        ss.ac.off();
        ss.heater.off();
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
    }

    // Partition: timerOff() when state == COOL and room.temp > coolTemp (70 > 68) -> AC turns on
    @Test
    void testTimerOffCoolRoomTempAboveCoolTemp() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 70 > 68 (coolTemp)
        ss.room.temp = 70;
        ss.timerOff();
        assertTrue(ss.ac.isOn);
    }

    // Partition: timerOff() when state == COOL and room.temp <= coolTemp (65 <= 68) -> AC turns off
    @Test
    void testTimerOffCoolRoomTempAtOrBelowCoolTemp() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.on();
        // 65 <= 68 (coolTemp)
        ss.room.temp = 65;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // Partition: timerOff() when state == COOL and room.temp == coolTemp (68 == 68) -> AC turns off (not strictly greater)
    @Test
    void testTimerOffCoolRoomTempEqualsCoolTemp() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.on();
        // 68 is NOT > 68, so AC off
        ss.room.temp = 68;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // Partition: timerOff() when state == HEAT and room.temp < heatTemp (74 < 77) -> heater turns on
    @Test
    void testTimerOffHeatRoomTempBelowHeatTemp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 74 < 77 (heatTemp)
        ss.room.temp = 74;
        ss.timerOff();
        assertTrue(ss.heater.isOn);
    }

    // Partition: timerOff() when state == HEAT and room.temp >= heatTemp (80 >= 77) -> heater turns off
    @Test
    void testTimerOffHeatRoomTempAtOrAboveHeatTemp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.on();
        // 80 >= 77 (heatTemp)
        ss.room.temp = 80;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // Partition: timerOff() when state == HEAT and room.temp == heatTemp (77 == 77) -> heater turns off (not strictly less)
    @Test
    void testTimerOffHeatRoomTempEqualsHeatTemp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.on();
        // 77 is NOT < 77, so heater off
        ss.room.temp = 77;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // state == COOL, room.temp > coolTemp -> AC should turn on
    @Test
    void testActionPerformedDelegatesToTimerOff() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 72 > 68 (coolTemp)
        ss.room.temp = 72;
        ss.ac.off();
        ss.actionPerformed(null);
        assertTrue(ss.ac.isOn);
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
    void cool_fromStateCOOL_isNoOp() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.timer.start();
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
    }

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

    // temp = coolTemp - 1 = 67: condition (67 > 68) is FALSE → AC turns off
    @Test
    void timerOff_coolState_tempBelowCoolTemp_ACTurnsOff() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 67
        ss.room.temp = ss.coolTemp - 1;
        ss.ac.isOn = true;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // temp = coolTemp = 68: condition (68 > 68) is FALSE → AC turns off
    @Test
    void timerOff_coolState_tempEqualCoolTemp_ACTurnsOff() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 68
        ss.room.temp = ss.coolTemp;
        ss.ac.isOn = true;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // temp = coolTemp + 1 = 69: condition (69 > 68) is TRUE → AC turns on
    @Test
    void timerOff_coolState_tempAboveCoolTemp_ACTurnsOn() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 69
        ss.room.temp = ss.coolTemp + 1;
        ss.ac.isOn = false;
        ss.timerOff();
        assertTrue(ss.ac.isOn);
    }

    // temp = heatTemp - 1 = 76: condition (76 < 77) is TRUE → heater turns on
    @Test
    void timerOff_heatState_tempBelowHeatTemp_HeaterTurnsOn() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 76
        ss.room.temp = ss.heatTemp - 1;
        ss.heater.isOn = false;
        ss.timerOff();
        assertTrue(ss.heater.isOn);
    }

    // temp = heatTemp = 77: condition (77 < 77) is FALSE → heater turns off
    @Test
    void timerOff_heatState_tempEqualHeatTemp_HeaterTurnsOff() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 77
        ss.room.temp = ss.heatTemp;
        ss.heater.isOn = true;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // temp = heatTemp + 1 = 78: condition (78 < 77) is FALSE → heater turns off
    @Test
    void timerOff_heatState_tempAboveHeatTemp_HeaterTurnsOff() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 78
        ss.room.temp = ss.heatTemp + 1;
        ss.heater.isOn = true;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

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
