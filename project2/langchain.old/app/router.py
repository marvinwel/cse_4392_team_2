
import os

from langchain_aws import ChatBedrockConverse
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


router_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are the request router for the UTA AI Advisor.

Classify the CURRENT student's question into exactly one route.

Conversation history:
{history}

Use conversation history to understand follow-up questions.
For example, if the student previously asked about CSE 4308
and now asks "Can I take it?", classify as course_eligibility.

Available routes:

course_information:
- Course descriptions and topics
- Course prerequisites and corequisites
- Course credit hours
- Academic catalog information
- General degree requirements

student_record:
- Student's completed courses
- Student's transcript
- Student's academic records

course_eligibility:
- Checking if a student can take a course
- Checking whether prerequisites are satisfied
- Questions such as "Can I take it?"
- Questions such as "Am I eligible?"

degree_plan:
- Generate a personalized degree plan
- Check degree progress
- Identify remaining degree requirements

unsupported:
- Questions unrelated to academic advising
- Requests outside available advisor capabilities

Examples:
"What is CSE 4308 about?" -> course_information
"Can I take it?" -> course_eligibility
"Do I meet its prerequisites?" -> course_eligibility
"What classes have I completed?" -> student_record
"Generate my degree plan" -> degree_plan

Return ONLY one of these exact values:
course_information
student_record
course_eligibility
degree_plan
unsupported

Do not answer the student's question.
Do not provide explanations."""
    ),
    ("human", "{question}")
])


router_llm = ChatBedrockConverse(
    model=os.getenv(
        "BEDROCK_MODEL_ID",
        "google.gemma-3-27b-it"
    ),
    region_name=os.getenv("AWS_REGION", "us-east-2"),
    temperature=0
)


router_chain = (
    router_prompt
    | router_llm
    | StrOutputParser()
)


def route_question(
    question: str,
    history: list[dict] | None = None
) -> str:

    history = history or []

    history_text = "\n".join(
        f"{message.get('role', 'unknown')}: "
        f"{message.get('content', '')}"
        for message in history[-12:]
    )

    decision = router_chain.invoke({
        "question": question,
        "history": history_text
    })

    route = decision.strip().lower().strip("`'\" ")

    valid_routes = (
        "course_information",
        "student_record",
        "course_eligibility",
        "degree_plan",
        "unsupported"
    )

    if route not in valid_routes:
        raise ValueError(
            f"Invalid route returned by model: {route}"
        )

    return route
