"""Compute per-corpus, per-method transliteration metrics + significance tests.

Outputs (results/method_evaluation/):
    metrics_summary.csv     one row per corpus x method
    metrics.json            full metric payload
    per_item/<c>__<m>.json  per-item CER arrays (strict + relaxed)
    significance.json       bootstrap 95% CIs + paired Wilcoxon vs. best method
"""

import argparse
import json
from pathlib import Path

import numpy as np

from metrics import aggregate

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PARALLEL_DIR = PROJECT_ROOT / "data" / "reference" / "parallel"
TRANSLIT_DIR = PROJECT_ROOT / "data" / "reference" / "transliterated"
RESULTS_DIR = PROJECT_ROOT / "results" / "method_evaluation"

ALL_METHODS = ["phonetic", "aksharamukha", "uroman", "nisansa_sirs_method"]


def _load_corpus(corpus: str) -> tuple[dict[str, list[str]], str]:
    refs: dict[str, list[str]] = {}
    level = "sentence"
    with (PARALLEL_DIR / f"{corpus}.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            refs[rec["id"]] = rec["references"]
            level = rec["level"]
    return refs, level


def _load_hypotheses(corpus: str, method: str) -> dict[str, str] | None:
    path = TRANSLIT_DIR / corpus / f"{method}.jsonl"
    if not path.exists():
        return None
    hyps: dict[str, str] = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            hyps[rec["id"]] = rec["hypothesis"]
    return hyps


def bootstrap_ci(values: np.ndarray, n_boot: int = 2000, seed: int = 42) -> tuple[float, float]:
    """Percentile bootstrap CI for the mean, computed in a memory-safe loop."""
    rng = np.random.default_rng(seed)
    n = len(values)
    if n == 0:
        return (float("nan"), float("nan"))
    means = np.empty(n_boot)
    for b in range(n_boot):
        means[b] = values[rng.integers(0, n, size=n)].mean()
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def paired_wilcoxon(a: np.ndarray, b: np.ndarray) -> float:
    from scipy.stats import wilcoxon
    diff = a - b
    if np.allclose(diff, 0):
        return 1.0
    try:
        return float(wilcoxon(a, b, zero_method="wilcox", alternative="two-sided").pvalue)
    except ValueError:
        return 1.0


def evaluate_corpus(corpus: str, methods: list[str]) -> tuple[list, dict]:
    refs, level = _load_corpus(corpus)
    ids = list(refs)
    results, per_item = [], {}
    for method in methods:
        hyps = _load_hypotheses(corpus, method)
        if hyps is None:
            continue
        ordered_hyps = [hyps.get(i, "") for i in ids]
        ordered_refs = [refs[i] for i in ids]
        res = aggregate(corpus, method, ordered_hyps, ordered_refs, level)
        results.append(res)
        per_item[method] = {
            "cer": np.array(res.per_item_cer),
            "cer_relaxed": np.array(res.per_item_cer_relaxed),
        }
        print(f"  {method:20s} CER={res.cer_mean:.4f} (cased {res.cer_mean_cased:.4f}) "
              f"chrF={res.chrf:.2f} exact={res.exact_pct:.1f}% "
              f"relaxedCER={res.cer_relaxed_mean:.4f}")
    return results, per_item


def run(corpora: list[str], methods: list[str]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "per_item").mkdir(exist_ok=True)

    all_summaries, significance = [], {}
    for corpus in corpora:
        print(f"\n=== {corpus} ===")
        results, per_item = evaluate_corpus(corpus, methods)
        for res in results:
            all_summaries.append(res.summary())
            with (RESULTS_DIR / "per_item" / f"{corpus}__{res.method}.json").open("w", encoding="utf-8") as fh:
                json.dump({"cer": res.per_item_cer, "cer_relaxed": res.per_item_cer_relaxed}, fh)

        if not results:
            continue
        # Best method = lowest mean strict CER on this corpus.
        best = min(results, key=lambda r: r.cer_mean)
        corpus_sig = {"best_method": best.method, "methods": {}}
        for res in results:
            cer = per_item[res.method]["cer"]
            lo, hi = bootstrap_ci(cer)
            entry = {"cer_mean": res.cer_mean, "cer_ci95": [lo, hi]}
            if res.method != best.method:
                entry["wilcoxon_vs_best_p"] = paired_wilcoxon(cer, per_item[best.method]["cer"])
            corpus_sig["methods"][res.method] = entry
        significance[corpus] = corpus_sig

    import csv
    if all_summaries:
        keys = list(all_summaries[0].keys())
        with (RESULTS_DIR / "metrics_summary.csv").open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_summaries)
    with (RESULTS_DIR / "metrics.json").open("w", encoding="utf-8") as fh:
        json.dump(all_summaries, fh, ensure_ascii=False, indent=2)
    with (RESULTS_DIR / "significance.json").open("w", encoding="utf-8") as fh:
        json.dump(significance, fh, ensure_ascii=False, indent=2)
    print(f"\nWrote metrics + significance to {RESULTS_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpora", nargs="+", default=["social_media", "swa_bhasha_words"])
    parser.add_argument("--methods", nargs="+", default=ALL_METHODS)
    args = parser.parse_args()
    run(args.corpora, args.methods)
