package cse4392;

import org.junit.jupiter.api.*;
import javax.swing.Timer;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.concurrent.CountDownLatch;

import static org.junit.jupiter.api.Assertions.*;

public class SeasonSwitchBVTest {

    private SeasonSwitch seasonSwitch;

    @BeforeEach
    public void setUp() {
        seasonSwitch = new SeasonSwitch();
        SeasonSwitch.state = 0; // Reset static state
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
        seasonSwitch.state = 0; // OFF
        seasonSwitch.cool();
        assertEquals(SeasonSwitch.COOL, seasonSwitch.state);
        assertTrue(seasonSwitch.ac.isOn);
        assertTrue(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = COOL (1), testing boundary values around 1
    @Test
    public void testCoolWhenStateIsCool() {
        seasonSwitch.state = 1; // COOL
        seasonSwitch.cool();
        assertEquals(SeasonSwitch.COOL, seasonSwitch.state);
        assertFalse(seasonSwitch.ac.isOn); // Should remain off
    }

    // Boundary: state = HEAT (2), testing boundary values around 2
    @Test
    public void testCoolWhenStateIsHeat() {
        seasonSwitch.state = 2; // HEAT
        seasonSwitch.cool();
        assertEquals(SeasonSwitch.COOL, seasonSwitch.state);
        assertTrue(seasonSwitch.ac.isOn);
        assertTrue(seasonSwitch.heater.isOn); // Heater should be off after transition
        assertTrue(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = OFF (0), testing boundary values around 0
    @Test
    public void testHeatWhenStateIsOff() {
        seasonSwitch.state = 0; // OFF
        seasonSwitch.heat();
        assertEquals(SeasonSwitch.HEAT, seasonSwitch.state);
        assertTrue(seasonSwitch.heater.isOn);
        assertTrue(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = HEAT (2), testing boundary values around 2
    @Test
    public void testHeatWhenStateIsHeat() {
        seasonSwitch.state = 2; // HEAT
        seasonSwitch.heat();
        assertEquals(SeasonSwitch.HEAT, seasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn); // Should remain off
    }

    // Boundary: state = COOL (1), testing boundary values around 1
    @Test
    public void testHeatWhenStateIsCool() {
        seasonSwitch.state = 1; // COOL
        seasonSwitch.heat();
        assertEquals(SeasonSwitch.HEAT, seasonSwitch.state);
        assertTrue(seasonSwitch.heater.isOn);
        assertTrue(seasonSwitch.ac.isOn); // AC should be off after transition
        assertTrue(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = OFF (0), testing boundary values around 0
    @Test
    public void testOffWhenStateIsOff() {
        seasonSwitch.state = 0; // OFF
        seasonSwitch.off();
        assertEquals(SeasonSwitch.OFF, seasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn);
        assertFalse(seasonSwitch.ac.isOn);
        assertFalse(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = HEAT (2), testing boundary values around 2
    @Test
    public void testOffWhenStateIsHeat() {
        seasonSwitch.state = 2; // HEAT
        seasonSwitch.off();
        assertEquals(SeasonSwitch.OFF, seasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn);
        assertFalse(seasonSwitch.ac.isOn);
        assertFalse(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = COOL (1), testing boundary values around 1
    @Test
    public void testOffWhenStateIsCool() {
        seasonSwitch.state = 1; // COOL
        seasonSwitch.off();
        assertEquals(SeasonSwitch.OFF, seasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn);
        assertFalse(seasonSwitch.ac.isOn);
        assertFalse(seasonSwitch.timer.isRunning());
    }

    // Boundary: room.temp = coolTemp (68), testing boundary values around 68
    @Test
    public void testTimerOffWhenRoomTempEqualsCoolTemp() {
        seasonSwitch.state = 1; // COOL
        seasonSwitch.room.temp = 68;
        seasonSwitch.timerOff();
        assertFalse(seasonSwitch.ac.isOn); // Should turn off when temp equals coolTemp
    }

    // Boundary: room.temp = coolTemp + 1 (69), testing boundary values around 68
    @Test
    public void testTimerOffWhenRoomTempAboveCoolTemp() {
        seasonSwitch.state = 1; // COOL
        seasonSwitch.room.temp = 69;
        seasonSwitch.timerOff();
        assertTrue(seasonSwitch.ac.isOn); // Should turn on when temp > coolTemp
    }

    // Boundary: room.temp = coolTemp - 1 (67), testing boundary values around 68
    @Test
    public void testTimerOffWhenRoomTempBelowCoolTemp() {
        seasonSwitch.state = 1; // COOL
        seasonSwitch.room.temp = 67;
        seasonSwitch.timerOff();
        assertFalse(seasonSwitch.ac.isOn); // Should stay off when temp < coolTemp
    }

    // Boundary: room.temp = heatTemp (77), testing boundary values around 77
    @Test
    public void testTimerOffWhenRoomTempEqualsHeatTemp() {
        seasonSwitch.state = 2; // HEAT
        seasonSwitch.room.temp = 77;
        seasonSwitch.timerOff();
        assertFalse(seasonSwitch.heater.isOn); // Should turn off when temp equals heatTemp
    }

    // Boundary: room.temp = heatTemp - 1 (76), testing boundary values around 77
    @Test
    public void testTimerOffWhenRoomTempBelowHeatTemp() {
        seasonSwitch.state = 2; // HEAT
        seasonSwitch.room.temp = 76;
        seasonSwitch.timerOff();
        assertTrue(seasonSwitch.heater.isOn); // Should turn on when temp < heatTemp
    }

    // Boundary: room.temp = heatTemp + 1 (78), testing boundary values around 77
    @Test
    public void testTimerOffWhenRoomTempAboveHeatTemp() {
        seasonSwitch.state = 2; // HEAT
        seasonSwitch.room.temp = 78;
        seasonSwitch.timerOff();
        assertFalse(seasonSwitch.heater.isOn); // Should turn off when temp > heatTemp
    }

    // Boundary: room.temp = 70 (initial temp), testing boundary values around 70
    @Test
    public void testActionPerformedWithCoolStateAndTempAtBoundary() {
        seasonSwitch.state = 1; // COOL
        seasonSwitch.room.temp = 68;
        seasonSwitch.actionPerformed(null);
        assertFalse(seasonSwitch.ac.isOn);
    }

    // Boundary: room.temp = 70 (initial temp), testing boundary values around 70
    @Test
    public void testActionPerformedWithHeatStateAndTempAtBoundary() {
        seasonSwitch.state = 2; // HEAT
        seasonSwitch.room.temp = 77;
        seasonSwitch.actionPerformed(null);
        assertFalse(seasonSwitch.heater.isOn);
    }
}