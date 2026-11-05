# 評価

リポジトリの README の「評価」の数字が、どの回答とどの判定から出たかをまとめます。

## 回答

`prompts.json` の日本語の依頼 56 本を、条件ごとに 2 回ずつ答えさせました（各 112 本）。

- モデル：Qwen3.8-Flash-Next の IQ3_S（ISTA-DASLab の GSQ-RCO 版）
- サーバー：Strata v0.2.10。下書きのモデル DFlash2 を使っています。
- 思考：`reasoning_effort` は `medium` です。
- サンプリング：モデルカードの値です（温度 1.0、top_p 0.95、top_k 20）。
- システムプロンプト：端末で動くコーディングエージェント Pi が送るものです。このリポジトリには入れていません。
- 出力の上限：6,000 トークンです。上限で切れた回答はありませんでした。

`results/` の各ファイルは、1 つの条件の 112 本の回答です。`prompt` は `prompts.json` の何番目の依頼か、`rep` は何回目か、`text` は回答の本文（思考を除く）です。

| ファイル | 条件 |
|---|---|
| `none.json` | 何もしない |
| `system-prompt.json` | システムプロンプトの末尾に、次の英文の指示を足す |
| `char-rule.json` | 文字の規則だけの logit_bias（24,795 トークン） |
| `bias.json` | `data/qwen3.8-flash-next/logit_bias.json`（40,130 トークン） |
| `bias-minp0.05.json` | 同じ logit_bias に、`min_p` 0.05 |
| `bias-minp0.1.json` | 同じ logit_bias に、`min_p` 0.1 |
| `bias-minp0.05-temp0.7.json` | 同じ logit_bias に、`min_p` 0.05 と温度 0.7 |

システムプロンプトに足した指示は、次のとおりです。

> Write every reply to the user in natural Japanese. Never mix Chinese into it: no Simplified Chinese characters, no Chinese words, no Chinese punctuation such as ， or ：. Use Japanese kanji forms (e.g. 選択, 検査, 拡張) and Japanese punctuation (、。).

`scripts/eval.py` で同じ形の回答を集められます。`--system` にシステムプロンプトのファイルを、`--extra '{"reasoning_effort": "medium"}'` で思考の強さを渡します。

DeepSeek-V4.1-Flash の回答は `deepseek/results/` にあります。DeepSeek-V4.1-Flash-1017（ISTA-DASLab の IQ2_XXS）を Strata v0.2.7（`strata/` のパッチを当てたもの）で動かし、`none`、`bias`、`bias-minp0.05` の 3 条件を 1 回ずつ答えさせました。どの条件も、システムプロンプトの末尾に次の一文を足し、`reasoning_budget_tokens` を 2,048 にしています。

> Keep every reply concise: lead with the answer, cover what the request asks, and leave out background, caveats and summaries the reader did not ask for.

`python3 eval/summarize.py eval/deepseek/results` で集計し直せます。

## 判定

回答はすべて、OpenAI の gpt-6.1-sol（Codex、推論の強さ high）に読ませました。どの条件の回答かは伏せ、条件を混ぜた順に 56 本ずつ渡しています。指示は `codex-task-reading.md` と `codex-task-pairs.md` です。

- 読み取り（`results/codex-reading.jsonl`）：回答ごとに、中国語の語や字の箇所（`zh`）と、中国語ではないが不自然な日本語の箇所（`odd`）を挙げさせました。
- 比較（`results/codex-pairs.jsonl`）：同じ依頼への 2 つの回答を、どちらの条件かを伏せて並べ、全体としてよいほう（`better`）と、日本語として自然なほう（`japanese`）を選ばせました。

判定は 3 回に分けて行いました。`round` がその回です。

| 回 | 読み取り | 比較 |
|---|---|---|
| 1 | `none`、`system-prompt`、`char-rule`、`bias` | `none` 対 `bias` |
| 2 | `bias`、`bias-minp0.05`、`bias-minp0.1` | `bias` 対 `bias-minp0.05`、`bias` 対 `bias-minp0.1` |
| 3 | `bias-minp0.05`、`bias-minp0.05-temp0.7` | `bias-minp0.05` 対 `bias-minp0.05-temp0.7` |

`bias` は 1 回目と 2 回目に、`bias-minp0.05` は 2 回目と 3 回目に読ませています。同じ回答への判定は、回をまたいでもほぼ同じでした（不自然な箇所を含む回答は、`bias` が 65 本と 61 本、`bias-minp0.05` が 48 本と 51 本）。

## 集計の決まり

リポジトリの README の数字は、`python3 eval/summarize.py` で、この下の決まりのとおりに集計し直せます。

- ツール呼び出しの回答は除く：システムプロンプトがコーディングエージェントのものなので、条件ごとに 6〜12 本の回答が、文章を書かずにファイルを書き込むツール呼び出しになりました。読む文章がないので、これらの回答と、これらを含む比較は数えません。回答の中の手元のパスは `/tmp/work` と `/home/user` に置き換えてあります。
- 句読点は数えない：指示では「：」「？」なども中国語の句読点として挙げさせました。ただ、これらは日本語でも使うので、集計では句読点だけの項目を除きました。
- 中国が話題の依頼の扱い：`cat` が `china` の依頼 8 本は、「你好」「谢谢」の説明のように、中国語を書くこと自体が求められる場合を含みます。そのため、この 8 本を除いた数も示しています。
- 判定の限界：Codex の判定は、1 つのモデルによる 1 回の判定で、個々の項目には誤りが含まれることがあります。数字は、条件のあいだの差を見るためのものです。
