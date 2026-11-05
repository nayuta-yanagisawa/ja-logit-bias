#!/usr/bin/env python3
"""Chooses the Chinese words to ban: kanji-only tokens that Japanese text almost never holds but Chinese text does.

    make_zh_words.py TOKENIZER_JSON JA.npz ZH.npz OUT_DIR [--allow data/ja-allow.txt] [--ja 10] [--zh 5]
                     [--review-min 1]

JA.npz and ZH.npz come from count_corpus.py with the same TOKENIZER_JSON. A token text of two or more kanji, all inside JIS X 0208, is banned when
the Japanese count is under --ja per 1e8 tokens and the Chinese count is at least --zh per 1e8, unless the allowlist
holds it. The counts of a text add up every token that spells it, with or without a leading space.

Writes into OUT_DIR:
  freq.tsv      every kanji-only token text with its Japanese and Chinese counts per 1e8 tokens
  zh-words.txt  the banned texts
  review.txt    the banned texts that Japanese text holds at least --review-min times per 1e8 tokens: the ones worth
                a human look, since banning a Japanese word among them costs the most. A word rarer than that occurs
                about once in 1e8 tokens of Japanese at most, so a wrong ban there costs little.
"""
import argparse
import pathlib

from common import kanji_word, load_counts, read_words, token_texts

ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
ap.add_argument("tokenizer")
ap.add_argument("ja")
ap.add_argument("zh")
ap.add_argument("out_dir")
ap.add_argument("--allow", default=str(pathlib.Path(__file__).resolve().parent.parent / "data" / "ja-allow.txt"))
ap.add_argument("--ja-max", "--ja", type=float, default=10.0, dest="ja_max")
ap.add_argument("--zh-min", "--zh", type=float, default=5.0, dest="zh_min")
ap.add_argument("--review-min", type=float, default=1.0)
a = ap.parse_args()


ja_counts, ja_scale = load_counts(a.ja, a.tokenizer)
zh_counts, zh_scale = load_counts(a.zh, a.tokenizer)
ids_of = {}
for i, s in token_texts(a.tokenizer).items():
    if s is not None and kanji_word(s.strip()):
        ids_of.setdefault(s.strip(), []).append(i)


def freq(counts, scale, ids):
    return sum(int(counts[i]) for i in ids if i < len(counts)) * scale


rows = sorted(((w, freq(ja_counts, ja_scale, ids), freq(zh_counts, zh_scale, ids)) for w, ids in ids_of.items()),
              key=lambda r: (-r[1], -r[2], r[0]))
allow = set(read_words(a.allow)) if a.allow else set()
banned = [(w, fj, fz) for w, fj, fz in rows if fj < a.ja_max and fz >= a.zh_min and w not in allow]
review = [w for w, fj, _ in banned if fj >= a.review_min]

out = pathlib.Path(a.out_dir)
out.mkdir(parents=True, exist_ok=True)
(out / "freq.tsv").write_text("text\tja_per_1e8\tzh_per_1e8\n" +
                              "".join(f"{w}\t{fj:.2f}\t{fz:.2f}\n" for w, fj, fz in rows), encoding="utf-8")
head = (f"# Kanji-only token texts that Japanese Wikipedia's Japanese sentences hold under {a.ja_max:g} times per 1e8\n"
        f"# tokens and Chinese Wikipedia's Chinese sentences at least {a.zh_min:g} times, less the allowlist "
        f"({len(allow)} words).\n")
(out / "zh-words.txt").write_text(head + "".join(w + "\n" for w, _, _ in banned), encoding="utf-8")
(out / "review.txt").write_text("".join(w + "\n" for w in review), encoding="utf-8")
print(f"{len(rows)} kanji-only token texts; banned {len(banned)}; {len(review)} of them occur in Japanese text at "
      f"least {a.review_min:g} times per 1e8 tokens (review.txt)")
