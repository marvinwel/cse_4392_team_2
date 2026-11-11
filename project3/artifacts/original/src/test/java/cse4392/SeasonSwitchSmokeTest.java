package cse4392;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Hand-written baseline (Person 3 fixture). Proves the Maven + JUnit 5 + Surefire + JaCoCo
 * toolchain works before any LLM-generated suite exists. Deliberately covers only a few
 * branches so the JaCoCo report shows real gaps for Sarthak's gap-test generator.
 *
 * The agent runs only the approved suite (mvn -Dtest=...), so this file does not
 * inflate the coverage numbers of generated-test runs.
 */
class SeasonSwitchSmokeTest {

    private SeasonSwitch s;

    @BeforeEach
    void setUp() {
        SeasonSwitch.state = SeasonSwitch.OFF;   // static field: reset between tests
        s = new SeasonSwitch();
    }

    @AfterEach
    void tearDown() {
        s.timer.stop();
        s.room.timer.stop();
        SeasonSwitch.state = SeasonSwitch.OFF;
    }

    @Test
    void coolFromOffTurnsAcOnAndStartsTimer() {
        s.cool();
        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
        assertTrue(s.ac.isOn);
        assertFalse(s.heater.isOn);
        assertTrue(s.timer.isRunning());
    }

    @Test
    void offFromHeatTurnsHeaterOffAndStopsTimer() {
        s.heat();
        s.off();
        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
        assertFalse(s.heater.isOn);
        assertFalse(s.timer.isRunning());
    }

    @Test
    void timerOffInCoolAtThresholdStopsAc() {
        s.cool();
        s.room.temp = 68;          // coolTemp = 68; condition is temp > 68, so AC goes off
        s.timerOff();
        assertFalse(s.ac.isOn);
    }
}
