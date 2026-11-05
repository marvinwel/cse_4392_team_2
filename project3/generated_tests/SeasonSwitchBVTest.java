package cse4392;

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

public class SeasonSwitchBVTest {

    @BeforeEach
    void setUp() {
        SeasonSwitch.state = 0;
        SeasonSwitch.timer.stop();
    }

    @AfterEach
    void tearDown() {
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