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
     * Testing cool() method with state=OFF (VALID case)
     */
    @Test
    public void testCoolFromOff() {
        seasonSwitch.cool();
        assertEquals(COOL, SeasonSwitch.state);
        assertTrue(seasonSwitch.ac.isOn);
        assertTrue(seasonSwitch.timer.isRunning());
    }

    /**
     * Testing cool() method with state=COOL (VALID case)
     */
    @Test
    public void testCoolFromCool() {
        SeasonSwitch.state = COOL;
        seasonSwitch.cool();
        assertEquals(COOL, SeasonSwitch.state);
        assertFalse(seasonSwitch.ac.isOn);
        assertFalse(seasonSwitch.timer.isRunning());
    }

    /**
     * Testing cool() method with state=HEAT (VALID case)
     */
    @Test
    public void testCoolFromHeat() {
        SeasonSwitch.state = HEAT;
        seasonSwitch.cool();
        assertEquals(COOL, SeasonSwitch.state);
        assertTrue(seasonSwitch.ac.isOn);
        assertTrue(seasonSwitch.heater.isOn);
        assertTrue(seasonSwitch.timer.isRunning());
    }

    /**
     * Testing cool() method with invalid state (INVALID case)
     */
    @Test
    public void testCoolFromInvalidState() {
        SeasonSwitch.state = 999;
        seasonSwitch.cool();
        assertEquals(999, SeasonSwitch.state);
    }

    /**
     * Testing heat() method with state=OFF (VALID case)
     */
    @Test
    public void testHeatFromOff() {
        seasonSwitch.heat();
        assertEquals(HEAT, SeasonSwitch.state);
        assertTrue(seasonSwitch.heater.isOn);
        assertTrue(seasonSwitch.timer.isRunning());
    }

    /**
     * Testing heat() method with state=HEAT (VALID case)
     */
    @Test
    public void testHeatFromHeat() {
        SeasonSwitch.state = HEAT;
        seasonSwitch.heat();
        assertEquals(HEAT, SeasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn);
        assertFalse(seasonSwitch.timer.isRunning());
    }

    /**
     * Testing heat() method with state=COOL (VALID case)
     */
    @Test
    public void testHeatFromCool() {
        SeasonSwitch.state = COOL;
        seasonSwitch.heat();
        assertEquals(HEAT, SeasonSwitch.state);
        assertTrue(seasonSwitch.heater.isOn);
        assertTrue(seasonSwitch.ac.isOn);
        assertTrue(seasonSwitch.timer.isRunning());
    }

    /**
     * Testing heat() method with invalid state (INVALID case)
     */
    @Test
    public void testHeatFromInvalidState() {
        SeasonSwitch.state = 999;
        seasonSwitch.heat();
        assertEquals(999, SeasonSwitch.state);
    }

    /**
     * Testing off() method with state=OFF (VALID case)
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
     * Testing off() method with state=HEAT (VALID case)
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
     * Testing off() method with state=COOL (VALID case)
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
     * Testing off() method with invalid state (INVALID case)
     */
    @Test
    public void testOffFromInvalidState() {
        SeasonSwitch.state = 999;
        seasonSwitch.off();
        assertEquals(999, SeasonSwitch.state);
    }

    /**
     * Testing timerOff() method with state=OFF (VALID case)
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
     * Testing timerOff() method with state=COOL and room.temp > coolTemp (VALID case)
     */
    @Test
    public void testTimerOffCoolAboveThreshold() {
        SeasonSwitch.state = COOL;
        seasonSwitch.room.temp = 75;
        seasonSwitch.timerOff();
        assertEquals(COOL, SeasonSwitch.state);
        assertTrue(seasonSwitch.ac.isOn);
    }

    /**
     * Testing timerOff() method with state=COOL and room.temp <= coolTemp (VALID case)
     */
    @Test
    public void testTimerOffCoolBelowOrAtThreshold() {
        SeasonSwitch.state = COOL;
        seasonSwitch.room.temp = 68;
        seasonSwitch.timerOff();
        assertEquals(COOL, SeasonSwitch.state);
        assertFalse(seasonSwitch.ac.isOn);
    }

    /**
     * Testing timerOff() method with state=HEAT and room.temp < heatTemp (VALID case)
     */
    @Test
    public void testTimerOffHeatBelowThreshold() {
        SeasonSwitch.state = HEAT;
        seasonSwitch.room.temp = 75;
        seasonSwitch.timerOff();
        assertEquals(HEAT, SeasonSwitch.state);
        assertTrue(seasonSwitch.heater.isOn);
    }

    /**
     * Testing timerOff() method with state=HEAT and room.temp >= heatTemp (VALID case)
     */
    @Test
    public void testTimerOffHeatAboveOrAtThreshold() {
        SeasonSwitch.state = HEAT;
        seasonSwitch.room.temp = 77;
        seasonSwitch.timerOff();
        assertEquals(HEAT, SeasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn);
    }

    /**
     * Testing timerOff() method with invalid state (INVALID case)
     */
    @Test
    public void testTimerOffFromInvalidState() {
        SeasonSwitch.state = 999;
        seasonSwitch.timerOff();
        assertEquals(999, SeasonSwitch.state);
    }

    /**
     * Testing actionPerformed() method (delegates to timerOff())
     */
    @Test
    public void testActionPerformed() {
        SeasonSwitch.state = COOL;
        seasonSwitch.room.temp = 75;
        seasonSwitch.actionPerformed(new ActionEvent(this, 0, ""));
        assertTrue(seasonSwitch.ac.isOn);
    }
}