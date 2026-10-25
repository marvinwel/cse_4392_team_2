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
- The student's own profile: name, student ID, major, classification, catalog year
- The student's own transcript, grades, GPA, completed courses, or credits
- What the student still has left to finish their degree
Example: "Who am I?" / "What's my major?" / "What courses have I taken?" / "How many credits do I have left?"

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

small_talk:
- Thanks, acknowledgements, greetings or goodbyes with NO question or request in them
Example: "Thank you" / "ok" / "Thanks, that helps" / "Hi" / "Bye"
- If the message also asks something ("ok, what about 3 classes?"), use that request's route instead

unsupported:
- Registration actions, financial aid, housing, anything else
- Unrelated questions
- NOT questions about the student's own profile or record (those are student_record)

Recent conversation:
{history}

Use the conversation history to understand follow-up questions.

Examples:
- "Make me a degree plan" followed by "What about 3 classes?"
  → degree_plan
- "What is CSE 3318?" followed by "What are its prerequisites?"
  → course_information
- "What is CSE 3318?" followed by "Can I take it?"
  → course_eligibility
- "Can I take CSE 4308?" followed by "ok thank you"
  → small_talk

Classify the CURRENT question using its meaning and the conversation history.
Short follow-ups like "what about 3 classes?" or "and in the fall?" usually
continue the previous route.

Return ONLY one of these exact values:
course_information
student_record
course_eligibility
degree_plan
compare_plans
small_talk
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
    "small_talk",
    "unsupported"
)


# Classify the student's question

def route_question(
    question: str,
    history: list[dict] | None = None
) -> str:

    history_text = "\n".join(
        f"{message.get('role', 'unknown')}: {message.get('content', '')}"
        for message in (history or [])[-12:]
    ) or "No previous conversation."

    decision = router_chain.invoke({
        "question": question,
        "history": history_text
    })

    route = decision.strip().lower().strip("`'\" .")

    if route in VALID_ROUTES:
        return route

    found = [r for r in VALID_ROUTES if r in route]

    if len(found) == 1:
        return found[0]

    # Never crash the request on an unexpected model reply.
    print(f"Router returned unexpected value: {route!r}", flush=True)
    return "unsupported"