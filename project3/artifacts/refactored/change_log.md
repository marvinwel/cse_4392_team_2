# Change log — refactored

## 1.  — initial generation

## 2.  — initial generation

## 3.  — 

## 4.  — 

## 5.  — 1. INVENTED BOUNDARIES FOR STATE: The state variable is not a numeric range with a MIN/MAX that the code compares against — it is an enumerated constant (OFF=0, COOL=1, HEAT=2) used only in switch statements. BVA does not apply to switch-on-enum values the same way it applies to numeric ranges. Testing state=-1 and state=3 as 'MIN-1' and 'MAX+1' invents boundaries that have no basis in the source code. There is no comparison like 'if (state >= 0 && state <= 2)'; the switch simply has no default. These eight tests (testBVACoolStateInvalidBelowMin, testBVACoolStateInvalidAboveMax, testBVAHeatStateInvalidBelowMin, testBVAHeatStateInvalidAboveMax, testBVAOffStateInvalidBelowMin, testBVAOffStateInvalidAboveMax, testBVATimerOffStateInvalidBelowMin, testBVATimerOffStateInvalidAboveMax) must be removed per check #3 ('No invented boundaries for things with no numeric comparison or range'). 2. MISSING BOUNDARY POINT FOR coolTemp: The condition is room.temp > coolTemp (i.e., > 68). BVA requires testing at N-1=67, N=68, and N+1=69. The tests cover 67, 68, and 69, which is correct, but the comment framework labels these as 'below boundary', 'at boundary', and 'above boundary' without explicitly noting that N=68 is the exact comparison value. This is acceptable as written, but the comment on testBVATimerOffCoolTempBelowBoundary says 'room.temp = coolTemp - 1' which is correct. No change needed here. 3. MISSING BOUNDARY POINT FOR heatTemp: Similarly, the condition is room.temp < heatTemp (i.e., < 77). Tests at 76, 77, and 78 are present and correct. No change needed here. 4. TIMER NOT STOPPED FOR TESTS THAT START THE TIMER: In testBVACoolFromOffStateMin, testBVACoolFromHeatStateMax, testBVAHeatFromOffStateMin, and testBVAHeatFromCoolStateMid, ss.cool() or ss.heat() starts ss.timer. The @AfterEach calls ss.timer.stop() and ss.room.timer.stop(), which is correct and sufficient — no change needed here. 5. ROOM TIMER NOT STARTED IN setUp: ss.room.timer is never started in setUp, so ss.room.timer.stop() in tearDown is harmless but the room timer is not running during tests. This is acceptable since tests do not rely on the room timer firing. 6. SUMMARY OF REQUIRED CHANGES: Remove the eight invalid-state tests for cool(), heat(), off(), and timerOff() that use state=-1 and state=3, as these represent invented boundaries not present in the source code.

```diff
--- SeasonSwitchBVTest.java (before)
+++ SeasonSwitchBVTest.java (after)
@@ -24,11 +24,10 @@
     }
 
     // -----------------------------------------------------------------------
-    // Boundaries for state constants: OFF=0, COOL=1, HEAT=2
-    // Valid range: 0..2; invalid below: -1; invalid above: 3
-    // -----------------------------------------------------------------------
-
-    // state = OFF (MIN valid boundary = 0): cool() from OFF should start AC
+    // cool() — valid state boundaries: OFF=0, COOL=1, HEAT=2
+    // -----------------------------------------------------------------------
+
+    // state = OFF (0): cool() from OFF should start AC and timer, set state=COOL
     @Test
     void testBVACoolFromOffStateMin() {
         // state == OFF (0), MIN valid boundary
@@ -38,7 +37,7 @@
         assertTrue(ss.timer.isRunning());
     }
 
-    // state = COOL (mid valid boundary = 1): cool() from COOL is no-op
+    // state = COOL (1): cool() from COOL is no-op
     @Test
     void testBVACoolFromCoolStateMid() {
         // state == COOL (1), mid valid boundary
@@ -49,7 +48,7 @@
         assertTrue(ss.ac.isOn);
     }
 
-    // state = HEAT (MAX valid boundary = 2): cool() from HEAT should switch
+    // state = HEAT (2): cool() from HEAT should turn off heater, start AC, set state=COOL
     @Test
     void testBVACoolFromHeatStateMax() {
         // state == HEAT (2), MAX valid boundary
@@ -62,29 +61,11 @@
         assertTrue(ss.timer.isRunning());
     }
 
-    // state = -1 (MIN-1, invalid): cool() switch has no default, nothing happens
-    @Test
-    void testBVACoolStateInvalidBelowMin() {
-        // state == -1, below valid range; switch has no default, no-op
-        SeasonSwitch.state = -1;
-        ss.cool();
-        assertEquals(-1, SeasonSwitch.state);
-        assertFalse(ss.ac.isOn);
-        assertFalse(ss.timer.isRunning());
-    }
-
-    // state = 3 (MAX+1, invalid): cool() switch has no default, nothing happens
-    @Test
-    void testBVACoolStateInvalidAboveMax() {
-        // state == 3, above valid range; switch has no default, no-op
-        SeasonSwitch.state = 3;
-        ss.cool();
-        assertEquals(3, SeasonSwitch.state);
-        assertFalse(ss.ac.isOn);
-        assertFalse(ss.timer.isRunning());
-    }
-
-    // state = OFF (MIN valid boundary = 0): heat() from OFF should start heater
+    // -----------------------------------------------------------------------
+    // heat() — valid state boundaries: OFF=0, COOL=1, HEAT=2
+    // -----------------------------------------------------------------------
+
+    // state = OFF (0): heat() from OFF should start heater and timer, set state=HEAT
     @Test
     void testBVAHeatFromOffStateMin() {
         // state == OFF (0), MIN valid boundary
@@ -94,7 +75,7 @@
         assertTrue(ss.timer.isRunning());
     }
 
-    // state = HEAT (MAX valid boundary = 2): heat() from HEAT is no-op
+    // state = HEAT (2): heat() from HEAT is no-op
     @Test
     void testBVAHeatFromHeatStateMax() {
         // state == HEAT (2), MAX valid boundary
@@ -105,7 +86,7 @@
         assertTrue(ss.heater.isOn);
     }
 
-    // state = COOL (mid valid boundary = 1): heat() from COOL should switch
+    // state = COOL (1): heat() from COOL should turn off AC, start heater, set state=HEAT
     @Test
     void testBVAHeatFromCoolStateMid() {
         // state == COOL (1), mid valid boundary
@@ -118,27 +99,11 @@
         assertTrue(ss.timer.isRunning());
     }
 
-    // state = -1 (MIN-1, invalid): heat() switch has no default, nothing happens
-    @Test
-    void testBVAHeatStateInvalidBelowMin() {
-        SeasonSwitch.state = -1;
-        ss.heat();
-        assertEquals(-1, SeasonSwitch.state);
-        assertFalse(ss.heater.isOn);
-        assertFalse(ss.timer.isRunning());
-    }
-
-    // state = 3 (MAX+1, invalid): heat() switch has no default, nothing happens
-    @Test
-    void testBVAHeatStateInvalidAboveMax() {
-        SeasonSwitch.state = 3;
-        ss.heat();
-        assertEquals(3, SeasonSwitch.state);
-        assertFalse(ss.heater.isOn);
-        assertFalse(ss.timer.isRunning());
-    }
-
-    // state = OFF (MIN valid boundary = 0): off() from OFF is no-op
+    // -----------------------------------------------------------------------
+    // off() — valid state boundaries: OFF=0, COOL=1, HEAT=2
+    // -----------------------------------------------------------------------
+
+    // state = OFF (0): off() from OFF is no-op
     @Test
     void testBVAOffFromOffStateMin() {
         // state == OFF (0), MIN valid boundary; off() is no-op
@@ -147,7 +112,7 @@
         assertFalse(ss.timer.isRunning());
     }
 
-    // state = COOL (mid valid boundary = 1): off() from COOL stops AC
+    // state = COOL (1): off() from COOL stops AC and timer, sets state=OFF
     @Test
     void testBVAOffFromCoolStateMid() {
         // state == COOL (1), mid valid boundary
@@ -160,7 +125,7 @@
         assertFalse(ss.timer.isRunning());
     }
 
-    // state = HEAT (MAX valid boundary = 2): off() from HEAT stops heater
+    // state = HEAT (2): off() from HEAT stops heater and timer, sets state=OFF
     @Test
     void testBVAOffFromHeatStateMax() {
         // state == HEAT (2), MAX valid boundary
@@ -173,25 +138,9 @@
         assertFalse(ss.timer.isRunning());
     }
 
-    // state = -1 (MIN-1, invalid): off() switch has no default, nothing happens
-    @Test
-    void testBVAOffStateInvalidBelowMin() {
-        SeasonSwitch.state = -1;
-        ss.off();
-        assertEquals(-1, SeasonSwitch.state);
-    }
-
-    // state = 3 (MAX+1, invalid): off() switch has no default, nothing happens
-    @Test
-    void testBVAOffStateInvalidAboveMax() {
-        SeasonSwitch.state = 3;
-        ss.off();
-        assertEquals(3, SeasonSwitch.state);
-    }
-
-    // -----------------------------------------------------------------------
-    // Boundaries for timerOff() in COOL state: condition is room.temp > coolTemp
-    // coolTemp = 68; boundaries at coolTemp-1=67, coolTemp=68, coolTemp+1=69
+    // -----------------------------------------------------------------------
+    // timerOff() in COOL state: condition is room.temp > coolTemp (strict >)
+    // coolTemp = 68; test at coolTemp-1=67, coolTemp=68, coolTemp+1=69
     // At exactly coolTemp (68): 68 > 68 is FALSE => ac.off()
     // -----------------------------------------------------------------------
 
@@ -200,16 +149,18 @@
     void testBVATimerOffCoolTempBelowBoundary() {
         // room.temp = coolTemp - 1; condition room.temp > coolTemp is FALSE
         SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
         ss.room.temp = ss.coolTemp - 1; // 67
         ss.timerOff();
         assertFalse(ss.ac.isOn);
     }
 
-    // room.temp = coolTemp = 68: 68 > 68 is FALSE => ac.off()
+    // room.temp = coolTemp = 68: 68 > 68 is FALSE (strict >) => ac.off()
     @Test
     void testBVATimerOffCoolTempAtBoundary() {
         // room.temp = coolTemp exactly; condition room.temp > coolTemp is FALSE (strict >)
         SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
         ss.room.temp = ss.coolTemp; // 68
         ss.timerOff();
         assertFalse(ss.ac.isOn);
@@ -226,8 +177,8 @@
     }
 
     // -----------------------------------------------------------------------
-    // Boundaries for timerOff() in HEAT state: condition is room.temp < heatTemp
-    // heatTemp = 77; boundaries at heatTemp-1=76, heatTemp=77, heatTemp+1=78
+    // timerOff() in HEAT state: condition is room.temp < heatTemp (strict <)
+    // heatTemp = 77; test at heatTemp-1=76, heatTemp=77, heatTemp+1=78
     // At exactly heatTemp (77): 77 < 77 is FALSE => heater.off()
     // -----------------------------------------------------------------------
 
@@ -241,11 +192,12 @@
         assertTrue(ss.heater.isOn);
     }
 
-    // room.temp = heatTemp = 77: 77 < 77 is FALSE => heater.off()
+    // room.temp = heatTemp = 77: 77 < 77 is FALSE (strict <) => heater.off()
     @Test
     void testBVATimerOffHeatTempAtBoundary() {
         // room.temp = heatTemp exactly; condition room.temp < heatTemp is FALSE (strict <)
         SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
         ss.room.temp = ss.heatTemp; // 77
         ss.timerOff();
         assertFalse(ss.heater.isOn);
@@ -256,6 +208,7 @@
     void testBVATimerOffHeatTempAboveBoundary() {
         // room.temp = heatTemp + 1; condition room.temp < heatTemp is FALSE
         SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
         ss.room.temp = ss.heatTemp + 1; // 78
         ss.timerOff();
         assertFalse(ss.heater.isOn);
@@ -276,69 +229,69 @@
     }
 
     // -----------------------------------------------------------------------
-    // timerOff() with invalid state values (no default in switch)
-    // -----------------------------------------------------------------------
-
-    // state = -1 (MIN-1, invalid): timerOff() switch has no default, nothing happens
-    @Test
-    void testBVATimerOffStateInvalidBelowMin() {
-        SeasonSwitch.state = -1;
-        ss.timerOff();
-        assertFalse(ss.ac.isOn);
-        assertFalse(ss.heater.isOn);
-    }
-
-    // state = 3 (MAX+1, invalid): timerOff() switch has no default, nothing happens
-    @Test
-    void testBVATimerOffStateInvalidAboveMax() {
-        SeasonSwitch.state = 3;
-        ss.timerOff();
-        assertFalse(ss.ac.isOn);
-        assertFalse(ss.heater.isOn);
-    }
-
-    // -----------------------------------------------------------------------
     // actionPerformed() delegates to timerOff(); verify via observable state
     // -----------------------------------------------------------------------
 
     // actionPerformed() in COOL state with room.temp > coolTemp => ac.on()
     @Test
     void testBVAActionPerformedCoolTempAboveBoundary() {
-        // actionPerformed calls timerOff(); room.temp = coolTemp+1 => ac.on()
-        SeasonSwitch.state = SeasonSwitch.COOL;
-        ss.room.temp = ss.coolTemp + 1; // 69 > 68 TRUE
-        ss.actionPerformed(null);
-        assertTrue(ss.ac.isOn);
+        // actionPerformed calls timerOff(); room.temp = coolTemp+1 => 69 > 68 TRUE => ac.on()
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.room.temp = ss.coolTemp + 1; // 69
+        ss.actionPerformed(null);
+        assertTrue(ss.ac.isOn);
+    }
+
+    // actionPerformed() in COOL state with room.temp = coolTemp => ac.off()
+    @Test
+    void testBVAActionPerformedCoolTempAtBoundary() {
+        // actionPerformed calls timerOff(); room.temp = coolTemp exactly => 68 > 68 FALSE => ac.off()
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        ss.room.temp = ss.coolTemp; // 68
+        ss.actionPerformed(null);
+        assertFalse(ss.ac.isOn);
+    }
+
+    // actionPerformed() in COOL state with room.temp = coolTemp - 1 => ac.off()
+    @Test
+    void testBVAActionPerformedCoolTempBelowBoundary() {
+        // actionPerformed calls timerOff(); room.temp = coolTemp-1 => 67 > 68 FALSE => ac.off()
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        ss.room.temp = ss.coolTemp - 1; // 67
+        ss.actionPerformed(null);
+        assertFalse(ss.ac.isOn);
     }
 
     // actionPerformed() in HEAT state with room.temp < heatTemp => heater.on()
     @Test
     void testBVAActionPerformedHeatTempBelowBoundary() {
-        // actionPerformed calls timerOff(); room.temp = heatTemp-1 => heater.on()
-        SeasonSwitch.state = SeasonSwitch.HEAT;
-        ss.room.temp = ss.heatTemp - 1; // 76 < 77 TRUE
-        ss.actionPerformed(null);
-        assertTrue(ss.heater.isOn);
-    }
-
-    // actionPerformed() in COOL state with room.temp = coolTemp => ac.off()
-    @Test
-    void testBVAActionPerformedCoolTempAtBoundary() {
-        // actionPerformed calls timerOff(); room.temp = coolTemp exactly => ac.off()
-        SeasonSwitch.state = SeasonSwitch.COOL;
-        ss.ac.isOn = true;
-        ss.room.temp = ss.coolTemp; // 68 > 68 FALSE
-        ss.actionPerformed(null);
-        assertFalse(ss.ac.isOn);
+        // actionPerformed calls timerOff(); room.temp = heatTemp-1 => 76 < 77 TRUE => heater.on()
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.room.temp = ss.heatTemp - 1; // 76
+        ss.actionPerformed(null);
+        assertTrue(ss.heater.isOn);
     }
 
     // actionPerformed() in HEAT state with room.temp = heatTemp => heater.off()
     @Test
     void testBVAActionPerformedHeatTempAtBoundary() {
-        // actionPerformed calls timerOff(); room.temp = heatTemp exactly => heater.off()
-        SeasonSwitch.state = SeasonSwitch.HEAT;
-        ss.heater.isOn = true;
-        ss.room.temp = ss.heatTemp; // 77 < 77 FALSE
+        // actionPerformed calls timerOff(); room.temp = heatTemp exactly => 77 < 77 FALSE => heater.off()
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        ss.room.temp = ss.heatTemp; // 77
+        ss.actionPerformed(null);
+        assertFalse(ss.heater.isOn);
+    }
+
+    // actionPerformed() in HEAT state with room.temp = heatTemp + 1 => heater.off()
+    @Test
+    void testBVAActionPerformedHeatTempAboveBoundary() {
+        // actionPerformed calls timerOff(); room.temp = heatTemp+1 => 78 < 77 FALSE => heater.off()
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        ss.room.temp = ss.heatTemp + 1; // 78
         ss.actionPerformed(null);
         assertFalse(ss.heater.isOn);
     }
```

## 6.  — 

## 7.  — 

## 8.  — 

## 9. test — Target 10 measured missing branch line(s)

```diff
--- approved JUnit suite (before)
+++ approved JUnit suite (after)
@@ -457,4 +457,85 @@
         ss.actionPerformed(null);
         assertFalse(ss.heater.isOn);
     }
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
+    void testMainHeatArg() throws Exception {
+        ExitTrap.Result r = ExitTrap.runMain(1500, "heat");
+        assertFalse(r.exitedByItself);
+        assertTrue(r.output.contains("Heating started"));
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
+    void testRoomActionPerformedStateOff() {
+        SeasonSwitch.state = SeasonSwitch.OFF;
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

## 10.  — 

## 11. test — Target 5 measured missing branch line(s)

```diff
--- approved JUnit suite (before)
+++ approved JUnit suite (after)
@@ -538,4 +538,48 @@
         ss.room.actionPerformed(null);
         assertEquals(tempBefore - 1, ss.room.temp);
     }
+
+    @Test
+    void testCoolDefaultBranch() {
+        SeasonSwitch.state = 99;
+        ss.cool();
+        assertEquals(99, SeasonSwitch.state);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+    }
+
+    @Test
+    void testHeatDefaultBranch() {
+        SeasonSwitch.state = 99;
+        ss.heat();
+        assertEquals(99, SeasonSwitch.state);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+    }
+
+    @Test
+    void testOffDefaultBranch() {
+        SeasonSwitch.state = 99;
+        ss.off();
+        assertEquals(99, SeasonSwitch.state);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+    }
+
+    @Test
+    void testTimerOffDefaultBranch() {
+        SeasonSwitch.state = 99;
+        ss.timerOff();
+        assertEquals(99, SeasonSwitch.state);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+    }
+
+    @Test
+    void testRoomActionPerformedDefaultBranch() {
+        SeasonSwitch.state = 99;
+        int tempBefore = ss.room.temp;
+        ss.room.actionPerformed(null);
+        assertEquals(tempBefore, ss.room.temp);
+    }
 }
```

## 12.  — 

## 13.  — initial generation

```diff
--- before
+++ after
@@ -0,0 +1,548 @@
+package cse4392;
+
+import org.junit.jupiter.api.AfterEach;
+import org.junit.jupiter.api.BeforeEach;
+import org.junit.jupiter.api.Test;
+import static org.junit.jupiter.api.Assertions.*;
+
+public class SeasonSwitchMergedTest {
+
+    SeasonSwitch ss;
+
+    @BeforeEach
+    void setUp() {
+        SeasonSwitch.state = SeasonSwitch.OFF;
+        ss = new SeasonSwitch();
+    }
+
+    @AfterEach
+    void tearDown() {
+        ss.timer.stop();
+        ss.room.timer.stop();
+        SeasonSwitch.state = SeasonSwitch.OFF;
+    }
+
+    // Partition: cool() called when state == OFF -> AC turns on, timer starts, state becomes COOL
+    @Test
+    void testEPCoolFromOff() {
+        ss.cool();
+        assertTrue(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+        assertTrue(ss.timer.isRunning());
+        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
+    }
+
+    // Partition: cool() called when state == COOL -> no change (already cooling)
+    @Test
+    void testEPCoolFromCool() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.on();
+        ss.timer.start();
+        ss.cool();
+        assertTrue(ss.ac.isOn);
+        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
+    }
+
+    // Partition: cool() called when state == HEAT -> heater off, AC on, timer starts, state becomes COOL
+    @Test
+    void testEPCoolFromHeat() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.on();
+        ss.timer.start();
+        ss.cool();
+        assertFalse(ss.heater.isOn);
+        assertTrue(ss.ac.isOn);
+        assertTrue(ss.timer.isRunning());
+        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
+    }
+
+    // Partition: heat() called when state == OFF -> heater turns on, timer starts, state becomes HEAT
+    @Test
+    void testEPHeatFromOff() {
+        ss.heat();
+        assertTrue(ss.heater.isOn);
+        assertFalse(ss.ac.isOn);
+        assertTrue(ss.timer.isRunning());
+        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
+    }
+
+    // Partition: heat() called when state == HEAT -> no change (already heating)
+    @Test
+    void testEPHeatFromHeat() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.on();
+        ss.timer.start();
+        ss.heat();
+        assertTrue(ss.heater.isOn);
+        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
+    }
+
+    // Partition: heat() called when state == COOL -> AC off, heater on, timer starts, state becomes HEAT
+    @Test
+    void testEPHeatFromCool() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.on();
+        ss.timer.start();
+        ss.heat();
+        assertFalse(ss.ac.isOn);
+        assertTrue(ss.heater.isOn);
+        assertTrue(ss.timer.isRunning());
+        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
+    }
+
+    // Partition: off() called when state == OFF -> no change
+    @Test
+    void testEPOffFromOff() {
+        ss.off();
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+        assertFalse(ss.timer.isRunning());
+        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
+    }
+
+    // Partition: off() called when state == HEAT -> heater off, timer stops, state becomes OFF
+    @Test
+    void testEPOffFromHeat() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.on();
+        ss.timer.start();
+        ss.off();
+        assertFalse(ss.heater.isOn);
+        assertFalse(ss.timer.isRunning());
+        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
+    }
+
+    // Partition: off() called when state == COOL -> AC off, timer stops, state becomes OFF
+    @Test
+    void testEPOffFromCool() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.on();
+        ss.timer.start();
+        ss.off();
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.timer.isRunning());
+        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
+    }
+
+    // Partition: timerOff() when state == OFF -> no change to AC or heater
+    @Test
+    void testEPTimerOffStateOff() {
+        ss.timerOff();
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
+    }
+
+    // Partition: timerOff() when state == COOL and room.temp > coolTemp (72 > 68) -> AC turns on
+    @Test
+    void testEPTimerOffCoolRoomTempAboveCoolTemp() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.room.temp = 72;
+        ss.timerOff();
+        assertTrue(ss.ac.isOn);
+    }
+
+    // Partition: timerOff() when state == COOL and room.temp <= coolTemp (65 <= 68) -> AC turns off
+    @Test
+    void testEPTimerOffCoolRoomTempAtOrBelowCoolTemp() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.on();
+        ss.room.temp = 65;
+        ss.timerOff();
+        assertFalse(ss.ac.isOn);
+    }
+
+    // Partition: timerOff() when state == HEAT and room.temp < heatTemp (74 < 77) -> heater turns on
+    @Test
+    void testEPTimerOffHeatRoomTempBelowHeatTemp() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.room.temp = 74;
+        ss.timerOff();
+        assertTrue(ss.heater.isOn);
+    }
+
+    // Partition: timerOff() when state == HEAT and room.temp >= heatTemp (80 >= 77) -> heater turns off
+    @Test
+    void testEPTimerOffHeatRoomTempAtOrAboveHeatTemp() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.on();
+        ss.room.temp = 80;
+        ss.timerOff();
+        assertFalse(ss.heater.isOn);
+    }
+
+    // Partition: actionPerformed() delegates to timerOff() when state == COOL and temp > coolTemp
+    @Test
+    void testEPActionPerformedCoolTempAboveThreshold() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.room.temp = 75;
+        ss.actionPerformed(null);
+        assertTrue(ss.ac.isOn);
+    }
+
+    // Partition: actionPerformed() delegates to timerOff() when state == HEAT and temp < heatTemp
+    @Test
+    void testEPActionPerformedHeatTempBelowThreshold() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.room.temp = 73;
+        ss.actionPerformed(null);
+        assertTrue(ss.heater.isOn);
+    }
+
+    // Partition: actionPerformed() delegates to timerOff() when state == OFF -> no device change
+    @Test
+    void testEPActionPerformedStateOff() {
+        ss.actionPerformed(null);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+    }
+
+    // state = OFF: cool() from OFF should start AC and timer, set state=COOL
+    @Test
+    void testBVACoolFromOffStateMin() {
+        ss.cool();
+        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
+        assertTrue(ss.ac.isOn);
+        assertTrue(ss.timer.isRunning());
+    }
+
+    // state = COOL: cool() from COOL is no-op
+    @Test
+    void testBVACoolFromCoolStateMid() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        ss.cool();
+        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
+        assertTrue(ss.ac.isOn);
+    }
+
+    // state = HEAT: cool() from HEAT should turn off heater, start AC, set state=COOL
+    @Test
+    void testBVACoolFromHeatStateMax() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        ss.cool();
+        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
+        assertFalse(ss.heater.isOn);
+        assertTrue(ss.ac.isOn);
+        assertTrue(ss.timer.isRunning());
+    }
+
+    // state = OFF: heat() from OFF should start heater and timer, set state=HEAT
+    @Test
+    void testBVAHeatFromOffStateMin() {
+        ss.heat();
+        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
+        assertTrue(ss.heater.isOn);
+        assertTrue(ss.timer.isRunning());
+    }
+
+    // state = HEAT: heat() from HEAT is no-op
+    @Test
+    void testBVAHeatFromHeatStateMax() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        ss.heat();
+        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
+        assertTrue(ss.heater.isOn);
+    }
+
+    // state = COOL: heat() from COOL should turn off AC, start heater, set state=HEAT
+    @Test
+    void testBVAHeatFromCoolStateMid() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        ss.heat();
+        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
+        assertFalse(ss.ac.isOn);
+        assertTrue(ss.heater.isOn);
+        assertTrue(ss.timer.isRunning());
+    }
+
+    // state = OFF: off() from OFF is no-op
+    @Test
+    void testBVAOffFromOffStateMin() {
+        ss.off();
+        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
+        assertFalse(ss.timer.isRunning());
+    }
+
+    // state = COOL: off() from COOL stops AC and timer, sets state=OFF
+    @Test
+    void testBVAOffFromCoolStateMid() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        ss.timer.start();
+        ss.off();
+        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.timer.isRunning());
+    }
+
+    // state = HEAT: off() from HEAT stops heater and timer, sets state=OFF
+    @Test
+    void testBVAOffFromHeatStateMax() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        ss.timer.start();
+        ss.off();
+        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
+        assertFalse(ss.heater.isOn);
+        assertFalse(ss.timer.isRunning());
+    }
+
+    // room.temp = coolTemp - 1 = 67: 67 > 68 is FALSE => ac.off()
+    @Test
+    void testBVATimerOffCoolTempBelowBoundary() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        ss.room.temp = ss.coolTemp - 1;
+        ss.timerOff();
+        assertFalse(ss.ac.isOn);
+    }
+
+    // room.temp = coolTemp = 68: 68 > 68 is FALSE (strict >) => ac.off()
+    @Test
+    void testBVATimerOffCoolTempAtBoundary() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        ss.room.temp = ss.coolTemp;
+        ss.timerOff();
+        assertFalse(ss.ac.isOn);
+    }
+
+    // room.temp = coolTemp + 1 = 69: 69 > 68 is TRUE => ac.on()
+    @Test
+    void testBVATimerOffCoolTempAboveBoundary() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.room.temp = ss.coolTemp + 1;
+        ss.timerOff();
+        assertTrue(ss.ac.isOn);
+    }
+
+    // room.temp = heatTemp - 1 = 76: 76 < 77 is TRUE => heater.on()
+    @Test
+    void testBVATimerOffHeatTempBelowBoundary() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.room.temp = ss.heatTemp - 1;
+        ss.timerOff();
+        assertTrue(ss.heater.isOn);
+    }
+
+    // room.temp = heatTemp = 77: 77 < 77 is FALSE (strict <) => heater.off()
+    @Test
+    void testBVATimerOffHeatTempAtBoundary() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        ss.room.temp = ss.heatTemp;
+        ss.timerOff();
+        assertFalse(ss.heater.isOn);
+    }
+
+    // room.temp = heatTemp + 1 = 78: 78 < 77 is FALSE => heater.off()
+    @Test
+    void testBVATimerOffHeatTempAboveBoundary() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        ss.room.temp = ss.heatTemp + 1;
+        ss.timerOff();
+        assertFalse(ss.heater.isOn);
+    }
+
+    // state = OFF: timerOff() does nothing
+    @Test
+    void testBVATimerOffStateOff() {
+        SeasonSwitch.state = SeasonSwitch.OFF;
+        ss.timerOff();
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+    }
+
+    // actionPerformed() in COOL state with room.temp > coolTemp => ac.on()
+    @Test
+    void testBVAActionPerformedCoolTempAboveBoundary() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.room.temp = ss.coolTemp + 1;
+        ss.actionPerformed(null);
+        assertTrue(ss.ac.isOn);
+    }
+
+    // actionPerformed() in COOL state with room.temp = coolTemp => ac.off()
+    @Test
+    void testBVAActionPerformedCoolTempAtBoundary() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        ss.room.temp = ss.coolTemp;
+        ss.actionPerformed(null);
+        assertFalse(ss.ac.isOn);
+    }
+
+    // actionPerformed() in COOL state with room.temp = coolTemp - 1 => ac.off()
+    @Test
+    void testBVAActionPerformedCoolTempBelowBoundary() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        ss.room.temp = ss.coolTemp - 1;
+        ss.actionPerformed(null);
+        assertFalse(ss.ac.isOn);
+    }
+
+    // actionPerformed() in HEAT state with room.temp < heatTemp => heater.on()
+    @Test
+    void testBVAActionPerformedHeatTempBelowBoundary() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.room.temp = ss.heatTemp - 1;
+        ss.actionPerformed(null);
+        assertTrue(ss.heater.isOn);
+    }
+
+    // actionPerformed() in HEAT state with room.temp = heatTemp => heater.off()
+    @Test
+    void testBVAActionPerformedHeatTempAtBoundary() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        ss.room.temp = ss.heatTemp;
+        ss.actionPerformed(null);
+        assertFalse(ss.heater.isOn);
+    }
+
+    // actionPerformed() in HEAT state with room.temp = heatTemp + 1 => heater.off()
+    @Test
+    void testBVAActionPerformedHeatTempAboveBoundary() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        ss.room.temp = ss.heatTemp + 1;
+        ss.actionPerformed(null);
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
+    void testMainHeatArg() throws Exception {
+        ExitTrap.Result r = ExitTrap.runMain(1500, "heat");
+        assertFalse(r.exitedByItself);
+        assertTrue(r.output.contains("Heating started"));
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
+    void testRoomActionPerformedStateOff() {
+        SeasonSwitch.state = SeasonSwitch.OFF;
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
+
+    // Adapted: state = null (was state = 99, which no longer compiles with State-typed field)
+    @Test
+    void testCoolDefaultBranch() {
+        SeasonSwitch.state = null;
+        ss.cool();
+        assertNull(SeasonSwitch.state);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+    }
+
+    // Adapted: state = null (was state = 99)
+    @Test
+    void testHeatDefaultBranch() {
+        SeasonSwitch.state = null;
+        ss.heat();
+        assertNull(SeasonSwitch.state);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+    }
+
+    // Adapted: state = null (was state = 99)
+    @Test
+    void testOffDefaultBranch() {
+        SeasonSwitch.state = null;
+        ss.off();
+        assertNull(SeasonSwitch.state);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+    }
+
+    // Adapted: state = null (was state = 99)
+    @Test
+    void testTimerOffDefaultBranch() {
+        SeasonSwitch.state = null;
+        ss.timerOff();
+        assertNull(SeasonSwitch.state);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+    }
+
+    // Adapted: state = null (was state = 99)
+    @Test
+    void testRoomActionPerformedDefaultBranch() {
+        SeasonSwitch.state = null;
+        int tempBefore = ss.room.temp;
+        ss.room.actionPerformed(null);
+        assertEquals(tempBefore, ss.room.temp);
+    }
+}
```

## 14.  — 
