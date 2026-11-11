package cse4392;

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

public class SeasonSwitchEPTest {

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

    // -----------------------------------------------------------------------
    // cool() tests
    // -----------------------------------------------------------------------

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

    // -----------------------------------------------------------------------
    // heat() tests
    // -----------------------------------------------------------------------

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

    // -----------------------------------------------------------------------
    // off() tests
    // -----------------------------------------------------------------------

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

    // -----------------------------------------------------------------------
    // timerOff() tests
    // -----------------------------------------------------------------------

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
        ss.room.temp = 72; // 72 > 68 (coolTemp)
        ss.ac.isOn = false;
        ss.timerOff();
        assertTrue(ss.ac.isOn);
    }

    // Partition: timerOff() when state == COOL and room.temp <= coolTemp (65 <= 68) -> AC turns off
    @Test
    void testTimerOffCoolRoomTempAtOrBelowCoolTemp() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.room.temp = 65; // 65 <= 68 (coolTemp)
        ss.ac.isOn = true;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // Partition: timerOff() when state == HEAT and room.temp < heatTemp (74 < 77) -> heater turns on
    @Test
    void testTimerOffHeatRoomTempBelowHeatTemp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.room.temp = 74; // 74 < 77 (heatTemp)
        ss.heater.isOn = false;
        ss.timerOff();
        assertTrue(ss.heater.isOn);
    }

    // Partition: timerOff() when state == HEAT and room.temp >= heatTemp (80 >= 77) -> heater turns off
    @Test
    void testTimerOffHeatRoomTempAtOrAboveHeatTemp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.room.temp = 80; // 80 >= 77 (heatTemp)
        ss.heater.isOn = true;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // -----------------------------------------------------------------------
    // actionPerformed() tests
    // -----------------------------------------------------------------------

    // Partition: actionPerformed() delegates to timerOff(); state == COOL, temp > coolTemp -> AC on
    @Test
    void testActionPerformedDelegatesToTimerOff() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.room.temp = 75; // 75 > 68 (coolTemp)
        ss.ac.isOn = false;
        ss.actionPerformed(null);
        assertTrue(ss.ac.isOn);
    }

    // Partition: actionPerformed() delegates to timerOff(); state == HEAT, temp >= heatTemp -> heater off
    @Test
    void testActionPerformedDelegatesToTimerOffHeatSatisfied() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.room.temp = 79; // 79 >= 77 (heatTemp)
        ss.heater.isOn = true;
        ss.actionPerformed(null);
        assertFalse(ss.heater.isOn);
    }
}