"""
Analysis script for the prompt-template-selection pilot results.

Expects two folders (edit the paths below):
  RAW_DIR      -> {model}_prompt_pilot_raw.csv       (one row per generation)
  SUMMARY_DIR  -> {model}_prompt_pilot_summary.csv    (one row per model/dataset/template)

Raw columns:     model, dataset, template, script, id, gold_label, pred, pred_label,
                 correct, raw_output, n_input_tokens, n_output_tokens
Summary columns: model, dataset, template, n, invalid_rate, accuracy_among_valid,
                 overall_accuracy

Run:
    python analyze_prompt_pilot.py
Outputs (all under ./analysis_out/):
    pooled_by_template.csv         overall winner per dataset, pooled across all models
    by_template_and_script.csv     does the winner hold for unicode vs romanized?
    by_model_and_template.csv      per-model breakdown (spot outlier models)
    invalid_reasons.csv            most common raw_output text behind INVALID preds
    model_ranking.csv              which model does best overall, per dataset
    summary.txt                    plain-English printout of the key findings
"""

from pathlib import Path
import pandas as pd

# ============================================================
# CONFIG — point these at your two folders
# ============================================================
RAW_DIR = Path("./results/prompt_template_evaluation/results/raw")
SUMMARY_DIR = Path("./results/prompt_template_evaluation/results/summaries")
OUT_DIR = Path("./results/prompt_template_evaluation/results/analysis_out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

pd.set_option("display.width", 140)
pd.set_option("display.max_columns", 20)


# ============================================================
# 1. Load everything
# ============================================================
def load_all_raw(raw_dir: Path) -> pd.DataFrame:
    paths = sorted(raw_dir.glob("*_prompt_pilot_raw.csv"))
    if not paths:
        raise FileNotFoundError(f"No raw CSVs found in {raw_dir.resolve()}")
    dfs = [pd.read_csv(p, encoding="utf-8-sig") for p in paths]
    df = pd.concat(dfs, ignore_index=True)
    print(f"Loaded {len(paths)} raw files -> {len(df):,} generations "
          f"from {df['model'].nunique()} models.")
    return df


def load_all_summary(summary_dir: Path) -> pd.DataFrame:
    paths = sorted(summary_dir.glob("*_prompt_pilot_summary.csv"))
    if not paths:
        raise FileNotFoundError(f"No summary CSVs found in {summary_dir.resolve()}")
    dfs = [pd.read_csv(p, encoding="utf-8-sig") for p in paths]
    df = pd.concat(dfs, ignore_index=True)
    print(f"Loaded {len(paths)} summary files -> {len(df):,} rows.")
    return df


# ============================================================
# 2. Metric helper (same definitions as the notebook)
# ============================================================
def compute_metrics(df: pd.DataFrame) -> pd.Series:
    n = len(df)
    if n == 0:
        return pd.Series({"n": 0, "invalid_rate": float("nan"),
                           "accuracy_among_valid": float("nan"),
                           "overall_accuracy": float("nan")})
    n_invalid = (df["pred"] == "INVALID").sum()
    n_valid = n - n_invalid
    n_correct = df["correct"].sum()
    return pd.Series({
        "n": n,
        "invalid_rate": n_invalid / n,
        "accuracy_among_valid": (n_correct / n_valid) if n_valid else float("nan"),
        "overall_accuracy": n_correct / n,
    })


# ============================================================
# 3. Analyses
# ============================================================
def pooled_by_template(raw: pd.DataFrame) -> pd.DataFrame:
    """Per dataset x template, pooled across every model and both scripts.
    This mirrors the notebook's final recommendation step, recomputed here
    as a sanity check / single source of truth."""
    out = (
        raw.groupby(["dataset", "template"])
        .apply(compute_metrics, include_groups=False)
        .reset_index()
        .sort_values(["dataset", "overall_accuracy"], ascending=[True, False])
    )
    return out


def by_template_and_script(raw: pd.DataFrame) -> pd.DataFrame:
    """Checks whether the winning template is consistent between unicode and
    romanized script, or whether the recommendation flips depending on script."""
    out = (
        raw.groupby(["dataset", "template", "script"])
        .apply(compute_metrics, include_groups=False)
        .reset_index()
        .sort_values(["dataset", "script", "overall_accuracy"], ascending=[True, True, False])
    )
    return out


def by_model_and_template(raw: pd.DataFrame) -> pd.DataFrame:
    """Per-model breakdown for every dataset/template. Use this to catch a
    template that only wins because one or two strong models carry it."""
    out = (
        raw.groupby(["dataset", "template", "model"])
        .apply(compute_metrics, include_groups=False)
        .reset_index()
        .sort_values(["dataset", "template", "overall_accuracy"], ascending=[True, True, False])
    )
    return out


def model_ranking(raw: pd.DataFrame) -> pd.DataFrame:
    """Which model performs best overall per dataset, using each model's own
    best template (its ceiling), plus its average across templates (robustness)."""
    per_model_template = (
        raw.groupby(["dataset", "model", "template"])
        .apply(compute_metrics, include_groups=False)
        .reset_index()
    )
    best = (
        per_model_template.sort_values("overall_accuracy", ascending=False)
        .groupby(["dataset", "model"])
        .first()
        .reset_index()
        .rename(columns={"template": "best_template", "overall_accuracy": "best_overall_accuracy"})
    )
    avg = (
        per_model_template.groupby(["dataset", "model"])["overall_accuracy"]
        .mean()
        .reset_index()
        .rename(columns={"overall_accuracy": "avg_overall_accuracy_across_templates"})
    )
    out = best.merge(avg, on=["dataset", "model"])
    out = out[["dataset", "model", "best_template", "best_overall_accuracy",
               "avg_overall_accuracy_across_templates", "n"]]
    return out.sort_values(["dataset", "best_overall_accuracy"], ascending=[True, False])


def invalid_reasons(raw: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """What the model actually output when the extractor returned INVALID.
    Helps decide if INVALID means 'refused/rambled' vs 'extractor bug'."""
    invalid = raw[raw["pred"] == "INVALID"].copy()
    if invalid.empty:
        return pd.DataFrame(columns=["dataset", "template", "model", "count", "example_raw_output"])
    invalid["raw_output_trunc"] = invalid["raw_output"].astype(str).str.slice(0, 80)
    grouped = (
        invalid.groupby(["dataset", "template", "model"])
        .agg(count=("id", "count"), example_raw_output=("raw_output_trunc", "first"))
        .reset_index()
        .sort_values("count", ascending=False)
        .head(top_n)
    )
    return grouped


def final_recommendation(pooled: pd.DataFrame) -> dict:
    rec = {}
    for dataset_key, group in pooled.groupby("dataset"):
        winner_row = group.sort_values("overall_accuracy", ascending=False).iloc[0]
        rec[dataset_key] = {
            "template": winner_row["template"],
            "overall_accuracy": winner_row["overall_accuracy"],
            "invalid_rate": winner_row["invalid_rate"],
        }
    return rec


# ============================================================
# 4. Run everything
# ============================================================
def main():
    raw = load_all_raw(RAW_DIR)
    _summary = load_all_summary(SUMMARY_DIR)  # loaded for completeness / cross-check

    # sanity check: raw-recomputed metrics should match the notebook's own summaries
    recomputed = (
        raw.groupby(["model", "dataset", "template"])
        .apply(compute_metrics, include_groups=False)
        .reset_index()
    )
    merged_check = recomputed.merge(
        _summary, on=["model", "dataset", "template"], suffixes=("_recomputed", "_summary")
    )
    mismatch = merged_check[
        (merged_check["overall_accuracy_recomputed"] - merged_check["overall_accuracy_summary"]).abs() > 1e-9
    ]
    if len(mismatch):
        print(f"WARNING: {len(mismatch)} rows differ between raw-recomputed metrics and "
              f"the saved summaries. Check for stale summary files.")
    else:
        print("Sanity check passed: raw-recomputed metrics match saved summaries exactly.")

    pooled = pooled_by_template(raw)
    script_split = by_template_and_script(raw)
    per_model = by_model_and_template(raw)
    ranking = model_ranking(raw)
    invalids = invalid_reasons(raw)

    pooled.to_csv(OUT_DIR / "pooled_by_template.csv", index=False, encoding="utf-8-sig")
    script_split.to_csv(OUT_DIR / "by_template_and_script.csv", index=False, encoding="utf-8-sig")
    per_model.to_csv(OUT_DIR / "by_model_and_template.csv", index=False, encoding="utf-8-sig")
    ranking.to_csv(OUT_DIR / "model_ranking.csv", index=False, encoding="utf-8-sig")
    invalids.to_csv(OUT_DIR / "invalid_reasons.csv", index=False, encoding="utf-8-sig")

    rec = final_recommendation(pooled)

    lines = []
    lines.append("=" * 78)
    lines.append("PROMPT TEMPLATE PILOT — ANALYSIS SUMMARY")
    lines.append("=" * 78)
    lines.append(f"Models: {raw['model'].nunique()} | Datasets: {list(raw['dataset'].unique())} "
                 f"| Total generations: {len(raw):,}")
    lines.append("")
    lines.append("Recommended template per dataset (pooled overall_accuracy):")
    for dataset_key, info in rec.items():
        lines.append(f"  {dataset_key:14} -> {info['template']:16} "
                     f"(overall_acc={info['overall_accuracy']:.3f}, "
                     f"invalid_rate={info['invalid_rate']:.3f})")
    lines.append("")

    lines.append("Does the winner hold across BOTH scripts (unicode & romanized)?")
    for dataset_key, winning in rec.items():
        sub = script_split[(script_split["dataset"] == dataset_key)
                            & (script_split["template"] == winning["template"])]
        consistent = sub["overall_accuracy"].min() if len(sub) else float("nan")
        lines.append(f"  {dataset_key:14} winner={winning['template']:16} "
                     f"min_across_scripts={consistent:.3f} "
                     f"({'consistent' if len(sub) == 2 and sub['overall_accuracy'].max() - sub['overall_accuracy'].min() < 0.1 else 'CHECK - diverges by script'})")
    lines.append("")

    lines.append("Any single model dragging the winning template down? (bottom 3 shown per dataset)")
    for dataset_key, winning in rec.items():
        sub = per_model[(per_model["dataset"] == dataset_key)
                         & (per_model["template"] == winning["template"])].sort_values("overall_accuracy")
        lines.append(f"  {dataset_key} / {winning['template']}:")
        for _, row in sub.head(3).iterrows():
            lines.append(f"    {row['model']:24} overall_acc={row['overall_accuracy']:.3f} "
                         f"invalid_rate={row['invalid_rate']:.3f}")
    lines.append("")

    lines.append(f"Full CSV breakdowns written to: {OUT_DIR.resolve()}")
    summary_text = "\n".join(lines)
    print("\n" + summary_text)
    (OUT_DIR / "summary.txt").write_text(summary_text, encoding="utf-8")


if __name__ == "__main__":
    main()
