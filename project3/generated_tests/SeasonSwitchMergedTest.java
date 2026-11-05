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
        assertTrue(ac.isOn);
    }

    // cool() - State HEAT
    @Test
    void cool_heat() {
        SeasonSwitch.state = 2;
        ss.cool();
        assertEquals(1, SeasonSwitch.state);
        assertTrue(ac.isOn);
        assertFalse(heater.isOn);
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
        assertTrue(heater.isOn);
    }

    // heat() - State COOL
    @Test
    void heat_cool() {
        SeasonSwitch.state = 1;
        ss.heat();
        assertEquals(2, SeasonSwitch.state);
        assertTrue(heater.isOn);
        assertFalse(ac.isOn);
        assertTrue(ss.timer.isRunning());
    }

    // off() - State OFF
    @Test
    void off_off() {
        SeasonSwitch.state = 0;
        ss.off();
        assertEquals(0, SeasonSwitch.state);
        assertFalse(ac.isOn);
        assertFalse(heater.isOn);
        assertFalse(ss.timer.isRunning());
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
        assertFalse(ac.isOn);
        assertFalse(heater.isOn);
    }

    // timerOff() - State COOL, temp < coolTemp
    @Test
    void timerOff_cool_temp_lt() {
        SeasonSwitch.state = 1;
        room.temp = 67;
        ss.timerOff();
        assertEquals(1, SeasonSwitch.state);
        assertFalse(ac.isOn);
    }

    // timerOff() - State COOL, temp == coolTemp
    @Test
    void timerOff_cool_temp_eq() {
        SeasonSwitch.state = 1;
        room.temp = 68;
        ss.timerOff();
        assertEquals(1, SeasonSwitch.state);
        assertFalse(ac.isOn);
    }

    // timerOff() - State COOL, temp > coolTemp
    @Test
    void timerOff_cool_temp_gt() {
        SeasonSwitch.state = 1;
        room.temp = 69;
        ss.timerOff();
        assertEquals(1, SeasonSwitch.state);
        assertTrue(ac.isOn);
    }

    // timerOff() - State HEAT, temp < heatTemp
    @Test
    void timerOff_heat_temp_lt() {
        SeasonSwitch.state = 2;
        room.temp = 76;
        ss.timerOff();
        assertEquals(2, SeasonSwitch.state);
        assertTrue(heater.isOn);
    }

    // timerOff() - State HEAT, temp == heatTemp
    @Test
    void timerOff_heat_temp_eq() {
        SeasonSwitch.state = 2;
        room.temp = 77;
        ss.timerOff();
        assertEquals(2, SeasonSwitch.state);
        assertFalse(heater.isOn);
    }

    // timerOff() - State HEAT, temp > heatTemp
    @Test
    void timerOff_heat_temp_gt() {
        SeasonSwitch.state = 2;
        room.temp = 78;
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
    void testCoolStateOffZero() {
        SeasonSwitch ss = new SeasonSwitch();
        ss.cool();
        assertEquals(1, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
        assertTrue(SeasonSwitch.timer.isRunning());
    }

    // cool() - state = COOL, boundary: 1
    @Test
    void testCoolStateCoolZero() {
        SeasonSwitch.state = 1;
        SeasonSwitch ss = new SeasonSwitch();
        ss.cool();
        assertEquals(1, SeasonSwitch.state);
    }

    // cool() - state = HEAT, boundary: 2
    @Test
    void testCoolStateHeatZero() {
        SeasonSwitch.state = 2;
        SeasonSwitch ss = new SeasonSwitch();
        ss.cool();
        assertEquals(1, SeasonSwitch.state);
        assertTrue(ss.ac.isOn);
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

    // heat() - state = HEAT, boundary: 2
    @Test
    void testHeatStateHeatZero() {
        SeasonSwitch.state = 2;
        SeasonSwitch ss = new SeasonSwitch();
        ss.heat();
        assertEquals(2, SeasonSwitch.state);
    }

    // heat() - state = COOL, boundary: 1
    @Test
    void testHeatStateCoolZero() {
        SeasonSwitch.state = 1;
        SeasonSwitch ss = new SeasonSwitch();
        ss.heat();
        assertEquals(2, SeasonSwitch.state);
        assertTrue(ss.heater.isOn);
        assertTrue(SeasonSwitch.timer.isRunning());
    }

    // off() - state = OFF, boundary: 0
    @Test
    void testOffStateOffZero() {
        SeasonSwitch ss = new SeasonSwitch();
        ss.off();
        assertEquals(0, SeasonSwitch.state);
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

    // timerOff() - room.temp > coolTemp, boundary: coolTemp - 1
    @Test
    void testTimerOffCoolTempMinusOne() {
        SeasonSwitch.state = 1;
        SeasonSwitch ss = new SeasonSwitch();
        ss.room.temp = 67;
        ss.timerOff();
        assertTrue(ss.ac.isOn);
    }

    // timerOff() - room.temp > coolTemp, boundary: coolTemp
    @Test
    void testTimerOffCoolTempZero() {
        SeasonSwitch.state = 1;
        SeasonSwitch ss = new SeasonSwitch();
        ss.room.temp = 68;
        ss.timerOff();
        assertFalse(ss.ac.isOn);
    }

    // timerOff() - room.temp > coolTemp, boundary: coolTemp + 1
    @Test
    void testTimerOffCoolTempPlusOne() {
        SeasonSwitch.state = 1;
        SeasonSwitch ss = new SeasonSwitch();
        ss.room.temp = 69;
        ss.timerOff();
        assertTrue(ss.ac.isOn);
    }

    // timerOff() - room.temp < heatTemp, boundary: heatTemp - 1
    @Test
    void testTimerOffHeatTempMinusOne() {
        SeasonSwitch.state = 2;
        SeasonSwitch ss = new SeasonSwitch();
        ss.room.temp = 76;
        ss.timerOff();
        assertTrue(ss.heater.isOn);
    }

    // timerOff() - room.temp < heatTemp, boundary: heatTemp
    @Test
    void testTimerOffHeatTempZero() {
        SeasonSwitch.state = 2;
        SeasonSwitch ss = new SeasonSwitch();
        ss.room.temp = 77;
        ss.timerOff();
        assertFalse(ss.heater.isOn);
    }

    // timerOff() - room.temp < heatTemp, boundary: heatTemp + 1
    @Test
    void testTimerOffHeatTempPlusOne() {
        SeasonSwitch.state = 2;
        SeasonSwitch ss = new SeasonSwitch();
        ss.room.temp = 78;
        ss.timerOff();
        assertTrue(ss.heater.isOn);
    }
}
