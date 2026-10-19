"""
Turn a student's message into tool parameters.

Gemma reads the message and returns JSON. Everything it returns is then checked and normalized
in code (course codes, term IDs, program IDs), so a sloppy model answer can't reach the tools.
"""

import json
import os
import re
from datetime import date
from functools import lru_cache
from typing import Optional

from langchain_aws import ChatBedrockConverse
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, ValidationError

from app.advisor_tools import _next_term, chroma_get, chroma_query, embed_query

COURSE_CODE = re.compile(r"\b([A-Za-z]{2,4})\s*-?\s*(\d{4})\b")
TERM_NAMES = {"SP": "Spring", "SU": "Summer", "FA": "Fall"}


# ---------------------------------------------------------------------------
# Parameter shapes
# ---------------------------------------------------------------------------

class EligibilityParams(BaseModel):
    courses: list[str] = Field(default_factory=list)
    term: Optional[str] = None


class PlanParams(BaseModel):
    start_term: Optional[str] = None
    max_courses_per_term: Optional[int] = Field(None, ge=1, le=8)
    max_credits_per_term: Optional[int] = Field(None, ge=3, le=21)
    include_summer: Optional[bool] = None
    preferred_electives: list[str] = Field(default_factory=list)
    program: Optional[str] = None


class CompareParams(BaseModel):
    plan_a: Optional[str] = None
    plan_b: Optional[str] = None


FIELDS = {
    "course_eligibility": (EligibilityParams, """{
  "courses": list of the courses the student asks about, as codes like "CSE 3318" or as the name they used,
  "term": the term they ask about, like "2027-SP", or null if they didn't say
}"""),
    "degree_plan": (PlanParams, """{
  "start_term": first term of the plan, like "2027-SP", or null,
  "max_courses_per_term": number of classes per semester they asked for, or null,
  "max_credits_per_term": number of credit hours per semester they asked for, or null,
  "include_summer": true if they want summer classes, false if they said no summers, else null,
  "preferred_electives": list of elective course codes or names they want, or [],
  "program": program code from the list below if they ask about a different major, else null
}"""),
    "compare_plans": (CompareParams, """{
  "plan_a": name of the first plan they mention, like "Plan 1", or null,
  "plan_b": name of the second plan they mention, or null
}"""),
}


# ---------------------------------------------------------------------------
# Terms
# ---------------------------------------------------------------------------

def current_term(today: date) -> str:
    code = "SP" if today.month <= 5 else "SU" if today.month <= 7 else "FA"
    return f"{today.year}-{code}"


def upcoming_terms(today: date, count: int = 6) -> list[str]:
    terms, term = [], current_term(today)
    for _ in range(count):
        term = _next_term(term, include_summer=True)
        terms.append(term)
    return terms


def next_regular_term(today: date) -> str:
    return next(t for t in upcoming_terms(today) if not t.endswith("SU"))


def term_label(term_id: str) -> str:
    year, code = term_id.split("-")
    return f"{TERM_NAMES[code]} {year}"


def normalize_term(value, today: date) -> Optional[str]:
    """Accept '2027-SP', 'Spring 2027', 'fall 27', 'next spring', 'next semester'."""
    if not value:
        return None
    text = str(value).strip().lower()

    m = re.fullmatch(r"(\d{4})\s*-\s*(sp|su|fa)", text)
    if m:
        return f"{m.group(1)}-{m.group(2).upper()}"

    names = {"spring": "SP", "summer": "SU", "fall": "FA", "autumn": "FA"}
    m = re.search(r"(spring|summer|fall|autumn)\s*'?(\d{4}|\d{2})\b", text) or \
        re.search(r"\b(\d{4})\s+(spring|summer|fall|autumn)", text)
    if m:
        season, year = (m.group(1), m.group(2)) if not m.group(1).isdigit() else (m.group(2), m.group(1))
        year = int(year) + (2000 if len(year) == 2 else 0)
        return f"{year}-{names[season]}"

    upcoming = upcoming_terms(today)
    for season, code in names.items():
        if season in text:
            return next(t for t in upcoming if t.endswith(code))
    if "next" in text and ("semester" in text or "term" in text):
        return next_regular_term(today)
    if "summer" in text:
        return next(t for t in upcoming if t.endswith("SU"))
    return None


# ---------------------------------------------------------------------------
# Courses and programs
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def known_subjects() -> frozenset:
    """Subject prefixes in the catalog (CSE, MATH, IE, ...), so 'fall 2027' isn't read as a course."""
    try:
        ids = chroma_get(where={"record_type": "course"})["ids"]
    except Exception:
        return frozenset()
    return frozenset(i.split()[0] for i in ids if " " in i)


def _is_course_match(m) -> bool:
    subject = m.group(1).upper()
    subjects = known_subjects()

    if subjects:
        return subject in subjects

    # Accept lowercase and uppercase course codes.
    return subject in {
        "CSE", "MATH", "IE", "COMS", "ENGL",
        "PHYS", "CHEM", "BIOL", "ECON",
        "POLS", "ENGR", "UNIV"
    }


def normalize_course_code(value) -> Optional[str]:
    m = next((m for m in COURSE_CODE.finditer(str(value or "")) if _is_course_match(m)), None)
    return f"{m.group(1).upper()} {m.group(2)}" if m else None


def codes_in(text: str) -> list[str]:
    seen = []
    for m in COURSE_CODE.finditer(text or ""):
        code = f"{m.group(1).upper()} {m.group(2)}"
        if _is_course_match(m) and code not in seen:
            seen.append(code)
    return seen


def resolve_course(value) -> tuple[Optional[str], Optional[str]]:
    """
    Return (course_id, note). A code is used as-is. A course name ("algorithms") is matched
    against course records by meaning, and the note says which course was assumed.
    """
    code = normalize_course_code(value)
    if code:
        return code, None
    if not value or COURSE_CODE.search(str(value)):
        return None, None        # empty, or code-shaped but not a real subject ("FALL 2027")
    res = chroma_query(embed_query(str(value)), n_results=1, where={"record_type": "course"})
    if not res["ids"][0]:
        return None, None
    md = res["metadatas"][0][0]
    return md["course_id"], f'Assumed "{value}" means {md["course_id"]} {md.get("title", "")}'.strip()


@lru_cache(maxsize=1)
def known_programs() -> tuple[tuple[str, str], ...]:
    res = chroma_get(where={"record_type": "program"})
    return tuple((pid, (md or {}).get("name", pid)) for pid, md in zip(res["ids"], res["metadatas"]))


def normalize_program(value) -> Optional[str]:
    if not value:
        return None
    text = str(value).strip().lower()
    for pid, name in known_programs():
        if text == pid.lower() or text == name.lower():
            return pid
    for pid, name in known_programs():
        if text in name.lower() or pid.lower() in text:
            return pid
    return None


# ---------------------------------------------------------------------------
# The LLM step
# ---------------------------------------------------------------------------

extract_prompt = ChatPromptTemplate.from_messages([
    ("system", """You extract settings from a student's message for the UTA AI Advisor.

Today is {today}. The current term is {current_term}.
Upcoming terms (use these IDs): {terms}
"Next semester" means {next_regular}.
Programs: {programs}

Previous settings in this conversation (JSON, may be empty): {previous}
If the student is changing their previous request (for example "what about 3 classes?"),
return the previous settings with their change applied. If they ask for something new,
do not carry over previous settings.

Return ONLY a JSON object with exactly these fields, no other text:
{fields}"""),
    ("human", "{question}"),
])

extract_llm = ChatBedrockConverse(
    model=os.getenv("BEDROCK_MODEL_ID", "google.gemma-3-27b-it"),
    region_name=os.getenv("AWS_REGION", "us-east-2"),
    temperature=0,
)

extract_chain = extract_prompt | extract_llm | StrOutputParser()


def parse_json(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return {}
    try:
        value = json.loads(text[start:end + 1])
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def extract(route: str, question: str, previous: Optional[dict] = None, today: Optional[date] = None):
    model, fields = FIELDS[route]
    today = today or date.today()
    try:
        programs = ", ".join(f"{pid} ({name})" for pid, name in known_programs()) or "none loaded"
    except Exception:
        programs = "unknown"
    raw = extract_chain.invoke({
        "today": today.isoformat(),
        "current_term": current_term(today),
        "terms": ", ".join(f"{term_label(t)} = {t}" for t in upcoming_terms(today)),
        "next_regular": next_regular_term(today),
        "programs": programs,
        "previous": json.dumps(previous or {}),
        "fields": fields,
        "question": question,
    })
    data = parse_json(raw)
    try:
        params = model.model_validate({
            k: v for k, v in data.items()
            if v is not None
    })

    except ValidationError:
        clean = {}

        for key, value in data.items():
            try:
                model.model_validate({key: value})
                clean[key] = value
            except ValidationError:
                pass

        params = model.model_validate(clean)

    if route == "course_eligibility":
        explicit_courses = codes_in(question)

        if explicit_courses:
            params.courses = explicit_courses

        if params.term:
            params.term = normalize_term(params.term, today)

        # Recover an explicitly mentioned term if Gemma omitted it.
        if not params.term:
            params.term = normalize_term(question, today)

    return params
