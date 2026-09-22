# Team Project 1: Run Protocol and Scoring Rules

CSE 4392/5320, Evolutionary Prompt Optimization (due 09/27/2026)

This document sets the rules every team member follows so that all runs and scores are comparable. **Freeze it before Round 1.** If a rule changes later, every logged run must be rescored under the new rule.

---

## 0. Team Decisions to Make Before Round 1

The rest of this document uses the **default** shown for each item. Change the default, record the decision in the decisions log (Section 7.3), and update the affected section before anyone starts running prompts.

### 0.1 Setup and logistics

| # | Decision | Default in this doc | Why it matters |
|---|---|---|---|
| 1 | Which LLM and version? Chat UI or API? | One model, recorded in the log (Section 2) | Scores are only comparable within one model. |
| 2 | Temperature (API only) | 0 | Lower temperature reduces run-to-run variation. |
| 3 | Where do the shared folder and logs live (Drive, GitHub, etc.)? | Layout in Section 8 | Everyone needs the same description text and ground truth. |
| 4 | Who writes the scoring script, and in what language? | Not assigned | Everything else depends on it, so it should be done first. |
| 5 | Internal deadlines for each phase | Not set | The due date is 09/27, and CoT and the PPT come last. |
| 6 | Who owns the prompt in each phase, and who owns each domain? | Rotate the prompt owner between phases (Section 1) | It gives two people prompt ownership. |

### 0.2 Run procedure

| # | Decision | Default in this doc | Why it matters |
|---|---|---|---|
| 7 | Runs per prompt version per domain | 3 | More runs give fairer comparisons but take more time. |
| 8 | Pass criterion: the mean of the runs, or every single run? | Mean of 3 runs ≥ 0.97 | "Every run" is stricter and may be hard to reach. |
| 9 | Do all 5 members write candidates for **both** rounds? | Yes (Section 3) | It doubles the candidate work. |
| 10 | Tie-break margin on library | Within 1 F1 point of the top score | It decides how many finalists go on to car rental and NTSS. |
| 11 | During classification, is the input the ground truth phrase list or the winning identification prompt's output? | Ground truth phrase list (Section 3, rule 4) | Using the ground truth list isolates classification quality; using the prompt's output is closer to the real pipeline. |
| 12 | Which classification responses are submitted: the ones from the ground truth list or from the identification output? | Not decided | The assignment asks for classification responses for all three domains, so state which input you used. |
| 13 | Are examples from outside the three domains allowed in prompts (few-shot)? Which ones? | Allowed, but none from library, car rental, or NTSS (Section 4, rule 4) | Examples from the three domains would inflate the scores. |
| 14 | Which LLM responses are submitted: every run, or only the final version's runs? | Final version's runs, with the full log available | The assignment asks for responses and F1 scores, and the full log backs up the PPT. |
| 15 | CoT: is it one prompt in one call, and does it also have to reach 97%? | One prompt, one call; scores recorded, with no iteration required | Step 9 only asks you to test the CoT prompt and save the results. |
| 16 | CoT scoring: report identification and classification F1 separately? | Yes, both | A CoT response contains both activities. |

### 0.3 Scoring

| # | Decision | Default in this doc | Why it matters |
|---|---|---|---|
| 17 | Identification: score the unique phrase set, or phrases per rule category? | Unique set; per-category recall is diagnostic only (Section 5.4) | Library's ground truth lists some phrases under more than one category. |
| 18 | Match strictness: exact after normalization, or partial overlaps allowed? | Exact after normalization (Section 5.4) | Partial matching raises scores but is harder to defend. |
| 19 | Contents of the equivalence list | Empty, except hyphen = space | Every entry you add raises scores, so agree on them up front. |
| 20 | Normalization: done by hand, or with a lemmatizer (for example, spaCy or NLTK)? | Not decided | Lemmatizers sometimes make mistakes; hand normalization is slower. |
| 21 | Association verb label: ignored or required? | Ignored, unless two associations connect the same pair (Section 5.5) | Verb synonyms (has, owns, holds) would otherwise count as misses. |
| 22 | Classification F1: micro (pooled) or macro (averaged across the four categories)? | Micro as primary, per-category as diagnostic (Section 5.5) | Macro weights association classes, which have very few items, as heavily as attributes. |
| 23 | Are association classes also counted on the class list? | Follow each ground truth file's structure (Section 5.5) | Library's class sheet does not include `loan transaction`, but its attribute sheet does. |
| 24 | Wrong-class attribute or wrong relationship type: 1 FP + 1 FN, or partial credit? | 1 FP + 1 FN (Section 5.5) | This is the standard, strict way to count. |
| 25 | Which F1 is official: the script's or the LLM's? | Script for decisions; both are logged and reported (Section 5.2) | The assignment requires the LLM's F1, but LLM arithmetic can be wrong. |
| 26 | What to do if the team disagrees with an instructor answer | Leave the ground truth unchanged and log it as a finding (Section 5.6) | Editing the ground truth undermines the scores. |

### 0.4 Questions to confirm with the GTA

- Is **one** identification prompt and **one** classification prompt expected to work across all three domains, or a separate prompt per domain?
- How strict should phrase matching be (plurals, synonyms, partial matches)?
- Should the reported F1 be the LLM's calculation, or may you report a script-verified score alongside it?
- For the classification activity, may the input include a fixed phrase list, or must it start from the description alone?

---

## 1. Overall Workflow

1. **Identification round.** All five members write a candidate identification prompt, test it on library, and the team picks a winner.
2. **Identification iteration.** Improve the winner until it scores F1 ≥ 97% on library, car rental, and NTSS (assignment steps 3–8).
3. **Classification round.** All five members write a candidate classification prompt, test it on library, and the team picks a winner.
4. **Classification iteration.** Improve the winner until it scores F1 ≥ 97% on all three domains.
5. **CoT.** Merge the two final prompts into one Chain-of-Thought prompt and run it on all three domains (step 9).
6. **PPT.** Build the presentation from the run log and change log (step 10).

During the iteration phases (steps 2 and 4), one person owns and edits the shared prompt. Each other member owns one domain: they run the prompt, score it, and report misses. Rotate the prompt owner between the identification and classification phases.

---

## 2. Fixed Run Setup (applies to every run)

| Setting | Rule |
|---|---|
| **Model** | One LLM for the entire project. Record the exact model name and version in the log. |
| **Settings** | If using an API, fix the temperature (0 recommended) and record it. If using a chat UI, record that default settings were used. |
| **Fresh context** | Start a new chat for every run. Never run two domains or two prompt versions in the same chat. |
| **No leakage** | Turn off memory and custom instructions. Never run inside a workspace or project that contains ground truth files. The LLM must not be able to see the answers. |
| **Input text** | Use the official description files only, pasted exactly as given. Everyone uses the same copy (store it in the shared folder). |
| **Output format** | Every prompt must require the output format in Section 6 so scoring is mechanical. |
| **Save everything** | Save the full prompt, the full LLM response, and the scores for every run, including failed and losing runs. |

### Naming convention

`<ACTIVITY>-v<version>-<DOMAIN>-r<run>`, for example `ID-v03-NTSS-r2` or `CL-cand-Joseph-LIB-r1`

- ACTIVITY: `ID` (identification), `CL` (classification), `COT`
- DOMAIN: `LIB`, `CAR`, `NTSS`
- Candidate prompts use `cand-<name>` in place of a version number.

---

## 3. Candidate Round Rules

1. **Write independently.** Each member writes their v1 prompt without seeing the others' prompts, to get genuinely different approaches. Set a shared deadline.
2. **Same inputs.** All candidates run on the same library text under the Section 2 setup.
3. **Three runs each.** Run every candidate **3 times** on library. Rank candidates by **mean F1** across the three runs, not by their best run.
4. **Classification input is fixed.** In the classification round, every candidate receives the library description **plus the same fixed phrase list**: the library ground truth phrases by default. This isolates classification quality from identification errors. (The CoT step later tests the full pipeline.)
5. **Tie-break.** If two or more candidates score within 1 F1 point of the top score on library, or all reach ≥ 97%:
   1. Run each finalist 3 times on car rental and on NTSS.
   2. Pick the finalist with the highest **minimum** mean F1 across the three domains.
   3. If still tied, pick the higher average across the three domains.
   4. If still tied, pick the shorter and simpler prompt.
6. **Crossover.** After choosing the winner, compare each losing candidate's results by category (for example, recall on "X is a Y" phrases, or on association classes). When a loser clearly beats the winner in a category, merge that rule into the winner as a new version. Keep the merge only if it passes the regression check in Section 4.
7. **Keep the losers.** Archive every candidate prompt and its scores for the presentation.

---

## 4. Iteration Rules (after a winner is chosen)

1. **Order.** Iterate on library until it passes, then run car rental and NTSS (assignment steps 4–8).
2. **Pass criterion.** A prompt version passes a domain when its **mean F1 over 3 runs is ≥ 0.97**.
3. **Done criterion.** One single prompt version passes all three domains.
4. **Fix general rules only.** When the prompt misses a phrase, fix the *methodology rule* that should have caught it. **Never** paste phrases, classes, or example sentences from the library, car rental, or NTSS descriptions into the prompt. Examples from other domains (such as the course slides' overseas-exchange example) are allowed.
5. **One kind of change per version.** Where possible, change one thing per version so you know what caused a score change.
6. **Change log entry.** Each new version records what changed, which misses it targets, and the resulting scores.
7. **Regression check.** After any change, rerun **every domain that previously passed**. A change that fixes NTSS but drops library below 97% is not accepted.
8. **Honest reporting.** Report the mean of all runs for the final version. Do not submit only the best run.

---

## 5. Scoring Rules

### 5.1 Definitions

- **TP (true positive):** an item in the LLM output that matches a ground truth item
- **FP (false positive):** an item in the LLM output with no ground truth match
- **FN (false negative):** a ground truth item with no match in the LLM output

```
Precision = TP / (TP + FP)
Recall    = TP / (TP + FN)
F1        = 2 × Precision × Recall / (Precision + Recall)
```

### 5.2 Who computes F1

- The assignment requires prompting the LLM to compute F1, so do that and record the LLM's number.
- Also compute F1 with the team's scoring script. LLMs often miscount TP, FP, and FN.
- **Use the script's score for all decisions** (pass/fail, ranking). Log both numbers, and note any mismatch. Mismatches are worth a slide.

### 5.3 Normalization (applied to both LLM output and ground truth before matching)

1. Lowercase everything.
2. Trim whitespace and collapse repeated spaces.
3. Remove leading articles (`a`, `an`, `the`) and trailing punctuation.
4. Reduce plural nouns to singular (`loan items` → `loan item`).
5. Reduce verbs to their base form (`issues`, `issued` → `issue`).
6. Treat optional plurals like `author(s)` as the base form (`author`).
7. Treat hyphens and spaces as the same (`bar-code` = `bar code`).

### 5.4 Identification matching

1. **Match on the normalized phrase, exactly.** Partial overlaps do not count (`library member` does not match `member`).
2. **Slash alternates are one item.** A ground truth entry like `customers / customer` or `member number / membership number` is one item, and either form matches it. Matching both forms still counts as **one** TP.
3. **Duplicates collapse.** If the LLM lists the same normalized phrase twice, it counts once.
4. **Score the unique phrase set.** A phrase listed under several rule categories in the ground truth (for example, `date of birth` under both nouns and "X of Y") counts once. The primary F1 ignores categories.
5. **Per-category recall (diagnostic only).** Also report recall per rule category (1–9) to find weak rules. For NTSS, use the superscripts in `ntss-underlined-1.doc`. This does not change the primary F1.
6. **Equivalence list.** Any extra equivalents the team accepts (for example, `barcode` = `bar code`) go in a shared equivalence list, decided **before** Round 1. Adding an entry mid-project means rescoring every logged run.

### 5.5 Classification matching

Score four categories, and pool their TP, FP, and FN into one **micro-averaged F1** as the primary score. Report each category's F1 separately as a diagnostic.

| Category | An item matches when… |
|---|---|
| **Classes** | The normalized class name matches. |
| **Attributes** | Both the class and the attribute match (`customer.name`). An attribute placed on the wrong class counts as **one FP and one FN**. |
| **Relationships** | The relationship type matches **and** both endpoints match (see direction rules below). |
| **Association classes** | The name matches **and** both associated classes match, in either order. |

**Relationship direction rules**

- `as(label, A, B)` (association): endpoints match in **either order**. The verb label is **ignored**, unless the ground truth has two associations between the same pair of classes; then the label must match the corresponding one.
- `isa(child, parent)` (inheritance): order **matters**.
- `ag(whole, part)` (aggregation): order **matters**.
- The wrong type (for example, `as` where the ground truth has `ag`) counts as one FP and one FN.

**Association classes also count as classes** only if they appear on the ground truth class sheet. Follow the ground truth file's structure for each domain.

### 5.6 Ground truth files

Convert all ground truth into the library spreadsheet's format so one script scores all three domains.

| Domain | Identification ground truth | Classification ground truth |
|---|---|---|
| Library | `Library-domain-phrases-1.docx` | `library-expert-1.xlsx` |
| Car rental | `4392-crclassified.doc` (phrase section) | `4392-crclassified.doc` (classification section) |
| NTSS | `ntss-underlined-1.doc` | `ntss-classified-1.doc` |

Once converted, the ground truth files are **read-only**. If the team disagrees with an instructor answer, log it as a finding for the PPT but do not edit the file.

### 5.7 Adjudication

If a match is genuinely unclear under these rules, two members decide together, and the decision goes into the equivalence list or the decisions log so the same call applies to every run.

---

## 6. Required LLM Output Format

Every prompt must instruct the LLM to answer in exactly this format.

**Identification**

```
PHRASES:
- <phrase>
- <phrase>
```

The LLM may additionally group phrases by rule number 1–9, but it must still give one flat list.

**Classification**

```
CLASSES:
- <class>
ATTRIBUTES:
- <class>.<attribute>
RELATIONSHIPS:
- as(<label>, <classA>, <classB>)
- isa(<child>, <parent>)
- ag(<whole>, <part>)
ASSOCIATION CLASSES:
- <name>(<classA>, <classB>)
```

---

## 7. Logs

### 7.1 Run log (one row per run)

| Run ID | Date | Member | Model | Prompt version | Domain | TP | FP | FN | Precision | Recall | F1 (script) | F1 (LLM) | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ID-v01-LIB-r1 | | | | | | | | | | | | | |

### 7.2 Change log (one row per prompt version)

| Version | Owner | What changed | Targeted misses | LIB mean F1 | CAR mean F1 | NTSS mean F1 | Accepted? |
|---|---|---|---|---|---|---|---|
| ID-v02 | | | | | | | |

### 7.3 Decisions log

| Date | Question | Decision | Decided by |
|---|---|---|---|
| | | | |

---

## 8. Shared Folder Layout

```
/descriptions        official library, car rental, NTSS text
/ground_truth        converted ground truth files (read-only)
/prompts
    /identification  candidates + every version
    /classification  candidates + every version
    /cot
/runs                full LLM responses, named by Run ID
/scoring             scoring script + equivalence list
/logs                run log, change log, decisions log
/ppt
```
