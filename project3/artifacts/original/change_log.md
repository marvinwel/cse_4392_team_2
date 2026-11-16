# Change log — original

## 1.  — initial generation

## 2.  — initial generation

## 3.  — 

## 4.  — 

## 5.  — Two issues must be fixed: (1) The public method actionPerformed(ActionEvent) is never tested directly. Add a test that calls ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, "")) with an appropriate state (e.g., COOL with room.temp > coolTemp) and verifies the delegated behavior (ac.isOn true/false), confirming it delegates to timerOff(). (2) testBVAStateOffMinCool and testBVACoolFromOff are exact duplicates (identical setup and assertions for cool() from OFF state). Remove one of them.

```diff
--- SeasonSwitchBVTest.java (before)
+++ SeasonSwitchBVTest.java (after)
@@ -5,6 +5,8 @@
 import org.junit.jupiter.api.Test;
 
 import static org.junit.jupiter.api.Assertions.*;
+
+import java.awt.event.ActionEvent;
 
 public class SeasonSwitchBVTest {
 
@@ -28,17 +30,6 @@
     // Valid range: 0..2; invalid below: -1; invalid above: 3
     // -----------------------------------------------------------------------
 
-    // state = OFF (MIN valid boundary = 0): cool() from OFF should start AC
-    @Test
-    void testBVAStateOffMinCool() {
-        // state == OFF (0), MIN of valid range
-        SeasonSwitch.state = SeasonSwitch.OFF;
-        ss.cool();
-        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
-        assertTrue(ss.ac.isOn);
-        assertTrue(ss.timer.isRunning());
-    }
-
     // state = HEAT (MAX valid boundary = 2): off() from HEAT should stop heater
     @Test
     void testBVAStateHeatMaxOff() {
@@ -283,7 +274,7 @@
 
     // -----------------------------------------------------------------------
     // Additional boundary: timerOff() in COOL state with temp exactly at
-    // coolTemp (boundary already covered above), verify state unchanged
+    // coolTemp, verify state unchanged
     // -----------------------------------------------------------------------
 
     // state = COOL, room.temp = coolTemp: ac turns off, state stays COOL
@@ -307,7 +298,7 @@
     }
 
     // -----------------------------------------------------------------------
-    // Boundary: invalid state -1 passed to off() — no default, does nothing
+    // Boundary: invalid state 3 (MAX+1) passed to off() — no default, does nothing
     // -----------------------------------------------------------------------
 
     // state = 3 (MAX+1 invalid): off() has no case for 3, does nothing
@@ -333,4 +324,20 @@
         assertFalse(ss.ac.isOn);
         assertFalse(ss.heater.isOn);
     }
+
+    // -----------------------------------------------------------------------
+    // actionPerformed() delegates to timerOff(): boundary at coolTemp+1
+    // state = COOL, room.temp = coolTemp+1 (69 > 68): condition TRUE -> ac.on()
+    // actionPerformed() calls timerOff() which turns AC on.
+    // -----------------------------------------------------------------------
+
+    // actionPerformed() with COOL state and room.temp > coolTemp: ac turns on
+    @Test
+    void testBVAActionPerformedCoolTempAboveBoundary() {
+        ss.cool();
+        ss.room.temp = ss.coolTemp + 1; // 69, condition (69 > 68) is TRUE
+        ss.actionPerformed(new ActionEvent(ss, ActionEvent.ACTION_PERFORMED, ""));
+        assertTrue(ss.ac.isOn);
+        assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
+    }
 }
```

## 6.  — 

## 7.  — 

## 8.  — 

## 9.  — Model returned invalid JSON (Expecting property name enclosed in double quotes, line 6 column 38). Reply began: 'I need to analyze the missed branches carefully.\n\n**Lines 101-102 in main():** \n```java\nif (args.length==0) s.cool(); else   // line 101\nif ("off".compareTo(arg'

## 10. test — Target 10 measured missing branch line(s)

```diff
--- approved JUnit suite (before)
+++ approved JUnit suite (after)
@@ -479,4 +479,85 @@
         assertTrue(ss.ac.isOn);
         assertEquals(SeasonSwitch.COOL, SeasonSwitch.state);
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
+    void testMainArgHeat() throws Exception {
+        ExitTrap.Result r = ExitTrap.runMain(1500, "heat");
+        assertFalse(r.exitedByItself);
+        assertTrue(r.output.contains("Heating started"));
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
+        int before = ss.room.temp;
+        ss.room.actionPerformed(null);
+        assertEquals(before, ss.room.temp);
+    }
+
+    @Test
+    void testRoomActionPerformedCoolAcOn() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = true;
+        int before = ss.room.temp;
+        ss.room.actionPerformed(null);
+        assertEquals(before - 1, ss.room.temp);
+    }
+
+    @Test
+    void testRoomActionPerformedCoolAcOff() {
+        SeasonSwitch.state = SeasonSwitch.COOL;
+        ss.ac.isOn = false;
+        int before = ss.room.temp;
+        ss.room.actionPerformed(null);
+        assertEquals(before + 1, ss.room.temp);
+    }
+
+    @Test
+    void testRoomActionPerformedHeatHeaterOn() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = true;
+        int before = ss.room.temp;
+        ss.room.actionPerformed(null);
+        assertEquals(before + 1, ss.room.temp);
+    }
+
+    @Test
+    void testRoomActionPerformedHeatHeaterOff() {
+        SeasonSwitch.state = SeasonSwitch.HEAT;
+        ss.heater.isOn = false;
+        int before = ss.room.temp;
+        ss.room.actionPerformed(null);
+        assertEquals(before - 1, ss.room.temp);
+    }
 }
```

## 11.  — 

## 12. test — Target 1 measured missing branch line(s)

```diff
--- approved JUnit suite (before)
+++ approved JUnit suite (after)
@@ -560,4 +560,12 @@
         ss.room.actionPerformed(null);
         assertEquals(before - 1, ss.room.temp);
     }
+
+    @Test
+    void testRoomActionPerformedInvalidState() {
+        SeasonSwitch.state = 3;
+        int before = ss.room.temp;
+        ss.room.actionPerformed(null);
+        assertEquals(before, ss.room.temp);
+    }
 }
```

## 13.  — 
