
# ============================================================
# Sinhala Script Robustness — Full Visualization Script
# ============================================================
# Run this script to generate all visualizations and save them
# in results/visualization/figures/
# ============================================================

import os, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from sklearn.metrics import (confusion_matrix, classification_report,
                             roc_curve, auc, precision_recall_curve,
                             average_precision_score)
from sklearn.preprocessing import LabelBinarizer

warnings.filterwarnings('ignore')

# ─── PATHS ───────────────────────────────────────────────────
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE      = os.path.normpath(os.path.join(_THIS_DIR, "..", "extrinsic_evaluation"))
OUT_DIR   = os.path.join(_THIS_DIR, "figures")
os.makedirs(OUT_DIR, exist_ok=True)

# ─── STYLE ───────────────────────────────────────────────────
PALETTE_MODELS = [
    "#6C63FF", "#FF6B6B", "#48CAE4", "#F4A261", "#2EC4B6",
    "#E9C46A", "#264653", "#A8DADC", "#E63946", "#43AA8B",
]
UNICODE_COLOR   = "#4361EE"
ROMAN_COLOR     = "#F72585"
GAP_COLOR       = "#4CC9F0"

plt.rcParams.update({
    "font.family":  "DejaVu Sans",
    "font.size":    12,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "axes.facecolor":   "#F8F9FA",
    "grid.color":       "white",
    "grid.linewidth":   1.2,
})

# ─── MODEL REGISTRY ──────────────────────────────────────────
MODELS = {
    "TinyLlama-1.1B":    "TinyLlama-1.1B-Chat-v1.0",
    "LaMini-GPT-1.5B":   "LaMini-GPT-1.5B",
    "SmolLM3-3B":        "SmolLM3-3B",
    "StableLM-3B":       "stablelm-zephyr-3b",
    "Qwen2-7B":          "Qwen2-7B-Instruct",
    "Zephyr-7B":         "zephyr-7b-beta",
    "Hormoz-8B":         "Hormoz-8B",
    "Llama-3.1-8B":      "Llama-3.1-8B-Instruct",
    "Qwen3.5-4B":        "Qwen-3.5-4B",
    "Qwen3.5-9B":        "Qwen-3.5-9B",
}

MODEL_NAMES = list(MODELS.keys())
COLORS = {m: PALETTE_MODELS[i] for i, m in enumerate(MODEL_NAMES)}

# ─── LOAD SUMMARY DATA ───────────────────────────────────────
def load_summary(model_name, folder):
    files = [f for f in os.listdir(os.path.join(BASE, folder))
             if "summary" in f and f.endswith(".csv")]
    if not files:
        return None
    return pd.read_csv(os.path.join(BASE, folder, files[0]))

def load_task_csv(model_name, folder, task_keyword):
    files = [f for f in os.listdir(os.path.join(BASE, folder))
             if task_keyword in f and "summary" not in f and f.endswith(".csv")]
    if not files:
        return None
    return pd.read_csv(os.path.join(BASE, folder, files[0]))

# Build master summary dataframe
records = []
for m_name, folder in MODELS.items():
    df = load_summary(m_name, folder)
    if df is not None:
        for _, row in df.iterrows():
            if pd.notna(row.get("Task")):
                records.append({
                    "Model":            m_name,
                    "Task":             row["Task"],
                    "N":                row["N"],
                    "Unicode_Acc":      row["Unicode Acc (%)"],
                    "Romanized_Acc":    row["Romanized Acc (%)"],
                    "Gap":              row["Gap (pp)"],
                    "Unicode_Invalid":  row["Unicode Invalid (%)"],
                    "Romanized_Invalid":row["Romanized Invalid (%)"],
                })

summary_df = pd.DataFrame(records)
TASKS = summary_df["Task"].unique().tolist()

print(f"[OK] Loaded summary data: {len(summary_df)} rows, {len(TASKS)} tasks, {len(MODEL_NAMES)} models")
print(f"   Tasks: {TASKS}")
print(f"   Models: {MODEL_NAMES}")

# ═══════════════════════════════════════════════════════════════
# FIGURE 1 — Grouped Bar Chart: Unicode vs Romanized Accuracy
# ═══════════════════════════════════════════════════════════════
def fig1_grouped_bar():
    fig, axes = plt.subplots(1, 3, figsize=(20, 7), sharey=False)
    fig.suptitle(
        "Unicode vs Romanized Script Accuracy per Model\n"
        "(Extrinsic Evaluation — All Tasks)",
        fontsize=16, fontweight="bold", y=1.02
    )

    for ax_idx, task in enumerate(TASKS):
        ax   = axes[ax_idx]
        task_df = summary_df[summary_df["Task"] == task].copy()
        task_df = task_df.sort_values("Unicode_Acc", ascending=False)

        x     = np.arange(len(task_df))
        width = 0.35

        bars1 = ax.bar(x - width/2, task_df["Unicode_Acc"],   width, color=UNICODE_COLOR,
                       label="Unicode", alpha=0.87, edgecolor="white", linewidth=0.8)
        bars2 = ax.bar(x + width/2, task_df["Romanized_Acc"], width, color=ROMAN_COLOR,
                       label="Romanized", alpha=0.87, edgecolor="white", linewidth=0.8)

        # Value annotations
        for bar in bars1:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.4, f"{h:.1f}",
                    ha="center", va="bottom", fontsize=7.5, fontweight="bold", color=UNICODE_COLOR)
        for bar in bars2:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.4, f"{h:.1f}",
                    ha="center", va="bottom", fontsize=7.5, fontweight="bold", color=ROMAN_COLOR)

        ax.set_xticks(x)
        ax.set_xticklabels(task_df["Model"], rotation=42, ha="right", fontsize=9)
        ax.set_title(task, fontsize=13, pad=8)
        ax.set_ylabel("Accuracy (%)", fontsize=11)
        ax.set_ylim(0, max(task_df["Unicode_Acc"].max(), task_df["Romanized_Acc"].max()) * 1.18)
        ax.yaxis.grid(True, linestyle="--", alpha=0.6)
        ax.set_axisbelow(True)
        ax.legend(fontsize=10)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig01_grouped_bar_accuracy.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved: {path}")
    return path

# ═══════════════════════════════════════════════════════════════
# FIGURE 2 — Performance Gap Heatmap (Unicode − Romanized)
# ═══════════════════════════════════════════════════════════════
def fig2_gap_heatmap():
    pivot = summary_df.pivot(index="Model", columns="Task", values="Gap")
    pivot = pivot.reindex(MODEL_NAMES)

    fig, ax = plt.subplots(figsize=(11, 7))
    fig.suptitle(
        "Performance Gap: Unicode − Romanized (pp)\n"
        "Positive = Unicode better  |  Negative = Romanized better",
        fontsize=14, fontweight="bold"
    )

    sns.heatmap(
        pivot, annot=True, fmt=".2f", cmap="RdYlGn",
        center=0, linewidths=0.8, linecolor="white",
        ax=ax, cbar_kws={"label": "Gap (pp)", "shrink": 0.8},
        annot_kws={"size": 11, "weight": "bold"},
        vmin=-20, vmax=20
    )
    ax.set_xlabel("Task", fontsize=12)
    ax.set_ylabel("Model", fontsize=12)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=15, ha="right")
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig02_gap_heatmap.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved: {path}")
    return path

# ═══════════════════════════════════════════════════════════════
# FIGURE 3 — Invalid Response Rate Heatmap
# ═══════════════════════════════════════════════════════════════
def fig3_invalid_heatmap():
    rows = []
    for _, r in summary_df.iterrows():
        rows.append({"Model": r["Model"], "Script": "Unicode",   "Task": r["Task"], "Invalid": r["Unicode_Invalid"]})
        rows.append({"Model": r["Model"], "Script": "Romanized", "Task": r["Task"], "Invalid": r["Romanized_Invalid"]})
    inv_df = pd.DataFrame(rows)

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    fig.suptitle("Invalid Response Rate (%) by Model & Task", fontsize=15, fontweight="bold")

    for ax, script in zip(axes, ["Unicode", "Romanized"]):
        sub = inv_df[inv_df["Script"] == script]
        piv = sub.pivot(index="Model", columns="Task", values="Invalid").reindex(MODEL_NAMES)
        sns.heatmap(piv, annot=True, fmt=".2f", cmap="YlOrRd",
                    linewidths=0.8, linecolor="white", ax=ax,
                    cbar_kws={"label": "Invalid (%)", "shrink": 0.85},
                    annot_kws={"size": 10, "weight": "bold"})
        ax.set_title(f"{script} Script", fontsize=13)
        ax.set_xlabel("Task", fontsize=11)
        ax.set_ylabel("Model" if script == "Unicode" else "", fontsize=11)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=15, ha="right")

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig03_invalid_rate_heatmap.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved: {path}")
    return path

# ═══════════════════════════════════════════════════════════════
# FIGURE 4 — SOLD Task: ROC Curves (Unicode & Romanized)
# ═══════════════════════════════════════════════════════════════
def fig4_roc_curves():
    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    fig.suptitle(
        "ROC Curves — SOLD Task (Sinhala Offensive Language Detection)\n"
        "Binary Classification: OFF vs NOT",
        fontsize=15, fontweight="bold"
    )

    for ax, script_col, title_suffix in zip(
        axes,
        [("unicode_pred", "unicode_correct"), ("romanized_pred", "romanized_correct")],
        ["Unicode Script", "Romanized Script"]
    ):
        pred_col, correct_col = script_col
        ax.set_title(title_suffix, fontsize=13)

        lb = LabelBinarizer()
        lb.fit(["NOT", "OFF"])

        for i, (m_name, folder) in enumerate(MODELS.items()):
            df = load_task_csv(m_name, folder, "sold")
            if df is None or pred_col not in df.columns:
                continue

            # Map predictions to numeric
            y_true  = (df["gold_label"] == "OFF").astype(int)
            y_score = (df[pred_col] == "OFF").astype(int).astype(float)

            # Add tiny jitter for models that predict all-one-class
            unique = np.unique(y_score)
            if len(unique) < 2:
                continue

            fpr, tpr, _ = roc_curve(y_true, y_score)
            roc_auc     = auc(fpr, tpr)

            ax.plot(fpr, tpr,
                    color=COLORS[m_name], linewidth=2.2, alpha=0.88,
                    label=f"{m_name} (AUC={roc_auc:.3f})")

        ax.plot([0, 1], [0, 1], "k--", linewidth=1.2, label="Random (AUC=0.500)")
        ax.fill_between([0, 1], [0, 1], alpha=0.04, color="grey")
        ax.set_xlabel("False Positive Rate", fontsize=11)
        ax.set_ylabel("True Positive Rate", fontsize=11)
        ax.legend(fontsize=8.5, loc="lower right", framealpha=0.9)
        ax.set_xlim([-0.02, 1.02])
        ax.set_ylim([-0.02, 1.05])
        ax.yaxis.grid(True, linestyle="--", alpha=0.5)
        ax.xaxis.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig04_roc_curves_sold.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved: {path}")
    return path

# ═══════════════════════════════════════════════════════════════
# FIGURE 5 — Precision-Recall Curves (SOLD)
# ═══════════════════════════════════════════════════════════════
def fig5_precision_recall():
    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    fig.suptitle(
        "Precision-Recall Curves — SOLD Task\n"
        "Binary Classification: OFF (Offensive) class",
        fontsize=15, fontweight="bold"
    )

    for ax, pred_col, title_suffix in zip(
        axes,
        ["unicode_pred", "romanized_pred"],
        ["Unicode Script", "Romanized Script"]
    ):
        ax.set_title(title_suffix, fontsize=13)

        for i, (m_name, folder) in enumerate(MODELS.items()):
            df = load_task_csv(m_name, folder, "sold")
            if df is None or pred_col not in df.columns:
                continue

            y_true  = (df["gold_label"] == "OFF").astype(int)
            y_score = (df[pred_col] == "OFF").astype(int).astype(float)

            unique = np.unique(y_score)
            if len(unique) < 2:
                continue

            prec, rec, _ = precision_recall_curve(y_true, y_score)
            ap = average_precision_score(y_true, y_score)

            ax.plot(rec, prec,
                    color=COLORS[m_name], linewidth=2.2, alpha=0.88,
                    label=f"{m_name} (AP={ap:.3f})")

        # Random baseline
        n_pos = summary_df[(summary_df["Task"] == "SOLD")]["N"].iloc[0]
        baseline = 0.5  # approximate for balanced SOLD
        ax.axhline(baseline, color="grey", linestyle="--", linewidth=1.2, label="Random Baseline")

        ax.set_xlabel("Recall", fontsize=11)
        ax.set_ylabel("Precision", fontsize=11)
        ax.legend(fontsize=8.5, loc="upper right", framealpha=0.9)
        ax.set_xlim([-0.02, 1.02])
        ax.set_ylim([0, 1.05])
        ax.yaxis.grid(True, linestyle="--", alpha=0.5)
        ax.xaxis.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig05_precision_recall_sold.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved: {path}")
    return path

# ═══════════════════════════════════════════════════════════════
# FIGURE 6 — F1 Score Bar Chart (SOLD — per model, per script)
# ═══════════════════════════════════════════════════════════════
def fig6_f1_scores():
    from sklearn.metrics import f1_score, precision_score, recall_score

    valid_labels = {"NOT", "OFF"}

    f1_records = []
    for m_name, folder in MODELS.items():
        df = load_task_csv(m_name, folder, "sold")
        if df is None:
            continue
        for script, pred_col in [("Unicode", "unicode_pred"), ("Romanized", "romanized_pred")]:
            if pred_col not in df.columns:
                continue
            # Map any out-of-vocabulary prediction to 'NOT' (invalid response treated as NOT)
            y_true = df["gold_label"].values
            y_pred_raw = df[pred_col].values
            y_pred = np.where(np.isin(y_pred_raw, list(valid_labels)), y_pred_raw, "NOT")
            f1     = f1_score(y_true, y_pred, pos_label="OFF", average="binary", zero_division=0)
            prec_v = precision_score(y_true, y_pred, pos_label="OFF", average="binary", zero_division=0)
            rec_v  = recall_score(y_true, y_pred, pos_label="OFF", average="binary", zero_division=0)
            f1_records.append({
                "Model": m_name, "Script": script,
                "F1": f1, "Precision": prec_v, "Recall": rec_v
            })

    f1_df = pd.DataFrame(f1_records)

    fig, axes = plt.subplots(1, 3, figsize=(21, 7))
    fig.suptitle(
        "SOLD Task — Precision, Recall & F1-Score per Model\n"
        "(Offensive Language Detection, class=OFF)",
        fontsize=15, fontweight="bold"
    )

    for ax, metric in zip(axes, ["Precision", "Recall", "F1"]):
        ax.set_title(metric, fontsize=14, pad=8)
        sub = f1_df.copy()
        x   = np.arange(len(MODEL_NAMES))
        w   = 0.35

        uni_vals = [sub[(sub["Model"] == m) & (sub["Script"] == "Unicode")][metric].values
                    for m in MODEL_NAMES]
        rom_vals = [sub[(sub["Model"] == m) & (sub["Script"] == "Romanized")][metric].values
                    for m in MODEL_NAMES]
        uni_vals = [v[0] if len(v) else 0 for v in uni_vals]
        rom_vals = [v[0] if len(v) else 0 for v in rom_vals]

        bars1 = ax.bar(x - w/2, uni_vals, w, color=UNICODE_COLOR, alpha=0.87, label="Unicode",
                       edgecolor="white")
        bars2 = ax.bar(x + w/2, rom_vals, w, color=ROMAN_COLOR, alpha=0.87, label="Romanized",
                       edgecolor="white")

        for bar, val in zip(bars1, uni_vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f"{val:.2f}", ha="center", va="bottom", fontsize=7.5,
                    fontweight="bold", color=UNICODE_COLOR)
        for bar, val in zip(bars2, rom_vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f"{val:.2f}", ha="center", va="bottom", fontsize=7.5,
                    fontweight="bold", color=ROMAN_COLOR)

        ax.set_xticks(x)
        ax.set_xticklabels(MODEL_NAMES, rotation=42, ha="right", fontsize=9)
        ax.set_ylim(0, 1.18)
        ax.set_ylabel(metric, fontsize=11)
        ax.yaxis.grid(True, linestyle="--", alpha=0.6)
        ax.set_axisbelow(True)
        ax.legend(fontsize=10)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig06_f1_precision_recall.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved: {path}")
    return path

# ═══════════════════════════════════════════════════════════════
# FIGURE 7 — Confusion Matrices for SOLD (best models)
# ═══════════════════════════════════════════════════════════════
def fig7_confusion_matrices():
    # Pick top 4 models by Unicode F1
    from sklearn.metrics import f1_score

    model_f1 = []
    valid_labels = {"NOT", "OFF"}
    for m_name, folder in MODELS.items():
        df = load_task_csv(m_name, folder, "sold")
        if df is None:
            continue
        y_true = df["gold_label"].values
        y_pred_raw = df["unicode_pred"].values
        y_pred = np.where(np.isin(y_pred_raw, list(valid_labels)), y_pred_raw, "NOT")
        f1u = f1_score(y_true, y_pred, pos_label="OFF", average="binary", zero_division=0)
        model_f1.append((m_name, f1u, folder))
    model_f1.sort(key=lambda x: -x[1])
    top_models = model_f1[:5]

    fig, axes = plt.subplots(2, 5, figsize=(24, 10))
    fig.suptitle(
        "SOLD Task — Confusion Matrices (All Models)\n"
        "Row 1: Unicode Script  |  Row 2: Romanized Script",
        fontsize=15, fontweight="bold"
    )

    all_models = [(m, f, fol) for m, f, fol in model_f1]
    if len(all_models) < 5:
        all_models = all_models + [None] * (5 - len(all_models))

    for col_idx in range(5):
        entry = all_models[col_idx] if col_idx < len(all_models) else None
        for row_idx, (script, pred_col) in enumerate([("Unicode", "unicode_pred"),
                                                       ("Romanized", "romanized_pred")]):
            ax = axes[row_idx][col_idx]
            if entry is None:
                ax.axis("off")
                continue
            m_name, f1u, folder = entry
            df = load_task_csv(m_name, folder, "sold")
            if df is None:
                ax.axis("off")
                continue

            y_true = df["gold_label"]
            y_pred = df[pred_col]
            labels = ["NOT", "OFF"]
            cm     = confusion_matrix(y_true, y_pred, labels=labels)

            sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                        xticklabels=labels, yticklabels=labels,
                        ax=ax, cbar=False, linewidths=0.5, linecolor="white",
                        annot_kws={"size": 12, "weight": "bold"})
            ax.set_title(
                f"{m_name}\n({script})",
                fontsize=9.5, fontweight="bold",
                color=UNICODE_COLOR if script == "Unicode" else ROMAN_COLOR
            )
            ax.set_xlabel("Predicted", fontsize=9)
            ax.set_ylabel("True" if col_idx == 0 else "", fontsize=9)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig07_confusion_matrices_sold.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved: {path}")
    return path

# ═══════════════════════════════════════════════════════════════
# FIGURE 8 — Model Ranking Radar / Spider Chart (All Tasks)
# ═══════════════════════════════════════════════════════════════
def fig8_radar_chart():
    # Normalize accuracy scores 0-1 per task across models
    tasks_for_radar = TASKS
    pivot_u = summary_df.pivot(index="Model", columns="Task", values="Unicode_Acc").reindex(MODEL_NAMES)
    pivot_r = summary_df.pivot(index="Model", columns="Task", values="Romanized_Acc").reindex(MODEL_NAMES)

    n_tasks = len(tasks_for_radar)
    angles  = np.linspace(0, 2 * np.pi, n_tasks, endpoint=False).tolist()
    angles += angles[:1]  # close the polygon

    fig, axes = plt.subplots(1, 2, figsize=(18, 8), subplot_kw=dict(polar=True))
    fig.suptitle(
        "Model Performance Radar Chart — Normalized Accuracy\n"
        "Across All Tasks",
        fontsize=15, fontweight="bold"
    )

    for ax, pivot, title in zip(axes, [pivot_u, pivot_r], ["Unicode Script", "Romanized Script"]):
        for i, m_name in enumerate(MODEL_NAMES):
            vals = [pivot.loc[m_name, t] if t in pivot.columns else 0 for t in tasks_for_radar]
            # Normalize per task to 0-1
            max_vals = [pivot[t].max() for t in tasks_for_radar if t in pivot.columns]
            vals_norm = [v / mx if mx > 0 else 0 for v, mx in zip(vals, max_vals)]
            vals_norm += vals_norm[:1]

            ax.plot(angles, vals_norm, color=COLORS[m_name], linewidth=2, alpha=0.85)
            ax.fill(angles, vals_norm, color=COLORS[m_name], alpha=0.08)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(tasks_for_radar, fontsize=11, fontweight="bold")
        ax.set_ylim(0, 1.1)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(["20%", "40%", "60%", "80%", "100%"], fontsize=8)
        ax.set_title(title, fontsize=13, pad=20, fontweight="bold")
        ax.grid(color="white", linewidth=1.2)
        ax.set_facecolor("#F0F4FF")

    # Legend outside
    legend_patches = [mpatches.Patch(color=COLORS[m], label=m) for m in MODEL_NAMES]
    fig.legend(handles=legend_patches, loc="lower center", ncol=5, fontsize=9,
               framealpha=0.9, bbox_to_anchor=(0.5, -0.04))

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig08_radar_chart.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved: {path}")
    return path

# ═══════════════════════════════════════════════════════════════
# FIGURE 9 — Script Robustness Score (Gap Analysis)
# ═══════════════════════════════════════════════════════════════
def fig9_robustness_score():
    """
    Robustness score = average |Gap| across tasks (lower = more robust).
    Also includes a signed average gap.
    """
    rob_records = []
    for m_name in MODEL_NAMES:
        sub = summary_df[summary_df["Model"] == m_name]
        avg_gap   = sub["Gap"].mean()
        avg_abs   = sub["Gap"].abs().mean()
        rob_records.append({
            "Model":          m_name,
            "Avg_Gap":        avg_gap,
            "Avg_AbsGap":     avg_abs,
            "Max_Gap":        sub["Gap"].max(),
        })
    rob_df = pd.DataFrame(rob_records).sort_values("Avg_AbsGap")

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    fig.suptitle(
        "Script Robustness Analysis\n"
        "Lower absolute gap = more robust (Unicode ≈ Romanized)",
        fontsize=15, fontweight="bold"
    )

    # Left: Average signed gap
    ax = axes[0]
    colors = [UNICODE_COLOR if v >= 0 else ROMAN_COLOR for v in rob_df["Avg_Gap"]]
    bars = ax.barh(rob_df["Model"], rob_df["Avg_Gap"], color=colors, alpha=0.87,
                   edgecolor="white")
    ax.axvline(0, color="black", linewidth=1.2, linestyle="-")
    ax.set_xlabel("Average Gap (pp)\nPositive = Unicode better", fontsize=11)
    ax.set_title("Average Signed Gap\n(Unicode − Romanized)", fontsize=12)
    for bar, val in zip(bars, rob_df["Avg_Gap"]):
        ax.text(val + (0.1 if val >= 0 else -0.1), bar.get_y() + bar.get_height()/2,
                f"{val:+.2f}", va="center", ha="left" if val >= 0 else "right",
                fontsize=9, fontweight="bold")
    ax.xaxis.grid(True, linestyle="--", alpha=0.5)

    # Right: Average absolute gap (robustness metric)
    ax2 = axes[1]
    rob_sorted = rob_df.sort_values("Avg_AbsGap")
    bar_colors = [PALETTE_MODELS[i % len(PALETTE_MODELS)]
                  for i in range(len(rob_sorted))]
    bars2 = ax2.barh(rob_sorted["Model"], rob_sorted["Avg_AbsGap"],
                     color=bar_colors, alpha=0.87, edgecolor="white")
    ax2.set_xlabel("Mean |Gap| (pp)\nLower = More Robust", fontsize=11)
    ax2.set_title("Mean Absolute Gap\n(Robustness Score — Lower is Better)", fontsize=12)
    for bar, val in zip(bars2, rob_sorted["Avg_AbsGap"]):
        ax2.text(val + 0.05, bar.get_y() + bar.get_height()/2,
                 f"{val:.2f}", va="center", ha="left", fontsize=9, fontweight="bold")
    ax2.xaxis.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig09_robustness_score.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved: {path}")
    return path

# ═══════════════════════════════════════════════════════════════
# FIGURE 10 — Heatmap: Full Accuracy Table (Unicode + Romanized)
# ═══════════════════════════════════════════════════════════════
def fig10_full_accuracy_heatmap():
    fig, axes = plt.subplots(1, 2, figsize=(14, 8))
    fig.suptitle(
        "Full Accuracy Heatmap — All Models × All Tasks",
        fontsize=15, fontweight="bold"
    )

    for ax, col, title in zip(axes,
                               ["Unicode_Acc", "Romanized_Acc"],
                               ["Unicode Script", "Romanized Script"]):
        piv = summary_df.pivot(index="Model", columns="Task", values=col).reindex(MODEL_NAMES)
        sns.heatmap(piv, annot=True, fmt=".1f", cmap="viridis",
                    linewidths=0.8, linecolor="white", ax=ax,
                    cbar_kws={"label": "Accuracy (%)", "shrink": 0.85},
                    annot_kws={"size": 11, "weight": "bold"},
                    vmin=0, vmax=70)
        ax.set_title(title, fontsize=13, fontweight="bold",
                     color=UNICODE_COLOR if "Unicode" in title else ROMAN_COLOR)
        ax.set_xlabel("Task", fontsize=11)
        ax.set_ylabel("Model", fontsize=11)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=15, ha="right")

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig10_full_accuracy_heatmap.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved: {path}")
    return path

# ═══════════════════════════════════════════════════════════════
# FIGURE 11 — Excel Data: Stacked Overview (from spreadsheet)
# ═══════════════════════════════════════════════════════════════
def fig11_excel_overview():
    """Reads directly from the provided Excel file and visualises all model blocks."""
    # Map row-block order (based on Excel inspection: rows 3-5, 9-11, ... etc.)
    model_labels_ordered = [
        "TinyLlama-1.1B", "LaMini-GPT-1.5B",
        "SmolLM3-3B", "StableLM-3B",
        "Qwen2-7B", "Zephyr-7B",
        "Hormoz-8B", "Llama-3.1-8B",
        "Qwen3.5-4B", "Qwen3.5-9B",
    ]

    tasks_e  = ["Sinhala MMLU", "SOLD", "Global PIQA"]
    n_models = len(MODEL_NAMES)
    n_tasks  = len(tasks_e)

    # We already have summary_df with the same data
    uni_matrix  = np.zeros((n_models, n_tasks))
    rom_matrix  = np.zeros((n_models, n_tasks))

    for i, m in enumerate(MODEL_NAMES):
        for j, t in enumerate(tasks_e):
            row = summary_df[(summary_df["Model"] == m) & (summary_df["Task"] == t)]
            if not row.empty:
                uni_matrix[i, j] = row["Unicode_Acc"].values[0]
                rom_matrix[i, j] = row["Romanized_Acc"].values[0]

    x  = np.arange(n_tasks)
    bw = 0.07
    offsets = np.linspace(-(n_models - 1) * bw / 2, (n_models - 1) * bw / 2, n_models)

    fig, axes = plt.subplots(2, 1, figsize=(16, 14))
    fig.suptitle(
        "Comprehensive Task Accuracy — All Models Side-by-Side",
        fontsize=15, fontweight="bold"
    )

    for ax_idx, (matrix, script) in enumerate([(uni_matrix, "Unicode"), (rom_matrix, "Romanized")]):
        ax = axes[ax_idx]
        for i, m_name in enumerate(MODEL_NAMES):
            bars = ax.bar(x + offsets[i], matrix[i], bw * 0.92,
                          color=COLORS[m_name], alpha=0.87,
                          label=m_name if ax_idx == 0 else None,
                          edgecolor="white")

        ax.set_xticks(x)
        ax.set_xticklabels(tasks_e, fontsize=13, fontweight="bold")
        ax.set_ylabel("Accuracy (%)", fontsize=12)
        ax.set_title(f"{script} Script — Task Accuracy by Model", fontsize=13,
                     color=UNICODE_COLOR if script == "Unicode" else ROMAN_COLOR)
        ax.yaxis.grid(True, linestyle="--", alpha=0.6)
        ax.set_axisbelow(True)
        ax.set_ylim(0, max(matrix.max(), 10) * 1.25)

    # Shared legend
    legend_patches = [mpatches.Patch(color=COLORS[m], label=m) for m in MODEL_NAMES]
    fig.legend(handles=legend_patches, loc="lower center", ncol=5,
               fontsize=10, framealpha=0.9, bbox_to_anchor=(0.5, -0.01))

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig11_comprehensive_task_accuracy.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved: {path}")
    return path

# ═══════════════════════════════════════════════════════════════
# FIGURE 12 — Per-Model SOLD Class Distribution
# ═══════════════════════════════════════════════════════════════
def fig12_class_distribution():
    fig, axes = plt.subplots(2, 5, figsize=(22, 10))
    fig.suptitle(
        "SOLD Task — Prediction Class Distribution per Model\n"
        "Blue = Unicode | Pink = Romanized",
        fontsize=15, fontweight="bold"
    )

    for idx, (m_name, folder) in enumerate(MODELS.items()):
        df = load_task_csv(m_name, folder, "sold")
        row_idx = idx // 5
        col_idx = idx % 5
        ax = axes[row_idx][col_idx]

        if df is None:
            ax.axis("off")
            continue

        # Count predictions
        u_counts = df["unicode_pred"].value_counts()
        r_counts = df["romanized_pred"].value_counts()
        gold_cnt = df["gold_label"].value_counts()

        labels = ["NOT", "OFF"]
        x      = np.arange(len(labels))
        w      = 0.25

        ax.bar(x - w,     [gold_cnt.get(l, 0) for l in labels],     w, color="#2D3561",  label="Gold",      alpha=0.85)
        ax.bar(x,         [u_counts.get(l, 0) for l in labels],      w, color=UNICODE_COLOR, label="Unicode", alpha=0.85)
        ax.bar(x + w,     [r_counts.get(l, 0) for l in labels],      w, color=ROMAN_COLOR,   label="Romanized", alpha=0.85)

        ax.set_title(m_name, fontsize=10, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_ylabel("Count", fontsize=9)
        if idx == 0:
            ax.legend(fontsize=8)
        ax.yaxis.grid(True, linestyle="--", alpha=0.5)
        ax.set_axisbelow(True)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig12_sold_class_distribution.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved: {path}")
    return path

# ═══════════════════════════════════════════════════════════════
# FIGURE 13 — Bubble Chart: Accuracy vs Invalid Rate
# ═══════════════════════════════════════════════════════════════
def fig13_bubble_accuracy_invalid():
    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    fig.suptitle(
        "Accuracy vs Invalid Response Rate — Bubble Chart\n"
        "Bubble size = Dataset size  |  Colour = Model",
        fontsize=15, fontweight="bold"
    )

    for ax, script, acc_col, inv_col in zip(
        axes,
        ["Unicode", "Romanized"],
        ["Unicode_Acc", "Romanized_Acc"],
        ["Unicode_Invalid", "Romanized_Invalid"]
    ):
        for i, m_name in enumerate(MODEL_NAMES):
            sub = summary_df[summary_df["Model"] == m_name]
            for _, row in sub.iterrows():
                size  = (row["N"] / summary_df["N"].max()) * 800 + 50
                ax.scatter(row[inv_col], row[acc_col],
                           s=size, color=COLORS[m_name], alpha=0.72,
                           edgecolors="white", linewidth=1.2)
                ax.annotate(f"{m_name[:5]}\n{row['Task'][:4]}",
                            xy=(row[inv_col], row[acc_col]),
                            fontsize=6.5, ha="center", va="bottom",
                            xytext=(0, 4), textcoords="offset points")

        ax.set_xlabel("Invalid Response Rate (%)", fontsize=11)
        ax.set_ylabel("Accuracy (%)", fontsize=11)
        ax.set_title(f"{script} Script", fontsize=13,
                     color=UNICODE_COLOR if script == "Unicode" else ROMAN_COLOR)
        ax.yaxis.grid(True, linestyle="--", alpha=0.5)
        ax.xaxis.grid(True, linestyle="--", alpha=0.5)

    legend_patches = [mpatches.Patch(color=COLORS[m], label=m) for m in MODEL_NAMES]
    fig.legend(handles=legend_patches, loc="lower center", ncol=5,
               fontsize=9, framealpha=0.9, bbox_to_anchor=(0.5, -0.04))

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig13_bubble_accuracy_invalid.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved: {path}")
    return path

# ═══════════════════════════════════════════════════════════════
# FIGURE 14 — Delta Plot: Romanized − Unicode per Task
# ═══════════════════════════════════════════════════════════════
def fig14_delta_plot():
    fig, axes = plt.subplots(1, 3, figsize=(20, 7))
    fig.suptitle(
        "Script Switch Delta: Romanized − Unicode Accuracy (pp)\n"
        "Negative = Unicode better  |  Positive = Romanized better",
        fontsize=15, fontweight="bold"
    )

    for ax, task in zip(axes, TASKS):
        sub = summary_df[summary_df["Task"] == task].copy()
        sub["Delta"] = sub["Romanized_Acc"] - sub["Unicode_Acc"]
        sub = sub.sort_values("Delta", ascending=False)

        colors = [ROMAN_COLOR if d >= 0 else UNICODE_COLOR for d in sub["Delta"]]
        bars   = ax.barh(sub["Model"], sub["Delta"], color=colors, alpha=0.85, edgecolor="white")

        for bar, val in zip(bars, sub["Delta"]):
            ax.text(val + (0.05 if val >= 0 else -0.05),
                    bar.get_y() + bar.get_height()/2,
                    f"{val:+.2f}", va="center",
                    ha="left" if val >= 0 else "right",
                    fontsize=8.5, fontweight="bold")

        ax.axvline(0, color="black", linewidth=1.2)
        ax.set_title(task, fontsize=13, pad=8)
        ax.set_xlabel("Δ Accuracy (pp)", fontsize=11)
        ax.xaxis.grid(True, linestyle="--", alpha=0.5)

        # Legend
        u_patch = mpatches.Patch(color=UNICODE_COLOR, label="Unicode better")
        r_patch = mpatches.Patch(color=ROMAN_COLOR, label="Romanized better")
        ax.legend(handles=[u_patch, r_patch], fontsize=9)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig14_delta_plot.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved: {path}")
    return path

# ═══════════════════════════════════════════════════════════════
# FIGURE 15 — Summary Dashboard
# ═══════════════════════════════════════════════════════════════
def fig15_dashboard():
    """Mini dashboard with key KPIs."""
    from sklearn.metrics import f1_score

    fig = plt.figure(figsize=(22, 12))
    fig.patch.set_facecolor("#0F0F23")
    fig.suptitle(
        "Sinhala Script Robustness — NLP Evaluation Dashboard",
        fontsize=18, fontweight="bold", color="white", y=0.98
    )

    # ── KPI boxes ──
    best_model_mmlu    = summary_df[summary_df["Task"] == "Sinhala MMLU"].sort_values("Unicode_Acc", ascending=False).iloc[0]
    best_model_sold    = summary_df[summary_df["Task"] == "SOLD"].sort_values("Unicode_Acc", ascending=False).iloc[0]
    most_robust        = summary_df.groupby("Model")["Gap"].apply(lambda x: x.abs().mean()).idxmin()
    avg_gap_all        = summary_df["Gap"].mean()

    kpis = [
        ("Best MMLU (Unicode)",  f"{best_model_mmlu['Model']}\n{best_model_mmlu['Unicode_Acc']:.1f}%", "#6C63FF"),
        ("Best SOLD (Unicode)",  f"{best_model_sold['Model']}\n{best_model_sold['Unicode_Acc']:.1f}%", "#F72585"),
        ("Most Robust Model",    f"{most_robust}", "#48CAE4"),
        ("Avg Gap (all models)", f"{avg_gap_all:+.2f} pp", "#F4A261"),
    ]

    for i, (label, value, color) in enumerate(kpis):
        ax = fig.add_subplot(3, 4, i + 1)
        ax.set_facecolor(color)
        ax.text(0.5, 0.6, value, transform=ax.transAxes,
                fontsize=13, fontweight="bold", ha="center", va="center", color="white")
        ax.text(0.5, 0.15, label, transform=ax.transAxes,
                fontsize=9, ha="center", va="center", color="white", alpha=0.85)
        ax.axis("off")

    # ── Mini bar chart: Unicode acc per model (Sinhala MMLU) ──
    ax5 = fig.add_subplot(3, 2, 3)
    mmlu_df = summary_df[summary_df["Task"] == "Sinhala MMLU"].set_index("Model").reindex(MODEL_NAMES)
    bars = ax5.bar(MODEL_NAMES, mmlu_df["Unicode_Acc"],
                   color=[COLORS[m] for m in MODEL_NAMES], alpha=0.87, edgecolor="white")
    ax5.bar(MODEL_NAMES, mmlu_df["Romanized_Acc"],
            color=[COLORS[m] for m in MODEL_NAMES], alpha=0.4, edgecolor="white",
            hatch="//")
    ax5.set_xticklabels(MODEL_NAMES, rotation=40, ha="right", fontsize=8)
    ax5.set_ylabel("Accuracy (%)")
    ax5.set_title("Sinhala MMLU — Solid=Unicode / Hatched=Romanized", fontsize=10, fontweight="bold")
    ax5.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax5.set_facecolor("#F8F9FA")

    # ── Mini bar chart: SOLD ──
    ax6 = fig.add_subplot(3, 2, 4)
    sold_df = summary_df[summary_df["Task"] == "SOLD"].set_index("Model").reindex(MODEL_NAMES)
    ax6.bar(MODEL_NAMES, sold_df["Unicode_Acc"],
            color=[COLORS[m] for m in MODEL_NAMES], alpha=0.87, edgecolor="white")
    ax6.bar(MODEL_NAMES, sold_df["Romanized_Acc"],
            color=[COLORS[m] for m in MODEL_NAMES], alpha=0.4, edgecolor="white", hatch="//")
    ax6.set_xticklabels(MODEL_NAMES, rotation=40, ha="right", fontsize=8)
    ax6.set_ylabel("Accuracy (%)")
    ax6.set_title("SOLD — Solid=Unicode / Hatched=Romanized", fontsize=10, fontweight="bold")
    ax6.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax6.set_facecolor("#F8F9FA")

    # ── Gap heatmap (mini) ──
    ax7 = fig.add_subplot(3, 1, 3)
    gap_pivot = summary_df.pivot(index="Model", columns="Task", values="Gap").reindex(MODEL_NAMES)
    sns.heatmap(gap_pivot, annot=True, fmt=".1f", cmap="RdYlGn",
                center=0, linewidths=0.8, linecolor="white",
                ax=ax7, cbar_kws={"label": "Gap (pp)", "shrink": 0.7},
                annot_kws={"size": 10, "weight": "bold"},
                vmin=-20, vmax=20)
    ax7.set_title("Performance Gap Heatmap: Unicode − Romanized (pp)", fontsize=12, fontweight="bold")
    ax7.set_xlabel("Task")
    ax7.set_ylabel("Model")
    ax7.set_yticklabels(ax7.get_yticklabels(), rotation=0)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    path = os.path.join(OUT_DIR, "fig15_dashboard.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"[OK] Saved: {path}")
    return path

# ═══════════════════════════════════════════════════════════════
# FIGURE 16 — Global PIQA Accuracy Comparison
# ═══════════════════════════════════════════════════════════════
def fig16_piqa_comparison():
    piqa_df = summary_df[summary_df["Task"] == "Global PIQA"].copy()
    piqa_df = piqa_df.sort_values("Unicode_Acc", ascending=False)

    fig, ax = plt.subplots(figsize=(13, 6))
    fig.suptitle(
        "Global PIQA — Physical Intuition Question Answering\n"
        "Unicode vs Romanized Script Performance",
        fontsize=14, fontweight="bold"
    )

    x = np.arange(len(piqa_df))
    w = 0.38
    b1 = ax.bar(x - w/2, piqa_df["Unicode_Acc"],   w, color=UNICODE_COLOR, alpha=0.87,
                label="Unicode", edgecolor="white")
    b2 = ax.bar(x + w/2, piqa_df["Romanized_Acc"], w, color=ROMAN_COLOR,   alpha=0.87,
                label="Romanized", edgecolor="white")

    for bar in b1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.3, f"{h:.0f}",
                ha="center", va="bottom", fontsize=9, fontweight="bold", color=UNICODE_COLOR)
    for bar in b2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.3, f"{h:.0f}",
                ha="center", va="bottom", fontsize=9, fontweight="bold", color=ROMAN_COLOR)

    # Random baseline for binary PIQA (50%)
    ax.axhline(50, color="grey", linestyle="--", linewidth=1.5, label="Random Baseline (50%)")

    ax.set_xticks(x)
    ax.set_xticklabels(piqa_df["Model"], rotation=35, ha="right", fontsize=10)
    ax.set_ylabel("Accuracy (%)", fontsize=12)
    ax.set_ylim(0, 80)
    ax.legend(fontsize=11)
    ax.yaxis.grid(True, linestyle="--", alpha=0.6)
    ax.set_axisbelow(True)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig16_piqa_comparison.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved: {path}")
    return path

# ═══════════════════════════════════════════════════════════════
# RUN ALL FIGURES
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Sinhala NLP Visualization — Running All Figures")
    print("="*60 + "\n")

    saved = []
    saved.append(fig1_grouped_bar())
    saved.append(fig2_gap_heatmap())
    saved.append(fig3_invalid_heatmap())
    saved.append(fig4_roc_curves())
    saved.append(fig5_precision_recall())
    saved.append(fig6_f1_scores())
    saved.append(fig7_confusion_matrices())
    saved.append(fig8_radar_chart())
    saved.append(fig9_robustness_score())
    saved.append(fig10_full_accuracy_heatmap())
    saved.append(fig11_excel_overview())
    saved.append(fig12_class_distribution())
    saved.append(fig13_bubble_accuracy_invalid())
    saved.append(fig14_delta_plot())
    saved.append(fig15_dashboard())
    saved.append(fig16_piqa_comparison())

    print("\n" + "="*60)
    print(f"[OK] All {len(saved)} figures saved to:")
    print(f"   {OUT_DIR}")
    print("="*60)
