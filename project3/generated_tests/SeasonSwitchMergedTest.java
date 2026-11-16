package cse4392;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class SeasonSwitchMergedTest {

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
        // 72 > 68 (coolTemp)
        ss.room.temp = 72;
        ss.timerOff();
        assertTrue(ss.ac.isOn);
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
    }

    // Partition: timerOff() when state == COOL and room.temp <= coolTemp (65 <= 68) -> AC turns off
    @Test
    void testEPTimerOffCoolRoomTempAtOrBelowCoolTemp() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.on();
        // 65 <= 68 (coolTemp)
        ss.room.temp = 65;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
    }

    // Partition: timerOff() when state == HEAT and room.temp < heatTemp (74 < 77) -> heater turns on
    @Test
    void testEPTimerOffHeatRoomTempBelowHeatTemp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 74 < 77 (heatTemp)
        ss.room.temp = 74;
        ss.timerOff();
        assertTrue(ss.heater.isOn);
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
    }

    // Partition: timerOff() when state == HEAT and room.temp >= heatTemp (80 >= 77) -> heater turns off
    @Test
    void testEPTimerOffHeatRoomTempAtOrAboveHeatTemp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.on();
        // 80 >= 77 (heatTemp)
        ss.room.temp = 80;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
    }

    // Partition: actionPerformed() delegates to timerOff() when state == COOL and temp > coolTemp
    @Test
    void testEPActionPerformedCoolTempAboveThreshold() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 73 > 68
        ss.room.temp = 73;
        ss.actionPerformed(null);
        assertTrue(ss.ac.isOn);
    }

    // Partition: actionPerformed() delegates to timerOff() when state == HEAT and temp < heatTemp
    @Test
    void testEPActionPerformedHeatTempBelowThreshold() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 75 < 77
        ss.room.temp = 75;
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

    // cool(): state = OFF-1 = -1 (below MIN, invalid) -> no case matches, no-op
    @Test
    void testBVACoolStateMinMinus1() {
        // state = -1, below valid range; no switch case matches -> no-op
        // -1
        SeasonSwitch.state = SeasonSwitch.OFF - 1;
        ss.cool();
        assertEquals(SeasonSwitch.OFF - 1, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // cool(): state = COOL = 1 (middle of valid range) -> no-op
    @Test
    void testBVACoolFromCoolStateMiddle() {
        // state == COOL (1), middle of valid state range; cool() does nothing
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        // unchanged
        assertTrue(ss.ac.isOn);
        // timer was not started by this no-op
        assertFalse(ss.timer.isRunning());
    }

    // cool(): state = HEAT = 2 (MAX of valid range) -> switches to AC
    @Test
    void testBVACoolFromHeatStateMax() {
        // state == HEAT (2), boundary MAX of valid state range
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // cool(): state = HEAT+1 = 3 (above MAX, invalid) -> no case matches, no-op
    @Test
    void testBVACoolStateMaxPlus1() {
        // state = 3, above valid range; no switch case matches -> no-op
        // 3
        SeasonSwitch.state = SeasonSwitch.HEAT + 1;
        ss.cool();
        assertEquals(SeasonSwitch.HEAT + 1, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // heat(): state = OFF-1 = -1 (below MIN, invalid) -> no-op
    @Test
    void testBVAHeatStateMinMinus1() {
        // state = -1, below valid range; no switch case matches -> no-op
        // -1
        SeasonSwitch.state = SeasonSwitch.OFF - 1;
        ss.heat();
        assertEquals(SeasonSwitch.OFF - 1, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // heat(): state = COOL = 1 (middle of valid range) -> switches to heater
    @Test
    void testBVAHeatFromCoolStateMiddle() {
        // state == COOL (1), middle of valid state range
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertFalse(ss.ac.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // heat(): state = HEAT = 2 (MAX of valid range) -> no-op
    @Test
    void testBVAHeatFromHeatStateMax() {
        // state == HEAT (2), boundary MAX of valid state range; heat() does nothing
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        // unchanged
        assertTrue(ss.heater.isOn);
        // timer was not started by this no-op
        assertFalse(ss.timer.isRunning());
    }

    // heat(): state = HEAT+1 = 3 (above MAX, invalid) -> no-op
    @Test
    void testBVAHeatStateMaxPlus1() {
        // state = 3, above valid range; no switch case matches -> no-op
        // 3
        SeasonSwitch.state = SeasonSwitch.HEAT + 1;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT + 1, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // off(): state = OFF-1 = -1 (below MIN, invalid) -> no-op
    @Test
    void testBVAOffStateMinMinus1() {
        // state = -1, below valid range; no switch case matches -> no-op
        // -1
        SeasonSwitch.state = SeasonSwitch.OFF - 1;
        ss.off();
        assertEquals(SeasonSwitch.OFF - 1, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // off(): state = HEAT+1 = 3 (above MAX, invalid) -> no-op
    @Test
    void testBVAOffStateMaxPlus1() {
        // state = 3, above valid range; no switch case matches -> no-op
        // 3
        SeasonSwitch.state = SeasonSwitch.HEAT + 1;
        ss.off();
        assertEquals(SeasonSwitch.HEAT + 1, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // timerOff(): state = OFF-1 = -1 (below MIN, invalid) -> no-op
    @Test
    void testBVATimerOffStateMinMinus1() {
        // state = -1, below valid range; no switch case matches -> no-op
        // -1
        SeasonSwitch.state = SeasonSwitch.OFF - 1;
        ss.ac.isOn = false;
        ss.heater.isOn = false;
        // would trigger ac if COOL
        ss.room.temp = ss.coolTemp + 1;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertEquals(SeasonSwitch.OFF - 1, SeasonSwitch.state);
    }

    // timerOff(): state = OFF = 0 (MIN of valid range) -> no-op
    @Test
    void testBVATimerOffStateOff() {
        // state == OFF; timerOff() hits case OFF: break, no device changes
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.ac.isOn = false;
        ss.heater.isOn = false;
        // would trigger ac if COOL
        ss.room.temp = ss.coolTemp + 1;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
    }

    // timerOff(): state = HEAT+1 = 3 (above MAX, invalid) -> no-op
    @Test
    void testBVATimerOffStateMaxPlus1() {
        // state = 3, above valid range; no switch case matches -> no-op
        // 3
        SeasonSwitch.state = SeasonSwitch.HEAT + 1;
        ss.ac.isOn = false;
        ss.heater.isOn = false;
        // would trigger heater if HEAT
        ss.room.temp = ss.heatTemp - 1;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertEquals(SeasonSwitch.HEAT + 1, SeasonSwitch.state);
    }

    // COOL state, room.temp = coolTemp - 1 = 67: 67 > 68 is FALSE -> ac.off()
    @Test
    void testBVATimerOffCoolTempOneBelowCoolTemp() {
        // room.temp == coolTemp - 1; condition room.temp > coolTemp is FALSE
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        // 67
        ss.room.temp = ss.coolTemp - 1;
        ss.timerOff();
        // ac turned off because 67 > 68 is false
        assertFalse(ss.ac.isOn);
    }

    // COOL state, room.temp = coolTemp = 68: 68 > 68 is FALSE -> ac.off()
    @Test
    void testBVATimerOffCoolTempEqualCoolTemp() {
        // room.temp == coolTemp exactly; condition room.temp > coolTemp is FALSE (strict >)
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        // 68
        ss.room.temp = ss.coolTemp;
        ss.timerOff();
        // ac turned off because 68 > 68 is false
        assertFalse(ss.ac.isOn);
    }

    // COOL state, room.temp = coolTemp + 1 = 69: 69 > 68 is TRUE -> ac.on()
    @Test
    void testBVATimerOffCoolTempOneAboveCoolTemp() {
        // room.temp == coolTemp + 1; condition room.temp > coolTemp is TRUE
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = false;
        // 69
        ss.room.temp = ss.coolTemp + 1;
        ss.timerOff();
        // ac turned on because 69 > 68 is true
        assertTrue(ss.ac.isOn);
    }

    // HEAT state, room.temp = heatTemp - 1 = 76: 76 < 77 is TRUE -> heater.on()
    @Test
    void testBVATimerOffHeatTempOneBelowHeatTemp() {
        // room.temp == heatTemp - 1; condition room.temp < heatTemp is TRUE
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = false;
        // 76
        ss.room.temp = ss.heatTemp - 1;
        ss.timerOff();
        // heater turned on because 76 < 77 is true
        assertTrue(ss.heater.isOn);
    }

    // HEAT state, room.temp = heatTemp = 77: 77 < 77 is FALSE -> heater.off()
    @Test
    void testBVATimerOffHeatTempEqualHeatTemp() {
        // room.temp == heatTemp exactly; condition room.temp < heatTemp is FALSE (strict <)
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        // 77
        ss.room.temp = ss.heatTemp;
        ss.timerOff();
        // heater turned off because 77 < 77 is false
        assertFalse(ss.heater.isOn);
    }

    // HEAT state, room.temp = heatTemp + 1 = 78: 78 < 77 is FALSE -> heater.off()
    @Test
    void testBVATimerOffHeatTempOneAboveHeatTemp() {
        // room.temp == heatTemp + 1; condition room.temp < heatTemp is FALSE
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        // 78
        ss.room.temp = ss.heatTemp + 1;
        ss.timerOff();
        // heater turned off because 78 < 77 is false
        assertFalse(ss.heater.isOn);
    }

    // actionPerformed(): COOL state, room.temp = coolTemp - 1 = 67: FALSE -> ac.off()
    @Test
    void testBVAActionPerformedCoolTempOneBelowCoolTemp() {
        // actionPerformed -> timerOff(); COOL, temp = coolTemp-1 = 67 > 68 FALSE -> ac.off()
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        // 67
        ss.room.temp = ss.coolTemp - 1;
        ss.actionPerformed(null);
        assertFalse(ss.ac.isOn);
    }

    // actionPerformed(): COOL state, room.temp = coolTemp = 68: FALSE -> ac.off()
    @Test
    void testBVAActionPerformedCoolTempEqualCoolTemp() {
        // actionPerformed -> timerOff(); COOL, temp = coolTemp = 68 > 68 FALSE -> ac.off()
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        // 68
        ss.room.temp = ss.coolTemp;
        ss.actionPerformed(null);
        assertFalse(ss.ac.isOn);
    }

    // actionPerformed(): COOL state, room.temp = coolTemp + 1 = 69: TRUE -> ac.on()
    @Test
    void testBVAActionPerformedCoolTempOneAboveCoolTemp() {
        // actionPerformed -> timerOff(); COOL, temp = coolTemp+1 = 69 > 68 TRUE -> ac.on()
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = false;
        // 69
        ss.room.temp = ss.coolTemp + 1;
        ss.actionPerformed(null);
        assertTrue(ss.ac.isOn);
    }

    // actionPerformed(): HEAT state, room.temp = heatTemp - 1 = 76: TRUE -> heater.on()
    @Test
    void testBVAActionPerformedHeatTempOneBelowHeatTemp() {
        // actionPerformed -> timerOff(); HEAT, temp = heatTemp-1 = 76 < 77 TRUE -> heater.on()
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = false;
        // 76
        ss.room.temp = ss.heatTemp - 1;
        ss.actionPerformed(null);
        assertTrue(ss.heater.isOn);
    }

    // actionPerformed(): HEAT state, room.temp = heatTemp = 77: FALSE -> heater.off()
    @Test
    void testBVAActionPerformedHeatTempEqualHeatTemp() {
        // actionPerformed -> timerOff(); HEAT, temp = heatTemp = 77 < 77 FALSE -> heater.off()
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        // 77
        ss.room.temp = ss.heatTemp;
        ss.actionPerformed(null);
        assertFalse(ss.heater.isOn);
    }

    // actionPerformed(): HEAT state, room.temp = heatTemp + 1 = 78: FALSE -> heater.off()
    @Test
    void testBVAActionPerformedHeatTempOneAboveHeatTemp() {
        // actionPerformed -> timerOff(); HEAT, temp = heatTemp+1 = 78 < 77 FALSE -> heater.off()
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        // 78
        ss.room.temp = ss.heatTemp + 1;
        ss.actionPerformed(null);
        assertFalse(ss.heater.isOn);
    }
}
