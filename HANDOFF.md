# Handoff: Team Project 1, Identification Prompt Optimization

Paste or attach this file at the start of a new chat to continue the work. Written 2026-09-27.

---

## What this project is

CSE 4392/5320, Team Project 1: Evolutionary Prompt Optimization, due 09/27/2026. I (Joseph) am iterating on a single LLM prompt that extracts "domain phrases" from a business description, following the Agile Unified Methodology's phrase-identification step. The prompt must reach **mean F1 >= 0.97 over 3 runs on all three domains** with one prompt version.

There are two activities in the assignment. **Only identification has been worked on so far.** Classification (classes, attributes, relationships, association classes) has not started.

Three domains:

| Domain | Description input | Identification ground truth |
|---|---|---|
| Library | (short library description) | `Library-domain-phrases-1.docx` |
| NTSS (trade shows) | `ntss-underlined-1.doc` body text | the underlined phrases in that same file |
| Car rental | (car rental description) | Brainstorming List column of `4392-crclassified.doc` |

Nine rule numbers: 1 Nouns, 2 X of Y, 3 Transitive verbs, 4 Adjectives/enumeration, 5 Numeric/quantity, 6 Possession, 7 Consist of/part of, 8 (unused), 9 X is a Y.

---

## Files to attach in the new chat

I have these locally. Ask me for whichever ones the task needs.

**Scoring kit** (`tp1_scoring_kit.zip`, unzipped on my Mac at `~/Downloads/tp1_scoring_kit/`):
- `scoring/score_rulesets.py` — CLI scorer, the one I run
- `scoring/scoring_modes.py` — rulesets A–D
- `scoring/score_identification.py` — normalization and ground truth loading
- `scoring/SCORING_RULESETS.md` — explains all four rulesets and how to run them
- `ground_truth/LIB_identification.json`, `NTSS_identification.json`, `CAR_identification.json`
- `runs/` — saved LLM responses

**Prompts**: `domain_phrase_prompt_v5.md`, `v5.1.md`, `v5.2.md`, `v5.3.md`

**Logs**: `run_log.md`, `change_log.md`, `decisions_log.md`, and `team_project1_run_protocol__1_.md` (the team's frozen rules document)

**Source files**: `Library-domain-phrases-1.docx`, `ntss-underlined-1.doc`, `ntss-classified-1.doc`, `4392-crclassified.doc`

---

## How to score a run

I paste the LLM's answer into a text file and run, from inside `scoring/`:

```bash
python score_rulesets.py ../ground_truth/NTSS_identification.json ../runs/myrun.txt
```

Defaults to rulesets B, C, D. `--ruleset all` adds A; `--ruleset D` or `--ruleset BD` picks specific ones. **Include the `.txt` extension** — I have forgotten it and gotten a `FileNotFoundError`.

Check the "phrases parsed" count in the output. If it is far below the number of phrases in the answer, the parser missed the headers.

### The four rulesets

All normalize both sides first: lowercase, collapse spaces, strip leading a/an/the and trailing punctuation, plurals to singular, verbs to base form, `author(s)` to `author`, hyphen = space.

| | Match type | Categories | Status |
|---|---|---|---|
| A | Exact only | Ignored | Reference only |
| **B** | Containment (GT inside output) | **Required** | Active, the one I usually quote |
| C | Exact, then containment | Ignored | Active |
| D | Exact, then containment for rules 6/7/9 only, one-to-one | Ignored | Active |

**The professor approved containment matching**, which is why A is no longer primary. The team has **not yet chosen** which of B, C, or D is the official score for pass/fail decisions — that is an open decision.

---

## Current state

### Prompt lineage

v5 is the stable baseline. v5.2 added a relevance filter and a proper-name rule. v5.3 (newest, **not yet run**) fixed three categories that regressed in v5.2.

### Scores, Ruleset B

| Prompt | Library | NTSS | Car rental |
|---|---|---|---|
| **v5** | **0.936** (3 runs, spread 0.005) | **0.692** (4 runs, 0.637–0.721) | **0.408** (1 run) |
| v5.2 | not run | **0.729** (4 runs, 0.689–0.772) | not run |
| v5.3 | not run | not run | not run |

v5 library per-category best: Nouns 0.961, X of Y 0.889, Verbs 0.970, Adjectives 0.889, Numeric 1.000, Possession 1.000, Consist of 1.000, X is a Y 1.000.

v5.2 vs v5 on NTSS, per category: Consist of 0.00 → 0.43, Numeric 0.22 → 0.44, Nouns 0.83 → 0.88, Adjectives 0.56 → 0.61, X is a Y 0.46 → 0.54, Possession 0.90 flat, Verbs 0.67 → 0.65, **X of Y 0.40 → 0.31**.

### What v5.2 changed (vs v5)

1. Rule 5: extract only what would become a class, attribute, attribute value, or relationship; skip background/motivation and generic words.
2. Rule 6: no proper names of instances (company, brand, venue, city, street, person), except the organization the document describes.
3. X of Y must literally contain "of".
4. Linking words spelled out and kept out of Verbs (has/have; consists of/involves/includes/including/comprises/contains; is a/types of/is known as/can be regarded as).
5. Numeric excludes dates, addresses, postal codes, identifiers.

### What v5.3 changed (vs v5.2)

1. **X of Y tightened**: exactly `<noun> of <noun phrase>`; no other prepositions; never join two phrases with "and"; work one "of" at a time and do not rephrase a sentence into "of" shape.
2. **Verbs**: keep prepositions that belong to the verb ("applied for", "signed off by"); exclude only the linking word itself, not the other verbs in the same sentence.
3. **Numeric rewritten**: the "how many / how much" test leads the category; distributive quantifiers (each, every, all) included explicitly; dates and addresses excluded with reasoning; keep quantity expressions whole.

---

## The single most important next step

**Run v5.3 on library, 3 times.** Rules 5 and 6 are precision filters, and library's ground truth rewards extracting nearly everything, so library is where a regression is most likely. v5.2 has never been run on library either.

If library drops more than about 0.02 from v5's 0.936, narrow the relevance filter instead of keeping it. Then run v5.3 on NTSS (beat 0.729) and car rental (beat 0.408).

**Always 3 runs per version per domain, then average.** Single runs have swung by 0.07 on NTSS. Library is stable at 0.005 spread; NTSS is not.

---

## Known open problems

### 1. The three ground truths conflict with each other

This is the biggest finding and probably a presentation slide.

| Convention | Library | NTSS | Car rental |
|---|---|---|---|
| Rule 6 Possession | fragment: *has a title language* | linking word only: *has* | none marked |
| Rule 7 Consist of | *made up of* | *involves*, *including* | none marked |
| Rule 9 X is a Y | statement: *customer is known as a member* | *can be regarded as* | none marked |
| Verbs with prepositions | bare: *borrow*, *extend* | *attended by*, *belong to* | *taken from*, *returned to* |
| Value lists | *8 / maximum of 8* | one span: *large, medium, or small* | split: *two*, *four* |
| How selective | nearly everything relevant | nearly everything relevant | **curated**: only what reaches the model |

The selectivity row is the one no matching rule can fix. Library and NTSS reward extracting everything that fits a rule; car rental rewards extracting only what ends up in the domain model. *a number of* is a TP on library and an FP on car rental. **Under any matching rule, one prompt probably cannot hit 0.97 on all three.**

**Open question for the professor:** which convention should the prompt follow for selectivity? That one answer caused 69 of car rental's false positives.

### 2. Car rental is far behind

0.408, and 74 of its ~96 FPs are phrases the Brainstorming List simply does not include (*job market*, *labor cost*, *Toyota*, *Corolla*, *tax purposes*). Rules 5 and 6 in v5.2/v5.3 target exactly this but have not been tested there yet.

### 3. The word map is incomplete

`WORD_MAP` in `score_identification.py` only has library's plurals and verb forms. **Car rental and NTSS scores are understated** because *vehicles*/*vehicle*, *manufacturers*/*manufacturer*, *pays*/*pay* etc. do not match. Adding ~20 car rental forms would raise that run from 0.384 to about 0.48 under Ruleset A. This is allowed under protocol normalization rules 4–5 but should be logged.

### 4. Ground truth judgment calls to ask the instructor about

Recurring errors that are probably annotator choices, not prompt failures:
- Library FPs in every run: *facility*, *support*, *current*
- Library FN in every run: *book bar code*
- Whether *unique* counts as an enumeration value
- Car rental: does "(not used)" next to *file cabinet* remove it from the ground truth? (I assumed no — it refers to the classification step.)

**Do not add prompt rules for these** unless the instructor gives a general reason.

---

## Rules for how to work on this

These matter. Several were learned the hard way.

1. **No test leakage.** Never put a phrase, sentence, or example from the library, NTSS, or car rental descriptions into the prompt. All examples must come from an unrelated domain (v5.3 uses a hotel and a hospital ward). An earlier version, v02, quoted library phrases and had to be excluded from all decisions. I also caught leakage in a draft of v5.3 itself, so check every new rule's examples.
2. **Distinguish leakage from overfitting.** Even a rule with no test wording can be test-tuned. The test: would you have written this rule from the course methodology alone, before seeing the ground truth? If not, log it with the dev error that motivated it. The linking-word list naming *involves* and *includes* is one of these — defensible as standard aggregation markers, but check the course slides for the part-of indicator list and cite that.
3. **Library is a dev set, not a test set.** Its ground truth has shaped many prompt rules. Report its score as a dev score.
4. **One kind of change per version** where possible. v5.2 bundled five changes, which makes attribution hard.
5. **The script score decides**, not an LLM's own arithmetic (protocol Section 5.2). LLMs miscount TP/FP/FN.
6. **Deliver prompts as attached `.md` files, not pasted.** Pasting into a chat window strips `<...>` placeholders and adds `&#x20;` and backslash escapes that compound with each copy. This corrupted several early runs.
7. **Fresh chat per run**, default settings, memory and custom instructions off, and never in a project containing ground truth files (protocol Section 2). This was **not verified** for the earliest logged runs.
8. Record the exact model and version in the run log. It is still marked **TBD** for every logged run.

---

## Scoring gotchas already fixed (do not re-break)

- The parser accepts bullets (`-`, `*`, `•`), bare phrase lines with no marker, numbered lists, flat `PHRASES:` lists, `<answer>` tags, and a header with items collapsed onto one line. It drops the `<analysis>` block so its rows are not read as phrases.
- All divisions are guarded; a file that parses to zero phrases prints a message instead of a `ZeroDivisionError`.
- All three ground truth JSONs use rule-number category names (1–9, with an empty rule 8). A mismatch here once caused a `KeyError` crash in Ruleset B and a silent wrong score in Ruleset D.
- Alternates split only on a spaced `" / "`, so *invited and/or selected* stays whole.
- All three ground truth JSONs were verified complete against their source documents with a script.

---

## A scoring prompt a teammate proposed

A teammate wrote a strict LLM-executed scoring prompt (exact match, rule numbers must match, comma-split ground truth, one-to-one, with TP+FP and TP+FN checks). I reviewed it: the safeguards are good, but as written it forbids containment (reversing the professor's decision), splits commas on only one side, and scores v5 library at 0.74. If the team wants it, it should be implemented as code (Ruleset E) rather than run by an LLM.

---

## What to ask me at the start of a new chat

If the task is unclear, ask me:
1. Which domain and which prompt version am I running?
2. Has the team chosen B, C, or D as the primary ruleset?
3. Any answer back from the professor or GTA on the selectivity question or the judgment calls?
