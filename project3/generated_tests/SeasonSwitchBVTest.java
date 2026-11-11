package cse4392;

import org.junit.jupiter.api.*;
import javax.swing.Timer;
import java.awt.event.ActionEvent;
import java.lang.reflect.Field;

import static org.junit.jupiter.api.Assertions.*;

public class SeasonSwitchBVTest {

    private SeasonSwitch seasonSwitch;

    @BeforeEach
    public void setUp() {
        seasonSwitch = new SeasonSwitch();
        // Reset static state
        try {
            Field stateField = SeasonSwitch.class.getDeclaredField("state");
            stateField.setAccessible(true);
            stateField.setInt(null, 0);
        } catch (Exception e) {
            fail("Failed to reset static state");
        }
    }

    @AfterEach
    public void tearDown() {
        if (seasonSwitch.timer != null && seasonSwitch.timer.isRunning()) {
            seasonSwitch.timer.stop();
        }
        if (seasonSwitch.room.timer != null && seasonSwitch.room.timer.isRunning()) {
            seasonSwitch.room.timer.stop();
        }
    }

    // Boundary: state = OFF (0), testing boundary values around 0
    @Test
    public void testCoolWhenStateIsOffBoundaryValue() {
        // State is 0 (OFF)
        seasonSwitch.cool();
        assertEquals(SeasonSwitch.COOL, seasonSwitch.state);
        assertTrue(seasonSwitch.ac.isOn);
        assertTrue(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = COOL (1), testing boundary values around 1
    @Test
    public void testCoolWhenStateIsCoolBoundaryValue() {
        // Set state to COOL
        try {
            Field stateField = SeasonSwitch.class.getDeclaredField("state");
            stateField.setAccessible(true);
            stateField.setInt(null, SeasonSwitch.COOL);
        } catch (Exception e) {
            fail("Failed to set state to COOL");
        }
        seasonSwitch.cool();
        assertEquals(SeasonSwitch.COOL, seasonSwitch.state);
        assertFalse(seasonSwitch.ac.isOn); // Should remain off
    }

    // Boundary: state = HEAT (2), testing boundary values around 2
    @Test
    public void testCoolWhenStateIsHeatBoundaryValue() {
        // Set state to HEAT
        try {
            Field stateField = SeasonSwitch.class.getDeclaredField("state");
            stateField.setAccessible(true);
            stateField.setInt(null, SeasonSwitch.HEAT);
        } catch (Exception e) {
            fail("Failed to set state to HEAT");
        }
        seasonSwitch.cool();
        assertEquals(SeasonSwitch.COOL, seasonSwitch.state);
        assertTrue(seasonSwitch.ac.isOn);
        assertTrue(seasonSwitch.heater.isOn); // Heater should be off after transition
        assertTrue(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = OFF (0), testing boundary values around 0
    @Test
    public void testHeatWhenStateIsOffBoundaryValue() {
        // State is 0 (OFF)
        seasonSwitch.heat();
        assertEquals(SeasonSwitch.HEAT, seasonSwitch.state);
        assertTrue(seasonSwitch.heater.isOn);
        assertTrue(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = COOL (1), testing boundary values around 1
    @Test
    public void testHeatWhenStateIsCoolBoundaryValue() {
        // Set state to COOL
        try {
            Field stateField = SeasonSwitch.class.getDeclaredField("state");
            stateField.setAccessible(true);
            stateField.setInt(null, SeasonSwitch.COOL);
        } catch (Exception e) {
            fail("Failed to set state to COOL");
        }
        seasonSwitch.heat();
        assertEquals(SeasonSwitch.HEAT, seasonSwitch.state);
        assertTrue(seasonSwitch.heater.isOn);
        assertFalse(seasonSwitch.ac.isOn); // AC should be off after transition
        assertTrue(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = HEAT (2), testing boundary values around 2
    @Test
    public void testHeatWhenStateIsHeatBoundaryValue() {
        // State is 2 (HEAT)
        seasonSwitch.heat();
        assertEquals(SeasonSwitch.HEAT, seasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn); // Should remain off
    }

    // Boundary: state = OFF (0), testing boundary values around 0
    @Test
    public void testOffWhenStateIsOffBoundaryValue() {
        // State is 0 (OFF)
        seasonSwitch.off();
        assertEquals(SeasonSwitch.OFF, seasonSwitch.state);
        assertFalse(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = COOL (1), testing boundary values around 1
    @Test
    public void testOffWhenStateIsCoolBoundaryValue() {
        // Set state to COOL
        try {
            Field stateField = SeasonSwitch.class.getDeclaredField("state");
            stateField.setAccessible(true);
            stateField.setInt(null, SeasonSwitch.COOL);
        } catch (Exception e) {
            fail("Failed to set state to COOL");
        }
        seasonSwitch.off();
        assertEquals(SeasonSwitch.OFF, seasonSwitch.state);
        assertFalse(seasonSwitch.ac.isOn);
        assertFalse(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = HEAT (2), testing boundary values around 2
    @Test
    public void testOffWhenStateIsHeatBoundaryValue() {
        // Set state to HEAT
        try {
            Field stateField = SeasonSwitch.class.getDeclaredField("state");
            stateField.setAccessible(true);
            stateField.setInt(null, SeasonSwitch.HEAT);
        } catch (Exception e) {
            fail("Failed to set state to HEAT");
        }
        seasonSwitch.off();
        assertEquals(SeasonSwitch.OFF, seasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn);
        assertFalse(seasonSwitch.timer.isRunning());
    }

    // Boundary: room.temp = coolTemp - 1 (67), testing boundary values around 68
    @Test
    public void testTimerOffWhenRoomTempBelowCoolTempBoundaryValue() {
        // Set room temperature below coolTemp
        seasonSwitch.room.temp = 67;
        try {
            Field stateField = SeasonSwitch.class.getDeclaredField("state");
            stateField.setAccessible(true);
            stateField.setInt(null, SeasonSwitch.COOL);
        } catch (Exception e) {
            fail("Failed to set state to COOL");
        }
        seasonSwitch.timerOff();
        assertTrue(seasonSwitch.ac.isOn);
    }

    // Boundary: room.temp = coolTemp (68), testing boundary values around 68
    @Test
    public void testTimerOffWhenRoomTempAtCoolTempBoundaryValue() {
        // Set room temperature at coolTemp
        seasonSwitch.room.temp = 68;
        try {
            Field stateField = SeasonSwitch.class.getDeclaredField("state");
            stateField.setAccessible(true);
            stateField.setInt(null, SeasonSwitch.COOL);
        } catch (Exception e) {
            fail("Failed to set state to COOL");
        }
        seasonSwitch.timerOff();
        assertFalse(seasonSwitch.ac.isOn);
    }

    // Boundary: room.temp = coolTemp + 1 (69), testing boundary values around 68
    @Test
    public void testTimerOffWhenRoomTempAboveCoolTempBoundaryValue() {
        // Set room temperature above coolTemp
        seasonSwitch.room.temp = 69;
        try {
            Field stateField = SeasonSwitch.class.getDeclaredField("state");
            stateField.setAccessible(true);
            stateField.setInt(null, SeasonSwitch.COOL);
        } catch (Exception e) {
            fail("Failed to set state to COOL");
        }
        seasonSwitch.timerOff();
        assertFalse(seasonSwitch.ac.isOn);
    }

    // Boundary: room.temp = heatTemp - 1 (76), testing boundary values around 77
    @Test
    public void testTimerOffWhenRoomTempBelowHeatTempBoundaryValue() {
        // Set room temperature below heatTemp
        seasonSwitch.room.temp = 76;
        try {
            Field stateField = SeasonSwitch.class.getDeclaredField("state");
            stateField.setAccessible(true);
            stateField.setInt(null, SeasonSwitch.HEAT);
        } catch (Exception e) {
            fail("Failed to set state to HEAT");
        }
        seasonSwitch.timerOff();
        assertTrue(seasonSwitch.heater.isOn);
    }

    // Boundary: room.temp = heatTemp (77), testing boundary values around 77
    @Test
    public void testTimerOffWhenRoomTempAtHeatTempBoundaryValue() {
        // Set room temperature at heatTemp
        seasonSwitch.room.temp = 77;
        try {
            Field stateField = SeasonSwitch.class.getDeclaredField("state");
            stateField.setAccessible(true);
            stateField.setInt(null, SeasonSwitch.HEAT);
        } catch (Exception e) {
            fail("Failed to set state to HEAT");
        }
        seasonSwitch.timerOff();
        assertFalse(seasonSwitch.heater.isOn);
    }

    // Boundary: room.temp = heatTemp + 1 (78), testing boundary values around 77
    @Test
    public void testTimerOffWhenRoomTempAboveHeatTempBoundaryValue() {
        // Set room temperature above heatTemp
        seasonSwitch.room.temp = 78;
        try {
            Field stateField = SeasonSwitch.class.getDeclaredField("state");
            stateField.setAccessible(true);
            stateField.setInt(null, SeasonSwitch.HEAT);
        } catch (Exception e) {
            fail("Failed to set state to HEAT");
        }
        seasonSwitch.timerOff();
        assertFalse(seasonSwitch.heater.isOn);
    }
}