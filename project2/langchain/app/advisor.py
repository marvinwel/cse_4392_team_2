"""
Student routes: eligibility, degree plans, plan comparison, and student records.

Each route follows the same steps:
  1. extract     Gemma pulls parameters from the message (app/extract.py), checked in code
  2. tool        a deterministic function in app/advisor_tools.py does the real work
  3. phrase      Gemma explains the tool's result to the student, using only that result
The structured result is also returned as "data" so the UI can render tables.
"""

import json
import os
from datetime import date

from langchain_aws import ChatBedrockConverse
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app import extract, session
from app.advisor_tools import (
    _courses_still_needed, best_grades, check_course_eligibility, compare_degree_plans,
    fetch_courses, fetch_program, generate_degree_plan, get_student_record, students_table,
)

STUDENT_ROUTES = ("student_record", "course_eligibility", "degree_plan", "compare_plans")


# ---------------------------------------------------------------------------
# Phrasing
# ---------------------------------------------------------------------------


phrase_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are the UTA AI Advisor talking with {student_name}.

Your task is to explain the RESULT in response to the student's question.

Use ONLY information provided in RESULT. Do not invent information.

GENERAL RULES:
- Speak directly to the student.
- Keep responses short, clear, and professional.
- Answer only what the student asked.
- Use course codes exactly as written in RESULT.
- Do not invent courses, grades, prerequisites, credits, or terms.
- Use clean Markdown with normal paragraphs and blank lines.
- Never use backslashes for line breaks.
- Mention relevant assumptions so the student can correct them.

COURSE ELIGIBILITY RULES:
- The Python eligibility tool's calculations are authoritative.
- Never recalculate or reinterpret prerequisite eligibility.
- Use prerequisites_missing to determine missing prerequisites.
- If prerequisites_missing is empty, all configured academic
  prerequisites are satisfied.
- If prerequisites_missing contains groups, explain only those
  missing groups and their required minimum grades.
- Prerequisite options within a group use OR logic.
- Different prerequisite groups use AND logic.
- A prerequisite group is satisfied when at least one option
  within that group is satisfied.
- NEVER report an individual option as missing when its parent
  group has satisfied=true.
- NEVER require every option in an OR group to be completed.
- If IE 3301 satisfies an OR group containing MATH 3313,
  do not claim MATH 3313 is missing or required.
- If prerequisites_missing is empty, do not identify any
  individual prerequisite as missing, even if its
  satisfied field is false.
- If prerequisites_met is provided, use it to explain
  which prerequisite groups have been satisfied.
- If a prerequisite is missing, explain that the student's
  transcript does not show completion with the required grade.
- Do not confuse missing prerequisites with other
  enrollment restrictions.

ENROLLMENT DECISIONS:
- Use the errors field to identify enrollment restrictions.
- If ok=false, explain the actual errors reported by the tool.
- Do not assume ok=false means prerequisites are missing.
- If all prerequisites are satisfied but another restriction
  exists, explicitly distinguish those two findings.
- If something is not allowed, explain why in plain language.
- Do not mention section availability when missing
  prerequisites already prevent enrollment.
- Only discuss schedule conflicts or section availability
  when relevant to the student's question.

CATALOG VALIDATION:
- Distinguish provisional prerequisite findings from
  final eligibility decisions.
- If catalog requirements are unvalidated, never claim
  the student is fully eligible.
- Do not describe missing coursework as unvalidated rules.
- Do not claim requirements were verified against an
  official university catalog.
- VALIDATED means approved for this project's demonstration.
- Do not mention validation status unless the student asks.

DEGREE PLANNING:
- For degree plans, list each term with its courses.
- Do not include unrelated technical elective or degree
  requirement warnings.
- Clearly distinguish confirmed requirements from assumptions.

RESPONSE PRIORITY:
1. Answer the student's question directly.
2. State whether configured academic prerequisites are satisfied.
3. Explain missing prerequisite groups, if any.
4. Explain other enrollment restrictions from errors.
5. Mention relevant assumptions when necessary.

IMPORTANT:
- Never contradict prerequisites_missing or errors.
- Never invent missing prerequisites.
- Never turn an optional OR alternative into a requirement.
- Focus on satisfied prerequisites, missing prerequisites,
  and enrollment restrictions.

RESULT:
{result}"""),
    ("human", "{question}"),
])


phrase_llm = ChatBedrockConverse(
    model=os.getenv("BEDROCK_MODEL_ID", "google.gemma-3-27b-it"),
    region_name=os.getenv("AWS_REGION", "us-east-2"),
    temperature=0.2,
)

phrase_chain = phrase_prompt | phrase_llm | StrOutputParser()


def phrase(question: str, record: dict, result: dict) -> str:
    return phrase_chain.invoke({
        "student_name": record.get("name") or "the student",
        "question": question,
        "result": json.dumps(result, indent=1, default=str),
    })


def reply(answer: str, data=None) -> dict:
    return {"answer": answer, "sources": [], "data": data}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

def handle(route: str, message: str, student_id: str | None, session_id: str | None,
           today: date | None = None) -> dict:
    today = today or date.today()
    if not student_id:
        return reply("Please select a student first, then ask again.")

    record = get_student_record.invoke({"student_id": student_id})
    if "error" in record:
        return reply(f"I couldn't find that student: {record['error']}")

    state = session.get(session_id, student_id)
    handlers = {
        "student_record": student_record,
        "course_eligibility": course_eligibility,
        "degree_plan": degree_plan,
        "compare_plans": compare_plans,
    }
    result = handlers[route](message, record, state, today)
    session.update(session_id, student_id, last_route=route, **result.pop("_session", {}))
    return result


def student_record(message, record, state, today) -> dict:
    data = dict(record)

    # Transcript questions already have the required data.
    # Avoid fetching every degree requirement and course.
    transcript_words = (
        "completed",
        "transcript",
        "grades",
        "courses taken",
        "classes taken",
    )

    if any(word in message.lower() for word in transcript_words):
        return reply(phrase(message, record, data), data)

    try:
        program = fetch_program(
            record["program_id"],
            catalog_year=int(record["catalog_year"])
        )

        grades = best_grades(record["transcript"])

        courses = fetch_courses(
            [c for g in program["requirements"] for c in g["courses"]]
            + [t["course_id"] for t in record["transcript"]],
            catalog_year=int(record["catalog_year"])
        )

        remaining, notes = _courses_still_needed(
            program, grades, courses, []
        )

        data.update({
            "program_name": program["name"],
            "total_credits_required": program["total_credits"],
            "remaining_required_courses": remaining,
            "notes": notes
        })

    except LookupError as error:
        data["notes"] = [str(error)]

    return reply(phrase(message, record, data), data)


def course_eligibility(message, record, state, today) -> dict:
    params = extract.extract("course_eligibility", message,
                             {"courses": [state["last_course_id"]]} if state.get("last_course_id") else {},
                             today)

    wanted = params.courses or extract.codes_in(message)
    if not wanted and state.get("last_course_id"):
        wanted = [state["last_course_id"]]
    if not wanted:
        return reply("Which course do you want me to check? Include the course code, like CSE 3318.")

    assumptions = []
    term_id = extract.normalize_term(params.term, today)
    if not term_id:
        term_id = extract.next_regular_term(today)
        assumptions.append(f"Checked for {extract.term_label(term_id)} because no term was given")

    results = []
    for value in wanted[:5]:
        course_id, note = extract.resolve_course(value)
        if note:
            assumptions.append(note)
        if not course_id:
            results.append({"ok": False, "course_id": str(value),
                            "errors": [f"couldn't find a course matching {value!r}"]})
            continue
        results.append(check_course_eligibility.invoke(
            {"student_id": record["student_id"], "course_id": course_id, "term_id": term_id}))

    data = {"term_id": term_id, "results": results, "assumptions": assumptions}
    answer = phrase(message, record, data)
    return {**reply(answer, data),
            "_session": {"last_course_id": results[-1].get("course_id"), "last_term_id": term_id}}


def degree_plan(message, record, state, today) -> dict:
    previous = state.get("last_plan_params") or {}
    params = extract.extract("degree_plan", message, previous, today)

    assumptions = []
    start_term = extract.normalize_term(params.start_term, today)
    if not start_term:
        start_term = extract.next_regular_term(today)
        assumptions.append(f"Plan starts {extract.term_label(start_term)}")

    program_id = extract.normalize_program(params.program)
    if params.program and not program_id:
        assumptions.append(f"Couldn't match program {params.program!r}; planned for {record['program_id']}")

    electives = [c for c in (extract.normalize_course_code(e) for e in params.preferred_electives) if c]
    settings = {
        "start_term": start_term,
        "max_credits_per_term": params.max_credits_per_term or 15,
        "max_courses_per_term": params.max_courses_per_term,
        "include_summer": bool(params.include_summer),
        "preferred_electives": electives,
        "program_id": program_id,
    }

    taken = set(record.get("saved_plans", [])) | set(state.get("plan_names", []))
    number = 1
    while f"Plan {number}" in taken:
        number += 1
    plan_name = f"Plan {number}"

    result = generate_degree_plan.invoke({"student_id": record["student_id"], "save_as": plan_name,
                                          **{k: v for k, v in settings.items() if v is not None}})
    data = {**result, "settings": settings, "assumptions": assumptions}
    if not result.get("saved"):
        data.pop("plan_name", None)

    plan_names = state.get("plan_names", []) + ([plan_name] if result.get("saved") else [])
    return {**reply(phrase(message, record, data), data),
            "_session": {"last_plan_params": {k: v for k, v in settings.items() if v not in (None, [])},
                         "plan_names": plan_names}}


def compare_plans(message, record, state, today) -> dict:
    params = extract.extract("compare_plans", message, {}, today)
    saved = record.get("saved_plans", [])

    def match(name):
        if not name:
            return None
        return next((p for p in saved if p.lower() == str(name).strip().lower()), None)

    a, b = match(params.plan_a), match(params.plan_b)

    # Fill in whatever wasn't named with the most recent plans from this chat
    # (or from all saved plans if this chat hasn't made any).
    recent = [p for p in state.get("plan_names", []) if p in saved] or list(saved)
    newest_first = [p for p in reversed(recent) if p not in (a, b)]
    if a and not b:
        b = newest_first[0] if newest_first else None
    elif b and not a:
        a = newest_first[0] if newest_first else None
    elif not a and not b and len(newest_first) >= 2:
        a, b = newest_first[1], newest_first[0]

    if not a or not b or a == b:
        return reply("I need two saved plans to compare. Ask me to make a plan, then ask for a "
                     "different version (for example, with fewer classes per semester).",
                     {"saved_plans": saved})

    data = compare_degree_plans.invoke({"student_id": record["student_id"], "plan_a": a, "plan_b": b})
    return reply(phrase(message, record, data), data)


# ---------------------------------------------------------------------------
# Student list for the UI's picker
# ---------------------------------------------------------------------------

def list_students() -> list[dict]:
    items, kwargs = [], {"ProjectionExpression": "student_id, first_name, last_name, program_id, scenario"}
    while True:
        page = students_table().scan(**kwargs)
        items += page.get("Items", [])
        if "LastEvaluatedKey" not in page:
            break
        kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]
    return sorted(({"student_id": i["student_id"],
                    "name": f"{i.get('first_name', '')} {i.get('last_name', '')}".strip(),
                    "program_id": i.get("program_id"), "scenario": i.get("scenario")} for i in items),
                  key=lambda s: s["student_id"])
