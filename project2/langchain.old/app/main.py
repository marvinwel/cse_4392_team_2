
from fastapi import FastAPI
from pydantic import BaseModel, Field
from app.extract import codes_in
from app.router import route_question
from app.rag import answer_course_question
from app.course_context import resolve_course


app = FastAPI(title="UTA AI Advisor - LangChain")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[ChatMessage] = Field(default_factory=list)


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/chat")
def chat(request: ChatRequest):

    # Convert history to dictionaries
    history = [
        message.model_dump()
        for message in request.history
    ]

    # Step 1: Route the student's question
    route = route_question(
        question=request.message,
        history=history
    )

    # Step 2: Resolve course references
    course_id = resolve_course(
        question=request.message,
        history=history
    )

    # Step 3: Handle course information
    if route == "course_information":

        # For follow-up questions, include the resolved course
        question = request.message

        if course_id and not codes_in(question):
            question = f"{question} (Course: {course_id})"

        result = answer_course_question(question)

        return {
            "route": route,
            "answer": result["answer"],
            "sources": result["sources"]
        }

    # Step 4: Handle course eligibility
    if route == "course_eligibility":

        if not course_id:
            return {
                "route": route,
                "answer": (
                    "Which course would you like me "
                    "to check?"
                ),
                "sources": []
            }

        # Eligibility logic will be connected here.
        return {
            "route": route,
            "answer": (
                f"I understand you're asking about "
                f"{course_id}. The eligibility checker "
                f"is not connected yet."
            ),
            "sources": []
        }

    # Step 5: Handle other routes
    return {
        "route": route,
        "answer": "This feature is not available yet.",
        "sources": []
    }
