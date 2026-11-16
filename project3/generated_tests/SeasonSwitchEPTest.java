package cse4392;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class SeasonSwitchEPTest {

    SeasonSwitch ss;

    @BeforeEach
    void setUp() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss = new SeasonSwitch();
    }

    @AfterEach
    void tearDown() {
        ss.timer.stop();
        ss.room.timer.stop();
        SeasonSwitch.state = SeasonSwitch.OFF;
    }

    // --- cool() tests ---

    // Partition: cool() called when state == OFF -> AC turns on, timer starts, state becomes COOL
    @Test
    void testEPCoolFromOff() {
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // Partition: cool() called when state == COOL -> no change (already cooling)
    @Test
    void testEPCoolFromCool() {
        ss.cool(); // move to COOL
        ss.ac.isOn = false; // manually alter to detect no-op
        ss.cool(); // should do nothing
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertFalse(ss.ac.isOn); // unchanged
    }

    // Partition: cool() called when state == HEAT -> heater off, AC on, timer starts, state becomes COOL
    @Test
    void testEPCoolFromHeat() {
        ss.heat(); // move to HEAT
        assertTrue(ss.heater.isOn);
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // --- heat() tests ---

    // Partition: heat() called when state == OFF -> heater turns on, timer starts, state becomes HEAT
    @Test
    void testEPHeatFromOff() {
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertFalse(ss.ac.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // Partition: heat() called when state == HEAT -> no change (already heating)
    @Test
    void testEPHeatFromHeat() {
        ss.heat(); // move to HEAT
        ss.heater.isOn = false; // manually alter to detect no-op
        ss.heat(); // should do nothing
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertFalse(ss.heater.isOn); // unchanged
    }

    // Partition: heat() called when state == COOL -> AC off, heater on, timer starts, state becomes HEAT
    @Test
    void testEPHeatFromCool() {
        ss.cool(); // move to COOL
        assertTrue(ss.ac.isOn);
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertFalse(ss.ac.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // --- off() tests ---

    // Partition: off() called when state == OFF -> no change (already off)
    @Test
    void testEPOffFromOff() {
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // Partition: off() called when state == HEAT -> heater off, timer stops, state becomes OFF
    @Test
    void testEPOffFromHeat() {
        ss.heat(); // move to HEAT
        assertTrue(ss.timer.isRunning());
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // Partition: off() called when state == COOL -> AC off, timer stops, state becomes OFF
    @Test
    void testEPOffFromCool() {
        ss.cool(); // move to COOL
        assertTrue(ss.timer.isRunning());
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // --- timerOff() tests ---

    // Partition: timerOff() when state == OFF -> no change
    @Test
    void testEPTimerOffWhenOff() {
        ss.timerOff();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // Partition: timerOff() when state == COOL and room.temp > coolTemp (72 > 68) -> AC turns on
    @Test
    void testEPTimerOffCoolRoomTempAboveCoolTemp() {
        ss.cool(); // state = COOL
        ss.room.temp = 72; // 72 > 68 (coolTemp), middle of above-threshold class
        ss.timerOff();
        assertTrue(ss.ac.isOn);
    }

    // Partition: timerOff() when state == COOL and room.temp <= coolTemp (65 <= 68) -> AC turns off
    @Test
    void testEPTimerOffCoolRoomTempAtOrBelowCoolTemp() {
        ss.cool(); // state = COOL
        ss.room.temp = 65; // 65 <= 68 (coolTemp), middle of at-or-below class
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // Partition: timerOff() when state == HEAT and room.temp < heatTemp (74 < 77) -> heater turns on
    @Test
    void testEPTimerOffHeatRoomTempBelowHeatTemp() {
        ss.heat(); // state = HEAT
        ss.room.temp = 74; // 74 < 77 (heatTemp), middle of below-threshold class
        ss.timerOff();
        assertTrue(ss.heater.isOn);
    }

    // Partition: timerOff() when state == HEAT and room.temp >= heatTemp (80 >= 77) -> heater turns off
    @Test
    void testEPTimerOffHeatRoomTempAtOrAboveHeatTemp() {
        ss.heat(); // state = HEAT
        ss.room.temp = 80; // 80 >= 77 (heatTemp), middle of at-or-above class
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // --- actionPerformed() tests ---

    // Partition: actionPerformed() delegates to timerOff(); state == COOL, temp > coolTemp -> AC on
    @Test
    void testEPActionPerformedCoolTempAboveThreshold() {
        ss.cool(); // state = COOL
        ss.room.temp = 73; // 73 > 68, middle of above-threshold class
        ss.actionPerformed(null);
        assertTrue(ss.ac.isOn);
    }

    // Partition: actionPerformed() delegates to timerOff(); state == HEAT, temp < heatTemp -> heater on
    @Test
    void testEPActionPerformedHeatTempBelowThreshold() {
        ss.heat(); // state = HEAT
        ss.room.temp = 75; // 75 < 77, middle of below-threshold class
        ss.actionPerformed(null);
        assertTrue(ss.heater.isOn);
    }

    // Partition: actionPerformed() delegates to timerOff(); state == OFF -> no effect
    @Test
    void testEPActionPerformedWhenOff() {
        ss.actionPerformed(null);
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }
}