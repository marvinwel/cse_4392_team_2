# Change log — original

## 1.  — initial generation

## 2.  — initial generation

## 3.  — 

## 4.  — 

## 5.  — Two issues must be fixed: (1) actionPerformed() is a public method but has no test. Add at least one test that calls ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, "")) with an appropriate state (e.g., COOL with room.temp > coolTemp) and verifies the resulting AC/heater state, confirming it delegates to timerOff(). (2) testBVATimerOffCoolAcWasOffTempAboveCool is a duplicate of testBVATimerOffCoolTempPlusOne (same state, same temp=coolTemp+1, same initial ac.isOn=false, same assertion); remove one. Similarly, testBVATimerOffHeatHeaterWasOffTempBelowHeat is a duplicate of testBVATimerOffHeatTempMinusOne (same state, same temp=heatTemp-1, same initial heater.isOn=false, same assertion); remove one.

```diff
--- SeasonSwitchBVTest.java (before)
+++ SeasonSwitchBVTest.java (after)
@@ -3,6 +3,8 @@
 import org.junit.jupiter.api.AfterEach;
 import org.junit.jupiter.api.BeforeEach;
 import org.junit.jupiter.api.Test;
+
+import java.awt.event.ActionEvent;
 
 import static org.junit.jupiter.api.Assertions.*;
 
@@ -31,7 +33,6 @@
     // state = OFF (MIN of valid range): cool() from OFF should start AC
     @Test
     void testBVACoolFromOffStateMin() {
-        // state == OFF (0), boundary MIN of valid state range
         SeasonSwitch.state = SeasonSwitch.OFF;
         ss.cool();
         assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
@@ -43,7 +44,6 @@
     // state = COOL (middle of valid range): cool() from COOL is a no-op
     @Test
     void testBVACoolFromCoolStateMiddle() {
-        // state == COOL (1), middle of valid state range; cool() does nothing
         SeasonSwitch.state = SeasonSwitch.COOL;
         ss.ac.isOn = true;
         ss.cool();
@@ -54,7 +54,6 @@
     // state = HEAT (MAX of valid range): cool() from HEAT should switch to AC
     @Test
     void testBVACoolFromHeatStateMax() {
-        // state == HEAT (2), boundary MAX of valid state range
         SeasonSwitch.state = SeasonSwitch.HEAT;
         ss.heater.isOn = true;
         ss.cool();
@@ -249,31 +248,6 @@
     }
 
     // -----------------------------------------------------------------------
-    // Additional boundary: timerOff() COOL with temp well above coolTemp
-    // and HEAT with temp well below heatTemp (confirming strict comparisons)
-    // -----------------------------------------------------------------------
-
-    // room.temp = coolTemp + 1 already covered; verify AC was previously off before timerOff
-    @Test
-    void testBVATimerOffCoolAcWasOffTempAboveCool() {
-        SeasonSwitch.state = SeasonSwitch.COOL;
-        ss.ac.isOn = false;
-        ss.room.temp = ss.coolTemp + 1; // 69 > 68, TRUE -> ac.on()
-        ss.timerOff();
-        assertTrue(ss.ac.isOn);
-    }
-
-    // room.temp = heatTemp - 1 already covered; verify heater was previously off before timerOff
-    @Test
-    void testBVATimerOffHeatHeaterWasOffTempBelowHeat() {
-        SeasonSwitch.state = SeasonSwitch.HEAT;
-        ss.heater.isOn = false;
-        ss.room.temp = ss.heatTemp - 1; // 76 < 77, TRUE -> heater.on()
-        ss.timerOff();
-        assertTrue(ss.heater.isOn);
-    }
-
-    // -----------------------------------------------------------------------
     // Boundary: state = -1 (MIN-1) for timerOff() — no matching case, no-op
     // -----------------------------------------------------------------------
 
@@ -336,4 +310,45 @@
         ss.off();
         assertFalse(ss.timer.isRunning());
     }
+
+    // -----------------------------------------------------------------------
+    // actionPerformed() delegates to timerOff(): verify via COOL state with
+    // room.temp > coolTemp — condition TRUE, so ac.on() should be called.
+    // actionPerformed() is a public method and must be covered.
+    // -----------------------------------------------------------------------
+
+    // state = COOL, room.temp = coolTemp + 1 (69 > 68, TRUE): actionPerformed
+    // calls timerOff() which calls ac.on()
+    @Test
+    void testBVAActionPerformedCoolTempAboveCoolTemp() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.room.temp = ss.coolTemp + 1; // 69 > 68, condition TRUE -> ac.on()
+        ss.ac.isOn = false;
+        ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, ""));
+        assertTrue(ss.ac.isOn); // timerOff() turned AC on
+        assertFalse(ss.heater.isOn);
+    }
+
+    // state = HEAT, room.temp = heatTemp - 1 (76 < 77, TRUE): actionPerformed
+    // calls timerOff() which calls heater.on()
+    @Test
+    void testBVAActionPerformedHeatTempBelowHeatTemp() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.room.temp = ss.heatTemp - 1; // 76 < 77, condition TRUE -> heater.on()
+        ss.heater.isOn = false;
+        ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, ""));
+        assertTrue(ss.heater.isOn); // timerOff() turned heater on
+        assertFalse(ss.ac.isOn);
+    }
+
+    // state = COOL, room.temp = coolTemp (68, NOT > 68, FALSE): actionPerformed
+    // calls timerOff() which calls ac.off()
+    @Test
+    void testBVAActionPerformedCoolTempAtCoolBoundary() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.room.temp = ss.coolTemp; // 68, 68 > 68 is FALSE -> ac.off()
+        ss.ac.isOn = true;
+        ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, ""));
+        assertFalse(ss.ac.isOn); // timerOff() turned AC off
+    }
 }
```

## 6.  — Two tests violate the EP rule that representative values must come from the MIDDLE of each class, not its edges: (1) testEPTimerOffCoolRoomTempEqualCoolTemp uses room.temp=68, which is the exact boundary between the 'temp>coolTemp' and 'temp<=coolTemp' partitions — this is a boundary value, not a middle-of-class representative, and it duplicates the partition already covered by testEPTimerOffCoolRoomTempAtOrBelowCoolTemp (temp=65). Remove this test. (2) testEPTimerOffHeatRoomTempEqualHeatTemp uses room.temp=77, which is the exact boundary between the 'temp<heatTemp' and 'temp>=heatTemp' partitions — same problem, duplicating the partition already covered by testEPTimerOffHeatRoomTempAtOrAboveHeatTemp (temp=80). Remove this test. Each partition needs exactly one test with a middle value; boundary values belong to boundary value analysis, not EP.

```diff
--- SeasonSwitchEPTest.java (before)
+++ SeasonSwitchEPTest.java (after)
@@ -135,11 +135,11 @@
         assertFalse(ss.heater.isOn);
     }
 
-    // Partition: timerOff() when state == COOL and room.temp > coolTemp (70 > 68) -> AC turns on
+    // Partition: timerOff() when state == COOL and room.temp > coolTemp (72 > 68) -> AC turns on
     @Test
     void testEPTimerOffCoolRoomTempAboveCoolTemp() {
         ss.cool(); // state = COOL
-        ss.room.temp = 72; // 72 > 68 (coolTemp), strictly greater
+        ss.room.temp = 72; // 72 > 68 (coolTemp), middle of above-threshold class
         ss.timerOff();
         assertTrue(ss.ac.isOn);
     }
@@ -148,16 +148,7 @@
     @Test
     void testEPTimerOffCoolRoomTempAtOrBelowCoolTemp() {
         ss.cool(); // state = COOL
-        ss.room.temp = 65; // 65 <= 68 (coolTemp)
-        ss.timerOff();
-        assertFalse(ss.ac.isOn);
-    }
-
-    // Partition: timerOff() when state == COOL and room.temp == coolTemp (68 == 68) -> AC turns off (not strictly greater)
-    @Test
-    void testEPTimerOffCoolRoomTempEqualCoolTemp() {
-        ss.cool(); // state = COOL
-        ss.room.temp = 68; // 68 == coolTemp, not > so AC off
+        ss.room.temp = 65; // 65 <= 68 (coolTemp), middle of at-or-below class
         ss.timerOff();
         assertFalse(ss.ac.isOn);
     }
@@ -166,7 +157,7 @@
     @Test
     void testEPTimerOffHeatRoomTempBelowHeatTemp() {
         ss.heat(); // state = HEAT
-        ss.room.temp = 74; // 74 < 77 (heatTemp), strictly less
+        ss.room.temp = 74; // 74 < 77 (heatTemp), middle of below-threshold class
         ss.timerOff();
         assertTrue(ss.heater.isOn);
     }
@@ -175,16 +166,7 @@
     @Test
     void testEPTimerOffHeatRoomTempAtOrAboveHeatTemp() {
         ss.heat(); // state = HEAT
-        ss.room.temp = 80; // 80 >= 77 (heatTemp)
-        ss.timerOff();
-        assertFalse(ss.heater.isOn);
-    }
-
-    // Partition: timerOff() when state == HEAT and room.temp == heatTemp (77 == 77) -> heater turns off (not strictly less)
-    @Test
-    void testEPTimerOffHeatRoomTempEqualHeatTemp() {
-        ss.heat(); // state = HEAT
-        ss.room.temp = 77; // 77 == heatTemp, not < so heater off
+        ss.room.temp = 80; // 80 >= 77 (heatTemp), middle of at-or-above class
         ss.timerOff();
         assertFalse(ss.heater.isOn);
     }
@@ -195,7 +177,7 @@
     @Test
     void testEPActionPerformedCoolTempAboveThreshold() {
         ss.cool(); // state = COOL
-        ss.room.temp = 73; // 73 > 68
+        ss.room.temp = 73; // 73 > 68, middle of above-threshold class
         ss.actionPerformed(null);
         assertTrue(ss.ac.isOn);
     }
@@ -204,7 +186,7 @@
     @Test
     void testEPActionPerformedHeatTempBelowThreshold() {
         ss.heat(); // state = HEAT
-        ss.room.temp = 75; // 75 < 77
+        ss.room.temp = 75; // 75 < 77, middle of below-threshold class
         ss.actionPerformed(null);
         assertTrue(ss.heater.isOn);
     }
```

## 7.  — 

## 8.  — 

## 9.  — 1. testBVATimerOffStateOff has an incorrect comment: it says 'no case match for OFF in switch' but timerOff() does have 'case OFF: break;' — the comment must be corrected to reflect that the OFF case exists and does nothing (break). 2. Technique Check 3 violation: the state variable (OFF=0, COOL=1, HEAT=2) is used only in switch statements with discrete cases, not in a numeric range comparison, so treating it as a MIN..MAX range and adding tests for state=-1 and state=3 are invented boundaries with no corresponding numeric comparison or range in the source. These tests (testBVACoolStateInvalidBelowMin, testBVAHeatStateInvalidAboveMax, testBVAOffStateInvalidBelowMin, testBVATimerOffStateInvalidAboveMax, testBVATimerOffStateInvalidBelowMin) must be removed.

```diff
--- SeasonSwitchBVTest.java (before)
+++ SeasonSwitchBVTest.java (after)
@@ -27,10 +27,11 @@
 
     // -----------------------------------------------------------------------
     // Boundaries for state constants: OFF=0, COOL=1, HEAT=2
-    // Valid range: 0..2; invalid below: -1; invalid above: 3
-    // -----------------------------------------------------------------------
-
-    // state = OFF (MIN of valid range): cool() from OFF should start AC
+    // These are discrete switch-case values, not a numeric range comparison.
+    // Tests cover each valid state value for each public method.
+    // -----------------------------------------------------------------------
+
+    // state = OFF: cool() from OFF should start AC and set state to COOL
     @Test
     void testBVACoolFromOffStateMin() {
         SeasonSwitch.state = SeasonSwitch.OFF;
@@ -41,7 +42,7 @@
         assertTrue(ss.timer.isRunning());
     }
 
-    // state = COOL (middle of valid range): cool() from COOL is a no-op
+    // state = COOL: cool() from COOL is a no-op
     @Test
     void testBVACoolFromCoolStateMiddle() {
         SeasonSwitch.state = SeasonSwitch.COOL;
@@ -51,7 +52,7 @@
         assertTrue(ss.ac.isOn); // unchanged
     }
 
-    // state = HEAT (MAX of valid range): cool() from HEAT should switch to AC
+    // state = HEAT: cool() from HEAT should turn off heater, turn on AC, set state to COOL
     @Test
     void testBVACoolFromHeatStateMax() {
         SeasonSwitch.state = SeasonSwitch.HEAT;
@@ -63,7 +64,7 @@
         assertTrue(ss.timer.isRunning());
     }
 
-    // state = OFF (MIN): heat() from OFF should start heater
+    // state = OFF: heat() from OFF should start heater and set state to HEAT
     @Test
     void testBVAHeatFromOffStateMin() {
         SeasonSwitch.state = SeasonSwitch.OFF;
@@ -73,7 +74,7 @@
         assertTrue(ss.timer.isRunning());
     }
 
-    // state = HEAT (MAX): heat() from HEAT is a no-op
+    // state = HEAT: heat() from HEAT is a no-op
     @Test
     void testBVAHeatFromHeatStateMax() {
         SeasonSwitch.state = SeasonSwitch.HEAT;
@@ -83,7 +84,7 @@
         assertTrue(ss.heater.isOn); // unchanged
     }
 
-    // state = COOL (middle): heat() from COOL should switch to heater
+    // state = COOL: heat() from COOL should turn off AC, turn on heater, set state to HEAT
     @Test
     void testBVAHeatFromCoolStateMiddle() {
         SeasonSwitch.state = SeasonSwitch.COOL;
@@ -95,7 +96,7 @@
         assertTrue(ss.timer.isRunning());
     }
 
-    // state = OFF (MIN): off() from OFF is a no-op
+    // state = OFF: off() from OFF is a no-op (case OFF: break)
     @Test
     void testBVAOffFromOffStateMin() {
         SeasonSwitch.state = SeasonSwitch.OFF;
@@ -105,7 +106,7 @@
         assertFalse(ss.heater.isOn);
     }
 
-    // state = HEAT (MAX): off() from HEAT should stop heater
+    // state = HEAT: off() from HEAT should stop heater and timer, set state to OFF
     @Test
     void testBVAOffFromHeatStateMax() {
         SeasonSwitch.state = SeasonSwitch.HEAT;
@@ -117,7 +118,7 @@
         assertFalse(ss.timer.isRunning());
     }
 
-    // state = COOL (middle): off() from COOL should stop AC
+    // state = COOL: off() from COOL should stop AC and timer, set state to OFF
     @Test
     void testBVAOffFromCoolStateMiddle() {
         SeasonSwitch.state = SeasonSwitch.COOL;
@@ -129,46 +130,9 @@
         assertFalse(ss.timer.isRunning());
     }
 
-    // state = -1 (MIN-1, invalid): cool() has no case for -1, does nothing
-    @Test
-    void testBVACoolStateInvalidBelowMin() {
-        SeasonSwitch.state = -1; // below OFF=0, no matching case
-        ss.cool();
-        assertEquals(-1, SeasonSwitch.state); // state unchanged
-        assertFalse(ss.ac.isOn);
-        assertFalse(ss.heater.isOn);
-    }
-
-    // state = 3 (MAX+1, invalid): heat() has no case for 3, does nothing
-    @Test
-    void testBVAHeatStateInvalidAboveMax() {
-        SeasonSwitch.state = 3; // above HEAT=2, no matching case
-        ss.heat();
-        assertEquals(3, SeasonSwitch.state); // state unchanged
-        assertFalse(ss.heater.isOn);
-    }
-
-    // state = -1 (MIN-1, invalid): off() has no case for -1, does nothing
-    @Test
-    void testBVAOffStateInvalidBelowMin() {
-        SeasonSwitch.state = -1;
-        ss.off();
-        assertEquals(-1, SeasonSwitch.state);
-    }
-
-    // state = 3 (MAX+1, invalid): timerOff() has no case for 3, does nothing
-    @Test
-    void testBVATimerOffStateInvalidAboveMax() {
-        SeasonSwitch.state = 3;
-        ss.ac.isOn = true;
-        ss.timerOff();
-        assertEquals(3, SeasonSwitch.state);
-        assertTrue(ss.ac.isOn); // unchanged
-    }
-
     // -----------------------------------------------------------------------
     // Boundaries for timerOff() COOL branch: room.temp > coolTemp (68)
-    // Condition is TRUE when room.temp > 68, i.e. strictly greater than.
+    // Condition is TRUE when room.temp > 68 (strict greater-than).
     // Boundary N = coolTemp = 68
     // -----------------------------------------------------------------------
 
@@ -176,7 +140,7 @@
     @Test
     void testBVATimerOffCoolTempMinusOne() {
         SeasonSwitch.state = SeasonSwitch.COOL;
-        ss.room.temp = ss.coolTemp - 1; // 67, temp > 68 is FALSE
+        ss.room.temp = ss.coolTemp - 1; // 67, 67 > 68 is FALSE
         ss.timerOff();
         assertFalse(ss.ac.isOn); // ac turned off
     }
@@ -185,7 +149,7 @@
     @Test
     void testBVATimerOffCoolTempAtBoundary() {
         SeasonSwitch.state = SeasonSwitch.COOL;
-        ss.room.temp = ss.coolTemp; // 68, temp > 68 is FALSE (strict >)
+        ss.room.temp = ss.coolTemp; // 68, 68 > 68 is FALSE (strict >)
         ss.timerOff();
         assertFalse(ss.ac.isOn); // ac turned off
     }
@@ -194,14 +158,14 @@
     @Test
     void testBVATimerOffCoolTempPlusOne() {
         SeasonSwitch.state = SeasonSwitch.COOL;
-        ss.room.temp = ss.coolTemp + 1; // 69, temp > 68 is TRUE
+        ss.room.temp = ss.coolTemp + 1; // 69, 69 > 68 is TRUE
         ss.timerOff();
         assertTrue(ss.ac.isOn); // ac turned on
     }
 
     // -----------------------------------------------------------------------
     // Boundaries for timerOff() HEAT branch: room.temp < heatTemp (77)
-    // Condition is TRUE when room.temp < 77, i.e. strictly less than.
+    // Condition is TRUE when room.temp < 77 (strict less-than).
     // Boundary N = heatTemp = 77
     // -----------------------------------------------------------------------
 
@@ -209,7 +173,7 @@
     @Test
     void testBVATimerOffHeatTempMinusOne() {
         SeasonSwitch.state = SeasonSwitch.HEAT;
-        ss.room.temp = ss.heatTemp - 1; // 76, temp < 77 is TRUE
+        ss.room.temp = ss.heatTemp - 1; // 76, 76 < 77 is TRUE
         ss.timerOff();
         assertTrue(ss.heater.isOn); // heater turned on
     }
@@ -218,7 +182,7 @@
     @Test
     void testBVATimerOffHeatTempAtBoundary() {
         SeasonSwitch.state = SeasonSwitch.HEAT;
-        ss.room.temp = ss.heatTemp; // 77, temp < 77 is FALSE (strict <)
+        ss.room.temp = ss.heatTemp; // 77, 77 < 77 is FALSE (strict <)
         ss.timerOff();
         assertFalse(ss.heater.isOn); // heater turned off
     }
@@ -227,16 +191,16 @@
     @Test
     void testBVATimerOffHeatTempPlusOne() {
         SeasonSwitch.state = SeasonSwitch.HEAT;
-        ss.room.temp = ss.heatTemp + 1; // 78, temp < 77 is FALSE
+        ss.room.temp = ss.heatTemp + 1; // 78, 78 < 77 is FALSE
         ss.timerOff();
         assertFalse(ss.heater.isOn); // heater turned off
     }
 
     // -----------------------------------------------------------------------
-    // timerOff() with state = OFF: no action taken regardless of temp
-    // -----------------------------------------------------------------------
-
-    // state = OFF: timerOff() does nothing (no case match for OFF in switch)
+    // timerOff() with state = OFF: case OFF: break — exists and does nothing
+    // -----------------------------------------------------------------------
+
+    // state = OFF: timerOff() hits case OFF: break, no device changes
     @Test
     void testBVATimerOffStateOff() {
         SeasonSwitch.state = SeasonSwitch.OFF;
@@ -245,20 +209,6 @@
         assertFalse(ss.ac.isOn);
         assertFalse(ss.heater.isOn);
         assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
-    }
-
-    // -----------------------------------------------------------------------
-    // Boundary: state = -1 (MIN-1) for timerOff() — no matching case, no-op
-    // -----------------------------------------------------------------------
-
-    @Test
-    void testBVATimerOffStateInvalidBelowMin() {
-        SeasonSwitch.state = -1;
-        ss.room.temp = ss.coolTemp + 1;
-        ss.timerOff();
-        assertFalse(ss.ac.isOn);
-        assertFalse(ss.heater.isOn);
-        assertEquals(-1, SeasonSwitch.state);
     }
 
     // -----------------------------------------------------------------------
@@ -351,4 +301,15 @@
         ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, ""));
         assertFalse(ss.ac.isOn); // timerOff() turned AC off
     }
+
+    // state = HEAT, room.temp = heatTemp (77, NOT < 77, FALSE): actionPerformed
+    // calls timerOff() which calls heater.off()
+    @Test
+    void testBVAActionPerformedHeatTempAtHeatBoundary() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.room.temp = ss.heatTemp; // 77, 77 < 77 is FALSE -> heater.off()
+        ss.heater.isOn = true;
+        ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, ""));
+        assertFalse(ss.heater.isOn); // timerOff() turned heater off
+    }
 }
```

## 10.  — 

## 11.  — 

## 12.  — 

## 13. test — Target 13 measured missing branch line(s)

```diff
--- approved JUnit suite (before)
+++ approved JUnit suite (after)
@@ -477,4 +477,112 @@
         // timerOff() turned heater off
         assertFalse(ss.heater.isOn);
     }
+
+    @Test
+    void testCoolSwitchDefaultBranch() {
+        SeasonSwitch.state = 99;
+        ss.cool();
+        assertEquals(99, SeasonSwitch.state);
+        assertFalse(ss.ac.isOn);
+    }
+
+    @Test
+    void testHeatSwitchDefaultBranch() {
+        SeasonSwitch.state = 99;
+        ss.heat();
+        assertEquals(99, SeasonSwitch.state);
+        assertFalse(ss.heater.isOn);
+    }
+
+    @Test
+    void testOffSwitchDefaultBranch() {
+        SeasonSwitch.state = 99;
+        ss.off();
+        assertEquals(99, SeasonSwitch.state);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+    }
+
+    @Test
+    void testTimerOffSwitchDefaultBranch() {
+        SeasonSwitch.state = 99;
+        ss.timerOff();
+        assertEquals(99, SeasonSwitch.state);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+    }
+
+    @Test
+    void testMainNoArgs() throws Exception {
+        ExitTrap.Result r = ExitTrap.runMain(1500);
+        assertFalse(r.exitedByItself);
+        assertTrue(r.output.contains("Cooling started"));
+    }
+
+    @Test
+    void testMainOffArg() throws Exception {
+        ExitTrap.Result r = ExitTrap.runMain("off");
+        assertTrue(r.exitedByItself);
+        assertEquals(0, r.exitCode);
+        assertTrue(r.output.contains("System off"));
+    }
+
+    @Test
+    void testMainCoolArg() throws Exception {
+        ExitTrap.Result r = ExitTrap.runMain(1500, "cool");
+        assertFalse(r.exitedByItself);
+        assertTrue(r.output.contains("Cooling started"));
+    }
+
+    @Test
+    void testMainUnknownArg() throws Exception {
+        ExitTrap.Result r = ExitTrap.runMain("unknown");
+        assertTrue(r.exitedByItself);
+        assertEquals(1, r.exitCode);
+        assertTrue(r.output.contains("Unknown command"));
+    }
+
+    @Test
+    void testRoomActionPerformedDefaultBranch() {
+        SeasonSwitch.state = 99;
+        int tempBefore = ss.room.temp;
+        ss.room.actionPerformed(null);
+        assertEquals(tempBefore, ss.room.temp);
+    }
+
+    @Test
+    void testRoomActionPerformedCoolAcOn() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        int tempBefore = ss.room.temp;
+        ss.room.actionPerformed(null);
+        assertEquals(tempBefore - 1, ss.room.temp);
+    }
+
+    @Test
+    void testRoomActionPerformedCoolAcOff() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = false;
+        int tempBefore = ss.room.temp;
+        ss.room.actionPerformed(null);
+        assertEquals(tempBefore + 1, ss.room.temp);
+    }
+
+    @Test
+    void testRoomActionPerformedHeatHeaterOn() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        int tempBefore = ss.room.temp;
+        ss.room.actionPerformed(null);
+        assertEquals(tempBefore + 1, ss.room.temp);
+    }
+
+    @Test
+    void testRoomActionPerformedHeatHeaterOff() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = false;
+        int tempBefore = ss.room.temp;
+        ss.room.actionPerformed(null);
+        assertEquals(tempBefore - 1, ss.room.temp);
+    }
 }
```

## 14.  — 

## 15. test — Target 2 measured missing branch line(s)

```diff
--- approved JUnit suite (before)
+++ approved JUnit suite (after)
@@ -585,4 +585,19 @@
         ss.room.actionPerformed(null);
         assertEquals(tempBefore - 1, ss.room.temp);
     }
+
+    @Test
+    void testMainHeatArg() throws Exception {
+        ExitTrap.Result r = ExitTrap.runMain(1500, "heat");
+        assertFalse(r.exitedByItself);
+        assertTrue(r.output.contains("Heating started"));
+    }
+
+    @Test
+    void testRoomActionPerformedStateOff() {
+        SeasonSwitch.state = SeasonSwitch.OFF;
+        int tempBefore = ss.room.temp;
+        ss.room.actionPerformed(null);
+        assertEquals(tempBefore, ss.room.temp);
+    }
 }
```

## 16.  — 
