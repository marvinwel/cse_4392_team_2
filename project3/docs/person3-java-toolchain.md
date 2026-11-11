# Person 3 (Joseph): Java toolchain, test execution and coverage

## Files
| Path | What it is |
|---|---|
| `java-original/pom.xml` | Pinned JUnit 5.11.4, Surefire 3.5.2, JaCoCo 0.8.12, compiler 3.13.0, Java release 17 (runs on 17 or 21); BRANCH COVEREDRATIO ≥ 1.00 |
| `java-original/src/main/java/cse4392/SeasonSwitch.java` | Copy of `app/SeasonSwitch.java` (the code under test) |
| `java-original/src/test/java/cse4392/SeasonSwitchSmokeTest.java` | 3 hand-written baseline tests (G1 smoke test) |
| `java-refactored/pom.xml` | Same build for Emily's State-pattern version |
| `app/java_tools.py` | `write_test_file`, `run_maven`, `parse_surefire`, `parse_jacoco` + CLI |
| `app/testing_nodes.py` | Graph nodes `run_tests`, `check_coverage`, `save_results` and router `route_test_results` (R2) |
| `fixtures/surefire-pass.xml`, `jacoco-partial.xml` | REAL reports from the first `mvn clean verify` (smoke suite: 3/3 pass, 5/36 branches) |
| `fixtures/surefire-fail.xml` | Hand-built failure fixture (seeded-defect scenario) in Surefire format, for Sarthak's repair loop |
| `tests/test_java_tools.py` | 22 unit tests; no Maven needed |
| `docs/coverage-scope.md` | Branch inventory (36 branches) + `main()` scope decision for the team |

## Commands (from the repo root)
```bash
# 1. Unit tests for the Python tools (no Maven/JDK needed)
python -m unittest discover -s tests -v

# 2. Baseline Maven run, as a human gate (fails on test failure OR <100% branch coverage)
cd java-original && mvn -B clean verify ; cd ..
#    The smoke suite deliberately covers ~5/36 branches, so this FAILS the coverage check. That is expected.

# 3. Same run the agent does: always produces reports, then prints parsed results
python app/java_tools.py original --test-class SeasonSwitchSmokeTest
python app/java_tools.py original --test-class SeasonSwitchMergedTest   # after copying Marvin's suite in

# Reports
#   java-original/target/surefire-reports/TEST-*.xml
#   java-original/target/site/jacoco/jacoco.xml   and   index.html
```

## Wiring into Marvin's main.py (Ryan)
```python
from testing_nodes import run_tests, check_coverage, save_results, route_test_results
# Add to AgentState:  phase: str; test_report: dict; coverage: dict; coverage_scope: dict; saved_artifacts: dict
graph.add_node("run_tests", run_tests)            # replaces run_tests_stub
graph.add_node("check_coverage", check_coverage)
graph.add_node("save_results", save_results)
graph.add_conditional_edges("run_tests", route_test_results,
                            {"passed": "check_coverage", "failed": "repair_agent"})
```
`run_tests` reads `state["merged_tests"]` (the approved suite), writes it to `java-<phase>/src/test/java/cse4392/<Class>.java`,
and runs only that class (`-Dtest=`). It returns `test_report` (counts, `all_passed`, per-failure message, type and trimmed stack
trace, build exit code, timeout flag, compile-error flag and log path). One Maven run produces both reports; `check_coverage` only
parses them and returns `coverage` (`branch.covered/missed/total/percent`, `fully_covered`, `missed_branches[]` with
class/method/line, plus per-class counts). `save_results` copies everything into `artifacts/<phase>/` with a `SUMMARY.md`.

## Contract for Sarthak (gen_missing_branch_tests / repair_agent)
- Failures: `state["test_report"]["failures"]` → `{test, classname, name, kind: failure|error, type, message, details}`.
  Compile errors: `test_report["build"]["compile_error"]` and `test_report["build_output_tail"]`.
- Gaps: `state["coverage"]["missed_branches"]` → `{source_file, class, method, line, missed_branches, covered_branches}`.

## Status
- Python tools and nodes: 22/22 unit tests pass against the fixtures.
- `SeasonSwitch.java` compiles on JDK 21. The branch inventory was checked against the `javap` bytecode.
- 2026-11-09 first real run (macOS, Maven 3.9.11, Java release 17): `mvn -B clean verify` compiled the code and ran 3/3 smoke tests
  green. JaCoCo analyzed 4 classes; branch ratio 0.13 (5/36) correctly FAILED the 1.00 gate. The real missed-branch lines
  match the predicted inventory in `coverage-scope.md` exactly.

## Suggested .gitignore additions
```
java-*/target/
```
