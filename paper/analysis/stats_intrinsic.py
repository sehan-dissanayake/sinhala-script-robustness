"""Intrinsic analysis: tokenizer-independent metrics, rank disagreement, n-gram reference."""
from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
from scipy import stats

import common as C

RNG = np.random.default_rng(20260831)

# Published Table II of the benchmark we extend (Unicode, Romanized, Mixed perplexity),
# used only as a reproduction check against our own runs.
PUBLISHED_PPL = {
    "Pythia-410M": (2.58, 1245.00, 4.92), "Mistral-Nemo-Base-2407": (2.82, 1978.10, 6.72),
    "Cerebras-GPT-1.3B": (2.86, 1040.17, 5.25), "Minitron-8B-Base": (2.98, 2136.14, 5.10),
    "Llama-3.1-8B": (3.22, 970.64, 6.38), "OPT-2.7B": (3.59, 1052.79, 6.29),
    "Llama-3.2-3B": (3.74, 1560.66, 7.42), "OPT-1.3B": (3.87, 1121.87, 6.85),
    "Phi-4-14B": (4.01, 1163.23, 12.07), "Llama-3.2-1B": (4.11, 1718.67, 8.57),
    "TinyLlama-1.1B-Chat": (4.38, 1014.17, 8.95), "StableLM-Zephyr-3B": (4.57, 2129.20, 7.54),
    "OPT-350M": (4.76, 1075.87, 8.19), "Mistral-7B-v0.3": (5.26, 921.40, 10.19),
    "LaMini-GPT-1.5B": (5.41, 1322.01, 9.49), "Hormoz-8B": (5.98, 4175.56, 13.64),
    "Qwen2-7B": (6.29, 1356.97, 14.17), "BLOOM-3B": (6.95, 3258.46, 15.97),
    "SmolLM3-3B": (6.98, 5372.60, 13.95), "Qwen1.5-1.8B": (8.07, 1584.79, 17.67),
    "Zephyr-7B-beta": (8.29, 1515.70, 15.82), "BLOOM-1B1": (11.01, 3558.50, 24.63),
    "BLOOM-560M": (12.64, 4915.05, 28.12), "Gemma-7B": (21.14, 3152.45, 66.52),
}


def _sp(a, b):
    r = stats.spearmanr(a, b)
    return {"rho": float(r.statistic), "p": float(r.pvalue), "n": int(len(a))}


def ngram_bpc(texts, order, folds=5, alpha=0.1, seed=0):
    """Held-out bits per character of an add-alpha character n-gram model.

    Folds are disjoint: the model for each fold sees only the other folds, so the
    number reported is genuinely out-of-sample. Returned in bits/char and bits/byte.
    """
    texts = list(texts)
    n = len(texts)
    idx = np.random.default_rng(seed).permutation(n)
    bits = 0.0
    nchar = 0
    for f in range(folds):
        te = set(idx[f::folds].tolist())
        train = [texts[i] for i in range(n) if i not in te]
        test = [texts[i] for i in range(n) if i in te]
        cnt: dict = defaultdict(lambda: defaultdict(int))
        vocab = set()
        for t in train:
            s = "\x02" * order + t + "\x03"
            vocab.update(s)
            for i in range(order, len(s)):
                cnt[s[i - order:i]][s[i]] += 1
        V = max(len(vocab), 1)
        for t in test:
            s = "\x02" * order + t + "\x03"
            for i in range(order, len(s)):
                c = cnt[s[i - order:i]]
                tot = sum(c.values())
                p = (c.get(s[i], 0) + alpha) / (tot + alpha * V)
                bits += -math.log2(p)
                nchar += 1
    bpc = bits / nchar
    total_c = sum(len(t) + 1 for t in texts)
    total_b = sum(len(t.encode("utf-8")) + 1 for t in texts)
    return bpc, bpc * total_c / total_b


def main():
    C.ensure_dirs()
    out = {}
    it = C.load_intrinsic()
    it.to_csv(os.path.join(C.OUT_DIR, "intrinsic_pooled.csv"), index=False)

    out["n_checkpoints"] = int(len(it))
    out["n_sentences_parallel"] = int(it.n.iloc[0])

    # ---- reproduction of the published perplexities -------------------------
    rep = []
    for _, r in it.iterrows():
        if r.model in PUBLISHED_PPL:
            pu, pr, pm = PUBLISHED_PPL[r.model]
            rep.append(dict(model=r.model, du=100 * (r.u_ppl - pu) / pu,
                            dr=100 * (r.r_ppl - pr) / pr, dm=100 * (r.m_ppl - pm) / pm))
    rep = pd.DataFrame(rep)
    out["reproduction"] = {
        "n_shared": int(len(rep)),
        "max_abs_pct_unicode": float(rep.du.abs().max()),
        "max_abs_pct_romanized": float(rep.dr.abs().max()),
        "median_abs_pct_unicode": float(rep.du.abs().median()),
        "median_abs_pct_romanized": float(rep.dr.abs().median()),
        "mixed_outliers": rep.loc[rep.dm.abs() > 5, "model"].tolist(),
        "median_abs_pct_mixed_excl_outliers": float(rep.loc[rep.dm.abs() <= 5, "dm"].abs().median()),
    }

    # ---- descriptive ranges ------------------------------------------------
    for cond, tag in (("unicode", "u"), ("romanized", "r"), ("mixed", "m")):
        out[f"{cond}_bpb"] = dict(min=float(it[f"{tag}_bpb"].min()), max=float(it[f"{tag}_bpb"].max()),
                                  median=float(it[f"{tag}_bpb"].median()),
                                  mean=float(it[f"{tag}_bpb"].mean()), sd=float(it[f"{tag}_bpb"].std(ddof=1)),
                                  cv_pct=float(it[f"{tag}_bpb"].std(ddof=1) / it[f"{tag}_bpb"].mean() * 100),
                                  argmin=it.loc[it[f"{tag}_bpb"].idxmin(), "model"],
                                  argmax=it.loc[it[f"{tag}_bpb"].idxmax(), "model"])
        out[f"{cond}_ppl"] = dict(min=float(it[f"{tag}_ppl"].min()), max=float(it[f"{tag}_ppl"].max()),
                                  median=float(it[f"{tag}_ppl"].median()),
                                  cv_pct=float(it[f"{tag}_ppl"].std(ddof=1) / it[f"{tag}_ppl"].mean() * 100),
                                  argmin=it.loc[it[f"{tag}_ppl"].idxmin(), "model"],
                                  argmax=it.loc[it[f"{tag}_ppl"].idxmax(), "model"])

    # dispersion: is the between-model spread of BPB smaller under Romanization?
    # bootstrap over checkpoints on the log ratio of standard deviations
    boot = []
    n = len(it)
    for _ in range(20000):
        i = RNG.integers(0, n, n)
        a = it.u_bpb.to_numpy()[i]
        b = it.r_bpb.to_numpy()[i]
        if a.std() > 0 and b.std() > 0:
            boot.append(math.log(b.std(ddof=1) / a.std(ddof=1)))
    boot = np.array(boot)
    out["sd_ratio_rom_over_uni"] = dict(
        point=float(it.r_bpb.std(ddof=1) / it.u_bpb.std(ddof=1)),
        ci=[float(np.exp(np.percentile(boot, 2.5))), float(np.exp(np.percentile(boot, 97.5)))],
        p_two_sided=float(2 * min((boot >= 0).mean(), (boot <= 0).mean())))

    # ---- degradation magnitude ---------------------------------------------
    out["ppl_ratio"] = dict(median=float(it.ppl_ratio.median()), min=float(it.ppl_ratio.min()),
                            max=float(it.ppl_ratio.max()),
                            argmin=it.loc[it.ppl_ratio.idxmin(), "model"],
                            argmax=it.loc[it.ppl_ratio.idxmax(), "model"])
    out["d_bpb"] = dict(median=float(it.d_bpb.median()), min=float(it.d_bpb.min()), max=float(it.d_bpb.max()),
                        argmin=it.loc[it.d_bpb.idxmin(), "model"], argmax=it.loc[it.d_bpb.idxmax(), "model"],
                        median_prob_factor=float(2 ** it.d_bpb.median()))
    out["d_bpw"] = dict(median=float(it.d_bpw.median()), min=float(it.d_bpw.min()), max=float(it.d_bpw.max()),
                        median_ratio=float((it.r_bpw / it.u_bpw).median()))
    out["m_ppl_ratio_median"] = float(it.m_ppl_ratio.median())
    out["m_d_bpb_median"] = float(it.m_d_bpb.median())

    # ---- rank (dis)agreement ------------------------------------------------
    out["rank"] = {
        "ppl_vs_bpb_unicode": _sp(it.u_ppl, it.u_bpb),
        "ppl_vs_bpb_romanized": _sp(it.r_ppl, it.r_bpb),
        "ppl_vs_bpb_mixed": _sp(it.m_ppl, it.m_bpb),
        "unicode_vs_romanized_ppl": _sp(it.u_ppl, it.r_ppl),
        "unicode_vs_romanized_bpb": _sp(it.u_bpb, it.r_bpb),
        "unicode_vs_mixed_ppl": _sp(it.u_ppl, it.m_ppl),
        "unicode_vs_mixed_bpb": _sp(it.u_bpb, it.m_bpb),
        "params_vs_unicode_ppl": _sp(it.params, it.u_ppl),
        "params_vs_unicode_bpb": _sp(it.params, it.u_bpb),
        "params_vs_romanized_ppl": _sp(it.params, it.r_ppl),
        "params_vs_romanized_bpb": _sp(it.params, it.r_bpb),
        "params_vs_mixed_bpb": _sp(it.params, it.m_bpb),
        "params_vs_d_bpb": _sp(it.params, it.d_bpb),
        "unicode_bpb_vs_d_bpb": _sp(it.u_bpb, it.d_bpb),
        "fertility_vs_unicode_ppl": _sp(it.u_tok_per_byte, it.u_ppl),
        "fertility_vs_romanized_ppl": _sp(it.r_tok_per_byte, it.r_ppl),
    }
    # top-5 overlap between metric rankings
    top_ppl = set(it.nsmallest(5, "u_ppl").model)
    top_bpb = set(it.nsmallest(5, "u_bpb").model)
    out["top5_overlap_unicode_ppl_vs_bpb"] = len(top_ppl & top_bpb)
    out["top5_unicode_ppl"] = it.nsmallest(5, "u_ppl").model.tolist()
    out["top5_unicode_bpb"] = it.nsmallest(5, "u_bpb").model.tolist()
    out["top5_romanized_bpb"] = it.nsmallest(5, "r_bpb").model.tolist()
    # largest single rank displacement between PPL and BPB
    rk = it.assign(rp=it.u_ppl.rank(), rb=it.u_bpb.rank())
    rk["rank_shift"] = rk.rp - rk.rb
    rk = rk.reindex(rk["rank_shift"].abs().sort_values(ascending=False).index)
    out["largest_rank_shifts"] = rk[["model", "u_ppl", "u_bpb", "rp", "rb", "rank_shift"]].head(6).round(4).to_dict("records")

    # ---- tokenizer fertility ------------------------------------------------
    out["fertility"] = {
        "unicode_tok_per_byte": dict(min=float(it.u_tok_per_byte.min()), max=float(it.u_tok_per_byte.max()),
                                     median=float(it.u_tok_per_byte.median())),
        "romanized_tok_per_byte": dict(min=float(it.r_tok_per_byte.min()), max=float(it.r_tok_per_byte.max()),
                                       median=float(it.r_tok_per_byte.median())),
        "unicode_tok_per_word": dict(min=float(it.u_tok_per_word.min()), max=float(it.u_tok_per_word.max()),
                                     median=float(it.u_tok_per_word.median())),
        "romanized_tok_per_word": dict(min=float(it.r_tok_per_word.min()), max=float(it.r_tok_per_word.max()),
                                       median=float(it.r_tok_per_word.median())),
        "median_token_ratio_rom_over_uni": float((it.r_tok / it.u_tok).median()),
        "n_with_fewer_romanized_tokens": int((it.r_tok < it.u_tok).sum()),
    }

    # ---- flattening: how much Unicode quality carries over? -----------------
    # Word counts are identical for both members of a pair, so BPW is the cleanest
    # cross-script quantity; bytes inflate 2.65x under Sinhala UTF-8.
    for x, y, name in ((it.u_bpb, it.r_bpb, "bpb"), (it.u_bpw, it.r_bpw, "bpw")):
        lr = stats.linregress(x, y)
        sl = []
        for _ in range(20000):
            i = RNG.integers(0, len(it), len(it))
            sl.append(stats.linregress(x.to_numpy()[i], y.to_numpy()[i]).slope)
        out[f"carryover_{name}"] = dict(
            slope=float(lr.slope), intercept=float(lr.intercept), r2=float(lr.rvalue ** 2),
            p=float(lr.pvalue), slope_ci=[float(np.percentile(sl, 2.5)), float(np.percentile(sl, 97.5))])
    out["bpw_n_models_better_romanized"] = int((it.r_bpw < it.u_bpw).sum())
    out["bpw_models_better_romanized"] = it.loc[it.r_bpw < it.u_bpw, "model"].tolist()
    out["bpw_unicode_range"] = [float(it.u_bpw.min()), float(it.u_bpw.max())]
    out["bpw_romanized_range"] = [float(it.r_bpw.min()), float(it.r_bpw.max())]
    out["rank"]["unicode_bpw_vs_d_bpw"] = _sp(it.u_bpw, it.d_bpw)

    # ---- per-sentence paired test on BPW ------------------------------------
    wil = []
    for key in C.INTRINSIC_MODELS:
        div, _ = C.load_intrinsic_items(key)
        w = stats.wilcoxon(div.romanized_bpw, div.unicode_bpw)
        wil.append(dict(model=C.INTRINSIC_MODELS[key][0], p=float(w.pvalue),
                        frac_worse=float((div.romanized_bpw > div.unicode_bpw).mean()),
                        median_delta=float((div.romanized_bpw - div.unicode_bpw).median())))
    wil = pd.DataFrame(wil)
    out["per_sentence_bpw"] = dict(
        n_models_significant_p05=int((wil.p < 0.05).sum()),
        n_models_romanized_worse=int((wil.median_delta > 0).sum()),
        n_models_romanized_better=int((wil.median_delta < 0).sum()),
        median_frac_worse=float(wil.frac_worse.median()))
    wil.to_csv(os.path.join(C.OUT_DIR, "intrinsic_wilcoxon.csv"), index=False)

    # ---- character n-gram reference ----------------------------------------
    d = pd.read_csv(os.path.join(C.REPO, "data", "raw", "intrinsic_evaluation_datasets",
                                 "diverse_sentences.csv"), encoding="utf-8-sig").dropna()
    ng = {}
    for col, tag in (("sinhala_unicode", "unicode"), ("sinhala_romanized", "romanized")):
        ng[tag] = {}
        for order in range(6):
            bpc, bpb = ngram_bpc(d[col].astype(str), order)
            ng[tag][f"order{order}"] = dict(bpc=round(bpc, 4), bpb=round(bpb, 4))
    out["ngram_reference"] = ng
    best_r = min(v["bpb"] for v in ng["romanized"].values())
    best_u = min(v["bpb"] for v in ng["unicode"].values())
    out["ngram_vs_llm"] = {
        "best_ngram_bpb_romanized": best_r,
        "best_ngram_order_romanized": min(ng["romanized"], key=lambda k: ng["romanized"][k]["bpb"]),
        "n_llms_beating_best_ngram_romanized": int((it.r_bpb < best_r).sum()),
        "n_llms_beating_bigram_romanized": int((it.r_bpb < ng["romanized"]["order1"]["bpb"]).sum()),
        "n_llms_beating_unigram_romanized": int((it.r_bpb < ng["romanized"]["order0"]["bpb"]).sum()),
        "best_ngram_bpb_unicode": best_u,
        "best_ngram_order_unicode": min(ng["unicode"], key=lambda k: ng["unicode"][k]["bpb"]),
        "n_llms_beating_best_ngram_unicode": int((it.u_bpb < best_u).sum()),
        "llms_beating_best_ngram_unicode": it.loc[it.u_bpb < best_u, "model"].tolist(),
    }
    # corpus statistics for the parallel set
    out["parallel_corpus"] = {
        "n": int(len(d)),
        "unicode_chars": int(d.sinhala_unicode.str.len().sum()),
        "unicode_bytes": int(sum(len(t.encode()) for t in d.sinhala_unicode)),
        "romanized_chars": int(d.sinhala_romanized.str.len().sum()),
        "romanized_bytes": int(sum(len(t.encode()) for t in d.sinhala_romanized)),
        "unicode_bytes_per_char": float(sum(len(t.encode()) for t in d.sinhala_unicode)
                                        / d.sinhala_unicode.str.len().sum()),
        "mean_words": float(d.sinhala_unicode.str.split().str.len().mean()),
    }

    with open(os.path.join(C.OUT_DIR, "intrinsic_numbers.json"), "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
