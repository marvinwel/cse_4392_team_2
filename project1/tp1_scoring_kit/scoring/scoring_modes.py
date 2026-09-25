"""
Four scoring rulesets for identification, used to show the team how the same
LLM output scores under each. Ruleset A is the official protocol scorer
(score_identification.py); B-D are comparisons.

A  Protocol (exact)          exact match after normalization, categories ignored
B  Chat rule                 containment (GT inside output), per category
C  Containment, no categories containment (GT inside output), categories ignored
D  Clause-only containment   exact everywhere; for GT phrases of rules 6, 7, 9
                             a match if either phrase contains the other (whole
                             words), one output phrase per GT phrase
"""
import json, re
import score_identification as S

KEYS = ("N", "XY", "V", "ADJ", "NUM", "POS", "CON", "GEN")
CATMAP = {"N": "1 Nouns / noun phrases", "XY": "2 X of Y", "V": "3 Transitive verbs",
          "ADJ": "4 Adjectives, enumeration", "NUM": "5 Numeric, quantity",
          "POS": "6 Possession", "CON": "7 Consist of / part of", "GEN": "8 X is a Y"}
CLAUSE = {"6 Possession", "7 Consist of / part of", "8 X is a Y"}


def norm(p, drop_commas=False):
    q = S.normalize(p)
    if drop_commas:
        q = re.sub(r"\s*,\s*", " ", q)
    return q


def contains(big, small):
    return re.search(r"(^| )" + re.escape(small) + r"( |$)", big) is not None


def f1(p, r):
    return 2 * p * r / (p + r) if p + r else 0.0


def gt_items(gt_path):
    return S.load_gt(gt_path)  # key -> alts, key -> categories


def ruleset_A(run, gt, cats):
    return _pooled(run, gt, cats, allow_contain=lambda k: False)


def ruleset_C(run, gt, cats):
    return _pooled(run, gt, cats, allow_contain=lambda k: True, one2one=False)


def ruleset_D(run, gt, cats):
    return _pooled(run, gt, cats, allow_contain=lambda k: bool(cats[k] & CLAUSE),
                   one2one=True, both_ways=True)


def _pooled(run, gt, cats, allow_contain, one2one=False, both_ways=False):
    """Categories ignored. Returns detail rows and totals (protocol-style single TP)."""
    out = {}
    for k in KEYS:
        for e in run[k]:
            for a in S.split_alternates(e):
                out.setdefault(norm(a), f"{e}  [{k}]")
    used, rows = set(), []
    status = {}
    for key, alts in gt.items():                      # pass 1: exact
        hit = sorted(alts & set(out))
        if hit:
            status[key] = ("TP", "exact", hit[0]); used |= set(hit)
    for key, alts in gt.items():                      # pass 2: containment
        if key in status or not allow_contain(key):
            continue
        for o in sorted(out):
            if one2one and o in used:
                continue
            if any(contains(o, a) or (both_ways and contains(a, o)) for a in alts):
                status[key] = ("TP", "containment", o); used.add(o)
                break
    for key in gt:
        if key not in status:
            status[key] = ("FN", "", "")
    all_alts = set().union(*gt.values())
    fps = sorted(o for o in out if o not in all_alts and o not in used)
    tp = sum(1 for s in status.values() if s[0] == "TP")
    fp, fn = len(fps), len(gt) - tp
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn)
    return dict(tp=tp, fp=fp, fn=fn, p=p, r=r, f1=f1(p, r), status=status, fps=fps, out=out)


def ruleset_B(run, gt_path):
    """Chat rule: per category; containment of GT inside output; commas ignored.
    Output lines and GT lines are counted separately (TP_out for precision, TP_gt for recall)."""
    gtc = json.load(open(gt_path))["categories"]
    D = TPd = G = TPg = 0
    detail = {}
    for k, cat in CATMAP.items():
        g_lines = gtc[cat]
        g_alts = [[norm(a, True) for a in S.split_alternates(e)] for e in g_lines]
        o_lines = run[k]
        o_alts = [[norm(a, True) for a in S.split_alternates(e)] for e in o_lines]
        o_ok = [any(contains(o, a) for o in oa for ga in g_alts for a in ga) for oa in o_alts]
        g_ok = [any(contains(o, a) for oa in o_alts for o in oa for a in ga) for ga in g_alts]
        D += len(o_lines); TPd += sum(o_ok); G += len(g_lines); TPg += sum(g_ok)
        detail[k] = dict(o=list(zip(o_lines, o_ok)), g=list(zip(g_lines, g_ok)))
    p, r = TPd / D, TPg / G
    return dict(D=D, TPd=TPd, G=G, TPg=TPg, p=p, r=r, f1=f1(p, r), detail=detail)
