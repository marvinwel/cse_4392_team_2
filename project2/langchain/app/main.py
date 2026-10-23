#new
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
from app.router import route_question
from app.rag import answer_course_question


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

    

class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: Optional[str] = None


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

    # Step 1: Route the student's question.
    route = route_question(
        request.message,
        state.get("last_route")
    )

    # Step 2: Execute the RAG pipeline.
    if route == "course_information":
        result = answer_course_question(request.message)

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

    # Step 3: Student-specific routes.
    if route in STUDENT_ROUTES:
        result = handle(
            route,
            request.message,
            student_id,
            session_id
        )

        return {
            "route": route,
            "answer": result["answer"],
            "sources": result["sources"],
            "data": result["data"]
        }

    # Step 4: Unsupported requests.
    return {
        "route": route,
        "answer": "This feature is not available yet.",
        "sources": [],
        "data": None
    }
