"""
Team Assignment 3 - Multi-agent test generation for SeasonSwitch.

Claude generates the tests, Amazon Nova Micro reviews them.
EP and BVA tests are each reviewed on their own before they are merged.

    load_source --+-- ep_agent  -- review_ep  --+-- ep_done  --+
                  |      ^-------- rejected ----+              |
                  |                                            +-- merge_tests -- run_tests --+-- check_coverage -- R3
                  +-- bva_agent -- review_bva --+-- bva_done --+                              |
                         ^-------- rejected ----+                                             +-- review_failures
                                                                                                 (Nova explains the failures,
                                                                                                  both agents regenerate)
    Too many rejections or failed test runs -> escalate_review
    Every ending (save_results / escalate_review / generate_gap_tests) -> save_change_log -> END

Logging:
    generated_tests/agent_run.log           - everything shown during the run
    generated_tests/change_log_<phase>.json - every change to the tests, with diffs and reasons
"""

import difflib
import json
import logging
import operator
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Annotated, TypedDict

from botocore.config import Config
from dotenv import load_dotenv
from langsmith import traceable
from langchain_core.prompts import ChatPromptTemplate
from langchain_aws import ChatBedrockConverse
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt

try:
    from refactor_nodes import build_refactor_nodes
except ImportError:  # when run as `python -m app.main`
    from app.refactor_nodes import build_refactor_nodes

# >>> PERSON 3 (Joseph) BEGIN: imports
# Maven/JUnit/JaCoCo execution, coverage and evidence nodes (app/testing_nodes.py)
try:
    from testing_nodes import run_tests, check_coverage, save_results, route_test_results
except ImportError:  # when run as `python -m app.main`
    from app.testing_nodes import run_tests, check_coverage, save_results, route_test_results
# <<< PERSON 3 (Joseph) END: imports


# ===========================================================================
# 1. Config
# ===========================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(Path(__file__).resolve().parent / ".env")

MAX_REVIEW_REJECTIONS = 3     # per agent (EP / BVA), per round
MAX_TEST_FIX_ROUNDS = 2       # how many times failed test runs go back for fixing
MAX_HUMAN_REJECTIONS = 3      # how many times the human reviewer can request changes
MAX_MERGE_FAILURES = 2        # how many times a failed EP/BVA merge goes back for fixing
MAX_REFACTOR_ERRORS = 2       # how many unusable refactor replies are retried
MAX_REFACTOR_FIX_ROUNDS = 2   # how many times failing refactored tests go back for fixing
REFACTOR_MAX_TOKENS = 16000   # one reply holds every refactored file plus the adapted tests

# Refactored phase: measure EVERY class, so the new State classes are counted.
# main() stays excluded only because the original phase excludes it; the team still
# has to settle main() and Room (docs/coverage-scope.md).
REFACTORED_COVERAGE_SCOPE = {"include_classes": None, "exclude_methods": ["SeasonSwitch.main"]}

GENERATOR_MODEL = "qwen.qwen3-coder-30b-a3b-v1:0"   # Qwen3 Coder 30B A3B: writes the tests
CLAUDE_MODEL = "us.anthropic.claude-sonnet-4-6"
REVIEW_MODEL = "us.amazon.nova-micro-v1:0"          # Amazon Nova Micro: reviews the tests (cheapest)
REVIEW_MAX_TOKENS = 4000                            # review answers are short JSON; keeps under Nova's output limit
REGION = "us-east-1"
TEMPERATURE = 0
MAX_TOKENS = 8000

OUTPUT_DIR = BASE_DIR / "generated_tests"
MERGER_JAR = BASE_DIR / "junit-merger" / "target" / "junit-merger-1.0.0.jar"

# Logging: show on screen and save to generated_tests/agent_run.log
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
log = logging.getLogger("assignment3")
log.setLevel(logging.INFO)
log.propagate = False                     # keep boto3 / langchain noise out of our log
_formatter = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%H:%M:%S")
for _handler in (logging.StreamHandler(),
                 logging.FileHandler(OUTPUT_DIR / "agent_run.log", mode="w", encoding="utf-8")):
    _handler.setFormatter(_formatter)
    log.addHandler(_handler)

generator_model = ChatBedrockConverse(
    model=CLAUDE_MODEL,
    region_name=REGION,
    temperature=TEMPERATURE,
    max_tokens=MAX_TOKENS,
)

# The reviewer answers in plain JSON and the review nodes read it.
# This works with any model (Nova could not do tool calls), so switching models is one line.
review_model = ChatBedrockConverse(
    model=REVIEW_MODEL,
    region_name=REGION,
    temperature=TEMPERATURE,
    max_tokens=REVIEW_MAX_TOKENS,
)

# The refactor reply is long (all source files + the adapted tests in one JSON object),
# so it gets a larger output limit and a longer read timeout than test generation.
refactor_model = ChatBedrockConverse(
    model=CLAUDE_MODEL,
    region_name=REGION,
    temperature=TEMPERATURE,
    max_tokens=REFACTOR_MAX_TOKENS,
    config=Config(read_timeout=600, retries={"max_attempts": 2}),
)

# Person 5 nodes. Ryan owns adding these callables to the graph and wiring R4.
refactor_agent, review_refactor = build_refactor_nodes(
    refactor_model, BASE_DIR, interrupt,
)


# ===========================================================================
# 2. State
# ===========================================================================
# EP and BVA run in parallel, so each one gets its own keys.
# (Two parallel nodes writing the same key would make LangGraph raise an error.)
class AgentState(TypedDict, total=False):
    source_path: str
    source_code: str
    class_name: str           # "SeasonSwitch"
    package_name: str         # "cse4392"

    # Equivalence Partitioning branch
    ep_tests: str
    ep_approved: bool
    ep_feedback: str
    ep_review_count: int      # total Nova reviews of the EP tests
    ep_rejections: int        # rejections in the current round

    # Boundary Value Analysis branch
    bv_tests: str
    bv_approved: bool
    bv_feedback: str
    bv_review_count: int      # total Nova reviews of the BVA tests
    bv_rejections: int

    merged_tests: str
    test_fix_rounds: int
    workflow_status: str

    # Human review of the merged tests (R1, Ryan)
    human_approved: bool
    human_feedback: str
    human_review_count: int
    human_rejections: int

    # Merge failure recovery (Ryan)
    merge_error: str          # empty when the last merge worked
    merge_failures: int

    # Person 5 State-pattern generation, test adaptation, and review gate.
    refactored_files: dict[str, str]
    refactored_tests: str
    refactor_explanation: str
    refactor_feedback: str
    refactor_approved: bool
    refactor_review_count: int
    refactor_revision_count: int
    refactor_status: str

    # Refactored-phase orchestration (Ryan)
    refactor_error: str       # empty when the last refactor reply was usable
    refactor_errors: int
    refactor_fix_rounds: int  # failed refactored test runs sent back for fixing

    # Change log: every node adds its entries; operator.add joins the lists,
    # so the parallel EP and BVA nodes can both add entries in the same step.
    change_log: Annotated[list, operator.add]

    # >>> PERSON 3 (Joseph) BEGIN: state keys
    phase: str              # "original" | "refactored"
    test_class: str         # optional: run this test class instead of merged_tests
    test_report: dict       # written by run_tests (Surefire results)
    coverage: dict          # written by check_coverage (JaCoCo branch coverage)
    coverage_scope: dict    # optional override of the measured scope
    saved_artifacts: dict   # written by save_results: {"original": path, ...}
    # <<< PERSON 3 (Joseph) END: state keys


# ===========================================================================
# 3. Prompts
# ===========================================================================
COMMON_RULES = """
Rules:
- These are FUNCTIONAL (black-box) test cases: derive partitions and boundaries
  from the inputs and expected behavior of each public method, not from its
  internal statement structure.
- Write JUnit 5 tests (org.junit.jupiter.api.*) in package {package_name}.
- Test ONLY the {class_name} class. Do NOT write tests for its inner classes.
  You MAY read inner-class fields (e.g. an on/off flag on a helper object) to
  check the result of a {class_name} method.
- Cover EVERY public method of {class_name} except main().
- Before writing an expected value, TRACE the code by hand for that input.
  Never assume behavior. A switch with no default case does nothing for
  unmatched values. Note whether each comparison is strict (<, >) or not (<=, >=).
- If a field is static, reset it in a @BeforeEach method, because static values
  carry over between tests.
- If the class starts timers or threads, stop them in an @AfterEach method.
- SHARED FIXTURE: the EP and BVA classes are merged into ONE class, so both must
  declare the SAME fixture, character for character. Copy exactly this, with no
  extra modifiers, comments, fields, @BeforeEach or @AfterEach methods:

    {class_name} ss;

    @BeforeEach
    void setUp() {{
        {class_name}.state = {class_name}.OFF;
        ss = new {class_name}();
    }}

    @AfterEach
    void tearDown() {{
        ss.timer.stop();
        ss.room.timer.stop();
        {class_name}.state = {class_name}.OFF;
    }}

  Put any extra per-test setup inside the test method itself.
- Besides return values or state, assert observable side effects
  (devices on/off, timers running or stopped).
- No duplicate tests: each test must use a different input or starting state.
- Put a short comment above each test naming the partition or boundary it covers.
- Only use methods, fields, and constructors that exist in the given code.
- Return ONLY the raw Java file. No markdown, no ``` fences, no explanation.
"""

EP_METHOD = """You are a software testing expert.
Generate FUNCTIONAL test cases using EQUIVALENCE PARTITIONING.

Method:
1. List every public method of {class_name} (except main) and every input it
   depends on: its parameters AND the fields it reads (such as a state variable
   or a value it compares against a threshold).
2. For each method, divide those inputs into equivalence classes, where every
   value in a class causes the same behavior:
   - one VALID class per distinct behavior (each case of a switch, each outcome of an if)
   - one VALID class per side of every comparison (e.g. above vs. at-or-below a threshold)
   - one INVALID class for values that match no case or are outside the allowed range
3. Pick ONE representative value from the middle of each class, not its edges.
4. Write one test per equivalence class.

Name every @Test method using the testEP prefix.
Example: testEPHeatFromOff().
Every generated method name must be unique.
"""

BV_METHOD = """You are a software testing expert.
Generate FUNCTIONAL test cases using BOUNDARY VALUE ANALYSIS.

Method:
1. Find every numeric comparison in {class_name} (e.g. temp > limit, x < max)
   and every bounded range of values a variable can take (e.g. state constants 0..2).
2. For each comparison against a value N, test N-1, N, and N+1, and say in the
   comment whether the condition is true or false at exactly N.
3. For each range MIN..MAX, test MIN and MAX (valid) and MIN-1 and MAX+1 (invalid).
   Trace what the code really does with the invalid values.
4. Do NOT invent boundaries for things that have no numeric comparison or range.
5. Use field names instead of hard-coded numbers where possible
   (e.g. coolTemp - 1 instead of 67).
6. Write one test per boundary value.

Name every @Test method using the testBVA prefix.
Example: testBVAHeatFromOff().
Every generated method name must be unique.
"""

GENERATE_HUMAN = """Generate or revise {test_class_name}.

Java source:
{source_code}

Previous tests:
{previous_tests}

Reviewer feedback:
{feedback}

If feedback is provided, revise the previous tests to address it while
preserving valid test coverage. Otherwise, generate new tests.
"""

generate_prompt = ChatPromptTemplate.from_messages([
    ("system", "{method}\n" + COMMON_RULES),
    ("human", GENERATE_HUMAN),
])

EP_CHECKS = """
1. One test per equivalence class: each switch case, each side of every comparison,
   and an INVALID class for unmatched / out-of-range values.
2. Representative values come from the MIDDLE of each class, not its edges.
"""

BV_CHECKS = """
1. Every numeric comparison against N is tested at N-1, N and N+1, and each comment
   says whether the condition is true or false at exactly N.
2. Every range MIN..MAX is tested at MIN, MAX, MIN-1 and MAX+1.
3. No invented boundaries for things with no numeric comparison or range.
"""

REVIEW_SYSTEM = """You are an expert Java JUnit 5 test reviewer.
Review these {technique} tests against the Java source.

Technique checks:
{technique_checks}
General checks:
- Expected assertion values are correct (trace the code for each input).
- All public methods of {class_name} except main are tested; no tests for inner classes.
- Static variables are reset in @BeforeEach; timers and threads are stopped in @AfterEach.
- No duplicate tests.
- No nonexistent methods, fields or constructors.

Reject incorrect or incomplete tests and give specific feedback on what must change.
Approve only when every check passes.

Respond ONLY with JSON in exactly this form, nothing else:
{{"approved": true or false, "feedback": "specific corrections, empty string if approved"}}
"""

review_prompt = ChatPromptTemplate.from_messages([
    ("system", REVIEW_SYSTEM),
    ("human", "Java source:\n{source_code}\n\n{technique} tests:\n{tests}"),
])

FAILURE_SYSTEM = """You are an expert Java JUnit 5 test reviewer.
The merged EP + BVA test class below was run and some tests FAILED.
For each failing test, explain why it failed (wrong expected value, missing reset,
nonexistent method, compile error, ...) and exactly how to fix it.
Name each failing test method so the EP and BVA authors can find their own tests.
Answer in plain text."""

failure_prompt = ChatPromptTemplate.from_messages([
    ("system", FAILURE_SYSTEM),
    ("human", "Java source:\n{source_code}\n\nMerged tests:\n{merged_tests}\n\nTest results:\n{test_results}"),
])


# ===========================================================================
# 4. Nodes
# ===========================================================================
def load_source(state: AgentState) -> dict:
    return {"source_code": Path(state["source_path"]).read_text(encoding="utf-8")}


# ---- Node 2: Equivalence Partitioning generator (Claude) ----
@traceable(name="Generate EP tests", run_type="tool")
def generate_ep_tests(state: AgentState) -> dict:
    previous_tests = state.get("ep_tests", "")
    feedback = state.get("ep_feedback", "")
    log.info("[EP] Claude %s Equivalence Partitioning tests...", "revising" if previous_tests else "generating")
    response = (generate_prompt | generator_model).invoke({
        "method": EP_METHOD.format(class_name=state["class_name"]),
        "package_name": state["package_name"],
        "class_name": state["class_name"],
        "test_class_name": f"{state['class_name']}EPTest",
        "source_code": state["source_code"],
        "previous_tests": previous_tests,
        "feedback": feedback,
    })
    # Bedrock can return a string or a list of content blocks
    content = response.content
    text = content if isinstance(content, str) else "".join(
        b.get("text", "") for b in content if isinstance(b, dict))
    # Keep only the Java code if the model wrapped it in ``` fences
    match = re.search(r"```(?:java)?\s*(.*?)```", text, re.S)
    new_tests = (match.group(1) if match else text).strip()

    # Log what changed and why
    test_file = f"{state['class_name']}EPTest.java"
    diff = list(difflib.unified_diff(previous_tests.splitlines(), new_tests.splitlines(),
                                     f"{test_file} (before)", f"{test_file} (after)", lineterm=""))
    added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
    entry = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "phase": state.get("phase"),
        "node": "ep_agent",
        "action": "revised_tests" if previous_tests else "generated_tests",
        "reason": feedback or "initial generation",
        "test_count": new_tests.count("@Test"),
        "lines_added": added,
        "lines_removed": removed,
        "diff": "\n".join(diff) if previous_tests else "",
    }
    log.info("[EP] %s: %d tests (+%d / -%d lines)",
             entry["action"], entry["test_count"], added, removed)

    return {"ep_tests": new_tests, "change_log": [entry]}


# ---- Node 3: Boundary Value generator (Qwen) ----
@traceable(name="Generate BVA tests", run_type="tool")
def generate_bv_tests(state: AgentState) -> dict:
    previous_tests = state.get("bv_tests", "")
    feedback = state.get("bv_feedback", "")
    log.info("[BVA] Claude %s Boundary Value Analysis tests...", "revising" if previous_tests else "generating")
    response = (generate_prompt | generator_model).invoke({
        "method": BV_METHOD.format(class_name=state["class_name"]),
        "package_name": state["package_name"],
        "class_name": state["class_name"],
        "test_class_name": f"{state['class_name']}BVTest",
        "source_code": state["source_code"],
        "previous_tests": previous_tests,
        "feedback": feedback,
    })
    # Bedrock can return a string or a list of content blocks
    content = response.content
    text = content if isinstance(content, str) else "".join(
        b.get("text", "") for b in content if isinstance(b, dict))
    # Keep only the Java code if the model wrapped it in ``` fences
    match = re.search(r"```(?:java)?\s*(.*?)```", text, re.S)
    new_tests = (match.group(1) if match else text).strip()

    # Log what changed and why
    test_file = f"{state['class_name']}BVTest.java"
    diff = list(difflib.unified_diff(previous_tests.splitlines(), new_tests.splitlines(),
                                     f"{test_file} (before)", f"{test_file} (after)", lineterm=""))
    added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
    entry = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "phase": state.get("phase"),
        "node": "bva_agent",
        "action": "revised_tests" if previous_tests else "generated_tests",
        "reason": feedback or "initial generation",
        "test_count": new_tests.count("@Test"),
        "lines_added": added,
        "lines_removed": removed,
        "diff": "\n".join(diff) if previous_tests else "",
    }
    log.info("[BVA] %s: %d tests (+%d / -%d lines)",
             entry["action"], entry["test_count"], added, removed)

    return {"bv_tests": new_tests, "change_log": [entry]}


# ---- Node 4: EP review (Nova) - returns how many EP reviews have been done ----
@traceable(name="Nova review EP tests")
def review_ep_tests(state: AgentState) -> dict:
    count = state.get("ep_review_count", 0) + 1
    log.info("[EP] Nova reviewing Equivalence Partitioning tests (review #%d)...", count)

    response = (review_prompt | review_model).invoke({
        "technique": "Equivalence Partitioning",
        "technique_checks": EP_CHECKS,
        "class_name": state["class_name"],
        "source_code": state["source_code"],
        "tests": state["ep_tests"],
    })
    content = response.content
    text = content if isinstance(content, str) else "".join(
        b.get("text", "") for b in content if isinstance(b, dict))

    # The reviewer answers in JSON; anything unreadable counts as a rejection
    match = re.search(r"\{.*\}", text, re.S)
    try:
        review = json.loads(match.group(0), strict=False)
        approved = review.get("approved") is True or str(review.get("approved")).lower() == "true"
        feedback = str(review.get("feedback", "")).strip()
    except Exception:
        log.warning("[EP] Reviewer did not return valid JSON; treating as rejected.")
        approved = False
        feedback = text.strip() or "Reviewer returned no output."

    rejections = state.get("ep_rejections", 0) + (0 if approved else 1)

    log.info("[EP] Approved: %s | reviews: %d | rejections this round: %d/%d",
             approved, count, rejections, MAX_REVIEW_REJECTIONS)
    if feedback:
        log.info("[EP] Feedback: %s", feedback)

    return {
        "ep_approved": approved,
        "ep_feedback": "" if approved else feedback,
        "ep_review_count": count,
        "ep_rejections": rejections,
        "change_log": [{
            "time": datetime.now().isoformat(timespec="seconds"),
            "phase": state.get("phase"),
            "node": "review_ep",
            "action": "approved" if approved else "rejected",
            "review_number": count,
            "feedback": feedback,
        }],
    }


# ---- Node 5: BVA review (Nova) - returns how many BVA reviews have been done ----
@traceable(name="Nova review BVA tests")
def review_bv_tests(state: AgentState) -> dict:
    count = state.get("bv_review_count", 0) + 1
    log.info("[BVA] Nova reviewing Boundary Value Analysis tests (review #%d)...", count)

    response = (review_prompt | review_model).invoke({
        "technique": "Boundary Value Analysis",
        "technique_checks": BV_CHECKS,
        "class_name": state["class_name"],
        "source_code": state["source_code"],
        "tests": state["bv_tests"],
    })
    content = response.content
    text = content if isinstance(content, str) else "".join(
        b.get("text", "") for b in content if isinstance(b, dict))

    # The reviewer answers in JSON; anything unreadable counts as a rejection
    match = re.search(r"\{.*\}", text, re.S)
    try:
        review = json.loads(match.group(0), strict=False)
        approved = review.get("approved") is True or str(review.get("approved")).lower() == "true"
        feedback = str(review.get("feedback", "")).strip()
    except Exception:
        log.warning("[BVA] Reviewer did not return valid JSON; treating as rejected.")
        approved = False
        feedback = text.strip() or "Reviewer returned no output."

    rejections = state.get("bv_rejections", 0) + (0 if approved else 1)

    log.info("[BVA] Approved: %s | reviews: %d | rejections this round: %d/%d",
             approved, count, rejections, MAX_REVIEW_REJECTIONS)
    if feedback:
        log.info("[BVA] Feedback: %s", feedback)

    return {
        "bv_approved": approved,
        "bv_feedback": "" if approved else feedback,
        "bv_review_count": count,
        "bv_rejections": rejections,
        "change_log": [{
            "time": datetime.now().isoformat(timespec="seconds"),
            "phase": state.get("phase"),
            "node": "review_bva",
            "action": "approved" if approved else "rejected",
            "review_number": count,
            "feedback": feedback,
        }],
    }

# ---- Nodes 6a / 6b: mark each branch approved; merge_tests waits for both ----
def ep_done(state: AgentState) -> dict:
    log.info("[EP] Tests approved after %d review(s).", state.get("ep_review_count", 0))
    return {"ep_approved": state.get("ep_approved", True)}


def bva_done(state: AgentState) -> dict:
    log.info("[BVA] Tests approved after %d review(s).", state.get("bv_review_count", 0))
    return {"bv_approved": state.get("bv_approved", True)}


@traceable(name="JavaParser JUnit Merge", run_type="tool")
def merge_tests(state: AgentState) -> dict:
    if not MERGER_JAR.exists():
        raise FileNotFoundError(
            f"Merger jar not found: {MERGER_JAR}\n"
            "Build it with: cd junit-merger && mvn clean package"
        )
    class_name = state["class_name"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ep_file = OUTPUT_DIR / f"{class_name}EPTest.java"
    bv_file = OUTPUT_DIR / f"{class_name}BVTest.java"
    merged_file = OUTPUT_DIR / f"{class_name}MergedTest.java"
    ep_file.write_text(state["ep_tests"], encoding="utf-8")
    bv_file.write_text(state["bv_tests"], encoding="utf-8")

    log.info("Merging approved EP and BVA test cases and removing duplicates...")
    merged_file.unlink(missing_ok=True)   # never let an old merged file be run by mistake
    proc = subprocess.run(
        ["java", "-jar", str(MERGER_JAR), str(ep_file), str(bv_file),
         str(merged_file), f"{class_name}MergedTest"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0 or not merged_file.exists():
        # The generated classes could not be combined: send the reason back to both agents.
        error_lines = [line for line in proc.stderr.splitlines() if "Exception" in line]
        error = (error_lines[0] if error_lines else proc.stderr.strip()[-500:]) or "unknown merger error"
        failures = state.get("merge_failures", 0) + 1
        log.warning("Merge failed (%d/%d): %s", failures, MAX_MERGE_FAILURES, error)
        request = ("The EP and BVA test classes could NOT be merged into one class:\n"
                   f"{error}\n"
                   "Use exactly the required SHARED FIXTURE, declare no other fields or "
                   "lifecycle methods, and keep every @Test method name unique.")
        return {
            "merge_error": error,
            "merge_failures": failures,
            "ep_feedback": request, "ep_approved": False, "ep_rejections": 0,
            "bv_feedback": request, "bv_approved": False, "bv_rejections": 0,
            "change_log": [{
                "time": datetime.now().isoformat(timespec="seconds"),
                "phase": state.get("phase"),
                "node": "merge_tests",
                "action": "merge_failed",
                "attempt": failures,
                "error": error,
            }],
        }
    merged = merged_file.read_text(encoding="utf-8")
    ep_count = state["ep_tests"].count("@Test")
    bv_count = state["bv_tests"].count("@Test")
    merged_count = merged.count("@Test")
    log.info("Merged %d EP + %d BVA tests into %d tests (%d duplicates removed).",
             ep_count, bv_count, merged_count, ep_count + bv_count - merged_count)

    return {
        "merged_tests": merged,
        "merge_error": "",
        "change_log": [{
            "time": datetime.now().isoformat(timespec="seconds"),
            "phase": state.get("phase"),
            "node": "merge_tests",
            "action": "merged_tests",
            "ep_tests": ep_count,
            "bv_tests": bv_count,
            "merged_tests": merged_count,
            "duplicates_removed": ep_count + bv_count - merged_count,
            "file": str(merged_file),
        }],
    }


# ---- Human review of the merged tests (human in the loop, assignment step 4) ----
def review_tests(state: AgentState) -> dict:
    """Pause the graph and ask a person to approve the merged tests or request changes."""
    count = state.get("human_review_count", 0) + 1
    decision = interrupt({
        "node": "review_tests",
        "review_number": count,
        "test_count": state["merged_tests"].count("@Test"),
        "file": str(OUTPUT_DIR / f"{state['class_name']}MergedTest.java"),
        "prior_feedback": state.get("human_feedback", ""),
    })
    if not isinstance(decision, dict) or not isinstance(decision.get("approved"), bool):
        raise ValueError("Resume review_tests with {'approved': bool, 'feedback': str}")

    approved = decision["approved"]
    feedback = str(decision.get("feedback", "")).strip()
    rejections = state.get("human_rejections", 0) + (0 if approved else 1)
    log.info("[HUMAN] Approved: %s | review #%d | change requests: %d/%d",
             approved, count, rejections, MAX_HUMAN_REJECTIONS)
    if feedback:
        log.info("[HUMAN] Feedback: %s", feedback)

    update = {
        "human_approved": approved,
        "human_feedback": "" if approved else feedback,
        "human_review_count": count,
        "human_rejections": rejections,
        "change_log": [{
            "time": datetime.now().isoformat(timespec="seconds"),
            "phase": state.get("phase"),
            "node": "review_tests",
            "action": ("auto_approved_no_human" if decision.get("auto")
                       else "human_approved" if approved else "human_requested_changes"),
            "review_number": count,
            "feedback": feedback,
        }],
    }
    if not approved:
        # Send the request to both generators, the same way review_failures does.
        request = ("A HUMAN REVIEWER requested these changes to the merged tests. "
                   f"Apply every change that concerns YOUR tests:\n{feedback}")
        update.update({
            "ep_feedback": request, "ep_approved": False, "ep_rejections": 0,
            "bv_feedback": request, "bv_approved": False, "bv_rejections": 0,
        })
    return update


@traceable(name="Nova review test failures")
def review_failures(state: AgentState) -> dict:
    """Tests failed when run: Nova explains why, and both agents get the feedback."""
    rounds = state.get("test_fix_rounds", 0) + 1
    log.warning("Tests failed. Nova reviewing the failures (fix round %d/%d)...",
                rounds, MAX_TEST_FIX_ROUNDS)

    report = state.get("test_report") or {}
    lines = [f"{report.get('passed', 0)}/{report.get('total', 0)} passed, "
             f"{report.get('failed', 0)} failed, {report.get('errors', 0)} errors"]
    for f in report.get("failures", []):
        lines.append(f"FAIL {f.get('test')}: {str(f.get('message', ''))[:500]}")
    test_results = "\n".join(lines)

    response = (failure_prompt | review_model).invoke({
        "source_code": state["source_code"],
        "merged_tests": state["merged_tests"],
        "test_results": test_results,
    })
    content = response.content
    text = content if isinstance(content, str) else "".join(
        b.get("text", "") for b in content if isinstance(b, dict))
    feedback = text.strip() or f"Fix the failing tests:\n{test_results}"
    feedback = f"These tests FAILED when run. Fix any of YOUR tests listed here:\n{feedback}"
    log.info("Failure feedback: %s", feedback)

    return {
        "test_fix_rounds": rounds,
        "ep_feedback": feedback, "ep_approved": False, "ep_rejections": 0,
        "bv_feedback": feedback, "bv_approved": False, "bv_rejections": 0,
        "change_log": [{
            "time": datetime.now().isoformat(timespec="seconds"),
            "phase": state.get("phase"),
            "node": "review_failures",
            "action": "test_run_failed",
            "fix_round": rounds,
            "test_results": test_results,
            "fix_instructions": feedback,
        }],
    }


# ---- Refactored phase: orchestration around Emily's nodes (Ryan) ----
def run_refactor_agent(state: AgentState) -> dict:
    """Call Emily's refactor_agent; an unusable model reply is retried instead of stopping the run."""
    log.info("[REFACTOR] Claude %s the State-pattern refactoring...",
             "revising" if state.get("refactored_files") else "generating")
    try:
        result = refactor_agent(state)
    except ValueError as exc:
        errors = state.get("refactor_errors", 0) + 1
        log.warning("[REFACTOR] Unusable reply (%d/%d): %s", errors, MAX_REFACTOR_ERRORS, exc)
        return {
            "refactor_error": str(exc),
            "refactor_errors": errors,
            "refactor_feedback": (f"Your previous reply was rejected: {exc}\n"
                                  "Return ONE complete, valid JSON object that follows every requirement."),
            "change_log": [{
                "time": datetime.now().isoformat(timespec="seconds"),
                "phase": "refactored",
                "node": "refactor_agent",
                "action": "refactor_reply_rejected",
                "attempt": errors,
                "error": str(exc),
            }],
        }
    log.info("[REFACTOR] Wrote %d source file(s) to java-refactored/.", len(result["refactored_files"]))
    return {**result, "refactor_error": "", "coverage_scope": REFACTORED_COVERAGE_SCOPE}


def refactor_failures(state: AgentState) -> dict:
    """Refactored tests failed: send the results back to the refactor agent (assignment step 10)."""
    rounds = state.get("refactor_fix_rounds", 0) + 1
    report = state.get("test_report") or {}
    lines = [f"{report.get('passed', 0)}/{report.get('total', 0)} passed, "
             f"{report.get('failed', 0)} failed, {report.get('errors', 0)} errors"]
    for f in report.get("failures", []):
        lines.append(f"FAIL {f.get('test')}: {str(f.get('message', ''))[:500]}")
    if report.get("build_output_tail"):
        lines.append("Build output:\n" + report["build_output_tail"][-2000:])
    test_results = "\n".join(lines)
    log.warning("[REFACTOR] Refactored tests failed (fix round %d/%d).", rounds, MAX_REFACTOR_FIX_ROUNDS)
    return {
        "refactor_fix_rounds": rounds,
        "refactor_feedback": ("The refactored code and adapted tests were run and FAILED. Fix the "
                              "refactored code, or adapt a test only where the new design requires it. "
                              f"Do not weaken any assertion.\n{test_results}"),
        "change_log": [{
            "time": datetime.now().isoformat(timespec="seconds"),
            "phase": "refactored",
            "node": "refactor_failures",
            "action": "refactored_test_run_failed",
            "fix_round": rounds,
            "test_results": test_results,
        }],
    }


# ------------------------------------------------------------
# Node 09: Generate missing-branch tests
# Placeholder for Sarthak's implementation
# ------------------------------------------------------------
def generate_gap_tests(state: AgentState) -> dict:
    # TODO: Implement generation of tests for missed branches, then review, run and recheck coverage
    log.warning("Coverage gap found: generate_gap_tests is not implemented yet.")
    return {"workflow_status": "awaiting_gap_tests"}


def escalate_review(state: AgentState) -> dict:
    if state.get("refactor_status") == "refactor_review_exhausted":
        log.error("Stopped: the refactoring was rejected the maximum number of times.")
        status = "refactor_review_exhausted"
    elif state.get("refactor_error"):
        log.error("Stopped: the refactor agent did not return usable output.")
        status = "refactor_generation_failed"
    elif state.get("refactor_fix_rounds", 0) > MAX_REFACTOR_FIX_ROUNDS:
        log.error("Stopped: refactored tests still fail after the maximum fix rounds.")
        status = "refactor_fix_exhausted"
    elif state.get("merge_error") and state.get("merge_failures", 0) > MAX_MERGE_FAILURES:
        log.error("Stopped: the EP and BVA tests could not be merged.")
        status = "merge_failed"
    elif state.get("test_fix_rounds", 0) > MAX_TEST_FIX_ROUNDS:
        log.error("Stopped: tests still fail after the maximum fix rounds.")
        status = "test_fix_exhausted"
    else:
        log.error("Stopped: tests were rejected the maximum number of times.")
        status = "review_exhausted"
    return {
        "workflow_status": status,
        "change_log": [{
            "time": datetime.now().isoformat(timespec="seconds"),
            "phase": state.get("phase"),
            "node": "escalate_review",
            "action": status,
        }],
    }


# ---- Final node: save the change log with the final test and coverage results ----
def save_change_log(state: AgentState) -> dict:
    phase = state.get("phase", "original")
    log_file = OUTPUT_DIR / f"change_log_{phase}.json"
    log_file.write_text(json.dumps({
        "class_name": state.get("class_name"),
        "phase": phase,
        "workflow_status": state.get("workflow_status", "finished"),
        "ep_review_count": state.get("ep_review_count", 0),
        "bv_review_count": state.get("bv_review_count", 0),
        "test_fix_rounds": state.get("test_fix_rounds", 0),
        "final_test_report": state.get("test_report"),
        "final_coverage": state.get("coverage"),
        "changes": state.get("change_log", []),
    }, indent=2, default=str), encoding="utf-8")
    log.info("Change log saved: %s (%d entries)", log_file, len(state.get("change_log", [])))
    return {"saved_artifacts": {**(state.get("saved_artifacts") or {}),
                                 f"change_log_{phase}": str(log_file)}}


# ===========================================================================
# 5. Routers
# ===========================================================================
# R1a: EP review decision
def route_ep_review(state: AgentState) -> str:
    if state.get("ep_approved"):
        return "approved"
    if state.get("ep_rejections", 0) >= MAX_REVIEW_REJECTIONS:
        return "max_attempts"
    return "regenerate"


# R1b: BVA review decision
def route_bv_review(state: AgentState) -> str:
    if state.get("bv_approved"):
        return "approved"
    if state.get("bv_rejections", 0) >= MAX_REVIEW_REJECTIONS:
        return "max_attempts"
    return "regenerate"


# After merge_tests: merged -> human review, failed -> both agents fix their classes
def route_merge(state: AgentState):
    if not state.get("merge_error"):
        return "merged"
    if state.get("merge_failures", 0) > MAX_MERGE_FAILURES:
        return "max_attempts"
    return ["ep_agent", "bva_agent"]


# R1 (human): approved -> run the tests, changes requested -> both agents revise
def route_test_review(state: AgentState):
    if state.get("human_approved"):
        return "approved"
    if state.get("human_rejections", 0) >= MAX_HUMAN_REJECTIONS:
        return "max_attempts"
    return ["ep_agent", "bva_agent"]


def route_after_failures(state: AgentState):
    """After failure review: both agents regenerate, unless out of fix rounds."""
    if state.get("test_fix_rounds", 0) > MAX_TEST_FIX_ROUNDS:
        return "max_attempts"
    return ["ep_agent", "bva_agent"]


# R2 by phase: a failed refactored run goes to the refactor agent, not the EP/BVA agents
def route_tests_by_phase(state: AgentState) -> str:
    result = route_test_results(state)
    if result == "failed" and state.get("phase") == "refactored":
        return "refactor_failed"
    return result


def route_refactor_failures(state: AgentState) -> str:
    if state.get("refactor_fix_rounds", 0) > MAX_REFACTOR_FIX_ROUNDS:
        return "max_attempts"
    return "revise"


# After the refactor agent: usable reply -> human review, unusable -> retry
def route_refactor_agent(state: AgentState) -> str:
    if not state.get("refactor_error"):
        return "review"
    if state.get("refactor_errors", 0) > MAX_REFACTOR_ERRORS:
        return "max_attempts"
    return "retry"


# ------------------------------------------------------------
# Conditional Router R4: human review of the refactoring
# Owner: Ryan
# ------------------------------------------------------------
def route_refactor_review(state: AgentState) -> str:
    status = state.get("refactor_status")
    if status == "refactor_approved":
        return "approved"
    if status == "refactor_review_exhausted":
        return "max_attempts"
    return "revise"


# After the change log is saved: the original phase continues into refactoring
def route_after_save(state: AgentState) -> str:
    if state.get("workflow_status") == "original_saved":
        return "refactor"
    return "end"


# ------------------------------------------------------------
# Conditional Router R3: Branch coverage routing
# Owner: Ryan
# ------------------------------------------------------------
def route_coverage(state: AgentState) -> str:
    coverage = state.get("coverage") or {}
    report = state.get("test_report") or {}
    branch = coverage.get("branch") or {}
    phase = state.get("phase")

    # Verify results belong to this phase
    if (
        report.get("all_passed") is not True
        or report.get("phase") != phase
        or coverage.get("report_found") is not True
        or coverage.get("phase") != phase
        or phase not in ("original", "refactored")
        or not isinstance(branch.get("total"), int)
        or not isinstance(branch.get("covered"), int)
        or not isinstance(branch.get("missed"), int)
        or branch["total"] <= 0
        or branch["covered"] < 0
        or branch["missed"] < 0
        or branch["covered"] + branch["missed"] != branch["total"]
    ):
        raise ValueError("Invalid or incomplete coverage results")

    if branch["missed"] > 0:          # below 100% branch coverage
        return "gap"
    if coverage.get("fully_covered") is not True:
        raise ValueError("Inconsistent coverage result")
    if phase == "original":
        return "refactor"
    return "complete"


# ===========================================================================
# 6. Graph
# ===========================================================================
def build_graph():
    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node("load_source", load_source)
    graph.add_node("ep_agent", generate_ep_tests)
    graph.add_node("bva_agent", generate_bv_tests)
    graph.add_node("review_ep", review_ep_tests)
    graph.add_node("review_bva", review_bv_tests)
    graph.add_node("ep_done", ep_done)
    graph.add_node("bva_done", bva_done)
    graph.add_node("merge_tests", merge_tests)
    graph.add_node("review_tests", review_tests)
    graph.add_node("review_failures", review_failures)
    graph.add_node("escalate_review", escalate_review)
    # >>> PERSON 3 (Joseph) BEGIN: nodes
    graph.add_node("run_tests", run_tests)
    graph.add_node("check_coverage", check_coverage)
    graph.add_node("save_results", save_results)
    # <<< PERSON 3 (Joseph) END: nodes
    graph.add_node("generate_gap_tests", generate_gap_tests)
    graph.add_node("save_change_log", save_change_log)
    graph.add_node("refactor_agent", run_refactor_agent)
    graph.add_node("review_refactor", review_refactor)
    graph.add_node("refactor_failures", refactor_failures)

    # Generate in parallel
    graph.add_edge(START, "load_source")
    graph.add_edge("load_source", "ep_agent")
    graph.add_edge("load_source", "bva_agent")

    # Each branch is reviewed on its own (R1 per branch)
    graph.add_edge("ep_agent", "review_ep")
    graph.add_edge("bva_agent", "review_bva")
    graph.add_conditional_edges("review_ep", route_ep_review, {
        "approved": "ep_done", "regenerate": "ep_agent", "max_attempts": "escalate_review",
    })
    graph.add_conditional_edges("review_bva", route_bv_review, {
        "approved": "bva_done", "regenerate": "bva_agent", "max_attempts": "escalate_review",
    })

    # Merge only after BOTH branches are approved
    graph.add_edge(["ep_done", "bva_done"], "merge_tests")
    # A failed merge goes back to both agents instead of stopping the run
    graph.add_conditional_edges("merge_tests", route_merge, {
        "merged": "review_tests", "ep_agent": "ep_agent", "bva_agent": "bva_agent",
        "max_attempts": "escalate_review",
    })

    # R1 (human): a person approves the merged tests before they run
    graph.add_conditional_edges("review_tests", route_test_review, {
        "approved": "run_tests", "ep_agent": "ep_agent", "bva_agent": "bva_agent",
        "max_attempts": "escalate_review",
    })

    # >>> PERSON 3 (Joseph) BEGIN: edges
    # R2: passed -> coverage, failed -> Nova reviews the failures
    graph.add_conditional_edges("run_tests", route_tests_by_phase, {
        "passed": "check_coverage", "failed": "review_failures",
        "refactor_failed": "refactor_failures",
    })
    # <<< PERSON 3 (Joseph) END: edges

    graph.add_conditional_edges("review_failures", route_after_failures, {
        "ep_agent": "ep_agent", "bva_agent": "bva_agent", "max_attempts": "escalate_review",
    })

    # R3: coverage and phase
    graph.add_conditional_edges("check_coverage", route_coverage, {
        "gap": "generate_gap_tests",
        "refactor": "save_results",   # save the original evidence, then refactor (route_after_save)
        "complete": "save_results",
    })

    # Every ending writes the change log first
    graph.add_edge("generate_gap_tests", "save_change_log")
    graph.add_edge("save_results", "save_change_log")
    graph.add_edge("escalate_review", "save_change_log")
    graph.add_conditional_edges("save_change_log", route_after_save, {
        "refactor": "refactor_agent", "end": END,
    })

    # Refactored phase: generate -> human review (R4) -> run the adapted tests
    graph.add_conditional_edges("refactor_agent", route_refactor_agent, {
        "review": "review_refactor", "retry": "refactor_agent", "max_attempts": "escalate_review",
    })
    graph.add_conditional_edges("review_refactor", route_refactor_review, {
        "approved": "run_tests", "revise": "refactor_agent", "max_attempts": "escalate_review",
    })
    graph.add_conditional_edges("refactor_failures", route_refactor_failures, {
        "revise": "refactor_agent", "max_attempts": "escalate_review",
    })

    return graph.compile(checkpointer=MemorySaver())


# ===========================================================================
# 7. Run
# ===========================================================================
def ask_human(payload: dict) -> dict:
    """Show a paused human review on the terminal; return {'approved': bool, 'feedback': str}."""
    print(f"\n=== HUMAN REVIEW REQUIRED: {payload.get('node')} "
          f"(review #{payload.get('review_number')}) ===")
    if payload.get("file"):
        print(f"Open and read: {payload['file']} ({payload.get('test_count')} tests)")
    for path in (payload.get("files") or {}):
        print(f"Open and read: java-refactored/{path}")
    if payload.get("adapted_tests"):
        print("Open and read the adapted tests in: java-refactored/src/test/java/cse4392/")
    if payload.get("explanation"):
        print(f"Refactoring notes: {payload['explanation']}")
    for item in payload.get("review_checklist") or []:
        print(f"  [ ] {item}")
    if payload.get("prior_feedback"):
        print(f"Your previous feedback: {payload['prior_feedback']}")
    while True:
        answer = input("Approve? [y = approve / n = request changes]: ").strip().lower()
        if answer in ("y", "yes"):
            return {"approved": True, "feedback": ""}
        if answer in ("n", "no"):
            feedback = input("What must change? ").strip()
            if feedback:
                return {"approved": False, "feedback": feedback}
            print("Feedback is required to request changes.")
        else:
            print("Please type y or n.")


if __name__ == "__main__":
    app = build_graph()
    config = {"configurable": {"thread_id": "assignment3-001"}, "recursion_limit": 100}

    result = app.invoke(
        {
            "source_path": str(BASE_DIR / "app" / "SeasonSwitch.java"),
            "class_name": "SeasonSwitch",
            "package_name": "cse4392",
            "phase": "original",
            "change_log": [],
             # Measure branch coverage for the SeasonSwitch class only:
            # not its inner classes (AC, Heater, Room), and not main(), which is not tested.
            "coverage_scope": {
                "include_classes": ["SeasonSwitch"],
                "exclude_methods": ["SeasonSwitch.main"],
            },
        },
        config=config,
    )
    # Human in the loop: the graph pauses at interrupt(); ask on the terminal, then resume.
    while True:
        pending = [i for task in app.get_state(config).tasks for i in task.interrupts]
        if not pending:
            break
        if os.environ.get("AUTO_APPROVE") == "1":
            # Testing shortcut only. Final evidence runs must use the real human review.
            print(f"AUTO_APPROVE=1: skipping human review at {pending[0].value.get('node')}")
            answer = {"approved": True, "feedback": "", "auto": True}
        else:
            answer = ask_human(pending[0].value)
        result = app.invoke(Command(resume=answer), config=config)

    print("\n=== Workflow Completed ===")
    print("Status:", result.get("workflow_status", "finished"))
    print(f"EP reviews:  {result.get('ep_review_count', 0)} (approved: {result.get('ep_approved')})")
    print(f"BVA reviews: {result.get('bv_review_count', 0)} (approved: {result.get('bv_approved')})")
    print("Test fix rounds:", result.get("test_fix_rounds", 0))

    # >>> PERSON 3 (Joseph) BEGIN: results printout
    report = result.get("test_report")
    if report:
        print(f"Tests: {report['passed']}/{report['total']} passed, "
              f"{report['failed']} failed, {report['errors']} errors")
        for f in report.get("failures", []):
            print(f"  FAIL {f['test']}: {f['message'][:160]}")
    cov = result.get("coverage")
    if cov:
        b = cov["branch"]
        print(f"Branch coverage: {b['covered']}/{b['total']} = {b['percent']}% "
              f"(fully covered: {cov['fully_covered']})")
    if result.get("saved_artifacts"):
        print(f"Evidence saved: {result['saved_artifacts']}")
    # <<< PERSON 3 (Joseph) END: results printout
