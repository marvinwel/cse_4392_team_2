package cse4392;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.*;

public class SeasonSwitchMergedTest {

    SeasonSwitch ss;

    Room room;

    AC ac;

    Heater heater;

    @BeforeEach
    void setUp() {
        ss = new SeasonSwitch();
        room = ss.room;
        ac = ss.ac;
        heater = ss.heater;
        // Reset static state
        SeasonSwitch.state = 0;
        ss.timer.stop();
        room.timer.stop();
        ac.isOn = false;
        heater.isOn = false;
        room.temp = 70;
    }

    @AfterEach
    void tearDown() {
        ss.timer.stop();
        room.timer.stop();
    }

    // cool() - State OFF
    @Test
    void cool_off() {
        ss.cool();
        assertEquals(1, SeasonSwitch.state);
        assertTrue(ac.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // cool() - State COOL
    @Test
    void cool_cool() {
        SeasonSwitch.state = 1;
        ss.cool();
        assertEquals(1, SeasonSwitch.state);
    }

    // cool() - State HEAT
    @Test
    void cool_heat() {
        SeasonSwitch.state = 2;
        ss.cool();
        assertEquals(1, SeasonSwitch.state);
        assertFalse(heater.isOn);
        assertTrue(ac.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // heat() - State OFF
    @Test
    void heat_off() {
        ss.heat();
        assertEquals(2, SeasonSwitch.state);
        assertTrue(heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // heat() - State HEAT
    @Test
    void heat_heat() {
        SeasonSwitch.state = 2;
        ss.heat();
        assertEquals(2, SeasonSwitch.state);
    }

    // heat() - State COOL
    @Test
    void heat_cool() {
        SeasonSwitch.state = 1;
        ss.heat();
        assertEquals(2, SeasonSwitch.state);
        assertFalse(ac.isOn);
        assertTrue(heater.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // off() - State OFF
    @Test
    void off_off() {
        SeasonSwitch.state = 0;
        ss.off();
        assertEquals(0, SeasonSwitch.state);
    }

    // off() - State HEAT
    @Test
    void off_heat() {
        SeasonSwitch.state = 2;
        ss.off();
        assertEquals(0, SeasonSwitch.state);
        assertFalse(heater.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // off() - State COOL
    @Test
    void off_cool() {
        SeasonSwitch.state = 1;
        ss.off();
        assertEquals(0, SeasonSwitch.state);
        assertFalse(ac.isOn);
        assertFalse(ss.timer.isRunning());
    }

    // timerOff() - State OFF
    @Test
    void timerOff_off() {
        SeasonSwitch.state = 0;
        ss.timerOff();
        assertEquals(0, SeasonSwitch.state);
    }

    // timerOff() - State COOL - temp > coolTemp
    @Test
    void timerOff_cool_temp_gt_coolTemp() {
        SeasonSwitch.state = 1;
        room.temp = 72;
        ss.timerOff();
        assertEquals(1, SeasonSwitch.state);
        assertTrue(ac.isOn);
    }

    // timerOff() - State COOL - temp <= coolTemp
    @Test
    void timerOff_cool_temp_lte_coolTemp() {
        SeasonSwitch.state = 1;
        room.temp = 68;
        ss.timerOff();
        assertEquals(1, SeasonSwitch.state);
        assertFalse(ac.isOn);
    }

    // timerOff() - State HEAT - temp < heatTemp
    @Test
    void timerOff_heat_temp_lt_heatTemp() {
        SeasonSwitch.state = 2;
        room.temp = 75;
        ss.timerOff();
        assertEquals(2, SeasonSwitch.state);
        assertTrue(heater.isOn);
    }

    // timerOff() - State HEAT - temp >= heatTemp
    @Test
    void timerOff_heat_temp_gte_heatTemp() {
        SeasonSwitch.state = 2;
        room.temp = 77;
        ss.timerOff();
        assertEquals(2, SeasonSwitch.state);
        assertFalse(heater.isOn);
    }

    @BeforeEach
    void setUpBVA() {
        SeasonSwitch.state = 0;
        SeasonSwitch.timer.stop();
    }

    @AfterEach
    void tearDownBVA() {
        SeasonSwitch.timer.stop();
    }

    // cool() - state = OFF, boundary: 0
    @Test
    void testCoolStateOffMinusOne() {
        SeasonSwitch.state = -1;
        SeasonSwitch ss = new SeasonSwitch();
        ss.cool();
        // Should still transition to COOL
        assertEquals(1, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertTrue(SeasonSwitch.timer.isRunning());
    }

    // cool() - state = OFF, boundary: 0
    @Test
    void testCoolStateOffZero() {
        SeasonSwitch ss = new SeasonSwitch();
        ss.cool();
        assertEquals(1, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertTrue(SeasonSwitch.timer.isRunning());
    }

    // cool() - state = OFF, boundary: 1
    @Test
    void testCoolStateOffPlusOne() {
        SeasonSwitch.state = 1;
        SeasonSwitch ss = new SeasonSwitch();
        ss.cool();
        // Should remain in COOL
        assertEquals(1, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertTrue(SeasonSwitch.timer.isRunning());
    }

    // cool() - state = COOL, boundary: 1
    @Test
    void testCoolStateCoolMinusOne() {
        SeasonSwitch.state = 0;
        SeasonSwitch ss = new SeasonSwitch();
        ss.cool();
        ss.cool();
        // Should remain in COOL
        assertEquals(1, SeasonSwitch.state);
    }

    // cool() - state = COOL, boundary: 1
    @Test
    void testCoolStateCoolZero() {
        SeasonSwitch.state = 1;
        SeasonSwitch ss = new SeasonSwitch();
        ss.cool();
        // Should remain in COOL
        assertEquals(1, SeasonSwitch.state);
    }

    // cool() - state = COOL, boundary: 2
    @Test
    void testCoolStateCoolPlusOne() {
        SeasonSwitch.state = 2;
        SeasonSwitch ss = new SeasonSwitch();
        ss.cool();
        assertEquals(1, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertTrue(SeasonSwitch.timer.isRunning());
    }

    // heat() - state = OFF, boundary: 0
    @Test
    void testHeatStateOffMinusOne() {
        SeasonSwitch.state = -1;
        SeasonSwitch ss = new SeasonSwitch();
        ss.heat();
        assertEquals(2, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertTrue(SeasonSwitch.timer.isRunning());
    }

    // heat() - state = OFF, boundary: 0
    @Test
    void testHeatStateOffZero() {
        SeasonSwitch ss = new SeasonSwitch();
        ss.heat();
        assertEquals(2, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertTrue(SeasonSwitch.timer.isRunning());
    }

    // heat() - state = OFF, boundary: 1
    @Test
    void testHeatStateOffPlusOne() {
        SeasonSwitch.state = 1;
        SeasonSwitch ss = new SeasonSwitch();
        ss.heat();
        assertEquals(2, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertTrue(SeasonSwitch.timer.isRunning());
    }

    // heat() - state = HEAT, boundary: 2
    @Test
    void testHeatStateHeatMinusOne() {
        SeasonSwitch.state = 1;
        SeasonSwitch ss = new SeasonSwitch();
        ss.heat();
        ss.heat();
        assertEquals(2, SeasonSwitch.state);
    }

    // heat() - state = HEAT, boundary: 2
    @Test
    void testHeatStateHeatZero() {
        SeasonSwitch.state = 2;
        SeasonSwitch ss = new SeasonSwitch();
        ss.heat();
        assertEquals(2, SeasonSwitch.state);
    }

    // heat() - state = HEAT, boundary: 3
    @Test
    void testHeatStateHeatPlusOne() {
        SeasonSwitch.state = 3;
        SeasonSwitch ss = new SeasonSwitch();
        ss.heat();
        assertEquals(2, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertTrue(SeasonSwitch.timer.isRunning());
    }

    // off() - state = OFF, boundary: 0
    @Test
    void testOffStateOffMinusOne() {
        SeasonSwitch.state = -1;
        SeasonSwitch ss = new SeasonSwitch();
        ss.off();
        assertEquals(-1, SeasonSwitch.state);
    }

    // off() - state = OFF, boundary: 0
    @Test
    void testOffStateOffZero() {
        SeasonSwitch ss = new SeasonSwitch();
        ss.off();
        assertEquals(0, SeasonSwitch.state);
    }

    // off() - state = OFF, boundary: 1
    @Test
    void testOffStateOffPlusOne() {
        SeasonSwitch.state = 1;
        SeasonSwitch ss = new SeasonSwitch();
        ss.off();
        assertEquals(0, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(SeasonSwitch.timer.isRunning());
    }

    // off() - state = HEAT, boundary: 2
    @Test
    void testOffStateHeatMinusOne() {
        SeasonSwitch.state = 1;
        SeasonSwitch ss = new SeasonSwitch();
        ss.off();
        assertEquals(0, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(SeasonSwitch.timer.isRunning());
    }

    // off() - state = HEAT, boundary: 2
    @Test
    void testOffStateHeatZero() {
        SeasonSwitch.state = 2;
        SeasonSwitch ss = new SeasonSwitch();
        ss.off();
        assertEquals(0, SeasonSwitch.state);
        assertFalse(ss.heater.isOn);
        assertFalse(SeasonSwitch.timer.isRunning());
    }

    // off() - state = HEAT, boundary: 3
    @Test
    void testOffStateHeatPlusOne() {
        SeasonSwitch.state = 3;
        SeasonSwitch ss = new SeasonSwitch();
        ss.off();
        assertEquals(3, SeasonSwitch.state);
    }

    // off() - state = COOL, boundary: 1
    @Test
    void testOffStateCoolMinusOne() {
        SeasonSwitch.state = 0;
        SeasonSwitch ss = new SeasonSwitch();
        ss.off();
        assertEquals(0, SeasonSwitch.state);
    }

    // off() - state = COOL, boundary: 1
    @Test
    void testOffStateCoolZero() {
        SeasonSwitch.state = 1;
        SeasonSwitch ss = new SeasonSwitch();
        ss.off();
        assertEquals(0, SeasonSwitch.state);
        assertFalse(ss.ac.isOn);
        assertFalse(SeasonSwitch.timer.isRunning());
    }

    // off() - state = COOL, boundary: 2
    @Test
    void testOffStateCoolPlusOne() {
        SeasonSwitch.state = 2;
        SeasonSwitch ss = new SeasonSwitch();
        ss.off();
        assertEquals(2, SeasonSwitch.state);
    }

    // timerOff() - room.temp > coolTemp, boundary: coolTemp
    @Test
    void testTimerOffCoolTempMinusOne() {
        SeasonSwitch.state = 1;
        SeasonSwitch ss = new SeasonSwitch();
        ss.room.temp = ss.coolTemp - 1;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // timerOff() - room.temp > coolTemp, boundary: coolTemp
    @Test
    void testTimerOffCoolTempZero() {
        SeasonSwitch.state = 1;
        SeasonSwitch ss = new SeasonSwitch();
        ss.room.temp = ss.coolTemp;
        ss.timerOff();
        assertTrue(ss.ac.isOn);
    }

    // timerOff() - room.temp > coolTemp, boundary: coolTemp + 1
    @Test
    void testTimerOffCoolTempPlusOne() {
        SeasonSwitch.state = 1;
        SeasonSwitch ss = new SeasonSwitch();
        ss.room.temp = ss.coolTemp + 1;
        ss.timerOff();
        assertTrue(ss.ac.isOn);
    }

    // timerOff() - room.temp < heatTemp, boundary: heatTemp
    @Test
    void testTimerOffHeatTempMinusOne() {
        SeasonSwitch.state = 2;
        SeasonSwitch ss = new SeasonSwitch();
        ss.room.temp = ss.heatTemp - 1;
        ss.timerOff();
        assertTrue(ss.heater.isOn);
    }

    // timerOff() - room.temp < heatTemp, boundary: heatTemp
    @Test
    void testTimerOffHeatTempZero() {
        SeasonSwitch.state = 2;
        SeasonSwitch ss = new SeasonSwitch();
        ss.room.temp = ss.heatTemp;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // timerOff() - room.temp < heatTemp, boundary: heatTemp + 1
    @Test
    void testTimerOffHeatTempPlusOne() {
        SeasonSwitch.state = 2;
        SeasonSwitch ss = new SeasonSwitch();
        ss.room.temp = ss.heatTemp + 1;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }
}
