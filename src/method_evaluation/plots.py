"""Publication-quality plots for the transliteration-method comparison.

Reads results/method_evaluation/{metrics.json, significance.json, per_item/*}
and writes PNGs to results/method_evaluation/plots/.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results" / "method_evaluation"
PLOTS_DIR = RESULTS_DIR / "plots"

METHOD_LABELS = {
    "phonetic": "Phonetic",
    "aksharamukha": "Aksharamukha",
    "uroman": "uroman",
    "nisansa_sirs_method": "Nisansa",
    "nisansa_w": "Nisansa (v→w)",
}
CORPUS_LABELS = {
    "social_media": "Social media\n(authentic sentences)",
    "swa_bhasha_words": "Swa-Bhasha\n(multi-ref words)",
    "augmented_sentences": "Augmented\n(sentences)",
    "augmented_sentences_sample": "Augmented\n(300k sample)",
    "swa_bhasha_words_nisansacov": "Swa-Bhasha words\n(25k Nisansa block)",
}
PALETTE = {
    "phonetic": "#2E86AB",
    "aksharamukha": "#E4572E",
    "uroman": "#8B5FBF",
    "nisansa_sirs_method": "#17A398",
    "nisansa_w": "#0E6E66",       # same family as Nisansa: it is a variant of it
}

sns.set_theme(style="whitegrid", context="talk")
plt.rcParams.update({
    "figure.dpi": 120,
    "savefig.dpi": 220,
    "font.family": "DejaVu Sans",
    "axes.titleweight": "bold",
    "axes.edgecolor": "#333333",
})


def _load():
    metrics = json.loads((RESULTS_DIR / "metrics.json").read_text(encoding="utf-8"))
    sig_path = RESULTS_DIR / "significance.json"
    sig = json.loads(sig_path.read_text(encoding="utf-8")) if sig_path.exists() else {}
    return metrics, sig


def _by_corpus(metrics):
    corpora, methods = [], []
    for m in metrics:
        if m["corpus"] not in corpora:
            corpora.append(m["corpus"])
        if m["method"] not in methods:
            methods.append(m["method"])
    grid = {(m["corpus"], m["method"]): m for m in metrics}
    return corpora, methods, grid


def _annotate_bars(ax, fmt="{:.3f}"):
    for p in ax.patches:
        h = p.get_height()
        if h and not np.isnan(h):
            ax.annotate(fmt.format(h), (p.get_x() + p.get_width() / 2, h),
                        ha="center", va="bottom", fontsize=10, xytext=(0, 2),
                        textcoords="offset points")


def plot_cer(metrics, sig):
    corpora, methods, grid = _by_corpus(metrics)
    x = np.arange(len(corpora))
    w = 0.8 / max(len(methods), 1)
    fig, ax = plt.subplots(figsize=(1.9 * len(corpora) + 5, 6.5))
    for i, method in enumerate(methods):
        vals, errs = [], [[], []]
        for corpus in corpora:
            m = grid.get((corpus, method))
            vals.append(m["cer_mean"] if m else np.nan)
            ci = sig.get(corpus, {}).get("methods", {}).get(method, {}).get("cer_ci95")
            if m and ci:
                errs[0].append(m["cer_mean"] - ci[0])
                errs[1].append(ci[1] - m["cer_mean"])
            else:
                errs[0].append(0); errs[1].append(0)
        ax.bar(x + i * w - 0.4 + w / 2, vals, w, yerr=errs, capsize=4,
               label=METHOD_LABELS.get(method, method), color=PALETTE.get(method), edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels([CORPUS_LABELS.get(c, c) for c in corpora])
    ax.set_ylabel("Character Error Rate  (lower = better)")
    ax.set_title("Strict CER vs. human romanization  (95% CI)")
    ax.legend(title="Method", frameon=True)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "cer_by_method.png")
    plt.close(fig)


def plot_quality(metrics):
    corpora, methods, grid = _by_corpus(metrics)
    fig, axes = plt.subplots(1, 3, figsize=(20, 6.5))
    for ax, (key, title, hi) in zip(axes, [
        ("chrf", "chrF  (higher = better)", True),
        ("chrf2", "chrF++  (higher = better)", True),
        ("bleu", "BLEU  (higher = better)", True),
    ]):
        x = np.arange(len(corpora))
        w = 0.8 / max(len(methods), 1)
        for i, method in enumerate(methods):
            vals = [grid.get((c, method), {}).get(key, np.nan) for c in corpora]
            ax.bar(x + i * w - 0.4 + w / 2, vals, w, label=METHOD_LABELS.get(method, method),
                   color=PALETTE.get(method), edgecolor="white")
        ax.set_xticks(x)
        ax.set_xticklabels([CORPUS_LABELS.get(c, c) for c in corpora], fontsize=11)
        ax.set_title(title)
    axes[0].set_ylabel("score")
    axes[-1].legend(title="Method", frameon=True, fontsize=11)
    fig.suptitle("Transliteration quality metrics by method", fontweight="bold")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "quality_metrics.png")
    plt.close(fig)


def plot_strict_vs_relaxed(metrics):
    """Isolates spelling-style gap: strict CER vs canonicalized (relaxed) CER."""
    corpora, methods, grid = _by_corpus(metrics)
    fig, axes = plt.subplots(1, len(corpora), figsize=(6.2 * len(corpora), 6.2), squeeze=False)
    for ax, corpus in zip(axes[0], corpora):
        labels = [METHOD_LABELS.get(m, m) for m in methods]
        strict = [grid.get((corpus, m), {}).get("cer_mean", np.nan) for m in methods]
        relaxed = [grid.get((corpus, m), {}).get("cer_relaxed_mean", np.nan) for m in methods]
        x = np.arange(len(methods))
        ax.bar(x - 0.2, strict, 0.4, label="Strict", color="#E4572E", edgecolor="white")
        ax.bar(x + 0.2, relaxed, 0.4, label="Relaxed (canonical)", color="#2E86AB", edgecolor="white")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=11)
        ax.set_title(CORPUS_LABELS.get(corpus, corpus).replace("\n", " "), fontsize=13)
        ax.set_ylabel("CER")
    axes[0][-1].legend(frameon=True)
    fig.suptitle("Genuine phonemic error vs. spelling-style difference", fontweight="bold")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "strict_vs_relaxed_cer.png")
    plt.close(fig)


def plot_exact_match(metrics):
    corpora, methods, grid = _by_corpus(metrics)
    fig, axes = plt.subplots(1, len(corpora), figsize=(6.2 * len(corpora), 6.2), squeeze=False)
    for ax, corpus in zip(axes[0], corpora):
        labels = [METHOD_LABELS.get(m, m) for m in methods]
        ex = [grid.get((corpus, m), {}).get("exact_pct", np.nan) for m in methods]
        exr = [grid.get((corpus, m), {}).get("exact_relaxed_pct", np.nan) for m in methods]
        x = np.arange(len(methods))
        ax.bar(x - 0.2, ex, 0.4, label="Exact", color="#8B5FBF", edgecolor="white")
        ax.bar(x + 0.2, exr, 0.4, label="Exact (canonical)", color="#17A398", edgecolor="white")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=11)
        ax.set_title(CORPUS_LABELS.get(corpus, corpus).replace("\n", " "), fontsize=13)
        ax.set_ylabel("% items matching a human variant")
    axes[0][-1].legend(frameon=True)
    fig.suptitle("Exact-match rate against accepted human romanizations", fontweight="bold")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "exact_match.png")
    plt.close(fig)


def plot_cer_distribution(metrics):
    corpora, methods, _ = _by_corpus(metrics)
    per_item = RESULTS_DIR / "per_item"
    for corpus in corpora:
        data, labels, colors = [], [], []
        for method in methods:
            f = per_item / f"{corpus}__{method}.json"
            if not f.exists():
                continue
            arr = np.array(json.loads(f.read_text())["cer"])
            if arr.size > 30000:  # subsample for a responsive KDE
                arr = np.random.default_rng(42).choice(arr, 30000, replace=False)
            arr = arr[arr <= np.percentile(arr, 99)]  # clip extreme tail for readability
            data.append(arr)
            labels.append(METHOD_LABELS.get(method, method))
            colors.append(PALETTE.get(method))
        if not data:
            continue
        fig, ax = plt.subplots(figsize=(2.2 * len(data) + 4, 6.5))
        parts = ax.violinplot(data, showmedians=True, showextrema=False)
        for body, c in zip(parts["bodies"], colors):
            body.set_facecolor(c); body.set_alpha(0.65); body.set_edgecolor("#333")
        parts["cmedians"].set_color("#111")
        ax.set_xticks(np.arange(1, len(labels) + 1))
        ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=11)
        ax.set_ylabel("per-item CER")
        ax.set_title(f"Per-item CER distribution — {CORPUS_LABELS.get(corpus, corpus)}".replace("\n", " "))
        fig.tight_layout()
        fig.savefig(PLOTS_DIR / f"cer_distribution_{corpus}.png")
        plt.close(fig)


def plot_heatmap(metrics):
    corpora, methods, grid = _by_corpus(metrics)
    metric_keys = [("cer_mean", "CER", True), ("cer_relaxed_mean", "CER (relaxed)", True),
                   ("chrf", "chrF", False), ("bleu", "BLEU", False), ("exact_pct", "Exact%", False)]
    for corpus in corpora:
        rows = [m for m in methods if (corpus, m) in grid]
        if not rows:
            continue
        raw = np.array([[grid[(corpus, m)][k] for k, _, _ in metric_keys] for m in rows], dtype=float)
        norm = np.zeros_like(raw)
        for j, (_, _, lower_better) in enumerate(metric_keys):
            col = raw[:, j]
            span = col.max() - col.min()
            norm[:, j] = 0.5 if span == 0 else (col.max() - col) / span if lower_better else (col - col.min()) / span
        fig, ax = plt.subplots(figsize=(1.4 * len(metric_keys) + 3, 1.1 * len(rows) + 3))
        sns.heatmap(norm, annot=raw, fmt=".2f", cmap="YlGnBu",
                    xticklabels=[t for _, t, _ in metric_keys],
                    yticklabels=[METHOD_LABELS.get(m, m) for m in rows],
                    cbar_kws={"label": "normalized (1 = best)"}, ax=ax, linewidths=0.5, linecolor="white")
        ax.set_title(f"Method x metric — {CORPUS_LABELS.get(corpus, corpus)}".replace("\n", " "))
        fig.tight_layout()
        fig.savefig(PLOTS_DIR / f"heatmap_{corpus}.png")
        plt.close(fig)


def plot_case_artifact(metrics):
    """Case-sensitive scoring credits the web method for a UI side-effect."""
    corpora, methods, grid = _by_corpus(metrics)
    corpora = [c for c in corpora
               if any(grid.get((c, m), {}).get("cer_mean_cased") is not None for m in methods)]
    if not corpora:
        return
    fig, axes = plt.subplots(1, len(corpora), figsize=(6.4 * len(corpora), 6.4), squeeze=False)
    for ax, corpus in zip(axes[0], corpora):
        rows = [m for m in methods if (corpus, m) in grid]
        x = np.arange(len(rows))
        folded = [grid[(corpus, m)]["cer_mean"] for m in rows]
        cased = [grid[(corpus, m)].get("cer_mean_cased", np.nan) for m in rows]
        ax.bar(x - 0.2, folded, 0.4, label="Case-folded (primary)", color="#2E86AB", edgecolor="white")
        ax.bar(x + 0.2, cased, 0.4, label="Case-sensitive", color="#C1444F", edgecolor="white")
        best_f = int(np.nanargmin(folded))
        best_c = int(np.nanargmin(cased))
        ax.annotate("best", (x[best_f] - 0.2, folded[best_f]), ha="center", va="bottom",
                    fontsize=10, xytext=(0, 3), textcoords="offset points", color="#2E86AB")
        ax.annotate("best", (x[best_c] + 0.2, cased[best_c]), ha="center", va="bottom",
                    fontsize=10, xytext=(0, 3), textcoords="offset points", color="#C1444F")
        ax.set_xticks(x)
        ax.set_xticklabels([METHOD_LABELS.get(m, m) for m in rows], rotation=20, ha="right", fontsize=11)
        ax.set_ylabel("CER")
        ax.set_title(CORPUS_LABELS.get(corpus, corpus).replace("\n", " "), fontsize=13)
    axes[0][-1].legend(frameon=True, fontsize=11)
    fig.suptitle("Letter case is an interface artifact: scoring it can flip the ranking",
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "case_sensitivity_artifact.png")
    plt.close(fig)


def main():
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    metrics, sig = _load()
    if not metrics:
        print("No metrics found. Run run_evaluation.py first.")
        return
    plot_cer(metrics, sig)
    plot_case_artifact(metrics)
    plot_quality(metrics)
    plot_strict_vs_relaxed(metrics)
    plot_exact_match(metrics)
    plot_cer_distribution(metrics)
    plot_heatmap(metrics)
    print(f"Wrote plots to {PLOTS_DIR}")


if __name__ == "__main__":
    main()
