"""
Advisor tools: DynamoDB (students, degree plans) + Chroma (everything catalog).

    pip install langchain-core boto3
    aws configure                                  # region us-east-2, same as the ingestion Lambda
    export CHROMA_URL="http://<chroma-host>:8000"  # same server + collection the Lambda writes to
    export CHROMA_COLLECTION_ID="<collection uuid>"
    export DYNAMO_ENDPOINT="http://localhost:8000"  # only when using DynamoDB Local
    python dynamo_setup.py                         # creates the student / plan tables

Where data lives
- DynamoDB advisor_students       profile + transcript (stored inside the item)
- DynamoDB advisor_degree_plans   saved plans; written ONLY by save_degree_plan, after validation
- Chroma   ONE collection, filled by the ingestion Lambda, holding three kinds of record
           (metadata "record_type"):
             course   id = exact course code ("CSE 3318"), from docs .../courses.json
             program  id = program code ("BS-CS"),        from docs .../programs.json
             chunk    id = hash, pieces of catalog / policy documents for open questions

Embeddings
  The Lambda embeds with Amazon Titan Text Embeddings v2 (1024 dims). search_catalog embeds
  the question with the SAME model; a different model would make the distances meaningless.

The one rule that makes this work
  Exact facts (credits, prereqs, sections, degree requirements) are read from
  Chroma with collection.get(ids=[...]): an exact ID lookup, no embeddings.
  Similarity search (collection.query) is ONLY for open-ended questions like
  "which course covers network security?". Embeddings can confuse CSE 3318
  with CSE 3315, so never answer an exact question from query().

Chroma metadata contract (the ingestion Lambda writes records this way)
  Chroma metadata values must be str/int/float/bool, so nested data is JSON text.

  course records   id: "CSE 3318"   record_type: "course"
    document:   full course description (this is what gets embedded)
    metadata:
      course_id      "CSE 3318"                       same string as the id
      title          "Algorithms and Data Structures"
      credits        3                                int
      prereqs        '[[{"course_id":"CSE 2315"}],
                       [{"course_id":"CSE 1325","min_grade":"C"},
                        {"course_id":"CSE 1320","min_grade":"C"}]]'
                     AND across the outer list, OR inside each inner list. "[]" if none.
      terms_offered  '["fall","spring"]'             "[]" = no restriction
      sections       '{"2027-SP":[{"section":"001",
                        "meetings":[{"day":"M","start":"10:00","end":"11:20"}]}]}'
                     "{}" if no schedule yet. Days M T W R F S; zero-padded 24h times.

  program records  id: "BS-CS"      record_type: "program"
    document:   program overview text
    metadata:
      program_id     "BS-CS"
      name           "B.S. Computer Science"
      total_credits  120                              int
      requirements   '[{"name":"Core","courses":["CSE 1310","CSE 1320"]},
                       {"name":"Tech electives","courses":["CSE 4308"],"min_credits":12}]'

  chunk records    id: hash         record_type: "chunk"
    document:   a chunk of text
    metadata:   source, category, page, plus course_id / program_id when known
                (enables exact filtering in search_catalog)

DynamoDB items
  advisor_students      key student_id
                        {student_id: "1001234567", first_name, last_name, program_id: "BS-CS",
                         catalog_year: 2025,
                         transcript: [{course_id: "CSE 1310", term_id: "2025-FA", grade: "A"}]}
  advisor_degree_plans  key student_id + plan_name
                        {student_id, plan_name, program_id,
                         terms: [{term_id: "2027-SP", courses: [{course_id, section}]}],
                         total_credits, created_at, updated_at}   (dates are ISO strings)

Term IDs look like "2027-SP", "2027-SU", "2027-FA".
"""

from __future__ import annotations

import json
import os
from decimal import Decimal
from datetime import datetime, timezone
from functools import lru_cache
from typing import Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

AWS_REGION = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-2"
DYNAMO_ENDPOINT = os.environ.get("DYNAMO_ENDPOINT")       # None = real AWS
STUDENTS_TABLE = os.environ.get("STUDENTS_TABLE", "advisor_students")
PLANS_TABLE = os.environ.get("PLANS_TABLE", "advisor_degree_plans")
CHROMA_URL = os.environ.get("CHROMA_URL", "http://localhost:8000").rstrip("/")
CHROMA_COLLECTION_ID = os.environ.get("CHROMA_COLLECTION_ID", "")
CHROMA_TENANT = os.environ.get("CHROMA_TENANT", "default_tenant")
CHROMA_DATABASE = os.environ.get("CHROMA_DATABASE", "default_database")

EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"   # must match the ingestion Lambda
EMBEDDING_DIMENSIONS = 1024

# UTA undergraduate limits (2023-24 catalog, Academic Regulations > Registration):
# max 19 hours fall/spring, 14 hours summer. Verify against the current catalog.
MAX_TERM_CREDITS = {"fall": 19, "spring": 19, "summer": 14}

GRADE_RANK = {"A": 4, "B": 3, "C": 2, "D": 1, "P": 1, "F": 0, "W": -1, "I": -1}
PASSING_RANK = GRADE_RANK["D"]
_TERM_CODES = {"SP": ("spring", 0), "SU": ("summer", 1), "FA": ("fall", 2)}


# ---------------------------------------------------------------------------
# Connections (created once, reused)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def dynamo():
    import boto3
    return boto3.resource("dynamodb", region_name=AWS_REGION, endpoint_url=DYNAMO_ENDPOINT or None)


def students_table():
    return dynamo().Table(STUDENTS_TABLE)


def plans_table():
    return dynamo().Table(PLANS_TABLE)


@lru_cache(maxsize=1)
def _bedrock():
    import boto3
    return boto3.client("bedrock-runtime", region_name=AWS_REGION)


def _chroma_request(action: str, payload: dict) -> dict:
    """Same Chroma HTTP API (v2) the ingestion Lambda uses."""
    import urllib.request
    url = (f"{CHROMA_URL}/api/v2/tenants/{CHROMA_TENANT}/databases/{CHROMA_DATABASE}"
           f"/collections/{CHROMA_COLLECTION_ID}/{action}")
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read()
    return json.loads(body) if body else {}


def chroma_get(ids=None, where=None, include=("metadatas",)) -> dict:
    """Exact lookup: no embeddings, no ranking."""
    payload = {"include": list(include)}
    if ids is not None:
        payload["ids"] = list(ids)
    if where:
        payload["where"] = where
    return _chroma_request("get", payload)


def embed_query(text: str) -> list[float]:
    resp = _bedrock().invoke_model(
        modelId=EMBEDDING_MODEL_ID, contentType="application/json", accept="application/json",
        body=json.dumps({"inputText": text, "dimensions": EMBEDDING_DIMENSIONS, "normalize": True}))
    return json.loads(resp["body"].read())["embedding"]


def chroma_query(embedding, n_results, where=None,
                 include=("documents", "metadatas", "distances")) -> dict:
    """Similarity search with a query embedding from the same model the Lambda used."""
    payload = {"query_embeddings": [embedding], "n_results": n_results, "include": list(include)}
    if where:
        payload["where"] = where
    return _chroma_request("query", payload)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def term_type(term_id: str) -> str:
    return _TERM_CODES[term_id.split("-")[1].upper()][0]


def term_order(term_id: str) -> tuple[int, int]:
    year, code = term_id.split("-")
    return int(year), _TERM_CODES[code.upper()][1]


def _plain(obj):
    """DynamoDB returns every number as Decimal; turn them back into int/float."""
    if isinstance(obj, Decimal):
        return int(obj) if obj == obj.to_integral_value() else float(obj)
    if isinstance(obj, list):
        return [_plain(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _plain(v) for k, v in obj.items()}
    return obj


def _json(value, default):
    return json.loads(value) if value else default


def fetch_courses(course_ids) -> dict[str, dict]:
    """Exact lookup by course code. Missing codes are simply absent from the result."""
    ids = sorted(set(course_ids))
    if not ids:
        return {}
    res = chroma_get(ids=ids)
    out = {}
    for cid, md in zip(res["ids"], res["metadatas"]):
        if (md or {}).get("record_type") != "course":
            continue
        out[cid] = {
            "course_id": cid,
            "title": md.get("title", ""),
            "credits": int(md["credits"]),
            "prereqs": _json(md.get("prereqs"), []),
            "terms_offered": _json(md.get("terms_offered"), []),
            "sections": _json(md.get("sections"), {}),
        }
    return out


def fetch_program(program_id: str) -> dict:
    res = chroma_get(ids=[program_id])
    if not res["ids"] or (res["metadatas"][0] or {}).get("record_type") != "program":
        raise LookupError(f"No program {program_id!r} in the catalog")
    md = res["metadatas"][0]
    return {
        "program_id": program_id,
        "name": md.get("name", program_id),
        "total_credits": int(md["total_credits"]),
        "requirements": _json(md.get("requirements"), []),
    }


def fetch_student(student_id: str) -> dict:
    item = students_table().get_item(Key={"student_id": student_id}).get("Item")
    if not item:
        raise LookupError(f"No student with id {student_id!r}")
    s = _plain(item)
    s.setdefault("transcript", [])
    return s


def fetch_plan(student_id: str, plan_name: str) -> dict:
    item = plans_table().get_item(Key={"student_id": student_id, "plan_name": plan_name}).get("Item")
    if not item:
        raise LookupError(f"Student {student_id!r} has no plan named {plan_name!r}")
    return _plain(item)


def list_plan_names(student_id: str) -> list[str]:
    from boto3.dynamodb.conditions import Key
    names, kwargs = [], {"KeyConditionExpression": Key("student_id").eq(student_id),
                         "ProjectionExpression": "plan_name"}
    while True:
        page = plans_table().query(**kwargs)
        names += [i["plan_name"] for i in page.get("Items", [])]
        if "LastEvaluatedKey" not in page:
            return names
        kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]


def best_grades(transcript) -> dict[str, int]:
    """Best grade rank per course, so retakes count."""
    best: dict[str, int] = {}
    for t in transcript:
        rank = GRADE_RANK.get(t["grade"].upper(), -1)
        best[t["course_id"]] = max(rank, best.get(t["course_id"], -99))
    return best


def _overlaps(a, b) -> bool:
    return a["day"] == b["day"] and a["start"] < b["end"] and b["start"] < a["end"]


def _plan_course_ids(plan_terms) -> list[str]:
    return [c["course_id"] for t in plan_terms for c in t["courses"]]


# ---------------------------------------------------------------------------
# The cross-reference: student (DynamoDB) x catalog (Chroma) -> checks (a)-(f)
# ---------------------------------------------------------------------------

def validate_course(course_id, term_id, *, student, program, courses, plan_terms) -> dict:
    """
    Check one course for one term against the student's record and the plan so far.

    courses     dict from fetch_courses() covering this course, the transcript,
                and every course already in plan_terms
    plan_terms  [{"term_id", "courses": [{"course_id", "section"}]}], NOT including this course

    Courses planned in EARLIER terms count as completed for prerequisites.
    """
    errors, warnings = [], []
    course = courses.get(course_id)
    if course is None:
        return {"ok": False, "course_id": course_id, "term_id": term_id,
                "errors": [f"{course_id} is not in the course catalog (check the exact code)"],
                "warnings": [], "suggested_section": None}

    grades = best_grades(student["transcript"])
    t_type, t_order = term_type(term_id), term_order(term_id)
    earlier = {c["course_id"] for t in plan_terms
               if term_order(t["term_id"]) < t_order for c in t["courses"]}
    same_term = next((t["courses"] for t in plan_terms if t["term_id"] == term_id), [])

    # (a) prerequisites
    def satisfied(opt):
        if opt["course_id"] in earlier:
            return True
        need = GRADE_RANK.get((opt.get("min_grade") or "D").upper(), PASSING_RANK)
        return grades.get(opt["course_id"], -99) >= need

    missing = [" or ".join(o["course_id"] + (f" ({o['min_grade']} or better)" if o.get("min_grade") else "")
                           for o in group)
               for group in course["prereqs"] if not any(satisfied(o) for o in group)]
    if missing:
        errors.append("prerequisites not met: " + "; ".join(missing))

    # (b) already passed, or already in this plan. A D is passing but can be retaken,
    #     because many prerequisites require a C or better.
    best = grades.get(course_id, -99)
    if best >= GRADE_RANK["C"]:
        errors.append(f"already passed {course_id}")
    elif best >= PASSING_RANK:
        warnings.append(f"retake: the current grade in {course_id} is a D")
    for t in plan_terms:
        if any(c["course_id"] == course_id for c in t["courses"]):
            errors.append(f"{course_id} is already in this plan ({t['term_id']})")

    # (c) counts toward the degree
    groups = [g["name"] for g in program["requirements"] if course_id in g["courses"]]
    if not groups:
        errors.append(f"{course_id} does not count toward {program['name']}")

    # offered in this kind of term
    if course["terms_offered"] and t_type not in course["terms_offered"]:
        errors.append(f"{course_id} is not offered in {t_type} (offered: {', '.join(course['terms_offered'])})")

    # (d) schedule conflict: find a section that doesn't overlap the ones already chosen
    taken = []
    for item in same_term:
        other = courses.get(item["course_id"], {})
        for sec in other.get("sections", {}).get(term_id, []):
            if sec["section"] == item.get("section"):
                taken += [(item["course_id"], m) for m in sec["meetings"]]

    suggested = None
    sections = course["sections"].get(term_id, [])
    if not sections:
        warnings.append(f"no section times published for {term_id}; schedule conflict not checked")
    else:
        for sec in sections:
            if not any(_overlaps(m, tm) for m in sec["meetings"] for _, tm in taken):
                suggested = sec["section"]
                break
        if suggested is None:
            clashing = sorted({cid for cid, tm in taken
                               for sec in sections for m in sec["meetings"] if _overlaps(m, tm)})
            errors.append(f"schedule conflict: every {course_id} section overlaps {', '.join(clashing)}")

    # (e) semester credit limit
    term_credits = sum(courses[c["course_id"]]["credits"] for c in same_term)
    limit = MAX_TERM_CREDITS[t_type]
    if term_credits + course["credits"] > limit:
        errors.append(f"{term_id} would have {term_credits + course['credits']} credits (limit {limit})")

    # (f) total degree credits
    earned = sum(courses[cid]["credits"] for cid, r in grades.items()
                 if r >= PASSING_RANK and cid in courses)
    planned = sum(courses[cid]["credits"] for cid in _plan_course_ids(plan_terms))
    if earned + planned + course["credits"] > program["total_credits"]:
        errors.append(f"would exceed the {program['total_credits']}-credit degree total "
                      f"({earned} earned + {planned} planned + {course['credits']})")

    return {"ok": not errors, "course_id": course_id, "title": course["title"],
            "credits": course["credits"], "term_id": term_id, "counts_toward": groups,
            "suggested_section": suggested, "errors": errors, "warnings": warnings}


def _next_term(term_id: str, include_summer: bool) -> str:
    year, code = term_id.upper().split("-")
    year = int(year)
    if code == "SP":
        return f"{year}-SU" if include_summer else f"{year}-FA"
    if code == "SU":
        return f"{year}-FA"
    return f"{year + 1}-SP"


def _courses_still_needed(program, grades, courses, preferred) -> tuple[list[str], list[str]]:
    """
    Decide which courses the plan must cover.
    - A requirement group with no min_credits / min_courses means "take every course".
    - Otherwise pick electives until the minimum is met: the student's preferred
      courses first, then catalog order, skipping any whose prerequisites can't be
      reached inside this degree.
    Returns (course_ids, notes).
    """
    passed = {c for c, r in grades.items() if r >= PASSING_RANK}
    in_degree = {c for g in program["requirements"] for c in g["courses"]}
    reachable = lambda c: all(any(o["course_id"] in passed or o["course_id"] in in_degree for o in grp)
                              for grp in courses[c]["prereqs"])
    chosen, notes = [], []

    is_elective = lambda g: g.get("min_credits") is not None or g.get("min_courses") is not None
    for g in sorted(program["requirements"], key=is_elective):          # required groups first
        listed = [c for c in g["courses"] if c in courses]
        missing_from_catalog = [c for c in g["courses"] if c not in courses]
        if missing_from_catalog:
            notes.append(f"{g['name']}: not in course catalog, skipped: {', '.join(missing_from_catalog)}")

        if not is_elective(g):
            chosen += [c for c in listed if c not in passed and c not in chosen]
            continue

        credits_needed = (g.get("min_credits") or 0) - sum(courses[c]["credits"] for c in listed if c in passed)
        courses_needed = (g.get("min_courses") or 0) - sum(1 for c in listed if c in passed)
        order = [c for c in (preferred or []) if c in listed] + [c for c in listed if c not in (preferred or [])]
        for c in order:
            if credits_needed <= 0 and courses_needed <= 0:
                break
            if c in passed or c in chosen or not reachable(c):
                continue
            chosen.append(c)
            credits_needed -= courses[c]["credits"]
            courses_needed -= 1
        if credits_needed > 0 or courses_needed > 0:
            notes.append(f"{g['name']}: not enough eligible courses in the catalog to meet the minimum")

    # Retakes: a course still needed requires a minimum grade the student doesn't have yet
    # (e.g. a D in CSE 1320 when CSE 1325 needs a C), so the earlier course must be repeated.
    def grade_ok(opt):
        need = GRADE_RANK.get((opt.get("min_grade") or "D").upper(), PASSING_RANK)
        return grades.get(opt["course_id"], -99) >= need

    changed = True
    while changed:
        changed = False
        for c in list(chosen):
            for grp in courses[c]["prereqs"]:
                if any(o["course_id"] in chosen or grade_ok(o) for o in grp):
                    continue
                retake = next((o for o in grp if o["course_id"] in passed and o["course_id"] in courses), None)
                if retake:
                    chosen.append(retake["course_id"])
                    notes.append(f"{retake['course_id']}: retake needed, {c} requires "
                                 f"{retake.get('min_grade') or 'D'} or better")
                    changed = True
    return chosen, notes


def _unlock_counts(course_ids, courses) -> dict[str, int]:
    """How many still-needed courses depend on each course, directly or indirectly.
    Courses that unlock the most go first, so long prerequisite chains start early."""
    direct = {c: set() for c in course_ids}
    for c in course_ids:
        for grp in courses[c]["prereqs"]:
            for opt in grp:
                if opt["course_id"] in direct:
                    direct[opt["course_id"]].add(c)
    counts = {}
    for c in course_ids:
        seen, stack = set(), list(direct[c])
        while stack:
            d = stack.pop()
            if d not in seen:
                seen.add(d)
                stack += direct[d]
        counts[c] = len(seen)
    return counts


def _store_plan(student_id, plan_name, program_id, terms, total) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    # Creates the plan or replaces it; created_at is kept from the first save.
    plans_table().update_item(
        Key={"student_id": student_id, "plan_name": plan_name},
        UpdateExpression="SET #prog = :prog, #terms = :terms, #total = :total, "
                         "#upd = :now, #crt = if_not_exists(#crt, :now)",
        ExpressionAttributeNames={"#prog": "program_id", "#terms": "terms", "#total": "total_credits",
                                  "#upd": "updated_at", "#crt": "created_at"},
        ExpressionAttributeValues={":prog": program_id, ":terms": terms, ":total": total, ":now": now})


def _normalize_terms(terms) -> list[dict]:
    """Accept dicts or pydantic models; sort terms chronologically."""
    out = []
    for t in terms:
        t = t.model_dump() if hasattr(t, "model_dump") else dict(t)
        courses = [c.model_dump() if hasattr(c, "model_dump") else
                   ({"course_id": c} if isinstance(c, str) else dict(c)) for c in t["courses"]]
        out.append({"term_id": t["term_id"].upper(), "courses": courses})
    return sorted(out, key=lambda t: term_order(t["term_id"]))


# ---------------------------------------------------------------------------
# Tools the agent can call
# ---------------------------------------------------------------------------

class PlanCourse(BaseModel):
    course_id: str = Field(description='Exact course code, e.g. "CSE 3318"')
    section: Optional[str] = Field(None, description='Section number like "001", if chosen')


class PlanTerm(BaseModel):
    term_id: str = Field(description='Term like "2027-SP", "2027-SU", "2027-FA"')
    courses: list[PlanCourse]


@tool
def get_student_record(student_id: str) -> dict:
    """Get a student's major, transcript with grades, earned credits, and saved degree plan names.
    Use this for any question about what the student has taken or how far along they are."""
    try:
        s = fetch_student(student_id)
        courses = fetch_courses(t["course_id"] for t in s["transcript"])
        grades = best_grades(s["transcript"])
        earned = sum(courses[c]["credits"] for c, r in grades.items() if r >= PASSING_RANK and c in courses)
        plans = list_plan_names(student_id)
        return {"student_id": s["student_id"], "name": f"{s.get('first_name', '')} {s.get('last_name', '')}".strip(),
                "program_id": s["program_id"], "catalog_year": s.get("catalog_year"),
                "transcript": s["transcript"], "earned_credits": earned, "saved_plans": plans}
    except LookupError as e:
        return {"error": str(e)}


@tool
def get_course_details(course_ids: list[str]) -> dict:
    """Exact lookup of courses by code: title, credits, prerequisites, terms offered, sections.
    Always use this (not search_catalog) when you know the course code."""
    found = fetch_courses(course_ids)
    missing = sorted(set(course_ids) - set(found))
    return {"courses": list(found.values()), "not_found": missing}


@tool
def search_catalog(question: str, course_id: Optional[str] = None,
                   program_id: Optional[str] = None, k: int = 4) -> dict:
    """Semantic search over course descriptions and catalog/degree-requirement documents.
    Use for open-ended questions ("which courses cover machine learning?", "what is the
    policy on repeating a course?"). Pass course_id or program_id to restrict results."""
    conds = [{f: {"$eq": v}} for f, v in (("course_id", course_id), ("program_id", program_id)) if v]
    where = None if not conds else conds[0] if len(conds) == 1 else {"$and": conds}

    res = chroma_query(embed_query(question), n_results=k, where=where)
    hits = []
    for doc, md, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        md = md or {}
        hits.append({"distance": round(dist, 4), "record_type": md.get("record_type"),
                     "course_id": md.get("course_id"), "program_id": md.get("program_id"),
                     "source": md.get("source"), "page": md.get("page"), "text": doc})
    return {"results": hits}


@tool
def check_course_eligibility(student_id: str, course_id: str, term_id: str,
                             plan_name: Optional[str] = None,
                             program_id: Optional[str] = None) -> dict:
    """Check whether a student can take a course in a term: prerequisites, already passed,
    counts toward the degree, offered that term, schedule conflicts, semester credit limit,
    and total degree credits. Pass plan_name to check against a saved plan, and program_id
    to check against a different major (for "what if I switch majors" questions)."""
    try:
        student = fetch_student(student_id)
        plan_terms = fetch_plan(student_id, plan_name)["terms"] if plan_name else []
        program = fetch_program(program_id or student["program_id"])
        courses = fetch_courses([course_id, *(t["course_id"] for t in student["transcript"]),
                                 *_plan_course_ids(plan_terms)])
        return validate_course(course_id.upper(), term_id.upper(), student=student, program=program,
                               courses=courses, plan_terms=plan_terms)
    except LookupError as e:
        return {"error": str(e)}


@tool
def save_degree_plan(student_id: str, plan_name: str, terms: list[PlanTerm],
                     program_id: Optional[str] = None) -> dict:
    """Validate a multi-semester degree plan and save it if every course passes all checks.
    Saving with an existing plan_name replaces that plan. Nothing is saved if any course fails;
    the errors are returned so the plan can be fixed and saved again."""
    try:
        student = fetch_student(student_id)
        program = fetch_program(program_id or student["program_id"])
    except LookupError as e:
        return {"error": str(e)}

    proposed = _normalize_terms(terms)
    courses = fetch_courses([*(t["course_id"] for t in student["transcript"]),
                             *_plan_course_ids(proposed)])

    accepted, problems, warnings = [], [], []
    for term in proposed:
        accepted.append({"term_id": term["term_id"], "courses": []})
        for item in term["courses"]:
            result = validate_course(item["course_id"].upper(), term["term_id"], student=student,
                                     program=program, courses=courses, plan_terms=accepted)
            if result["ok"]:
                accepted[-1]["courses"].append({"course_id": result["course_id"],
                                                "section": item.get("section") or result["suggested_section"]})
                warnings += [f"{result['course_id']}: {w}" for w in result["warnings"]]
            else:
                problems.append({"course_id": item["course_id"], "term_id": term["term_id"],
                                 "errors": result["errors"]})

    if problems:
        return {"saved": False, "problems": problems}

    total = sum(courses[c["course_id"]]["credits"] for t in accepted for c in t["courses"])
    _store_plan(student_id, plan_name, program["program_id"], accepted, total)
    return {"saved": True, "plan_name": plan_name, "total_planned_credits": total,
            "terms": [{"term_id": t["term_id"],
                       "credits": sum(courses[c["course_id"]]["credits"] for c in t["courses"]),
                       "courses": t["courses"]} for t in accepted],
            "warnings": warnings}


@tool
def generate_degree_plan(student_id: str, start_term: str, max_credits_per_term: int = 15,
                         max_courses_per_term: Optional[int] = None, include_summer: bool = False,
                         preferred_electives: Optional[list[str]] = None,
                         program_id: Optional[str] = None, save_as: Optional[str] = None) -> dict:
    """Build a semester-by-semester plan to finish the student's degree, starting at start_term
    (e.g. "2027-SP"). Every course is checked with the same rules as check_course_eligibility.
    Use max_courses_per_term for requests like "only 3 classes a semester", include_summer to
    use summer terms, preferred_electives for electives the student wants, and program_id to
    plan for a different major. Pass save_as to save the result under that plan name."""
    try:
        student = fetch_student(student_id)
        program = fetch_program(program_id or student["program_id"])
    except LookupError as e:
        return {"error": str(e)}

    start_term = start_term.upper()
    courses = fetch_courses([*(c for g in program["requirements"] for c in g["courses"]),
                             *(t["course_id"] for t in student["transcript"]),
                             *(preferred_electives or [])])
    grades = best_grades(student["transcript"])
    remaining, notes = _courses_still_needed(program, grades, courses, preferred_electives)
    priority = _unlock_counts(remaining, courses)

    plan, last_errors, term, idle = [], {}, start_term, 0
    while remaining and len(plan) < 16 and idle < 3:        # idle = full year with no progress
        cap = min(max_credits_per_term, MAX_TERM_CREDITS[term_type(term)])
        plan.append({"term_id": term, "courses": []})
        credits = 0
        for cid in sorted(remaining, key=lambda c: (-priority[c], c)):
            if max_courses_per_term and len(plan[-1]["courses"]) >= max_courses_per_term:
                break
            if credits + courses[cid]["credits"] > cap:
                continue
            result = validate_course(cid, term, student=student, program=program,
                                     courses=courses, plan_terms=plan)
            if result["ok"]:
                plan[-1]["courses"].append({"course_id": cid, "section": result["suggested_section"]})
                credits += courses[cid]["credits"]
            else:
                last_errors[cid] = result["errors"]

        added = {c["course_id"] for c in plan[-1]["courses"]}
        if added:
            remaining, idle = [c for c in remaining if c not in added], 0
        else:
            plan.pop()
            idle += 1
        term = _next_term(term, include_summer)

    total = sum(courses[c["course_id"]]["credits"] for t in plan for c in t["courses"])
    out = {"program_id": program["program_id"], "start_term": start_term,
           "complete": not remaining, "last_term": plan[-1]["term_id"] if plan else None,
           "semesters": len(plan), "total_planned_credits": total,
           "terms": [{"term_id": t["term_id"],
                      "credits": sum(courses[c["course_id"]]["credits"] for c in t["courses"]),
                      "courses": t["courses"]} for t in plan],
           "could_not_schedule": {c: last_errors.get(c, ["never reached"]) for c in remaining},
           "notes": notes}
    if save_as:
        if remaining:
            out["saved"] = False
            out["save_note"] = "not saved: some required courses could not be scheduled"
        else:
            _store_plan(student_id, save_as, program["program_id"], plan, total)
            out["saved"], out["plan_name"] = True, save_as
    return out


@tool
def compare_degree_plans(student_id: str, plan_a: str, plan_b: str) -> dict:
    """Compare two saved degree plans side by side: last term, number of semesters,
    credits per semester, and which courses are only in one plan."""
    try:
        plans = {name: fetch_plan(student_id, name) for name in (plan_a, plan_b)}
    except LookupError as e:
        return {"error": str(e)}
    courses = fetch_courses(cid for p in plans.values() for cid in _plan_course_ids(p["terms"]))

    def summary(p):
        terms = sorted(p["terms"], key=lambda t: term_order(t["term_id"]))
        return {"program_id": p["program_id"], "semesters": len(terms),
                "last_term": terms[-1]["term_id"] if terms else None,
                "total_credits": p.get("total_credits"),
                "credits_per_term": {t["term_id"]: sum(courses[c["course_id"]]["credits"]
                                                       for c in t["courses"] if c["course_id"] in courses)
                                     for t in terms}}

    a_ids, b_ids = (set(_plan_course_ids(plans[n]["terms"])) for n in (plan_a, plan_b))
    return {plan_a: summary(plans[plan_a]), plan_b: summary(plans[plan_b]),
            f"only_in_{plan_a}": sorted(a_ids - b_ids), f"only_in_{plan_b}": sorted(b_ids - a_ids)}


ALL_TOOLS = [get_student_record, get_course_details, search_catalog, check_course_eligibility,
             generate_degree_plan, save_degree_plan, compare_degree_plans]
