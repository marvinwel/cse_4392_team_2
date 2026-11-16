package cse4392;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.awt.event.ActionEvent;

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
    // These are discrete switch-case values, not a numeric range comparison.
    // Tests cover each valid state value for each public method.
    // -----------------------------------------------------------------------

    // state = OFF: cool() from OFF should start AC and set state to COOL
    @Test
    void testBVACoolFromOffStateMin() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // state = COOL: cool() from COOL is a no-op
    @Test
    void testBVACoolFromCoolStateMiddle() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn); // unchanged
    }

    // state = HEAT: cool() from HEAT should turn off heater, turn on AC, set state to COOL
    @Test
    void testBVACoolFromHeatStateMax() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // state = OFF: heat() from OFF should start heater and set state to HEAT
    @Test
    void testBVAHeatFromOffStateMin() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // state = HEAT: heat() from HEAT is a no-op
    @Test
    void testBVAHeatFromHeatStateMax() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn); // unchanged
    }

    // state = COOL: heat() from COOL should turn off AC, turn on heater, set state to HEAT
    @Test
    void testBVAHeatFromCoolStateMiddle() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertFalse(ss.ac.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // state = OFF: off() from OFF is a no-op (case OFF: break)
    @Test
    void testBVAOffFromOffStateMin() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // state = HEAT: off() from HEAT should stop heater and timer, set state to OFF
    @Test
    void testBVAOffFromHeatStateMax() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.timer.start();
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // state = COOL: off() from COOL should stop AC and timer, set state to OFF
    @Test
    void testBVAOffFromCoolStateMiddle() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.timer.start();
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // -----------------------------------------------------------------------
    // Boundaries for timerOff() COOL branch: room.temp > coolTemp (68)
    // Condition is TRUE when room.temp > 68 (strict greater-than).
    // Boundary N = coolTemp = 68
    // -----------------------------------------------------------------------

    // room.temp = coolTemp - 1 = 67: condition (temp > coolTemp) is FALSE -> ac.off()
    @Test
    void testBVATimerOffCoolTempMinusOne() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.room.temp = ss.coolTemp - 1; // 67, 67 > 68 is FALSE
        ss.timerOff();
        assertFalse(ss.ac.isOn); // ac turned off
    }

    // room.temp = coolTemp = 68: condition (temp > coolTemp) is FALSE at exactly N -> ac.off()
    @Test
    void testBVATimerOffCoolTempAtBoundary() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.room.temp = ss.coolTemp; // 68, 68 > 68 is FALSE (strict >)
        ss.timerOff();
        assertFalse(ss.ac.isOn); // ac turned off
    }

    // room.temp = coolTemp + 1 = 69: condition (temp > coolTemp) is TRUE -> ac.on()
    @Test
    void testBVATimerOffCoolTempPlusOne() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.room.temp = ss.coolTemp + 1; // 69, 69 > 68 is TRUE
        ss.timerOff();
        assertTrue(ss.ac.isOn); // ac turned on
    }

    // -----------------------------------------------------------------------
    // Boundaries for timerOff() HEAT branch: room.temp < heatTemp (77)
    // Condition is TRUE when room.temp < 77 (strict less-than).
    // Boundary N = heatTemp = 77
    // -----------------------------------------------------------------------

    // room.temp = heatTemp - 1 = 76: condition (temp < heatTemp) is TRUE -> heater.on()
    @Test
    void testBVATimerOffHeatTempMinusOne() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.room.temp = ss.heatTemp - 1; // 76, 76 < 77 is TRUE
        ss.timerOff();
        assertTrue(ss.heater.isOn); // heater turned on
    }

    // room.temp = heatTemp = 77: condition (temp < heatTemp) is FALSE at exactly N -> heater.off()
    @Test
    void testBVATimerOffHeatTempAtBoundary() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.room.temp = ss.heatTemp; // 77, 77 < 77 is FALSE (strict <)
        ss.timerOff();
        assertFalse(ss.heater.isOn); // heater turned off
    }

    // room.temp = heatTemp + 1 = 78: condition (temp < heatTemp) is FALSE -> heater.off()
    @Test
    void testBVATimerOffHeatTempPlusOne() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.room.temp = ss.heatTemp + 1; // 78, 78 < 77 is FALSE
        ss.timerOff();
        assertFalse(ss.heater.isOn); // heater turned off
    }

    // -----------------------------------------------------------------------
    // timerOff() with state = OFF: case OFF: break — exists and does nothing
    // -----------------------------------------------------------------------

    // state = OFF: timerOff() hits case OFF: break, no device changes
    @Test
    void testBVATimerOffStateOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.room.temp = ss.coolTemp + 1; // would trigger AC if in COOL
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
    }

    // -----------------------------------------------------------------------
    // Boundary: verify timer starts on cool() from OFF (timer was stopped)
    // -----------------------------------------------------------------------

    @Test
    void testBVACoolTimerStartsFromOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        assertFalse(ss.timer.isRunning());
        ss.cool();
        assertTrue(ss.timer.isRunning());
    }

    // -----------------------------------------------------------------------
    // Boundary: verify timer starts on heat() from OFF (timer was stopped)
    // -----------------------------------------------------------------------

    @Test
    void testBVAHeatTimerStartsFromOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        assertFalse(ss.timer.isRunning());
        ss.heat();
        assertTrue(ss.timer.isRunning());
    }

    // -----------------------------------------------------------------------
    // Boundary: off() from COOL stops timer (timer was running)
    // -----------------------------------------------------------------------

    @Test
    void testBVAOffTimerStopsFromCool() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.timer.start();
        assertTrue(ss.timer.isRunning());
        ss.off();
        assertFalse(ss.timer.isRunning());
    }

    // -----------------------------------------------------------------------
    // Boundary: off() from HEAT stops timer (timer was running)
    // -----------------------------------------------------------------------

    @Test
    void testBVAOffTimerStopsFromHeat() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.timer.start();
        assertTrue(ss.timer.isRunning());
        ss.off();
        assertFalse(ss.timer.isRunning());
    }

    // -----------------------------------------------------------------------
    // actionPerformed() delegates to timerOff(): verify via COOL state with
    // room.temp > coolTemp — condition TRUE, so ac.on() should be called.
    // actionPerformed() is a public method and must be covered.
    // -----------------------------------------------------------------------

    // state = COOL, room.temp = coolTemp + 1 (69 > 68, TRUE): actionPerformed
    // calls timerOff() which calls ac.on()
    @Test
    void testBVAActionPerformedCoolTempAboveCoolTemp() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.room.temp = ss.coolTemp + 1; // 69 > 68, condition TRUE -> ac.on()
        ss.ac.isOn = false;
        ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, ""));
        assertTrue(ss.ac.isOn); // timerOff() turned AC on
        assertFalse(ss.heater.isOn);
    }

    // state = HEAT, room.temp = heatTemp - 1 (76 < 77, TRUE): actionPerformed
    // calls timerOff() which calls heater.on()
    @Test
    void testBVAActionPerformedHeatTempBelowHeatTemp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.room.temp = ss.heatTemp - 1; // 76 < 77, condition TRUE -> heater.on()
        ss.heater.isOn = false;
        ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, ""));
        assertTrue(ss.heater.isOn); // timerOff() turned heater on
        assertFalse(ss.ac.isOn);
    }

    // state = COOL, room.temp = coolTemp (68, NOT > 68, FALSE): actionPerformed
    // calls timerOff() which calls ac.off()
    @Test
    void testBVAActionPerformedCoolTempAtCoolBoundary() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.room.temp = ss.coolTemp; // 68, 68 > 68 is FALSE -> ac.off()
        ss.ac.isOn = true;
        ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, ""));
        assertFalse(ss.ac.isOn); // timerOff() turned AC off
    }

    // state = HEAT, room.temp = heatTemp (77, NOT < 77, FALSE): actionPerformed
    // calls timerOff() which calls heater.off()
    @Test
    void testBVAActionPerformedHeatTempAtHeatBoundary() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.room.temp = ss.heatTemp; // 77, 77 < 77 is FALSE -> heater.off()
        ss.heater.isOn = true;
        ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, ""));
        assertFalse(ss.heater.isOn); // timerOff() turned heater off
    }
}