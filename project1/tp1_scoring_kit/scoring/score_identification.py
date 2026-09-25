"""
Identification scorer for Team Project 1 (run protocol Sections 5.3 and 5.4).

Usage:
    python score_identification.py ../ground_truth/LIB_identification.json ../runs/LIB_identification_runs.json

Matching rules implemented:
  5.3 Normalization (both sides): lowercase; trim/collapse spaces; strip leading
      a/an/the and trailing punctuation; plural nouns -> singular; verbs -> base
      form; author(s) -> author; hyphen = space.
      Normalization is done with a hand-maintained word map (decision 20 = "by hand").
      Add words to WORD_MAP when a new domain introduces them.
  5.4 Exact match on the normalized phrase. Slash alternates are one item.
      Duplicates collapse. Score the unique phrase set (categories ignored).
      Per-category recall is reported as a diagnostic only.

Adjudication applied (see decisions log): square brackets in ground truth are
editorial marks and are removed, keeping their contents ("[are]" -> "are").
"""
import json
import re
import sys

# Hand normalization map: plural nouns -> singular, verb forms -> base form.
WORD_MAP = {
    # plural nouns
    "items": "item", "sections": "section", "tapes": "tape", "books": "book",
    "records": "record", "details": "detail", "types": "type", "authors": "author",
    "customers": "customer", "libraries": "library", "numbers": "number",
    "members": "member", "loans": "loan", "titles": "title", "cards": "card",
    # verbs -> base form
    "issues": "issue", "issued": "issue", "shows": "show", "showed": "show",
    "kept": "keep", "keeps": "keep", "denoted": "denote", "denotes": "denote",
    "identified": "identify", "identifies": "identify", "borrowed": "borrow",
    "borrows": "borrow", "reserved": "reserve", "reserves": "reserve",
    "renewed": "renew", "renews": "renew", "extended": "extend", "extends": "extend",
    "scanned": "scan", "scans": "scan", "entered": "enter", "enters": "enter",
    "stamped": "stamp", "stamps": "stamp", "searched": "search", "searches": "search",
    "supports": "support", "supported": "support", "updated": "update", "updates": "update",
    "known": "know", "has": "have", "is": "be", "are": "be", "made": "make",
}

LEADING_ARTICLES = ("a ", "an ", "the ")


def normalize(phrase: str) -> str:
    p = phrase.lower().strip()
    p = p.replace("[", "").replace("]", "")      # adjudication: GT editorial brackets
    p = p.replace("(s)", "")                     # 5.3.6 author(s) -> author
    p = p.replace("-", " ")                      # 5.3.7 hyphen = space
    p = re.sub(r"\s+", " ", p).strip()           # 5.3.2
    p = re.sub(r"[.,;:!?]+$", "", p).strip()     # 5.3.3 trailing punctuation
    for art in LEADING_ARTICLES:                 # 5.3.3 leading article
        if p.startswith(art):
            p = p[len(art):]
            break
    tokens = []
    for tok in p.split(" "):
        m = re.match(r"^(\W*)(.*?)(\W*)$", tok)
        pre, core, post = m.groups()
        tokens.append(pre + WORD_MAP.get(core, core) + post)
    return " ".join(tokens)


def split_alternates(entry: str):
    return [a.strip() for a in entry.split(" / ") if a.strip()]  # spaced slash only, so "and/or" stays intact


def load_gt(path):
    gt = json.load(open(path))
    items = {}          # key -> set of normalized alternates
    item_cats = {}      # key -> set of categories
    for cat, entries in gt["categories"].items():
        for entry in entries:
            alts = frozenset(normalize(a) for a in split_alternates(entry))
            key = min(alts)
            # merge items that share any alternate (duplicate across categories)
            existing = next((k for k, v in items.items() if v & alts), None)
            if existing:
                items[existing] |= alts
                item_cats[existing].add(cat)
            else:
                items[key] = set(alts)
                item_cats[key] = {cat}
    return items, item_cats


def score_run(run, gt_items, gt_cats):
    out = set()
    for key, vals in run.items():
        if isinstance(vals, list):
            for entry in vals:
                for alt in split_alternates(entry):
                    out.add(normalize(alt))
    matched = {k for k, alts in gt_items.items() if alts & out}
    all_gt_alts = set().union(*gt_items.values())
    fp_phrases = sorted(p for p in out if p not in all_gt_alts)
    fn_items = sorted(k for k in gt_items if k not in matched)
    tp, fp, fn = len(matched), len(fp_phrases), len(fn_items)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    # per-category recall (diagnostic)
    cat_rec = {}
    cats = sorted({c for cs in gt_cats.values() for c in cs})
    for c in cats:
        keys = [k for k, cs in gt_cats.items() if c in cs]
        hit = sum(1 for k in keys if k in matched)
        cat_rec[c] = (hit, len(keys))
    return dict(tp=tp, fp=fp, fn=fn, precision=prec, recall=rec, f1=f1,
                fp_phrases=fp_phrases, fn_items=fn_items, cat_recall=cat_rec)


def main(gt_path, runs_path):
    gt_items, gt_cats = load_gt(gt_path)
    runs = json.load(open(runs_path))["runs"]
    results = []
    for r in runs:
        res = score_run({k: v for k, v in r.items() if k in
                         ("N", "XY", "V", "ADJ", "NUM", "POS", "CON", "GEN", "PHRASES")},
                        gt_items, gt_cats)
        res["run_id"] = r["run_id"]
        res["prompt_version"] = r["prompt_version"]
        res["chat_f1_micro"] = r.get("chat_f1_micro")
        results.append(res)
    return gt_items, gt_cats, results


if __name__ == "__main__":
    gt_items, _, results = main(sys.argv[1], sys.argv[2])
    print(f"Ground truth unique items: {len(gt_items)}")
    for r in results:
        print(f"{r['run_id']:18s} TP={r['tp']:2d} FP={r['fp']:2d} FN={r['fn']:2d} "
              f"P={r['precision']:.3f} R={r['recall']:.3f} F1={r['f1']:.3f}")
