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
    // cool() — valid state boundaries: OFF=0, COOL=1, HEAT=2
    // -----------------------------------------------------------------------

    // state = OFF (0): cool() from OFF should start AC and timer, set state=COOL
    @Test
    void testBVACoolFromOffStateMin() {
        // state == OFF (0), MIN valid boundary
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // state = COOL (1): cool() from COOL is no-op
    @Test
    void testBVACoolFromCoolStateMid() {
        // state == COOL (1), mid valid boundary
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
    }

    // state = HEAT (2): cool() from HEAT should turn off heater, start AC, set state=COOL
    @Test
    void testBVACoolFromHeatStateMax() {
        // state == HEAT (2), MAX valid boundary
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertTrue(ss.ac.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // -----------------------------------------------------------------------
    // heat() — valid state boundaries: OFF=0, COOL=1, HEAT=2
    // -----------------------------------------------------------------------

    // state = OFF (0): heat() from OFF should start heater and timer, set state=HEAT
    @Test
    void testBVAHeatFromOffStateMin() {
        // state == OFF (0), MIN valid boundary
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // state = HEAT (2): heat() from HEAT is no-op
    @Test
    void testBVAHeatFromHeatStateMax() {
        // state == HEAT (2), MAX valid boundary
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
    }

    // state = COOL (1): heat() from COOL should turn off AC, start heater, set state=HEAT
    @Test
    void testBVAHeatFromCoolStateMid() {
        // state == COOL (1), mid valid boundary
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertTrue(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // -----------------------------------------------------------------------
    // off() — valid state boundaries: OFF=0, COOL=1, HEAT=2
    // -----------------------------------------------------------------------

    // state = OFF (0): off() from OFF is no-op
    @Test
    void testBVAOffFromOffStateMin() {
        // state == OFF (0), MIN valid boundary; off() is no-op
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.timer.isRunning());
    }

    // state = COOL (1): off() from COOL stops AC and timer, sets state=OFF
    @Test
    void testBVAOffFromCoolStateMid() {
        // state == COOL (1), mid valid boundary
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.timer.start();
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // state = HEAT (2): off() from HEAT stops heater and timer, sets state=OFF
    @Test
    void testBVAOffFromHeatStateMax() {
        // state == HEAT (2), MAX valid boundary
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.timer.start();
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // -----------------------------------------------------------------------
    // timerOff() in COOL state: condition is room.temp > coolTemp (strict >)
    // coolTemp = 68; test at coolTemp-1=67, coolTemp=68, coolTemp+1=69
    // At exactly coolTemp (68): 68 > 68 is FALSE => ac.off()
    // -----------------------------------------------------------------------

    // room.temp = coolTemp - 1 = 67: 67 > 68 is FALSE => ac.off()
    @Test
    void testBVATimerOffCoolTempBelowBoundary() {
        // room.temp = coolTemp - 1; condition room.temp > coolTemp is FALSE
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.room.temp = ss.coolTemp - 1; // 67
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // room.temp = coolTemp = 68: 68 > 68 is FALSE (strict >) => ac.off()
    @Test
    void testBVATimerOffCoolTempAtBoundary() {
        // room.temp = coolTemp exactly; condition room.temp > coolTemp is FALSE (strict >)
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.room.temp = ss.coolTemp; // 68
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // room.temp = coolTemp + 1 = 69: 69 > 68 is TRUE => ac.on()
    @Test
    void testBVATimerOffCoolTempAboveBoundary() {
        // room.temp = coolTemp + 1; condition room.temp > coolTemp is TRUE
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.room.temp = ss.coolTemp + 1; // 69
        ss.timerOff();
        assertTrue(ss.ac.isOn);
    }

    // -----------------------------------------------------------------------
    // timerOff() in HEAT state: condition is room.temp < heatTemp (strict <)
    // heatTemp = 77; test at heatTemp-1=76, heatTemp=77, heatTemp+1=78
    // At exactly heatTemp (77): 77 < 77 is FALSE => heater.off()
    // -----------------------------------------------------------------------

    // room.temp = heatTemp - 1 = 76: 76 < 77 is TRUE => heater.on()
    @Test
    void testBVATimerOffHeatTempBelowBoundary() {
        // room.temp = heatTemp - 1; condition room.temp < heatTemp is TRUE
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.room.temp = ss.heatTemp - 1; // 76
        ss.timerOff();
        assertTrue(ss.heater.isOn);
    }

    // room.temp = heatTemp = 77: 77 < 77 is FALSE (strict <) => heater.off()
    @Test
    void testBVATimerOffHeatTempAtBoundary() {
        // room.temp = heatTemp exactly; condition room.temp < heatTemp is FALSE (strict <)
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.room.temp = ss.heatTemp; // 77
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // room.temp = heatTemp + 1 = 78: 78 < 77 is FALSE => heater.off()
    @Test
    void testBVATimerOffHeatTempAboveBoundary() {
        // room.temp = heatTemp + 1; condition room.temp < heatTemp is FALSE
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.room.temp = ss.heatTemp + 1; // 78
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // -----------------------------------------------------------------------
    // timerOff() with state = OFF: no-op
    // -----------------------------------------------------------------------

    // state = OFF: timerOff() does nothing
    @Test
    void testBVATimerOffStateOff() {
        // state == OFF; timerOff() switch hits OFF case: break, no side effects
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // -----------------------------------------------------------------------
    // actionPerformed() delegates to timerOff(); verify via observable state
    // -----------------------------------------------------------------------

    // actionPerformed() in COOL state with room.temp > coolTemp => ac.on()
    @Test
    void testBVAActionPerformedCoolTempAboveBoundary() {
        // actionPerformed calls timerOff(); room.temp = coolTemp+1 => 69 > 68 TRUE => ac.on()
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.room.temp = ss.coolTemp + 1; // 69
        ss.actionPerformed(null);
        assertTrue(ss.ac.isOn);
    }

    // actionPerformed() in COOL state with room.temp = coolTemp => ac.off()
    @Test
    void testBVAActionPerformedCoolTempAtBoundary() {
        // actionPerformed calls timerOff(); room.temp = coolTemp exactly => 68 > 68 FALSE => ac.off()
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.room.temp = ss.coolTemp; // 68
        ss.actionPerformed(null);
        assertFalse(ss.ac.isOn);
    }

    // actionPerformed() in COOL state with room.temp = coolTemp - 1 => ac.off()
    @Test
    void testBVAActionPerformedCoolTempBelowBoundary() {
        // actionPerformed calls timerOff(); room.temp = coolTemp-1 => 67 > 68 FALSE => ac.off()
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.room.temp = ss.coolTemp - 1; // 67
        ss.actionPerformed(null);
        assertFalse(ss.ac.isOn);
    }

    // actionPerformed() in HEAT state with room.temp < heatTemp => heater.on()
    @Test
    void testBVAActionPerformedHeatTempBelowBoundary() {
        // actionPerformed calls timerOff(); room.temp = heatTemp-1 => 76 < 77 TRUE => heater.on()
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.room.temp = ss.heatTemp - 1; // 76
        ss.actionPerformed(null);
        assertTrue(ss.heater.isOn);
    }

    // actionPerformed() in HEAT state with room.temp = heatTemp => heater.off()
    @Test
    void testBVAActionPerformedHeatTempAtBoundary() {
        // actionPerformed calls timerOff(); room.temp = heatTemp exactly => 77 < 77 FALSE => heater.off()
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.room.temp = ss.heatTemp; // 77
        ss.actionPerformed(null);
        assertFalse(ss.heater.isOn);
    }

    // actionPerformed() in HEAT state with room.temp = heatTemp + 1 => heater.off()
    @Test
    void testBVAActionPerformedHeatTempAboveBoundary() {
        // actionPerformed calls timerOff(); room.temp = heatTemp+1 => 78 < 77 FALSE => heater.off()
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.room.temp = ss.heatTemp + 1; // 78
        ss.actionPerformed(null);
        assertFalse(ss.heater.isOn);
    }
}