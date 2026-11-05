# Task: compare two Japanese answers to the same request

`pairs.jsonl` holds pairs of answers that language models wrote to the same Japanese request. Each line is
`{"id": ..., "request": ..., "A": ..., "B": ...}`. Read both answers in full.

Judge which answer is the better reply to a Japanese reader: correct and complete content, natural Japanese, fitting
the request. Do not prefer an answer for its length alone.

Write `labels.jsonl`, one line per pair, in the input order:
`{"id": ..., "better": "A" | "B" | "tie", "japanese": "A" | "B" | "tie", "reason": "one short sentence"}`
`better` is the overall judgement; `japanese` judges only how natural and correct the Japanese is. Every input id must
appear exactly once.
