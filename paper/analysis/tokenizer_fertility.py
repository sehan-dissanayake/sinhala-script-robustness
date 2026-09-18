"""Tokenizer fertility for the Sinhala-specific tokenizers named in review.

Motivation
----------
The paper argues that perplexity on Sinhala is largely a report on the
tokenizer. Four recent papers build or study Sinhala tokenizers, and the
obvious question is what they do to fertility in *both* script conditions.
Fertility needs only a tokenizer, no forward pass, so it can be measured for
encoder models too, whose per-token likelihoods are not comparable with the
causal checkpoints of the main pool.

Rule applied to every tokenizer, so the column is comparable: subword pieces
produced for the raw sentence with no special tokens, divided by the number of
whitespace words. Whitespace pieces count as pieces, because the model consumes
them.

Outputs paper/analysis/out/tokenizer_fertility.json. Needs network access the
first time; the tokenizers are a few MB each.

Run from the repository root:  python paper/analysis/tokenizer_fertility.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

CORPUS = os.path.join(
    C.REPO, "data", "raw", "intrinsic_evaluation_datasets", "diverse_sentences.csv"
)
CACHE = os.path.join(C.REPO, "data", "reference", "tokenizers")

# display name -> huggingface id. Only the Sinhala-specific tokenizers are
# downloaded; the general-purpose references come from the recorded runs of the
# 31 checkpoints, which is what the rest of the paper quotes.
HF_TOKENIZERS = {
    # SinLlama's extended Llama-3 vocabulary (aravinda2025sinllama).
    "SinLlama (Extended-Sinhala-LLaMA)": "polyglots/Extended-Sinhala-LLaMA",
    # SinBERT, the encoder the Sinhala Global PIQA paper evaluates with.
    "SinBERT-large": "NLPC-UOM/SinBERT-large",
}

# HelaBERT ships a bare SentencePiece model rather than a transformers tokenizer.
HELABERT_SPM = (
    "https://huggingface.co/ThisenEkanayake/HelaBERT/resolve/main/"
    "tokenizer/unigram_32000_0.9995.model"
)


def corpus():
    d = pd.read_csv(CORPUS).dropna()
    return d["sinhala_unicode"].tolist(), d["sinhala_romanized"].tolist()


def fertility(encode, texts):
    n_tok = sum(len(encode(t)) for t in texts)
    n_word = sum(len(t.split()) for t in texts)
    return n_tok / n_word


def helabert():
    import sentencepiece as spm

    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, "helabert_unigram_32000.model")
    if not os.path.exists(path):
        urllib.request.urlretrieve(HELABERT_SPM, path)
    sp = spm.SentencePieceProcessor(model_file=path)
    return sp.get_piece_size(), (lambda t: sp.encode(t))


def main():
    from transformers import AutoTokenizer

    uni, rom = corpus()
    rows = {}

    size, enc = helabert()
    rows["HelaBERT"] = {
        "vocab": size,
        "unicode": fertility(enc, uni),
        "romanized": fertility(enc, rom),
    }

    for name, hf_id in HF_TOKENIZERS.items():
        tk = AutoTokenizer.from_pretrained(hf_id)
        enc = lambda t: tk(t, add_special_tokens=False)["input_ids"]  # noqa: E731
        rows[name] = {
            "vocab": len(tk),
            "unicode": fertility(enc, uni),
            "romanized": fertility(enc, rom),
        }

    # The pool of 31, for context. Computed from the recorded runs, where the
    # token count is scored tokens (sequence length minus one), so it differs
    # from the counts above in the third decimal.
    it = C.load_intrinsic()
    pool = {
        "n": int(len(it)),
        "unicode_min": float(it.u_tok_per_word.min()),
        "unicode_median": float(it.u_tok_per_word.median()),
        "unicode_max": float(it.u_tok_per_word.max()),
        "romanized_min": float(it.r_tok_per_word.min()),
        "romanized_median": float(it.r_tok_per_word.median()),
        "romanized_max": float(it.r_tok_per_word.max()),
    }

    out = {"n_sentences": len(uni), "tokenizers": rows, "pool_of_31": pool}
    C.ensure_dirs()
    path = os.path.join(C.OUT_DIR, "tokenizer_fertility.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(f"{'tokenizer':36s} {'vocab':>8s} {'Sinhala':>9s} {'Romanized':>10s}")
    for name, r in rows.items():
        print(f"{name:36s} {r['vocab']:8d} {r['unicode']:9.3f} {r['romanized']:10.3f}")
    print(f"\npool of {pool['n']}: Sinhala {pool['unicode_min']:.2f}-"
          f"{pool['unicode_max']:.2f} (median {pool['unicode_median']:.2f}), "
          f"Romanized {pool['romanized_min']:.2f}-{pool['romanized_max']:.2f} "
          f"(median {pool['romanized_median']:.2f})")
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
