package cse4392;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

public class SeasonSwitchBVTest {

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

    // -----------------------------------------------------------------------
    // Boundaries for state constants: OFF=0, COOL=1, HEAT=2
    // Valid range MIN=0 (OFF) .. MAX=2 (HEAT).
    // BVA requires testing MIN-1 = -1 and MAX+1 = 3 as out-of-range values.
    // All switch/case blocks have no default, so unmatched values are no-ops.
    // -----------------------------------------------------------------------

    // cool(): state = OFF-1 = -1 (below MIN, invalid) -> no case matches, no-op
    @Test
    void testBVACoolStateMinMinus1() {
        // state = -1, below valid range; no switch case matches -> no-op
        SeasonSwitch.state = SeasonSwitch.OFF - 1; // -1
        ss.cool();
        assertEquals(SeasonSwitch.OFF - 1, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // cool(): state = OFF = 0 (MIN of valid range) -> starts AC
    @Test
    void testBVACoolFromOffStateMin() {
        // state == OFF (0), boundary MIN of valid state range
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // cool(): state = COOL = 1 (middle of valid range) -> no-op
    @Test
    void testBVACoolFromCoolStateMiddle() {
        // state == COOL (1), middle of valid state range; cool() does nothing
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn); // unchanged
        assertFalse(ss.timer.isRunning()); // timer was not started by this no-op
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
        SeasonSwitch.state = SeasonSwitch.HEAT + 1; // 3
        ss.cool();
        assertEquals(SeasonSwitch.HEAT + 1, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // -----------------------------------------------------------------------
    // heat(): state boundaries OFF-1, OFF, COOL, HEAT, HEAT+1
    // -----------------------------------------------------------------------

    // heat(): state = OFF-1 = -1 (below MIN, invalid) -> no-op
    @Test
    void testBVAHeatStateMinMinus1() {
        // state = -1, below valid range; no switch case matches -> no-op
        SeasonSwitch.state = SeasonSwitch.OFF - 1; // -1
        ss.heat();
        assertEquals(SeasonSwitch.OFF - 1, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // heat(): state = OFF = 0 (MIN of valid range) -> starts heater
    @Test
    void testBVAHeatFromOffStateMin() {
        // state == OFF (0), boundary MIN of valid state range
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertFalse(ss.ac.isOn);
        assertTrue(ss.timer.isRunning());
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
        assertTrue(ss.heater.isOn); // unchanged
        assertFalse(ss.timer.isRunning()); // timer was not started by this no-op
    }

    // heat(): state = HEAT+1 = 3 (above MAX, invalid) -> no-op
    @Test
    void testBVAHeatStateMaxPlus1() {
        // state = 3, above valid range; no switch case matches -> no-op
        SeasonSwitch.state = SeasonSwitch.HEAT + 1; // 3
        ss.heat();
        assertEquals(SeasonSwitch.HEAT + 1, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // -----------------------------------------------------------------------
    // off(): state boundaries OFF-1, OFF, COOL, HEAT, HEAT+1
    // -----------------------------------------------------------------------

    // off(): state = OFF-1 = -1 (below MIN, invalid) -> no-op
    @Test
    void testBVAOffStateMinMinus1() {
        // state = -1, below valid range; no switch case matches -> no-op
        SeasonSwitch.state = SeasonSwitch.OFF - 1; // -1
        ss.off();
        assertEquals(SeasonSwitch.OFF - 1, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // off(): state = OFF = 0 (MIN of valid range) -> no-op
    @Test
    void testBVAOffFromOffStateMin() {
        // state == OFF (0), boundary MIN; off() does nothing
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // off(): state = COOL = 1 (middle of valid range) -> stops AC
    @Test
    void testBVAOffFromCoolStateMiddle() {
        // state == COOL (1), middle of valid state range
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.timer.start();
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // off(): state = HEAT = 2 (MAX of valid range) -> stops heater
    @Test
    void testBVAOffFromHeatStateMax() {
        // state == HEAT (2), boundary MAX of valid state range
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.timer.start();
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // off(): state = HEAT+1 = 3 (above MAX, invalid) -> no-op
    @Test
    void testBVAOffStateMaxPlus1() {
        // state = 3, above valid range; no switch case matches -> no-op
        SeasonSwitch.state = SeasonSwitch.HEAT + 1; // 3
        ss.off();
        assertEquals(SeasonSwitch.HEAT + 1, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // -----------------------------------------------------------------------
    // timerOff() state boundary tests: OFF-1, OFF, COOL, HEAT, HEAT+1
    // -----------------------------------------------------------------------

    // timerOff(): state = OFF-1 = -1 (below MIN, invalid) -> no-op
    @Test
    void testBVATimerOffStateMinMinus1() {
        // state = -1, below valid range; no switch case matches -> no-op
        SeasonSwitch.state = SeasonSwitch.OFF - 1; // -1
        ss.ac.isOn = false;
        ss.heater.isOn = false;
        ss.room.temp = ss.coolTemp + 1; // would trigger ac if COOL
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
        ss.room.temp = ss.coolTemp + 1; // would trigger ac if COOL
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
    }

    // timerOff(): state = HEAT+1 = 3 (above MAX, invalid) -> no-op
    @Test
    void testBVATimerOffStateMaxPlus1() {
        // state = 3, above valid range; no switch case matches -> no-op
        SeasonSwitch.state = SeasonSwitch.HEAT + 1; // 3
        ss.ac.isOn = false;
        ss.heater.isOn = false;
        ss.room.temp = ss.heatTemp - 1; // would trigger heater if HEAT
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertEquals(SeasonSwitch.HEAT + 1, SeasonSwitch.state);
    }

    // -----------------------------------------------------------------------
    // timerOff() COOL branch: condition is room.temp > coolTemp (strict >)
    //   coolTemp = 68; test at coolTemp-1 (N-1), coolTemp (N), coolTemp+1 (N+1)
    //   At exactly N=coolTemp: condition is FALSE (strict >)
    // -----------------------------------------------------------------------

    // COOL state, room.temp = coolTemp - 1 = 67: 67 > 68 is FALSE -> ac.off()
    @Test
    void testBVATimerOffCoolTempOneBelowCoolTemp() {
        // room.temp == coolTemp - 1; condition room.temp > coolTemp is FALSE
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.room.temp = ss.coolTemp - 1; // 67
        ss.timerOff();
        assertFalse(ss.ac.isOn); // ac turned off because 67 > 68 is false
    }

    // COOL state, room.temp = coolTemp = 68: 68 > 68 is FALSE -> ac.off()
    @Test
    void testBVATimerOffCoolTempEqualCoolTemp() {
        // room.temp == coolTemp exactly; condition room.temp > coolTemp is FALSE (strict >)
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.room.temp = ss.coolTemp; // 68
        ss.timerOff();
        assertFalse(ss.ac.isOn); // ac turned off because 68 > 68 is false
    }

    // COOL state, room.temp = coolTemp + 1 = 69: 69 > 68 is TRUE -> ac.on()
    @Test
    void testBVATimerOffCoolTempOneAboveCoolTemp() {
        // room.temp == coolTemp + 1; condition room.temp > coolTemp is TRUE
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = false;
        ss.room.temp = ss.coolTemp + 1; // 69
        ss.timerOff();
        assertTrue(ss.ac.isOn); // ac turned on because 69 > 68 is true
    }

    // -----------------------------------------------------------------------
    // timerOff() HEAT branch: condition is room.temp < heatTemp (strict <)
    //   heatTemp = 77; test at heatTemp-1 (N-1), heatTemp (N), heatTemp+1 (N+1)
    //   At exactly N=heatTemp: condition is FALSE (strict <)
    // -----------------------------------------------------------------------

    // HEAT state, room.temp = heatTemp - 1 = 76: 76 < 77 is TRUE -> heater.on()
    @Test
    void testBVATimerOffHeatTempOneBelowHeatTemp() {
        // room.temp == heatTemp - 1; condition room.temp < heatTemp is TRUE
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = false;
        ss.room.temp = ss.heatTemp - 1; // 76
        ss.timerOff();
        assertTrue(ss.heater.isOn); // heater turned on because 76 < 77 is true
    }

    // HEAT state, room.temp = heatTemp = 77: 77 < 77 is FALSE -> heater.off()
    @Test
    void testBVATimerOffHeatTempEqualHeatTemp() {
        // room.temp == heatTemp exactly; condition room.temp < heatTemp is FALSE (strict <)
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.room.temp = ss.heatTemp; // 77
        ss.timerOff();
        assertFalse(ss.heater.isOn); // heater turned off because 77 < 77 is false
    }

    // HEAT state, room.temp = heatTemp + 1 = 78: 78 < 77 is FALSE -> heater.off()
    @Test
    void testBVATimerOffHeatTempOneAboveHeatTemp() {
        // room.temp == heatTemp + 1; condition room.temp < heatTemp is FALSE
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.room.temp = ss.heatTemp + 1; // 78
        ss.timerOff();
        assertFalse(ss.heater.isOn); // heater turned off because 78 < 77 is false
    }

    // -----------------------------------------------------------------------
    // actionPerformed() delegates to timerOff(); it is a distinct public method
    // and requires its own full N-1/N/N+1 boundary coverage for both comparisons.
    // -----------------------------------------------------------------------

    // actionPerformed(): COOL state, room.temp = coolTemp - 1 = 67: FALSE -> ac.off()
    @Test
    void testBVAActionPerformedCoolTempOneBelowCoolTemp() {
        // actionPerformed -> timerOff(); COOL, temp = coolTemp-1 = 67 > 68 FALSE -> ac.off()
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.room.temp = ss.coolTemp - 1; // 67
        ss.actionPerformed(null);
        assertFalse(ss.ac.isOn);
    }

    // actionPerformed(): COOL state, room.temp = coolTemp = 68: FALSE -> ac.off()
    @Test
    void testBVAActionPerformedCoolTempEqualCoolTemp() {
        // actionPerformed -> timerOff(); COOL, temp = coolTemp = 68 > 68 FALSE -> ac.off()
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.room.temp = ss.coolTemp; // 68
        ss.actionPerformed(null);
        assertFalse(ss.ac.isOn);
    }

    // actionPerformed(): COOL state, room.temp = coolTemp + 1 = 69: TRUE -> ac.on()
    @Test
    void testBVAActionPerformedCoolTempOneAboveCoolTemp() {
        // actionPerformed -> timerOff(); COOL, temp = coolTemp+1 = 69 > 68 TRUE -> ac.on()
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = false;
        ss.room.temp = ss.coolTemp + 1; // 69
        ss.actionPerformed(null);
        assertTrue(ss.ac.isOn);
    }

    // actionPerformed(): HEAT state, room.temp = heatTemp - 1 = 76: TRUE -> heater.on()
    @Test
    void testBVAActionPerformedHeatTempOneBelowHeatTemp() {
        // actionPerformed -> timerOff(); HEAT, temp = heatTemp-1 = 76 < 77 TRUE -> heater.on()
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = false;
        ss.room.temp = ss.heatTemp - 1; // 76
        ss.actionPerformed(null);
        assertTrue(ss.heater.isOn);
    }

    // actionPerformed(): HEAT state, room.temp = heatTemp = 77: FALSE -> heater.off()
    @Test
    void testBVAActionPerformedHeatTempEqualHeatTemp() {
        // actionPerformed -> timerOff(); HEAT, temp = heatTemp = 77 < 77 FALSE -> heater.off()
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.room.temp = ss.heatTemp; // 77
        ss.actionPerformed(null);
        assertFalse(ss.heater.isOn);
    }

    // actionPerformed(): HEAT state, room.temp = heatTemp + 1 = 78: FALSE -> heater.off()
    @Test
    void testBVAActionPerformedHeatTempOneAboveHeatTemp() {
        // actionPerformed -> timerOff(); HEAT, temp = heatTemp+1 = 78 < 77 FALSE -> heater.off()
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.room.temp = ss.heatTemp + 1; // 78
        ss.actionPerformed(null);
        assertFalse(ss.heater.isOn);
    }
}