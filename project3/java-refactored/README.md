# java-refactored

Same Maven/JUnit/JaCoCo setup as `java-original/` (identical pinned versions and the same 100% BRANCH rule).

- Emily's `refactor_state_pattern` / `adapt_tests` writes the State-pattern sources to `src/main/java/cse4392/`
  (the `SeasonSwitch` class name and public API must not change) and the reused approved suite to `src/test/java/cse4392/`.
- The graph sets `phase = "refactored"`. `run_tests`, `check_coverage` and `save_results` then use this folder,
  and evidence goes to `artifacts/refactored/`.
