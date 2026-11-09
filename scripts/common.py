"""Shared pieces: which characters Japanese text uses, and the text each token stands for."""
import hashlib
import json
import pathlib

# The four characters of the 2010 jōyō kanji list that JIS X 0208 lacks. Japanese text uses them, so they stay allowed.
JOYO_OUTSIDE_0208 = set("𠮟塡剝頰")


def is_han(c):
    """A CJK ideograph of the Basic Multilingual Plane: the unified block, extension A, or the compatibility block.

    The planes above it hold rare characters that models seldom write, so the character rule leaves them alone.
    """
    o = ord(c)
    return 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF or 0xF900 <= o <= 0xFAFF


def jis_ok(c):
    """In JIS X 0208 (Shift_JIS encodes exactly its kanji), or one of the four jōyō kanji outside it."""
    if c in JOYO_OUTSIDE_0208:
        return True
    try:
        c.encode("shift_jis")
        return True
    except UnicodeEncodeError:
        return False


def token_texts(tokenizer_json):
    """Maps each token id to the text it stands for, or None when the token holds only part of a character.

    Decoding token by token through the tokenizer's own decoder works for byte-level BPE (Qwen, DeepSeek) and for
    SentencePiece-style vocabularies alike. A partial UTF-8 sequence decodes to U+FFFD.
    """
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(str(tokenizer_json))
    out = {}
    for i in range(tok.get_vocab_size(with_added_tokens=True)):
        s = tok.decode([i], skip_special_tokens=False)
        out[i] = None if "�" in s else s
    return out


def kanji_word(text):
    """A token text the word rule judges: one or more kanji, all of them allowed by the character rule."""
    return len(text) >= 1 and all(is_han(c) and jis_ok(c) for c in text)


def file_sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def load_counts(path, tokenizer_json):
    """Token counts from count_corpus.py, refused unless they were made with this very tokenizer file.

    Counts made with another tokenizer would attach each frequency to the wrong token id, and the word list built on
    them would look normal while banning the wrong words.
    """
    import numpy as np
    d = np.load(path)
    want = file_sha256(tokenizer_json)
    got = str(d["tokenizer_sha256"]) if "tokenizer_sha256" in d else "(none recorded)"
    if got != want:
        raise SystemExit(f"{path} was counted with tokenizer sha256 {got}, but {tokenizer_json} is {want}: "
                         "count again with this tokenizer")
    return d["counts"], 1e8 / int(d["tokens"])


def read_words(path):
    """One word a line; '#' starts a comment."""
    p = pathlib.Path(path)
    return [w for w in (ln.split("#")[0].strip() for ln in p.read_text(encoding="utf-8").splitlines()) if w]


def write_json(path, obj):
    pathlib.Path(path).write_text(json.dumps(obj, ensure_ascii=False) + "\n", encoding="utf-8")
