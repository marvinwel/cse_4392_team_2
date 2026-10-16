
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app import session
from app.advisor import STUDENT_ROUTES, handle, list_students
from app.router import route_question
from app.rag import answer_course_question


app = FastAPI(title="UTA AI Advisor - LangChain")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    # Which student is asking. Needed for eligibility, degree plans, and transcripts.
    student_id: Optional[str] = None
    # Same value for every message in one chat window, so follow-up questions work.
    session_id: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/students")
def students():
    # For the UI's student picker
    return {"students": list_students()}


@app.post("/chat")
def chat(request: ChatRequest):

    state = session.get(request.session_id, request.student_id)

    # Step 1: Route the student's question
    route = route_question(request.message, state.get("last_route"))

    # Step 2: Execute the RAG pipeline
    if route == "course_information":

        result = answer_course_question(request.message)

        session.update(request.session_id, request.student_id, last_route=route)

        return {
            "route": route,
            "answer": result["answer"],
            "sources": result["sources"],
            "data": None
        }

    # Step 3: Student-specific routes (eligibility, plans, transcript)
    if route in STUDENT_ROUTES:

        result = handle(
            route,
            request.message,
            request.student_id,
            request.session_id
        )

        return {
            "route": route,
            "answer": result["answer"],
            "sources": result["sources"],
            "data": result["data"]
        }

    # Step 4: Handle unsupported requests
    return {
        "route": route,
        "answer": "This feature is not available yet.",
        "sources": [],
        "data": None
    }
