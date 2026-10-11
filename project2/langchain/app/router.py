
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
- Course prerequisites and corequisites
- Course credit hours
- Academic catalog information
- General degree requirements

unsupported:
- Checking a specific student's eligibility
- Checking completed courses or transcripts
- Generating personalized degree plans
- Unrelated questions

Return ONLY one of these exact values:
course_information
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


# Classify the student's question
def route_question(question: str) -> str:

    decision = router_chain.invoke({
        "question": question
    })

    route = decision.strip().lower().strip("`'\" ")

    valid_routes = (
        "course_information",
        "unsupported"
    )

    if route not in valid_routes:
        raise ValueError(
            f"Invalid route returned by model: {route}"
        )

    return route
