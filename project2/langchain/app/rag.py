
import json
import os

import boto3
import requests

from langchain_aws import ChatBedrockConverse
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


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


def answer_course_question(question: str) -> dict:
    embedding = embed_question(question)

    results = search_chromadb(embedding)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    if not documents:
        return {
            "answer": "I could not find relevant information in the catalog.",
            "sources": []
        }

    context_parts = []
    sources = []

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
