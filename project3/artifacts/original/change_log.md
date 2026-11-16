# Change log — original

## 1.  — initial generation

## 2.  — initial generation

## 3.  — 

## 4.  — 

## 5.  — Two issues must be fixed: (1) The public method actionPerformed(ActionEvent) is never tested. Add a test that calls ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, "")) and verifies the same side effects as timerOff() for at least one state (e.g., state=COOL with room.temp > coolTemp confirms ac.isOn becomes true). (2) The four tests in the 'Additional boundary' section are exact duplicates of earlier BVA tests: testBVATimerOffCoolAcOnTempBelowCoolTemp duplicates testBVATimerOffCoolTempMinusOne (both state=COOL, temp=67, assert ac off); testBVATimerOffCoolAcOffTempAboveCoolTemp duplicates testBVATimerOffCoolTempPlusOne (both state=COOL, temp=69, assert ac on); testBVATimerOffHeatHeaterOffTempBelowHeatTemp duplicates testBVATimerOffHeatTempMinusOne (both state=HEAT, temp=76, assert heater on); testBVATimerOffHeatHeaterOnTempAboveHeatTemp duplicates testBVATimerOffHeatTempPlusOne (both state=HEAT, temp=78, assert heater off). Remove these four duplicate tests.

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
 
@@ -266,52 +268,19 @@
     }
 
     // -----------------------------------------------------------------------
-    // Additional boundary: timerOff() COOL branch with temp well below coolTemp
-    // to confirm AC stays off (not a boundary per se, but covers the else branch
-    // with a clearly false condition)
-    // -----------------------------------------------------------------------
-
-    // room.temp = coolTemp - 1 with AC initially on: AC should be turned off
-    @Test
-    void testBVATimerOffCoolAcOnTempBelowCoolTemp() {
-        // temp=67, coolTemp=68; condition false -> ac.off() even if ac was on
-        SeasonSwitch.state = SeasonSwitch.COOL;
-        ss.ac.isOn = true;
-        ss.room.temp = ss.coolTemp - 1; // 67
-        ss.timerOff();
-        assertFalse(ss.ac.isOn);
-    }
-
-    // room.temp = coolTemp + 1 with AC initially off: AC should be turned on
-    @Test
-    void testBVATimerOffCoolAcOffTempAboveCoolTemp() {
-        // temp=69, coolTemp=68; condition true -> ac.on() even if ac was off
-        SeasonSwitch.state = SeasonSwitch.COOL;
+    // actionPerformed(ActionEvent) delegates to timerOff(); verify same effects.
+    // Boundary: state=COOL, room.temp = coolTemp+1 (69) -> condition TRUE -> ac.on()
+    // -----------------------------------------------------------------------
+
+    // actionPerformed() with state=COOL and temp > coolTemp: AC should turn on
+    @Test
+    void testBVAActionPerformedCoolTempAboveCoolTemp() {
+        // actionPerformed delegates to timerOff();
+        // state=COOL, temp=69 > coolTemp=68 -> ac.on()
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.room.temp = ss.coolTemp + 1; // 69
         ss.ac.isOn = false;
-        ss.room.temp = ss.coolTemp + 1; // 69
-        ss.timerOff();
-        assertTrue(ss.ac.isOn);
-    }
-
-    // room.temp = heatTemp - 1 with heater initially off: heater should be turned on
-    @Test
-    void testBVATimerOffHeatHeaterOffTempBelowHeatTemp() {
-        // temp=76, heatTemp=77; condition true -> heater.on() even if heater was off
-        SeasonSwitch.state = SeasonSwitch.HEAT;
-        ss.heater.isOn = false;
-        ss.room.temp = ss.heatTemp - 1; // 76
-        ss.timerOff();
-        assertTrue(ss.heater.isOn);
-    }
-
-    // room.temp = heatTemp + 1 with heater initially on: heater should be turned off
-    @Test
-    void testBVATimerOffHeatHeaterOnTempAboveHeatTemp() {
-        // temp=78, heatTemp=77; condition false -> heater.off() even if heater was on
-        SeasonSwitch.state = SeasonSwitch.HEAT;
-        ss.heater.isOn = true;
-        ss.room.temp = ss.heatTemp + 1; // 78
-        ss.timerOff();
-        assertFalse(ss.heater.isOn);
+        ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, ""));
+        assertTrue(ss.ac.isOn);
     }
 }
```

## 6.  — 

## 7.  — 

## 8.  — 

## 9. test — Target 7 measured missing branch line(s)

```diff
--- approved JUnit suite (before)
+++ approved JUnit suite (after)
@@ -449,4 +449,66 @@
         ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, ""));
         assertTrue(ss.ac.isOn);
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
+    void testMainArgOff() throws Exception {
+        ExitTrap.Result r = ExitTrap.runMain("off");
+        assertTrue(r.exitedByItself);
+        assertEquals(0, r.exitCode);
+        assertTrue(r.output.contains("System off"));
+    }
+
+    @Test
+    void testMainArgCool() throws Exception {
+        ExitTrap.Result r = ExitTrap.runMain(1500, "cool");
+        assertFalse(r.exitedByItself);
+        assertTrue(r.output.contains("Cooling started"));
+    }
+
+    @Test
+    void testMainArgUnknown() throws Exception {
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
+        ss.ac.isOn = false;
+        ss.room.actionPerformed(null);
+        assertEquals(tempBefore, ss.room.temp);
+    }
+
+    @Test
+    void testRoomActionPerformedHeatHeaterOn() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        int tempBefore = ss.room.temp;
+        ss.room.actionPerformed(null);
+        assertEquals(tempBefore + 1, ss.room.temp);
+        ss.heater.isOn = false;
+        ss.room.actionPerformed(null);
+        assertEquals(tempBefore, ss.room.temp);
+    }
 }
```

## 10.  — 

## 11. test — Target 2 measured missing branch line(s)

```diff
--- approved JUnit suite (before)
+++ approved JUnit suite (after)
@@ -511,4 +511,19 @@
         ss.room.actionPerformed(null);
         assertEquals(tempBefore, ss.room.temp);
     }
+
+    @Test
+    void testMainArgHeat() throws Exception {
+        ExitTrap.Result r = ExitTrap.runMain(1500, "heat");
+        assertFalse(r.exitedByItself);
+        assertTrue(r.output.contains("Heating started"));
+    }
+
+    @Test
+    void testRoomActionPerformedInvalidState() {
+        SeasonSwitch.state = -1;
+        int tempBefore = ss.room.temp;
+        ss.room.actionPerformed(null);
+        assertEquals(tempBefore, ss.room.temp);
+    }
 }
```

## 12.  — 
