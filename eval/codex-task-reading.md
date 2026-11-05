# Task: find Chinese in Japanese answers

`answers.jsonl` holds answers that a language model wrote to Japanese requests. Each line is
`{"id": ..., "request": ..., "answer": ...}`. Read every answer in full.

For each answer, list every place where it writes Chinese instead of Japanese:
- Chinese words or grammar written in kanji that Japanese shares (可以, 进行, 序号, 激活, 的话, 一下子).
- Simplified Chinese character forms (检查 for 検査, 们, 这).
- Chinese punctuation in Japanese prose (，：；？！ used as full-width Chinese marks).
- Traditional Chinese forms that Japanese does not use (國家, 說明).

Do not list:
- Chinese names of people, places, companies, dishes or works, written as Japanese writes them (北京, 習近平, 麻婆豆腐).
- Chinese text the request itself asked for (for example 你好 and 谢谢 when the request asks about Chinese greetings),
  as long as the answer presents it as Chinese.
- Code, commands, identifiers and URLs.
- Rare, literary or technical words that are correct Japanese.

Separately, list wording that is neither Chinese nor natural Japanese: a wrong or odd kanji, a garbled or split word,
a word replaced by a strange substitute. Leave out ordinary stylistic choices.

Write `labels.jsonl`, one line per answer, in the input order:
`{"id": ..., "zh": ["each Chinese item, quoted exactly as it appears", ...], "odd": ["each odd item", ...]}`
Use empty lists when there is nothing. Every input id must appear exactly once. Judge each answer on its own.
