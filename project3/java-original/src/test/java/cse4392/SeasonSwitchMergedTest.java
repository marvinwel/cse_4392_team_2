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
    }

    // Partition: timerOff() when state == HEAT and room.temp < heatTemp (74 < 77) -> heater turns on
    @Test
    void testEPTimerOffHeatRoomTempBelowHeatTemp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 74 < 77 (heatTemp)
        ss.room.temp = 74;
        ss.timerOff();
        assertTrue(ss.heater.isOn);
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

    // room.temp = coolTemp - 1 = 67: 67 > 68 is FALSE => ac.off()
    @Test
    void testBVATimerOffCoolTempBelowBoundary() {
        // room.temp = coolTemp - 1; condition room.temp > coolTemp is FALSE
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        // 67
        ss.room.temp = ss.coolTemp - 1;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // room.temp = coolTemp = 68: 68 > 68 is FALSE (strict >) => ac.off()
    @Test
    void testBVATimerOffCoolTempAtBoundary() {
        // room.temp = coolTemp exactly; condition room.temp > coolTemp is FALSE (strict >)
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        // 68
        ss.room.temp = ss.coolTemp;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // room.temp = coolTemp + 1 = 69: 69 > 68 is TRUE => ac.on()
    @Test
    void testBVATimerOffCoolTempAboveBoundary() {
        // room.temp = coolTemp + 1; condition room.temp > coolTemp is TRUE
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 69
        ss.room.temp = ss.coolTemp + 1;
        ss.timerOff();
        assertTrue(ss.ac.isOn);
    }

    // room.temp = heatTemp - 1 = 76: 76 < 77 is TRUE => heater.on()
    @Test
    void testBVATimerOffHeatTempBelowBoundary() {
        // room.temp = heatTemp - 1; condition room.temp < heatTemp is TRUE
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 76
        ss.room.temp = ss.heatTemp - 1;
        ss.timerOff();
        assertTrue(ss.heater.isOn);
    }

    // room.temp = heatTemp = 77: 77 < 77 is FALSE (strict <) => heater.off()
    @Test
    void testBVATimerOffHeatTempAtBoundary() {
        // room.temp = heatTemp exactly; condition room.temp < heatTemp is FALSE (strict <)
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        // 77
        ss.room.temp = ss.heatTemp;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // room.temp = heatTemp + 1 = 78: 78 < 77 is FALSE => heater.off()
    @Test
    void testBVATimerOffHeatTempAboveBoundary() {
        // room.temp = heatTemp + 1; condition room.temp < heatTemp is FALSE
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        // 78
        ss.room.temp = ss.heatTemp + 1;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // state = OFF: timerOff() does nothing
    @Test
    void testBVATimerOffStateOff() {
        // state == OFF; timerOff() switch hits OFF case: break, no side effects
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // actionPerformed() in COOL state with room.temp > coolTemp => ac.on()
    @Test
    void testBVAActionPerformedCoolTempAboveBoundary() {
        // actionPerformed calls timerOff(); room.temp = coolTemp+1 => 69 > 68 TRUE => ac.on()
        SeasonSwitch.state = SeasonSwitch.COOL;
        // 69
        ss.room.temp = ss.coolTemp + 1;
        ss.actionPerformed(null);
        assertTrue(ss.ac.isOn);
    }

    // actionPerformed() in COOL state with room.temp = coolTemp => ac.off()
    @Test
    void testBVAActionPerformedCoolTempAtBoundary() {
        // actionPerformed calls timerOff(); room.temp = coolTemp exactly => 68 > 68 FALSE => ac.off()
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        // 68
        ss.room.temp = ss.coolTemp;
        ss.actionPerformed(null);
        assertFalse(ss.ac.isOn);
    }

    // actionPerformed() in COOL state with room.temp = coolTemp - 1 => ac.off()
    @Test
    void testBVAActionPerformedCoolTempBelowBoundary() {
        // actionPerformed calls timerOff(); room.temp = coolTemp-1 => 67 > 68 FALSE => ac.off()
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        // 67
        ss.room.temp = ss.coolTemp - 1;
        ss.actionPerformed(null);
        assertFalse(ss.ac.isOn);
    }

    // actionPerformed() in HEAT state with room.temp < heatTemp => heater.on()
    @Test
    void testBVAActionPerformedHeatTempBelowBoundary() {
        // actionPerformed calls timerOff(); room.temp = heatTemp-1 => 76 < 77 TRUE => heater.on()
        SeasonSwitch.state = SeasonSwitch.HEAT;
        // 76
        ss.room.temp = ss.heatTemp - 1;
        ss.actionPerformed(null);
        assertTrue(ss.heater.isOn);
    }

    // actionPerformed() in HEAT state with room.temp = heatTemp => heater.off()
    @Test
    void testBVAActionPerformedHeatTempAtBoundary() {
        // actionPerformed calls timerOff(); room.temp = heatTemp exactly => 77 < 77 FALSE => heater.off()
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        // 77
        ss.room.temp = ss.heatTemp;
        ss.actionPerformed(null);
        assertFalse(ss.heater.isOn);
    }

    // actionPerformed() in HEAT state with room.temp = heatTemp + 1 => heater.off()
    @Test
    void testBVAActionPerformedHeatTempAboveBoundary() {
        // actionPerformed calls timerOff(); room.temp = heatTemp+1 => 78 < 77 FALSE => heater.off()
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        // 78
        ss.room.temp = ss.heatTemp + 1;
        ss.actionPerformed(null);
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
    void testMainHeatArg() throws Exception {
        ExitTrap.Result r = ExitTrap.runMain(1500, "heat");
        assertFalse(r.exitedByItself);
        assertTrue(r.output.contains("Heating started"));
    }

    @Test
    void testMainUnknownArg() throws Exception {
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
    void testCoolDefaultBranch() {
        SeasonSwitch.state = 99;
        ss.cool();
        assertEquals(99, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    @Test
    void testHeatDefaultBranch() {
        SeasonSwitch.state = 99;
        ss.heat();
        assertEquals(99, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    @Test
    void testOffDefaultBranch() {
        SeasonSwitch.state = 99;
        ss.off();
        assertEquals(99, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    @Test
    void testTimerOffDefaultBranch() {
        SeasonSwitch.state = 99;
        ss.timerOff();
        assertEquals(99, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    @Test
    void testRoomActionPerformedDefaultBranch() {
        SeasonSwitch.state = 99;
        int tempBefore = ss.room.temp;
        ss.room.actionPerformed(null);
        assertEquals(tempBefore, ss.room.temp);
    }
}
