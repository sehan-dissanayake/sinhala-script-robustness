"""Shared loaders for the paper's analysis and figures.

Everything here reads only from results/ (the ground truth) and recomputes
aggregates from per-item records. Nothing is hard-coded from a doc.
"""
from __future__ import annotations

import glob
import math
import os
import re

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INTR_DIR = os.path.join(REPO, "results", "intrinsic_evaluation")
EXTR_DIR = os.path.join(REPO, "results", "extrinsic_evaluation")
OUT_DIR = os.path.join(REPO, "paper", "analysis", "out")
FIG_DIR = os.path.join(REPO, "paper", "figures")
LN2 = math.log(2)

# ---------------------------------------------------------------- intrinsic --

# directory name in results/intrinsic_evaluation -> (display name, params in B)
INTRINSIC_MODELS = {
    "OPT-350M": ("OPT-350M", 0.35),
    "Bloom-560m": ("BLOOM-560M", 0.56),
    "Pythia-410M": ("Pythia-410M", 0.41),
    "bloom-1b1": ("BLOOM-1B1", 1.1),
    "TinyLlama-1.1B-Chat-v1.0": ("TinyLlama-1.1B-Chat", 1.1),
    "Llama-3.2-1B": ("Llama-3.2-1B", 1.2),
    "Cerebras-GPT-1.3B": ("Cerebras-GPT-1.3B", 1.3),
    "Opt-1.3b": ("OPT-1.3B", 1.3),
    "LaMini-GPT-1.5B": ("LaMini-GPT-1.5B", 1.5),
    "Qwen1.5-1.8B": ("Qwen1.5-1.8B", 1.8),
    "Opt-2.7B": ("OPT-2.7B", 2.7),
    "Bloom-3B": ("BLOOM-3B", 3.0),
    "Llama-3.2-3B": ("Llama-3.2-3B", 3.2),
    "SmolLM3-3B": ("SmolLM3-3B", 3.1),
    "stablelm-zephyr-3b": ("StableLM-Zephyr-3B", 2.8),
    "Qwen3.5-4B-Base": ("Qwen3.5-4B-Base", 4.0),
    "Qwen3.5-4B": ("Qwen3.5-4B", 4.0),
    "Mistral-7B-v0.3": ("Mistral-7B-v0.3", 7.2),
    "Qwen2-7B": ("Qwen2-7B", 7.6),
    "Qwen/Qwen2-7B-Instruct": ("Qwen2-7B-Instruct", 7.6),
    "gemma-7b": ("Gemma-7B", 8.5),
    "zephyr-7b-beta": ("Zephyr-7B-beta", 7.2),
    "Llama-3.1-8B": ("Llama-3.1-8B", 8.0),
    "meta-llama-Llama-3.1-8B-Instruct": ("Llama-3.1-8B-Instruct", 8.0),
    "Minitron-8B-Base": ("Minitron-8B-Base", 8.4),
    "Hormoz-8B": ("Hormoz-8B", 8.0),
    "Gemma-2-9B": ("Gemma-2-9B", 9.2),
    "Qwen3.5-9B-Base": ("Qwen3.5-9B-Base", 9.0),
    "Qwen3.5-9B": ("Qwen3.5-9B", 9.0),
    "Phi-4-14B": ("Phi-4-14B", 14.7),
    "Mistral-Nemo-Base-2407": ("Mistral-Nemo-Base-2407", 12.2),
}

# stale duplicates that lack the byte/char/word counts
_INTR_SKIP = {"phi-4_diverse_intrinsic.csv", "phi-4_mixed_intrinsic.csv"}


def _pool(path: str, prefix: str) -> dict:
    d = pd.read_csv(path, encoding="utf-8-sig")
    nll = d[f"{prefix}_nll"].sum()
    return {
        "n": len(d),
        "ppl": math.exp(nll / d[f"{prefix}_nscored"].sum()),
        "bpb": nll / (d[f"{prefix}_nbytes"].sum() * LN2),
        "bpc": nll / (d[f"{prefix}_nchars"].sum() * LN2),
        "bpw": nll / (d[f"{prefix}_nwords"].sum() * LN2),
        "tok": d[f"{prefix}_nscored"].sum(),
        "bytes": d[f"{prefix}_nbytes"].sum(),
        "words": d[f"{prefix}_nwords"].sum(),
    }


def load_intrinsic() -> pd.DataFrame:
    """Corpus-pooled intrinsic metrics for all 31 models, recomputed per item."""
    rows = []
    for key, (name, params) in INTRINSIC_MODELS.items():
        d = os.path.join(INTR_DIR, key)
        files = os.listdir(d)
        div = [f for f in files if f.endswith("diverse_intrinsic.csv") and f not in _INTR_SKIP]
        mix = [f for f in files if f.endswith("mixed_intrinsic.csv") and f not in _INTR_SKIP]
        u = _pool(os.path.join(d, div[0]), "unicode")
        r = _pool(os.path.join(d, div[0]), "romanized")
        m = _pool(os.path.join(d, mix[0]), "mixed")
        row = {"model": name, "key": key, "params": params, "n": u["n"]}
        for tag, s in (("u", u), ("r", r), ("m", m)):
            for k in ("ppl", "bpb", "bpc", "bpw", "tok", "bytes", "words"):
                row[f"{tag}_{k}"] = s[k]
        rows.append(row)
    t = pd.DataFrame(rows)
    t["ppl_ratio"] = t.r_ppl / t.u_ppl
    t["m_ppl_ratio"] = t.m_ppl / t.u_ppl
    t["d_bpb"] = t.r_bpb - t.u_bpb
    t["d_bpw"] = t.r_bpw - t.u_bpw
    t["m_d_bpb"] = t.m_bpb - t.u_bpb
    # tokenizer fertility: scored tokens per byte of source text
    t["u_tok_per_byte"] = t.u_tok / t.u_bytes
    t["r_tok_per_byte"] = t.r_tok / t.r_bytes
    t["u_tok_per_word"] = t.u_tok / t.u_words
    t["r_tok_per_word"] = t.r_tok / t.r_words
    return t


def load_intrinsic_items(key: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per-sentence intrinsic records for one model (diverse, mixed)."""
    d = os.path.join(INTR_DIR, key)
    files = os.listdir(d)
    div = [f for f in files if f.endswith("diverse_intrinsic.csv") and f not in _INTR_SKIP][0]
    mix = [f for f in files if f.endswith("mixed_intrinsic.csv") and f not in _INTR_SKIP][0]
    return (
        pd.read_csv(os.path.join(d, div), encoding="utf-8-sig"),
        pd.read_csv(os.path.join(d, mix), encoding="utf-8-sig"),
    )


# ---------------------------------------------------------------- extrinsic --

# display name -> (file prefix, intrinsic dir key, params, instruction-tuned?)
EXTRINSIC_MODELS = {
    "TinyLlama-1.1B-Chat": ("tinyllama_1_1b_chat_v1_0", "TinyLlama-1.1B-Chat-v1.0", 1.1),
    "LaMini-GPT-1.5B": ("lamini_gpt_1_5b", "LaMini-GPT-1.5B", 1.5),
    "StableLM-Zephyr-3B": ("stablelm_zephyr_3b", "stablelm-zephyr-3b", 2.8),
    "SmolLM3-3B": ("smollm3_3b", "SmolLM3-3B", 3.1),
    "Qwen3.5-4B": ("qwen_3_5_4b", "Qwen3.5-4B", 4.0),
    "Zephyr-7B-beta": ("zephyr_7b_beta", "zephyr-7b-beta", 7.2),
    "Qwen2-7B-Instruct": ("qwen2_7b_instruct", "Qwen/Qwen2-7B-Instruct", 7.6),
    "Llama-3.1-8B-Instruct": ("llama_3_1_8b_instruct", "meta-llama-Llama-3.1-8B-Instruct", 8.0),
    "Hormoz-8B": ("hormoz_8b", "Hormoz-8B", 8.0),
    "Qwen3.5-9B": ("qwen_3_5_9b", "Qwen3.5-9B", 9.0),
}

DATASETS = {"sinhala_mmlu": "SinhalaMMLU", "sold": "SOLD", "global_piqa": "Global PIQA"}


def _find(prefix: str, dataset: str) -> str:
    hits = glob.glob(os.path.join(EXTR_DIR, "*", f"{prefix}_{dataset}.csv"))
    if len(hits) != 1:
        raise FileNotFoundError(f"{prefix}_{dataset}.csv -> {hits}")
    return hits[0]


def load_items(model: str, dataset: str) -> pd.DataFrame:
    prefix = EXTRINSIC_MODELS[model][0]
    d = pd.read_csv(_find(prefix, dataset), encoding="utf-8-sig")
    d.columns = [c.lstrip("\ufeff") for c in d.columns]
    d["model"] = model
    d["dataset"] = dataset
    return d


def load_all_items(dataset: str) -> pd.DataFrame:
    return pd.concat([load_items(m, dataset) for m in EXTRINSIC_MODELS], ignore_index=True)


MCQ_VALID = {"sinhala_mmlu", "global_piqa"}


def validity(d: pd.DataFrame, script: str, dataset: str) -> pd.Series:
    """Boolean series: did the model emit a parseable answer?

    The runners write the literal string 'INVALID' when no label could be
    extracted from the generation.
    """
    if dataset in MCQ_VALID:
        v = d[f"{script}_pred_label"].astype(str)
        return ~v.isin(["INVALID", "nan", "None", ""])
    return d[f"{script}_pred"].astype(str).isin(["NOT", "OFF"])


_MMLU_NOPT_CACHE = None


def mmlu_option_counts() -> np.ndarray:
    """Per-item option count for SinhalaMMLU.

    The prompt builder enumerates exactly the options an item has and the
    extractor only accepts those digits, so an item that any model answered
    with '5' has five options; so does an item whose gold label is 'E'.
    """
    global _MMLU_NOPT_CACHE
    if _MMLU_NOPT_CACHE is not None:
        return _MMLU_NOPT_CACHE
    base = load_items(next(iter(EXTRINSIC_MODELS)), "sinhala_mmlu")
    five = (base["gold_label"] == "E").to_numpy().copy()
    for m in EXTRINSIC_MODELS:
        dd = load_items(m, "sinhala_mmlu")
        for s in ("unicode", "romanized"):
            v = pd.to_numeric(dd[f"{s}_pred_digit"], errors="coerce").fillna(0)
            five |= (v.to_numpy() >= 5)
    n = np.where(five, 5, 4)
    _MMLU_NOPT_CACHE = n
    return n


def chance_level(dataset: str) -> float:
    """Random-guessing accuracy in percent, accounting for variable option counts."""
    if dataset in ("sold", "global_piqa"):
        return 50.0
    return float(np.mean(1.0 / mmlu_option_counts()) * 100)


def chance_per_item(dataset: str, n_items: int) -> np.ndarray:
    if dataset == "sinhala_mmlu":
        return 1.0 / mmlu_option_counts()
    return np.full(n_items, 0.5)


def ensure_dirs():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
