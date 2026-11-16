# Repair and gap-test agents: what the dashboard reads

The dashboard does not ask the repair agent or the gap-test agent for anything new.
It reads what `app/repair_nodes.py` and `app/main.py` already record. If these names
change, update `app/ui/data.py` (`repair_rows`) and `app/ui/runner.py` (step maps).

## Workflow state keys

| State key | Used for |
|---|---|
| `repair_log` | The repair list. One row per proposal, AI error, human decision and rerun result |
| `repair_attempts_by_phase` | "attempts used" on the JUnit screens |
| `coverage_rounds_by_phase` | "rounds used" on the coverage screens |
| `repair_error`, `gap_error` | The reason shown when the workflow stops early |
| `workflow_status` | Statuses ending in `exhausted`, `failed` or `blocked` are shown as stopped |

Each `repair_log` row (written by `repair_log_entry`): `kind` (`repair` or `gap`), `phase`,
`outcome` (`proposed`, `ai_error`, `human_rejected`, `approved`, `applied`, `rerun_passed`,
`rerun_failed`, `exhausted`), and where they apply `attempt`, `tests`, `diagnosis`, `target`,
`path`, `error`, `feedback`, `auto`, `passed`, `total`.

When no workflow is running in the dashboard, the same list is read from the change log the
last run saved: `generated_tests/change_log_<phase>.json` (`repair_log` and the two counters).

## Human review of a proposal

`review_tests` pauses with these payload keys. The dashboard opens the proposal screen when
`review_context` is `repair` or `gap`, otherwise the normal test review.

| Payload key | Used for |
|---|---|
| `review_context` | Which screen opens |
| `proposed_target` | The file named above the diff |
| `proposed_diff` | The diff shown, unchanged |
| `ai_review_notes` | Warning boxes on the normal test review (`EP`, `BVA`) |
| `prior_feedback` | "Your previous feedback" |

The answer sent back is `{"approved": bool, "feedback": str}`. The normal test review may also
send `test_feedback` (`{test method name: comment}`); it is ignored for a proposal.

## Graph node names

`repair_agent`, `apply_code_repair`, `generate_gap_tests`, `run_tests`, `check_coverage`,
`review_tests`, `escalate_review` are mapped to the 11 steps in `app/ui/runner.py`.
A node that is not in the map is shown under the current step with its own name.
