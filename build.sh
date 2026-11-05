#!/bin/bash
# Rebuilds a model's word list and logit_bias from the Wikipedia dumps.
#
#   ./build.sh HF_REPO NAME [WORK_DIR]
#   ./build.sh Qwen/Qwen3.8-Flash-Next qwen3.8-flash-next
#
# Downloads the model's tokenizer.json and the 20231101 Japanese and Chinese Wikipedia dumps (about 5.4 GB) into
# WORK_DIR (default ./work), counts the tokens of each (about 10 minutes on 8 threads), and writes data/NAME/.
# Counts already in data/NAME/ that were made with this very tokenizer.json skip the download and the count.
# REVISION picks a revision of the model repository (default main). Needs Python 3 with tokenizers,
# numpy and pyarrow (requirements.txt), and the `hf` command of huggingface_hub. PYTHON picks the interpreter.
set -euo pipefail
repo=${1:?usage: build.sh HF_REPO NAME [WORK_DIR]}
name=${2:?usage: build.sh HF_REPO NAME [WORK_DIR]}
work=${3:-work}
here=$(cd "$(dirname "$0")" && pwd)
out=$here/data/$name
threads=${THREADS:-8}
mkdir -p "$out" "$work"

py=${PYTHON:-python3}
hf download "$repo" tokenizer.json --revision "${REVISION:-main}" --local-dir "$work/$name"
tok=$work/$name/tokenizer.json
sha=$("$py" -c 'import hashlib, sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' "$tok")
for lang in ja zh; do
    counted=$("$py" -c 'import sys, numpy as np; d = np.load(sys.argv[1]); print(d["tokenizer_sha256"] if "tokenizer_sha256" in d else "")' \
        "$out/$lang-counts.npz" 2>/dev/null || true)
    if [ "$counted" != "$sha" ]; then
        hf download wikimedia/wikipedia --repo-type dataset --include "20231101.$lang/*" --local-dir "$work/wikipedia"
        "$py" "$here/scripts/count_corpus.py" --lang "$lang" --threads "$threads" \
            "$work/wikipedia/20231101.$lang" "$tok" "$out/$lang-counts.npz"
    fi
done
"$py" "$here/scripts/make_zh_words.py" "$tok" "$out/ja-counts.npz" "$out/zh-counts.npz" "$out"
"$py" "$here/scripts/make_bias.py" "$tok" "$out/zh-words.txt" "$out/logit_bias.json"
