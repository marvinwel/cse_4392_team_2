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
    // Valid range: 0..2; invalid below: -1; invalid above: 3
    // -----------------------------------------------------------------------

    // state = OFF (MIN of valid range): cool() from OFF should start AC
    @Test
    void testBVACoolFromOffStateMin() {
        // state == OFF (0), boundary MIN of valid state range
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // state = COOL (middle of valid range): cool() from COOL is no-op
    @Test
    void testBVACoolFromCoolStateMid() {
        // state == COOL (1), middle of valid state range
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
    }

    // state = HEAT (MAX of valid range): cool() from HEAT should switch
    @Test
    void testBVACoolFromHeatStateMax() {
        // state == HEAT (2), boundary MAX of valid state range
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertTrue(ss.ac.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // state = OFF (MIN): heat() from OFF should start heater
    @Test
    void testBVAHeatFromOffStateMin() {
        // state == OFF (0), boundary MIN of valid state range
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // state = HEAT (MAX): heat() from HEAT is no-op
    @Test
    void testBVAHeatFromHeatStateMax() {
        // state == HEAT (2), boundary MAX of valid state range
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
    }

    // state = COOL (middle): heat() from COOL should switch
    @Test
    void testBVAHeatFromCoolStateMid() {
        // state == COOL (1), middle of valid state range
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertTrue(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // state = OFF (MIN): off() from OFF is no-op
    @Test
    void testBVAOffFromOffStateMin() {
        // state == OFF (0), boundary MIN of valid state range
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // state = HEAT (MAX): off() from HEAT should stop heater
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

    // state = COOL (middle): off() from COOL should stop AC
    @Test
    void testBVAOffFromCoolStateMid() {
        // state == COOL (1), middle of valid state range
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.timer.start();
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // state = -1 (MIN-1, invalid): cool() has no matching case, does nothing
    @Test
    void testBVACoolStateInvalidBelowMin() {
        // state == -1, one below MIN of valid state range; switch has no default
        SeasonSwitch.state = -1;
        ss.cool();
        // No case matches; state unchanged, AC stays off
        assertEquals(-1, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // state = 3 (MAX+1, invalid): heat() has no matching case, does nothing
    @Test
    void testBVAHeatStateInvalidAboveMax() {
        // state == 3, one above MAX of valid state range; switch has no default
        SeasonSwitch.state = 3;
        ss.heat();
        // No case matches; state unchanged, heater stays off
        assertEquals(3, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // state = -1 (MIN-1, invalid): off() has no matching case, does nothing
    @Test
    void testBVAOffStateInvalidBelowMin() {
        // state == -1, one below MIN of valid state range; switch has no default
        SeasonSwitch.state = -1;
        ss.off();
        assertEquals(-1, SeasonSwitch.state);
    }

    // state = 3 (MAX+1, invalid): timerOff() has no matching case, does nothing
    @Test
    void testBVATimerOffStateInvalidAboveMax() {
        // state == 3, one above MAX of valid state range; switch has no default
        SeasonSwitch.state = 3;
        ss.timerOff();
        assertEquals(3, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // -----------------------------------------------------------------------
    // Boundaries for timerOff() COOL branch: room.temp > coolTemp (68)
    // Comparison is strict (>), so at exactly coolTemp the condition is FALSE.
    // Test coolTemp-1=67, coolTemp=68, coolTemp+1=69
    // -----------------------------------------------------------------------

    // room.temp = coolTemp - 1 = 67: condition (temp > coolTemp) is FALSE -> AC off
    @Test
    void testBVATimerOffCoolTempMinusOne() {
        // temp=67, coolTemp=68; 67 > 68 is false -> ac.off()
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.room.temp = ss.coolTemp - 1; // 67
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // room.temp = coolTemp = 68: condition (temp > coolTemp) is FALSE (strict >) -> AC off
    @Test
    void testBVATimerOffCoolTempExact() {
        // temp=68, coolTemp=68; 68 > 68 is false -> ac.off()
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.room.temp = ss.coolTemp; // 68
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // room.temp = coolTemp + 1 = 69: condition (temp > coolTemp) is TRUE -> AC on
    @Test
    void testBVATimerOffCoolTempPlusOne() {
        // temp=69, coolTemp=68; 69 > 68 is true -> ac.on()
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.room.temp = ss.coolTemp + 1; // 69
        ss.timerOff();
        assertTrue(ss.ac.isOn);
    }

    // -----------------------------------------------------------------------
    // Boundaries for timerOff() HEAT branch: room.temp < heatTemp (77)
    // Comparison is strict (<), so at exactly heatTemp the condition is FALSE.
    // Test heatTemp-1=76, heatTemp=77, heatTemp+1=78
    // -----------------------------------------------------------------------

    // room.temp = heatTemp - 1 = 76: condition (temp < heatTemp) is TRUE -> heater on
    @Test
    void testBVATimerOffHeatTempMinusOne() {
        // temp=76, heatTemp=77; 76 < 77 is true -> heater.on()
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.room.temp = ss.heatTemp - 1; // 76
        ss.timerOff();
        assertTrue(ss.heater.isOn);
    }

    // room.temp = heatTemp = 77: condition (temp < heatTemp) is FALSE (strict <) -> heater off
    @Test
    void testBVATimerOffHeatTempExact() {
        // temp=77, heatTemp=77; 77 < 77 is false -> heater.off()
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.room.temp = ss.heatTemp; // 77
        ss.heater.isOn = true;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // room.temp = heatTemp + 1 = 78: condition (temp < heatTemp) is FALSE -> heater off
    @Test
    void testBVATimerOffHeatTempPlusOne() {
        // temp=78, heatTemp=77; 78 < 77 is false -> heater.off()
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.room.temp = ss.heatTemp + 1; // 78
        ss.heater.isOn = true;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // -----------------------------------------------------------------------
    // timerOff() when state == OFF: no action taken
    // -----------------------------------------------------------------------

    // state = OFF: timerOff() does nothing (break in switch)
    @Test
    void testBVATimerOffWhenOff() {
        // state == OFF; switch hits case OFF: break -> no side effects
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.timerOff();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // -----------------------------------------------------------------------
    // actionPerformed(ActionEvent) delegates to timerOff(); verify same effects.
    // Boundary: state=COOL, room.temp = coolTemp+1 (69) -> condition TRUE -> ac.on()
    // -----------------------------------------------------------------------

    // actionPerformed() with state=COOL and temp > coolTemp: AC should turn on
    @Test
    void testBVAActionPerformedCoolTempAboveCoolTemp() {
        // actionPerformed delegates to timerOff();
        // state=COOL, temp=69 > coolTemp=68 -> ac.on()
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.room.temp = ss.coolTemp + 1; // 69
        ss.ac.isOn = false;
        ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, ""));
        assertTrue(ss.ac.isOn);
    }
}