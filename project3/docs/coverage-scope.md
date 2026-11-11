# JaCoCo coverage scope: original SeasonSwitch (Person 3 proposal, needs team sign-off)

The professor requires **100% BRANCH coverage** (not line coverage) for the original and the refactored code.
This note fixes **what is measured** so nobody quietly excludes the hard branches later.

## What JaCoCo will measure

Verified from the compiled bytecode (`javap -c`) of `app/SeasonSwitch.java`. JaCoCo counts each distinct jump target. `javac` gives every `case` its own target, plus one for `default`, so each 3-case `switch` is **4 branches**.

| Class (JaCoCo name) | Method | Source lines | Branches | How to reach every branch |
|---|---|---|---|---|
| `SeasonSwitch` | `cool()` | 18 | 4 | state = OFF, COOL, HEAT, **invalid (e.g. 5)** |
| `SeasonSwitch` | `heat()` | 36 | 4 | same four states |
| `SeasonSwitch` | `off()` | 54 | 4 | same four states |
| `SeasonSwitch` | `timerOff()` | 74, 77, 86 | 4 + 2 + 2 | four states; COOL with temp >68 and ≤68; HEAT with temp <77 and ≥77 |
| `SeasonSwitch` | `main(String[])` | 101, 102, 107, 108 | 8 | no args / `off` / `cool` / `heat` / unknown (see below) |
| `SeasonSwitch$Room` | `actionPerformed()` | 134, 137, 140 | 4 + 2 + 2 | call `s.room.actionPerformed(null)` directly in each state, with AC/heater on and off |
| `SeasonSwitch$AC`, `$Heater` | `on()`, `off()` | — | 0 | (lines only) |
| **Total** | | | **36** | 28 in `SeasonSwitch`, 8 in `Room` |

**Default branches (5 of the 36):** these are reachable because `SeasonSwitch.state` is a package-private `static int`. A test in package `cse4392` can set `SeasonSwitch.state = 5`. That is the EP "invalid state" partition, so it is a legitimate test and not a coverage trick. Tests must reset `state` in `@BeforeEach`/`@AfterEach` because it is static.

## The hard part: `main()` (8 branches)

- `off` and unknown args call `System.exit(...)`, which would kill the Surefire test JVM.
- no args, `cool` and `heat` block forever on `new CountDownLatch(5).await()`. They only return if the thread is interrupted, and that interrupt path is also how the `catch` block gets covered.

Options for the team:

| Option | Scope / config | Pros | Cons |
|---|---|---|---|
| **A. Full scope (recommended)** | `BUNDLE` (the current pom); `exclude_methods: []` | Matches "100% branch coverage" literally; nothing hidden | `main` needs an integration-style test, described below |
| B. Exclude `main` | `DEFAULT_COVERAGE_SCOPE["exclude_methods"] = ["SeasonSwitch.main"]` | Simple | Must be justified in the deck. The pom `BUNDLE` check would still fail, so it would need changing too. Risk of losing points |
| C. Change the source | — | — | **Not allowed**: the original code is the thing under test |

How Option A would test `main` without editing the source:

1. **no args / `cool` / `heat`:** run `SeasonSwitch.main(args)` on a separate thread, wait until `SeasonSwitch.state` changes, then `thread.interrupt()`. The `catch` stops both timers and `main` returns. All of this stays in the test JVM, so JaCoCo records it.
2. **`off` / unknown:** run `java -cp target/classes cse4392.SeasonSwitch off` (and `bogus`) as a **child JVM** from the test, with the same JaCoCo agent attached (`append=true`). Then assert exit codes 0 and 1 and check stdout. The child JVM writes its coverage to `jacoco.exec` on exit.
   - Pom change if we choose this: pass the agent string into the test with `<jacoco.agent.argLine>` / `@{argLine}`. Person 3 owns this.

## What is enforced where

- `mvn clean verify` (humans and CI) fails if any test fails or if `BUNDLE` branch coverage is below 1.00.
- The agent runs with `-Djacoco.haltOnFailure=false -Dmaven.test.failure.ignore=true`, so reports are always produced. `check_coverage` then sets `fully_covered` from the XML for the agreed scope, and Ryan's R3 router acts on that.
- The scope used is written into every `artifacts/<phase>/SUMMARY.md` and `coverage.json`.

## Decision (fill in at the meeting)

- [ ] Option chosen: ____ Agreed by: ____ Date: ____
- [ ] If B: justification sentence for the slides: ____
- [ ] Refactored phase uses the same rule. A State-pattern refactor adds new classes (`State`, `OffState`, …). All of them are included, and `SeasonSwitch.main` follows the same option.
