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
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // Partition: cool() called when state == COOL -> no change (already cooling)
    @Test
    void testEPCoolFromCool() {
        // move to COOL
        ss.cool();
        // manually alter to detect no-op
        ss.ac.isOn = false;
        // should do nothing
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        // unchanged
        assertFalse(ss.ac.isOn);
    }

    // Partition: cool() called when state == HEAT -> heater off, AC on, timer starts, state becomes COOL
    @Test
    void testEPCoolFromHeat() {
        // move to HEAT
        ss.heat();
        assertTrue(ss.heater.isOn);
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // Partition: heat() called when state == OFF -> heater turns on, timer starts, state becomes HEAT
    @Test
    void testEPHeatFromOff() {
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertFalse(ss.ac.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // Partition: heat() called when state == HEAT -> no change (already heating)
    @Test
    void testEPHeatFromHeat() {
        // move to HEAT
        ss.heat();
        // manually alter to detect no-op
        ss.heater.isOn = false;
        // should do nothing
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        // unchanged
        assertFalse(ss.heater.isOn);
    }

    // Partition: heat() called when state == COOL -> AC off, heater on, timer starts, state becomes HEAT
    @Test
    void testEPHeatFromCool() {
        // move to COOL
        ss.cool();
        assertTrue(ss.ac.isOn);
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertFalse(ss.ac.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // Partition: off() called when state == OFF -> no change (already off)
    @Test
    void testEPOffFromOff() {
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // Partition: off() called when state == HEAT -> heater off, timer stops, state becomes OFF
    @Test
    void testEPOffFromHeat() {
        // move to HEAT
        ss.heat();
        assertTrue(ss.timer.isRunning());
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // Partition: off() called when state == COOL -> AC off, timer stops, state becomes OFF
    @Test
    void testEPOffFromCool() {
        // move to COOL
        ss.cool();
        assertTrue(ss.timer.isRunning());
        ss.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // Partition: timerOff() when state == OFF -> no change
    @Test
    void testEPTimerOffWhenOff() {
        ss.timerOff();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // Partition: timerOff() when state == COOL and room.temp > coolTemp (72 > 68) -> AC turns on
    @Test
    void testEPTimerOffCoolRoomTempAboveCoolTemp() {
        // state = COOL
        ss.cool();
        // 72 > 68 (coolTemp), middle of above-threshold class
        ss.room.temp = 72;
        ss.timerOff();
        assertTrue(ss.ac.isOn);
    }

    // Partition: timerOff() when state == COOL and room.temp <= coolTemp (65 <= 68) -> AC turns off
    @Test
    void testEPTimerOffCoolRoomTempAtOrBelowCoolTemp() {
        // state = COOL
        ss.cool();
        // 65 <= 68 (coolTemp), middle of at-or-below class
        ss.room.temp = 65;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // Partition: timerOff() when state == HEAT and room.temp < heatTemp (74 < 77) -> heater turns on
    @Test
    void testEPTimerOffHeatRoomTempBelowHeatTemp() {
        // state = HEAT
        ss.heat();
        // 74 < 77 (heatTemp), middle of below-threshold class
        ss.room.temp = 74;
        ss.timerOff();
        assertTrue(ss.heater.isOn);
    }

    // Partition: timerOff() when state == HEAT and room.temp >= heatTemp (80 >= 77) -> heater turns off
    @Test
    void testEPTimerOffHeatRoomTempAtOrAboveHeatTemp() {
        // state = HEAT
        ss.heat();
        // 80 >= 77 (heatTemp), middle of at-or-above class
        ss.room.temp = 80;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // Partition: actionPerformed() delegates to timerOff(); state == COOL, temp > coolTemp -> AC on
    @Test
    void testEPActionPerformedCoolTempAboveThreshold() {
        // state = COOL
        ss.cool();
        // 73 > 68, middle of above-threshold class
        ss.room.temp = 73;
        ss.actionPerformed(null);
        assertTrue(ss.ac.isOn);
    }

    // Partition: actionPerformed() delegates to timerOff(); state == HEAT, temp < heatTemp -> heater on
    @Test
    void testEPActionPerformedHeatTempBelowThreshold() {
        // state = HEAT
        ss.heat();
        // 75 < 77, middle of below-threshold class
        ss.room.temp = 75;
        ss.actionPerformed(null);
        assertTrue(ss.heater.isOn);
    }

    // Partition: actionPerformed() delegates to timerOff(); state == OFF -> no effect
    @Test
    void testEPActionPerformedWhenOff() {
        ss.actionPerformed(null);
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

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
        // unchanged
        assertTrue(ss.ac.isOn);
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
        // unchanged
        assertTrue(ss.heater.isOn);
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

    // room.temp = coolTemp - 1 = 67: condition (temp > coolTemp) is FALSE -> ac.off()
    @Test
    void testBVATimerOffCoolTempMinusOne() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 67, 67 > 68 is FALSE
        ss.room.temp = ss.coolTemp - 1;
        ss.timerOff();
        // ac turned off
        assertFalse(ss.ac.isOn);
    }

    // room.temp = coolTemp = 68: condition (temp > coolTemp) is FALSE at exactly N -> ac.off()
    @Test
    void testBVATimerOffCoolTempAtBoundary() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 68, 68 > 68 is FALSE (strict >)
        ss.room.temp = ss.coolTemp;
        ss.timerOff();
        // ac turned off
        assertFalse(ss.ac.isOn);
    }

    // room.temp = coolTemp + 1 = 69: condition (temp > coolTemp) is TRUE -> ac.on()
    @Test
    void testBVATimerOffCoolTempPlusOne() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 69, 69 > 68 is TRUE
        ss.room.temp = ss.coolTemp + 1;
        ss.timerOff();
        // ac turned on
        assertTrue(ss.ac.isOn);
    }

    // room.temp = heatTemp - 1 = 76: condition (temp < heatTemp) is TRUE -> heater.on()
    @Test
    void testBVATimerOffHeatTempMinusOne() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 76, 76 < 77 is TRUE
        ss.room.temp = ss.heatTemp - 1;
        ss.timerOff();
        // heater turned on
        assertTrue(ss.heater.isOn);
    }

    // room.temp = heatTemp = 77: condition (temp < heatTemp) is FALSE at exactly N -> heater.off()
    @Test
    void testBVATimerOffHeatTempAtBoundary() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 77, 77 < 77 is FALSE (strict <)
        ss.room.temp = ss.heatTemp;
        ss.timerOff();
        // heater turned off
        assertFalse(ss.heater.isOn);
    }

    // room.temp = heatTemp + 1 = 78: condition (temp < heatTemp) is FALSE -> heater.off()
    @Test
    void testBVATimerOffHeatTempPlusOne() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 78, 78 < 77 is FALSE
        ss.room.temp = ss.heatTemp + 1;
        ss.timerOff();
        // heater turned off
        assertFalse(ss.heater.isOn);
    }

    // state = OFF: timerOff() hits case OFF: break, no device changes
    @Test
    void testBVATimerOffStateOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        // would trigger AC if in COOL
        ss.room.temp = ss.coolTemp + 1;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
    }

    @Test
    void testBVACoolTimerStartsFromOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        assertFalse(ss.timer.isRunning());
        ss.cool();
        assertTrue(ss.timer.isRunning());
    }

    @Test
    void testBVAHeatTimerStartsFromOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        assertFalse(ss.timer.isRunning());
        ss.heat();
        assertTrue(ss.timer.isRunning());
    }

    @Test
    void testBVAOffTimerStopsFromCool() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.timer.start();
        assertTrue(ss.timer.isRunning());
        ss.off();
        assertFalse(ss.timer.isRunning());
    }

    @Test
    void testBVAOffTimerStopsFromHeat() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.timer.start();
        assertTrue(ss.timer.isRunning());
        ss.off();
        assertFalse(ss.timer.isRunning());
    }

    // calls timerOff() which calls ac.on()
    @Test
    void testBVAActionPerformedCoolTempAboveCoolTemp() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 69 > 68, condition TRUE -> ac.on()
        ss.room.temp = ss.coolTemp + 1;
        ss.ac.isOn = false;
        ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, ""));
        // timerOff() turned AC on
        assertTrue(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // calls timerOff() which calls heater.on()
    @Test
    void testBVAActionPerformedHeatTempBelowHeatTemp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 76 < 77, condition TRUE -> heater.on()
        ss.room.temp = ss.heatTemp - 1;
        ss.heater.isOn = false;
        ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, ""));
        // timerOff() turned heater on
        assertTrue(ss.heater.isOn);
        assertFalse(ss.ac.isOn);
    }

    // calls timerOff() which calls ac.off()
    @Test
    void testBVAActionPerformedCoolTempAtCoolBoundary() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 68, 68 > 68 is FALSE -> ac.off()
        ss.room.temp = ss.coolTemp;
        ss.ac.isOn = true;
        ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, ""));
        // timerOff() turned AC off
        assertFalse(ss.ac.isOn);
    }

    // calls timerOff() which calls heater.off()
    @Test
    void testBVAActionPerformedHeatTempAtHeatBoundary() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 77, 77 < 77 is FALSE -> heater.off()
        ss.room.temp = ss.heatTemp;
        ss.heater.isOn = true;
        ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, ""));
        // timerOff() turned heater off
        assertFalse(ss.heater.isOn);
    }

    @Test
    void testCoolSwitchDefaultBranch() {
        SeasonSwitch.state = 99;
        ss.cool();
        assertEquals(99, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
    }

    @Test
    void testHeatSwitchDefaultBranch() {
        SeasonSwitch.state = 99;
        ss.heat();
        assertEquals(99, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
    }

    @Test
    void testOffSwitchDefaultBranch() {
        SeasonSwitch.state = 99;
        ss.off();
        assertEquals(99, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    @Test
    void testTimerOffSwitchDefaultBranch() {
        SeasonSwitch.state = 99;
        ss.timerOff();
        assertEquals(99, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    @Test
    void testMainNoArgs() throws Exception {
        ExitTrap.Result r = ExitTrap.runMain(1500);
        assertFalse(r.exitedByItself);
        assertTrue(r.output.contains("Cooling started"));
    }

    @Test
    void testMainOffArg() throws Exception {
        ExitTrap.Result r = ExitTrap.runMain("off");
        assertTrue(r.exitedByItself);
        assertEquals(0, r.exitCode);
        assertTrue(r.output.contains("System off"));
    }

    @Test
    void testMainCoolArg() throws Exception {
        ExitTrap.Result r = ExitTrap.runMain(1500, "cool");
        assertFalse(r.exitedByItself);
        assertTrue(r.output.contains("Cooling started"));
    }

    @Test
    void testMainUnknownArg() throws Exception {
        ExitTrap.Result r = ExitTrap.runMain("unknown");
        assertTrue(r.exitedByItself);
        assertEquals(1, r.exitCode);
        assertTrue(r.output.contains("Unknown command"));
    }

    @Test
    void testRoomActionPerformedDefaultBranch() {
        SeasonSwitch.state = 99;
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
    }

    @Test
    void testRoomActionPerformedCoolAcOff() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = false;
        int tempBefore = ss.room.temp;
        ss.room.actionPerformed(null);
        assertEquals(tempBefore + 1, ss.room.temp);
    }

    @Test
    void testRoomActionPerformedHeatHeaterOn() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        int tempBefore = ss.room.temp;
        ss.room.actionPerformed(null);
        assertEquals(tempBefore + 1, ss.room.temp);
    }

    @Test
    void testRoomActionPerformedHeatHeaterOff() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = false;
        int tempBefore = ss.room.temp;
        ss.room.actionPerformed(null);
        assertEquals(tempBefore - 1, ss.room.temp);
    }

    @Test
    void testMainHeatArg() throws Exception {
        ExitTrap.Result r = ExitTrap.runMain(1500, "heat");
        assertFalse(r.exitedByItself);
        assertTrue(r.output.contains("Heating started"));
    }

    @Test
    void testRoomActionPerformedStateOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        int tempBefore = ss.room.temp;
        ss.room.actionPerformed(null);
        assertEquals(tempBefore, ss.room.temp);
    }
}
