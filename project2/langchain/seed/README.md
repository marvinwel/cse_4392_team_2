# Seed data for testing the advisor

Everything in this folder is **fictional test data**.

| File | What it is | Loaded with |
|---|---|---|
| `students.json` | 8 fictional students (profile + transcript) | `python scripts/dynamo_setup.py --seed seed/students.json` |
| `sample_catalog/courses.json` | 24 sample courses with credits, prerequisites, terms offered, and a few spring 2027 sections | `python scripts/load_sample_catalog.py` |
| `sample_catalog/programs.json` | 2 sample degree programs (BS-CS, BS-SE) | same script |

**The sample catalog is NOT verified against the UTA catalog.** Course codes and titles look like UTA's,
but prerequisites, terms offered, and requirement lists were made up so every advisor feature can be
exercised. Do not push these files into the `docs/` folder that feeds the RAG pipeline. When the real
`courses.json` / `programs.json` go through the pipeline, the Lambda replaces these records.
To remove them sooner: `python scripts/load_sample_catalog.py --remove`.

## The students

| ID | Name | Program | Scenario | Good test questions |
|---|---|---|---|---|
| 1002000101 | Maya Okafor | BS-CS | First-semester freshman, nothing completed | "Make me a degree plan starting spring 2027" |
| 1002000102 | Diego Ramirez | BS-CS | Sophomore on track | "Can I take CSE 1325 next spring?" |
| 1002000103 | Priya Natarajan | BS-CS | Junior with strong grades | "Can I take CSE 3320 and CSE 3318 in spring?" / "Plan the rest of my degree" |
| 1002000104 | Jordan Lee | BS-CS | D in CSE 1320 blocks CSE 1325 / CSE 2312 (need C) | "Can I take CSE 1325?" (no: needs a C in 1320) / "Make me a plan" (includes the retake) |
| 1002000105 | Aisha Rahman | BS-SE | Senior: needs Senior Design II + one elective | "What do I have left?" / "Plan my last semester" |
| 1002000106 | Ethan Brooks | BS-CS | Failed CSE 3318, passed the retake; W in MATH 3330 | "What's my transcript?" / "Can I take CSE 4303?" (needs MATH 3330) |
| 1002000107 | Sofia Martinez | BS-SE | Switched from BS-CS to BS-SE | "What if I switched back to computer science?" |
| 1002000108 | Kenji Watanabe | BS-CS | Part-time, takes summers | "Plan with 2 classes a semester including summers" |

Spring 2027 sections (days and times) exist for CSE 2312, 3310, 3318, 3320, and 4308, so plans that
include those courses in spring 2027 show a section number and are checked for time conflicts. Other
terms have no published sections, so plans for them note that conflicts weren't checked.
