"""
Conversation memory compaction for the UTA AI Advisor.

Older chat turns are summarized by the LLM; the most recent turns are kept
word for word. The router then receives:

    [{"role": "summary", "content": "<short summary of older turns>"},
     ...recent messages...]

instead of every message, so the prompt stays small as the chat grows.
"""

import os
from functools import lru_cache

from langchain_aws import ChatBedrockConverse
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


# Messages kept word for word (2 messages = 1 student question + 1 answer).
KEEP_RECENT = int(os.getenv("HISTORY_KEEP_RECENT", "4"))

# Older messages are summarized in blocks of this size. Because the cut point
# only moves every BLOCK messages, the same older text is seen on consecutive
# turns and the cached summary is reused (about one LLM call every 2 turns).
BLOCK = int(os.getenv("HISTORY_SUMMARY_BLOCK", "4"))

# Long answers (degree plans) are trimmed before summarizing.
MAX_CHARS_PER_MESSAGE = 1500


summary_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You compress a conversation between a UTA student and the UTA AI Advisor.
The summary is used as context for the student's NEXT question.

Write at most 6 short bullet points. Keep:
- Course codes discussed and what was said about them
  (eligible or not, missing prerequisites, grades mentioned)
- The student's stated preferences: classes or credits per semester,
  summer sessions, start term, major, concentration, electives
- Any degree plan requested and its settings
- Questions the student asked that are still open

Drop greetings and repeated text.
Do not add any fact that is not in the conversation."""
    ),
    ("human", "Conversation to summarize:\n{transcript}")
])


summary_llm = ChatBedrockConverse(
    model=os.getenv("BEDROCK_MODEL_ID", "google.gemma-3-27b-it"),
    region_name=os.getenv("AWS_REGION", "us-east-2"),
    temperature=0,
    max_tokens=300,
)


summary_chain = summary_prompt | summary_llm | StrOutputParser()


def _format(messages: list[dict]) -> str:
    lines = []
    for message in messages:
        content = str(message.get("content", ""))
        if len(content) > MAX_CHARS_PER_MESSAGE:
            content = content[:MAX_CHARS_PER_MESSAGE] + " ..."
        lines.append(f"{message.get('role', 'unknown')}: {content}")
    return "\n".join(lines)


@lru_cache(maxsize=256)
def _summarize(transcript: str) -> str:
    return summary_chain.invoke({"transcript": transcript}).strip()


def compact_history(history: list[dict] | None) -> list[dict]:
    """Return [summary message] + recent messages, or the history unchanged
    when it is still short."""
    history = history or []

    older_count = ((len(history) - KEEP_RECENT) // BLOCK) * BLOCK
    if older_count <= 0:
        return history

    older = history[:older_count]
    recent = history[older_count:]
    transcript = _format(older)

    try:
        summary = _summarize(transcript)
    except Exception as exc:
        # Never let a failed summary break the student's request.
        print(f"History summary failed; using recent messages only: {exc!r}", flush=True)
        return recent

    compacted = [{"role": "summary", "content": summary}] + recent

    before = sum(len(str(m.get("content", ""))) for m in history)
    after = sum(len(str(m.get("content", ""))) for m in compacted)
    print(
        f"History compacted: {len(history)} messages / {before} chars -> "
        f"summary + {len(recent)} messages / {after} chars",
        flush=True,
    )

    return compacted