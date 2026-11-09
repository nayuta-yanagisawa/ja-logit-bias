# Evaluation

How the list was evaluated on Qwen3.8-Flash-Next: the setup, the results of every condition, the speed, and the files behind each figure. `python3 eval/summarize.py` recomputes every reading and comparison figure below from `results/`.

## Setup

`prompts.json` holds 56 Japanese requests, each with its text (`p`) and a category (`cat`): technical explanation (`tech`, 12), code (`code`, 8), business writing (`biz`, 8), casual chat (`casual`, 8), translation and summary (`trans`, 8), questions about China (`china`, 8) and formal essays (`formal`, 4). In each condition the model answered every request twice, so a condition has 112 answers; `rep` (0 or 1) says which asking an answer is.

- Model: Qwen3.8-Flash-Next, IQ3_S quantization.
- Server: [Strata](https://github.com/Niko1221/Strata) v0.2.10 for rounds 1 to 3, v0.2.12 for rounds 4 and 5. Strata ran with speculative decoding: a small draft model (DFlash2) proposes tokens and Qwen3.8-Flash-Next accepts or rejects them.
- System prompt: the one [Pi](https://pi.dev), a coding agent for the terminal, sends, since the list is meant for a coding agent. It holds the evaluator's local paths and instructions, so it is not published, and the runs cannot be repeated exactly. Under it the model sometimes answers with a tool call that writes a file instead of prose.
- Thinking: `reasoning_effort` `medium`.
- Sampling: the model card's values (temperature 1.0, top_p 0.95, top_k 20), unless the condition says otherwise.
- Output limit: 6,000 tokens. The longest answer is 5,519 tokens.

`scripts/eval.py` sends the requests and collects the answers: `--system` takes a system prompt file, `--system-extra` text appended to it, `--bias` a `logit_bias` file, and `--extra` JSON merged into each request, such as `'{"reasoning_effort": "medium", "min_p": 0.05}'`. It prints rough counts of its own (kanji outside JIS X 0208, a few Chinese function words); the figures here come from the readings instead.

## Lists

- The current list: `data/qwen3.8-flash-next/logit_bias.json`, built by the rules in the repository's README (42,125 tokens).
- The earlier list: an earlier version (40,130 tokens, `git show 7f4cc54:data/qwen3.8-flash-next/logit_bias.json`). Its word rule judged only tokens of two or more kanji, required at least 5 occurrences per 100 million tokens of Chinese sentences, and kept an allowlist of words it would otherwise have banned.
- The character-rule list: the tokens of the character rule alone (24,795 tokens).

## Results

Answers that were only a tool call are left out (see Counting). "All answers" counts every answer with prose; "China left out" leaves out the 16 answers to questions about China, some of which ask for Chinese.

| Round | Condition (file in `results/`) | Chinese, all answers | Chinese, China left out | Odd wording |
|---|---|---|---|---|
| 5 | Nothing (`none-v0.2.12`) | 44/101 (44%) | 30/85 (35%) | 55/101 (54%) |
| 5 | System prompt instruction (`system-prompt-v0.2.12`) | 46/103 (45%) | 34/87 (39%) | 50/103 (49%) |
| 5 | Current list + min_p 0.05 (`current-minp0.05`) | 11/103 (11%) | 3/87 (3%) | 46/103 (45%) |
| 4 | Earlier list + min_p 0.05 (`earlier-minp0.05`) | 6/105 (6%) | 2/89 (2%) | 57/105 (54%) |
| 4 | Current list + min_p 0.05 (`current-minp0.05`) | 8/103 (8%) | 3/87 (3%) | 44/103 (43%) |
| 3 | Earlier list + min_p 0.05 (`bias-minp0.05`) | 10/101 (10%) | 6/85 (7%) | 51/101 (50%) |
| 3 | Earlier list + min_p 0.05 + temperature 0.7 (`bias-minp0.05-temp0.7`) | 5/103 (5%) | 2/87 (2%) | 44/103 (43%) |
| 2 | Earlier list (`bias`) | 11/106 (10%) | 5/90 (6%) | 61/106 (58%) |
| 2 | Earlier list + min_p 0.05 (`bias-minp0.05`) | 11/101 (11%) | 6/85 (7%) | 48/101 (48%) |
| 2 | Earlier list + min_p 0.1 (`bias-minp0.1`) | 8/100 (8%) | 5/84 (6%) | 50/100 (50%) |
| 1 | Nothing (`none`) | 49/103 (48%) | 34/87 (39%) | 49/103 (48%) |
| 1 | System prompt instruction (`system-prompt`) | 43/105 (41%) | 29/89 (33%) | 47/105 (45%) |
| 1 | Character-rule list (`char-rule`) | 31/103 (30%) | 23/87 (26%) | 57/103 (55%) |
| 1 | Earlier list (`bias`) | 13/106 (12%) | 7/90 (8%) | 65/106 (61%) |

Codex's readings shift somewhat from round to round: the same 106 answers of `bias` had odd wording in 65 in round 1 and in 61 in round 2. So conditions are compared only within a round. A comparison pairs the two conditions' answers to the same request and the same asking, counts the pairs where only one of the two has the problem, and applies a sign test to those counts. The counts below are over all answers.

- Round 5, current list against nothing: Chinese only without the list in 33 pairs, only with it in 0 (p < 0.001). Odd wording 20 against 10 (p = 0.10). Outside questions about China, the Chinese left with the list was 案例 spelled one kanji per token, 茑屋書店 and 給與.
- Round 5, system prompt instruction against nothing: Chinese 18 pairs each way (p = 1.0); odd wording 26 without, 20 with (p = 0.46).
- Round 4, current list against earlier list: Chinese only with the earlier list in 4 pairs, only with the current one in 6 (p = 0.75); odd wording 26 against 15 (p = 0.12). Outside questions about China, the current list let through the same three as in round 5: 案例, 茑屋書店 and 給與.
- Round 3, temperature 0.7 against 1.0, both with the earlier list and min_p 0.05: Chinese only at 1.0 in 8 pairs, only at 0.7 in 3 (p = 0.23); odd wording 24 against 16 (p = 0.27). Neither is beyond chance, so the model card's 1.0 is kept.
- Round 2, min_p with the earlier list: odd wording only with the list alone in 26 pairs, only with min_p 0.05 in 16 (p = 0.16); against min_p 0.1, 20 and 14 (p = 0.39). Chinese 9 each way with 0.05 (p = 1.0), 9 against 6 with 0.1 (p = 0.61).
- Round 1, each against nothing: the earlier list removed Chinese, only without it in 38 pairs and only with it in 2 (p < 0.001), and added odd wording, only with it in 26 pairs and only without in 12 (p = 0.034). The character-rule list: Chinese 28 against 10 (p = 0.005), odd wording 17 against 24 (p = 0.35). The system prompt instruction: Chinese 20 against 12 (p = 0.22), odd wording 21 against 19 (p = 0.88).

Rounds 1 to 3 also had Codex put two answers to the same request and asking side by side, conditions hidden, and pick the better reply and the more natural Japanese (`results/codex-pairs.jsonl`).

| Round | Pair | Better reply | More natural Japanese |
|---|---|---|---|
| 1 | earlier list – nothing | 52 – 44, 7 ties (p = 0.48) | 49 – 41, 13 ties (p = 0.46) |
| 2 | min_p 0.05 – list alone | 51 – 42, 7 ties (p = 0.41) | 50 – 34, 16 ties (p = 0.10) |
| 2 | min_p 0.1 – list alone | 51 – 42, 7 ties (p = 0.41) | 50 – 31, 19 ties (p = 0.045) |
| 3 | temperature 0.7 – 1.0 | 48 – 45, 7 ties (p = 0.84) | 43 – 36, 21 ties (p = 0.50) |

## Speed

Measured on Strata v0.2.12 with 8 of the requests (every seventh: 0, 7, …, 49). Each was sent twice without a ban and twice with the current list and `min_p` 0.05, one request at a time, alternating which went first. The server's own timings give the decoding speed apart from reading the prompt: 82.8 tok/s without the list and 80.5 with it. Single requests ranged from 65.9 to 94.4 tok/s without the list and from 64.6 to 90.8 with it. The draft model's proposals were accepted at the rate 0.658 and 0.647.

A one-token request, sent 12 times each way and alternating, took a median 0.078 s without the list and 0.085 s with it: receiving the 670 KB list costs a few milliseconds.

`speed.json` holds both: under `decode`, one row per request with `prompt` (the index in `prompts.json`), `rep`, `list` (whether the list was sent) and the server's `prompt_n`, `prompt_ms`, `predicted_n`, `predicted_ms`, `draft_n` and `draft_n_accepted`; under `one_token`, one row per request with `list` and `secs`.

## Files in `results/`

Each answer file holds one condition's 112 answers: `prompt` (the index in `prompts.json`), `cat`, `rep`, `secs` (the request's wall time), `tokens` (the completion tokens the server reports) and `text` (the answer without its thinking). Paths of the evaluator's machine in the answers are replaced by `/tmp/work` and `/home/user`.

| File | Condition | Server | Rounds read |
|---|---|---|---|
| `none.json` | no ban | v0.2.10 | 1 |
| `system-prompt.json` | the instruction below appended to the system prompt | v0.2.10 | 1 |
| `char-rule.json` | the character-rule list | v0.2.10 | 1 |
| `bias.json` | the earlier list | v0.2.10 | 1, 2 |
| `bias-minp0.05.json` | the earlier list, `min_p` 0.05 | v0.2.10 | 2, 3 |
| `bias-minp0.1.json` | the earlier list, `min_p` 0.1 | v0.2.10 | 2 |
| `bias-minp0.05-temp0.7.json` | the earlier list, `min_p` 0.05, temperature 0.7 | v0.2.10 | 3 |
| `earlier-minp0.05.json` | the earlier list, `min_p` 0.05 | v0.2.12 | 4 |
| `current-minp0.05.json` | the current list, `min_p` 0.05 | v0.2.12 | 4, 5 |
| `none-v0.2.12.json` | no ban | v0.2.12 | 5 |
| `system-prompt-v0.2.12.json` | the instruction below appended to the system prompt | v0.2.12 | 5 |

`bias-minp0.05.json` and `earlier-minp0.05.json` are the same condition on two server versions; round 4 needed answers from the same server as the current list's. `none-v0.2.12.json` and `system-prompt-v0.2.12.json` were generated by two runs at once, so their `secs` cannot be compared with the other files'.

The instruction appended to the system prompt:

> Write every reply to the user in natural Japanese. Never mix Chinese into it: no Simplified Chinese characters, no Chinese words, no Chinese punctuation such as ， or ：. Use Japanese kanji forms (e.g. 選択, 検査, 拡張) and Japanese punctuation (、。).

`codex-reading.jsonl` holds one reading per answer per round: `round`, `cond` (the answer file's name), `prompt`, `rep`, the Chinese items found (`zh`) and the odd items (`odd`). `codex-pairs.jsonl` holds the side-by-side comparisons: `round`, `prompt`, `rep`, the condition shown first (`A`) and second (`B`), the condition chosen for `better` and for `japanese` (or `tie`), and Codex's one-sentence `reason`.

## Reading

The reader was OpenAI's gpt-6.1-sol through Codex, with reasoning effort high. For each round, the answers of that round's conditions were shuffled together and split into batches of 56. Each batch went to a new Codex session as lines of `{"id", "request", "answer"}`, with the instructions in `codex-task-reading.md`; side-by-side comparisons went as pairs of answers with `codex-task-pairs.md`. Codex returned one line of labels per id, and the ids were mapped back to condition, request and asking.

## Counting

- Answers that were only a tool call are left out, and so is any comparison that holds one, since they hold no prose to read. This drops 6 to 12 answers per condition.
- Items made only of punctuation such as ： and ？ are not counted as Chinese. The reading instructions list them as Chinese punctuation, but Japanese uses them too.
- Each reading is one model's single judgement, and single items can be wrong. The figures are for comparing conditions within a round.
