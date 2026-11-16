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

    // room.temp = coolTemp - 1 = 67: condition (temp > coolTemp) is FALSE -> AC off
    @Test
    void testBVATimerOffCoolTempMinusOne() {
        // temp=67, coolTemp=68; 67 > 68 is false -> ac.off()
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 67
        ss.room.temp = ss.coolTemp - 1;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // room.temp = coolTemp = 68: condition (temp > coolTemp) is FALSE (strict >) -> AC off
    @Test
    void testBVATimerOffCoolTempExact() {
        // temp=68, coolTemp=68; 68 > 68 is false -> ac.off()
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 68
        ss.room.temp = ss.coolTemp;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // room.temp = coolTemp + 1 = 69: condition (temp > coolTemp) is TRUE -> AC on
    @Test
    void testBVATimerOffCoolTempPlusOne() {
        // temp=69, coolTemp=68; 69 > 68 is true -> ac.on()
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 69
        ss.room.temp = ss.coolTemp + 1;
        ss.timerOff();
        assertTrue(ss.ac.isOn);
    }

    // room.temp = heatTemp - 1 = 76: condition (temp < heatTemp) is TRUE -> heater on
    @Test
    void testBVATimerOffHeatTempMinusOne() {
        // temp=76, heatTemp=77; 76 < 77 is true -> heater.on()
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 76
        ss.room.temp = ss.heatTemp - 1;
        ss.timerOff();
        assertTrue(ss.heater.isOn);
    }

    // room.temp = heatTemp = 77: condition (temp < heatTemp) is FALSE (strict <) -> heater off
    @Test
    void testBVATimerOffHeatTempExact() {
        // temp=77, heatTemp=77; 77 < 77 is false -> heater.off()
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 77
        ss.room.temp = ss.heatTemp;
        ss.heater.isOn = true;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // room.temp = heatTemp + 1 = 78: condition (temp < heatTemp) is FALSE -> heater off
    @Test
    void testBVATimerOffHeatTempPlusOne() {
        // temp=78, heatTemp=77; 78 < 77 is false -> heater.off()
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 78
        ss.room.temp = ss.heatTemp + 1;
        ss.heater.isOn = true;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

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

    // actionPerformed() with state=COOL and temp > coolTemp: AC should turn on
    @Test
    void testBVAActionPerformedCoolTempAboveCoolTemp() {
        // actionPerformed delegates to timerOff();
        // state=COOL, temp=69 > coolTemp=68 -> ac.on()
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 69
        ss.room.temp = ss.coolTemp + 1;
        ss.ac.isOn = false;
        ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, ""));
        assertTrue(ss.ac.isOn);
    }

    @Test
    void testMainNoArgs() throws Exception {
        ExitTrap.Result r = ExitTrap.runMain(1500);
        assertFalse(r.exitedByItself);
        assertTrue(r.output.contains("Cooling started"));
    }

    @Test
    void testMainArgOff() throws Exception {
        ExitTrap.Result r = ExitTrap.runMain("off");
        assertTrue(r.exitedByItself);
        assertEquals(0, r.exitCode);
        assertTrue(r.output.contains("System off"));
    }

    @Test
    void testMainArgCool() throws Exception {
        ExitTrap.Result r = ExitTrap.runMain(1500, "cool");
        assertFalse(r.exitedByItself);
        assertTrue(r.output.contains("Cooling started"));
    }

    @Test
    void testMainArgUnknown() throws Exception {
        ExitTrap.Result r = ExitTrap.runMain("unknown");
        assertTrue(r.exitedByItself);
        assertEquals(1, r.exitCode);
        assertTrue(r.output.contains("Unknown command"));
    }

    @Test
    void testRoomActionPerformedStateOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        int tempBefore = ss.room.temp;
        ss.room.actionPerformed(null);
        assertEquals(tempBefore, ss.room.temp);
    }

    @Test
    void testRoomActionPerformedCoolAcOn() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        int tempBefore = ss.room.temp;
        ss.room.actionPerformed(null);
        assertEquals(tempBefore - 1, ss.room.temp);
        ss.ac.isOn = false;
        ss.room.actionPerformed(null);
        assertEquals(tempBefore, ss.room.temp);
    }

    @Test
    void testRoomActionPerformedHeatHeaterOn() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        int tempBefore = ss.room.temp;
        ss.room.actionPerformed(null);
        assertEquals(tempBefore + 1, ss.room.temp);
        ss.heater.isOn = false;
        ss.room.actionPerformed(null);
        assertEquals(tempBefore, ss.room.temp);
    }

    @Test
    void testMainArgHeat() throws Exception {
        ExitTrap.Result r = ExitTrap.runMain(1500, "heat");
        assertFalse(r.exitedByItself);
        assertTrue(r.output.contains("Heating started"));
    }

    @Test
    void testRoomActionPerformedInvalidState() {
        SeasonSwitch.state = -1;
        int tempBefore = ss.room.temp;
        ss.room.actionPerformed(null);
        assertEquals(tempBefore, ss.room.temp);
    }
}
