#!/usr/bin/env python3
"""Writes the logit_bias that keeps a model's Japanese free of Chinese.

    make_bias.py TOKENIZER_JSON ZH_WORDS OUT.json [--value -100]

Bans two kinds of token:
  - every token whose text holds a kanji outside JIS X 0208, the character set of ordinary Japanese text (the four
    jōyō kanji 𠮟 塡 剝 頰 stay allowed). This removes Simplified forms such as 检 and 们.
  - every token whose text, without its leading space, is a line of ZH_WORDS (make_zh_words.py). This removes Chinese
    words written in characters Japanese shares, such as 序号 and 可以, and single kanji such as 个.
OUT.json maps each banned token id to --value, the shape OpenAI-compatible servers take as `logit_bias`.
"""
import argparse

from common import is_han, jis_ok, read_words, token_texts, write_json

ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
ap.add_argument("tokenizer")
ap.add_argument("zh_words")
ap.add_argument("out")
ap.add_argument("--value", type=float, default=-100)
a = ap.parse_args()

words = set(read_words(a.zh_words))
by_char = by_word = 0
bias = {}
for i, s in token_texts(a.tokenizer).items():
    if s is None:   # part of a character: it cannot be judged alone
        continue
    if any(is_han(c) and not jis_ok(c) for c in s):
        by_char += 1
    elif s.strip() in words:
        by_word += 1
    else:
        continue
    bias[str(i)] = int(a.value) if a.value == int(a.value) else a.value
write_json(a.out, bias)
print(f"banned {len(bias)} tokens: {by_char} by character, {by_word} by word ({len(words)} words); wrote {a.out}")
