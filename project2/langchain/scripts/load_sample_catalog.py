"""
Load the SAMPLE catalog (seed/sample_catalog/*.json) straight into the team's Chroma collection,
so the advisor routes can be tested before the real catalog goes through the GitHub -> S3 -> Lambda
pipeline. Records are written exactly the way the ingestion Lambda writes courses.json / programs.json.

Run from the langchain/ folder with the same environment as the app (.env):

    python scripts/load_sample_catalog.py            # load / refresh the sample records
    python scripts/load_sample_catalog.py --remove   # delete only the sample records

The sample data is NOT verified against the UTA catalog. When the real courses.json is pushed
through the pipeline, the Lambda replaces these records (and removes sample courses that are not
in the real file).
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.advisor_tools import _chroma_request, chroma_get, embed_query  # noqa: E402

SEED_DIR = Path(__file__).resolve().parents[1] / "seed" / "sample_catalog"
SOURCE = "seed/sample_catalog"


def course_records(courses):
    return (
        [c["course_id"] for c in courses],
        [f"{c['course_id']} {c['title']}. {c.get('description', '')}".strip() for c in courses],
        [{"record_type": "course", "course_id": c["course_id"], "title": c["title"], "credits": c["credits"],
          "prereqs": json.dumps(c.get("prereqs", [])), "terms_offered": json.dumps(c.get("terms_offered", [])),
          "sections": json.dumps(c.get("sections", {})), "source": f"{SOURCE}/courses.json"} for c in courses],
    )


def program_records(programs):
    return (
        [p["program_id"] for p in programs],
        [f"{p['name']} ({p['program_id']}). {p.get('overview', '')}".strip() for p in programs],
        [{"record_type": "program", "program_id": p["program_id"], "name": p["name"],
          "total_credits": p["total_credits"], "requirements": json.dumps(p.get("requirements", [])),
          "source": f"{SOURCE}/programs.json"} for p in programs],
    )


def check(courses, programs):
    ids = {c["course_id"] for c in courses}
    problems = [f"{c['course_id']}: prereq {o['course_id']} missing"
                for c in courses for g in c.get("prereqs", []) for o in g if o["course_id"] not in ids]
    problems += [f"{p['program_id']}: {cid} missing"
                 for p in programs for g in p["requirements"] for cid in g["courses"] if cid not in ids]
    problems += [f"{c['course_id']}: credits must be an int" for c in courses if not isinstance(c["credits"], int)]
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--remove", action="store_true", help="delete the sample records instead of loading them")
    args = ap.parse_args()

    if args.remove:
        ids = []
        for name in ("courses.json", "programs.json"):
            ids += chroma_get(where={"source": f"{SOURCE}/{name}"})["ids"]
        if ids:
            _chroma_request("delete", {"ids": ids})
        print(f"removed {len(ids)} sample records")
        return

    courses = json.loads((SEED_DIR / "courses.json").read_text())
    programs = json.loads((SEED_DIR / "programs.json").read_text())
    problems = check(courses, programs)
    if problems:
        sys.exit("sample catalog has problems:\n  " + "\n  ".join(problems))

    for label, (ids, docs, metas) in (("courses", course_records(courses)), ("programs", program_records(programs))):
        _chroma_request("upsert", {"ids": ids, "documents": docs, "metadatas": metas,
                                   "embeddings": [embed_query(d) for d in docs]})
        print(f"loaded {len(ids)} {label}: {', '.join(ids)}")


if __name__ == "__main__":
    main()
