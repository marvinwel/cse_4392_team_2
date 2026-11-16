package cse4392;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.awt.event.ActionEvent;

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
    }

    // Partition: timerOff() when state == COOL and room.temp > coolTemp (70 > 68) -> AC turns on
    @Test
    void testEPTimerOffCoolTempAboveCoolThreshold() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 72 > 68 (coolTemp)
        ss.room.temp = 72;
        ss.timerOff();
        assertTrue(ss.ac.isOn);
    }

    // Partition: timerOff() when state == COOL and room.temp <= coolTemp (65 <= 68) -> AC turns off
    @Test
    void testEPTimerOffCoolTempAtOrBelowCoolThreshold() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.on();
        // 65 <= 68 (coolTemp)
        ss.room.temp = 65;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // Partition: timerOff() when state == HEAT and room.temp < heatTemp (74 < 77) -> heater turns on
    @Test
    void testEPTimerOffHeatTempBelowHeatThreshold() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 74 < 77 (heatTemp)
        ss.room.temp = 74;
        ss.timerOff();
        assertTrue(ss.heater.isOn);
    }

    // Partition: timerOff() when state == HEAT and room.temp >= heatTemp (80 >= 77) -> heater turns off
    @Test
    void testEPTimerOffHeatTempAtOrAboveHeatThreshold() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.on();
        // 80 >= 77 (heatTemp)
        ss.room.temp = 80;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // Partition: actionPerformed() delegates to timerOff() when state == COOL and temp > coolTemp
    @Test
    void testEPActionPerformedCoolTempAboveThreshold() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 75 > 68
        ss.room.temp = 75;
        ss.actionPerformed(null);
        assertTrue(ss.ac.isOn);
    }

    // Partition: actionPerformed() delegates to timerOff() when state == HEAT and temp < heatTemp
    @Test
    void testEPActionPerformedHeatTempBelowThreshold() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 73 < 77
        ss.room.temp = 73;
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

    // room.temp = coolTemp - 1 = 67: condition (67 > 68) is FALSE -> ac.off()
    @Test
    void testBVACoolTempMinusOne() {
        ss.cool();
        // 67
        ss.room.temp = ss.coolTemp - 1;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // room.temp = coolTemp = 68: condition (68 > 68) is FALSE -> ac.off()
    @Test
    void testBVACoolTempExact() {
        ss.cool();
        // 68, condition is FALSE (strict >)
        ss.room.temp = ss.coolTemp;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // room.temp = coolTemp + 1 = 69: condition (69 > 68) is TRUE -> ac.on()
    @Test
    void testBVACoolTempPlusOne() {
        ss.cool();
        // 69, condition is TRUE
        ss.room.temp = ss.coolTemp + 1;
        ss.timerOff();
        assertTrue(ss.ac.isOn);
    }

    // room.temp = heatTemp - 1 = 76: condition (76 < 77) is TRUE -> heater.on()
    @Test
    void testBVAHeatTempMinusOne() {
        ss.heat();
        // 76, condition is TRUE
        ss.room.temp = ss.heatTemp - 1;
        ss.timerOff();
        assertTrue(ss.heater.isOn);
    }

    // room.temp = heatTemp = 77: condition (77 < 77) is FALSE -> heater.off()
    @Test
    void testBVAHeatTempExact() {
        ss.heat();
        // 77, condition is FALSE (strict <)
        ss.room.temp = ss.heatTemp;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // room.temp = heatTemp + 1 = 78: condition (78 < 77) is FALSE -> heater.off()
    @Test
    void testBVAHeatTempPlusOne() {
        ss.heat();
        // 78, condition is FALSE
        ss.room.temp = ss.heatTemp + 1;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

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
        // unchanged
        assertTrue(ss.ac.isOn);
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
        // unchanged
        assertTrue(ss.heater.isOn);
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

    // state = OFF: timerOff() is a no-op (case OFF: break)
    @Test
    void testBVATimerOffStateOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.timerOff();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // state = COOL, room.temp = coolTemp: ac turns off, state stays COOL
    @Test
    void testBVATimerOffCoolStateUnchanged() {
        ss.cool();
        // 68, condition (68>68) FALSE
        ss.room.temp = ss.coolTemp;
        ss.timerOff();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
    }

    // state = HEAT, room.temp = heatTemp: heater turns off, state stays HEAT
    @Test
    void testBVATimerOffHeatStateUnchanged() {
        ss.heat();
        // 77, condition (77<77) FALSE
        ss.room.temp = ss.heatTemp;
        ss.timerOff();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
    }

    // state = 3 (MAX+1 invalid): off() has no case for 3, does nothing
    @Test
    void testBVAStateInvalidAboveMaxOff() {
        SeasonSwitch.state = 3;
        ss.off();
        assertEquals(3, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // state = -1 (MIN-1 invalid): timerOff() has no case for -1, does nothing
    @Test
    void testBVAStateInvalidBelowMinTimerOff() {
        SeasonSwitch.state = -1;
        ss.timerOff();
        assertEquals(-1, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // actionPerformed() with COOL state and room.temp > coolTemp: ac turns on
    @Test
    void testBVAActionPerformedCoolTempAboveBoundary() {
        ss.cool();
        // 69, condition (69 > 68) is TRUE
        ss.room.temp = ss.coolTemp + 1;
        ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, ""));
        assertTrue(ss.ac.isOn);
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
    }
}
