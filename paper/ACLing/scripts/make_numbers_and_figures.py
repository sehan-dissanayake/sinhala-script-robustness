"""Numbers and figures for the ACLing 2026 version of the paper.

Reads only the frozen analysis outputs in paper/analysis/out/ and writes
  paper/ACLing/figures/*.pdf      the figures used in main.tex
  paper/ACLing/scripts/numbers.json  every number quoted in the text that is
                                      not already in paper/analysis/out/

Run from the repository root:
  python paper/ACLing/scripts/make_numbers_and_figures.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "paper" / "analysis" / "out"
HERE = Path(__file__).resolve().parent
FIG = HERE.parent / "figures"
FIG.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# data
# ---------------------------------------------------------------------------
it = pd.read_csv(OUT / "intrinsic_pooled.csv")
rob = json.loads((OUT / "robustness_numbers.json").read_text())
new7 = set(rob["shared24"]["new_checkpoints"])
it["shared24"] = ~it.model.isin(new7)
sin = json.loads((OUT / "sinllama.json").read_text())
ext = pd.read_csv(OUT / "extrinsic_main.csv")
sold = pd.read_csv(OUT / "sold_detail.csv")
link = pd.read_csv(OUT / "linkage.csv")

# code points per corpus (characters as Python counts them)
it["u_cp"] = it.u_bpb * it.u_bytes / it.u_bpc
it["r_cp"] = it.r_bpb * it.r_bytes / it.r_bpc
it["log2_ratio"] = np.log2(it.r_ppl) - np.log2(it.u_ppl)

numbers: dict = {}

# ---------------------------------------------------------------------------
# 1. The exact split of log2(PPL ratio) depends on the unit
#    log2 PPL = (bits per unit) * (units per token)
#    d(log2 PPL) = mean(bits/unit) * d(units/token) + mean(units/token) * d(bits/unit)
# ---------------------------------------------------------------------------
UNITS = {
    "byte": ("u_bpb", "r_bpb", "u_bytes", "r_bytes"),
    "code point": ("u_bpc", "r_bpc", "u_cp", "r_cp"),
    "word": ("u_bpw", "r_bpw", "u_words", "r_words"),
}


def split(df: pd.DataFrame, unit: str):
    ua, ra, un, rn = UNITS[unit]
    xu, xr = df[un] / df.u_tok, df[rn] / df.r_tok
    tok = (df[ua] + df[ra]) / 2 * (xr - xu)
    content = (xu + xr) / 2 * (df[ra] - df[ua])
    assert np.allclose(tok + content, df.log2_ratio)
    return tok, content


decomp = {}
for pool, df in [("all31", it), ("shared24", it[it.shared24])]:
    decomp[pool] = {"n": int(len(df)), "mean_log2_ratio": float(df.log2_ratio.mean()),
                    "geo_mean_ratio": float(2 ** df.log2_ratio.mean()),
                    "median_ratio": float(np.median(df.r_ppl / df.u_ppl))}
    for unit in UNITS:
        tok, content = split(df, unit)
        decomp[pool][unit] = {
            "units_sinhala": float(df[UNITS[unit][2]].iloc[0]),
            "units_romanized": float(df[UNITS[unit][3]].iloc[0]),
            "mean_token_term": float(tok.mean()),
            "mean_content_term": float(content.mean()),
            "token_share_of_mean_pct": float(100 * tok.mean() / df.log2_ratio.mean()),
            "n_content_negative": int((content < 0).sum()),
        }
numbers["decomposition"] = decomp

# per-word content gap
d_bpw = it.r_bpw - it.u_bpw
numbers["per_word_gap"] = {
    "median_bits": float(d_bpw.median()),
    "median_total_bits_ratio": float((it.r_bpw / it.u_bpw).median()),
    "n_negative": int((d_bpw < 0).sum()),
    "min": float(d_bpw.min()), "argmin": it.model[d_bpw.idxmin()],
    "max": float(d_bpw.max()), "argmax": it.model[d_bpw.idxmax()],
    "shared24_median_bits": float(d_bpw[it.shared24].median()),
    "shared24_n_negative": int((d_bpw[it.shared24] < 0).sum()),
    "sinhala_bpw_range": [float(it.u_bpw.min()), float(it.u_bpw.max())],
    "romanized_bpw_range": [float(it.r_bpw.min()), float(it.r_bpw.max())],
    "rho_sinhala_bpw_vs_gap": float(stats.spearmanr(it.u_bpw, d_bpw).statistic),
    "p_sinhala_bpw_vs_gap": float(stats.spearmanr(it.u_bpw, d_bpw).pvalue),
}
lr = stats.linregress(it.u_bpw, it.r_bpw)
numbers["per_word_gap"]["levels_slope"] = float(lr.slope)
numbers["per_word_gap"]["levels_r2"] = float(lr.rvalue ** 2)

# linkage with the per-word gap
L = link[link.model != "LaMini-GPT-1.5B"].copy()
lk = {}
for col in ["u_bpb", "r_bpb", "d_bpw", "ppl_ratio", "params"]:
    a, b = stats.spearmanr(L[col], L.gap), stats.spearmanr(L[col], L.d_mcc)
    lk[col] = {"rho_mmlu": float(a.statistic), "p_mmlu": float(a.pvalue),
               "rho_sold": float(b.statistic), "p_sold": float(b.pvalue)}
numbers["linkage"] = lk

# SinLlama in word units
p, a = sin["parent"], sin["adapted"]
numbers["sinllama"] = {
    k: {"tok_per_word": m["u_tok_per_word"], "ppl": m["u_ppl"], "u_bpw": m["u_bpw"],
        "r_bpw": m["r_bpw"], "gap_bpw": m["r_bpw"] - m["u_bpw"], "ppl_ratio": m["ppl_ratio"]}
    for k, m in [("Llama-3-8B", p), ("SinLlama", a)]
}

# ---------------------------------------------------------------------------
# Table rows: the five best models by Sinhala-script BPB, with their perplexity rank
# ---------------------------------------------------------------------------
TAB = HERE.parent / "tables"
TAB.mkdir(exist_ok=True)
rk = it.copy()
rk["ppl_rank"] = rk.u_ppl.rank(method="min").astype(int)
rk["bpb_rank"] = rk.u_bpb.rank(method="min").astype(int)
top = rk.sort_values("u_bpb").head(5)
rows = ["% Generated by scripts/make_numbers_and_figures.py. Do not edit by hand."]
for r in top.itertuples():
    rows.append(f"{r.model} & {r.params:.1f} & {r.bpb_rank} & {r.ppl_rank} & {r.u_ppl:.2f} & "
                f"{r.u_bpb:.3f} & {r.u_bpw:.2f} & {r.r_ppl:,.0f} & {r.r_bpb:.3f} & {r.r_bpw:.2f} \\\\")
med = it[["u_ppl", "u_bpb", "u_bpw", "r_ppl", "r_bpb", "r_bpw"]].median()
rows.append("\\colrule")
rows.append(f"Median of 31 & & & & {med.u_ppl:.2f} & {med.u_bpb:.3f} & {med.u_bpw:.2f} & "
            f"{med.r_ppl:,.0f} & {med.r_bpb:.3f} & {med.r_bpw:.2f} \\\\")
(TAB / "tab_top5.tex").write_text("\n".join(rows).replace(",", "{,}") + "\n")
numbers["top5_overlap_ppl_bpb"] = int(len(set(top.model) & set(rk.sort_values("u_ppl").head(5).model)))

(HERE / "numbers.json").write_text(json.dumps(numbers, indent=2))
print(json.dumps(numbers, indent=2))

# ---------------------------------------------------------------------------
# figure style
# ---------------------------------------------------------------------------
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["STIXGeneral"], "mathtext.fontset": "stix",
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8.5, "legend.fontsize": 7,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "axes.spines.top": False,
    "axes.spines.right": False, "pdf.fonttype": 42, "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
})


def family(m: str) -> str:
    for key, fam in [("Qwen3.5", "Qwen3.5"), ("Qwen", "Qwen1.5/2"), ("Gemma", "Gemma"),
                     ("Llama", "Llama"), ("Mistral", "Mistral"), ("Zephyr", "Mistral"),
                     ("BLOOM", "BLOOM"), ("OPT", "OPT"), ("Pythia", "Pythia"),
                     ("Phi", "Phi")]:
        if key.lower() in m.lower():
            return fam
    return "other"


PAL = {"Qwen3.5": "#1b6ca8", "Qwen1.5/2": "#6baed6", "Gemma": "#2a9d8f", "Llama": "#e76f51",
       "Mistral": "#f4a261", "BLOOM": "#8d6cab", "OPT": "#b5838d", "Pythia": "#6d6875",
       "Phi": "#c9184a", "other": "#9a9a9a"}
ORDER = list(PAL)
it["fam"] = it.model.map(family)


def fam_legend(ax, loc):
    hs = [plt.Line2D([], [], marker="o", ls="", ms=4, mfc=PAL[f], mec="white", mew=0.4,
                     label=f) for f in ORDER if f in set(it.fam)]
    ax.legend(handles=hs, loc=loc, frameon=False, ncol=2, handletextpad=0.2,
              columnspacing=0.6, borderaxespad=0.2)


# ---------------------------------------------------------------------------
# Figure 1: (a) perplexity follows the tokenizer, (b) per-word cost in both scripts
# ---------------------------------------------------------------------------
MARK = {"Qwen3.5": "o", "Qwen1.5/2": "s", "Gemma": "D", "Llama": "^", "Mistral": "v",
        "BLOOM": "P", "OPT": "X", "Pythia": "h", "Phi": "*", "other": "o"}
MSIZE = {"Phi": 46, "P": 30, "X": 30}


def fam_scatter(ax, xcol, ycol):
    for f in ORDER:
        sub = it[it.fam == f]
        if sub.empty:
            continue
        m = MARK[f]
        size = MSIZE.get(f, MSIZE.get(m, 24))
        ax.scatter(sub[xcol], sub[ycol], s=size, marker=m, c=PAL[f], edgecolor="0.15",
                   lw=0.45, alpha=0.92, zorder=3)


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.4, 2.6), gridspec_kw={"wspace": 0.30})

fam_scatter(ax1, "u_tok_per_word", "u_ppl")
ax1.set_yscale("log")
ax1.set_yticks([3, 5, 10, 20])
ax1.set_yticklabels(["3", "5", "10", "20"])
ax1.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
ax1.set_xlabel("Sinhala-script tokens per word (tokenizer fertility)")
ax1.set_ylabel("Sinhala-script perplexity (log scale)")
rho = stats.spearmanr(it.u_tok_per_word, it.u_ppl).statistic
ax1.set_title(f"(a) Perplexity follows the tokenizer ($\\rho$ = {rho:.2f})", loc="left")
ax1.set_xlim(3.3, 15.2)
ax1.set_ylim(2.2, 34)
ax1.grid(axis="y", which="major", color="0.92", lw=0.5, zorder=0)
for name, tx, ty, ha in [("Qwen3.5-9B", 5.6, 26, "left"), ("Gemma-2-9B", 5.6, 13.2, "left"),
                         ("Pythia-410M", 11.6, 2.45, "right")]:
    r = it[it.model == name].iloc[0]
    ax1.annotate(name, (r.u_tok_per_word, r.u_ppl), xytext=(tx, ty), fontsize=6.5, ha=ha,
                 va="center", arrowprops=dict(arrowstyle="-", lw=0.4, color="0.45",
                                              shrinkA=1, shrinkB=3))

lo, hi = 7.5, 35.5
ax2.plot([lo, hi], [lo, hi], color="0.55", lw=0.7, ls="--", zorder=1)
ax2.text(29.5, 12.0, "below the line: the Romanized\nversion costs fewer bits", fontsize=6.5,
         color="0.35", ha="center", va="center")
ax2.text(33.2, 31.0, "equal cost", fontsize=6.5, color="0.35", ha="right", rotation=45)
fam_scatter(ax2, "u_bpw", "r_bpw")
# SinLlama and its parent
pu, pr, au, ar = p["u_bpw"], p["r_bpw"], a["u_bpw"], a["r_bpw"]
ax2.scatter([pu], [pr], s=26, marker="s", c="white", edgecolor="k", lw=0.7, zorder=4)
ax2.scatter([au], [ar], s=34, marker="D", c="k", zorder=4)
ax2.annotate("", xy=(au + 0.35, ar + 0.05), xytext=(pu - 0.35, pr - 0.02),
             arrowprops=dict(arrowstyle="->", lw=0.7, color="k"), zorder=4)
ax2.text(au, ar - 2.2, "SinLlama", fontsize=6.5, ha="center")
ax2.text(pu - 3.2, pr + 3.6, "Llama-3-8B", fontsize=6.5, ha="center")
ax2.annotate("", xy=(pu - 0.3, pr + 0.5), xytext=(pu - 2.6, pr + 3.4), arrowprops=dict(arrowstyle="-", lw=0.4, color="0.4"))
ax2.set_xlim(lo, hi)
ax2.set_ylim(7.5, 35.5)
ax2.set_aspect("equal")
ax2.set_xlabel("Sinhala script, bits per word")
ax2.set_ylabel("Romanized, bits per word")
ax2.set_title("(b) The same 500 sentences in both scripts", loc="left")
hs = [plt.Line2D([], [], marker=MARK[f], ls="", ms=5.2 if f != "Phi" else 7, mfc=PAL[f],
                 mec="0.15", mew=0.45, label=f) for f in ORDER if f in set(it.fam)]
fig.legend(handles=hs, loc="lower center", ncol=len(hs), frameon=False, handletextpad=0.15,
           columnspacing=1.1, bbox_to_anchor=(0.5, -0.16), fontsize=7)
fig.savefig(FIG / "fig1_intrinsic.pdf")
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 2: romanization narrows the spread between models
#   (a) bits per word, 31 models   (b) SinhalaMMLU accuracy, 10 models
#   (c) Romanized against Sinhala-script accuracy, models and item groups
# ---------------------------------------------------------------------------
mm = ext[(ext.dataset == "sinhala_mmlu") & (ext.model != "LaMini-GPT-1.5B")].copy()
chance = rob["flattening_models"]["chance"]
lev = rob["flattening_models"]["levels"]
cel = rob["flattening_cells"]["levels"]
cells = pd.read_csv(OUT / "mmlu_strata.csv")
comp = set(json.loads((OUT / "extrinsic_numbers.json").read_text())["competent_models"]["sinhala_mmlu"])
C_S, C_R, C_HI, C_LINE = "#1b6ca8", "#e76f51", "#c9184a", "0.72"


def slope_panel(ax, u, r, names, ylabel, unit, title, chance_line=None):
    """Two-column slope chart. The best and worst Sinhala-script models are highlighted."""
    hi = {u.idxmin() if unit == "bits" else u.idxmax(), u.idxmax() if unit == "bits" else u.idxmin()}
    for i in u.index:
        col, lw, z = (C_HI, 1.3, 3) if i in hi else (C_LINE, 0.6, 1)
        ax.plot([0, 1], [u[i], r[i]], color=col, lw=lw, zorder=z, solid_capstyle="round")
    ax.scatter(np.zeros(len(u)), u, s=13, c=C_S, edgecolor="white", lw=0.3, zorder=4)
    ax.scatter(np.ones(len(r)), r, s=13, c=C_R, edgecolor="white", lw=0.3, zorder=4)
    for x, v, col, side in [(-0.16, u, C_S, "right"), (1.16, r, C_R, "left")]:
        ax.plot([x, x], [v.min(), v.max()], color=col, lw=1.0)
        for y in (v.min(), v.max()):
            ax.plot([x - 0.035, x + 0.035], [y, y], color=col, lw=1.0)
        lab = f"spread\n{v.max() - v.min():.1f}" + (" pp" if unit == "pp" else "")
        ax.text(x + (-0.1 if side == "right" else 0.1), (v.min() + v.max()) / 2, lab,
                color=col, fontsize=6.5, ha=side, va="center")
    if chance_line is not None:
        ax.axhline(chance_line, color="0.5", lw=0.6, ls="--", zorder=0)
        ax.text(0.5, 20.4, f"dashed line: chance ({chance_line:.1f}%)", fontsize=6.0,
                color="0.4", ha="center", va="center")
    ax.set_xlim(-0.85, 1.8)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Sinhala\nscript", "Romanized"])
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="x", length=0)
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc="left")


fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(6.4, 2.3),
                                    gridspec_kw={"wspace": 0.42, "width_ratios": [1, 1, 1.35]})
slope_panel(ax1, it.u_bpw, it.r_bpw, it.model, "bits per word (lower is better)", "bits",
            "(a) LM cost, 31 models")
mmi = mm.reset_index(drop=True)
slope_panel(ax2, mmi.u_acc, mmi.r_acc, mmi.model, "SinhalaMMLU accuracy (%)", "pp",
            "(b) SinhalaMMLU, 10 models", chance_line=chance)
ax2.set_ylim(19.5, 46)

lo, hi = 19.5, 46
ax3.plot([lo, hi], [lo, hi], color="0.6", lw=0.7, ls=":", zorder=1)
ax3.axhline(chance, color="0.5", lw=0.6, ls="--", zorder=0)
ax3.text(45.5, chance - 0.5, "chance", fontsize=6.3, color="0.4", ha="right", va="top")
xs = np.linspace(21, 45.5, 10)
ax3.plot(xs, lev["intercept"] + lev["slope"] * xs, color=C_S, lw=1.1, zorder=2)
xc = np.linspace(cells.u.min() - 1, cells.u.max() + 1, 10)
ax3.plot(xc, cel["intercept"] + cel["slope"] * xc, color="#2a9d8f", lw=1.1, ls="--", zorder=2)
ax3.scatter(cells.u, cells.r, s=17, marker="s", facecolor="white", edgecolor="#2a9d8f", lw=0.8,
            zorder=3)
for r in mm.itertuples():
    filled = r.model in comp
    ax3.scatter(r.u_acc, r.r_acc, s=22, c=C_S if filled else "white", edgecolor=C_S, lw=0.8,
                zorder=4)
hs = [plt.Line2D([], [], color=C_S, marker="o", ms=4, lw=1.1,
                 label=f"10 models, slope {lev['slope']:.2f}"),
      plt.Line2D([], [], color="#2a9d8f", marker="s", ms=4, mfc="white", lw=1.1, ls="--",
                 label=f"16 item groups, slope {cel['slope']:.2f}"),
      plt.Line2D([], [], color="0.6", lw=0.7, ls=":", label="full carry-over, slope 1")]
ax3.legend(handles=hs, loc="upper left", frameon=True, facecolor="white", edgecolor="none", framealpha=1, handletextpad=0.3, borderaxespad=0.1,
           fontsize=6.5, handlelength=2.2)
ax3.set_xlim(lo, hi)
ax3.set_ylim(19.5, 37)
ax3.set_xlabel("Sinhala-script accuracy (%)")
ax3.set_ylabel("Romanized accuracy (%)")
ax3.set_title("(c) Carry-over of accuracy", loc="left")
fig.savefig(FIG / "fig2_spread.pdf")
plt.close(fig)
print("figures written to", FIG)
