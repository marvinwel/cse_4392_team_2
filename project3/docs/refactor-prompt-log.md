# Refactoring prompt variations (assignment step 8)

The assignment asks the team to try variations of the State-pattern prompt until the
result is satisfactory, then use the final prompt in the agent system. The prompt lives
in `app/refactor_nodes.py` (`REFACTOR_PROMPT`). Each variation is recorded here with
what it produced.

## Variation 1 (2026-11-13)

**Prompt requirement:** "Use a State interface and concrete states for OFF, COOL, and
HEAT. Put mode behavior and transitions in those states; do not retain a switch ladder
for operating modes."

**Result (run through the agent system, Claude Sonnet on Bedrock):**
- 47/47 adapted tests passed on the refactored code.
- One file only (`SeasonSwitch.java`). The three states were anonymous objects inside it.
- The code kept `static int state` and added `switch (state)` in a `currentState()`
  helper to pick the State object.
- `Room.actionPerformed` still used `switch (state)`.

**Verdict:** not satisfactory. The mode is still an int and a switch still selects
behavior. The model kept them so tests that assign `SeasonSwitch.state = <int>` compile.

## Variation 2 (2026-11-13)

**Change:** require a State-typed `state` field, OFF/COOL/HEAT redefined as State
objects, one top-level file per state class, no switch or if/else chain on the mode
(including `Room.actionPerformed`), and out-of-range-mode tests adapted to a `null`
state that the main class treats as a no-op.

**Result:** _fill in after the run: files produced, tests passed/total, branch coverage,
whether any switch or int mode remains._

**Verdict:** _satisfactory / not satisfactory, and why._

## Final prompt

_State which variation is used in the submitted agent system._
