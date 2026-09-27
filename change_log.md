# Change Log — Identification

One row per prompt version (protocol Section 7.2). LIB mean F1 is the **script** score (exact match after normalization, Section 5.4), averaged over all logged runs of that version. Car rental and NTSS have not been run yet. Prompt files are in `prompts/identification/`.

No version passes yet (pass = mean F1 ≥ 0.97 on a domain).

## 7.2 Change log

| Version | Owner | What changed | Targeted misses | LIB mean F1 | CAR mean F1 | NTSS mean F1 | Accepted? |
|---|---|---|---|---|---|---|---|
| ID-v00 | Joseph | Pre-log prompts (not archived; may differ between runs). | — | 0.757 (3 runs) | not run | not run | n/a: baseline only, prompt text unknown |
| ID-v01 | Joseph | First archived prompt: 13 general rules, 9 phrase types, nested-bullet output. | — | 0.739 (1 run) | not run | not run | Baseline for later versions |
| ID-v02 | Joseph | Rewrote rules per category; `<analysis>`/`<answer>` split; attribute-value test for adjectives; participle rule for verbs; Generalization template. **Examples and rules quoted library ground truth phrases.** | Adjective FPs (unique, other, current, manually), reserved/renewed misfiled, noun over-splitting | 0.838 (1 run) | not run | not run | **No:** violates Section 4 rule 4 (library phrases in prompt). Excluded from all decisions. |
| ID-v03 | Joseph | Removed every library phrase from v02; all examples moved to a hotel domain; removed the key-constraint (unique) exclusion; "don't split compound nouns" rule. | Same as v02, without leakage | 0.822 (4 runs) | not run | not run | Yes: replaced v02 as the leakage-free base |
| ID-v04 | Joseph | Added 4-column contrast-set test for adjectives; X of Y extracted from every sentence; Generalization marker list (placeholder). Several changes in one version. | Adjective FPs, X of Y misses (types of loan items), Generalization recall | 0.867 (1 run) | not run | not run | **No:** run invalid, all `<...>` placeholders stripped on paste and marker list never filled in |
| ID-v04.1 | Joseph | Same rules as v04 with `{}` placeholders and ANALYSIS:/ANSWER: markers; marker list filled in; verb exclusion for Possession/Consist/Generalization markers. | Paste corruption from v04 | 0.811 (1 run) | not run | not run | No: superseded by v05 (single run, paste artifacts) |
| ID-v05 | Joseph | Merged working rules into one file delivered as an attachment: verb-over-adjective priority; literal verb forms; keep multiple specific terms together in Generalization; allow dropping "There" in "There are…"; vague quantities in Numeric; no unseen plural variants; full example answer in required layout. | borrowed/reserved/renewed as adjectives; Generalization split or not reordered; missing "a number of"; "libraries" | **0.839 (3 runs)** | not run | not run | **Yes:** current best leakage-free version. Does not pass. |
| ID-v05.1 | Joseph | v05 plus: adjective candidates used as verbs are moved to Verbs (not dropped); negations ("non-X") don't count as alternative values. | reserved/renewed dropped (v05-r1); unique kept via "non-unique" (v05-r2) | 0.807 (3 runs) | not run | not run | No: lower mean than v05 (0.807 vs 0.839); unique/current still kept in 2 of 3 runs |

## Notes for the next version

- **Largest remaining loss:** categories 6–8 (Possession, Consist of, X is a Y) have 0.00 recall for Possession and Consist of in every version (see the per-category recall table in the run log). The prompts ask for full clauses ("A book has a title, and author(s)"), but the ground truth stores fragments ("has a title, and author(s)", "made up of"). Under exact matching, every full clause is 1 FP and the ground truth fragment is 1 FN. This costs roughly 0.07 F1 per run (v05-r1 would go from 0.844 to about 0.917 if these four pairs matched). Settle how these categories are matched (decisions log, open items) before changing the prompt.
- **Recurring FPs likely to be ground truth judgment calls:** facility, support, current, unique. Recurring FN: book bar code. Ask the instructor rather than tuning for them.
- **Protocol deviations to fix going forward:** one kind of change per version (v02, v04, v05 bundled several); output must use the Section 6 `PHRASES:` flat list; 3 runs per version before comparing (v01, v02, v04, v04.1 have 1 run each).
