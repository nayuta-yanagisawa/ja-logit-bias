#!/usr/bin/env python3
"""Recomputes the README's evaluation table from the answers and Codex's judgements in eval/results/.

    python3 eval/summarize.py [RESULTS_DIR]      (default eval/results; eval/deepseek/results for DeepSeek)

An answer made only of a tool call (the model, under a coding agent's system prompt, wrote a file instead of
replying) has no prose to judge, so it is left out of every count, and so is a comparison that holds one.
Codex was asked to list punctuation such as ： and ？ as Chinese; Japanese uses those too, so items made only of
punctuation are not counted.
"""
import collections
import json
import math
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
R = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "results"
PROMPTS = json.loads((HERE / "prompts.json").read_text(encoding="utf-8"))
PUNCT = set("：:？！，；?!,;")
ORDER = ["none", "system-prompt", "char-rule", "bias", "bias-minp0.05", "bias-minp0.1", "bias-minp0.05-temp0.7",
         "earlier-minp0.05", "rule-a-minp0.05"]


def prose(text):
    return re.sub(r"<tool_call>.*?(</tool_call>|$)", "", text, flags=re.S).strip()


answers = {}
for f in R.glob("*.json"):
    for r in json.loads(f.read_text(encoding="utf-8")):
        answers[(f.stem, r["prompt"], r["rep"])] = bool(prose(r["text"]))


def real(items):
    return [x for x in items if not all(c in PUNCT or c.isspace() for c in x)]


def sign_p(a, b):
    n, k = a + b, min(a, b)
    return min(1.0, 2 * sum(math.comb(n, j) for j in range(k + 1)) / 2 ** n) if n else 1.0


reads = [json.loads(l) for l in (R / "codex-reading.jsonl").read_text(encoding="utf-8").splitlines() if l]
pairs = [json.loads(l) for l in (R / "codex-pairs.jsonl").read_text(encoding="utf-8").splitlines() if l]

print("Reading (answers with prose only)")
print(f"{'round':>5} {'condition':24} {'prose':>5} {'Chinese':>8} {'non-China':>10} {'odd':>9} {'odd items':>9}")
odd_of = {}
for rnd in sorted({x["round"] for x in reads}):
    for cond in [c for c in ORDER if any(x["cond"] == c and x["round"] == rnd for x in reads)]:
        rows = [x for x in reads if x["round"] == rnd and x["cond"] == cond and answers[(cond, x["prompt"], x["rep"])]]
        zh = [x for x in rows if real(x["zh"])]
        nc = [x for x in rows if PROMPTS[x["prompt"]]["cat"] != "china"]
        nczh = [x for x in nc if real(x["zh"])]
        odd = [x for x in rows if x["odd"]]
        for x in rows:
            odd_of[(rnd, cond, x["prompt"], x["rep"])] = bool(x["odd"])
        print(f"{rnd:>5} {cond:24} {len(rows):>5} {len(zh):>3} ({100 * len(zh) / len(rows):2.0f}%) "
              f"{len(nczh):>3}/{len(nc):<3}({100 * len(nczh) / len(nc):2.0f}%) {len(odd):>3} ({100 * len(odd) / len(rows):2.0f}%) "
              f"{sum(len(x['odd']) for x in rows):>9}")

print("\nOdd wording, same request and repetition, within a round (only-A / only-B, sign test)")
for rnd, a, b in [(1, "none", "bias"), (1, "none", "char-rule"), (2, "bias", "bias-minp0.05"), (2, "bias", "bias-minp0.1"),
                  (3, "bias-minp0.05", "bias-minp0.05-temp0.7"),
                  (4, "earlier-minp0.05", "rule-a-minp0.05")]:
    keys = [(p, r) for (rr, c, p, r) in odd_of if rr == rnd and c == a and (rnd, b, p, r) in odd_of]
    if not keys:
        continue
    oa = sum(odd_of[(rnd, a, p, r)] and not odd_of[(rnd, b, p, r)] for p, r in keys)
    ob = sum(odd_of[(rnd, b, p, r)] and not odd_of[(rnd, a, p, r)] for p, r in keys)
    print(f"  round {rnd} {a} vs {b}: only {a} {oa}, only {b} {ob}, p = {sign_p(oa, ob):.3f} ({len(keys)} pairs)")

print("\nBlind comparison (pairs where both answers have prose)")
groups = collections.defaultdict(lambda: collections.Counter())
for x in pairs:
    if not (answers[(x["A"], x["prompt"], x["rep"])] and answers[(x["B"], x["prompt"], x["rep"])]):
        continue
    g = groups[(x["round"],) + tuple(sorted((x["A"], x["B"])))]
    g["better:" + x["better"]] += 1
    g["japanese:" + x["japanese"]] += 1
for (rnd, a, b), g in sorted(groups.items()):
    for k in ("better", "japanese"):
        wa, wb, t = g[f"{k}:{a}"], g[f"{k}:{b}"], g[f"{k}:tie"]
        print(f"  round {rnd} {k:8} {a} {wa} - {b} {wb} - tie {t}, p = {sign_p(wa, wb):.3f}")
