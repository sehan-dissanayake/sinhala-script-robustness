"""Robustness analyses added for the ACL revision.

Five blocks, all recomputed from results/ through common.py:

  1. shared24     Reproduction of the published benchmark on exactly the 24
                  checkpoints it evaluated, so ratio and correlation claims are
                  compared against the same pool rather than our larger one.
  2. decomposition Exact arithmetic split of the log perplexity ratio into the
                  part caused by token-count normalisation and the part caused
                  by a genuine rise in per-byte loss.
  3. flattening   Leave-one-out and bootstrap refits of the model-level and
                  cell-level flattening regressions, plus a permutation null
                  that shows why the headroom form of the regression must not
                  be read as independent evidence.
  4. linkage_ci   Bootstrap confidence intervals and leave-one-out ranges for
                  every Spearman correlation in the intrinsic-to-downstream
                  table.
  5. pilot        The prompt-template pilot, tabulated for disclosure.

Run from the repository root:  python paper/analysis/stats_robustness.py
"""
from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
from scipy import stats

import common as CM

RNG = np.random.default_rng(20260902)
B = 10000
LN2 = math.log(2)

# Perplexities as published in Table II of the benchmark we extend, keyed by our
# display names. Transcribed from the paper's own table, used only to quantify
# how closely our recomputation reproduces it.
PUBLISHED = {
    "Pythia-410M": (2.58, 1245.00, 4.92),
    "Mistral-Nemo-Base-2407": (2.82, 1978.10, 6.72),
    "Cerebras-GPT-1.3B": (2.86, 1040.17, 5.25),
    "Minitron-8B-Base": (2.98, 2136.14, 5.10),
    "Llama-3.1-8B": (3.22, 970.64, 6.38),
    "OPT-2.7B": (3.59, 1052.79, 6.29),
    "Llama-3.2-3B": (3.74, 1560.66, 7.42),
    "OPT-1.3B": (3.87, 1121.87, 6.85),
    "Phi-4-14B": (4.01, 1163.23, 12.07),
    "Llama-3.2-1B": (4.11, 1718.67, 8.57),
    "TinyLlama-1.1B-Chat": (4.38, 1014.17, 8.95),
    "StableLM-Zephyr-3B": (4.57, 2129.20, 7.54),
    "OPT-350M": (4.76, 1075.87, 8.19),
    "Mistral-7B-v0.3": (5.26, 921.40, 10.19),
    "LaMini-GPT-1.5B": (5.41, 1322.01, 9.49),
    "Hormoz-8B": (5.98, 4175.56, 13.64),
    "Qwen2-7B": (6.29, 1356.97, 14.17),
    "BLOOM-3B": (6.95, 3258.46, 15.97),
    "SmolLM3-3B": (6.98, 5372.60, 13.95),
    "Qwen1.5-1.8B": (8.07, 1584.79, 17.67),
    "Zephyr-7B-beta": (8.29, 1515.70, 15.82),
    "BLOOM-1B1": (11.01, 3558.50, 24.63),
    "BLOOM-560M": (12.64, 4915.05, 28.12),
    "Gemma-7B": (21.14, 3152.45, 66.52),
}


def _sp(x, y):
    s = stats.spearmanr(x, y)
    return float(s.statistic), float(s.pvalue)


def _cv(v):
    v = np.asarray(v, float)
    return float(v.std(ddof=1) / v.mean() * 100)


# ------------------------------------------------------ 1. shared-24 pool ----
def shared24(it: pd.DataFrame) -> dict:
    """Reproduce the published benchmark on exactly its own 24 checkpoints."""
    sub = it[it.model.isin(PUBLISHED)].copy()
    assert len(sub) == 24, f"expected 24 shared checkpoints, found {len(sub)}"
    new = sorted(set(it.model) - set(PUBLISHED))

    pub = pd.DataFrame(PUBLISHED, index=["u", "r", "m"]).T
    sub = sub.set_index("model")
    dev = {}
    for cond, ours_col in (("u", "u_ppl"), ("r", "r_ppl"), ("m", "m_ppl")):
        d = (sub[ours_col] - pub[cond]).abs() / pub[cond] * 100
        dev[cond] = d
    mixed_out = sorted(dev["m"][dev["m"] > 5].index)

    out = {
        "n_shared": int(len(sub)),
        "n_new": len(new),
        "new_checkpoints": new,
        "published_ppl_deviation_pct": {
            "unicode_median": float(dev["u"].median()),
            "unicode_max": float(dev["u"].max()),
            "unicode_argmax": str(dev["u"].idxmax()),
            "romanized_median": float(dev["r"].median()),
            "romanized_max": float(dev["r"].max()),
            "romanized_argmax": str(dev["r"].idxmax()),
            "mixed_median": float(dev["m"].median()),
            "mixed_outliers_gt5pct": mixed_out,
            "mixed_median_excl_outliers": float(
                dev["m"].drop(index=mixed_out).median()),
        },
        # the published headline quantities, recomputed on the published pool
        "ppl_ratio": {
            "median": float(sub.ppl_ratio.median()),
            "min": float(sub.ppl_ratio.min()),
            "max": float(sub.ppl_ratio.max()),
            "argmin": str(sub.ppl_ratio.idxmin()),
            "argmax": str(sub.ppl_ratio.idxmax()),
        },
        "m_ppl_ratio_median": float(sub.m_ppl_ratio.median()),
        "cv_pct": {
            "unicode_ppl": _cv(sub.u_ppl),
            "romanized_ppl": _cv(sub.r_ppl),
            "mixed_ppl": _cv(sub.m_ppl),
        },
        "d_bpb_median": float(sub.d_bpb.median()),
        "d_bpb_median_prob_factor": float(2 ** sub.d_bpb.median()),
        "d_bpw_median": float(sub.d_bpw.median()),
    }
    for name, (x, y) in {
        "params_vs_unicode_ppl": (sub.params, sub.u_ppl),
        "params_vs_romanized_ppl": (sub.params, sub.r_ppl),
        "params_vs_mixed_ppl": (sub.params, sub.m_ppl),
        "params_vs_unicode_bpb": (sub.params, sub.u_bpb),
        "params_vs_romanized_bpb": (sub.params, sub.r_bpb),
        "unicode_vs_romanized_ppl": (sub.u_ppl, sub.r_ppl),
        "unicode_vs_mixed_ppl": (sub.u_ppl, sub.m_ppl),
        "ppl_vs_bpb_unicode": (sub.u_ppl, sub.u_bpb),
        "fertility_vs_unicode_ppl": (sub.u_tok_per_word, sub.u_ppl),
    }.items():
        r, p = _sp(x, y)
        out[name] = dict(rho=r, p=p, n=int(len(sub)))
    return out


# --------------------------------------------- 2. perplexity decomposition ---
def decomposition(it: pd.DataFrame) -> dict:
    r"""Split the log perplexity ratio exactly into two named parts.

    Perplexity is exp(NLL / T) with T the number of scored tokens, and
    NLL = ln2 * bpb * Bytes, so

        log2 PPL = bpb * (Bytes / T) = A * x,

    with A the bits per byte and x the number of bytes each token carries.
    Across the two script conditions the change in log2 PPL is exactly

        A_r x_r - A_u x_u = Abar * (x_r - x_u)  +  xbar * (A_r - A_u),

    where Abar and xbar are the two-condition means. The first term is the
    part of the reported degradation that comes only from the same content
    being cut into a different number of tokens. The second is the part that
    comes from the model genuinely assigning less probability per byte.
    """
    d = it.copy()
    d["x_u"] = d.u_bytes / d.u_tok           # bytes per token, native
    d["x_r"] = d.r_bytes / d.r_tok           # bytes per token, Romanized
    d["A_u"], d["A_r"] = d.u_bpb, d.r_bpb

    # exactness check against the perplexities we actually measured
    d["log2ppl_u_pred"] = d.A_u * d.x_u
    d["log2ppl_r_pred"] = d.A_r * d.x_r
    resid = np.abs(d.log2ppl_u_pred - np.log2(d.u_ppl)).max()
    resid = max(resid, np.abs(d.log2ppl_r_pred - np.log2(d.r_ppl)).max())

    Abar = (d.A_u + d.A_r) / 2
    xbar = (d.x_u + d.x_r) / 2
    d["total"] = d.A_r * d.x_r - d.A_u * d.x_u          # bits, log2 of the ratio
    d["tok_term"] = Abar * (d.x_r - d.x_u)
    d["loss_term"] = xbar * (d.A_r - d.A_u)
    d["tok_share"] = d.tok_term / d.total

    out = {
        "identity_max_abs_resid_bits": float(resid),
        "median_total_bits": float(d.total.median()),
        "median_tok_term_bits": float(d.tok_term.median()),
        "median_loss_term_bits": float(d.loss_term.median()),
        "median_tok_share_pct": float(d.tok_share.median() * 100),
        "min_tok_share_pct": float(d.tok_share.min() * 100),
        "max_tok_share_pct": float(d.tok_share.max() * 100),
        # multiplicative reading: the reported ratio factorises into these two
        "median_total_factor": float(2 ** d.total.median()),
        "median_tok_factor": float(2 ** d.tok_term.median()),
        "median_loss_factor": float(2 ** d.loss_term.median()),
        "n": int(len(d)),
        "bytes_per_token_native_median": float(d.x_u.median()),
        "bytes_per_token_romanized_median": float(d.x_r.median()),
    }
    # same split on the 24 published checkpoints
    s = d[d.model.isin(PUBLISHED)]
    out["shared24"] = {
        "median_total_bits": float(s.total.median()),
        "median_tok_term_bits": float(s.tok_term.median()),
        "median_loss_term_bits": float(s.loss_term.median()),
        "median_tok_share_pct": float(s.tok_share.median() * 100),
        "median_total_factor": float(2 ** s.total.median()),
        "median_tok_factor": float(2 ** s.tok_term.median()),
        "median_loss_factor": float(2 ** s.loss_term.median()),
    }
    d[["model", "total", "tok_term", "loss_term", "tok_share"]].to_csv(
        os.path.join(CM.OUT_DIR, "ppl_decomposition.csv"), index=False)
    return out


# ------------------------------------------------- 3. flattening robustness --
def _ols(x, y):
    lr = stats.linregress(x, y)
    n = len(x)
    return dict(slope=float(lr.slope), intercept=float(lr.intercept),
                r2=float(lr.rvalue ** 2), p=float(lr.pvalue),
                stderr=float(lr.stderr), n=int(n),
                # two-sided test of slope = 1, the full-transfer null
                p_slope_eq_1=float(2 * stats.t.sf(
                    abs((lr.slope - 1.0) / lr.stderr), df=n - 2)))


def _loco(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    sl, r2 = [], []
    for i in range(len(x)):
        m = np.ones(len(x), bool); m[i] = False
        lr = stats.linregress(x[m], y[m])
        sl.append(lr.slope); r2.append(lr.rvalue ** 2)
    return dict(slope_min=float(min(sl)), slope_max=float(max(sl)),
                r2_min=float(min(r2)), r2_max=float(max(r2)),
                n_fits=int(len(sl)))


def _boot_slope(x, y, b=B):
    x = np.asarray(x, float); y = np.asarray(y, float)
    n = len(x); out = []
    for _ in range(b):
        idx = RNG.integers(0, n, n)
        if len(np.unique(x[idx])) < 3:
            continue
        out.append(stats.linregress(x[idx], y[idx]).slope)
    out = np.asarray(out)
    return dict(lo=float(np.percentile(out, 2.5)), hi=float(np.percentile(out, 97.5)),
                median=float(np.median(out)), n_ok=int(len(out)))


def flattening(EX: pd.DataFrame, chance: float) -> dict:
    mm = EX[(EX.dataset == "sinhala_mmlu") & (EX.model != "LaMini-GPT-1.5B")]
    u = mm.u_acc.to_numpy(float)
    r = mm.r_acc.to_numpy(float)
    head = u - chance
    loss = u - r

    lv = _ols(u, r)          # levels form: Romanized on native
    hd = _ols(head, loss)    # headroom form, as previously reported

    # Permutation null. Break any association between native and Romanized
    # ability by shuffling the Romanized scores across checkpoints, then refit
    # both forms. The levels form collapses to a zero slope, as it should. The
    # headroom form keeps a slope near one and a high R^2 purely because native
    # accuracy appears on both axes, which is why it cannot be read as
    # independent evidence.
    P = 20000
    ns_lv, nr_lv, ns_hd, nr_hd = [], [], [], []
    for _ in range(P):
        rp = RNG.permutation(r)
        a = stats.linregress(u, rp); ns_lv.append(a.slope); nr_lv.append(a.rvalue ** 2)
        bfit = stats.linregress(head, u - rp); ns_hd.append(bfit.slope); nr_hd.append(bfit.rvalue ** 2)
    ns_lv, nr_lv = np.array(ns_lv), np.array(nr_lv)
    ns_hd, nr_hd = np.array(ns_hd), np.array(nr_hd)

    return {
        "n": int(len(u)),
        "chance": float(chance),
        "levels": {**lv,
                   "slope_boot_ci": _boot_slope(u, r),
                   "loco": _loco(u, r),
                   "retained_fraction": lv["slope"],
                   "erased_fraction": 1 - lv["slope"]},
        "headroom": {**hd,
                     "slope_boot_ci": _boot_slope(head, loss),
                     "loco": _loco(head, loss)},
        "permutation_null": {
            "n_perm": P,
            "levels_slope_mean": float(ns_lv.mean()),
            "levels_r2_mean": float(nr_lv.mean()),
            "levels_r2_p95": float(np.percentile(nr_lv, 95)),
            "levels_p_r2_ge_obs": float((nr_lv >= lv["r2"]).mean()),
            "headroom_slope_mean": float(ns_hd.mean()),
            "headroom_slope_p2_5": float(np.percentile(ns_hd, 2.5)),
            "headroom_slope_p97_5": float(np.percentile(ns_hd, 97.5)),
            "headroom_r2_mean": float(nr_hd.mean()),
            "headroom_r2_p95": float(np.percentile(nr_hd, 95)),
            "headroom_p_r2_ge_obs": float((nr_hd >= hd["r2"]).mean()),
        },
        "algebraic_identity_note": (
            "loss = u - r and headroom = u - chance, so the headroom slope is "
            "1 minus the levels slope by construction: "
            f"1 - {lv['slope']:.4f} = {1 - lv['slope']:.4f} against a fitted "
            f"{hd['slope']:.4f}."),
    }


def flattening_cells(chance: float) -> dict:
    c = pd.read_csv(os.path.join(CM.OUT_DIR, "mmlu_strata.csv"))
    u, r = c.u.to_numpy(float), c.r.to_numpy(float)
    lv = _ols(u, r)
    hd = _ols(u - chance, u - r)
    rho, prho = _sp(u - chance, u - r)
    return {
        "n_cells": int(len(c)),
        "levels": {**lv, "slope_boot_ci": _boot_slope(u, r), "loco": _loco(u, r)},
        "headroom": {**hd, "spearman_rho": rho, "spearman_p": prho},
        # weighting cells by item count, so the big Humanities cells are not
        # given the same influence as the small Language ones
        "levels_weighted_slope": float(
            np.polyfit(u, r, 1, w=np.sqrt(c.n.to_numpy(float)))[0]),
    }


# ---------------------------------------------------------- 4. linkage CIs ---
def linkage_ci() -> dict:
    j = pd.read_csv(os.path.join(CM.OUT_DIR, "linkage.csv"))
    j = j[j.model != "LaMini-GPT-1.5B"]
    preds = ["u_bpb", "r_bpb", "d_bpb", "u_bpw", "d_bpw", "ppl_ratio", "u_ppl",
             "r_ppl", "params"]
    tgts = (("gap", "mmlu_gap"), ("u_acc", "mmlu_unicode_acc"), ("d_mcc", "sold_d_mcc"))
    out = {}
    for x in preds:
        for y, yl in tgts:
            a = j[x].to_numpy(float); b = j[y].to_numpy(float)
            n = len(a)
            rho, p = _sp(a, b)
            bs = []
            for _ in range(B):
                idx = RNG.integers(0, n, n)
                if len(np.unique(a[idx])) < 3 or len(np.unique(b[idx])) < 3:
                    continue
                bs.append(stats.spearmanr(a[idx], b[idx]).statistic)
            bs = np.asarray([v for v in bs if np.isfinite(v)])
            loo = []
            for i in range(n):
                m = np.ones(n, bool); m[i] = False
                loo.append(stats.spearmanr(a[m], b[m]).statistic)
            out[f"{x}~{yl}"] = dict(
                rho=rho, p=p, n=int(n),
                ci_lo=float(np.percentile(bs, 2.5)),
                ci_hi=float(np.percentile(bs, 97.5)),
                loo_min=float(min(loo)), loo_max=float(max(loo)),
                loo_sign_stable=bool(np.sign(min(loo)) == np.sign(max(loo))))
    return out


# ------------------------------------------------------- 5. prompt pilot -----
def pilot() -> dict:
    base = os.path.join(CM.REPO, "results", "prompt_template_evaluation", "results",
                        "analysis_out")
    pooled = pd.read_csv(os.path.join(base, "pooled_by_template.csv"), encoding="utf-8-sig")
    byscript = pd.read_csv(os.path.join(base, "by_template_and_script.csv"), encoding="utf-8-sig")
    pooled.columns = [c.lstrip("\ufeff") for c in pooled.columns]
    byscript.columns = [c.lstrip("\ufeff") for c in byscript.columns]

    sel = os.path.join(CM.REPO, "results", "prompt_template_evaluation",
                       "sinhala_mmlu_prompt_selection.jsonl")
    pilot_ids = [json.loads(l)["id"] for l in open(sel, encoding="utf-8")]
    # the pilot items come from the same id space as the frozen evaluation set
    ev = pd.read_csv(CM._find(CM.EXTRINSIC_MODELS["Qwen3.5-9B"][0], "sinhala_mmlu"),
                     encoding="utf-8-sig")
    ev.columns = [c.lstrip("\ufeff") for c in ev.columns]
    overlap = sorted(set(pilot_ids) & set(ev["id"].astype(str)))

    winners = {}
    for ds, g in pooled.groupby("dataset"):
        g = g.sort_values("overall_accuracy", ascending=False)
        winners[ds] = {
            "best_template": str(g.iloc[0].template),
            "best_overall_acc": float(g.iloc[0].overall_accuracy),
            "t1_overall_acc": float(g[g.template == "T1_direct"].overall_accuracy.iloc[0]),
            "t1_invalid_rate": float(g[g.template == "T1_direct"].invalid_rate.iloc[0]),
            "best_invalid_rate": float(g.iloc[0].invalid_rate),
        }
    # does the chosen template keep its ordering under both scripts?
    consist = {}
    for ds, g in byscript.groupby("dataset"):
        piv = g.pivot(index="template", columns="script", values="overall_accuracy")
        consist[ds] = {
            "t1_unicode": float(piv.loc["T1_direct", "unicode"]),
            "t1_romanized": float(piv.loc["T1_direct", "romanized"]),
            "t1_rank_unicode": int(piv["unicode"].rank(ascending=False).loc["T1_direct"]),
            "t1_rank_romanized": int(piv["romanized"].rank(ascending=False).loc["T1_direct"]),
        }
    return {
        "n_generations": int(pooled.n.sum() * 1),
        "n_models": 9,
        "n_templates": 3,
        "n_items_per_dataset": 20,
        "template_used": "T1_direct",
        "criterion": "pooled overall accuracy, unparseable output counted wrong",
        "winners": winners,
        "script_consistency": consist,
        "mmlu_pilot_items": len(pilot_ids),
        "mmlu_pilot_items_in_eval_set": len(overlap),
        "mmlu_eval_items": int(len(ev)),
        "mmlu_pilot_overlap_pct": 100.0 * len(overlap) / len(ev),
        "pooled_table": pooled.to_dict("records"),
        "byscript_table": byscript.to_dict("records"),
    }


def main():
    CM.ensure_dirs()
    it = pd.read_csv(os.path.join(CM.OUT_DIR, "intrinsic_pooled.csv"))
    EX = pd.read_csv(os.path.join(CM.OUT_DIR, "extrinsic_main.csv"))
    chance = CM.chance_level("sinhala_mmlu")

    out = {
        "shared24": shared24(it),
        "decomposition": decomposition(it),
        "flattening_models": flattening(EX, chance),
        "flattening_cells": flattening_cells(chance),
        "linkage_ci": linkage_ci(),
        "pilot": pilot(),
    }
    with open(os.path.join(CM.OUT_DIR, "robustness_numbers.json"), "w") as f:
        json.dump(out, f, indent=2, default=str)

    slim = json.loads(json.dumps(out, default=str))
    slim["pilot"].pop("pooled_table"); slim["pilot"].pop("byscript_table")
    print(json.dumps(slim, indent=2))


if __name__ == "__main__":
    main()
