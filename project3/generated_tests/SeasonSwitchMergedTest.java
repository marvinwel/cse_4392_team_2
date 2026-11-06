package cse4392;

import org.junit.jupiter.api.*;
import javax.swing.Timer;
import java.awt.event.ActionEvent;
import java.util.concurrent.CountDownLatch;
import static org.junit.jupiter.api.Assertions.*;

public class SeasonSwitchMergedTest {

    private SeasonSwitch seasonSwitch;

    private static final int OFF = 0, COOL = 1, HEAT = 2;

    @BeforeEach
    public void setUp() {
        seasonSwitch = new SeasonSwitch();
        // Reset static state
        SeasonSwitch.state = 0;
        // Ensure timer is stopped
        seasonSwitch.timer.stop();
        // Ensure room timer is stopped
        seasonSwitch.room.timer.stop();
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
        // Should remain off
        assertFalse(seasonSwitch.ac.isOn);
        // Should not start again
        assertFalse(seasonSwitch.timer.isRunning());
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
        // Heater should be turned off
        assertTrue(seasonSwitch.heater.isOn);
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
        // Should remain off
        assertFalse(seasonSwitch.heater.isOn);
        // Should not start again
        assertFalse(seasonSwitch.timer.isRunning());
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
        // AC should be turned off
        assertTrue(seasonSwitch.ac.isOn);
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
        // Above coolTemp (68)
        seasonSwitch.room.temp = 75;
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
        // Below or equal to coolTemp (68)
        seasonSwitch.room.temp = 65;
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
        // Below heatTemp (77)
        seasonSwitch.room.temp = 70;
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
        // Above or equal to heatTemp (77)
        seasonSwitch.room.temp = 80;
        seasonSwitch.timerOff();
        assertEquals(HEAT, SeasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn);
    }

    /**
     * Tests invalid state value (outside valid range)
     */
    @Test
    public void testInvalidStateValue() {
        // Invalid state
        SeasonSwitch.state = 99;
        seasonSwitch.cool();
        // Should not change
        assertEquals(99, SeasonSwitch.state);
    }

    @BeforeEach
    public void setUpBVA() {
        seasonSwitch = new SeasonSwitch();
        SeasonSwitch.state = OFF;
        seasonSwitch.ac.isOn = false;
        seasonSwitch.heater.isOn = false;
        seasonSwitch.room.temp = 70;
    }

    @AfterEach
    public void tearDownBVA() {
        if (seasonSwitch.timer.isRunning()) {
            seasonSwitch.timer.stop();
        }
        if (seasonSwitch.room.timer.isRunning()) {
            seasonSwitch.room.timer.stop();
        }
    }

    // Boundary: state = OFF (0), testing boundary values around 0
    @Test
    public void testCoolWhenStateIsOff() {
        seasonSwitch.state = OFF;
        seasonSwitch.cool();
        assertEquals(COOL, seasonSwitch.state);
        assertTrue(seasonSwitch.ac.isOn);
        assertTrue(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = COOL (1), testing boundary values around 1
    @Test
    public void testCoolWhenStateIsCool() {
        seasonSwitch.state = COOL;
        seasonSwitch.cool();
        assertEquals(COOL, seasonSwitch.state);
        assertFalse(seasonSwitch.ac.isOn);
        assertFalse(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = HEAT (2), testing boundary values around 2
    @Test
    public void testCoolWhenStateIsHeat() {
        seasonSwitch.state = HEAT;
        seasonSwitch.cool();
        assertEquals(COOL, seasonSwitch.state);
        assertTrue(seasonSwitch.ac.isOn);
        assertTrue(seasonSwitch.timer.isRunning());
        assertFalse(seasonSwitch.heater.isOn);
    }

    // Boundary: state = OFF (0), testing boundary values around 0
    @Test
    public void testHeatWhenStateIsOff() {
        seasonSwitch.state = OFF;
        seasonSwitch.heat();
        assertEquals(HEAT, seasonSwitch.state);
        assertTrue(seasonSwitch.heater.isOn);
        assertTrue(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = HEAT (2), testing boundary values around 2
    @Test
    public void testHeatWhenStateIsHeat() {
        seasonSwitch.state = HEAT;
        seasonSwitch.heat();
        assertEquals(HEAT, seasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn);
        assertFalse(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = COOL (1), testing boundary values around 1
    @Test
    public void testHeatWhenStateIsCool() {
        seasonSwitch.state = COOL;
        seasonSwitch.heat();
        assertEquals(HEAT, seasonSwitch.state);
        assertTrue(seasonSwitch.heater.isOn);
        assertTrue(seasonSwitch.timer.isRunning());
        assertFalse(seasonSwitch.ac.isOn);
    }

    // Boundary: state = OFF (0), testing boundary values around 0
    @Test
    public void testOffWhenStateIsOff() {
        seasonSwitch.state = OFF;
        seasonSwitch.off();
        assertEquals(OFF, seasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn);
        assertFalse(seasonSwitch.ac.isOn);
        assertFalse(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = HEAT (2), testing boundary values around 2
    @Test
    public void testOffWhenStateIsHeat() {
        seasonSwitch.state = HEAT;
        seasonSwitch.heater.on();
        seasonSwitch.off();
        assertEquals(OFF, seasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn);
        assertFalse(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = COOL (1), testing boundary values around 1
    @Test
    public void testOffWhenStateIsCool() {
        seasonSwitch.state = COOL;
        seasonSwitch.ac.on();
        seasonSwitch.off();
        assertEquals(OFF, seasonSwitch.state);
        assertFalse(seasonSwitch.ac.isOn);
        assertFalse(seasonSwitch.timer.isRunning());
    }

    // Boundary: room.temp = coolTemp (68), testing boundary values around 68
    @Test
    public void testTimerOffWhenRoomTempEqualsCoolTemp() {
        seasonSwitch.state = COOL;
        seasonSwitch.room.temp = seasonSwitch.coolTemp;
        seasonSwitch.timerOff();
        assertFalse(seasonSwitch.ac.isOn);
    }

    // Boundary: room.temp = coolTemp - 1 (67), testing boundary values around 67
    @Test
    public void testTimerOffWhenRoomTempLessThanCoolTemp() {
        seasonSwitch.state = COOL;
        seasonSwitch.room.temp = seasonSwitch.coolTemp - 1;
        seasonSwitch.timerOff();
        assertTrue(seasonSwitch.ac.isOn);
    }

    // Boundary: room.temp = coolTemp + 1 (69), testing boundary values around 69
    @Test
    public void testTimerOffWhenRoomTempGreaterThanCoolTemp() {
        seasonSwitch.state = COOL;
        seasonSwitch.room.temp = seasonSwitch.coolTemp + 1;
        seasonSwitch.timerOff();
        assertFalse(seasonSwitch.ac.isOn);
    }

    // Boundary: room.temp = heatTemp (77), testing boundary values around 77
    @Test
    public void testTimerOffWhenRoomTempEqualsHeatTemp() {
        seasonSwitch.state = HEAT;
        seasonSwitch.room.temp = seasonSwitch.heatTemp;
        seasonSwitch.timerOff();
        assertFalse(seasonSwitch.heater.isOn);
    }

    // Boundary: room.temp = heatTemp - 1 (76), testing boundary values around 76
    @Test
    public void testTimerOffWhenRoomTempLessThanHeatTemp() {
        seasonSwitch.state = HEAT;
        seasonSwitch.room.temp = seasonSwitch.heatTemp - 1;
        seasonSwitch.timerOff();
        assertTrue(seasonSwitch.heater.isOn);
    }

    // Boundary: room.temp = heatTemp + 1 (78), testing boundary values around 78
    @Test
    public void testTimerOffWhenRoomTempGreaterThanHeatTemp() {
        seasonSwitch.state = HEAT;
        seasonSwitch.room.temp = seasonSwitch.heatTemp + 1;
        seasonSwitch.timerOff();
        assertFalse(seasonSwitch.heater.isOn);
    }

    // Boundary: room.temp = 0 (minimum valid temp), testing boundary values around 0
    @Test
    public void testRoomTempBelowValidRange() {
        seasonSwitch.state = COOL;
        seasonSwitch.room.temp = 0;
        seasonSwitch.timerOff();
        assertTrue(seasonSwitch.ac.isOn);
    }

    // Boundary: room.temp = 100 (maximum valid temp), testing boundary values around 100
    @Test
    public void testRoomTempAboveValidRange() {
        seasonSwitch.state = HEAT;
        seasonSwitch.room.temp = 100;
        seasonSwitch.timerOff();
        assertTrue(seasonSwitch.heater.isOn);
    }
}
