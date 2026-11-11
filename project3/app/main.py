from pathlib import Path
from dotenv import load_dotenv
from langsmith import traceable
from typing import TypedDict
from langchain_core.prompts import ChatPromptTemplate
from langchain_aws import ChatBedrockConverse
from langgraph.graph import StateGraph, START, END
import re
from langgraph.types import interrupt
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
import subprocess
from pathlib import Path

# >>> PERSON 3 (Joseph) BEGIN: imports
# Maven/JUnit/JaCoCo execution, coverage and evidence nodes (app/testing_nodes.py)
try:
    from testing_nodes import run_tests, check_coverage, save_results, route_test_results
except ImportError:  # when run as `python -m app.main`
    from app.testing_nodes import run_tests, check_coverage, save_results, route_test_results
# <<< PERSON 3 (Joseph) END: imports

MAX_REVIEW_ATTEMPTS = 3 #Max attempts for review
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(Path(__file__).resolve().parent / ".env")

# ---------------------------------------------------------------------------
# Model config
# ---------------------------------------------------------------------------
# us.amazon.nova-2-lite-v1:0 is best for tool agent, expensive
# us.amazon.nova-lite-v1:0, older and cheaper
NOVA_MODEL = "us.amazon.nova-micro-v1:0" #support up to two tools, cheapest
GEMMA_MODEL = "google.gemma-3-27b-it"
QWEN_MODEL = "qwen.qwen3-coder-30b-a3b-v1:0" #Qwen3 Coder 30B A3B 
REGION = "us-east-1"
TEMPERATURE = 0
MAX_TOKENS = 8000

model = ChatBedrockConverse(
    model=QWEN_MODEL,
    region_name=REGION,
    temperature=TEMPERATURE,
    max_tokens=MAX_TOKENS,
    disable_streaming=False,
)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
class AgentState(TypedDict, total=False):
    source_path: str      # path to SeasonSwitch.java
    source_code: str
    class_name: str       # "SeasonSwitch"
    package_name: str     # "cse4392"
    ep_tests: str         # generated Equivalence Partition test class
    bv_tests: str         # generated Boundary Value test class
    merged_tests: str
    review_approved: bool
    review_feedback: str
    review_attempts: int
    workflow_status: str
    # >>> PERSON 3 (Joseph) BEGIN: state keys
    phase: str              # "original" | "refactored"
    test_class: str         # optional: run this test class instead of merged_tests
    test_report: dict       # written by run_tests (Surefire results)
    coverage: dict          # written by check_coverage (JaCoCo branch coverage)
    coverage_scope: dict    # optional override of the measured scope
    saved_artifacts: dict   # written by save_results: {"original": path, ...}
    # <<< PERSON 3 (Joseph) END: state keys


# ---------------------------------------------------------------------------
# template
# ---------------------------------------------------------------------------


template = ChatPromptTemplate.from_messages([
        ("system","""{system-message}\n
        Rules:
        - These are FUNCTIONAL (black-box) test cases: derive partitions and boundaries
        from the inputs and expected behavior of each public method, not from its
        internal statement structure.
        - Write JUnit 5 tests (org.junit.jupiter.api.*) in package {package_name};
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
        - Besides return values or state, assert observable side effects
        (devices on/off, timers running or stopped).
        - No duplicate tests: each test must use a different input or starting state.
        - Put a short comment above each test naming the partition or boundary it covers.
        - Only use methods, fields, and constructors that exist in the given code.
        - Return ONLY the raw Java file. No markdown, no ``` fences, no explanation.
        """),
        ("human","{human-message}")
    ])

chain = template | model

def clean_java(text: str) -> str:
    """Remove ``` fences in case the model adds them anyway."""
    return text.strip().removeprefix("```java").removeprefix("```").removesuffix("```").strip()



# ---------------------------------------------------------------------------
# Node 1: load source
# ---------------------------------------------------------------------------

def load_source(state: AgentState):
    source_code = Path(state["source_path"]).read_text()

    return {"source_code": source_code}


# ---------------------------------------------------------------------------
# Node 2: Equivalence Partition tests
# ---------------------------------------------------------------------------
@traceable(name="Generate ep test", run_type="tool")
def generate_ep_tests(state: AgentState) -> dict:
    feedback = state.get("review_feedback", "")
    previous_tests = state.get("ep_tests", "")
    class_name = state.get("class_name", "SeasonSwitch")
    package_name = state.get("package_name", "cse4392")


    ep_prompt = f"""You are a software testing expert.
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
        """
    
    print("Generating functional test cases using Equivalence Partitioning.......\n")
    response = chain.invoke({
        "system-message": ep_prompt,
        "package_name": package_name,
        "class_name": class_name,
        "human-message": f"""
            Generate or revise {class_name}EPTest.

            Java source:
            {state['source_code']}

            Previous EP tests:
            {previous_tests}

            Reviewer feedback:
            {feedback}

            If feedback is provided, revise the previous tests
            to address it while preserving valid test coverage.

            Otherwise, generate new equivalence partition tests.
            """
    })
    return {"ep_tests": clean_java(response.content)}


# ---------------------------------------------------------------------------
# Node 3: Boundary Value tests
# ---------------------------------------------------------------------------
@traceable(name="Generate bv test", run_type="tool")
def generate_bv_tests(state: AgentState) -> dict:
    feedback = state.get("review_feedback", "")
    previous_tests = state.get("bv_tests", "")
    class_name = state.get("class_name", "SeasonSwitch")
    package_name = state.get("package_name", "cse4392")


    bv_prompt = f"""You are a software testing expert.
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
        """

    print("Generating functional test cases using Boundary Value Analysis.......\n")
    response = chain.invoke({
        "system-message": bv_prompt,
        "package_name": package_name,
        "class_name": class_name,
        "human-message": f"""
            Generate or revise {class_name}BVTest.

            Java source:
            {state['source_code']}

            Previous BVA tests:
            {previous_tests}

            Reviewer feedback:
            {feedback}

            If feedback is provided, revise the previous tests
            to address it while preserving valid test coverage.

            Otherwise, generate new boundary value tests.
            """
    })
    return {"bv_tests": clean_java(response.content)}


# ---------------------------------------------------------------------------
# Node 4: merge_tests
# ---------------------------------------------------------------------------



MERGER_JAR = (
    BASE_DIR / "junit-merger" / "target"
    / "junit-merger-1.0.0.jar"
)

@traceable(name="JavaParser JUnit Merge", run_type="tool")
def merge_tests(state: AgentState) -> dict:
    class_name = state["class_name"]

    output_dir = BASE_DIR / "generated_tests"
    output_dir.mkdir(parents=True, exist_ok=True)

    ep_file = output_dir / f"{class_name}EPTest.java"
    bv_file = output_dir / f"{class_name}BVTest.java"
    merged_file = output_dir / f"{class_name}MergedTest.java"

    ep_file.write_text(state["ep_tests"], encoding="utf-8")
    bv_file.write_text(state["bv_tests"], encoding="utf-8")

    print("Merging Equivalence Partitioning (EP) and Boundary Value Analysis (BVA) test cases.......\n")
    subprocess.run(
        [
            "java",
            "-jar",
            str(MERGER_JAR),
            str(ep_file),
            str(bv_file),
            str(merged_file),
            f"{class_name}MergedTest",
        ],
        check=True,
    )

    return {
        "merged_tests": merged_file.read_text(encoding="utf-8")
    }


# ---------------------------------------------------------------------------
# Node 5: Human Review of Generated Tests
# ---------------------------------------------------------------------------
def review_tests(state: AgentState) -> dict:
    decision = interrupt({
        "message": "Review the generated JUnit test cases.",
        "tests": state["merged_tests"],
        "instructions": "Approve or reject with feedback."
    })

    attempts = state.get("review_attempts", 0)

    return {
        "review_approved": decision["approved"],
        "review_feedback": decision.get("feedback", ""),
        "review_attempts": attempts + (0 if decision["approved"] else 1)
    }



# ---------------------------------------------------------------------------
# Conditional router R1
# ---------------------------------------------------------------------------
def route_test_review(state: AgentState) -> str:

    if state["review_approved"]:
        return "approved"

    if state.get("review_attempts", 0) >= MAX_REVIEW_ATTEMPTS:
        return "max_attempts"

    return "regenerate"

# >>> PERSON 3 (Joseph) BEGIN: repair_agent placeholder (replace with Sarthak's node)
def repair_agent_stub(state: AgentState) -> dict:
    report = state.get("test_report", {})
    print(f"{report.get('failed', 0)} failed / {report.get('errors', 0)} errors: "
          "repair_agent is not implemented yet.")
    return {
        "workflow_status": "awaiting_repair_agent"
    }
# <<< PERSON 3 (Joseph) END: repair_agent placeholder


# Stop safely when human review reaches the retry limit
def escalate_review(state: AgentState) -> dict:
    print("Review failed: maximum rejection attempts reached.")
    return {
        "workflow_status": "review_exhausted"
    }

# ---------------------------------------------------------------------------
# Build Graph: both generators run in parallel from START
# ---------------------------------------------------------------------------
def build_graph():
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("load_source", load_source)
    graph.add_node("ep_agent", generate_ep_tests)
    graph.add_node("bva_agent", generate_bv_tests)
    graph.add_node("merge_tests", merge_tests)
    graph.add_node("review_tests", review_tests)

    # >>> PERSON 3 (Joseph) BEGIN: nodes
    graph.add_node("run_tests", run_tests)
    graph.add_node("check_coverage", check_coverage)
    graph.add_node("save_results", save_results)
    graph.add_node("repair_agent", repair_agent_stub)   # placeholder for Sarthak
    # <<< PERSON 3 (Joseph) END: nodes

    # Temporary nodes
    graph.add_node("escalate_review", escalate_review)

    # Start workflow
    graph.add_edge(START, "load_source")

    # Run test generators in parallel
    graph.add_edge("load_source", "ep_agent")
    graph.add_edge("load_source", "bva_agent")

    # Wait for both generators before merging
    graph.add_edge(
        ["ep_agent", "bva_agent"],
        "merge_tests"
    )

    # Human review
    graph.add_edge("merge_tests", "review_tests")

    # Route review decision
    graph.add_conditional_edges(
        "review_tests",
        route_test_review,
        {
            "approved": "run_tests",
            "regenerate": "load_source",
            "max_attempts": "escalate_review"
        }
    )

    # >>> PERSON 3 (Joseph) BEGIN: edges
    # R2: passed -> coverage, failed -> repair
    graph.add_conditional_edges(
        "run_tests",
        route_test_results,
        {
            "passed": "check_coverage",
            "failed": "repair_agent"
        }
    )

    # Until Ryan's R3 coverage router exists: always save the current evidence
    graph.add_edge("check_coverage", "save_results")

    # Temporary endpoints until R3 / repair loop exist
    graph.add_edge("save_results", END)
    graph.add_edge("repair_agent", END)
    # <<< PERSON 3 (Joseph) END: edges

    # Temporary endpoints
    graph.add_edge("escalate_review", END)

    return graph.compile(checkpointer=MemorySaver())


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = build_graph()

    config = {
    "configurable": {
        "thread_id": "assignment3-001"
    }
    }

    result = app.invoke({
        "source_path": str(BASE_DIR / "app" / "SeasonSwitch.java"),
        "class_name": "SeasonSwitch",
        "package_name": "cse4392",
        # >>> PERSON 3 (Joseph) BEGIN: initial phase
        "phase": "original",
        # <<< PERSON 3 (Joseph) END: initial phase
    },config=config)



    while "__interrupt__" in result:
        review = result["__interrupt__"][0].value

        print("\n=== Generated Tests for Review ===")
        print(
            f"\nReview file: "
                f"{BASE_DIR / 'generated_tests' / 'SeasonSwitchMergedTest.java'}"
        )
        print(f"Number of generated tests: {review['tests'].count('@Test')}")

        while True:
            answer = input("\nApprove tests? (yes/no): ").strip().lower()

            if answer in ("yes", "y", "no", "n"):
                break

            print("Please enter yes or no. Blank answers are not accepted.")

        approved = answer in ("yes", "y")

        feedback = ""
        if not approved:
            feedback = input("Enter your feedback: ").strip()

        result = app.invoke(
            Command(resume={
                "approved": approved,
                "feedback": feedback
            }),
            config=config
        )

    status = result.get("workflow_status", "unknown")
    print(f"\nWorkflow status: {status}")

    # >>> PERSON 3 (Joseph) BEGIN: results printout
    report = result.get("test_report")
    if report:
        print(f"Tests: {report['passed']}/{report['total']} passed, "
              f"{report['failed']} failed, {report['errors']} errors")
        for f in report["failures"]:
            print(f"  FAIL {f['test']}: {f['message'][:160]}")
    cov = result.get("coverage")
    if cov:
        b = cov["branch"]
        print(f"Branch coverage: {b['covered']}/{b['total']} = {b['percent']}% "
              f"(fully covered: {cov['fully_covered']})")
    if result.get("saved_artifacts"):
        print(f"Evidence saved: {result['saved_artifacts']}")
    # <<< PERSON 3 (Joseph) END: results printout

    if status == "review_exhausted":
           raise SystemExit(
               "Stopped: tests were not approved after 3 attempts."
           )

    out_dir = Path("generated_tests")
    out_dir.mkdir(exist_ok=True)
    (out_dir / "SeasonSwitchEPTest.java").write_text(result["ep_tests"])
    (out_dir / "SeasonSwitchBVTest.java").write_text(result["bv_tests"])
    (out_dir / "SeasonSwitchMergedTest.java").write_text(
    result["merged_tests"]
)

    print("=== Equivalence Partition tests ===\n", result["ep_tests"])
    print("\n=== Boundary Value tests ===\n", result["bv_tests"])
