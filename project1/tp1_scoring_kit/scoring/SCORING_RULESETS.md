# Identification Scoring Rulesets (A–D)

Four ways to score an LLM's identification output against a ground truth file. **Ruleset A is the official protocol score** used for all decisions. B, C, and D are for comparison; D is the version proposed for team and GTA approval.

## How to run

You need Python 3 and the `scoring/` and `ground_truth/` folders from the team kit. No extra packages.

1. Save the LLM's answer as a plain text file, e.g. `ID-v05-LIB-r1.txt`. Paste it as-is. The script understands:
   - category headers followed by `- phrase` lines (our current format),
   - a flat `PHRASES:` list (protocol Section 6 format),
   - `<analysis>` / `<answer>` tags, which are skipped,
   - a header with items collapsed onto one line (`Nouns / noun phrases - library - member`).
2. From inside `scoring/`, run:

```bash
# all four rulesets
python score_rulesets.py ../ground_truth/LIB_identification.json ../runs/ID-v05-LIB-r1.txt

# three runs at once (prints the mean)
python score_rulesets.py ../ground_truth/LIB_identification.json r1.txt r2.txt r3.txt

# one ruleset only
python score_rulesets.py ../ground_truth/LIB_identification.json r1.txt --ruleset A
```

Ground truth files: `LIB_identification.json`, `NTSS_identification.json`, `CAR_identification.json`.

3. Check the "phrases parsed" count in the output. If it's far lower than the number of phrases in the answer, the headers weren't recognized; fix the headers and rerun.

Ruleset B prints `n/a` for a flat `PHRASES:` list, because it needs categories.

---

## Shared steps (all rulesets)

### Normalization

Applied to every output phrase and every ground truth phrase before comparing (protocol Section 5.3):

1. Lowercase.
2. Trim and collapse spaces.
3. Remove a leading *a*, *an*, or *the*, and trailing punctuation.
4. Plural nouns become singular (*loan items* → *loan item*).
5. Verbs become base form (*issued* → *issue*, *has* → *have*, *is/are* → *be*).
6. *author(s)* → *author*.
7. Hyphen = space (*bar-code* = *bar code*).
8. *(Pending adjudication)* Square brackets in the ground truth are removed, keeping the word (*[are]* → *are*).

Steps 4 and 5 use a hand-maintained word map (`WORD_MAP` in `score_identification.py`). When a new domain introduces new plurals or verb forms (e.g., *registered*, *organized*), add them there, or those phrases won't match.

### Alternates

- A ground truth line with " / " is **one item**; either alternate matches it, and matching both still counts once (*member number / membership number*).
- An output line with " / " is split into separate phrases.
- Only a spaced " / " splits a line, so *invited and/or selected* stays whole.

### Duplicates

The same normalized output phrase listed twice counts once (Rulesets A, C, D).

### Formulas

```
Precision = TP / (TP + FP)
Recall    = TP / (TP + FN)
F1        = 2 × Precision × Recall / (Precision + Recall)
```

---

## Ruleset A — Protocol exact match (official)

1. Normalize both sides.
2. A ground truth item is a **TP** if some output phrase is **identical** to one of its alternates.
3. **Categories are ignored.** All output phrases form one pool; where the model listed a phrase doesn't matter.
4. **FP:** an output phrase identical to no ground truth alternate.
5. **FN:** a ground truth item with no identical output phrase.

A longer output phrase that contains a ground truth phrase does **not** match it. *A book has a title, and author(s)* vs. ground truth *has a title, and author(s)* = 1 FP + 1 FN.

---

## Ruleset B — Chat rule (per category, containment)

Comparison only. This is the rule used when scoring by hand in the analysis chat.

1. Normalize both sides, and also remove commas.
2. **Categories matter.** Compare output phrases only with ground truth phrases in the **same category**.
3. **Containment:** a ground truth line is **found** if it appears, as whole words, inside any output line in its category.
4. An output line is **matched** if it contains at least one ground truth phrase of its category.
5. Lines are counted as written: every output line counts, and every ground truth line counts (a phrase listed under two categories counts twice).
6. Precision = matched output lines ÷ all output lines. Recall = found ground truth lines ÷ all ground truth lines. F1 from those, pooled over all categories.

A correct phrase under the wrong category = 1 FP (where it's listed) + 1 FN (where it belongs). Note that B uses two different TP counts, unlike the protocol formula.

---

## Ruleset C — Containment, categories ignored

Comparison only. It can be gamed: one very long phrase can match many ground truth items.

1. Normalize both sides.
2. Try exact matches first (as in A).
3. For each ground truth item still unmatched: it's a **TP** if one of its alternates appears, as whole words, **inside any output phrase**.
4. An output phrase that contained a matched item is not an FP. One output phrase may satisfy several ground truth items.
5. Categories are ignored.

---

## Ruleset D — Clause-only containment (proposed)

For team and GTA approval. It relaxes matching only for the rules whose ground truth format differs across domains.

1. Normalize both sides.
2. Try exact matches first (as in A). This is the **only** way to match rules 1–5 (Nouns, X of Y, Verbs, Adjectives, Numeric).
3. For each unmatched ground truth item tagged **rule 6 (Possession), 7 (Consist of), or 9 (X is a Y)**: it's a **TP** if either phrase contains the other, as whole words.
   - Ground truth inside output: *has a title language* inside *A language tape has a title language and level*.
   - Output inside ground truth: output *has* inside *has a title language*.
4. **One-to-one:** each output phrase can satisfy at most one ground truth item.
5. An output phrase used for a match is not an FP.
6. Categories are ignored.

Why only these rules: library stores them as fragments (*has a title language*), NTSS as linking words only (*has*), and car rental not at all. Exact matching can't credit one prompt across all three.

---

## Quick comparison

| | A | B | C | D |
|---|---|---|---|---|
| Match type | Exact | Containment | Exact, then containment | Exact, then containment for rules 6, 7, 9 only |
| Containment direction | — | GT inside output | GT inside output | Either direction |
| Categories | Ignored | Required | Ignored | Ignored |
| One output phrase → one GT item | — | No | No | Yes |
| Status | **Official** | Comparison | Comparison | Proposed |
