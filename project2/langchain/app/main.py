#force update
import json
import boto3
import jwt

from typing import Optional
from functools import lru_cache

from boto3.dynamodb.conditions import Attr
from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app import session
from app.advisor import STUDENT_ROUTES, handle
from app.advisor_tools import students_table
from app.extract import codes_in
from app.course_context import resolve_course
from app.router import route_question
from app.rag import answer_course_question
from app.memory import compact_history



# Reply for questions the router classifies as "unsupported"
# (registration actions, financial aid, housing, unrelated topics).
UNSUPPORTED_ANSWER = (
    "I can only help with UTA academic advising, such as answering questions "
    "about course information, your academic records, course eligibility, "
    "and Degree planning\n"
    "For registration, financial aid or housing, please contact the "
    "appropriate UTA office or your academic advisor."
)




app = FastAPI(title="UTA AI Advisor - LangChain")


@lru_cache(maxsize=1)
def get_cognito_config():
    client = boto3.client(
        "secretsmanager",
        region_name="us-east-2"
    )

    response = client.get_secret_value(
        SecretId="uta-ai-advisor/backend/cognito"
    )

    return json.loads(response["SecretString"])


config = get_cognito_config()

COGNITO_REGION = config["region"]
COGNITO_POOL_ID = config["user_pool_id"]
COGNITO_CLIENT_ID = config["client_id"]

COGNITO_ISSUER = (
    f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/"
    f"{COGNITO_POOL_ID}"
)


@lru_cache(maxsize=1)
def jwks_client():
    return jwt.PyJWKClient(
        f"{COGNITO_ISSUER}/.well-known/jwks.json"
    )


def authenticated_user(authorization: str = Header(default="")):
    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        key = jwks_client().get_signing_key_from_jwt(token).key

        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=COGNITO_ISSUER,
            options={"require": ["exp", "iat", "iss", "sub"]},
        )

        if claims.get("token_use") != "access":
            raise ValueError("Invalid token type")

        if claims.get("client_id") != COGNITO_CLIENT_ID:
            raise ValueError("Invalid application client")

        return claims

    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_authenticated_student(claims: dict) -> str:
    cognito_sub = claims["sub"]

    table = students_table()

    response = table.scan(
        FilterExpression=Attr("cognito_sub").eq(cognito_sub),
        ProjectionExpression="student_id",
        Limit=100
    )

    students = response.get("Items", [])

    while "LastEvaluatedKey" in response:
        response = table.scan(
            FilterExpression=Attr("cognito_sub").eq(cognito_sub),
            ProjectionExpression="student_id",
            ExclusiveStartKey=response["LastEvaluatedKey"],
            Limit=100
        )
        students.extend(response.get("Items", []))

    if len(students) != 1:
        raise HTTPException(
            status_code=403,
            detail="No unique student record is linked to this Cognito account"
        )

    return students[0]["student_id"]


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: Optional[str] = None
    history: list[ChatMessage] = Field(default_factory=list)


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/chat")
def chat(
    request: ChatRequest,
    claims: dict = Depends(authenticated_user)
):
    # Identify the student from the verified Cognito account.
    student_id = get_authenticated_student(claims)

    # Scope conversation state to this authenticated student.
    session_id = (
        f"{student_id}:{request.session_id}"
        if request.session_id
        else None
    )

    state = session.get(session_id, student_id)

    # Convert conversation history to dictionaries.
    history = [
        message.model_dump()
        for message in request.history
    ]

    # Summarize older turns with the LLM so the router prompt stays small.
    # Recent turns are kept word for word.
    context_history = compact_history(history)

    # Step 1: Route the student's question using the compact history.
    route = route_question(
        question=request.message,
        history=context_history
    )

    # Step 2: Resolve course references from the FULL history, so a course
    # mentioned in an older (summarized) turn can still be found.
    course_id = resolve_course(
        question=request.message,
        history=history
    )

    print(
        f"Route for {request.message!r}: {route} (course: {course_id})",
        flush=True
    )

    # Step 3: Execute the RAG pipeline.
    if route == "course_information":
        question = request.message

        if course_id and not codes_in(question):
            question = f"{question} (Course: {course_id})"

        result = answer_course_question(question)

        session.update(
            session_id,
            student_id,
            last_route=route
        )

        return {
            "route": route,
            "answer": result["answer"],
            "sources": result["sources"],
            "data": None
        }

    # Step 4: Student-specific routes.
    if route in STUDENT_ROUTES:
        question = request.message

        # Follow-ups like "did I take it?" or "can I take it?" name no course,
        # so attach the course resolved from the conversation history.
        # (Not for degree_plan / compare_plans: those are about the whole plan.)
        if (
            route in ("student_record", "course_eligibility")
            and course_id
            and not codes_in(question)
        ):
            question = f"{question} (Course: {course_id})"

        if route == "course_eligibility":
            if not course_id:
                session.update(
                    session_id,
                    student_id,
                    last_route=route
                )

                return {
                    "route": route,
                    "answer": "Which course would you like me to check?",
                    "sources": [],
                    "data": None
                }

        result = handle(
            route,
            question,
            student_id,
            session_id
        )

        # Preserve the active route for subsequent follow-up questions.
        # session.update should merge fields rather than replace session state.
        session.update(
            session_id,
            student_id,
            last_route=route
        )

        return {
            "route": route,
            "answer": result["answer"],
            "sources": result["sources"],
            "data": result["data"]
        }

    # Step 5: Unsupported requests.
    session.update(
        session_id,
        student_id,
        last_route=route
    )

    return {
        "route": route,
        "answer": UNSUPPORTED_ANSWER,
        "sources": [],
        "data": None
    }