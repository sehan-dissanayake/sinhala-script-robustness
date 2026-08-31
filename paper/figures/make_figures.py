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

# Okabe--Ito, safe for the common colour vision deficiencies and in greyscale.
UNI = "#0072B2"     # blue      : native Unicode
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
    return it, ex, sold, strata, ni, ne


def plain_log_y(ax, ticks):
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(FixedLocator(ticks))
    ax.yaxis.set_minor_locator(FixedLocator([]))
    f = ScalarFormatter()
    f.set_scientific(False)
    ax.yaxis.set_major_formatter(f)


# ---------------------------------------------------------------- figure 1 ---

def slope_panel(ax, left, right, labels, highlight, ylabel, chance=None,
                chance_label=None, label_dx=4):
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
        ax.text(0.42, chance - 0.25, chance_label, ha="center", va="top",
                fontsize=6.0, color=REF)
    for lab in highlight:
        i = labels.index(lab)
        ax.annotate(lab, (1.0, right[i]), xytext=(label_dx, 0),
                    textcoords="offset points", va="center", ha="left", fontsize=6.2)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["native\nUnicode", "Romanized"])
    ax.set_ylabel(ylabel)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="x", length=0, pad=3)


def spread_bracket(ax, xpos, lo, hi, color, text, side):
    ax.annotate("", xy=(xpos, lo), xytext=(xpos, hi), annotation_clip=False,
                arrowprops=dict(arrowstyle="|-|,widthA=0.22,widthB=0.22",
                                lw=0.8, color=color))
    dx = -3 if side == "left" else 3
    ax.annotate(text, (xpos, (lo + hi) / 2), xytext=(dx, 0), annotation_clip=False,
                textcoords="offset points", ha=("right" if side == "left" else "left"),
                va="center", fontsize=6.2, color=color)


def fig1(it, ex, ni, ne):
    fig, axes = plt.subplots(1, 2, figsize=(WIDE, 2.75), gridspec_kw=dict(wspace=0.36))

    # (a) intrinsic, bits per word: word counts are identical within a pair
    a = axes[0]
    d = it.sort_values("u_bpw")
    hl = ["Llama-3.1-8B", "Qwen3.5-9B-Base", "Zephyr-7B-beta", "LaMini-GPT-1.5B"]
    slope_panel(a, d.u_bpw.tolist(), d.r_bpw.tolist(), d.model.tolist(), hl,
                "bits per word (lower is better)")
    a.set_title("(a) language modelling cost, 31 checkpoints", loc="left", pad=6)
    spread_bracket(a, -0.135, it.u_bpw.min(), it.u_bpw.max(), UNI,
                   f"spread\n{it.u_bpw.max()-it.u_bpw.min():.1f}", "left")
    spread_bracket(a, 1.76, it.r_bpw.min(), it.r_bpw.max(), ROM,
                   f"spread\n{it.r_bpw.max()-it.r_bpw.min():.1f}", "right")
    a.set_xlim(-0.40, 2.02)

    # (b) extrinsic, SinhalaMMLU accuracy
    b = axes[1]
    m = ex[(ex.dataset == "sinhala_mmlu") & (ex.model != "LaMini-GPT-1.5B")].sort_values("u_acc")
    hl2 = ["Qwen3.5-9B", "Qwen3.5-4B", "Llama-3.1-8B-Instruct", "TinyLlama-1.1B-Chat"]
    slope_panel(b, m.u_acc.tolist(), m.r_acc.tolist(), m.model.tolist(), hl2,
                "SinhalaMMLU accuracy (%)",
                chance=ne["chance"]["sinhala_mmlu"], chance_label="chance 23.4")
    b.set_title("(b) downstream accuracy, 9 instruction-tuned checkpoints",
                loc="left", pad=6)
    spread_bracket(b, -0.135, m.u_acc.min(), m.u_acc.max(), UNI,
                   f"spread\n{m.u_acc.max()-m.u_acc.min():.1f} pp", "left")
    spread_bracket(b, 2.05, m.r_acc.min(), m.r_acc.max(), ROM,
                   f"spread\n{m.r_acc.max()-m.r_acc.min():.1f} pp", "right")
    b.set_xlim(-0.44, 2.40)
    save(fig, "fig1_flattening")


# ---------------------------------------------------------------- figure 2 ---

def fig2(it, ni):
    fig, axes = plt.subplots(2, 1, figsize=(COL, 3.30), gridspec_kw=dict(hspace=0.58))
    fert = it.u_tok_per_word
    ticks = [3, 5, 10, 20]

    a = axes[0]
    sc = a.scatter(it.u_bpb, it.u_ppl, c=fert, cmap="viridis_r", s=16,
                   edgecolor="black", linewidth=0.25, zorder=3)
    plain_log_y(a, ticks)
    a.set_xlabel("bits per byte, native Unicode")
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

def fig3(ex, sold, strata, ne):
    fig, axes = plt.subplots(2, 1, figsize=(COL, 3.15), gridspec_kw=dict(hspace=0.60))
    chance = ne["chance"]["sinhala_mmlu"]

    a = axes[0]
    m = ex[(ex.dataset == "sinhala_mmlu") & (ex.model != "LaMini-GPT-1.5B")]
    st = strata.copy()
    st["headroom"] = st.u - chance
    a.axhline(0, color="0.85", lw=0.6, zorder=0)
    a.axvline(0, color="0.85", lw=0.6, zorder=0)
    a.scatter(st.headroom, st.gap, s=10, marker="s", facecolor="none",
              edgecolor=MIX, linewidth=0.7, zorder=2,
              label=f"domain $\\times$ difficulty cells ($n$ = {len(st)})")
    a.scatter(m.head_u, m.gap, s=21, color=UNI, edgecolor="black", linewidth=0.3,
              zorder=4, label=f"checkpoints ($n$ = {len(m)})")
    xs = np.linspace(-3.5, 22.5, 40)
    f1 = ne["gap_vs_headroom_mmlu"]
    a.plot(xs, f1["intercept"] + f1["slope"] * xs, color=UNI, lw=1.0, zorder=3)
    f2 = ne["mmlu_cell_gap_vs_headroom"]
    a.plot(xs, f2["intercept"] + f2["slope"] * xs, color=MIX, lw=1.0,
           ls=(0, (4, 2)), zorder=3)
    a.set_xlabel("native-script headroom above chance (pp)")
    a.set_ylabel("Romanization loss (pp)")
    a.set_xlim(-4.0, 23.5)
    a.set_ylim(-3.2, 17.5)
    a.set_title("(a) the loss tracks native-script headroom", loc="left", pad=4)
    a.text(0.03, 0.97, f"slope {f1['slope']:.2f},  $R^2$ = {f1['r2']:.2f}",
           transform=a.transAxes, va="top", ha="left", fontsize=6.1, color=UNI)
    a.text(0.03, 0.86, f"slope {f2['slope']:.2f},  $R^2$ = {f2['r2']:.2f}",
           transform=a.transAxes, va="top", ha="left", fontsize=6.1, color=MIX)
    a.legend(loc="lower right", fontsize=5.9)

    b = axes[1]
    s = sold[sold.u_mcc >= 0.10].sort_values("u_mcc").reset_index(drop=True)
    y = np.arange(len(s))
    for yi in y:
        b.annotate("", xy=(s.r_mcc[yi], yi), xytext=(s.u_mcc[yi], yi),
                   arrowprops=dict(arrowstyle="-|>,head_width=0.12,head_length=0.28",
                                   lw=0.85, color="0.55", shrinkA=1.6, shrinkB=0.4))
    b.scatter(s.u_mcc, y, s=19, color=UNI, zorder=4, edgecolor="white", linewidth=0.3,
              label="native Unicode")
    b.scatter(s.r_mcc, y, s=19, color=ROM, zorder=4, edgecolor="white", linewidth=0.3,
              label="Romanized")
    b.set_yticks(y)
    b.set_yticklabels(s.model, fontsize=6.0)
    b.set_xlabel("SOLD Matthews correlation coefficient")
    b.set_xlim(0.0, 0.415)
    b.set_ylim(-0.75, len(s) - 0.25)
    b.set_title("(b) offensive-language detection collapses", loc="left", pad=4)
    for yi in y:
        b.annotate(f"{s.mcc_retained_pct[yi]:.0f}% kept", (0.325, yi),
                   fontsize=5.9, va="center", ha="left", color="0.35")
    b.legend(loc="upper left", fontsize=5.9, bbox_to_anchor=(-0.012, 1.03))
    save(fig, "fig3_floor_effect")


# ---------------------------------------------------------------- figure 4 ---

def fig4(it, ni):
    fig, ax = plt.subplots(figsize=(COL, 1.72))
    conds = [("native Unicode", "u_bpb", UNI, "unicode"),
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




# --------------------------------------------------- short-paper figure ------

def figS1(it, ex, strata, ni, ne):
    """One column, two panels: the metric artifact and the floor-effect law.

    Used by the 4-page version, where float budget allows only two figures.
    """
    fig, axes = plt.subplots(2, 1, figsize=(COL, 2.55), gridspec_kw=dict(hspace=0.58))

    a = axes[0]
    sc = a.scatter(it.u_bpb, it.u_ppl, c=it.u_tok_per_word, cmap="viridis_r", s=17,
                   edgecolor="black", linewidth=0.25, zorder=3)
    plain_log_y(a, [3, 5, 10, 20])
    a.set_xlabel("bits per byte, native Unicode")
    a.set_ylabel("perplexity")
    a.set_xlim(1.08, 2.52)
    a.set_ylim(2.0, 40)
    r = ni["rank"]["ppl_vs_bpb_unicode"]
    a.set_title(f"(a) the two metrics disagree:  $\\rho$ = {r['rho']:.2f}, "
                f"$p$ = {r['p']:.2f}", loc="left", pad=4)
    cb = fig.colorbar(sc, ax=a, pad=0.02, aspect=11)
    cb.set_label("tokens / word", labelpad=2)
    cb.outline.set_linewidth(0.4)
    cb.ax.tick_params(width=0.4, length=1.8)
    for name, dx, dy in [("Qwen3.5-4B", 13, 5), ("Gemma-2-9B", 13, -5),
                         ("Pythia-410M", 36, 7)]:
        row = it[it.model == name].iloc[0]
        a.annotate(name, (row.u_bpb, row.u_ppl), xytext=(dx, dy),
                   textcoords="offset points", fontsize=5.8, ha="left", va="center",
                   arrowprops=dict(arrowstyle="-", lw=0.4, color="0.35",
                                   shrinkA=0.5, shrinkB=2.5))

    b = axes[1]
    chance = ne["chance"]["sinhala_mmlu"]
    m = ex[(ex.dataset == "sinhala_mmlu") & (ex.model != "LaMini-GPT-1.5B")]
    st = strata.copy()
    st["headroom"] = st.u - chance
    b.axhline(0, color="0.85", lw=0.6, zorder=0)
    b.axvline(0, color="0.85", lw=0.6, zorder=0)
    b.scatter(st.headroom, st.gap, s=10, marker="s", facecolor="none",
              edgecolor=MIX, linewidth=0.7, zorder=2,
              label=f"benchmark strata ($n$ = {len(st)})")
    b.scatter(m.head_u, m.gap, s=21, color=UNI, edgecolor="black", linewidth=0.3,
              zorder=4, label=f"checkpoints ($n$ = {len(m)})")
    xs = np.linspace(-3.5, 22.5, 40)
    f1 = ne["gap_vs_headroom_mmlu"]
    f2 = ne["mmlu_cell_gap_vs_headroom"]
    b.plot(xs, f1["intercept"] + f1["slope"] * xs, color=UNI, lw=1.0, zorder=3)
    b.plot(xs, f2["intercept"] + f2["slope"] * xs, color=MIX, lw=1.0,
           ls=(0, (4, 2)), zorder=3)
    b.set_xlabel("native-script headroom above chance (pp)")
    b.set_ylabel("Romanization loss (pp)")
    b.set_xlim(-4.0, 23.5)
    b.set_ylim(-3.2, 17.5)
    b.set_title("(b) the loss tracks native-script headroom", loc="left", pad=4)
    b.text(0.03, 0.97, f"slope {f1['slope']:.2f},  $R^2$ = {f1['r2']:.2f}",
           transform=b.transAxes, va="top", ha="left", fontsize=6.1, color=UNI)
    b.text(0.03, 0.86, f"slope {f2['slope']:.2f},  $R^2$ = {f2['r2']:.2f}",
           transform=b.transAxes, va="top", ha="left", fontsize=6.1, color=MIX)
    b.legend(loc="lower right", fontsize=5.9)
    save(fig, "figS1_metric_and_law")


def figS2(it, ex, ne):
    """Single-column stacked version of the flattening figure, for the 4-page paper,
    which has room for only one full-width float."""
    fig, axes = plt.subplots(2, 1, figsize=(COL, 3.75), gridspec_kw=dict(hspace=0.42))

    a = axes[0]
    d = it.sort_values("u_bpw")
    hl = ["Llama-3.1-8B", "Qwen3.5-9B-Base", "LaMini-GPT-1.5B"]
    slope_panel(a, d.u_bpw.tolist(), d.r_bpw.tolist(), d.model.tolist(), hl,
                "bits per word")
    a.set_title("(a) 31 checkpoints, language modelling cost", loc="left", pad=5)
    spread_bracket(a, -0.10, it.u_bpw.min(), it.u_bpw.max(), UNI,
                   f"{it.u_bpw.max()-it.u_bpw.min():.1f}", "left")
    spread_bracket(a, 2.02, it.r_bpw.min(), it.r_bpw.max(), ROM,
                   f"{it.r_bpw.max()-it.r_bpw.min():.1f}", "right")
    a.set_xlim(-0.22, 2.28)

    b = axes[1]
    m = ex[(ex.dataset == "sinhala_mmlu") & (ex.model != "LaMini-GPT-1.5B")].sort_values("u_acc")
    hl2 = ["Qwen3.5-9B", "Qwen3.5-4B", "Llama-3.1-8B-Instruct"]
    slope_panel(b, m.u_acc.tolist(), m.r_acc.tolist(), m.model.tolist(), hl2,
                "SinhalaMMLU accuracy (%)",
                chance=ne["chance"]["sinhala_mmlu"], chance_label="chance 23.4")
    b.set_title("(b) 9 instruction-tuned checkpoints, accuracy", loc="left", pad=5)
    spread_bracket(b, -0.10, m.u_acc.min(), m.u_acc.max(), UNI,
                   f"{m.u_acc.max()-m.u_acc.min():.1f}", "left")
    spread_bracket(b, 2.02, m.r_acc.min(), m.r_acc.max(), ROM,
                   f"{m.r_acc.max()-m.r_acc.min():.1f}", "right")
    b.set_xlim(-0.22, 2.28)
    save(fig, "figS2_flattening_narrow")


if __name__ == "__main__":
    C.ensure_dirs()
    it, ex, sold, strata, ni, ne = load()
    fig1(it, ex, ni, ne)
    fig2(it, ni)
    fig3(ex, sold, strata, ne)
    fig4(it, ni)
    figS1(it, ex, strata, ni, ne)
    figS2(it, ex, ne)
