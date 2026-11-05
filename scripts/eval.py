#!/usr/bin/env python3
"""Asks a model Japanese questions and counts the Chinese in its answers.

    eval.py --url http://localhost:8080 --model NAME --label base --out base.json
            [--bias data/qwen3.8-flash-next/logit_bias.json] [--prompts eval/prompts.json] [--n 2]
            [--system FILE] [--system-extra TEXT] [--extra '{"reasoning_effort": "medium"}']

Sends each prompt N times to an OpenAI-compatible /v1/chat/completions endpoint and scores the final answer, with
code blocks and inline code left out:
  outside_0208  kanji outside JIS X 0208 (the four jōyō kanji outside it excepted): Simplified forms such as 们 这
  zh_punct      the full-width comma and semicolon (，；). Chinese prose uses them; Japanese prose mostly uses 、 but
                academic Japanese writes ，too, so this count is reported apart and not counted as Chinese
  zh_words      common Chinese function words written in characters Japanese shares (可以 但是 如果 ...)
These counts find only the plainest mixing. Reading the answers finds more; eval/README.md says how the published
results were read.
An answer that ended for any reason but "stop" (the token limit, most often) or came back empty is kept apart and
left out of the summary, since a missing answer would otherwise count as one free of Chinese.
Prints one line per answer and a summary. Writes every answer with its scores to --out after each answer, and a run
started again with the same --out skips the answers already there.
"""
import argparse
import json
import pathlib
import re
import time
import urllib.request

from common import is_han, jis_ok

ZH_WORDS = ["可以", "但是", "如果", "因为", "已经", "这样", "那么", "我们", "他们", "这个", "进行",
            "通过", "实现", "的话", "什么", "怎么", "还是", "或者", "以及", "并且", "比如"]
ZH_PUNCT = "，；"


def score(text):
    prose = re.sub(r"```.*?```", "", text, flags=re.S)
    prose = re.sub(r"`[^`]*`", "", prose)
    outside = [c for c in prose if is_han(c) and not jis_ok(c)]
    punct = [c for c in prose if c in ZH_PUNCT]
    words = [w for w in ZH_WORDS for _ in range(prose.count(w))]
    return {"outside_0208": len(outside), "zh_punct": len(punct), "zh_words": len(words), "chars": len(prose),
            "samples": "".join(outside[:12]) + (" | " + " ".join(sorted(set(words))) if words else "")}


def ask(a, system, prompt, bias):
    messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    body = {"model": a.model, "max_tokens": a.max_tokens, "messages": messages, **json.loads(a.extra)}
    if bias:
        body["logit_bias"] = bias
    req = urllib.request.Request(a.url.rstrip("/") + "/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=a.timeout))
    choice = r["choices"][0]
    return (choice["message"].get("content") or "", choice.get("finish_reason"), time.time() - t,
            r["usage"]["completion_tokens"])


def main():
    here = pathlib.Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--bias", default=None, help="a logit_bias JSON file from make_bias.py")
    ap.add_argument("--prompts", default=str(here / "eval" / "prompts.json"))
    ap.add_argument("--n", type=int, default=2)
    ap.add_argument("--system", default=None, help="a file holding the system prompt")
    ap.add_argument("--system-extra", default="", help="text appended to the system prompt")
    ap.add_argument("--extra", default="{}", help="JSON merged into each request body")
    ap.add_argument("--max-tokens", type=int, default=6000)
    ap.add_argument("--timeout", type=int, default=900)
    a = ap.parse_args()
    system = pathlib.Path(a.system).read_text(encoding="utf-8") if a.system else ""
    if a.system_extra:
        system = (system + "\n\n" + a.system_extra).strip()
    bias = json.load(open(a.bias)) if a.bias else None
    prompts = json.load(open(a.prompts, encoding="utf-8"))
    out = pathlib.Path(a.out)
    rows = json.loads(out.read_text(encoding="utf-8")) if out.exists() else []
    done = {(r["prompt"], r["rep"]) for r in rows}
    for rep in range(a.n):
        for i, item in enumerate(prompts):
            if (i, rep) in done:
                continue
            text, finish, secs, ntok = ask(a, system, item["p"], bias)
            s = score(text)
            s.update({"prompt": i, "cat": item["cat"], "rep": rep, "finish": finish, "secs": round(secs, 1),
                      "tokens": ntok, "text": text})
            rows.append(s)
            out.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            print(f"[{a.label}] p{i} r{rep}: {secs:5.1f}s {ntok:5d} tok, {s['chars']:5d} ch, {finish}, outside_0208 "
                  f"{s['outside_0208']} punct {s['zh_punct']} words {s['zh_words']} {s['samples']}", flush=True)
    whole = [r for r in rows if r["finish"] == "stop" and r["chars"] > 0]
    chars = max(sum(r["chars"] for r in whole), 1)
    hit = sum(1 for r in whole if r["outside_0208"] + r["zh_words"] > 0)
    tot = {k: sum(r[k] for r in whole) for k in ("outside_0208", "zh_punct", "zh_words")}
    print(f"[{a.label}] SUMMARY {len(whole)} complete answers ({len(rows) - len(whole)} cut off or empty, left out), "
          f"{hit} with Chinese characters or words; per 1,000 characters: "
          + ", ".join(f"{k} {1000 * v / chars:.2f}" for k, v in tot.items())
          + f"; mean {chars / max(len(whole), 1):.0f} characters", flush=True)


if __name__ == "__main__":
    main()
