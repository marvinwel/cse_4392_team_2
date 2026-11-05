package cse4392;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

public class SeasonSwitchEPTest {

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
        SeasonSwitch.state = 0; // Reset static state
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
}