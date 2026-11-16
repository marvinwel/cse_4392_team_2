package cse4392;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

import java.awt.event.ActionEvent;

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
    // Valid range: 0..2; invalid below: -1; invalid above: 3
    // -----------------------------------------------------------------------

    // state = HEAT (MAX valid boundary = 2): off() from HEAT should stop heater
    @Test
    void testBVAStateHeatMaxOff() {
        // state == HEAT (2), MAX of valid range
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // state = -1 (MIN-1, invalid): cool() has no case for -1, does nothing
    @Test
    void testBVAStateInvalidBelowMinCool() {
        // state == -1, below valid range; switch has no default, so nothing happens
        SeasonSwitch.state = -1;
        ss.cool();
        assertEquals(-1, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // state = 3 (MAX+1, invalid): heat() has no case for 3, does nothing
    @Test
    void testBVAStateInvalidAboveMaxHeat() {
        // state == 3, above valid range; switch has no default, so nothing happens
        SeasonSwitch.state = 3;
        ss.heat();
        assertEquals(3, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // state = -1 (MIN-1, invalid): off() has no case for -1, does nothing
    @Test
    void testBVAStateInvalidBelowMinOff() {
        SeasonSwitch.state = -1;
        ss.off();
        assertEquals(-1, SeasonSwitch.state);
    }

    // state = 3 (MAX+1, invalid): timerOff() has no case for 3, does nothing
    @Test
    void testBVAStateInvalidAboveMaxTimerOff() {
        SeasonSwitch.state = 3;
        ss.timerOff();
        assertEquals(3, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // -----------------------------------------------------------------------
    // Boundaries for timerOff() COOL branch: room.temp > coolTemp (coolTemp=68)
    // Comparison is strict (>), so at exactly coolTemp the condition is FALSE.
    // Test coolTemp-1=67, coolTemp=68, coolTemp+1=69
    // -----------------------------------------------------------------------

    // room.temp = coolTemp - 1 = 67: condition (67 > 68) is FALSE -> ac.off()
    @Test
    void testBVACoolTempMinusOne() {
        ss.cool();
        ss.room.temp = ss.coolTemp - 1; // 67
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // room.temp = coolTemp = 68: condition (68 > 68) is FALSE -> ac.off()
    @Test
    void testBVACoolTempExact() {
        ss.cool();
        ss.room.temp = ss.coolTemp; // 68, condition is FALSE (strict >)
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // room.temp = coolTemp + 1 = 69: condition (69 > 68) is TRUE -> ac.on()
    @Test
    void testBVACoolTempPlusOne() {
        ss.cool();
        ss.room.temp = ss.coolTemp + 1; // 69, condition is TRUE
        ss.timerOff();
        assertTrue(ss.ac.isOn);
    }

    // -----------------------------------------------------------------------
    // Boundaries for timerOff() HEAT branch: room.temp < heatTemp (heatTemp=77)
    // Comparison is strict (<), so at exactly heatTemp the condition is FALSE.
    // Test heatTemp-1=76, heatTemp=77, heatTemp+1=78
    // -----------------------------------------------------------------------

    // room.temp = heatTemp - 1 = 76: condition (76 < 77) is TRUE -> heater.on()
    @Test
    void testBVAHeatTempMinusOne() {
        ss.heat();
        ss.room.temp = ss.heatTemp - 1; // 76, condition is TRUE
        ss.timerOff();
        assertTrue(ss.heater.isOn);
    }

    // room.temp = heatTemp = 77: condition (77 < 77) is FALSE -> heater.off()
    @Test
    void testBVAHeatTempExact() {
        ss.heat();
        ss.room.temp = ss.heatTemp; // 77, condition is FALSE (strict <)
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // room.temp = heatTemp + 1 = 78: condition (78 < 77) is FALSE -> heater.off()
    @Test
    void testBVAHeatTempPlusOne() {
        ss.heat();
        ss.room.temp = ss.heatTemp + 1; // 78, condition is FALSE
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // -----------------------------------------------------------------------
    // Boundaries for state transitions in cool()
    // -----------------------------------------------------------------------

    // state = OFF (0 = MIN valid): cool() transitions OFF -> COOL
    @Test
    void testBVACoolFromOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // state = COOL (1): cool() is a no-op
    @Test
    void testBVACoolFromCool() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn); // unchanged
    }

    // state = HEAT (2 = MAX valid): cool() transitions HEAT -> COOL
    @Test
    void testBVACoolFromHeat() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertTrue(ss.ac.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // -----------------------------------------------------------------------
    // Boundaries for state transitions in heat()
    // -----------------------------------------------------------------------

    // state = OFF (0 = MIN valid): heat() transitions OFF -> HEAT
    @Test
    void testBVAHeatFromOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // state = HEAT (2 = MAX valid): heat() is a no-op
    @Test
    void testBVAHeatFromHeat() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn); // unchanged
    }

    // state = COOL (1): heat() transitions COOL -> HEAT
    @Test
    void testBVAHeatFromCool() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertTrue(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // -----------------------------------------------------------------------
    // Boundaries for state transitions in off()
    // -----------------------------------------------------------------------

    // state = OFF (0 = MIN valid): off() is a no-op
    @Test
    void testBVAOffFromOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // state = COOL (1): off() transitions COOL -> OFF
    @Test
    void testBVAOffFromCool() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.timer.start();
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // state = HEAT (2 = MAX valid): off() transitions HEAT -> OFF
    @Test
    void testBVAOffFromHeat() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.timer.start();
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // -----------------------------------------------------------------------
    // Boundaries for timerOff() with state = OFF (MIN valid)
    // -----------------------------------------------------------------------

    // state = OFF: timerOff() is a no-op (case OFF: break)
    @Test
    void testBVATimerOffStateOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.timerOff();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // -----------------------------------------------------------------------
    // Additional boundary: timerOff() in COOL state with temp exactly at
    // coolTemp, verify state unchanged
    // -----------------------------------------------------------------------

    // state = COOL, room.temp = coolTemp: ac turns off, state stays COOL
    @Test
    void testBVATimerOffCoolStateUnchanged() {
        ss.cool();
        ss.room.temp = ss.coolTemp; // 68, condition (68>68) FALSE
        ss.timerOff();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
    }

    // state = HEAT, room.temp = heatTemp: heater turns off, state stays HEAT
    @Test
    void testBVATimerOffHeatStateUnchanged() {
        ss.heat();
        ss.room.temp = ss.heatTemp; // 77, condition (77<77) FALSE
        ss.timerOff();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
    }

    // -----------------------------------------------------------------------
    // Boundary: invalid state 3 (MAX+1) passed to off() — no default, does nothing
    // -----------------------------------------------------------------------

    // state = 3 (MAX+1 invalid): off() has no case for 3, does nothing
    @Test
    void testBVAStateInvalidAboveMaxOff() {
        SeasonSwitch.state = 3;
        ss.off();
        assertEquals(3, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // -----------------------------------------------------------------------
    // Boundary: invalid state -1 for timerOff() — no default, does nothing
    // -----------------------------------------------------------------------

    // state = -1 (MIN-1 invalid): timerOff() has no case for -1, does nothing
    @Test
    void testBVAStateInvalidBelowMinTimerOff() {
        SeasonSwitch.state = -1;
        ss.timerOff();
        assertEquals(-1, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // -----------------------------------------------------------------------
    // actionPerformed() delegates to timerOff(): boundary at coolTemp+1
    // state = COOL, room.temp = coolTemp+1 (69 > 68): condition TRUE -> ac.on()
    // actionPerformed() calls timerOff() which turns AC on.
    // -----------------------------------------------------------------------

    // actionPerformed() with COOL state and room.temp > coolTemp: ac turns on
    @Test
    void testBVAActionPerformedCoolTempAboveBoundary() {
        ss.cool();
        ss.room.temp = ss.coolTemp + 1; // 69, condition (69 > 68) is TRUE
        ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, ""));
        assertTrue(ss.ac.isOn);
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
    }
}