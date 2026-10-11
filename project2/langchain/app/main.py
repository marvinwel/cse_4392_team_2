
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.router import route_question
from app.rag import answer_course_question


app = FastAPI(title="UTA AI Advisor - LangChain")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/chat")
def chat(request: ChatRequest):

    # Step 1: Route the student's question
    route = route_question(request.message)

    # Step 2: Execute the RAG pipeline
    if route == "course_information":

        result = answer_course_question(request.message)

        return {
            "route": route,
            "answer": result["answer"],
            "sources": result["sources"]
        }

    # Step 3: Handle unsupported requests
    return {
        "route": route,
        "answer": "This feature is not available yet.",
        "sources": []
    }
