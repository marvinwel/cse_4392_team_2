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
        ss.room.temp = 65;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
    }

    // Partition: timerOff() when state == HEAT and room.temp < heatTemp (74 < 77) -> heater turns on
    @Test
    void testEPTimerOffHeatRoomTempBelowHeatTemp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
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
        ss.room.temp = 80;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
    }

    // Partition: actionPerformed() delegates to timerOff() when state == COOL and temp > coolTemp
    @Test
    void testEPActionPerformedCoolTempAboveThreshold() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.room.temp = 73;
        ss.actionPerformed(null);
        assertTrue(ss.ac.isOn);
    }

    // Partition: actionPerformed() delegates to timerOff() when state == HEAT and temp < heatTemp
    @Test
    void testEPActionPerformedHeatTempBelowThreshold() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
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

    // cool(): state = null (invalid) -> no-op
    @Test
    void testBVACoolStateMinMinus1() {
        SeasonSwitch.state = null;
        ss.cool();
        assertNull(SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // cool(): state = COOL (middle of valid range) -> no-op
    @Test
    void testBVACoolFromCoolStateMiddle() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // cool(): state = HEAT (MAX of valid range) -> switches to AC
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

    // cool(): state = null (above MAX, invalid) -> no-op
    @Test
    void testBVACoolStateMaxPlus1() {
        SeasonSwitch.state = null;
        ss.cool();
        assertNull(SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // heat(): state = null (below MIN, invalid) -> no-op
    @Test
    void testBVAHeatStateMinMinus1() {
        SeasonSwitch.state = null;
        ss.heat();
        assertNull(SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // heat(): state = COOL (middle of valid range) -> switches to heater
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

    // heat(): state = HEAT (MAX of valid range) -> no-op
    @Test
    void testBVAHeatFromHeatStateMax() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.heat();
        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // heat(): state = null (above MAX, invalid) -> no-op
    @Test
    void testBVAHeatStateMaxPlus1() {
        SeasonSwitch.state = null;
        ss.heat();
        assertNull(SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // off(): state = null (below MIN, invalid) -> no-op
    @Test
    void testBVAOffStateMinMinus1() {
        SeasonSwitch.state = null;
        ss.off();
        assertNull(SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // off(): state = null (above MAX, invalid) -> no-op
    @Test
    void testBVAOffStateMaxPlus1() {
        SeasonSwitch.state = null;
        ss.off();
        assertNull(SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
    }

    // timerOff(): state = null (below MIN, invalid) -> no-op
    @Test
    void testBVATimerOffStateMinMinus1() {
        SeasonSwitch.state = null;
        ss.ac.isOn = false;
        ss.heater.isOn = false;
        ss.room.temp = ss.coolTemp + 1;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertNull(SeasonSwitch.state);
    }

    // timerOff(): state == OFF (MIN of valid range) -> no-op
    @Test
    void testBVATimerOffStateOff() {
        SeasonSwitch.state = SeasonSwitch.OFF;
        ss.ac.isOn = false;
        ss.heater.isOn = false;
        ss.room.temp = ss.coolTemp + 1;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
    }

    // timerOff(): state = null (above MAX, invalid) -> no-op
    @Test
    void testBVATimerOffStateMaxPlus1() {
        SeasonSwitch.state = null;
        ss.ac.isOn = false;
        ss.heater.isOn = false;
        ss.room.temp = ss.heatTemp - 1;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
        assertFalse(ss.heater.isOn);
        assertNull(SeasonSwitch.state);
    }

    // COOL state, room.temp = coolTemp - 1 = 67: 67 > 68 is FALSE -> ac.off()
    @Test
    void testBVATimerOffCoolTempOneBelowCoolTemp() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.room.temp = ss.coolTemp - 1;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // COOL state, room.temp = coolTemp = 68: 68 > 68 is FALSE -> ac.off()
    @Test
    void testBVATimerOffCoolTempEqualCoolTemp() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.room.temp = ss.coolTemp;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // COOL state, room.temp = coolTemp + 1 = 69: 69 > 68 is TRUE -> ac.on()
    @Test
    void testBVATimerOffCoolTempOneAboveCoolTemp() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = false;
        ss.room.temp = ss.coolTemp + 1;
        ss.timerOff();
        assertTrue(ss.ac.isOn);
    }

    // HEAT state, room.temp = heatTemp - 1 = 76: 76 < 77 is TRUE -> heater.on()
    @Test
    void testBVATimerOffHeatTempOneBelowHeatTemp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = false;
        ss.room.temp = ss.heatTemp - 1;
        ss.timerOff();
        assertTrue(ss.heater.isOn);
    }

    // HEAT state, room.temp = heatTemp = 77: 77 < 77 is FALSE -> heater.off()
    @Test
    void testBVATimerOffHeatTempEqualHeatTemp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.room.temp = ss.heatTemp;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // HEAT state, room.temp = heatTemp + 1 = 78: 78 < 77 is FALSE -> heater.off()
    @Test
    void testBVATimerOffHeatTempOneAboveHeatTemp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.room.temp = ss.heatTemp + 1;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // actionPerformed(): COOL state, room.temp = coolTemp - 1 = 67: FALSE -> ac.off()
    @Test
    void testBVAActionPerformedCoolTempOneBelowCoolTemp() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.room.temp = ss.coolTemp - 1;
        ss.actionPerformed(null);
        assertFalse(ss.ac.isOn);
    }

    // actionPerformed(): COOL state, room.temp = coolTemp = 68: FALSE -> ac.off()
    @Test
    void testBVAActionPerformedCoolTempEqualCoolTemp() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = true;
        ss.room.temp = ss.coolTemp;
        ss.actionPerformed(null);
        assertFalse(ss.ac.isOn);
    }

    // actionPerformed(): COOL state, room.temp = coolTemp + 1 = 69: TRUE -> ac.on()
    @Test
    void testBVAActionPerformedCoolTempOneAboveCoolTemp() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = false;
        ss.room.temp = ss.coolTemp + 1;
        ss.actionPerformed(null);
        assertTrue(ss.ac.isOn);
    }

    // actionPerformed(): HEAT state, room.temp = heatTemp - 1 = 76: TRUE -> heater.on()
    @Test
    void testBVAActionPerformedHeatTempOneBelowHeatTemp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = false;
        ss.room.temp = ss.heatTemp - 1;
        ss.actionPerformed(null);
        assertTrue(ss.heater.isOn);
    }

    // actionPerformed(): HEAT state, room.temp = heatTemp = 77: FALSE -> heater.off()
    @Test
    void testBVAActionPerformedHeatTempEqualHeatTemp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.room.temp = ss.heatTemp;
        ss.actionPerformed(null);
        assertFalse(ss.heater.isOn);
    }

    // actionPerformed(): HEAT state, room.temp = heatTemp + 1 = 78: FALSE -> heater.off()
    @Test
    void testBVAActionPerformedHeatTempOneAboveHeatTemp() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
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
        ss.room.temp = 70;
        ss.room.actionPerformed(null);
        assertEquals(69, ss.room.temp);
    }

    @Test
    void testRoomActionPerformedCoolAcOff() {
        SeasonSwitch.state = SeasonSwitch.COOL;
        ss.ac.isOn = false;
        ss.room.temp = 70;
        ss.room.actionPerformed(null);
        assertEquals(71, ss.room.temp);
    }

    @Test
    void testRoomActionPerformedHeatHeaterOn() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = true;
        ss.room.temp = 70;
        ss.room.actionPerformed(null);
        assertEquals(71, ss.room.temp);
    }

    @Test
    void testRoomActionPerformedHeatHeaterOff() {
        SeasonSwitch.state = SeasonSwitch.HEAT;
        ss.heater.isOn = false;
        ss.room.temp = 70;
        ss.room.actionPerformed(null);
        assertEquals(69, ss.room.temp);
    }

    @Test
    void testRoomActionPerformedUnmatchedState() {
        SeasonSwitch.state = null;
        int tempBefore = ss.room.temp;
        ss.room.actionPerformed(null);
        assertEquals(tempBefore, ss.room.temp);
    }
}
