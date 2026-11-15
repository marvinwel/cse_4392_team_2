# Person 4 — Sarthak: repair and coverage-gap nodes

## Files and ownership

- `app/repair_nodes.py` — **new**, owns `repair_agent`, `generate_gap_tests`, retry guards, validation, diffs, and safe source updates.
- `app/main.py` — **small wiring changes**: register the nodes; failed test runs go to `repair_agent`, missed branches go to `generate_gap_tests`, revised tests return to Ryan's existing human review (`review_tests`) before execution. The original EP/BVA generator, Maven, JaCoCo, and State-pattern implementations are unchanged.
- `tests/test_repair_nodes.py` — **new**, deterministic tests using a fake model, real JaCoCo fixtures and actual `javac` execution for a seeded defect.

## Workflow

1. Joseph's `run_tests` produces Surefire errors or a compile failure. Ryan routes failures to `repair_agent` in **either** phase.
2. The agent reads only the currently active `java-original/` or `java-refactored/` working source, approved JUnit suite, and failure report. The shared existing model proposes a complete replacement for **one** existing Java source file or the approved test file.
3. A production-code repair is validated, applied atomically to the **working phase copy only**, logged with a unified diff and reason, then rerun. `app/SeasonSwitch.java` and the original uploaded ZIP are not touched.
4. A test-file repair is **not written** until the existing `review_tests` human interrupt explicitly approves the diff. A rejected proposal restores the last approved suite; reviewer feedback is supplied to the next bounded attempt. Assertion count and existing test-method names cannot decrease, but human review is still mandatory for every test change.
5. Joseph's `check_coverage` provides measured JaCoCo `missed_branches` (source file, class, line). `generate_gap_tests` requests only new `COVERAGE` JUnit methods mapped to those exact reported gaps. They append to the approved suite, go to human review, run through Joseph's Maven node, and return to JaCoCo measurement.
6. At most **3 repair proposals and 3 coverage-test proposals per phase**. Invalid proposals, missing evidence or exhausted retries escalate to a recorded failure state; they do **not** report success or endlessly loop.

## Verification

From the `project3` repository root:

```sh
python -m compileall -q app tests
python -m unittest discover -s tests -p 'test_*.py' -v
```

The new tests include code/test repair decisions, human-rejection feedback and restoration, JaCoCo-driven coverage proposals, path traversal protection, output validation, retry caps, and **real Java compilation/execution** of a deliberately seeded threshold bug before and after repair.

To run the **actual full multi-agent workflow** (requires your team's Bedrock credentials, installed Python dependencies, and Maven on `PATH`):

```sh
python app/main.py
```

Do not use `AUTO_APPROVE=1` as evidence of human review. The professor requires both human approvals. Also note that the repository's current `main.py` run configuration measures `SeasonSwitch` **excluding `main()` and inner classes**; that narrower scope is a team decision to resolve with Ryan and Joseph before claiming full required branch coverage. See `docs/coverage-scope.md`.
