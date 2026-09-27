# Run Log — Identification (Library)

Logged retrospectively on 2026-09-19 under run protocol Sections 5.3–5.4 (exact match after normalization, unique phrase set, categories ignored). Scored with `scoring/score_identification.py` against `ground_truth/LIB_identification.json` (55 unique items).

**F1 (LLM)** is the micro F1 computed in the analysis chat by Claude, using a *different* rule (per-category scoring, a ground truth phrase counted as matched if it appeared *inside* a derived phrase). It is not comparable to the script score; see the decisions log. Per Section 5.2, only the script score is used for decisions.

Model: **TBD — record the exact model and version used for these runs.** Settings: chat UI, default settings. All runs by Joseph on 2026-09-19 (exact times not recorded).

## 7.1 Run log

| Run ID | Date | Member | Model | Prompt version | Domain | TP | FP | FN | Precision | Recall | F1 (script) | F1 (LLM) | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ID-v00-LIB-r1 | 2026-09-19 | Joseph | TBD (chat UI) | v00 | LIB | 40 | 19 | 15 | 0.678 | 0.727 | **0.702** | 0.826 | Prompt not archived. Pre-log baseline. |
| ID-v00-LIB-r2 | 2026-09-19 | Joseph | TBD (chat UI) | v00 | LIB | 46 | 17 | 9 | 0.730 | 0.836 | **0.780** | 0.843 | Prompt not archived. Duplicate items in output (collapsed by rule 5.4.3). |
| ID-v00-LIB-r3 | 2026-09-19 | Joseph | TBD (chat UI) | v00 | LIB | 47 | 17 | 8 | 0.734 | 0.855 | **0.790** | 0.870 | Prompt not archived. |
| ID-v01-LIB-r1 | 2026-09-19 | Joseph | TBD (chat UI) | v01 | LIB | 41 | 15 | 14 | 0.732 | 0.745 | **0.739** | 0.852 | First archived prompt. Noun recall low (details, date of birth, current loan, book bar code missed). |
| ID-v02-LIB-r1 | 2026-09-19 | Joseph | TBD (chat UI) | v02 | LIB | 49 | 13 | 6 | 0.790 | 0.891 | **0.838** | 0.920 | EXCLUDED: prompt contained library ground truth phrases (Section 4 rule 4). Output collapsed onto one line. |
| ID-v03-LIB-r1 | 2026-09-19 | Joseph | TBD (chat UI) | v03 | LIB | 48 | 10 | 7 | 0.828 | 0.873 | **0.850** | 0.933 | First leakage-free prompt (hotel-domain examples). Pasted into chat. |
| ID-v04-LIB-r1 | 2026-09-19 | Joseph | TBD (chat UI) | v04 | LIB | 49 | 9 | 6 | 0.845 | 0.891 | **0.867** | 0.925 | INVALID CONDITIONS: `<...>` placeholders stripped on paste; Generalization marker list left as placeholder text. |
| ID-v04.1-LIB-r1 | 2026-09-19 | Joseph | TBD (chat UI) | v04.1 | LIB | 45 | 11 | 10 | 0.804 | 0.818 | **0.811** | 0.867 | Prompt pasted with `&#x20;` / backslash artifacts. Generalization sentence split into two lines. |
| ID-v03-LIB-r2 | 2026-09-19 | Joseph | TBD (chat UI) | v03 | LIB | 47 | 10 | 8 | 0.825 | 0.855 | **0.839** | 0.940 | Same prompt as v03-r1 (escaped brackets on paste). All verbs converted to base form. No Generalization output. |
| ID-v03-LIB-r3 | 2026-09-19 | Joseph | TBD (chat UI) | v03 | LIB | 43 | 15 | 12 | 0.741 | 0.782 | **0.761** | 0.873 | Same prompt as v03-r1 (double-escaped on paste). Over-split nouns (language, loan, number). |
| ID-v03-LIB-r4 | 2026-09-19 | Joseph | TBD (chat UI) | v03 | LIB | 46 | 9 | 9 | 0.836 | 0.836 | **0.836** | 0.906 | Same prompt, delivered as attached .md file (first clean delivery). borrowed/reserved/renewed misfiled as adjectives. |
| ID-v05-LIB-r1 | 2026-09-19 | Joseph | TBD (chat UI) | v05 | LIB | 46 | 8 | 9 | 0.852 | 0.836 | **0.844** | 0.939 | Attached .md. reserved/renewed dropped entirely (routing gap). |
| ID-v05-LIB-r2 | 2026-09-19 | Joseph | TBD (chat UI) | v05 | LIB | 48 | 11 | 7 | 0.814 | 0.873 | **0.842** | 0.934 | Attached .md. unique and two in Adjectives. |
| ID-v05-LIB-r3 | 2026-09-19 | Joseph | TBD (chat UI) | v05 | LIB | 47 | 11 | 8 | 0.810 | 0.855 | **0.832** | 0.934 | Attached .md. Over-split nouns (loan, update). |
| ID-v05.1-LIB-r1 | 2026-09-19 | Joseph | TBD (chat UI) | v05.1 | LIB | 45 | 11 | 10 | 0.804 | 0.818 | **0.811** | 0.921 | Attached .md. current loan split to loan; details missing. |
| ID-v05.1-LIB-r2 | 2026-09-19 | Joseph | TBD (chat UI) | v05.1 | LIB | 46 | 11 | 9 | 0.807 | 0.836 | **0.821** | 0.925 | Attached .md. Generalization sentence not reordered. |
| ID-v05.1-LIB-r3 | 2026-09-19 | Joseph | TBD (chat UI) | v05.1 | LIB | 45 | 14 | 10 | 0.763 | 0.818 | **0.789** | 0.942 | Attached .md. Auxiliaries kept (is issued, must be kept). |

## Summary by prompt version (library)

| Version | Runs | Mean F1 (script) | Min | Max | Mean F1 (LLM, chat rule) | Passes (mean ≥ 0.97)? |
|---|---|---|---|---|---|---|
| v00 | 3 | **0.757** | 0.702 | 0.790 | 0.846 | No |
| v01 | 1 | **0.739** | 0.739 | 0.739 | 0.852 | No |
| v02 | 1 | **0.838** | 0.838 | 0.838 | 0.920 | No |
| v03 | 4 | **0.822** | 0.761 | 0.850 | 0.913 | No |
| v04 | 1 | **0.867** | 0.867 | 0.867 | 0.925 | No |
| v04.1 | 1 | **0.811** | 0.811 | 0.811 | 0.867 | No |
| v05 | 3 | **0.839** | 0.832 | 0.844 | 0.936 | No |
| v05.1 | 3 | **0.807** | 0.789 | 0.821 | 0.929 | No |

## Per-category recall (diagnostic only, Section 5.4 rule 5)

Pooled over all runs of each version. A phrase listed under two ground truth categories (date of birth) counts in both.

| Version | 1 Nouns / noun phrases | 2 X of Y | 3 Transitive verbs | 4 Adjectives, enumeration | 5 Numeric, quantity | 6 Possession | 7 Consist of / part of | 8 X is a Y |
|---|---|---|---|---|---|---|---|---|
| v00 | 0.93 | 0.67 | 0.93 | 0.83 | 0.67 | 0.00 | 0.00 | 0.33 |
| v01 | 0.83 | 0.60 | 1.00 | 0.50 | 0.75 | 0.00 | 0.00 | 0.00 |
| v02 | 0.96 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 | 0.00 | 0.00 |
| v03 | 0.94 | 0.80 | 1.00 | 1.00 | 0.62 | 0.00 | 0.00 | 0.00 |
| v04 | 1.00 | 1.00 | 1.00 | 1.00 | 0.75 | 0.00 | 0.00 | 0.00 |
| v04.1 | 0.92 | 0.80 | 1.00 | 1.00 | 0.50 | 0.00 | 0.00 | 0.00 |
| v05 | 0.96 | 0.93 | 0.95 | 1.00 | 0.50 | 0.00 | 0.00 | 0.50 |
| v05.1 | 0.93 | 0.93 | 0.98 | 1.00 | 0.42 | 0.00 | 0.00 | 0.00 |

## Misses per run (script output)

Phrases are shown in normalized form (lowercase, singular, base-form verbs).

**ID-v00-LIB-r1**  
FP (19): book have a title and author; current; daily update of record; facility; have; item on loan; language; language tape have a title language and level; make up; make up of a number of subject section; manual; maximum of 8 item; number; number of item on loan; other; support; there be two type of loan item, language tape, and book; two type; unique  
FN (15): 8; beginner; book; book bar code; french; have a title language; have a title, and author; language tape; language tape, and book be two type of loan item; make up of; number of; number of item; renew; two; update of record

**ID-v00-LIB-r2**  
FP (17): current; daily update; facility; have a title and author; have a title language and level; language; language tape and book be two type of loan item; make up of a number of subject section; manually; maximum; other; subject; support; two type of loan item; unique; unique member number; up to a maximum of 8 item  
FN (9): detail; have a title language; have a title, and author; language tape, and book be two type of loan item; make up of; number of; renew; reserve; update of record

**ID-v00-LIB-r3**  
FP (17): current; daily update of record; each customer be know as a member; facility; have a title and author; have a title language and level; language; make up; make up of a number of subject section; manually; number of item on loan; other; subject; support; there be two type of loan item, language tape, and book; unique; up to a maximum of 8 item  
FN (8): book bar code; customer be know as a member; have a title language; have a title, and author; language tape, and book be two type of loan item; make up of; number of item; type of loan item

**ID-v01-LIB-r1**  
FP (15): book have a title, and author; current; each customer be know as a member; facility; language tape have a title language, and level; library be make up of a number of subject section; loan; manually; number of item on loan; other; subject; there be two type of loan item, language tape, and book; unique; up to a maximum of 8; update  
FN (14): 8; beginner; book bar code; current loan; customer be know as a member; detail; french; have a title language; have a title, and author; language tape, and book be two type of loan item; make up of; membership; number of item; type of loan item

**ID-v02-LIB-r1**  
FP (13): be issue; book have a title, and author; customer be a member; facility; language; language tape and book be two type of loan item; language tape have a title language (e.g. french), and level (e.g. beginner); library be make up of a number of subject section; loan; number; support; type; up to  
FN (6): customer be know as a member; have a title language; have a title, and author; language tape, and book be two type of loan item; make up of; title language

**ID-v03-LIB-r1**  
FP (10): book have a title, and author; current; facility; language tape have a title language (e.g. french), and level (e.g. beginner); library be make up of a number of subject section; number of item on loan; support; there be two type of loan item, language tape, and book; unique; up to a maximum of 8 item  
FN (7): customer be know as a member; have a title language; have a title, and author; language tape, and book be two type of loan item; make up of; number of; type of loan item

**ID-v04-LIB-r1**  
FP (9): book have a title, and author; daily update; facility; know; language tape have a title language (e.g. french), and level (e.g. beginner); library be make up of a number of subject section; number of item on loan; support; up to a maximum of 8 item  
FN (6): customer be know as a member; have a title language; have a title, and author; language tape, and book be two type of loan item; make up of; number of

**ID-v04.1-LIB-r1**  
FP (11): book be type of loan item; book have a title, and author; current; facility; language tape be type of loan item; language tape have a title language (e.g. french), and level (e.g. beginner); library be make up of a number of subject section; loan; maximum of 8 item; support; update  
FN (10): book bar code; current loan; customer be know as a member; have a title language; have a title, and author; language tape, and book be two type of loan item; less than 8; make up of; number of; type of loan item

**ID-v03-LIB-r2**  
FP (10): book have a title, and author; current; facility; language tape have a title language (e.g. french), and level (e.g. beginner); library be make up of a number of subject section; number of item on loan; support; type; unique; up to a maximum of 8 item  
FN (8): 8; book bar code; customer be know as a member; have a title language; have a title, and author; language tape, and book be two type of loan item; make up of; number of

**ID-v03-LIB-r3**  
FP (15): book have a title, and author; current; each customer be know as a member; each customer have a name, address, and date of birth; facility; language; language tape have a title language and level; library be make up of a number of subject section; loan; number; number of item on loan; support; there be two type of loan item, language tape, and book; unique; up to a maximum of 8 item  
FN (12): 8; book bar code; current loan; customer be know as a member; have a title language; have a title, and author; language tape, and book be two type of loan item; make up of; number of; number of item; number of subject section; title language

**ID-v03-LIB-r4**  
FP (9): book have a title, and author; each customer be know as a member; facility; language tape have a title language, and level; library be make up of a number of subject section; support; there be two type of loan item, language tape, and book; type; up to a maximum of 8 item  
FN (9): book bar code; customer be know as a member; have a title language; have a title, and author; language tape, and book be two type of loan item; make up of; membership; number of; type of loan item

**ID-v05-LIB-r1**  
FP (8): book have a title, and author; current; each customer be know as a member; facility; language tape have a title language (e.g. french), and level (e.g. beginner); library be make up of a number of subject section; support; up to a maximum of 8 item  
FN (9): 8; book bar code; customer be know as a member; have a title language; have a title, and author; make up of; number of; renew; reserve

**ID-v05-LIB-r2**  
FP (11): book have a title, and author; current; each customer be know as a member; facility; language tape have a title language (e.g. french), and level (e.g. beginner); library be make up of a number of subject section; number; support; two type of loan item; unique; up to a maximum of 8 item  
FN (7): 8; book bar code; customer be know as a member; have a title language; have a title, and author; make up of; number of

**ID-v05-LIB-r3**  
FP (11): book have a title, and author; current; each customer be know as a member; facility; language tape have a title language (e.g. french), and level (e.g. beginner); library be make up of a number of subject section; loan; support; unique; up to a maximum of 8 item; update  
FN (8): 8; book bar code; customer be know as a member; have a title language; have a title, and author; make up of; number of; type of loan item

**ID-v05.1-LIB-r1**  
FP (11): book have a title and author; each customer be know as a member; facility; language tape and book be two type of loan item; language tape have a title language and level; library be make up of a number of subject section; loan; support; two type of loan item; up to a maximum of 8 item; update  
FN (10): book bar code; current loan; customer be know as a member; detail; have a title language; have a title, and author; language tape, and book be two type of loan item; make up of; number of; two

**ID-v05.1-LIB-r2**  
FP (11): book have a title, and author; current; each customer be know as a member; facility; language tape have a title language (e.g. french), and level (e.g. beginner); library be make up of a number of subject section; number of item on loan; support; there be two type of loan item, language tape, and book; unique; up to a maximum of 8 item  
FN (9): 8; book bar code; customer be know as a member; have a title language; have a title, and author; language tape, and book be two type of loan item; make up of; number of; number of subject section

**ID-v05.1-LIB-r3**  
FP (14): be issue; book have a title, and author; current; each customer be know as a member; facility; language tape have a title language (e.g. french), and level (e.g. beginner); library be make up of a number of subject section; must be keep; number of item on loan; support; there be two type of loan item, language tape, and book; two type of loan item; unique; up to a maximum of 8 item  
FN (10): 8; book bar code; customer be know as a member; have a title language; have a title, and author; keep; language tape, and book be two type of loan item; make up of; number of; two

