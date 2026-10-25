"""
Courtesy replies for the small_talk route ("thank you", "ok", "hi", "bye").

A LangChain chain asks Gemma for a short, friendly reply plus one follow-up
question based on the recent conversation.
"""

import os

from langchain_aws import ChatBedrockConverse
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


FALLBACK_REPLY = (
    "You're welcome! Is there anything else I can help you with, "
    "like a course question or your degree plan?"
)


courtesy_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are the UTA AI Advisor, a friendly academic advisor for
UTA Computer Science students.

The student just sent a short conversational message (thanks, ok, a greeting
or a goodbye). Reply in this format:
1. One or two short, warm sentences that respond to their message.
2. One follow-up question that offers a useful next step based on the recent
   conversation. For example, after a course question offer to check whether
   they can take it; after an eligibility answer offer to add it to a degree plan.
   If there is no recent conversation, ask what they would like help with:
   course information, their record, course eligibility, or a degree plan.
If the student is saying goodbye, wish them well and skip the follow-up question.

Rules:
- Keep the whole reply under 50 words.
- Do not state any facts about courses, grades, prerequisites or requirements.
- Speak directly to the student.

Recent conversation:
{history}"""
    ),
    ("human", "{message}")
])


courtesy_llm = ChatBedrockConverse(
    model=os.getenv("BEDROCK_MODEL_ID", "google.gemma-3-27b-it"),
    region_name=os.getenv("AWS_REGION", "us-east-2"),
    temperature=0.3,
    max_tokens=150,
)


courtesy_chain = courtesy_prompt | courtesy_llm | StrOutputParser()


def courtesy_reply(message: str, history: list[dict] | None = None) -> str:
    history_text = "\n".join(
        f"{m.get('role', 'unknown')}: {m.get('content', '')}"
        for m in (history or [])[-6:]
    ) or "No previous conversation."

    try:
        reply = courtesy_chain.invoke({
            "message": message,
            "history": history_text
        }).strip()
    except Exception as exc:
        print(f"Courtesy reply failed: {exc!r}", flush=True)
        return FALLBACK_REPLY

    return reply or FALLBACK_REPLY