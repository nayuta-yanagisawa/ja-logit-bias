# ja-logit-bias

LLMs trained on large amounts of Chinese, such as Qwen, sometimes mix Chinese into Japanese answers. Japanese and Chinese share many kanji tokens, and the model drifts from one language into the other: it writes 検査 in its Simplified form 检查, or writes a Chinese word in characters Japanese shares, 序号 for 連番 or 可以 for できる. This repository holds a `logit_bias` for Qwen3.8-Flash-Next that keeps such tokens from being generated, with no retraining of the model.

The list is `data/qwen3.8-flash-next/logit_bias.json`. Its token ids are those of Qwen3.8-Flash-Next's tokenizer, so it fits any build of that model that keeps the tokenizer, whatever the quantization. No other model is covered: the scripts accept another tokenizer, but no list for one has been built or evaluated.

## Effect

The list was evaluated where it is meant to be used, in a coding agent. Qwen3.8-Flash-Next answered 56 Japanese requests, each asked twice, under the system prompt of [Pi](https://pi.dev), a coding agent for the terminal. The requests cover technical explanations, code, business writing, casual chat, translation, formal essays and questions about China. OpenAI's gpt-6.1-sol, run through Codex, then read every answer without knowing which condition produced it, and listed the Chinese in it and its odd wording: wording that is neither Chinese nor natural Japanese, such as a wrong kanji, a garbled word or an English word in place of a Japanese one.

| Condition | Answers with Chinese, requests about China left out | Answers with odd wording |
|---|---|---|
| Nothing | 30/85 (35%) | 55/101 (54%) |
| System prompt says "do not mix in Chinese" | 34/87 (39%) | 50/103 (49%) |
| This list, with `min_p` 0.05 | 3/87 (3%) | 46/103 (45%) |

The counts leave out answers that were only a tool call writing a file (9 to 11 of 112 per condition), since they hold no prose. The Chinese column also leaves out the 16 answers to requests about China, some of which ask for Chinese.

The list removed nearly all the Chinese. Pairing the two conditions' answers to the same request and the same asking, 33 pairs had Chinese only without the list and none only with it (sign test p < 0.001). The instruction in the system prompt made no measurable difference: 18 pairs each way. Odd wording did not become more common with the list: 20 pairs had it only without the list and 10 only with it (p = 0.10). The three answers that kept Chinese held 案例 spelled one kanji per token, 茑屋書店 and 給與.

Pi's system prompt holds the evaluator's local paths and instructions and is not published, so the evaluation cannot be repeated exactly. The setup, every condition measured, the paired tests and the data are in [`eval/README.md`](eval/README.md).

## Usage

A server that takes an OpenAI-style `logit_bias` (`{"token id": -100, ...}`) needs only that field added to the request:

```python
import json, urllib.request

bias = json.load(open("data/qwen3.8-flash-next/logit_bias.json"))
body = {
    "model": "qwen3.8-flash-next",
    "messages": [{"role": "user", "content": "冪等性とは何か説明してください。"}],
    "logit_bias": bias,
    "min_p": 0.05,
}
req = urllib.request.Request("http://localhost:8080/v1/chat/completions", data=json.dumps(body).encode(),
                             headers={"Content-Type": "application/json"})
print(json.load(urllib.request.urlopen(req))["choices"][0]["message"]["content"])
```

The list holds 42,125 tokens, 670 KB of JSON that goes with every request. On [Strata](https://github.com/Niko1221/Strata), the inference server used here, it hardly slows generation: decoding ran at 80.5 tok/s with the list and 82.8 without, while single requests ranged from 65 to 94 tok/s, and the list added a few milliseconds to each request.

`min_p` 0.05 is part of the measured setup, but it is not in OpenAI's API, and some servers do not take it. The list without it has not been measured. An earlier, smaller version of the list without `min_p` made odd wording more common than no ban (only the banned answer was odd in 26 pairs, only the unbanned one in 12, p = 0.034): where the model starts to drift into Chinese, the ban can push it into English or a garbled word instead. With `min_p` 0.05 such answers were fewer, 16 pairs against 26, though within chance (p = 0.16).

The list has been used only with Strata v0.2.10 and v0.2.12, serving Qwen3.8-Flash-Next. In Pi, put `"logit_bias": {...}` and `"min_p": 0.05` in the model's `samplingParams` in `~/.pi/agent/models.json`. llama.cpp, vLLM and SGLang take an OpenAI-style `logit_bias` according to their documentation or source, but have not been tried. Ollama does not take `logit_bias`.

## The banned tokens

Two rules choose the tokens, and each gets a bias of -100, which most servers treat as "never generate". The list follows from a character set, token counts from Wikipedia and the fixed settings below; no word on it was chosen by hand.

### The character rule

A token is banned when it contains a kanji outside JIS X 0208, the character set of ordinary Japanese text. The four jōyō kanji of 2010 that JIS X 0208 lacks (𠮟 塡 剝 頰) stay allowed. This removes Simplified forms such as 检 and 们, and the model writes Japanese instead (検, 達). It bans 24,795 tokens.

The larger Japanese set JIS X 0213 is not used, because its third and fourth levels include many Simplified forms (开 关 么 种 and others).

### The word rule

Chinese written in characters Japanese shares, such as 序号 and 可以, passes the character rule. So every token made only of kanji within JIS X 0208, one kanji or more, is counted in Japanese and in Chinese Wikipedia. A token is banned when it occurs under 10 times per 100 million tokens of Japanese sentences and at least once in Chinese sentences. This bans 17,330 tokens: 16,902 of two or more kanji and 428 single kanji.

- Japanese sentences are lines of Japanese Wikipedia in which hiragana make up at least five characters and at least a tenth of the line. This leaves out Chinese names and quotations standing alone on a line.
- Chinese sentences are lines of Chinese Wikipedia with five or more ideographs and no kana.
- The threshold of 10 was set by hand.

Single kanji are included because some Simplified forms are inside JIS X 0208 (个 从 网 气), and Chinese words are sometimes written one kanji per token.

### Cost to Japanese

Of the tokens in Japanese Wikipedia's Japanese sentences, 0.0198% are banned (character rule 0.0036%, word rule 0.0162%); of those in Chinese Wikipedia's Chinese sentences, 23%. The ban is on tokens, not on strings, so a banned word can still be spelled with smaller tokens, though the model seldom does (see Limits).

## Limits

- Simplified Chinese cannot be written: no translation into Chinese, no quotation, not even a greeting such as 谢谢.
- Rare Japanese words can become unwritable. In a quick check in Pi, outside the evaluation, the model was asked to write three banned words, 摘要, 塑造 and 蚯蚓; it wrote 要約, "to shape" and a wrong kanji, 螻, instead of spelling them one kanji per token.
- Characters that Japanese uses 10 or more times per 100 million tokens are not banned even as single-kanji tokens. They include Traditional forms such as 從 數 點 寫 and characters of Chinese words such as 爬, so the Chinese word 爬行者 can still be written as 爬 + 行者. The same goes for Chinese words that Japanese uses now and then, such as 科技.
- A Simplified character with no token of its own cannot be banned, because it is spelled with byte tokens shared with other characters. Asked for rainy-day plans in Tokyo, the model wrote the bookstore 蔦屋書店 as 茑屋書店 in 6 of 14 answers with a ban, as often as without one (4 of 8).
- Chinese renderings of foreign names written in shared characters pass, such as 麦肯吉 for McKinsey.
- The ban keeps the model from writing Chinese, not from drifting toward it. Where it drifts, it may write English or a garbled word instead.

## Rebuilding the list

```sh
pip install -r requirements.txt
./build.sh Qwen/Qwen3.8-Flash-Next qwen3.8-flash-next
```

`build.sh` downloads the model's `tokenizer.json` and writes `data/qwen3.8-flash-next/`. It reuses the token counts already there when they were made with the same `tokenizer.json`; otherwise it downloads the 2023-11-01 dumps of Japanese and Chinese Wikipedia (about 5.4 GB together) and counts them, which takes about 10 minutes on 8 threads. To try another threshold, run the last two commands of `build.sh` by hand, with `--ja` on `make_zh_words.py`.

Another model would need its own list, since token ids differ between tokenizers. `./build.sh <Hugging Face repository> <name>` builds one the same way, but whether the rules work for that model, and what they cost it, has to be measured there (`scripts/eval.py`, [`eval/README.md`](eval/README.md)).

## Files

| Path | Contents |
|---|---|
| `build.sh` | downloads the inputs, then runs `count_corpus.py`, `make_zh_words.py` and `make_bias.py` |
| `scripts/count_corpus.py` | counts the tokens in Wikipedia's sentences |
| `scripts/make_zh_words.py` | chooses the tokens the word rule bans |
| `scripts/make_bias.py` | writes the `logit_bias` from the character rule and the word list |
| `scripts/eval.py` | sends the Japanese requests to a server and collects the answers |
| `data/qwen3.8-flash-next/` | Qwen3.8-Flash-Next's token counts, banned words and `logit_bias.json` |
| `eval/` | the evaluation: requests, answers, readings, timings, and `summarize.py`, which recomputes the figures |

## License

The scripts are under the MIT License and the data under CC BY 4.0. The counts come from Wikipedia, and the token ids are those of Qwen's tokenizer. `NOTICE.md` has the details.
