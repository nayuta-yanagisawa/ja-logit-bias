#!/usr/bin/env python3
"""Counts how often each token occurs in the Japanese or Chinese sentences of a Wikipedia dump.

    count_corpus.py --lang ja PARQUET_DIR TOKENIZER_JSON OUT.npz [--threads 4]

PARQUET_DIR holds the parquet files of the wikimedia/wikipedia dataset on Hugging Face (20231101.ja or 20231101.zh).
A line counts as a Japanese sentence when at least five of its characters, and at least a tenth, are hiragana. That
keeps out Chinese names, titles and quotations that Japanese articles hold alone on a line. A line counts as a Chinese
sentence when it holds five or more ideographs and no kana. Writes `counts` (one integer per token id), `tokens`
(the number of tokens counted) and `tokenizer_sha256`, which make_zh_words.py checks before it uses the counts.
"""
import argparse
import glob
import os
import re
import time

ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
ap.add_argument("parquet_dir")
ap.add_argument("tokenizer")
ap.add_argument("out")
ap.add_argument("--lang", choices=["ja", "zh"], required=True)
ap.add_argument("--threads", type=int, default=4)
a = ap.parse_args()
os.environ["RAYON_NUM_THREADS"] = str(a.threads)
os.environ["TOKENIZERS_PARALLELISM"] = "true"
import numpy as np                      # noqa: E402  (after the thread settings, which the libraries read at import)
import pyarrow.parquet as pq            # noqa: E402
from tokenizers import Tokenizer        # noqa: E402

from common import file_sha256          # noqa: E402

tok = Tokenizer.from_file(a.tokenizer)
V = tok.get_vocab_size(with_added_tokens=True)
counts = np.zeros(V, dtype=np.int64)
HIRA = re.compile(r"[ぁ-ゟ]")
KANA = re.compile(r"[ぁ-ヿ]")
HAN = re.compile(r"[一-鿿]")
files = sorted(glob.glob(os.path.join(a.parquet_dir, "*.parquet")))
if not files:
    raise SystemExit(f"no parquet file in {a.parquet_dir}")
kept = seen = ntok = 0
t0 = time.time()
for fi, f in enumerate(files):
    pf = pq.ParquetFile(f)
    for rg in range(pf.num_row_groups):
        batch = []
        for text in pf.read_row_group(rg, columns=["text"]).column("text").to_pylist():
            for line in text.split("\n"):
                seen += 1
                if a.lang == "ja":
                    h = len(HIRA.findall(line))
                    keep = h >= 5 and h * 10 >= len(line)
                else:
                    keep = len(HAN.findall(line)) >= 5 and not KANA.search(line)
                if keep:
                    batch.append(line)
        kept += len(batch)
        for i in range(0, len(batch), 20000):
            encs = tok.encode_batch(batch[i:i + 20000], add_special_tokens=False)
            ids = np.concatenate([np.asarray(e.ids, dtype=np.int64) for e in encs] or [np.zeros(0, np.int64)])
            ntok += len(ids)
            counts += np.bincount(ids, minlength=V)[:V]
    print(f"file {fi + 1}/{len(files)}: {kept}/{seen} lines kept, {ntok} tokens, {(time.time() - t0) / 60:.1f} min",
          flush=True)
np.savez_compressed(a.out, counts=counts, tokens=ntok, lines=kept, tokenizer_sha256=file_sha256(a.tokenizer))
print(f"done: wrote {a.out}")
