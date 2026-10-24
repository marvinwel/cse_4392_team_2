
import json
import os

import boto3
import requests

from langchain_aws import ChatBedrockConverse
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.advisor_tools import fetch_courses
from app.extract import codes_in


AWS_REGION = os.getenv("AWS_REGION", "us-east-2")

EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"

CHROMA_URL = os.environ["CHROMA_URL"].rstrip("/")
CHROMA_COLLECTION_ID = os.environ["CHROMA_COLLECTION_ID"]

BEDROCK_MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "google.gemma-3-27b-it"
)


bedrock = boto3.client(
    "bedrock-runtime",
    region_name=AWS_REGION
)


answer_llm = ChatBedrockConverse(
    model=BEDROCK_MODEL_ID,
    region_name=AWS_REGION,
    temperature=0.2
)


answer_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are the UTA AI Advisor.

Answer the student's question using ONLY the
provided academic catalog context.

If the information is not available in the context,
say that you could not find it in the catalog.

Do not invent course descriptions, prerequisites,
credit hours, or degree requirements.

Context:
{context}"""
    ),
    ("human", "{question}")
])


answer_chain = (
    answer_prompt
    | answer_llm
    | StrOutputParser()
)


def embed_question(question: str) -> list[float]:
    response = bedrock.invoke_model(
        modelId=EMBEDDING_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps({
            "inputText": question,
            "dimensions": 1024,
            "normalize": True
        })
    )

    result = json.loads(response["body"].read())

    return result["embedding"]


def search_chromadb(embedding: list[float]) -> dict:
    url = (
        f"{CHROMA_URL}"
        "/api/v2/tenants/default_tenant"
        "/databases/default_database"
        f"/collections/{CHROMA_COLLECTION_ID}/query"
    )

    response = requests.post(
        url,
        json={
            "query_embeddings": [embedding],
            "n_results": 4,
            "include": [
                "documents",
                "metadatas",
                "distances"
            ]
        },
        timeout=20
    )

    response.raise_for_status()

    return response.json()


def describe_course(course: dict) -> str:
    prereqs = "; and ".join(
        " or ".join(
            option["course_id"]
            + (f" ({option['min_grade']} or better)" if option.get("min_grade") else "")
            for option in group
        )
        for group in course["prereqs"]
    ) or "none"

    offered = ", ".join(course["terms_offered"]) or "not specified"

    return (
        f"Catalog record for {course['course_id']} {course['title']}: "
        f"{course['credits']} credit hours. "
        f"Prerequisites: {prereqs}. "
        f"Terms offered: {offered}."
    )


def exact_course_records(question: str) -> list[dict]:
    """
    Similarity search can confuse CSE 3318 with CSE 3315, so when the question names
    course codes, fetch those exact records by ID and put them first in the context.
    """
    codes = codes_in(question)

    if not codes:
        return []

    try:
        found = fetch_courses(codes)
    except Exception:
        return []

    return [found[code] for code in codes if code in found]


def answer_course_question(question: str) -> dict:
    embedding = embed_question(question)

    results = search_chromadb(embedding)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    exact = exact_course_records(question)

    if not documents and not exact:
        return {
            "answer": "I could not find relevant information in the catalog.",
            "sources": []
        }

    context_parts = [
        f"Source: course catalog\n{describe_course(course)}"
        for course in exact
    ]
    sources = ["course catalog"] if exact else []

    for index, document in enumerate(documents):
        metadata = metadatas[index] or {}

        source = metadata.get("source", "Unknown document")

        context_parts.append(
            f"Source: {source}\n{document}"
        )

        if source not in sources:
            sources.append(source)

    context = "\n\n---\n\n".join(context_parts)

    answer = answer_chain.invoke({
        "question": question,
        "context": context
    })

    return {
        "answer": answer,
        "sources": sources
    }
