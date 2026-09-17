"""The Sinhala-adapted checkpoint, measured against its own parent.

SinLlama is Llama-3-8B with a Sinhala-extended tokenizer and continual
pre-training on 10.7M Sinhala sentences. Both are scored here on the same 500
parallel sentence pairs and 500 mixed-script sentences as the pool of 31, with
the same evaluator, so the difference between the two rows is the Sinhala
adaptation and nothing else.

Neither checkpoint joins the pool of 31. That pool exists to be comparable with
the published benchmark, and a Sinhala-adapted model is not one of the general
open checkpoints it compared. What this script does instead is report the pair
beside the pool, and check that adding SinLlama as a 32nd point would not change
any of the paper's conclusions.

Writes:
    out/sinllama.json
    ../tables/tab_sinllama.tex
    ../tables/tab_tokenizers.tex     (needs out/tokenizer_fertility.json)

Run from the repository root:  python paper/analysis/stats_sinllama.py
"""
from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from scipy import stats

import common as C

TAB = os.path.join(C.REPO, "paper", "tables")

# directory in results/intrinsic_evaluation -> display name
PARENT = ("Meta-Llama-3-8B", "Llama-3-8B")
ADAPTED = ("SAWithanage-SinLlama-Llama-3-8B-Merged", "SinLlama-8B")

# Vocabulary sizes, from each checkpoint's own config/tokenizer.
VOCAB = {"Llama-3-8B": 128256, "SinLlama-8B": 139336}


def _plain(o):
    """numpy scalars out of pandas do not survive json.dump on their own."""
    if hasattr(o, "item"):
        return o.item()
    raise TypeError(f"not serialisable: {type(o).__name__}")


def pooled(key: str, name: str, params: float = 8.0) -> dict:
    """Corpus-pooled metrics for one checkpoint, the same way common.load_intrinsic
    does it, but for a directory that is deliberately not in INTRINSIC_MODELS."""
    d = os.path.join(C.INTR_DIR, key)
    files = os.listdir(d)
    div = [f for f in files if f.endswith("diverse_intrinsic.csv")][0]
    mix = [f for f in files if f.endswith("mixed_intrinsic.csv")][0]
    u = C._pool(os.path.join(d, div), "unicode")
    r = C._pool(os.path.join(d, div), "romanized")
    m = C._pool(os.path.join(d, mix), "mixed")
    row = {"model": name, "key": key, "params": params, "n": u["n"]}
    for tag, s in (("u", u), ("r", r), ("m", m)):
        for k in ("ppl", "bpb", "bpc", "bpw", "tok", "bytes", "words"):
            row[f"{tag}_{k}"] = s[k]
    row["ppl_ratio"] = r["ppl"] / u["ppl"]
    row["m_ppl_ratio"] = m["ppl"] / u["ppl"]
    row["d_bpb"] = r["bpb"] - u["bpb"]
    row["d_bpw"] = r["bpw"] - u["bpw"]
    row["m_d_bpb"] = m["bpb"] - u["bpb"]
    for tag in ("u", "r", "m"):
        row[f"{tag}_tok_per_word"] = row[f"{tag}_tok"] / row[f"{tag}_words"]
        row[f"{tag}_tok_per_byte"] = row[f"{tag}_tok"] / row[f"{tag}_bytes"]
    return row


def decompose(row: dict) -> dict:
    """Equation 3 of the paper, applied to one checkpoint.

    Included because it is the one checkpoint on which the decomposition stops
    being informative, and that is worth recording rather than hiding: when a
    tokenizer spends a very different number of bytes per token in the two
    conditions, the two terms are each far larger than the total they sum to.
    """
    a_u, a_r = row["u_bpb"], row["r_bpb"]
    x_u = row["u_bytes"] / row["u_tok"]
    x_r = row["r_bytes"] / row["r_tok"]
    total = math.log2(row["ppl_ratio"])
    norm = ((a_u + a_r) / 2) * (x_r - x_u)
    loss = ((x_u + x_r) / 2) * (a_r - a_u)
    return {
        "bytes_per_token_unicode": x_u,
        "bytes_per_token_romanized": x_r,
        "total_bits": total,
        "normalizer_bits": norm,
        "per_byte_bits": loss,
        "normalizer_share": norm / total,
        "residual": total - (norm + loss),
    }


def main():
    it = C.load_intrinsic()
    parent = pooled(*PARENT)
    adapted = pooled(*ADAPTED)

    # Does the pool's conclusion survive adding the adapted checkpoint?
    big = pd.concat([it, pd.DataFrame([adapted])], ignore_index=True)
    def rho(df, a, b):
        r = stats.spearmanr(df[a], df[b])
        return {"rho": float(r.statistic), "p": float(r.pvalue), "n": int(len(df))}

    robustness = {}
    for label, a, b in (
        ("ppl_vs_bpb_unicode", "u_ppl", "u_bpb"),
        ("fertility_vs_unicode_ppl", "u_tok_per_word", "u_ppl"),
        ("params_vs_unicode_bpb", "params", "u_bpb"),
        ("unicode_bpb_vs_d_bpw", "u_bpb", "d_bpw"),
    ):
        robustness[label] = {"pool_of_31": rho(it, a, b), "with_sinllama": rho(big, a, b)}

    # Rank of the adapted checkpoint among 32, lower value ranked first.
    ranks = {}
    for col in ("u_ppl", "u_bpb", "r_bpb", "ppl_ratio", "d_bpb", "d_bpw", "u_tok_per_word"):
        ranks[col] = int(big[col].rank()[big.model == "SinLlama-8B"].iloc[0])

    gains = {}
    for cond, tag in (("unicode", "u"), ("romanized", "r"), ("mixed", "m")):
        gains[cond] = {
            "bpb_parent": parent[f"{tag}_bpb"],
            "bpb_adapted": adapted[f"{tag}_bpb"],
            "bpb_delta": adapted[f"{tag}_bpb"] - parent[f"{tag}_bpb"],
            "bpb_pct_reduction": 100 * (1 - adapted[f"{tag}_bpb"] / parent[f"{tag}_bpb"]),
            "bpw_parent": parent[f"{tag}_bpw"],
            "bpw_adapted": adapted[f"{tag}_bpw"],
            "ppl_parent": parent[f"{tag}_ppl"],
            "ppl_adapted": adapted[f"{tag}_ppl"],
            "ppl_factor": adapted[f"{tag}_ppl"] / parent[f"{tag}_ppl"],
            "fertility_parent": parent[f"{tag}_tok_per_word"],
            "fertility_adapted": adapted[f"{tag}_tok_per_word"],
        }

    out = {
        "n_sentences": parent["n"],
        "parent": {k: v for k, v in parent.items() if k != "key"},
        "adapted": {k: v for k, v in adapted.items() if k != "key"},
        "parent_weights_note": (
            "meta-llama/Meta-Llama-3-8B is gated; the run used "
            "NousResearch/Meta-Llama-3-8B, whose four safetensors shards carry "
            "the same sizes and SHA-256 digests as the official repository."
        ),
        "vocab": VOCAB,
        "gains": gains,
        "adaptation_asymmetry": (
            gains["unicode"]["bpb_delta"] / gains["romanized"]["bpb_delta"]
        ),
        "fertility_factor_unicode": (
            parent["u_tok_per_word"] / adapted["u_tok_per_word"]
        ),
        "ppl_ratio": {
            "parent": parent["ppl_ratio"],
            "adapted": adapted["ppl_ratio"],
            "factor": parent["ppl_ratio"] / adapted["ppl_ratio"],
        },
        "d_bpb": {"parent": parent["d_bpb"], "adapted": adapted["d_bpb"],
                  "change": adapted["d_bpb"] - parent["d_bpb"]},
        "d_bpw": {"parent": parent["d_bpw"], "adapted": adapted["d_bpw"]},
        "decomposition_adapted": decompose(adapted),
        "decomposition_parent": decompose(parent),
        "ranks_among_32": ranks,
        "pool_of_31": {
            "u_bpb_min": float(it.u_bpb.min()), "u_bpb_median": float(it.u_bpb.median()),
            "u_ppl_max": float(it.u_ppl.max()), "u_ppl_median": float(it.u_ppl.median()),
            "r_bpb_min": float(it.r_bpb.min()), "r_bpb_median": float(it.r_bpb.median()),
            "u_bpw_min": float(it.u_bpw.min()), "u_bpw_median": float(it.u_bpw.median()),
            "r_bpw_median": float(it.r_bpw.median()),
            "ppl_ratio_min": float(it.ppl_ratio.min()),
            "ppl_ratio_median": float(it.ppl_ratio.median()),
            "d_bpb_median": float(it.d_bpb.median()),
            "d_bpb_max": float(it.d_bpb.max()),
            "d_bpw_median": float(it.d_bpw.median()),
            "d_bpw_max": float(it.d_bpw.max()),
            "fertility_min": float(it.u_tok_per_word.min()),
            "fertility_median": float(it.u_tok_per_word.median()),
            "fertility_max": float(it.u_tok_per_word.max()),
        },
        "conclusion_robustness": robustness,
    }

    C.ensure_dirs()
    path = os.path.join(C.OUT_DIR, "sinllama.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=_plain)
    print("wrote", path)

    write_tables(it, parent, adapted)
    report(out)


def nb(name):
    return name.replace("-", "\\nobreakdash-")


def w(name, body):
    p = os.path.join(TAB, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write("% Generated by paper/analysis/stats_sinllama.py. Do not edit by hand.\n")
        f.write(body if body.endswith("\n") else body + "\n")
    print("wrote", p)


def write_tables(it, parent, adapted):
    def row(label, d, mark=""):
        return (f"{label}{mark} & {d['u_tok_per_word']:.2f} & {d['u_ppl']:.2f} "
                f"& {d['u_bpb']:.3f} & {d['u_bpw']:.2f} "
                f"& {d['r_bpb']:.3f} & {d['r_bpw']:.2f} "
                f"& {d['ppl_ratio']:.1f} & {d['d_bpb']:.3f} \\\\")

    best = it.loc[it.u_bpb.idxmin()].to_dict()
    med = {c: float(it[c].median()) for c in
           ("u_tok_per_word", "u_ppl", "u_bpb", "u_bpw", "r_bpb", "r_bpw",
            "ppl_ratio", "d_bpb")}

    body = "\n".join([
        row(nb("Llama-3-8B"), parent),
        row(nb("SinLlama-8B"), adapted),
        r"\addlinespace[2pt]",
        row(nb(best["model"]), best, r"$^{\dagger}$"),
        row(r"median of the 31", med),
    ])
    w("tab_sinllama.tex", body)

    # Tokenizer fertility. Written here so the paper has one generator per table,
    # but the measurements come from tokenizer_fertility.py, which needs network
    # access and is therefore kept separate.
    fp = os.path.join(C.OUT_DIR, "tokenizer_fertility.json")
    if not os.path.exists(fp):
        print(f"skipping tab_tokenizers.tex: run tokenizer_fertility.py first")
        return
    tf = json.load(open(fp))
    t, pool = tf["tokenizers"], tf["pool_of_31"]
    order = [
        ("HelaBERT", "HelaBERT"),
        ("SinLlama (Extended-Sinhala-LLaMA)", "SinLlama"),
        ("SinBERT-large", "SinBERT-large"),
    ]
    rows = []
    for key, label in order:
        r = t[key]
        rows.append(f"{nb(label)} & {r['vocab']:,} & {r['unicode']:.2f} "
                    f"& {r['romanized']:.2f} \\\\")
    rows.append(r"\addlinespace[2pt]")
    # Ranges rather than a "best" row: the tokenizer that is most efficient on
    # the Sinhala script is not the one most efficient on Romanized text, so a
    # single best-of row would silently mix two models across the two columns.
    rows.append(f"the 31 general tokenizers & --- & "
                f"{pool['unicode_min']:.2f}--{pool['unicode_max']:.2f} & "
                f"{pool['romanized_min']:.2f}--{pool['romanized_max']:.2f} \\\\")
    rows.append(f"\\quad median & --- & {pool['unicode_median']:.2f} "
                f"& {pool['romanized_median']:.2f} \\\\")
    w("tab_tokenizers.tex", "\n".join(rows))


def report(o):
    g, p = o["gains"], o["pool_of_31"]
    print("\n--- the adaptation, on identical text ---")
    for cond in ("unicode", "romanized", "mixed"):
        v = g[cond]
        print(f"  {cond:10s} bpb {v['bpb_parent']:.4f} -> {v['bpb_adapted']:.4f}  "
              f"({v['bpb_pct_reduction']:+.1f}%)   ppl {v['ppl_parent']:.2f} -> "
              f"{v['ppl_adapted']:.2f} ({v['ppl_factor']:.1f}x)")
    print(f"  Sinhala gain is {o['adaptation_asymmetry']:.2f}x the Romanized gain")
    print(f"  fertility {g['unicode']['fertility_parent']:.2f} -> "
          f"{g['unicode']['fertility_adapted']:.2f} "
          f"({o['fertility_factor_unicode']:.2f}x fewer tokens per word)")
    print(f"\n  reported ratio {o['ppl_ratio']['parent']:.1f}x -> "
          f"{o['ppl_ratio']['adapted']:.1f}x  "
          f"(a {o['ppl_ratio']['factor']:.1f}x apparent improvement)")
    print(f"  real per-byte gap {o['d_bpb']['parent']:.4f} -> "
          f"{o['d_bpb']['adapted']:.4f} bits ({o['d_bpb']['change']:+.4f}), "
          f"against a pool median of {p['d_bpb_median']:.4f}")
    d = o["decomposition_adapted"]
    print(f"\n  decomposition of the adapted ratio: total {d['total_bits']:.2f} bits "
          f"= normalizer {d['normalizer_bits']:.2f} + per-byte "
          f"{d['per_byte_bits']:.2f}  (residual {d['residual']:.2e})")
    print(f"  bytes per token {d['bytes_per_token_unicode']:.2f} Sinhala vs "
          f"{d['bytes_per_token_romanized']:.2f} Romanized")
    print("\n--- rank among 32, 1 = lowest value ---")
    print("  " + "  ".join(f"{k}={v}" for k, v in o["ranks_among_32"].items()))
    print("\n--- would adding it change a conclusion? ---")
    for k, v in o["conclusion_robustness"].items():
        a, b = v["pool_of_31"], v["with_sinllama"]
        print(f"  {k:28s} {a['rho']:+.3f} (n=31)  ->  {b['rho']:+.3f} (n=32)")


if __name__ == "__main__":
    main()
