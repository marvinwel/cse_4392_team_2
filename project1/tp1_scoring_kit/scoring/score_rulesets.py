"""Parse an LLM identification response and score it under rulesets A-D."""
import re
import sys
import scoring_modes as M

HEADERS = [("GEN", ("x is a y", "generaliz", "specializ")), ("CON", ("consist", "part of")),
           ("POS", ("possession",)), ("NUM", ("numeric", "quantity")),
           ("ADJ", ("adjective", "adjative", "enumeration")),
           ("V", ("verb",)), ("XY", ("x of y",)), ("N", ("noun",)), ("FLAT", ("phrases:",))]


def header_key(line):
    """A line is a category header only if it is short and names a category."""
    if len(line.split()) > 7:
        return None
    low = line.lower()
    for key, words in HEADERS:
        if any(w in low for w in words):
            return key
    return None


def parse_response(text):
    run = {k: [] for k in M.KEYS}
    # drop the analysis block: its rows would otherwise be read as phrases
    text = re.sub(r"<analysis>.*?</analysis>", "\n", text, flags=re.I | re.S)
    m = re.search(r"<answer>(.*?)(</answer>|$)", text, flags=re.I | re.S)
    if m:
        text = m.group(1)
    elif "ANSWER:" in text:
        text = text.split("ANSWER:", 1)[1]
    text = re.sub(r"</?(answer|analysis|phrases)>", "\n", text, flags=re.I)
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
        line = re.sub(r"^\d+[.)]\s+", "", line)      # numbered lists
        parts = re.split(r"\s+-\s+", line)           # header with items on one line
        key = header_key(parts[0])
        if key:
            cur = "N" if key == "FLAT" else key
            flat = flat or key == "FLAT"
            run[cur].extend(p.strip() for p in parts[1:] if p.strip())
        elif cur and "|" not in line and "->" not in line:
            run[cur].append(line)                    # bare phrase line, no bullet
    return run, flat


def main(argv):
    ruleset = "BCD"
    if "--ruleset" in argv:
        i = argv.index("--ruleset"); ruleset = argv[i + 1].upper(); del argv[i:i + 2]
    gt_path, files = argv[0], argv[1:]
    gt, cats = M.gt_items(gt_path)
    wanted = "ABCD" if ruleset == "ALL" else ruleset
    print(f"Ground truth: {gt_path} ({len(gt)} unique phrases)")
    print(f"{'Response':32s} " + "  ".join(f"{r:>5s}" for r in wanted))
    for f in files:
        run, flat = parse_response(open(f, encoding="utf-8").read())
        n = sum(len(v) for v in run.values())
        if n == 0:
            print(f"{f.split('/')[-1][:32]:32s} " + "  ".join("  n/a" for _ in wanted)
                  + "   (0 phrases parsed - no category headers found in this file)")
            continue
        cells = []
        for r in wanted:
            if r == "B":
                cells.append("  n/a" if flat else f"{M.ruleset_B(run, gt_path)['f1']:.3f}")
            else:
                fn = {"A": M.ruleset_A, "C": M.ruleset_C, "D": M.ruleset_D}[r]
                cells.append(f"{fn(run, gt, cats)['f1']:.3f}")
        print(f"{f.split('/')[-1][:32]:32s} " + "  ".join(cells) + f"   ({n} phrases parsed)")


if __name__ == "__main__":
    main(sys.argv[1:])
