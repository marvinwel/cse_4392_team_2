"""
Score one or more LLM identification responses under rulesets A-D.

Usage:
    python score_rulesets.py <ground_truth.json> <response.txt> [<response2.txt> ...] [--ruleset A|B|C|D|all]

A response file is the LLM's answer pasted as plain text. Category headers
(e.g. "Nouns / noun phrases", "Transitive verbs") followed by "- phrase" lines
are understood, as is a flat "PHRASES:" list (Ruleset B needs category headers).
"""
import re
import sys
import scoring_modes as M

HEADERS = [("GEN", ("x is a y", "generaliz", "specializ")), ("CON", ("consist", "part of")),
           ("POS", ("possession",)), ("NUM", ("numeric", "quantity")), ("ADJ", ("adjective", "adjative", "enumeration")),
           ("V", ("verb",)), ("XY", ("x of y",)), ("N", ("noun",)), ("FLAT", ("phrases:",))]


def header_key(line):
    low = line.lower()
    for key, words in HEADERS:
        if any(w in low for w in words):
            return key
    return None


def parse_response(text):
    run = {k: [] for k in M.KEYS}
    text = re.sub(r"</?(answer|analysis|phrases)>", "\n", text, flags=re.I)
    text = text.split("ANSWER:", 1)[-1] if "ANSWER:" in text else text
    cur, flat = None, False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        bullet = re.match(r"^[-*•]\s+(.*)$", line)
        if bullet:
            if cur:
                run[cur].append(bullet.group(1).strip())
            continue
        key = header_key(line)
        if key:
            cur = "N" if key == "FLAT" else key
            flat = flat or key == "FLAT"
            # header and items collapsed onto one line: "Nouns - a - b - c"
            parts = re.split(r"\s+-\s+", line)
            run[cur].extend(p.strip() for p in parts[1:] if p.strip())
    return run, flat


def main(argv):
    ruleset = "ALL"
    if "--ruleset" in argv:
        i = argv.index("--ruleset"); ruleset = argv[i + 1].upper(); del argv[i:i + 2]
    gt_path, files = argv[0], argv[1:]
    gt, cats = M.gt_items(gt_path)
    wanted = "ABCD" if ruleset == "ALL" else ruleset
    print(f"Ground truth: {gt_path} ({len(gt)} unique phrases)")
    print(f"{'Response':32s} " + "  ".join(f"{r:>5s}" for r in wanted))
    totals = {r: [] for r in wanted}
    for f in files:
        run, flat = parse_response(open(f, encoding="utf-8").read())
        n = sum(len(v) for v in run.values())
        scores = {}
        for r in wanted:
            if r == "B":
                scores[r] = None if flat else M.ruleset_B(run, gt_path)["f1"]
            else:
                scores[r] = {"A": M.ruleset_A, "C": M.ruleset_C, "D": M.ruleset_D}[r](run, gt, cats)["f1"]
            if scores[r] is not None:
                totals[r].append(scores[r])
        name = f.split("/")[-1][:32]
        print(f"{name:32s} " + "  ".join("  n/a" if scores[r] is None else f"{scores[r]:.3f}" for r in wanted)
              + f"   ({n} phrases parsed)")
    if len(files) > 1:
        print(f"{'Mean':32s} " + "  ".join(f"{sum(v)/len(v):.3f}" if v else "  n/a" for v in totals.values()))


if __name__ == "__main__":
    main(sys.argv[1:])
