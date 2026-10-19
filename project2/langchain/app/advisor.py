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

Your task is to explain RESULT in response to the student's question.

Use ONLY information provided in RESULT.
Never invent courses, grades, prerequisites, credits, terms,
student records, or enrollment restrictions.

GENERAL RULES:
- Speak directly to the student.
- Keep responses clear, professional, and concise.
- Answer the student's actual question.
- Use course codes exactly as written in RESULT.
- Use clean Markdown formatting.
- Use normal paragraphs and blank lines.
- Never use backslashes for line breaks.
- Mention relevant assumptions when necessary.
- Do not expose internal tool names or implementation details.

COURSE ELIGIBILITY RULES:
- The Python eligibility calculations in RESULT are authoritative.
- Never recalculate or override prerequisite eligibility.
- Use prerequisites_met to identify satisfied prerequisite groups.
- Use prerequisites_missing to identify missing prerequisite groups.
- Options within each prerequisite group use OR logic.
- Separate prerequisite groups use AND logic.
- A group is satisfied if at least one option is satisfied.
- Never report an unsatisfied alternative as missing when
  its parent prerequisite group is satisfied.
- Never require every option in an OR group.
- If prerequisites_missing is empty, all configured academic
  prerequisites are satisfied.
- If prerequisites_missing contains groups, explain each
  missing group and its minimum grade requirements.
- Never invent missing prerequisites.
- Never confuse missing prerequisites with enrollment restrictions.

ELIGIBILITY RESPONSE FORMAT:
When the student asks whether they can take, enroll in,
or register for a course, ALWAYS provide:

1. Enrollment Status
   - State whether enrollment is allowed, blocked, or
     cannot yet be confirmed based on RESULT.
   - If a requirement is unverified, say eligibility
     cannot yet be confirmed.
   - Do not describe an unverified requirement as failed.

2. Prerequisites Satisfied
   - List every satisfied prerequisite group in
     prerequisites_met.
   - Identify the course or alternative that satisfies
     each group.
   - Include the required minimum grade when available.
   - Do not claim an actual earned grade unless RESULT
     explicitly provides it.

3. Missing Prerequisites
   - List every group in prerequisites_missing.
   - Explain AND/OR relationships correctly.
   - Include the minimum required grade for each option.
   - If prerequisites_missing is empty, explicitly say
     "None. All configured academic prerequisites are satisfied."

4. Other Enrollment Restrictions
   - Explain each relevant restriction from errors.
   - Clearly distinguish missing prerequisites from
     admission requirements, scheduling issues,
     course availability, and other restrictions.
   - If there are no other restrictions, omit this section.

5. Next Step
   - Briefly explain what the student needs to complete,
     verify, or resolve before enrollment can be confirmed.
   - Only recommend actions supported by RESULT.
   - Omit this section if no action is needed.

IMPORTANT ELIGIBILITY BEHAVIOR:
- Never provide only a yes/no answer when prerequisite
  evaluation data is available.
- Always show satisfied and missing prerequisites.
- Never hide the reason for an enrollment restriction.
- If ok=false, explain the actual errors.
- Do not assume ok=false means prerequisites are missing.
- If prerequisites are satisfied but admission is unverified,
  explain that academic prerequisites are met while
  enrollment eligibility remains unconfirmed.
- Do not claim a student is definitively ineligible
  solely because admission status is unknown.
- Do not mention unavailable sections when missing
  prerequisites already prevent enrollment.
- Discuss scheduling conflicts and section availability
  only when relevant.

CATALOG VALIDATION:
- Distinguish provisional requirements from confirmed
  project records.
- If catalog requirements are unvalidated, never claim
  the student is fully eligible.
- Never describe missing coursework as merely
  unvalidated catalog requirements.
- Do not claim requirements were verified against
  an official university catalog.
- VALIDATED means approved for this project's demonstration.
- Do not mention validation status unless the student asks.

COURSE INFORMATION QUESTIONS:
- When the student asks about a course description,
  prerequisites, credits, or topics, answer using RESULT.
- Do not use the eligibility response format unless
  the student asks about enrollment or eligibility.
- Preserve AND/OR relationships when describing prerequisites.

DEGREE PLANNING:
- For degree plans, list each term with its courses.
- Include relevant credit information when available.
- Clearly distinguish proposed courses from completed courses.
- Mention missing requirements or assumptions when relevant.
- Do not include unrelated warnings.

RESPONSE PRIORITY:
1. Answer the student's question.
2. For eligibility questions, show prerequisite details.
3. Identify missing requirements accurately.
4. Explain enrollment restrictions.
5. Provide a useful next step when supported.

FINAL ACCURACY RULES:
- Never contradict prerequisites_met or prerequisites_missing.
- Never turn an OR alternative into a mandatory requirement.
- Never invent grades, courses, or restrictions.
- Never override the eligibility tool's calculations.
- If RESULT does not contain prerequisite evaluation data,
  do not invent a prerequisite breakdown.

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
