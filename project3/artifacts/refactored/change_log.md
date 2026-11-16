# Change log — refactored

## 1.  — initial generation

## 2.  — initial generation

## 3.  — 

## 4.  — 

## 5.  — Two categories of problems must be fixed:

1. INVENTED BOUNDARIES (state as numeric range): The `state` field is used only in switch/case statements matching discrete named constants (OFF=0, COOL=1, HEAT=2). There is no numeric comparison like `state > N` or `state < N`, so BVA does not apply to state values. Remove all six tests that use state=-1 or state=3 as 'MIN-1'/'MAX+1' boundaries: testBVACoolStateInvalidBelowMin, testBVAHeatStateInvalidAboveMax, testBVAOffStateInvalidBelowMin, testBVAOffStateInvalidAboveMax, testBVATimerOffStateInvalidBelowMin, testBVATimerOffStateInvalidAboveMax.

2. DUPLICATE TESTS: The four timer-transition tests at the bottom duplicate assertions already made in earlier tests. testBVACoolFromOffTimerStarted duplicates the timer assertion in testBVACoolFromOffStateMin. testBVAHeatFromOffTimerStarted duplicates the timer assertion in testBVAHeatFromOffStateMin. testBVAOffFromCoolTimerStopped duplicates the timer assertion in testBVAOffFromCoolStateMiddle. testBVAOffFromHeatTimerStopped duplicates the timer assertion in testBVAOffFromHeatStateMax. Remove these four duplicate tests.

```diff
--- SeasonSwitchBVTest.java (before)
+++ SeasonSwitchBVTest.java (after)
@@ -25,7 +25,8 @@
 
     // -----------------------------------------------------------------------
     // Boundaries for state constants: OFF=0, COOL=1, HEAT=2
-    // Valid range: 0..2; invalid below: -1; invalid above: 3
+    // These are discrete named constants used in switch/case; BVA applies only
+    // to the named values themselves, not to numeric neighbors.
     // -----------------------------------------------------------------------
 
     // state = OFF (MIN of valid range): cool() from OFF should start AC
@@ -137,50 +138,11 @@
         assertFalse(ss.timer.isRunning());
     }
 
-    // state = -1 (MIN-1, invalid): cool() has no case for -1, does nothing
-    @Test
-    void testBVACoolStateInvalidBelowMin() {
-        // state == -1, one below MIN of valid range; switch has no default, no-op
-        SeasonSwitch.state = -1;
-        ss.cool();
-        assertEquals(-1, SeasonSwitch.state); // unchanged
-        assertFalse(ss.ac.isOn);
-        assertFalse(ss.heater.isOn);
-    }
-
-    // state = 3 (MAX+1, invalid): heat() has no case for 3, does nothing
-    @Test
-    void testBVAHeatStateInvalidAboveMax() {
-        // state == 3, one above MAX of valid range; switch has no default, no-op
-        SeasonSwitch.state = 3;
-        ss.heat();
-        assertEquals(3, SeasonSwitch.state); // unchanged
-        assertFalse(ss.heater.isOn);
-        assertFalse(ss.ac.isOn);
-    }
-
-    // state = -1 (MIN-1, invalid): off() has no case for -1, does nothing
-    @Test
-    void testBVAOffStateInvalidBelowMin() {
-        // state == -1, one below MIN of valid range; switch has no default, no-op
-        SeasonSwitch.state = -1;
-        ss.off();
-        assertEquals(-1, SeasonSwitch.state); // unchanged
-    }
-
-    // state = 3 (MAX+1, invalid): off() has no case for 3, does nothing
-    @Test
-    void testBVAOffStateInvalidAboveMax() {
-        // state == 3, one above MAX of valid range; switch has no default, no-op
-        SeasonSwitch.state = 3;
-        ss.off();
-        assertEquals(3, SeasonSwitch.state); // unchanged
-    }
-
     // -----------------------------------------------------------------------
     // Boundaries for timerOff() / actionPerformed():
     // COOL branch: condition is room.temp > coolTemp (strict >)
-    //   coolTemp = 68; test at 67 (N-1), 68 (N), 69 (N+1)
+    //   coolTemp = 68; test at coolTemp-1 (N-1), coolTemp (N), coolTemp+1 (N+1)
+    //   At exactly N=coolTemp: condition is FALSE (strict >)
     // -----------------------------------------------------------------------
 
     // COOL state, room.temp = coolTemp - 1 = 67: 67 > 68 is FALSE -> ac.off()
@@ -218,7 +180,8 @@
 
     // -----------------------------------------------------------------------
     // HEAT branch: condition is room.temp < heatTemp (strict <)
-    //   heatTemp = 77; test at 76 (N-1), 77 (N), 78 (N+1)
+    //   heatTemp = 77; test at heatTemp-1 (N-1), heatTemp (N), heatTemp+1 (N+1)
+    //   At exactly N=heatTemp: condition is FALSE (strict <)
     // -----------------------------------------------------------------------
 
     // HEAT state, room.temp = heatTemp - 1 = 76: 76 < 77 is TRUE -> heater.on()
@@ -270,36 +233,6 @@
         assertFalse(ss.ac.isOn);
         assertFalse(ss.heater.isOn);
         assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
-    }
-
-    // -----------------------------------------------------------------------
-    // timerOff() with invalid state values (no default in switch)
-    // -----------------------------------------------------------------------
-
-    // state = -1 (MIN-1, invalid): timerOff() has no case for -1, does nothing
-    @Test
-    void testBVATimerOffStateInvalidBelowMin() {
-        // state == -1; switch has no default, no-op
-        SeasonSwitch.state = -1;
-        ss.ac.isOn = false;
-        ss.heater.isOn = false;
-        ss.timerOff();
-        assertFalse(ss.ac.isOn);
-        assertFalse(ss.heater.isOn);
-        assertEquals(-1, SeasonSwitch.state);
-    }
-
-    // state = 3 (MAX+1, invalid): timerOff() has no case for 3, does nothing
-    @Test
-    void testBVATimerOffStateInvalidAboveMax() {
-        // state == 3; switch has no default, no-op
-        SeasonSwitch.state = 3;
-        ss.ac.isOn = false;
-        ss.heater.isOn = false;
-        ss.timerOff();
-        assertFalse(ss.ac.isOn);
-        assertFalse(ss.heater.isOn);
-        assertEquals(3, SeasonSwitch.state);
     }
 
     // -----------------------------------------------------------------------
@@ -327,50 +260,4 @@
         ss.actionPerformed(null);
         assertTrue(ss.heater.isOn);
     }
-
-    // -----------------------------------------------------------------------
-    // Additional boundary: transition timer running/stopped across off()
-    // -----------------------------------------------------------------------
-
-    // Timer is running when cool() starts; verify it is running after cool() from OFF
-    @Test
-    void testBVACoolFromOffTimerStarted() {
-        // Boundary: timer transitions from stopped to running on cool() from OFF
-        SeasonSwitch.state = SeasonSwitch.OFF;
-        assertFalse(ss.timer.isRunning());
-        ss.cool();
-        assertTrue(ss.timer.isRunning());
-    }
-
-    // Timer is running when heat() starts; verify it is running after heat() from OFF
-    @Test
-    void testBVAHeatFromOffTimerStarted() {
-        // Boundary: timer transitions from stopped to running on heat() from OFF
-        SeasonSwitch.state = SeasonSwitch.OFF;
-        assertFalse(ss.timer.isRunning());
-        ss.heat();
-        assertTrue(ss.timer.isRunning());
-    }
-
-    // Timer stops when off() called from COOL
-    @Test
-    void testBVAOffFromCoolTimerStopped() {
-        // Boundary: timer transitions from running to stopped on off() from COOL
-        SeasonSwitch.state = SeasonSwitch.COOL;
-        ss.timer.start();
-        assertTrue(ss.timer.isRunning());
-        ss.off();
-        assertFalse(ss.timer.isRunning());
-    }
-
-    // Timer stops when off() called from HEAT
-    @Test
-    void testBVAOffFromHeatTimerStopped() {
-        // Boundary: timer transitions from running to stopped on off() from HEAT
-        SeasonSwitch.state = SeasonSwitch.HEAT;
-        ss.timer.start();
-        assertTrue(ss.timer.isRunning());
-        ss.off();
-        assertFalse(ss.timer.isRunning());
-    }
 }
```

## 6.  — 

## 7.  — 1. Technique check – missing N-1 and N+1 for the state-based switch/case: The tests treat OFF=0, COOL=1, HEAT=2 as a MIN/MAX range and test only the three named values, but they never test the out-of-range neighbours (state = -1, i.e. OFF-1, and state = 3, i.e. HEAT+1). BVA on a range MIN..MAX requires MIN-1 and MAX+1 as well. Either add tests for state=-1 and state=3 (both should be no-ops for every method because no switch case matches), or explicitly justify why those boundaries are excluded. Without them the technique check fails.
2. Technique check – actionPerformed boundary coverage is incomplete: actionPerformed is tested only at coolTemp+1 (TRUE branch) and heatTemp-1 (TRUE branch). The boundary values at coolTemp (FALSE), coolTemp-1 (FALSE), heatTemp (FALSE), and heatTemp+1 (FALSE) are not covered through actionPerformed itself. Because actionPerformed is a distinct public method it needs its own full N-1/N/N+1 coverage, not just two spot-checks.
3. Technique check – no invented boundaries comment is violated for state: The comment says 'BVA applies only to the named values themselves, not to numeric neighbors,' but that contradicts the BVA rule that every range MIN..MAX must be tested at MIN-1 and MAX+1. The comment is used to justify omitting required boundary points; this is incorrect.
4. General check – timer not stopped in testBVACoolFromOffStateMin, testBVACoolFromHeatStateMax, testBVAHeatFromOffStateMin, testBVAHeatFromCoolStateMiddle: These tests call ss.cool() or ss.heat() which call ss.timer.start(), but the @AfterEach only calls ss.timer.stop() on the shared ss instance. Because SeasonSwitch.state is static and shared, if a previous test leaves the timer running and state=COOL or HEAT, the Room.actionPerformed callback can fire during a subsequent test and mutate room.temp or device state unexpectedly. The tearDown must also reset ss.ac.isOn and ss.heater.isOn to false to guarantee a clean slate, since those fields are instance-level and setUp creates a new instance but state is static and could cause the Room timer (not started in these tests but potentially left running) to interfere.
5. General check – ss.room.timer is never started in any test, so Room.actionPerformed cannot fire, which is fine; however tearDown calls ss.room.timer.stop() unconditionally. This is harmless but should be noted as correct defensive practice – no change needed here.
6. Correctness check – testBVACoolFromCoolStateMiddle asserts assertTrue(ss.timer.isRunning()) is NOT present, which is correct (cool() from COOL is a no-op and timer is not started), but the test does not assert assertFalse(ss.timer.isRunning()) either. This is an omission: the no-op case should assert the timer was NOT started to distinguish it from the active cases.
7. Correctness check – testBVAHeatFromHeatStateMax similarly omits assertFalse(ss.timer.isRunning()), leaving the no-op incompletely verified.
8. Correctness check – testBVAOffFromOffStateMin does not assert assertFalse(ss.timer.isRunning()), which should be verified for the no-op case.
9. Summary of required changes: (a) Add tests for state=-1 and state=3 for cool(), heat(), off(), and timerOff() (all should be no-ops). (b) Add the remaining N/N-1/N+1 boundary tests for actionPerformed() (at coolTemp, coolTemp-1, heatTemp, heatTemp+1). (c) Add assertFalse(ss.timer.isRunning()) to the three no-op state tests (COOL→cool, HEAT→heat, OFF→off). (d) Remove or correct the comment that claims BVA does not apply to numeric neighbours of state constants.

```diff
--- SeasonSwitchBVTest.java (before)
+++ SeasonSwitchBVTest.java (after)
@@ -25,11 +25,24 @@
 
     // -----------------------------------------------------------------------
     // Boundaries for state constants: OFF=0, COOL=1, HEAT=2
-    // These are discrete named constants used in switch/case; BVA applies only
-    // to the named values themselves, not to numeric neighbors.
-    // -----------------------------------------------------------------------
-
-    // state = OFF (MIN of valid range): cool() from OFF should start AC
+    // Valid range MIN=0 (OFF) .. MAX=2 (HEAT).
+    // BVA requires testing MIN-1 = -1 and MAX+1 = 3 as out-of-range values.
+    // All switch/case blocks have no default, so unmatched values are no-ops.
+    // -----------------------------------------------------------------------
+
+    // cool(): state = OFF-1 = -1 (below MIN, invalid) -> no case matches, no-op
+    @Test
+    void testBVACoolStateMinMinus1() {
+        // state = -1, below valid range; no switch case matches -> no-op
+        SeasonSwitch.state = SeasonSwitch.OFF - 1; // -1
+        ss.cool();
+        assertEquals(SeasonSwitch.OFF - 1, SeasonSwitch.state);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+        assertFalse(ss.timer.isRunning());
+    }
+
+    // cool(): state = OFF = 0 (MIN of valid range) -> starts AC
     @Test
     void testBVACoolFromOffStateMin() {
         // state == OFF (0), boundary MIN of valid state range
@@ -41,7 +54,7 @@
         assertTrue(ss.timer.isRunning());
     }
 
-    // state = COOL (middle of valid range): cool() from COOL is a no-op
+    // cool(): state = COOL = 1 (middle of valid range) -> no-op
     @Test
     void testBVACoolFromCoolStateMiddle() {
         // state == COOL (1), middle of valid state range; cool() does nothing
@@ -50,9 +63,10 @@
         ss.cool();
         assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
         assertTrue(ss.ac.isOn); // unchanged
-    }
-
-    // state = HEAT (MAX of valid range): cool() from HEAT should switch to AC
+        assertFalse(ss.timer.isRunning()); // timer was not started by this no-op
+    }
+
+    // cool(): state = HEAT = 2 (MAX of valid range) -> switches to AC
     @Test
     void testBVACoolFromHeatStateMax() {
         // state == HEAT (2), boundary MAX of valid state range
@@ -65,7 +79,35 @@
         assertTrue(ss.timer.isRunning());
     }
 
-    // state = OFF (MIN): heat() from OFF should start heater
+    // cool(): state = HEAT+1 = 3 (above MAX, invalid) -> no case matches, no-op
+    @Test
+    void testBVACoolStateMaxPlus1() {
+        // state = 3, above valid range; no switch case matches -> no-op
+        SeasonSwitch.state = SeasonSwitch.HEAT + 1; // 3
+        ss.cool();
+        assertEquals(SeasonSwitch.HEAT + 1, SeasonSwitch.state);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+        assertFalse(ss.timer.isRunning());
+    }
+
+    // -----------------------------------------------------------------------
+    // heat(): state boundaries OFF-1, OFF, COOL, HEAT, HEAT+1
+    // -----------------------------------------------------------------------
+
+    // heat(): state = OFF-1 = -1 (below MIN, invalid) -> no-op
+    @Test
+    void testBVAHeatStateMinMinus1() {
+        // state = -1, below valid range; no switch case matches -> no-op
+        SeasonSwitch.state = SeasonSwitch.OFF - 1; // -1
+        ss.heat();
+        assertEquals(SeasonSwitch.OFF - 1, SeasonSwitch.state);
+        assertFalse(ss.heater.isOn);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.timer.isRunning());
+    }
+
+    // heat(): state = OFF = 0 (MIN of valid range) -> starts heater
     @Test
     void testBVAHeatFromOffStateMin() {
         // state == OFF (0), boundary MIN of valid state range
@@ -77,7 +119,20 @@
         assertTrue(ss.timer.isRunning());
     }
 
-    // state = HEAT (MAX): heat() from HEAT is a no-op
+    // heat(): state = COOL = 1 (middle of valid range) -> switches to heater
+    @Test
+    void testBVAHeatFromCoolStateMiddle() {
+        // state == COOL (1), middle of valid state range
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        ss.heat();
+        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
+        assertTrue(ss.heater.isOn);
+        assertFalse(ss.ac.isOn);
+        assertTrue(ss.timer.isRunning());
+    }
+
+    // heat(): state = HEAT = 2 (MAX of valid range) -> no-op
     @Test
     void testBVAHeatFromHeatStateMax() {
         // state == HEAT (2), boundary MAX of valid state range; heat() does nothing
@@ -86,22 +141,37 @@
         ss.heat();
         assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
         assertTrue(ss.heater.isOn); // unchanged
-    }
-
-    // state = COOL (middle): heat() from COOL should switch to heater
-    @Test
-    void testBVAHeatFromCoolStateMiddle() {
-        // state == COOL (1), middle of valid state range
-        SeasonSwitch.state = SeasonSwitch.COOL;
-        ss.ac.isOn = true;
+        assertFalse(ss.timer.isRunning()); // timer was not started by this no-op
+    }
+
+    // heat(): state = HEAT+1 = 3 (above MAX, invalid) -> no-op
+    @Test
+    void testBVAHeatStateMaxPlus1() {
+        // state = 3, above valid range; no switch case matches -> no-op
+        SeasonSwitch.state = SeasonSwitch.HEAT + 1; // 3
         ss.heat();
-        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
-        assertTrue(ss.heater.isOn);
-        assertFalse(ss.ac.isOn);
-        assertTrue(ss.timer.isRunning());
-    }
-
-    // state = OFF (MIN): off() from OFF is a no-op
+        assertEquals(SeasonSwitch.HEAT + 1, SeasonSwitch.state);
+        assertFalse(ss.heater.isOn);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.timer.isRunning());
+    }
+
+    // -----------------------------------------------------------------------
+    // off(): state boundaries OFF-1, OFF, COOL, HEAT, HEAT+1
+    // -----------------------------------------------------------------------
+
+    // off(): state = OFF-1 = -1 (below MIN, invalid) -> no-op
+    @Test
+    void testBVAOffStateMinMinus1() {
+        // state = -1, below valid range; no switch case matches -> no-op
+        SeasonSwitch.state = SeasonSwitch.OFF - 1; // -1
+        ss.off();
+        assertEquals(SeasonSwitch.OFF - 1, SeasonSwitch.state);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+    }
+
+    // off(): state = OFF = 0 (MIN of valid range) -> no-op
     @Test
     void testBVAOffFromOffStateMin() {
         // state == OFF (0), boundary MIN; off() does nothing
@@ -110,154 +180,238 @@
         assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
         assertFalse(ss.ac.isOn);
         assertFalse(ss.heater.isOn);
-    }
-
-    // state = HEAT (MAX): off() from HEAT should stop heater
-    @Test
-    void testBVAOffFromHeatStateMax() {
-        // state == HEAT (2), boundary MAX of valid state range
-        SeasonSwitch.state = SeasonSwitch.HEAT;
-        ss.heater.isOn = true;
+        assertFalse(ss.timer.isRunning());
+    }
+
+    // off(): state = COOL = 1 (middle of valid range) -> stops AC
+    @Test
+    void testBVAOffFromCoolStateMiddle() {
+        // state == COOL (1), middle of valid state range
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
         ss.timer.start();
         ss.off();
         assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
-        assertFalse(ss.heater.isOn);
-        assertFalse(ss.timer.isRunning());
-    }
-
-    // state = COOL (middle): off() from COOL should stop AC
-    @Test
-    void testBVAOffFromCoolStateMiddle() {
-        // state == COOL (1), middle of valid state range
-        SeasonSwitch.state = SeasonSwitch.COOL;
-        ss.ac.isOn = true;
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.timer.isRunning());
+    }
+
+    // off(): state = HEAT = 2 (MAX of valid range) -> stops heater
+    @Test
+    void testBVAOffFromHeatStateMax() {
+        // state == HEAT (2), boundary MAX of valid state range
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
         ss.timer.start();
         ss.off();
         assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
-        assertFalse(ss.ac.isOn);
-        assertFalse(ss.timer.isRunning());
-    }
-
-    // -----------------------------------------------------------------------
-    // Boundaries for timerOff() / actionPerformed():
-    // COOL branch: condition is room.temp > coolTemp (strict >)
-    //   coolTemp = 68; test at coolTemp-1 (N-1), coolTemp (N), coolTemp+1 (N+1)
-    //   At exactly N=coolTemp: condition is FALSE (strict >)
-    // -----------------------------------------------------------------------
-
-    // COOL state, room.temp = coolTemp - 1 = 67: 67 > 68 is FALSE -> ac.off()
-    @Test
-    void testBVATimerOffCoolTempOneBelowCoolTemp() {
-        // room.temp == coolTemp - 1; condition room.temp > coolTemp is FALSE
-        SeasonSwitch.state = SeasonSwitch.COOL;
-        ss.ac.isOn = true;
-        ss.room.temp = ss.coolTemp - 1; // 67
-        ss.timerOff();
-        assertFalse(ss.ac.isOn); // ac turned off because 67 > 68 is false
-    }
-
-    // COOL state, room.temp = coolTemp = 68: 68 > 68 is FALSE -> ac.off()
-    @Test
-    void testBVATimerOffCoolTempEqualCoolTemp() {
-        // room.temp == coolTemp exactly; condition room.temp > coolTemp is FALSE (strict >)
-        SeasonSwitch.state = SeasonSwitch.COOL;
-        ss.ac.isOn = true;
-        ss.room.temp = ss.coolTemp; // 68
-        ss.timerOff();
-        assertFalse(ss.ac.isOn); // ac turned off because 68 > 68 is false
-    }
-
-    // COOL state, room.temp = coolTemp + 1 = 69: 69 > 68 is TRUE -> ac.on()
-    @Test
-    void testBVATimerOffCoolTempOneAboveCoolTemp() {
-        // room.temp == coolTemp + 1; condition room.temp > coolTemp is TRUE
-        SeasonSwitch.state = SeasonSwitch.COOL;
-        ss.ac.isOn = false;
-        ss.room.temp = ss.coolTemp + 1; // 69
-        ss.timerOff();
-        assertTrue(ss.ac.isOn); // ac turned on because 69 > 68 is true
-    }
-
-    // -----------------------------------------------------------------------
-    // HEAT branch: condition is room.temp < heatTemp (strict <)
-    //   heatTemp = 77; test at heatTemp-1 (N-1), heatTemp (N), heatTemp+1 (N+1)
-    //   At exactly N=heatTemp: condition is FALSE (strict <)
-    // -----------------------------------------------------------------------
-
-    // HEAT state, room.temp = heatTemp - 1 = 76: 76 < 77 is TRUE -> heater.on()
-    @Test
-    void testBVATimerOffHeatTempOneBelowHeatTemp() {
-        // room.temp == heatTemp - 1; condition room.temp < heatTemp is TRUE
-        SeasonSwitch.state = SeasonSwitch.HEAT;
-        ss.heater.isOn = false;
-        ss.room.temp = ss.heatTemp - 1; // 76
-        ss.timerOff();
-        assertTrue(ss.heater.isOn); // heater turned on because 76 < 77 is true
-    }
-
-    // HEAT state, room.temp = heatTemp = 77: 77 < 77 is FALSE -> heater.off()
-    @Test
-    void testBVATimerOffHeatTempEqualHeatTemp() {
-        // room.temp == heatTemp exactly; condition room.temp < heatTemp is FALSE (strict <)
-        SeasonSwitch.state = SeasonSwitch.HEAT;
-        ss.heater.isOn = true;
-        ss.room.temp = ss.heatTemp; // 77
-        ss.timerOff();
-        assertFalse(ss.heater.isOn); // heater turned off because 77 < 77 is false
-    }
-
-    // HEAT state, room.temp = heatTemp + 1 = 78: 78 < 77 is FALSE -> heater.off()
-    @Test
-    void testBVATimerOffHeatTempOneAboveHeatTemp() {
-        // room.temp == heatTemp + 1; condition room.temp < heatTemp is FALSE
-        SeasonSwitch.state = SeasonSwitch.HEAT;
-        ss.heater.isOn = true;
-        ss.room.temp = ss.heatTemp + 1; // 78
-        ss.timerOff();
-        assertFalse(ss.heater.isOn); // heater turned off because 78 < 77 is false
-    }
-
-    // -----------------------------------------------------------------------
-    // timerOff() with state = OFF: no-op
-    // -----------------------------------------------------------------------
-
-    // OFF state: timerOff() does nothing (case OFF: break)
-    @Test
-    void testBVATimerOffStateOff() {
-        // state == OFF; timerOff() hits case OFF: break, no device changes
-        SeasonSwitch.state = SeasonSwitch.OFF;
+        assertFalse(ss.heater.isOn);
+        assertFalse(ss.timer.isRunning());
+    }
+
+    // off(): state = HEAT+1 = 3 (above MAX, invalid) -> no-op
+    @Test
+    void testBVAOffStateMaxPlus1() {
+        // state = 3, above valid range; no switch case matches -> no-op
+        SeasonSwitch.state = SeasonSwitch.HEAT + 1; // 3
+        ss.off();
+        assertEquals(SeasonSwitch.HEAT + 1, SeasonSwitch.state);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+    }
+
+    // -----------------------------------------------------------------------
+    // timerOff() state boundary tests: OFF-1, OFF, COOL, HEAT, HEAT+1
+    // -----------------------------------------------------------------------
+
+    // timerOff(): state = OFF-1 = -1 (below MIN, invalid) -> no-op
+    @Test
+    void testBVATimerOffStateMinMinus1() {
+        // state = -1, below valid range; no switch case matches -> no-op
+        SeasonSwitch.state = SeasonSwitch.OFF - 1; // -1
         ss.ac.isOn = false;
         ss.heater.isOn = false;
         ss.room.temp = ss.coolTemp + 1; // would trigger ac if COOL
         ss.timerOff();
         assertFalse(ss.ac.isOn);
         assertFalse(ss.heater.isOn);
+        assertEquals(SeasonSwitch.OFF - 1, SeasonSwitch.state);
+    }
+
+    // timerOff(): state = OFF = 0 (MIN of valid range) -> no-op
+    @Test
+    void testBVATimerOffStateOff() {
+        // state == OFF; timerOff() hits case OFF: break, no device changes
+        SeasonSwitch.state = SeasonSwitch.OFF;
+        ss.ac.isOn = false;
+        ss.heater.isOn = false;
+        ss.room.temp = ss.coolTemp + 1; // would trigger ac if COOL
+        ss.timerOff();
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
         assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
     }
 
-    // -----------------------------------------------------------------------
-    // actionPerformed() delegates to timerOff(); verify via observable effect
-    // -----------------------------------------------------------------------
-
-    // actionPerformed() in COOL state with temp > coolTemp: ac.on()
-    @Test
-    void testBVAActionPerformedCoolTempAboveCoolTemp() {
-        // actionPerformed delegates to timerOff(); COOL, temp = coolTemp+1 -> ac.on()
-        SeasonSwitch.state = SeasonSwitch.COOL;
+    // timerOff(): state = HEAT+1 = 3 (above MAX, invalid) -> no-op
+    @Test
+    void testBVATimerOffStateMaxPlus1() {
+        // state = 3, above valid range; no switch case matches -> no-op
+        SeasonSwitch.state = SeasonSwitch.HEAT + 1; // 3
         ss.ac.isOn = false;
-        ss.room.temp = ss.coolTemp + 1; // 69 > 68 TRUE
+        ss.heater.isOn = false;
+        ss.room.temp = ss.heatTemp - 1; // would trigger heater if HEAT
+        ss.timerOff();
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+        assertEquals(SeasonSwitch.HEAT + 1, SeasonSwitch.state);
+    }
+
+    // -----------------------------------------------------------------------
+    // timerOff() COOL branch: condition is room.temp > coolTemp (strict >)
+    //   coolTemp = 68; test at coolTemp-1 (N-1), coolTemp (N), coolTemp+1 (N+1)
+    //   At exactly N=coolTemp: condition is FALSE (strict >)
+    // -----------------------------------------------------------------------
+
+    // COOL state, room.temp = coolTemp - 1 = 67: 67 > 68 is FALSE -> ac.off()
+    @Test
+    void testBVATimerOffCoolTempOneBelowCoolTemp() {
+        // room.temp == coolTemp - 1; condition room.temp > coolTemp is FALSE
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        ss.room.temp = ss.coolTemp - 1; // 67
+        ss.timerOff();
+        assertFalse(ss.ac.isOn); // ac turned off because 67 > 68 is false
+    }
+
+    // COOL state, room.temp = coolTemp = 68: 68 > 68 is FALSE -> ac.off()
+    @Test
+    void testBVATimerOffCoolTempEqualCoolTemp() {
+        // room.temp == coolTemp exactly; condition room.temp > coolTemp is FALSE (strict >)
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        ss.room.temp = ss.coolTemp; // 68
+        ss.timerOff();
+        assertFalse(ss.ac.isOn); // ac turned off because 68 > 68 is false
+    }
+
+    // COOL state, room.temp = coolTemp + 1 = 69: 69 > 68 is TRUE -> ac.on()
+    @Test
+    void testBVATimerOffCoolTempOneAboveCoolTemp() {
+        // room.temp == coolTemp + 1; condition room.temp > coolTemp is TRUE
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = false;
+        ss.room.temp = ss.coolTemp + 1; // 69
+        ss.timerOff();
+        assertTrue(ss.ac.isOn); // ac turned on because 69 > 68 is true
+    }
+
+    // -----------------------------------------------------------------------
+    // timerOff() HEAT branch: condition is room.temp < heatTemp (strict <)
+    //   heatTemp = 77; test at heatTemp-1 (N-1), heatTemp (N), heatTemp+1 (N+1)
+    //   At exactly N=heatTemp: condition is FALSE (strict <)
+    // -----------------------------------------------------------------------
+
+    // HEAT state, room.temp = heatTemp - 1 = 76: 76 < 77 is TRUE -> heater.on()
+    @Test
+    void testBVATimerOffHeatTempOneBelowHeatTemp() {
+        // room.temp == heatTemp - 1; condition room.temp < heatTemp is TRUE
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = false;
+        ss.room.temp = ss.heatTemp - 1; // 76
+        ss.timerOff();
+        assertTrue(ss.heater.isOn); // heater turned on because 76 < 77 is true
+    }
+
+    // HEAT state, room.temp = heatTemp = 77: 77 < 77 is FALSE -> heater.off()
+    @Test
+    void testBVATimerOffHeatTempEqualHeatTemp() {
+        // room.temp == heatTemp exactly; condition room.temp < heatTemp is FALSE (strict <)
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        ss.room.temp = ss.heatTemp; // 77
+        ss.timerOff();
+        assertFalse(ss.heater.isOn); // heater turned off because 77 < 77 is false
+    }
+
+    // HEAT state, room.temp = heatTemp + 1 = 78: 78 < 77 is FALSE -> heater.off()
+    @Test
+    void testBVATimerOffHeatTempOneAboveHeatTemp() {
+        // room.temp == heatTemp + 1; condition room.temp < heatTemp is FALSE
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        ss.room.temp = ss.heatTemp + 1; // 78
+        ss.timerOff();
+        assertFalse(ss.heater.isOn); // heater turned off because 78 < 77 is false
+    }
+
+    // -----------------------------------------------------------------------
+    // actionPerformed() delegates to timerOff(); it is a distinct public method
+    // and requires its own full N-1/N/N+1 boundary coverage for both comparisons.
+    // -----------------------------------------------------------------------
+
+    // actionPerformed(): COOL state, room.temp = coolTemp - 1 = 67: FALSE -> ac.off()
+    @Test
+    void testBVAActionPerformedCoolTempOneBelowCoolTemp() {
+        // actionPerformed -> timerOff(); COOL, temp = coolTemp-1 = 67 > 68 FALSE -> ac.off()
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        ss.room.temp = ss.coolTemp - 1; // 67
+        ss.actionPerformed(null);
+        assertFalse(ss.ac.isOn);
+    }
+
+    // actionPerformed(): COOL state, room.temp = coolTemp = 68: FALSE -> ac.off()
+    @Test
+    void testBVAActionPerformedCoolTempEqualCoolTemp() {
+        // actionPerformed -> timerOff(); COOL, temp = coolTemp = 68 > 68 FALSE -> ac.off()
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        ss.room.temp = ss.coolTemp; // 68
+        ss.actionPerformed(null);
+        assertFalse(ss.ac.isOn);
+    }
+
+    // actionPerformed(): COOL state, room.temp = coolTemp + 1 = 69: TRUE -> ac.on()
+    @Test
+    void testBVAActionPerformedCoolTempOneAboveCoolTemp() {
+        // actionPerformed -> timerOff(); COOL, temp = coolTemp+1 = 69 > 68 TRUE -> ac.on()
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = false;
+        ss.room.temp = ss.coolTemp + 1; // 69
         ss.actionPerformed(null);
         assertTrue(ss.ac.isOn);
     }
 
-    // actionPerformed() in HEAT state with temp < heatTemp: heater.on()
-    @Test
-    void testBVAActionPerformedHeatTempBelowHeatTemp() {
-        // actionPerformed delegates to timerOff(); HEAT, temp = heatTemp-1 -> heater.on()
+    // actionPerformed(): HEAT state, room.temp = heatTemp - 1 = 76: TRUE -> heater.on()
+    @Test
+    void testBVAActionPerformedHeatTempOneBelowHeatTemp() {
+        // actionPerformed -> timerOff(); HEAT, temp = heatTemp-1 = 76 < 77 TRUE -> heater.on()
         SeasonSwitch.state = SeasonSwitch.HEAT;
         ss.heater.isOn = false;
-        ss.room.temp = ss.heatTemp - 1; // 76 < 77 TRUE
+        ss.room.temp = ss.heatTemp - 1; // 76
         ss.actionPerformed(null);
         assertTrue(ss.heater.isOn);
     }
+
+    // actionPerformed(): HEAT state, room.temp = heatTemp = 77: FALSE -> heater.off()
+    @Test
+    void testBVAActionPerformedHeatTempEqualHeatTemp() {
+        // actionPerformed -> timerOff(); HEAT, temp = heatTemp = 77 < 77 FALSE -> heater.off()
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        ss.room.temp = ss.heatTemp; // 77
+        ss.actionPerformed(null);
+        assertFalse(ss.heater.isOn);
+    }
+
+    // actionPerformed(): HEAT state, room.temp = heatTemp + 1 = 78: FALSE -> heater.off()
+    @Test
+    void testBVAActionPerformedHeatTempOneAboveHeatTemp() {
+        // actionPerformed -> timerOff(); HEAT, temp = heatTemp+1 = 78 < 77 FALSE -> heater.off()
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        ss.room.temp = ss.heatTemp + 1; // 78
+        ss.actionPerformed(null);
+        assertFalse(ss.heater.isOn);
+    }
 }
```

## 8.  — 

## 9.  — 

## 10.  — 

## 11. test — Target 10 measured missing branch line(s)

```diff
--- approved JUnit suite (before)
+++ approved JUnit suite (after)
@@ -535,4 +535,85 @@
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
+        ss.room.temp = 70;
+        ss.room.actionPerformed(null);
+        assertEquals(69, ss.room.temp);
+    }
+
+    @Test
+    void testRoomActionPerformedCoolAcOff() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = false;
+        ss.room.temp = 70;
+        ss.room.actionPerformed(null);
+        assertEquals(71, ss.room.temp);
+    }
+
+    @Test
+    void testRoomActionPerformedHeatHeaterOn() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        ss.room.temp = 70;
+        ss.room.actionPerformed(null);
+        assertEquals(71, ss.room.temp);
+    }
+
+    @Test
+    void testRoomActionPerformedHeatHeaterOff() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = false;
+        ss.room.temp = 70;
+        ss.room.actionPerformed(null);
+        assertEquals(69, ss.room.temp);
+    }
 }
```

## 12.  — 

## 13. test — Target 1 measured missing branch line(s)

```diff
--- approved JUnit suite (before)
+++ approved JUnit suite (after)
@@ -616,4 +616,12 @@
         ss.room.actionPerformed(null);
         assertEquals(69, ss.room.temp);
     }
+
+    @Test
+    void testRoomActionPerformedUnmatchedState() {
+        SeasonSwitch.state = -1;
+        int tempBefore = ss.room.temp;
+        ss.room.actionPerformed(null);
+        assertEquals(tempBefore, ss.room.temp);
+    }
 }
```

## 14.  — 

## 15.  — 

## 16.  — Your previous reply was rejected: Refactor model returned invalid JSON: Expecting property name enclosed in double quotes: line 2 column 13 (char 14)
Return ONE complete, valid JSON object that follows every requirement.

```diff
--- before
+++ after
@@ -0,0 +1,561 @@
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
+    // Partition: timerOff() when state == COOL and room.temp > coolTemp (70 > 68) -> AC turns on
+    @Test
+    void testEPTimerOffCoolRoomTempAboveCoolTemp() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.room.temp = 72;
+        ss.timerOff();
+        assertTrue(ss.ac.isOn);
+        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
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
+        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
+    }
+
+    // Partition: timerOff() when state == HEAT and room.temp < heatTemp (74 < 77) -> heater turns on
+    @Test
+    void testEPTimerOffHeatRoomTempBelowHeatTemp() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.room.temp = 74;
+        ss.timerOff();
+        assertTrue(ss.heater.isOn);
+        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
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
+        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
+    }
+
+    // Partition: actionPerformed() delegates to timerOff() when state == COOL and temp > coolTemp
+    @Test
+    void testEPActionPerformedCoolTempAboveThreshold() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.room.temp = 73;
+        ss.actionPerformed(null);
+        assertTrue(ss.ac.isOn);
+    }
+
+    // Partition: actionPerformed() delegates to timerOff() when state == HEAT and temp < heatTemp
+    @Test
+    void testEPActionPerformedHeatTempBelowThreshold() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.room.temp = 75;
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
+    // cool(): state = null (invalid) -> no-op
+    @Test
+    void testBVACoolStateMinMinus1() {
+        SeasonSwitch.state = null;
+        ss.cool();
+        assertNull(SeasonSwitch.state);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+        assertFalse(ss.timer.isRunning());
+    }
+
+    // cool(): state = COOL (middle of valid range) -> no-op
+    @Test
+    void testBVACoolFromCoolStateMiddle() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        ss.cool();
+        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
+        assertTrue(ss.ac.isOn);
+        assertFalse(ss.timer.isRunning());
+    }
+
+    // cool(): state = HEAT (MAX of valid range) -> switches to AC
+    @Test
+    void testBVACoolFromHeatStateMax() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        ss.cool();
+        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
+        assertTrue(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+        assertTrue(ss.timer.isRunning());
+    }
+
+    // cool(): state = null (above MAX, invalid) -> no-op
+    @Test
+    void testBVACoolStateMaxPlus1() {
+        SeasonSwitch.state = null;
+        ss.cool();
+        assertNull(SeasonSwitch.state);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+        assertFalse(ss.timer.isRunning());
+    }
+
+    // heat(): state = null (below MIN, invalid) -> no-op
+    @Test
+    void testBVAHeatStateMinMinus1() {
+        SeasonSwitch.state = null;
+        ss.heat();
+        assertNull(SeasonSwitch.state);
+        assertFalse(ss.heater.isOn);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.timer.isRunning());
+    }
+
+    // heat(): state = COOL (middle of valid range) -> switches to heater
+    @Test
+    void testBVAHeatFromCoolStateMiddle() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        ss.heat();
+        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
+        assertTrue(ss.heater.isOn);
+        assertFalse(ss.ac.isOn);
+        assertTrue(ss.timer.isRunning());
+    }
+
+    // heat(): state = HEAT (MAX of valid range) -> no-op
+    @Test
+    void testBVAHeatFromHeatStateMax() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        ss.heat();
+        assertEquals(SeasonSwitch.HEAT, SeasonSwitch.state);
+        assertTrue(ss.heater.isOn);
+        assertFalse(ss.timer.isRunning());
+    }
+
+    // heat(): state = null (above MAX, invalid) -> no-op
+    @Test
+    void testBVAHeatStateMaxPlus1() {
+        SeasonSwitch.state = null;
+        ss.heat();
+        assertNull(SeasonSwitch.state);
+        assertFalse(ss.heater.isOn);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.timer.isRunning());
+    }
+
+    // off(): state = null (below MIN, invalid) -> no-op
+    @Test
+    void testBVAOffStateMinMinus1() {
+        SeasonSwitch.state = null;
+        ss.off();
+        assertNull(SeasonSwitch.state);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+    }
+
+    // off(): state = null (above MAX, invalid) -> no-op
+    @Test
+    void testBVAOffStateMaxPlus1() {
+        SeasonSwitch.state = null;
+        ss.off();
+        assertNull(SeasonSwitch.state);
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+    }
+
+    // timerOff(): state = null (below MIN, invalid) -> no-op
+    @Test
+    void testBVATimerOffStateMinMinus1() {
+        SeasonSwitch.state = null;
+        ss.ac.isOn = false;
+        ss.heater.isOn = false;
+        ss.room.temp = ss.coolTemp + 1;
+        ss.timerOff();
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+        assertNull(SeasonSwitch.state);
+    }
+
+    // timerOff(): state == OFF (MIN of valid range) -> no-op
+    @Test
+    void testBVATimerOffStateOff() {
+        SeasonSwitch.state = SeasonSwitch.OFF;
+        ss.ac.isOn = false;
+        ss.heater.isOn = false;
+        ss.room.temp = ss.coolTemp + 1;
+        ss.timerOff();
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+        assertEquals(SeasonSwitch.OFF, SeasonSwitch.state);
+    }
+
+    // timerOff(): state = null (above MAX, invalid) -> no-op
+    @Test
+    void testBVATimerOffStateMaxPlus1() {
+        SeasonSwitch.state = null;
+        ss.ac.isOn = false;
+        ss.heater.isOn = false;
+        ss.room.temp = ss.heatTemp - 1;
+        ss.timerOff();
+        assertFalse(ss.ac.isOn);
+        assertFalse(ss.heater.isOn);
+        assertNull(SeasonSwitch.state);
+    }
+
+    // COOL state, room.temp = coolTemp - 1 = 67: 67 > 68 is FALSE -> ac.off()
+    @Test
+    void testBVATimerOffCoolTempOneBelowCoolTemp() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        ss.room.temp = ss.coolTemp - 1;
+        ss.timerOff();
+        assertFalse(ss.ac.isOn);
+    }
+
+    // COOL state, room.temp = coolTemp = 68: 68 > 68 is FALSE -> ac.off()
+    @Test
+    void testBVATimerOffCoolTempEqualCoolTemp() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        ss.room.temp = ss.coolTemp;
+        ss.timerOff();
+        assertFalse(ss.ac.isOn);
+    }
+
+    // COOL state, room.temp = coolTemp + 1 = 69: 69 > 68 is TRUE -> ac.on()
+    @Test
+    void testBVATimerOffCoolTempOneAboveCoolTemp() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = false;
+        ss.room.temp = ss.coolTemp + 1;
+        ss.timerOff();
+        assertTrue(ss.ac.isOn);
+    }
+
+    // HEAT state, room.temp = heatTemp - 1 = 76: 76 < 77 is TRUE -> heater.on()
+    @Test
+    void testBVATimerOffHeatTempOneBelowHeatTemp() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = false;
+        ss.room.temp = ss.heatTemp - 1;
+        ss.timerOff();
+        assertTrue(ss.heater.isOn);
+    }
+
+    // HEAT state, room.temp = heatTemp = 77: 77 < 77 is FALSE -> heater.off()
+    @Test
+    void testBVATimerOffHeatTempEqualHeatTemp() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        ss.room.temp = ss.heatTemp;
+        ss.timerOff();
+        assertFalse(ss.heater.isOn);
+    }
+
+    // HEAT state, room.temp = heatTemp + 1 = 78: 78 < 77 is FALSE -> heater.off()
+    @Test
+    void testBVATimerOffHeatTempOneAboveHeatTemp() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        ss.room.temp = ss.heatTemp + 1;
+        ss.timerOff();
+        assertFalse(ss.heater.isOn);
+    }
+
+    // actionPerformed(): COOL state, room.temp = coolTemp - 1 = 67: FALSE -> ac.off()
+    @Test
+    void testBVAActionPerformedCoolTempOneBelowCoolTemp() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        ss.room.temp = ss.coolTemp - 1;
+        ss.actionPerformed(null);
+        assertFalse(ss.ac.isOn);
+    }
+
+    // actionPerformed(): COOL state, room.temp = coolTemp = 68: FALSE -> ac.off()
+    @Test
+    void testBVAActionPerformedCoolTempEqualCoolTemp() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        ss.room.temp = ss.coolTemp;
+        ss.actionPerformed(null);
+        assertFalse(ss.ac.isOn);
+    }
+
+    // actionPerformed(): COOL state, room.temp = coolTemp + 1 = 69: TRUE -> ac.on()
+    @Test
+    void testBVAActionPerformedCoolTempOneAboveCoolTemp() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = false;
+        ss.room.temp = ss.coolTemp + 1;
+        ss.actionPerformed(null);
+        assertTrue(ss.ac.isOn);
+    }
+
+    // actionPerformed(): HEAT state, room.temp = heatTemp - 1 = 76: TRUE -> heater.on()
+    @Test
+    void testBVAActionPerformedHeatTempOneBelowHeatTemp() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = false;
+        ss.room.temp = ss.heatTemp - 1;
+        ss.actionPerformed(null);
+        assertTrue(ss.heater.isOn);
+    }
+
+    // actionPerformed(): HEAT state, room.temp = heatTemp = 77: FALSE -> heater.off()
+    @Test
+    void testBVAActionPerformedHeatTempEqualHeatTemp() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        ss.room.temp = ss.heatTemp;
+        ss.actionPerformed(null);
+        assertFalse(ss.heater.isOn);
+    }
+
+    // actionPerformed(): HEAT state, room.temp = heatTemp + 1 = 78: FALSE -> heater.off()
+    @Test
+    void testBVAActionPerformedHeatTempOneAboveHeatTemp() {
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
+        ss.room.temp = 70;
+        ss.room.actionPerformed(null);
+        assertEquals(69, ss.room.temp);
+    }
+
+    @Test
+    void testRoomActionPerformedCoolAcOff() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = false;
+        ss.room.temp = 70;
+        ss.room.actionPerformed(null);
+        assertEquals(71, ss.room.temp);
+    }
+
+    @Test
+    void testRoomActionPerformedHeatHeaterOn() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        ss.room.temp = 70;
+        ss.room.actionPerformed(null);
+        assertEquals(71, ss.room.temp);
+    }
+
+    @Test
+    void testRoomActionPerformedHeatHeaterOff() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = false;
+        ss.room.temp = 70;
+        ss.room.actionPerformed(null);
+        assertEquals(69, ss.room.temp);
+    }
+
+    @Test
+    void testRoomActionPerformedUnmatchedState() {
+        SeasonSwitch.state = null;
+        int tempBefore = ss.room.temp;
+        ss.room.actionPerformed(null);
+        assertEquals(tempBefore, ss.room.temp);
+    }
+}
```

## 17.  — 
