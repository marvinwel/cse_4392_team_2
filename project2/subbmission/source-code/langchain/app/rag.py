import os
from urllib.parse import urlparse

import chromadb

from langchain_aws import BedrockEmbeddings, ChatBedrockConverse
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.advisor_tools import fetch_courses
from app.extract import codes_in


AWS_REGION = os.getenv("AWS_REGION", "us-east-2")

EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"

CHROMA_URL = os.environ["CHROMA_URL"].rstrip("/")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "uta_ai_advisor")

BEDROCK_MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "google.gemma-3-27b-it"
)


# Same embedding settings as the ingestion Lambda, so the question vector
# and the stored document vectors are comparable.
embeddings = BedrockEmbeddings(
    model_id=EMBEDDING_MODEL_ID,
    region_name=AWS_REGION,
    model_kwargs={
        "dimensions": 1024,
        "normalize": True
    }
)


# LangChain vector store over the existing ChromaDB collection.
chroma_url = urlparse(CHROMA_URL)

chroma_client = chromadb.HttpClient(
    host=chroma_url.hostname,
    port=chroma_url.port or (443 if chroma_url.scheme == "https" else 8000),
    ssl=chroma_url.scheme == "https"
)

vector_store = Chroma(
    client=chroma_client,
    collection_name=CHROMA_COLLECTION_NAME,
    embedding_function=embeddings
)


# Retriever: embeds the question with Titan and returns the 4 nearest chunks.
retriever = vector_store.as_retriever(
    search_kwargs={"k": 4}
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


def describe_course(course: dict) -> str:
    prereq_groups = course.get("prereqs") or []

    prereqs = "; and ".join(
        " or ".join(
            option["course_id"]
            + (
                f" ({option['min_grade']} or better)"
                if option.get("min_grade")
                else ""
            )
            for option in group
        )
        for group in prereq_groups
    ) or "none"

    offered = ", ".join(
        course.get("terms_offered") or []
    ) or "not specified"

    return (
        f"Catalog record for {course.get('course_id', 'Unknown')} "
        f"{course.get('title', '')}: "
        f"{course.get('credits', 'Unknown')} credit hours. "
        f"Description: {course.get('description') or 'Not specified'}. "
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
    docs = retriever.invoke(question)

    documents = [doc.page_content for doc in docs]
    metadatas = [doc.metadata for doc in docs]

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
