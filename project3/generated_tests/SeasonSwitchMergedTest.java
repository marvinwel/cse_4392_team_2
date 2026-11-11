package cse4392;

import org.junit.jupiter.api.*;
import javax.swing.Timer;
import java.awt.event.ActionEvent;
import java.util.concurrent.CountDownLatch;
import static org.junit.jupiter.api.Assertions.*;
import java.lang.reflect.Field;

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

    @BeforeEach
    public void setUpBVA() {
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
    public void tearDownBVA() {
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
        // Should remain off
        assertFalse(seasonSwitch.ac.isOn);
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
        // Heater should be off after transition
        assertTrue(seasonSwitch.heater.isOn);
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
        // AC should be off after transition
        assertFalse(seasonSwitch.ac.isOn);
        assertTrue(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = HEAT (2), testing boundary values around 2
    @Test
    public void testHeatWhenStateIsHeatBoundaryValue() {
        // State is 2 (HEAT)
        seasonSwitch.heat();
        assertEquals(SeasonSwitch.HEAT, seasonSwitch.state);
        // Should remain off
        assertFalse(seasonSwitch.heater.isOn);
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
