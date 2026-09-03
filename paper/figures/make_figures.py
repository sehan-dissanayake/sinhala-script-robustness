"""Publication figures. Reads only paper/analysis/out/ and results/.

Run from the repository root:  python paper/figures/make_figures.py
Outputs vector PDFs into paper/figures/.

Note: strings below are rendered by matplotlib's own text engine, not LaTeX, so
they must not contain LaTeX escapes. Only $...$ mathtext is interpreted.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "analysis"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, ScalarFormatter

import common as C

OUT = C.OUT_DIR
FIG = C.FIG_DIR
os.makedirs(FIG, exist_ok=True)

# ACL geometry: 6.3in text width, 0.2in column separation.
COL = 3.05
WIDE = 6.30

# Height of figure 1. Overridable so a paper with a different page geometry
# can trade vertical space without shrinking the labels.
H1 = 2.26

# Vertical nudge, in points, for the left-hand spread label of figure 1 panel (a).
# The midpoint of that range sits almost exactly on a y tick, so at some figure
# heights the label and the tick label collide.
SPREAD_DY_A = 5

# Okabe--Ito, safe for the common colour vision deficiencies and in greyscale.
UNI = "#0072B2"     # blue      : Sinhala script
ROM = "#D55E00"     # vermillion: Romanized
MIX = "#009E73"     # green     : mixed script
REF = "#4D4D4D"     # grey      : reference lines
HI = "#CC79A7"      # pink      : highlights

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["STIXGeneral", "Times New Roman", "Nimbus Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 7.2,
    "axes.labelsize": 7.2,
    "axes.titlesize": 7.4,
    "xtick.labelsize": 6.6,
    "ytick.labelsize": 6.6,
    "legend.fontsize": 6.4,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.minor.width": 0.4,
    "ytick.minor.width": 0.4,
    "xtick.major.size": 2.4,
    "ytick.major.size": 2.4,
    "lines.linewidth": 0.9,
    "legend.frameon": False,
    "legend.handlelength": 1.4,
    "legend.handletextpad": 0.5,
    "legend.borderpad": 0.2,
    "legend.labelspacing": 0.3,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.01,
    "pdf.fonttype": 42,
})


def save(fig, name):
    p = os.path.join(FIG, name)
    fig.savefig(p + ".pdf")
    fig.savefig(p + ".png", dpi=400)
    plt.close(fig)
    print("wrote", p + ".pdf")


def load():
    it = pd.read_csv(os.path.join(OUT, "intrinsic_pooled.csv"))
    ex = pd.read_csv(os.path.join(OUT, "extrinsic_main.csv"))
    sold = pd.read_csv(os.path.join(OUT, "sold_detail.csv"))
    strata = pd.read_csv(os.path.join(OUT, "mmlu_strata.csv"))
    ni = json.load(open(os.path.join(OUT, "intrinsic_numbers.json")))
    ne = json.load(open(os.path.join(OUT, "extrinsic_numbers.json")))
    rb = json.load(open(os.path.join(OUT, "robustness_numbers.json")))
    return it, ex, sold, strata, ni, ne, rb


def plain_log_y(ax, ticks):
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(FixedLocator(ticks))
    ax.yaxis.set_minor_locator(FixedLocator([]))
    f = ScalarFormatter()
    f.set_scientific(False)
    ax.yaxis.set_major_formatter(f)


# ---------------------------------------------------------------- figure 1 ---

def slope_panel(ax, left, right, labels, highlight, ylabel, chance=None,
                chance_label=None, label_dx=4, annotate=True):
    """Two-column slope chart: one line per checkpoint, left value to right value."""
    x = [0.0, 1.0]
    for lo, ro, lab in zip(left, right, labels):
        hot = lab in highlight
        ax.plot(x, [lo, ro], color=(HI if hot else "0.66"),
                lw=(1.3 if hot else 0.55), alpha=(1.0 if hot else 0.8),
                zorder=(3 if hot else 1), solid_capstyle="round")
    ax.scatter([0.0] * len(left), left, s=12, color=UNI, zorder=4,
               edgecolor="white", linewidth=0.3, clip_on=False)
    ax.scatter([1.0] * len(right), right, s=12, color=ROM, zorder=4,
               edgecolor="white", linewidth=0.3, clip_on=False)
    if chance is not None:
        ax.axhline(chance, color=REF, lw=0.7, ls=(0, (3, 2)), zorder=0)
        ax.text(0.62, chance - 0.30, chance_label, ha="center", va="top",
                fontsize=6.0, color=REF)
    if annotate:
        for lab in highlight:
            i = labels.index(lab)
            ax.annotate(lab, (1.0, right[i]), xytext=(label_dx, 0),
                        textcoords="offset points", va="center", ha="left",
                        fontsize=6.2)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Sinhala\nscript", "Romanized"])
    ax.set_ylabel(ylabel)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="x", length=0, pad=3)


def spread_bracket(ax, xpos, lo, hi, color, text, side, dy=0):
    """Vertical range bracket with its size written beside it.

    dy nudges the label vertically, in points, for the cases where the midpoint
    of the range happens to land on a y tick label.
    """
    ax.annotate("", xy=(xpos, lo), xytext=(xpos, hi), annotation_clip=False,
                arrowprops=dict(arrowstyle="|-|,widthA=0.22,widthB=0.22",
                                lw=0.8, color=color))
    dx = -3 if side == "left" else 3
    ax.annotate(text, (xpos, (lo + hi) / 2), xytext=(dx, dy), annotation_clip=False,
                textcoords="offset points", ha=("right" if side == "left" else "left"),
                va="center", fontsize=6.2, color=color)


def fig1(it, ex, ni, ne, rb):
    """Three views of the same flattening, across the full text width.

    (a) intrinsic cost per word, (b) downstream accuracy, (c) how much of a
    checkpoint's Sinhala-script accuracy survives the change of script.
    """
    fig, axes = plt.subplots(1, 3, figsize=(WIDE, H1),
                             gridspec_kw=dict(wspace=0.40, width_ratios=[1, 1, 1.5]))

    # (a) intrinsic, bits per word: word counts are identical within a pair
    a = axes[0]
    d = it.sort_values("u_bpw")
    hl = ["Llama-3.1-8B", "LaMini-GPT-1.5B"]
    slope_panel(a, d.u_bpw.tolist(), d.r_bpw.tolist(), d.model.tolist(), hl,
                "bits per word (lower is better)", annotate=False)
    a.set_title("(a) LM cost, 31 checkpoints", loc="left", pad=6)
    spread_bracket(a, -0.17, it.u_bpw.min(), it.u_bpw.max(), UNI,
                   f"spread\n{it.u_bpw.max()-it.u_bpw.min():.1f}", "left",
                   dy=SPREAD_DY_A)
    spread_bracket(a, 1.17, it.r_bpw.min(), it.r_bpw.max(), ROM,
                   f"spread\n{it.r_bpw.max()-it.r_bpw.min():.1f}", "right")
    a.set_xlim(-0.50, 1.46)

    # (b) extrinsic, SinhalaMMLU accuracy
    b = axes[1]
    m = ex[(ex.dataset == "sinhala_mmlu") & (ex.model != "LaMini-GPT-1.5B")].sort_values("u_acc")
    hl2 = ["Qwen3.5-9B", "TinyLlama-1.1B-Chat"]
    slope_panel(b, m.u_acc.tolist(), m.r_acc.tolist(), m.model.tolist(), hl2,
                "SinhalaMMLU accuracy (%)",
                chance=ne["chance"]["sinhala_mmlu"], chance_label="chance 23.4",
                annotate=False)
    b.set_title("(b) SinhalaMMLU accuracy", loc="left", pad=6)
    spread_bracket(b, -0.17, m.u_acc.min(), m.u_acc.max(), UNI,
                   f"spread\n{m.u_acc.max()-m.u_acc.min():.1f} pp", "left")
    spread_bracket(b, 1.17, m.r_acc.min(), m.r_acc.max(), ROM,
                   f"spread\n{m.r_acc.max()-m.r_acc.min():.1f} pp", "right")
    b.set_xlim(-0.50, 1.46)

    # (c) how much of it survives
    c = axes[2]
    chance = ne["chance"]["sinhala_mmlu"]
    st = strata_for_panel()
    lv = rb["flattening_models"]["levels"]
    cl = rb["flattening_cells"]["levels"]
    lo, hi = 20.5, 46.5
    xs = np.linspace(lo, hi, 40)
    c.plot(xs, xs, color="0.62", lw=0.8, ls=(0, (2, 2)), zorder=1)
    c.axhline(chance, color=REF, lw=0.7, ls=(0, (1, 2)), zorder=1)
    c.scatter(st.u, st.r, s=9, marker="s", facecolor="none", edgecolor=MIX,
              linewidth=0.65, zorder=2)
    c.scatter(m.u_acc, m.r_acc, s=19, color=UNI, edgecolor="black", linewidth=0.3,
              zorder=4)
    c.plot(xs, cl["intercept"] + cl["slope"] * xs, color=MIX, lw=1.0,
           ls=(0, (4, 2)), zorder=3)
    c.plot(xs, lv["intercept"] + lv["slope"] * xs, color=UNI, lw=1.0, zorder=3)
    c.set_xlabel("Sinhala-script accuracy (%)")
    c.set_ylabel("Romanized accuracy (%)")
    c.set_xlim(lo, hi)
    c.set_ylim(21.0, 34.6)
    c.set_title("(c) how much survives", loc="left", pad=6)
    handles = [
        Line2D([], [], color=UNI, marker="o", lw=1.0, markersize=3.2,
               markeredgecolor="black", markeredgewidth=0.3,
               label=f"{len(m)} checkpoints, slope {lv['slope']:.2f}"),
        Line2D([], [], color=MIX, marker="s", lw=1.0, ls=(0, (4, 2)), markersize=3.0,
               markerfacecolor="none", markeredgewidth=0.65,
               label=f"{len(st)} cells, slope {cl['slope']:.2f}"),
    ]
    c.legend(handles=handles, loc="lower right", fontsize=5.7,
             labelspacing=0.24, handlelength=1.6, frameon=True, framealpha=0.92,
             edgecolor="none", borderpad=0.25)
    c.annotate("full transfer", (30.4, 31.6), fontsize=5.7, color="0.42",
               rotation=52, ha="center", va="center")
    c.annotate("chance", (lo + 0.35, chance - 0.30), fontsize=5.7, color=REF,
               ha="left", va="top")
    save(fig, "fig1_flattening")


def strata_for_panel():
    return pd.read_csv(os.path.join(OUT, "mmlu_strata.csv"))


# ---------------------------------------------------------------- figure 2 ---

def fig2(it, ni):
    fig, axes = plt.subplots(2, 1, figsize=(COL, 3.30), gridspec_kw=dict(hspace=0.58))
    fert = it.u_tok_per_word
    ticks = [3, 5, 10, 20]

    a = axes[0]
    sc = a.scatter(it.u_bpb, it.u_ppl, c=fert, cmap="viridis_r", s=16,
                   edgecolor="black", linewidth=0.25, zorder=3)
    plain_log_y(a, ticks)
    a.set_xlabel("bits per byte, Sinhala script")
    a.set_ylabel("perplexity")
    a.set_xlim(1.08, 2.52)
    a.set_ylim(2.0, 40)
    r = ni["rank"]["ppl_vs_bpb_unicode"]
    a.set_title(f"(a) perplexity vs. bits per byte:  $\\rho$ = {r['rho']:.2f}, "
                f"$p$ = {r['p']:.2f}", loc="left", pad=4)
    cb = fig.colorbar(sc, ax=a, pad=0.02, aspect=11)
    cb.set_label("tokens / word", labelpad=2)
    cb.outline.set_linewidth(0.4)
    cb.ax.tick_params(width=0.4, length=1.8)
    for name, dx, dy, ha in [("Qwen3.5-4B", 13, 5, "left"), ("Gemma-2-9B", 13, -5, "left"),
                             ("Pythia-410M", 34, -9, "left")]:
        row = it[it.model == name].iloc[0]
        a.annotate(name, (row.u_bpb, row.u_ppl), xytext=(dx, dy),
                   textcoords="offset points", fontsize=5.8, ha=ha, va="center",
                   arrowprops=dict(arrowstyle="-", lw=0.4, color="0.35",
                                   shrinkA=0.5, shrinkB=2.5))

    b = axes[1]
    b.scatter(fert, it.u_ppl, s=16, color=UNI, edgecolor="black", linewidth=0.25, zorder=3)
    plain_log_y(b, ticks)
    b.set_xlabel("tokens per Sinhala word (tokenizer fertility)")
    b.set_ylabel("perplexity")
    b.set_xlim(3.2, 15.6)
    b.set_ylim(2.0, 40)
    r2 = ni["rank"]["fertility_vs_unicode_ppl"]
    b.set_title(f"(b) perplexity vs. tokenizer fertility:  $\\rho$ = {r2['rho']:.2f}, "
                f"$p$ < $10^{{-9}}$", loc="left", pad=4)
    sl, ic = np.polyfit(fert, np.log(it.u_ppl), 1)
    xs = np.linspace(fert.min(), fert.max(), 50)
    b.plot(xs, np.exp(ic + sl * xs), color=REF, lw=0.8, ls=(0, (3, 2)), zorder=2)
    b.annotate("Qwen3.5, Gemma\ntokenizers", (5.3, 32), fontsize=5.8,
               va="top", ha="left")
    b.annotate("byte fallback\n(OPT, Pythia, Minitron)", (13.4, 6.6), fontsize=5.8,
               va="center", ha="right")
    save(fig, "fig2_perplexity_artifact")


# ---------------------------------------------------------------- figure 3 ---

def fig3(ex, sold, strata, ne, rb):
    """Matthews correlation on SOLD, before and after romanization."""
    fig, b = plt.subplots(figsize=(COL, 1.62))
    s = sold[sold.u_mcc >= 0.10].sort_values("u_mcc").reset_index(drop=True)
    y = np.arange(len(s))
    for yi in y:
        b.annotate("", xy=(s.r_mcc[yi], yi), xytext=(s.u_mcc[yi], yi),
                   arrowprops=dict(arrowstyle="-|>,head_width=0.12,head_length=0.28",
                                   lw=0.85, color="0.55", shrinkA=1.6, shrinkB=0.4))
    b.scatter(s.u_mcc, y, s=19, color=UNI, zorder=4, edgecolor="white", linewidth=0.3,
              label="Sinhala script")
    b.scatter(s.r_mcc, y, s=19, color=ROM, zorder=4, edgecolor="white", linewidth=0.3,
              label="Romanized")
    b.set_yticks(y)
    b.set_yticklabels(s.model, fontsize=6.0)
    b.set_xlabel("SOLD Matthews correlation coefficient")
    b.set_xlim(0.0, 0.415)
    b.set_ylim(-0.8, len(s) - 0.2)
    for yi in y:
        b.annotate(f"{s.mcc_retained_pct[yi]:.0f}% kept", (0.325, yi),
                   fontsize=5.9, va="center", ha="left", color="0.35")
    b.legend(loc="lower right", fontsize=5.9)
    save(fig, "fig3_sold_mcc")


# ---------------------------------------------------------------- figure 4 ---

def fig4(it, ni):
    fig, ax = plt.subplots(figsize=(COL, 1.72))
    conds = [("Sinhala script", "u_bpb", UNI, "unicode"),
             ("mixed script", "m_bpb", MIX, None),
             ("Romanized", "r_bpb", ROM, "romanized")]
    rng = np.random.default_rng(7)
    styles = {1: (0, (1, 1.5)), 3: (0, (3.5, 2))}
    for i, (name, col, colr, ngkey) in enumerate(conds):
        v = it[col].to_numpy()
        ax.scatter(v, i + rng.uniform(-0.17, 0.17, len(v)), s=12, color=colr,
                   alpha=0.85, edgecolor="black", linewidth=0.2, zorder=3)
        ax.plot([np.median(v)] * 2, [i - 0.32, i + 0.32], color="black", lw=1.1, zorder=4)
        if ngkey:
            for order in (1, 3):
                x = ni["ngram_reference"][ngkey][f"order{order}"]["bpb"]
                ax.plot([x, x], [i - 0.37, i + 0.37], color=REF, lw=0.9,
                        ls=styles[order], zorder=2)
    ax.set_yticks(range(3))
    ax.set_yticklabels([c[0] for c in conds])
    ax.set_ylim(-0.62, 2.62)
    ax.invert_yaxis()
    ax.set_xlabel("bits per byte (lower is better)")
    ax.set_xlim(1.05, 4.35)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    handles = [Line2D([], [], color=REF, lw=0.9, ls=styles[1], label="character 2-gram"),
               Line2D([], [], color=REF, lw=0.9, ls=styles[3], label="character 4-gram"),
               Line2D([], [], color="black", lw=1.1, label="median checkpoint")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 1.19),
              ncol=3, fontsize=6.0, columnspacing=0.9)
    save(fig, "fig4_ngram_reference")




# ---------------------------------------------------------------- figure 5 ---

def fig5(it):
    """Where the reported degradation ratio actually comes from.

    Each checkpoint's log2 perplexity ratio is split exactly into the part caused
    by the same content occupying a different number of tokens, and the part
    caused by the model assigning less probability per byte.
    """
    d = pd.read_csv(os.path.join(OUT, "ppl_decomposition.csv"))
    d = d.merge(it[["model", "u_ppl", "r_ppl"]], on="model")
    d["ratio"] = d.r_ppl / d.u_ppl
    d = d.sort_values("total").reset_index(drop=True)
    y = np.arange(len(d))

    fig, ax = plt.subplots(figsize=(COL, 4.35))
    ax.barh(y, d.tok_term, height=0.72, color=HI, edgecolor="black", linewidth=0.25,
            label="token-count normaliser", zorder=3)
    ax.barh(y, d.loss_term, left=d.tok_term, height=0.72, color=UNI,
            edgecolor="black", linewidth=0.25, label="per-byte loss", zorder=3)
    for i, r in d.iterrows():
        ax.annotate(f"{r.ratio:.0f}$\\times$", (r.total + 0.12, i), fontsize=5.6,
                    va="center", ha="left", color="0.3")
    ax.set_yticks(y)
    ax.set_yticklabels(d.model, fontsize=5.8)
    ax.set_ylim(-0.7, len(d) - 0.3)
    ax.set_xlim(0, 11.4)
    ax.set_xlabel("bits of the log$_2$ perplexity ratio")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.055), ncol=2, fontsize=6.2,
              columnspacing=1.0)
    save(fig, "fig5_ppl_decomposition")


if __name__ == "__main__":
    C.ensure_dirs()
    it, ex, sold, strata, ni, ne, rb = load()
    fig1(it, ex, ni, ne, rb)
    fig2(it, ni)
    fig3(ex, sold, strata, ne, rb)
    fig4(it, ni)
    fig5(it)
