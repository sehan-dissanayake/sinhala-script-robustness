"""Extrinsic analysis: paired significance, effect sizes, strata, degeneracy, linkage."""
from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.contingency_tables import mcnemar

import common as CM

RNG = np.random.default_rng(20260831)
B = 10000


# --------------------------------------------------------------------- tests --

def holm(p):
    p = np.asarray(p, dtype=float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    run = 0.0
    for i, o in enumerate(order):
        run = max(run, (m - i) * p[o])
        adj[o] = min(1.0, run)
    return adj


def paired_acc(u, r):
    u = np.asarray(u, int); r = np.asarray(r, int)
    b = int(((u == 1) & (r == 0)).sum())
    c = int(((u == 0) & (r == 1)).sum())
    tbl = [[int(((u == 1) & (r == 1)).sum()), b], [c, int(((u == 0) & (r == 0)).sum())]]
    if b + c == 0:
        p, kind = 1.0, "exact"
    elif b + c < 25:
        p, kind = float(mcnemar(tbl, exact=True).pvalue), "exact"
    else:
        p, kind = float(mcnemar(tbl, exact=False, correction=True).pvalue), "chi2"
    d = u - r
    n = len(u)
    boot = d[RNG.integers(0, n, size=(B, n))].mean(axis=1) * 100
    return dict(n=n, u_acc=u.mean() * 100, r_acc=r.mean() * 100, gap=d.mean() * 100,
                b=b, c=c, n_disc=b + c, p=p, test=kind,
                gap_lo=float(np.percentile(boot, 2.5)), gap_hi=float(np.percentile(boot, 97.5)))


def above_chance(correct, chance_vec):
    """One-sided normal approximation to the Poisson-binomial null."""
    k = int(np.sum(correct))
    mu = float(np.sum(chance_vec))
    sd = float(np.sqrt(np.sum(chance_vec * (1 - chance_vec))))
    z = (k - mu) / sd
    return dict(z=float(z), p=float(stats.norm.sf(z)), acc=float(np.mean(correct) * 100),
                chance=float(np.mean(chance_vec) * 100))


def macro_f1_w(gold_off, pred_off, valid, w):
    po, pn = pred_off & valid, (~pred_off) & valid
    f1 = []
    for cp, cg in ((po, gold_off), (pn, ~gold_off)):
        tp = w @ (cp & cg); fp = w @ (cp & ~cg); fn = w @ (~cp & cg)
        f1.append(np.where(2 * tp + fp + fn > 0, 2 * tp / (2 * tp + fp + fn + 1e-12), 0.0))
    return (f1[0] + f1[1]) / 2 * 100


def mcc_w(gold_off, pred_off, valid, w):
    """Matthews correlation with invalid answers folded in as the wrong class."""
    p = pred_off & valid                     # predicted OFF
    tp = w @ (p & gold_off); tn = w @ (~p & ~gold_off)
    fp = w @ (p & ~gold_off); fn = w @ (~p & gold_off)
    den = np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return np.where(den > 0, (tp * tn - fp * fn) / (den + 1e-12), 0.0)


def boot_weights(n, b=B):
    idx = RNG.integers(0, n, size=(b, n))
    w = np.zeros((b, n))
    np.add.at(w, (np.repeat(np.arange(b), n), idx.ravel()), 1.0)
    return w / n


# ---------------------------------------------------------------------- main --

def main():
    CM.ensure_dirs()
    out = {}
    chance = {d: CM.chance_level(d) for d in CM.DATASETS}
    out["chance"] = chance
    out["mmlu_five_option_items"] = int((CM.mmlu_option_counts() == 5).sum())
    out["n_items"] = {d: int(len(CM.load_items(next(iter(CM.EXTRINSIC_MODELS)), d))) for d in CM.DATASETS}
    out["n_models"] = len(CM.EXTRINSIC_MODELS)

    # ---------------------------------------------------------------- table --
    rows = []
    for ds in CM.DATASETS:
        for m in CM.EXTRINSIC_MODELS:
            d = CM.load_items(m, ds)
            cv = CM.chance_per_item(ds, len(d))
            r = paired_acc(d.unicode_correct, d.romanized_correct)
            r.update(model=m, dataset=ds, params=CM.EXTRINSIC_MODELS[m][2])
            for s, tag in (("unicode", "u"), ("romanized", "r")):
                ok = CM.validity(d, s, ds)
                r[f"{tag}_invalid"] = float((~ok).mean() * 100)
                col = f"{s}_pred" if ds == "sold" else f"{s}_pred_label"
                vc = d.loc[ok, col].astype(str).value_counts(normalize=True)
                r[f"{tag}_top_share"] = float(vc.iloc[0] * 100) if len(vc) else np.nan
                r[f"{tag}_top_label"] = vc.index[0] if len(vc) else None
                ac = above_chance(d[f"{s}_correct"].to_numpy(), cv)
                r[f"{tag}_z"] = ac["z"]; r[f"{tag}_p_above"] = ac["p"]
                r[f"{tag}_tok"] = int(d[f"{s}_n_input_tokens"].sum())
            r["tok_ratio"] = r["r_tok"] / r["u_tok"]
            r["head_u"] = r["u_acc"] - chance[ds]
            r["head_r"] = r["r_acc"] - chance[ds]
            r["retention"] = r["head_r"] / r["head_u"] if r["head_u"] > 1e-9 else np.nan
            rows.append(r)
    T = pd.DataFrame(rows)
    T["p_holm"] = np.concatenate([holm(T.loc[T.dataset == ds, "p"].tolist()) for ds in CM.DATASETS])

    # competence screen: significantly above chance on the native-script condition
    ALPHA = 0.01
    T["competent"] = T.u_p_above < ALPHA
    T["degenerate_u"] = T.u_top_share > 90
    T.to_csv(os.path.join(CM.OUT_DIR, "extrinsic_main.csv"), index=False)
    out["competence_alpha"] = ALPHA
    comp = {ds: T[(T.dataset == ds) & T.competent & ~T.degenerate_u].model.tolist() for ds in CM.DATASETS}
    out["competent_models"] = comp
    out["competent_and_nondegenerate_all_mcq"] = sorted(set(comp["sinhala_mmlu"]))

    # ------------------------------------------------------------- headline --
    for ds in CM.DATASETS:
        s = T[T.dataset == ds]
        sc = s[s.competent & ~s.degenerate_u]
        sx = s[s.model != "LaMini-GPT-1.5B"]
        out[f"{ds}_summary"] = dict(
            u_range=[float(s.u_acc.min()), float(s.u_acc.max())],
            r_range=[float(s.r_acc.min()), float(s.r_acc.max())],
            u_spread=float(s.u_acc.max() - s.u_acc.min()),
            r_spread=float(s.r_acc.max() - s.r_acc.min()),
            u_range_x=[float(sx.u_acc.min()), float(sx.u_acc.max())],
            r_range_x=[float(sx.r_acc.min()), float(sx.r_acc.max())],
            u_spread_x=float(sx.u_acc.max() - sx.u_acc.min()),
            r_spread_x=float(sx.r_acc.max() - sx.r_acc.min()),
            n_competent=int(len(sc)),
            competent_gaps={r.model: round(r.gap, 2) for r in sc.itertuples()},
            competent_retention={r.model: round(r.retention, 3) for r in sc.itertuples()},
            n_sig_holm_competent=int((sc.p_holm < 0.05).sum()),
            max_p_holm_competent=float(sc.p_holm.max()) if len(sc) else np.nan,
            median_retention=float(sc.retention.median()) if len(sc) else np.nan,
        )

    # flattening regression on MMLU: romanized accuracy against unicode accuracy
    for ds in ["sinhala_mmlu", "global_piqa"]:
        s = T[(T.dataset == ds) & ~T.model.isin(["LaMini-GPT-1.5B"])]
        lr = stats.linregress(s.u_acc, s.r_acc)
        sl = [stats.linregress(s.u_acc.to_numpy()[i], s.r_acc.to_numpy()[i]).slope
              for i in RNG.integers(0, len(s), size=(5000, len(s)))]
        out[f"{ds}_flattening"] = dict(slope=float(lr.slope), intercept=float(lr.intercept),
                                       r2=float(lr.rvalue ** 2), p=float(lr.pvalue),
                                       slope_ci=[float(np.percentile(sl, 2.5)), float(np.percentile(sl, 97.5))],
                                       n=int(len(s)), note="LaMini excluded (native-script parse failure)")
    # does the gap grow with native competence?
    s = T[(T.dataset == "sinhala_mmlu") & ~T.model.isin(["LaMini-GPT-1.5B"])]
    lr = stats.linregress(s.head_u, s.gap)
    out["gap_vs_headroom_mmlu"] = dict(slope=float(lr.slope), intercept=float(lr.intercept),
                                       r2=float(lr.rvalue ** 2), p=float(lr.pvalue), n=int(len(s)),
                                       spearman=stats.spearmanr(s.head_u, s.gap).statistic)

    # -------------------------------------------------------------- SOLD ----
    sold = []
    for m in CM.EXTRINSIC_MODELS:
        d = CM.load_items(m, "sold").reset_index(drop=True)
        gold_off = (d.gold_label.astype(str) == "OFF").to_numpy()
        n = len(d)
        w = boot_weights(n)
        one = np.ones((1, n)) / n
        rec = dict(model=m, params=CM.EXTRINSIC_MODELS[m][2])
        pack = {}
        for s, tag in (("unicode", "u"), ("romanized", "r")):
            pr = d[f"{s}_pred"].fillna("INVALID").astype(str).to_numpy()
            po = pr == "OFF"; ok = np.isin(pr, ["NOT", "OFF"])
            pack[s] = (po, ok)
            rec[f"{tag}_macroF1"] = float(macro_f1_w(gold_off, po, ok, one)[0])
            rec[f"{tag}_mcc"] = float(mcc_w(gold_off, po, ok, one)[0])
            rec[f"{tag}_off_rate"] = float(po.mean() * 100)
            rec[f"{tag}_invalid"] = float((~ok).mean() * 100)
            rec[f"{tag}_acc"] = float((np.where(po, "OFF", np.where(ok, "NOT", "X"))
                                       == d.gold_label.astype(str).to_numpy()).mean() * 100)
        dF1 = macro_f1_w(gold_off, *pack["unicode"], w) - macro_f1_w(gold_off, *pack["romanized"], w)
        dM = mcc_w(gold_off, *pack["unicode"], w) - mcc_w(gold_off, *pack["romanized"], w)
        rec["d_macroF1"] = rec["u_macroF1"] - rec["r_macroF1"]
        rec["d_mcc"] = rec["u_mcc"] - rec["r_mcc"]
        rec["dF1_ci"] = [float(np.percentile(dF1, 2.5)), float(np.percentile(dF1, 97.5))]
        rec["dF1_p"] = float(2 * min((dF1 <= 0).mean(), (dF1 >= 0).mean()))
        rec["dMCC_ci"] = [float(np.percentile(dM, 2.5)), float(np.percentile(dM, 97.5))]
        rec["dMCC_p"] = float(2 * min((dM <= 0).mean(), (dM >= 0).mean()))
        rec["mcc_retained_pct"] = 100 * rec["r_mcc"] / rec["u_mcc"] if rec["u_mcc"] > 0 else np.nan
        sold.append(rec)
    S = pd.DataFrame(sold)
    S["dF1_p_holm"] = holm(S.dF1_p.tolist())
    S["dMCC_p_holm"] = holm(S.dMCC_p.tolist())
    S.to_csv(os.path.join(CM.OUT_DIR, "sold_detail.csv"), index=False)
    out["sold_majority_baseline"] = float(
        max((CM.load_items("Hormoz-8B", "sold").gold_label == "NOT").mean(),
            (CM.load_items("Hormoz-8B", "sold").gold_label == "OFF").mean()) * 100)
    # models with a non-trivial native-script signal: MCC bootstrap CI excludes 0.10
    real = S[S.u_mcc >= 0.10].model.tolist()
    out["sold_real_signal_models"] = real
    sr = S[S.model.isin(real)]
    out["sold_summary"] = dict(
        n_real=len(real),
        u_mcc={r.model: round(r.u_mcc, 3) for r in sr.itertuples()},
        r_mcc={r.model: round(r.r_mcc, 3) for r in sr.itertuples()},
        mcc_retained_pct={r.model: round(r.mcc_retained_pct, 1) for r in sr.itertuples()},
        median_mcc_retained=float(sr.mcc_retained_pct.median()),
        d_macroF1={r.model: round(r.d_macroF1, 2) for r in sr.itertuples()},
        n_dMCC_sig_holm=int((sr.dMCC_p_holm < 0.05).sum()),
        acc_change={r.model: round(r.u_acc - r.r_acc, 2) for r in sr.itertuples()},
    )
    # accuracy is uninformative here: correlation between accuracy change and MCC change
    out["sold_acc_vs_mcc_delta"] = dict(
        pearson=float(stats.pearsonr(S.u_acc - S.r_acc, S.d_mcc)[0]),
        note="across all 10 models")

    # ------------------------------------------------------- MMLU strata ----
    d = CM.load_all_items("sinhala_mmlu")
    comp_m = out["competent_and_nondegenerate_all_mcq"]
    dc = d[d.model.isin(comp_m)].copy()
    long = pd.concat([
        dc.assign(script="unicode", correct=dc.unicode_correct),
        dc.assign(script="romanized", correct=dc.romanized_correct)])
    long["script"] = pd.Categorical(long.script, ["unicode", "romanized"])
    long["difficulty"] = pd.Categorical(long.difficulty, ["Easy", "Medium", "Hard"])

    strata = []
    for (dom, dif), g in dc.groupby(["domain", "difficulty"]):
        strata.append(dict(domain=dom, difficulty=dif, n=len(g) // len(comp_m),
                           u=g.unicode_correct.mean() * 100, r=g.romanized_correct.mean() * 100,
                           gap=(g.unicode_correct.mean() - g.romanized_correct.mean()) * 100))
    pd.DataFrame(strata).to_csv(os.path.join(CM.OUT_DIR, "mmlu_strata.csv"), index=False)

    by_dif = []
    for dif, g in dc.groupby("difficulty", observed=True):
        r = paired_acc(g.unicode_correct, g.romanized_correct)
        r.update(difficulty=dif, n_items=len(g) // len(comp_m))
        by_dif.append(r)
    by_dif = pd.DataFrame(by_dif)
    by_dif["p_holm"] = holm(by_dif.p.tolist())
    by_dif.to_csv(os.path.join(CM.OUT_DIR, "mmlu_by_difficulty.csv"), index=False)
    out["mmlu_by_difficulty"] = by_dif[["difficulty", "n_items", "u_acc", "r_acc", "gap",
                                        "gap_lo", "gap_hi", "p_holm"]].round(4).to_dict("records")

    by_dom = []
    for dom, g in dc.groupby("domain", observed=True):
        r = paired_acc(g.unicode_correct, g.romanized_correct)
        r.update(domain=dom, n_items=len(g) // len(comp_m))
        by_dom.append(r)
    by_dom = pd.DataFrame(by_dom)
    by_dom["p_holm"] = holm(by_dom.p.tolist())
    by_dom.to_csv(os.path.join(CM.OUT_DIR, "mmlu_by_domain.csv"), index=False)
    out["mmlu_by_domain"] = by_dom[["domain", "n_items", "u_acc", "r_acc", "gap",
                                    "gap_lo", "gap_hi", "p_holm"]].round(4).to_dict("records")

    # interaction test, item-clustered logistic regression
    fit = smf.glm("correct ~ C(script) * C(difficulty) + C(model)", data=long,
                  family=sm.families.Binomial()).fit(cov_type="cluster",
                                                     cov_kwds={"groups": long["id"]})
    terms = [t for t in fit.params.index if "script" in t and "difficulty" in t]
    out["mmlu_script_x_difficulty"] = {t: dict(coef=float(fit.params[t]), p=float(fit.pvalues[t]))
                                       for t in terms}
    fit2 = smf.glm("correct ~ C(script) * C(domain) + C(model)", data=long,
                   family=sm.families.Binomial()).fit(cov_type="cluster",
                                                      cov_kwds={"groups": long["id"]})
    terms2 = [t for t in fit2.params.index if "script" in t and "domain" in t]
    out["mmlu_script_x_domain"] = {t: dict(coef=float(fit2.params[t]), p=float(fit2.pvalues[t]))
                                   for t in terms2}
    out["mmlu_script_main_effect"] = dict(
        coef=float(fit.params["C(script)[T.romanized]"]),
        p=float(fit.pvalues["C(script)[T.romanized]"]),
        odds_ratio=float(np.exp(fit.params["C(script)[T.romanized]"])))

    # ------------------------------------------------------- Global PIQA ----
    dp = CM.load_all_items("global_piqa")
    dpc = dp[dp.model.isin(comp_m)]
    out["piqa_cultural"] = {}
    for flag, g in dp.groupby(dp.culturally_specific.astype(str)):
        r = paired_acc(g.unicode_correct, g.romanized_correct)
        out["piqa_cultural"][f"culturally_specific={flag}"] = {
            k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}
    out["piqa_n_culturally_specific"] = int(
        CM.load_items("Hormoz-8B", "global_piqa").culturally_specific.astype(str).eq("True").sum())
    r = paired_acc(dpc.unicode_correct, dpc.romanized_correct)
    out["piqa_pooled_competent"] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}

    # pooled across the competent cohort, per dataset
    out["pooled_competent"] = {}
    for ds in CM.DATASETS:
        dd = CM.load_all_items(ds)
        dd = dd[dd.model.isin(comp[ds])] if comp[ds] else dd.iloc[0:0]
        if len(dd):
            r = paired_acc(dd.unicode_correct, dd.romanized_correct)
            out["pooled_competent"][ds] = {k: (round(v, 6) if isinstance(v, float) else v)
                                           for k, v in r.items()}

    # ------------------------------------------------- token-length control --
    out["token_ratio"] = {}
    for ds in CM.DATASETS:
        s = T[T.dataset == ds]
        out["token_ratio"][ds] = dict(median=float(s.tok_ratio.median()),
                                      min=float(s.tok_ratio.min()), max=float(s.tok_ratio.max()),
                                      n_shorter=int((s.tok_ratio < 1).sum()), n=int(len(s)))
    # within MMLU: is the drop concentrated on items whose romanization inflates tokens?
    tercile = []
    for m in comp_m:
        dd = CM.load_items(m, "sinhala_mmlu")
        ratio = dd.romanized_n_input_tokens / dd.unicode_n_input_tokens
        q = pd.qcut(ratio, 3, labels=["low", "mid", "high"])
        for lab, g in dd.groupby(q, observed=True):
            tercile.append(dict(model=m, tercile=lab, n=len(g),
                                gap=(g.unicode_correct.mean() - g.romanized_correct.mean()) * 100,
                                mean_ratio=float(ratio[g.index].mean())))
    tc = pd.DataFrame(tercile)
    out["mmlu_gap_by_token_ratio_tercile"] = tc.groupby("tercile", observed=True)[
        ["gap", "mean_ratio"]].mean().round(3).to_dict("index")
    tc.to_csv(os.path.join(CM.OUT_DIR, "mmlu_token_tercile.csv"), index=False)

    # ------------------------------------------------------------- linkage --
    it = pd.read_csv(os.path.join(CM.OUT_DIR, "intrinsic_pooled.csv"))
    key2name = {v[1]: k for k, v in CM.EXTRINSIC_MODELS.items()}
    it["ext"] = it.key.map(key2name)
    lk = it.dropna(subset=["ext"]).set_index("ext")
    mm = T[T.dataset == "sinhala_mmlu"].set_index("model")
    j = lk.join(mm[["gap", "u_acc", "r_acc", "head_u", "retention"]]).join(
        S.set_index("model")[["d_macroF1", "d_mcc", "u_mcc"]])
    j.to_csv(os.path.join(CM.OUT_DIR, "linkage.csv"))
    out["linkage_n"] = int(len(j))
    jj = j.drop(index=["LaMini-GPT-1.5B"], errors="ignore")
    out["linkage"] = {}
    for x in ["u_bpb", "r_bpb", "d_bpb", "u_bpw", "d_bpw", "ppl_ratio", "u_ppl", "r_ppl", "params"]:
        for y, yl in (("gap", "mmlu_gap"), ("u_acc", "mmlu_unicode_acc"), ("d_mcc", "sold_d_mcc")):
            sp = stats.spearmanr(jj[x], jj[y])
            out["linkage"][f"{x}~{yl}"] = dict(rho=float(sp.statistic), p=float(sp.pvalue), n=int(len(jj)))

    # ------------------------------------------- extra: floor-effect scaling --
    # Across the 18 domain x difficulty cells, does the gap track native headroom?
    cells = pd.read_csv(os.path.join(CM.OUT_DIR, "mmlu_strata.csv"))
    cells["headroom"] = cells.u - chance["sinhala_mmlu"]
    lr = stats.linregress(cells.headroom, cells.gap)
    out["mmlu_cell_gap_vs_headroom"] = dict(
        n_cells=int(len(cells)), slope=float(lr.slope), intercept=float(lr.intercept),
        r2=float(lr.rvalue ** 2), p=float(lr.pvalue),
        spearman=float(stats.spearmanr(cells.headroom, cells.gap).statistic))

    # ------------------------------------------- extra: Global PIQA power ----
    pq = T[(T.dataset == "global_piqa") & (T.model != "LaMini-GPT-1.5B")]
    n_pos = int((pq.gap > 0).sum()); n_neg = int((pq.gap < 0).sum())
    out["piqa_sign_test"] = dict(n_positive=n_pos, n_negative=n_neg,
                                 p=float(stats.binomtest(n_pos, n_pos + n_neg, 0.5).pvalue))
    # minimum detectable effect at n=100, alpha=.05, power=.80, for the observed discordance
    out["piqa_median_discordant_pairs"] = int(pq.n_disc.median())

    # ------------------------------------------- extra: answer concentration --
    conc = []
    for ds in ["sinhala_mmlu", "sold"]:
        for m in CM.EXTRINSIC_MODELS:
            d = CM.load_items(m, ds)
            rec = dict(dataset=ds, model=m)
            for s, tag in (("unicode", "u"), ("romanized", "r")):
                ok = CM.validity(d, s, ds)
                col = f"{s}_pred" if ds == "sold" else f"{s}_pred_label"
                p = d.loc[ok, col].astype(str).value_counts(normalize=True).to_numpy()
                rec[f"{tag}_top"] = float(p[0] * 100) if len(p) else np.nan
                rec[f"{tag}_H"] = float(-(p * np.log2(p)).sum()) if len(p) else np.nan
            rec["d_top"] = rec["r_top"] - rec["u_top"]
            conc.append(rec)
    conc = pd.DataFrame(conc)
    conc.to_csv(os.path.join(CM.OUT_DIR, "answer_concentration.csv"), index=False)
    cm_ = conc[(conc.dataset == "sinhala_mmlu") & conc.model.isin(comp_m)]
    out["answer_concentration_mmlu_competent"] = dict(
        u_top_mean=float(cm_.u_top.mean()), r_top_mean=float(cm_.r_top.mean()),
        n_more_concentrated_romanized=int((cm_.d_top > 0).sum()), n=int(len(cm_)),
        wilcoxon_p=float(stats.wilcoxon(cm_.r_top, cm_.u_top).pvalue))
    cs = conc[(conc.dataset == "sold") & conc.model.isin(real)]
    out["sold_off_rate_shift"] = {r.model: dict(u=round(v, 2), r=round(w, 2)) for r, v, w in zip(
        S[S.model.isin(real)].itertuples(), S[S.model.isin(real)].u_off_rate,
        S[S.model.isin(real)].r_off_rate)}
    out["sold_gold_off_rate"] = float((CM.load_items("Hormoz-8B", "sold").gold_label == "OFF").mean() * 100)

    # ------------------------------------------- extra: SOLD MCC screening ---
    scr = []
    for m in CM.EXTRINSIC_MODELS:
        d = CM.load_items(m, "sold").reset_index(drop=True)
        gold_off = (d.gold_label.astype(str) == "OFF").to_numpy()
        w = boot_weights(len(d), 4000)
        pr = d.unicode_pred.fillna("INVALID").astype(str).to_numpy()
        v = mcc_w(gold_off, pr == "OFF", np.isin(pr, ["NOT", "OFF"]), w)
        scr.append(dict(model=m, u_mcc_lo=float(np.percentile(v, 2.5)),
                        u_mcc_hi=float(np.percentile(v, 97.5))))
    out["sold_unicode_mcc_ci"] = {r["model"]: [round(r["u_mcc_lo"], 3), round(r["u_mcc_hi"], 3)]
                                  for r in scr}

    with open(os.path.join(CM.OUT_DIR, "extrinsic_numbers.json"), "w") as f:
        json.dump(out, f, indent=2, default=str)

    pd.set_option("display.width", 300)
    print("=== main ===")
    print(T[["dataset", "model", "params", "u_acc", "r_acc", "gap", "gap_lo", "gap_hi", "b", "c",
             "p_holm", "u_invalid", "r_invalid", "u_top_share", "u_p_above", "retention", "tok_ratio",
             "competent", "degenerate_u"]].round(4).to_string(index=False))
    print("\n=== SOLD ===")
    print(S[["model", "u_acc", "r_acc", "u_macroF1", "r_macroF1", "d_macroF1", "dF1_ci",
             "u_mcc", "r_mcc", "d_mcc", "dMCC_ci", "dMCC_p_holm", "mcc_retained_pct",
             "u_off_rate", "r_off_rate", "u_invalid", "r_invalid"]].round(4).to_string(index=False))
    print("\n=== selected numbers ===")
    print(json.dumps({k: v for k, v in out.items() if k != "linkage"}, indent=2, default=str))
    print("\n=== linkage ===")
    for k, v in out["linkage"].items():
        print(f"  {k}: rho={v['rho']:+.3f} p={v['p']:.4f}")


if __name__ == "__main__":
    main()
