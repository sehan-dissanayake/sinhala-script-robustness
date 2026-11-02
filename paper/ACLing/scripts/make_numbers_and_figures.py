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
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.4, 2.3), gridspec_kw={"wspace": 0.32})

for f in ORDER:
    s = it[it.fam == f]
    ax1.scatter(s.u_tok_per_word, s.u_ppl, s=16, c=PAL[f], edgecolor="white", lw=0.4, zorder=3)
ax1.set_yscale("log")
ax1.set_yticks([3, 5, 10, 20])
ax1.set_yticklabels(["3", "5", "10", "20"])
ax1.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
ax1.set_xlabel("Sinhala-script tokens per word (tokenizer fertility)")
ax1.set_ylabel("Sinhala-script perplexity (log scale)")
rho = stats.spearmanr(it.u_tok_per_word, it.u_ppl).statistic
ax1.set_title(f"(a) Perplexity follows the tokenizer ($\\rho$ = {rho:.2f})", loc="left")
for name, dx, dy, ha in [("Gemma-2-9B", 0.4, -2.2, "left"), ("Qwen3.5-9B", 0.5, 2, "left"),
                         ("Pythia-410M", -2.6, -0.25, "right")]:
    r = it[it.model == name].iloc[0]
    ax1.annotate(name, (r.u_tok_per_word, r.u_ppl), xytext=(r.u_tok_per_word + dx, r.u_ppl + dy),
                 fontsize=6.5, ha=ha, arrowprops=dict(arrowstyle="-", lw=0.4, color="0.4"))
fam_legend(ax1, "upper right")
ax1.set_ylim(2.2, 32)

lo, hi = 7.5, 35.5
ax2.plot([lo, hi], [lo, hi], color="0.55", lw=0.7, ls="--", zorder=1)
ax2.text(29.5, 12.0, "below the line: the Romanized\nversion costs fewer bits", fontsize=6.5,
         color="0.35", ha="center", va="center")
ax2.text(33.2, 31.0, "equal cost", fontsize=6.5, color="0.35", ha="right", rotation=45)
for f in ORDER:
    s = it[it.fam == f]
    ax2.scatter(s.u_bpw, s.r_bpw, s=16, c=PAL[f], edgecolor="white", lw=0.4, zorder=3)
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
fig.savefig(FIG / "fig1_intrinsic.pdf")
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 2: (a) SinhalaMMLU accuracy in both scripts, (b) SOLD MCC
# ---------------------------------------------------------------------------
mm = ext[(ext.dataset == "sinhala_mmlu") & (ext.model != "LaMini-GPT-1.5B")].copy()
chance = rob["flattening_models"]["chance"]
lev = rob["flattening_models"]["levels"]
comp = set(json.loads((OUT / "extrinsic_numbers.json").read_text())["competent_models"]["sinhala_mmlu"])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.4, 2.3), gridspec_kw={"wspace": 0.42,
                                                                        "width_ratios": [1, 1.15]})
lo, hi = 19.5, 46
ax1.plot([lo, hi], [lo, hi], color="0.55", lw=0.7, ls="--", zorder=1)
ax1.text(38.0, 39.6, "no change", fontsize=6.5, color="0.35", rotation=45, ha="center")
ax1.axhline(chance, color="0.7", lw=0.6, ls=":")
ax1.axvline(chance, color="0.7", lw=0.6, ls=":")
ax1.text(chance - 0.4, 37.0, f"chance ({chance:.1f}%)", fontsize=6.5, color="0.4", rotation=90,
         ha="right", va="center")
xs = np.linspace(20.5, 45.5, 10)
ax1.plot(xs, lev["intercept"] + lev["slope"] * xs, color="#1b6ca8", lw=1.1, zorder=2)
ax1.text(45.3, 20.3, f"fitted line\nslope {lev['slope']:.2f}", fontsize=6.5, color="#1b6ca8",
         ha="right")
for r in mm.itertuples():
    c = "#1b6ca8" if r.model in comp else "white"
    ax1.scatter(r.u_acc, r.r_acc, s=22, c=c, edgecolor="#1b6ca8", lw=0.8, zorder=3)
labels = {"Qwen3.5-9B": (42.5, 32.0), "Qwen3.5-4B": (40.0, 23.6),
          "Llama-3.1-8B-Instruct": (34.0, 34.0), "Phi-4-14B": (26.0, 32.5),
          "Qwen2-7B-Instruct": (33.3, 21.2), "Hormoz-8B": (26.2, 20.4)}
for name, (tx, ty) in labels.items():
    r = mm[mm.model == name].iloc[0]
    ax1.annotate(name, (r.u_acc, r.r_acc), xytext=(tx, ty), fontsize=6.3, ha="center",
                 va="center", arrowprops=dict(arrowstyle="-", lw=0.4, color="0.5",
                                              shrinkA=1, shrinkB=2.5))
ax1.set_xlim(lo, hi)
ax1.set_ylim(lo, hi)
ax1.set_aspect("equal")
ax1.set_xlabel("Sinhala-script accuracy (%)")
ax1.set_ylabel("Romanized accuracy (%)")
ax1.set_title("(a) SinhalaMMLU, 10 models", loc="left")
hs = [plt.Line2D([], [], marker="o", ls="", ms=4.5, mfc="#1b6ca8", mec="#1b6ca8",
                 label="passes screen"),
      plt.Line2D([], [], marker="o", ls="", ms=4.5, mfc="white", mec="#1b6ca8",
                 label="near chance")]
ax1.legend(handles=hs, loc="upper left", frameon=False, handletextpad=0.2, borderaxespad=0.1)

six = ["Hormoz-8B", "Qwen2-7B-Instruct", "Phi-4-14B", "Qwen3.5-4B", "Llama-3.1-8B-Instruct",
       "Qwen3.5-9B"]
sd = sold.set_index("model").loc[six]
y = np.arange(len(six))
ax2.hlines(y, sd.r_mcc, sd.u_mcc, color="0.75", lw=1.6, zorder=1)
ax2.scatter(sd.u_mcc, y, s=26, c="#1b6ca8", zorder=3, label="Sinhala script")
ax2.scatter(sd.r_mcc, y, s=26, c="#e76f51", zorder=3, label="Romanized")
for yi, r in zip(y, sd.itertuples()):
    ax2.text(0.335, yi, f"{r.mcc_retained_pct:.0f}% kept", va="center", fontsize=6.5,
             color="0.3")
ax2.set_yticks(y)
ax2.set_yticklabels(six, fontsize=6.8)
ax2.set_xlim(0, 0.38)
ax2.set_xticks([0, 0.1, 0.2, 0.3])
ax2.set_xlabel("Matthews correlation (MCC)")
ax2.set_title("(b) SOLD, six models with a Sinhala-script signal", loc="left")
ax2.legend(loc="lower right", frameon=False, handletextpad=0.1, borderaxespad=0.1,
           bbox_to_anchor=(0.86, -0.02))
fig.savefig(FIG / "fig2_downstream.pdf")
plt.close(fig)
print("figures written to", FIG)
