
#test
import os

from langchain_aws import ChatBedrockConverse
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# Define the routing prompt
router_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are the request router for the UTA AI Advisor.

Classify the student's question into exactly one route.

course_information:
- Course descriptions and topics
- Course prerequisites and corequisites in general
- Course credit hours
- Academic catalog information and policies
- General degree requirements
Example: "What is CSE 3318 about?" / "What are the prerequisites for CSE 3320?"

student_record:
- The student's own transcript, grades, completed courses, or credits
- What the student still has left to finish their degree
Example: "What courses have I taken?" / "How many credits do I have left?"

course_eligibility:
- Whether THIS student can take a specific course, now or in a given term
Example: "Can I take CSE 3318 next spring?" / "Am I eligible for Operating Systems?"

degree_plan:
- Making or changing a semester-by-semester plan to graduate
- Changes to a plan: number of classes, summers, start term, electives, switching majors
Example: "Make me a degree plan" / "What about only 3 classes a semester?"

compare_plans:
- Comparing two of the student's degree plans
Example: "Compare my two plans" / "Which plan finishes sooner?"

unsupported:
- Registration actions, financial aid, housing, anything else
- Unrelated questions

The previous route in this conversation was: {previous_route}
Short follow-ups like "what about 3 classes?" or "and in the fall?" usually
continue the previous route.

Conversation history:
{history}

Use conversation history to understand follow-up questions.
For example, if the student previously asked about CSE 4308
and now asks "Can I take it?", classify as course_eligibility.

Return ONLY one of these exact values:
course_information
student_record
course_eligibility
degree_plan
compare_plans
unsupported

Do not answer the student's question.
Do not provide explanations."""
    ),
    ("human", "{question}")
])


# Initialize Google Gemma through Amazon Bedrock
router_llm = ChatBedrockConverse(
    model=os.getenv(
        "BEDROCK_MODEL_ID",
        "google.gemma-3-27b-it"
    ),
    region_name=os.getenv("AWS_REGION", "us-east-2"),
    temperature=0
)


# LangChain routing pipeline
router_chain = (
    router_prompt
    | router_llm
    | StrOutputParser()
)


VALID_ROUTES = (
    "course_information",
    "student_record",
    "course_eligibility",
    "degree_plan",
    "compare_plans",
    "unsupported"
)


# Classify the student's question
def route_question(
    question: str,
    previous_route: str | None = None,
    history: list[dict] | None = None  # NEW
) -> str:

    # NEW: Format previous conversation messages
    history = history or []

    history_text = "\n".join(
        f"{message.get('role', 'unknown')}: "
        f"{message.get('content', '')}"
        for message in history[-12:]
    )

    decision = router_chain.invoke({
        "question": question,
        "previous_route": previous_route or "none",
        "history": history_text  # NEW
    })

    route = decision.strip().lower().strip("`'\" .")

    if route in VALID_ROUTES:
        return route

    # Small models sometimes add words around the label; accept it if exactly one label appears.
    found = [r for r in VALID_ROUTES if r in route]

    if len(found) == 1:
        return found[0]

    raise ValueError(
        f"Invalid route returned by model: {route}"
    )
