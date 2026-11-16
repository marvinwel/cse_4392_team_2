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

**Result (run through the agent system, Claude Sonnet on Bedrock):**
- 51/51 adapted tests passed on the refactored code.
- Five files: `State.java`, `OffState.java`, `CoolState.java`, `HeatState.java`, `SeasonSwitch.java`.
- `static State state`, with OFF/COOL/HEAT as State objects. No int mode and no switch remain.
- `Room.actionPerformed` delegates to `state.roomTick(...)`.
- Branch coverage 12/18 (main() excluded). All 6 missed branches are room-tick code
  (`Room.actionPerformed`, `CoolState.roomTick`, `HeatState.roomTick`), which no test calls yet.

**Verdict:** satisfactory as a State-pattern design. Coverage is not yet 100%; that
needs Room tests, not a prompt change.

## Web LLM iterations (2026-11-16)

The assignment asks for prompt variations with a web-based LLM. Each version below was
pasted into a new temporary chat in ChatGPT (GPT 6, High), together with the original
`SeasonSwitch.java`. The prompt texts are in `docs/web-llm-prompts/`. Each answer was
then checked against the approved JUnit suite of the human-reviewed run (53 tests).

### Web version 1: plain request

**Prompt:** "Refactor this Java class to use the State design pattern."

**Result:**
- One file. The State interface, the three states, AC, Heater and Room are all
  `private` nested classes.
- `state` became a private instance field. The `OFF`, `COOL` and `HEAT` constants were removed.
- No `switch` remains, and Room delegates to `state.updateRoom()`.

**Verdict:** this is a real State pattern, but it breaks the interface. The tests read
`ss.ac`, `ss.heater` and `SeasonSwitch.state`, which are now private or gone, so the suite
cannot compile against it (found by reading the code). This led to adding the
assignment's hint about keeping the class name and interface.

### Web version 2: keep the class name and interface

**Change:** "Keep the class name SeasonSwitch, its package, and every public method name
and parameter list exactly the same, so the existing JUnit tests can be reused."

**Result:**
- Five files: `SeasonSwitch`, the `SeasonState` interface, `OffState`, `CoolingState`, `HeatingState`.
- It kept `static int state` and the int constants "for compatibility". The real mode is
  a separate private `currentState` field.
- Run against the 53 approved original tests: 19 pass, **34 fail**. Tests that set
  `SeasonSwitch.state = SeasonSwitch.COOL` no longer change the behavior, because
  the int field is only a copy.

**Verdict:** not satisfactory. It has two sources of truth for the mode. The prompt has
to require a State-typed `state` field and State-object constants.

### Web version 3: final prompt (same requirements as the agent's `REFACTOR_PROMPT`)

**Change:** the full requirement list from `app/refactor_nodes.py`: a State-typed
`static State state`, `OFF`/`COOL`/`HEAT` as State objects, one top-level file per state,
no switch or if/else on the mode (including `Room.actionPerformed`), and a null
state as a no-op. The JSON output format and the test-adaptation lines were left
out, because they only matter inside the agent.

**Result:**
- Five files: `State`, `OffState`, `CoolState`, `HeatState`, `SeasonSwitch`.
- `static State state = OFF`, and the constants are State objects. No int mode and no `switch` remain.
- Run against the adapted tests from the human-reviewed run: **53/53 pass, 26/26
  branches (100%)**.

**Verdict:** satisfactory. It matches the design the agent produces with the same
requirements. This confirms the final prompt that is used in the agent system.

## Final prompt

Variation 2 is the prompt used in the submitted agent system. Web version 3 above
confirms it on a web-based LLM.
