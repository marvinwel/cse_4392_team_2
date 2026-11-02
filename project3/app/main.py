from pathlib import Path
from typing import TypedDict

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END


# ---------------------------------------------------------------------------
# Model config
# ---------------------------------------------------------------------------
NOVA_MODEL = "us.amazon.nova-micro-v1:0"
GEMMA_MODEL = "google.gemma-3-27b-it"
REGION = "us-east-1"
TEMPERATURE = 0
MAX_TOKENS = 4096

model = ChatBedrockConverse(
    model=GEMMA_MODEL,
    region_name=REGION,
    temperature=TEMPERATURE,
    max_tokens=MAX_TOKENS,
    disable_streaming=False,
)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
class TestGenState(TypedDict, total=False):
    source_path: str      # path to SeasonSwitch.java
    class_name: str       # "SeasonSwitch"
    package_name: str     # "cse4392"
    ep_tests: str         # generated Equivalence Partition test class
    bv_tests: str         # generated Boundary Value test class


# ---------------------------------------------------------------------------
# Shared rules (used by both nodes)
# ---------------------------------------------------------------------------
COMMON_RULES = """
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
"""


def clean_java(text: str) -> str:
    """Remove ``` fences in case the model adds them anyway."""
    return text.strip().removeprefix("```java").removeprefix("```").removesuffix("```").strip()


# ---------------------------------------------------------------------------
# Node 1: Equivalence Partition tests
# ---------------------------------------------------------------------------
def generate_ep_tests(state: TestGenState) -> dict:
    class_name = state.get("class_name", "SeasonSwitch")
    package_name = state.get("package_name", "cse4392")
    source_code = Path(state["source_path"]).read_text()

    system_prompt = f"""You are a software testing expert.
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
        """ + COMMON_RULES.format(class_name=class_name, package_name=package_name)

    response = model.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Generate the test class {class_name}EPTest for this code:\n\n{source_code}"),
    ])
    return {"ep_tests": clean_java(response.content)}


# ---------------------------------------------------------------------------
# Node 2: Boundary Value tests
# ---------------------------------------------------------------------------
def generate_bv_tests(state: TestGenState) -> dict:
    class_name = state.get("class_name", "SeasonSwitch")
    package_name = state.get("package_name", "cse4392")
    source_code = Path(state["source_path"]).read_text()

    system_prompt = f"""You are a software testing expert.
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
        """ + COMMON_RULES.format(class_name=class_name, package_name=package_name)

    response = model.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Generate the test class {class_name}BVTest for this code:\n\n{source_code}"),
    ])
    return {"bv_tests": clean_java(response.content)}


# ---------------------------------------------------------------------------
# Build Graph: both generators run in parallel from START
# ---------------------------------------------------------------------------
def build_graph():
    graph = StateGraph(TestGenState)
    graph.add_node("generate_ep_tests", generate_ep_tests)
    graph.add_node("generate_bv_tests", generate_bv_tests)

    graph.add_edge(START, "generate_ep_tests")
    graph.add_edge(START, "generate_bv_tests")
    graph.add_edge("generate_ep_tests", END)
    graph.add_edge("generate_bv_tests", END)
    return graph.compile()


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = build_graph()
    result = app.invoke({
        "source_path": "SeasonSwitch.java",
        "class_name": "SeasonSwitch",
        "package_name": "cse4392",
    })

    out_dir = Path("generated_tests")
    out_dir.mkdir(exist_ok=True)
    (out_dir / "SeasonSwitchEPTest.java").write_text(result["ep_tests"])
    (out_dir / "SeasonSwitchBVTest.java").write_text(result["bv_tests"])

    print("=== Equivalence Partition tests ===\n", result["ep_tests"])
    print("\n=== Boundary Value tests ===\n", result["bv_tests"])