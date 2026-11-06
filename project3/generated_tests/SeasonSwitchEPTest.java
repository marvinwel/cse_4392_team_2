package cse4392;

import org.junit.jupiter.api.*;
import javax.swing.Timer;
import java.awt.event.ActionEvent;
import java.util.concurrent.CountDownLatch;

import static org.junit.jupiter.api.Assertions.*;

public class SeasonSwitchEPTest {

    private SeasonSwitch seasonSwitch;
    private static final int OFF = 0, COOL = 1, HEAT = 2;

    @BeforeEach
    public void setUp() {
        seasonSwitch = new SeasonSwitch();
        SeasonSwitch.state = 0; // Reset static state
        seasonSwitch.timer.stop(); // Ensure timer is stopped
        seasonSwitch.room.timer.stop(); // Ensure room timer is stopped
    }

    @AfterEach
    public void tearDown() {
        seasonSwitch.timer.stop();
        seasonSwitch.room.timer.stop();
    }

    /**
     * Tests cool() when state is OFF (valid case)
     */
    @Test
    public void testCoolFromOff() {
        seasonSwitch.cool();
        assertEquals(COOL, SeasonSwitch.state);
        assertTrue(seasonSwitch.ac.isOn);
        assertTrue(seasonSwitch.timer.isRunning());
    }

    /**
     * Tests cool() when state is COOL (valid case)
     */
    @Test
    public void testCoolFromCool() {
        SeasonSwitch.state = COOL;
        seasonSwitch.cool();
        assertEquals(COOL, SeasonSwitch.state);
        assertFalse(seasonSwitch.ac.isOn); // Should remain off
        assertFalse(seasonSwitch.timer.isRunning()); // Should not start again
    }

    /**
     * Tests cool() when state is HEAT (valid case)
     */
    @Test
    public void testCoolFromHeat() {
        SeasonSwitch.state = HEAT;
        seasonSwitch.cool();
        assertEquals(COOL, SeasonSwitch.state);
        assertTrue(seasonSwitch.ac.isOn);
        assertTrue(seasonSwitch.heater.isOn); // Heater should be turned off
        assertTrue(seasonSwitch.timer.isRunning());
    }

    /**
     * Tests heat() when state is OFF (valid case)
     */
    @Test
    public void testHeatFromOff() {
        seasonSwitch.heat();
        assertEquals(HEAT, SeasonSwitch.state);
        assertTrue(seasonSwitch.heater.isOn);
        assertTrue(seasonSwitch.timer.isRunning());
    }

    /**
     * Tests heat() when state is HEAT (valid case)
     */
    @Test
    public void testHeatFromHeat() {
        SeasonSwitch.state = HEAT;
        seasonSwitch.heat();
        assertEquals(HEAT, SeasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn); // Should remain off
        assertFalse(seasonSwitch.timer.isRunning()); // Should not start again
    }

    /**
     * Tests heat() when state is COOL (valid case)
     */
    @Test
    public void testHeatFromCool() {
        SeasonSwitch.state = COOL;
        seasonSwitch.heat();
        assertEquals(HEAT, SeasonSwitch.state);
        assertTrue(seasonSwitch.heater.isOn);
        assertTrue(seasonSwitch.ac.isOn); // AC should be turned off
        assertTrue(seasonSwitch.timer.isRunning());
    }

    /**
     * Tests off() when state is OFF (valid case)
     */
    @Test
    public void testOffFromOff() {
        seasonSwitch.off();
        assertEquals(OFF, SeasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn);
        assertFalse(seasonSwitch.ac.isOn);
        assertFalse(seasonSwitch.timer.isRunning());
    }

    /**
     * Tests off() when state is HEAT (valid case)
     */
    @Test
    public void testOffFromHeat() {
        SeasonSwitch.state = HEAT;
        seasonSwitch.off();
        assertEquals(OFF, SeasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn);
        assertFalse(seasonSwitch.ac.isOn);
        assertFalse(seasonSwitch.timer.isRunning());
    }

    /**
     * Tests off() when state is COOL (valid case)
     */
    @Test
    public void testOffFromCool() {
        SeasonSwitch.state = COOL;
        seasonSwitch.off();
        assertEquals(OFF, SeasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn);
        assertFalse(seasonSwitch.ac.isOn);
        assertFalse(seasonSwitch.timer.isRunning());
    }

    /**
     * Tests timerOff() when state is OFF (valid case)
     */
    @Test
    public void testTimerOffFromOff() {
        SeasonSwitch.state = OFF;
        seasonSwitch.timerOff();
        assertEquals(OFF, SeasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn);
        assertFalse(seasonSwitch.ac.isOn);
    }

    /**
     * Tests timerOff() when state is COOL and room.temp > coolTemp (valid case)
     */
    @Test
    public void testTimerOffFromCoolWithHighTemp() {
        SeasonSwitch.state = COOL;
        seasonSwitch.room.temp = 75; // Above coolTemp (68)
        seasonSwitch.timerOff();
        assertEquals(COOL, SeasonSwitch.state);
        assertTrue(seasonSwitch.ac.isOn);
    }

    /**
     * Tests timerOff() when state is COOL and room.temp <= coolTemp (valid case)
     */
    @Test
    public void testTimerOffFromCoolWithLowTemp() {
        SeasonSwitch.state = COOL;
        seasonSwitch.room.temp = 65; // Below or equal to coolTemp (68)
        seasonSwitch.timerOff();
        assertEquals(COOL, SeasonSwitch.state);
        assertFalse(seasonSwitch.ac.isOn);
    }

    /**
     * Tests timerOff() when state is HEAT and room.temp < heatTemp (valid case)
     */
    @Test
    public void testTimerOffFromHeatWithLowTemp() {
        SeasonSwitch.state = HEAT;
        seasonSwitch.room.temp = 70; // Below heatTemp (77)
        seasonSwitch.timerOff();
        assertEquals(HEAT, SeasonSwitch.state);
        assertTrue(seasonSwitch.heater.isOn);
    }

    /**
     * Tests timerOff() when state is HEAT and room.temp >= heatTemp (valid case)
     */
    @Test
    public void testTimerOffFromHeatWithHighTemp() {
        SeasonSwitch.state = HEAT;
        seasonSwitch.room.temp = 80; // Above or equal to heatTemp (77)
        seasonSwitch.timerOff();
        assertEquals(HEAT, SeasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn);
    }

    /**
     * Tests invalid state value (outside valid range)
     */
    @Test
    public void testInvalidStateValue() {
        SeasonSwitch.state = 99; // Invalid state
        seasonSwitch.cool();
        assertEquals(99, SeasonSwitch.state); // Should not change
    }
}