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
        assertTrue(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
    }

    // Partition: cool() called when state == COOL -> no change (already cooling)
    @Test
    void testEPCoolFromCool() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.on();
        ss.timer.start();
        ss.cool();
        // State remains COOL, AC still on
        assertTrue(ss.ac.isOn);
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
    }

    // Partition: cool() called when state == HEAT -> heater off, AC on, timer starts, state becomes COOL
    @Test
    void testEPCoolFromHeat() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.on();
        ss.timer.start();
        ss.cool();
        assertFalse(ss.heater.isOn);
        assertTrue(ss.ac.isOn);
        assertTrue(ss.timer.isRunning());
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
    }

    // --- heat() tests ---

    // Partition: heat() called when state == OFF -> heater turns on, timer starts, state becomes HEAT
    @Test
    void testEPHeatFromOff() {
        ss.heat();
        assertTrue(ss.heater.isOn);
        assertFalse(ss.ac.isOn);
        assertTrue(ss.timer.isRunning());
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
    }

    // Partition: heat() called when state == HEAT -> no change (already heating)
    @Test
    void testEPHeatFromHeat() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.on();
        ss.timer.start();
        ss.heat();
        // State remains HEAT, heater still on
        assertTrue(ss.heater.isOn);
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
    }

    // Partition: heat() called when state == COOL -> AC off, heater on, timer starts, state becomes HEAT
    @Test
    void testEPHeatFromCool() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.on();
        ss.timer.start();
        ss.heat();
        assertFalse(ss.ac.isOn);
        assertTrue(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
    }

    // --- off() tests ---

    // Partition: off() called when state == OFF -> no change
    @Test
    void testEPOffFromOff() {
        ss.off();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
    }

    // Partition: off() called when state == HEAT -> heater off, timer stops, state becomes OFF
    @Test
    void testEPOffFromHeat() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.on();
        ss.timer.start();
        ss.off();
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
    }

    // Partition: off() called when state == COOL -> AC off, timer stops, state becomes OFF
    @Test
    void testEPOffFromCool() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.on();
        ss.timer.start();
        ss.off();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.timer.isRunning());
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
    }

    // --- timerOff() tests ---

    // Partition: timerOff() when state == OFF -> no change to AC or heater
    @Test
    void testEPTimerOffStateOff() {
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
    }

    // Partition: timerOff() when state == COOL and room.temp > coolTemp (70 > 68) -> AC turns on
    @Test
    void testEPTimerOffCoolRoomTempAboveCoolTemp() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.room.temp = 72; // 72 > 68 (coolTemp)
        ss.timerOff();
        assertTrue(ss.ac.isOn);
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
    }

    // Partition: timerOff() when state == COOL and room.temp <= coolTemp (65 <= 68) -> AC turns off
    @Test
    void testEPTimerOffCoolRoomTempAtOrBelowCoolTemp() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.on();
        ss.room.temp = 65; // 65 <= 68 (coolTemp)
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
    }

    // Partition: timerOff() when state == HEAT and room.temp < heatTemp (74 < 77) -> heater turns on
    @Test
    void testEPTimerOffHeatRoomTempBelowHeatTemp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.room.temp = 74; // 74 < 77 (heatTemp)
        ss.timerOff();
        assertTrue(ss.heater.isOn);
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
    }

    // Partition: timerOff() when state == HEAT and room.temp >= heatTemp (80 >= 77) -> heater turns off
    @Test
    void testEPTimerOffHeatRoomTempAtOrAboveHeatTemp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.on();
        ss.room.temp = 80; // 80 >= 77 (heatTemp)
        ss.timerOff();
        assertFalse(ss.heater.isOn);
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
    }

    // --- actionPerformed() tests ---

    // Partition: actionPerformed() delegates to timerOff() when state == COOL and temp > coolTemp
    @Test
    void testEPActionPerformedCoolTempAboveThreshold() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.room.temp = 73; // 73 > 68
        ss.actionPerformed(null);
        assertTrue(ss.ac.isOn);
    }

    // Partition: actionPerformed() delegates to timerOff() when state == HEAT and temp < heatTemp
    @Test
    void testEPActionPerformedHeatTempBelowThreshold() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.room.temp = 75; // 75 < 77
        ss.actionPerformed(null);
        assertTrue(ss.heater.isOn);
    }

    // Partition: actionPerformed() delegates to timerOff() when state == OFF -> no device change
    @Test
    void testEPActionPerformedStateOff() {
        ss.actionPerformed(null);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }
}