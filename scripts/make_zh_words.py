#!/usr/bin/env python3
"""Chooses the Chinese words to ban: kanji-only tokens that Japanese text almost never holds but Chinese text does.

    make_zh_words.py TOKENIZER_JSON JA.npz ZH.npz OUT_DIR [--ja 10]

JA.npz and ZH.npz come from count_corpus.py with the same TOKENIZER_JSON. A token text of one or more kanji, all inside
JIS X 0208, is banned when Japanese text holds it under --ja times per 1e8 tokens and Chinese text holds it at all.
The rule has no allowlist and no exception by length, so the list follows from the counts alone. A Japanese word it
bans stays writable in smaller tokens, since the ban is on the token, not the character. The counts of a text add up
every token that spells it, with or without a leading space.

Writes into OUT_DIR:
  freq.tsv      every kanji-only token text with its Japanese and Chinese counts per 1e8 tokens
  zh-words.txt  the banned texts
"""
import argparse
import pathlib

from common import kanji_word, load_counts, token_texts

ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
ap.add_argument("tokenizer")
ap.add_argument("ja")
ap.add_argument("zh")
ap.add_argument("out_dir")
ap.add_argument("--ja-max", "--ja", type=float, default=10.0, dest="ja_max")
a = ap.parse_args()


ja_counts, ja_scale = load_counts(a.ja, a.tokenizer)
zh_counts, zh_scale = load_counts(a.zh, a.tokenizer)
ids_of = {}
for i, s in token_texts(a.tokenizer).items():
    if s is not None and kanji_word(s.strip()):
        ids_of.setdefault(s.strip(), []).append(i)


def count(counts, ids):
    return sum(int(counts[i]) for i in ids if i < len(counts))


rows = sorted(((w, count(ja_counts, ids) * ja_scale, count(zh_counts, ids)) for w, ids in ids_of.items()),
              key=lambda r: (-r[1], -r[2], r[0]))
banned = [w for w, fj, nz in rows if fj < a.ja_max and nz >= 1]

out = pathlib.Path(a.out_dir)
out.mkdir(parents=True, exist_ok=True)
(out / "freq.tsv").write_text("text\tja_per_1e8\tzh_per_1e8\n" +
                              "".join(f"{w}\t{fj:.2f}\t{nz * zh_scale:.2f}\n" for w, fj, nz in rows), encoding="utf-8")
head = (f"# Kanji-only token texts that Japanese Wikipedia's Japanese sentences hold under {a.ja_max:g} times per 1e8\n"
        "# tokens and Chinese Wikipedia's Chinese sentences hold at least once.\n")
(out / "zh-words.txt").write_text(head + "".join(w + "\n" for w in banned), encoding="utf-8")
ones = sum(1 for w in banned if len(w) == 1)
print(f"{len(rows)} kanji-only token texts; banned {len(banned)} ({len(banned) - ones} of two or more kanji, "
      f"{ones} single kanji)")
