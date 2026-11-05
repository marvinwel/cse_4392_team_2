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
    void testCoolStateOffMinusOne() {
        SeasonSwitch.state = -1;
        SeasonSwitch ss = new SeasonSwitch();
        ss.cool();
        assertEquals(1, SeasonSwitch.state); // Should still transition to COOL
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
        assertEquals(1, SeasonSwitch.state); // Should remain in COOL
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
        assertEquals(1, SeasonSwitch.state); // Should remain in COOL
    }

    // cool() - state = COOL, boundary: 1
    @Test
    void testCoolStateCoolZero() {
        SeasonSwitch.state = 1;
        SeasonSwitch ss = new SeasonSwitch();
        ss.cool();
        assertEquals(1, SeasonSwitch.state); // Should remain in COOL
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