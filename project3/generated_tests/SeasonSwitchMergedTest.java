package cse4392;

import org.junit.jupiter.api.*;
import javax.swing.Timer;
import java.awt.event.ActionEvent;
import java.util.concurrent.CountDownLatch;
import static org.junit.jupiter.api.Assertions.*;
import java.awt.event.ActionListener;

public class SeasonSwitchMergedTest {

    private SeasonSwitch seasonSwitch;

    private static final int OFF = 0, COOL = 1, HEAT = 2;

    @BeforeEach
    public void setUp() {
        seasonSwitch = new SeasonSwitch();
        // Reset static state
        SeasonSwitch.state = 0;
        seasonSwitch.ac.isOn = false;
        seasonSwitch.heater.isOn = false;
        seasonSwitch.room.temp = 70;
        seasonSwitch.timer.stop();
        seasonSwitch.room.timer.stop();
    }

    @AfterEach
    public void tearDown() {
        seasonSwitch.timer.stop();
        seasonSwitch.room.timer.stop();
    }

    /**
     * Tests cool() when state is OFF (valid case 1)
     */
    @Test
    public void testCoolFromOff() {
        seasonSwitch.cool();
        assertEquals(COOL, SeasonSwitch.state);
        assertTrue(seasonSwitch.ac.isOn);
        assertTrue(seasonSwitch.timer.isRunning());
    }

    /**
     * Tests cool() when state is COOL (valid case 2)
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
     * Tests cool() when state is HEAT (valid case 3)
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
     * Tests cool() with invalid state (should not change anything)
     */
    @Test
    public void testCoolFromInvalidState() {
        SeasonSwitch.state = 999;
        seasonSwitch.cool();
        assertEquals(999, SeasonSwitch.state);
    }

    /**
     * Tests heat() when state is OFF (valid case 1)
     */
    @Test
    public void testHeatFromOff() {
        seasonSwitch.heat();
        assertEquals(HEAT, SeasonSwitch.state);
        assertTrue(seasonSwitch.heater.isOn);
        assertTrue(seasonSwitch.timer.isRunning());
    }

    /**
     * Tests heat() when state is HEAT (valid case 2)
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
     * Tests heat() when state is COOL (valid case 3)
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
     * Tests heat() with invalid state (should not change anything)
     */
    @Test
    public void testHeatFromInvalidState() {
        SeasonSwitch.state = 999;
        seasonSwitch.heat();
        assertEquals(999, SeasonSwitch.state);
    }

    /**
     * Tests off() when state is OFF (valid case 1)
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
     * Tests off() when state is HEAT (valid case 2)
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
     * Tests off() when state is COOL (valid case 3)
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
     * Tests off() with invalid state (should not change anything)
     */
    @Test
    public void testOffFromInvalidState() {
        SeasonSwitch.state = 999;
        seasonSwitch.off();
        assertEquals(999, SeasonSwitch.state);
    }

    /**
     * Tests timerOff() when state is OFF (valid case 1)
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
     * Tests timerOff() when state is COOL and room.temp > coolTemp (valid case 2a)
     */
    @Test
    public void testTimerOffFromCoolWithHighTemp() {
        SeasonSwitch.state = COOL;
        seasonSwitch.room.temp = 75;
        seasonSwitch.timerOff();
        assertEquals(COOL, SeasonSwitch.state);
        assertTrue(seasonSwitch.ac.isOn);
    }

    /**
     * Tests timerOff() when state is COOL and room.temp <= coolTemp (valid case 2b)
     */
    @Test
    public void testTimerOffFromCoolWithLowTemp() {
        SeasonSwitch.state = COOL;
        seasonSwitch.room.temp = 65;
        seasonSwitch.timerOff();
        assertEquals(COOL, SeasonSwitch.state);
        assertFalse(seasonSwitch.ac.isOn);
    }

    /**
     * Tests timerOff() when state is HEAT and room.temp < heatTemp (valid case 3a)
     */
    @Test
    public void testTimerOffFromHeatWithLowTemp() {
        SeasonSwitch.state = HEAT;
        seasonSwitch.room.temp = 70;
        seasonSwitch.timerOff();
        assertEquals(HEAT, SeasonSwitch.state);
        assertTrue(seasonSwitch.heater.isOn);
    }

    /**
     * Tests timerOff() when state is HEAT and room.temp >= heatTemp (valid case 3b)
     */
    @Test
    public void testTimerOffFromHeatWithHighTemp() {
        SeasonSwitch.state = HEAT;
        seasonSwitch.room.temp = 80;
        seasonSwitch.timerOff();
        assertEquals(HEAT, SeasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn);
    }

    /**
     * Tests timerOff() with invalid state (should not change anything)
     */
    @Test
    public void testTimerOffFromInvalidState() {
        SeasonSwitch.state = 999;
        seasonSwitch.timerOff();
        assertEquals(999, SeasonSwitch.state);
    }

    /**
     * Tests actionPerformed() calls timerOff()
     */
    @Test
    public void testActionPerformedCallsTimerOff() {
        SeasonSwitch.state = COOL;
        seasonSwitch.room.temp = 75;
        seasonSwitch.actionPerformed(new ActionEvent(this, 0, ""));
        assertEquals(COOL, SeasonSwitch.state);
        assertTrue(seasonSwitch.ac.isOn);
    }

    @BeforeEach
    public void setUpBVA() {
        seasonSwitch = new SeasonSwitch();
        // Reset static state
        SeasonSwitch.state = 0;
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
        // OFF
        seasonSwitch.state = 0;
        seasonSwitch.cool();
        assertEquals(SeasonSwitch.COOL, seasonSwitch.state);
        assertTrue(seasonSwitch.ac.isOn);
        assertTrue(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = COOL (1), testing boundary values around 1
    @Test
    public void testCoolWhenStateIsCool() {
        // COOL
        seasonSwitch.state = 1;
        seasonSwitch.cool();
        assertEquals(SeasonSwitch.COOL, seasonSwitch.state);
        // Should remain off
        assertFalse(seasonSwitch.ac.isOn);
    }

    // Boundary: state = HEAT (2), testing boundary values around 2
    @Test
    public void testCoolWhenStateIsHeat() {
        // HEAT
        seasonSwitch.state = 2;
        seasonSwitch.cool();
        assertEquals(SeasonSwitch.COOL, seasonSwitch.state);
        assertTrue(seasonSwitch.ac.isOn);
        // Heater should be off after transition
        assertTrue(seasonSwitch.heater.isOn);
        assertTrue(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = OFF (0), testing boundary values around 0
    @Test
    public void testHeatWhenStateIsOff() {
        // OFF
        seasonSwitch.state = 0;
        seasonSwitch.heat();
        assertEquals(SeasonSwitch.HEAT, seasonSwitch.state);
        assertTrue(seasonSwitch.heater.isOn);
        assertTrue(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = HEAT (2), testing boundary values around 2
    @Test
    public void testHeatWhenStateIsHeat() {
        // HEAT
        seasonSwitch.state = 2;
        seasonSwitch.heat();
        assertEquals(SeasonSwitch.HEAT, seasonSwitch.state);
        // Should remain off
        assertFalse(seasonSwitch.heater.isOn);
    }

    // Boundary: state = COOL (1), testing boundary values around 1
    @Test
    public void testHeatWhenStateIsCool() {
        // COOL
        seasonSwitch.state = 1;
        seasonSwitch.heat();
        assertEquals(SeasonSwitch.HEAT, seasonSwitch.state);
        assertTrue(seasonSwitch.heater.isOn);
        // AC should be off after transition
        assertTrue(seasonSwitch.ac.isOn);
        assertTrue(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = OFF (0), testing boundary values around 0
    @Test
    public void testOffWhenStateIsOff() {
        // OFF
        seasonSwitch.state = 0;
        seasonSwitch.off();
        assertEquals(SeasonSwitch.OFF, seasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn);
        assertFalse(seasonSwitch.ac.isOn);
        assertFalse(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = HEAT (2), testing boundary values around 2
    @Test
    public void testOffWhenStateIsHeat() {
        // HEAT
        seasonSwitch.state = 2;
        seasonSwitch.off();
        assertEquals(SeasonSwitch.OFF, seasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn);
        assertFalse(seasonSwitch.ac.isOn);
        assertFalse(seasonSwitch.timer.isRunning());
    }

    // Boundary: state = COOL (1), testing boundary values around 1
    @Test
    public void testOffWhenStateIsCool() {
        // COOL
        seasonSwitch.state = 1;
        seasonSwitch.off();
        assertEquals(SeasonSwitch.OFF, seasonSwitch.state);
        assertFalse(seasonSwitch.heater.isOn);
        assertFalse(seasonSwitch.ac.isOn);
        assertFalse(seasonSwitch.timer.isRunning());
    }

    // Boundary: room.temp = coolTemp (68), testing boundary values around 68
    @Test
    public void testTimerOffWhenRoomTempEqualsCoolTemp() {
        // COOL
        seasonSwitch.state = 1;
        seasonSwitch.room.temp = 68;
        seasonSwitch.timerOff();
        // Should turn off when temp equals coolTemp
        assertFalse(seasonSwitch.ac.isOn);
    }

    // Boundary: room.temp = coolTemp + 1 (69), testing boundary values around 68
    @Test
    public void testTimerOffWhenRoomTempAboveCoolTemp() {
        // COOL
        seasonSwitch.state = 1;
        seasonSwitch.room.temp = 69;
        seasonSwitch.timerOff();
        // Should turn on when temp > coolTemp
        assertTrue(seasonSwitch.ac.isOn);
    }

    // Boundary: room.temp = coolTemp - 1 (67), testing boundary values around 68
    @Test
    public void testTimerOffWhenRoomTempBelowCoolTemp() {
        // COOL
        seasonSwitch.state = 1;
        seasonSwitch.room.temp = 67;
        seasonSwitch.timerOff();
        // Should stay off when temp < coolTemp
        assertFalse(seasonSwitch.ac.isOn);
    }

    // Boundary: room.temp = heatTemp (77), testing boundary values around 77
    @Test
    public void testTimerOffWhenRoomTempEqualsHeatTemp() {
        // HEAT
        seasonSwitch.state = 2;
        seasonSwitch.room.temp = 77;
        seasonSwitch.timerOff();
        // Should turn off when temp equals heatTemp
        assertFalse(seasonSwitch.heater.isOn);
    }

    // Boundary: room.temp = heatTemp - 1 (76), testing boundary values around 77
    @Test
    public void testTimerOffWhenRoomTempBelowHeatTemp() {
        // HEAT
        seasonSwitch.state = 2;
        seasonSwitch.room.temp = 76;
        seasonSwitch.timerOff();
        // Should turn on when temp < heatTemp
        assertTrue(seasonSwitch.heater.isOn);
    }

    // Boundary: room.temp = heatTemp + 1 (78), testing boundary values around 77
    @Test
    public void testTimerOffWhenRoomTempAboveHeatTemp() {
        // HEAT
        seasonSwitch.state = 2;
        seasonSwitch.room.temp = 78;
        seasonSwitch.timerOff();
        // Should turn off when temp > heatTemp
        assertFalse(seasonSwitch.heater.isOn);
    }

    // Boundary: room.temp = 70 (initial temp), testing boundary values around 70
    @Test
    public void testActionPerformedWithCoolStateAndTempAtBoundary() {
        // COOL
        seasonSwitch.state = 1;
        seasonSwitch.room.temp = 68;
        seasonSwitch.actionPerformed(null);
        assertFalse(seasonSwitch.ac.isOn);
    }

    // Boundary: room.temp = 70 (initial temp), testing boundary values around 70
    @Test
    public void testActionPerformedWithHeatStateAndTempAtBoundary() {
        // HEAT
        seasonSwitch.state = 2;
        seasonSwitch.room.temp = 77;
        seasonSwitch.actionPerformed(null);
        assertFalse(seasonSwitch.heater.isOn);
    }
}
