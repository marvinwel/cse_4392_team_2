package cse4392;

import org.junit.jupiter.api.*;
import javax.swing.Timer;
import java.awt.event.ActionEvent;
import java.util.concurrent.CountDownLatch;

import static org.junit.jupiter.api.Assertions.*;

public class SeasonSwitchBVTest {

    private SeasonSwitch seasonSwitch;
    private static final int OFF = 0, COOL = 1, HEAT = 2;

    @BeforeEach
    public void setUp() {
        seasonSwitch = new SeasonSwitch();
        SeasonSwitch.state = OFF;
        seasonSwitch.ac.isOn = false;
        seasonSwitch.heater.isOn = false;
        seasonSwitch.room.temp = 70;
    }

    @AfterEach
    public void tearDown() {
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