"""Export the evaluation results as CSV.

Two files, from the same numbers:

  method_evaluation_results.csv - for sharing. Separate titled blocks with blank
      lines between them, so it opens in Excel as readable sections rather than
      one 22-column wall. Labels are spelled out, not internal method keys.
  results_table.csv             - flat, one row per corpus x method, for further
      analysis in pandas or a pivot table.

    python src/method_evaluation/export_results_table.py
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results" / "method_evaluation"
ENDPOINT_DIR = PROJECT_ROOT / "data" / "reference" / "nisansa_endpoint"
REVIEW_PATH = RESULTS_DIR / "method_evaluation_results.csv"
FLAT_PATH = RESULTS_DIR / "results_table.csv"

CORPUS_ORDER = ["social_media", "swa_bhasha_words", "augmented_sentences_sample"]
CORPUS_LABELS = {
    "social_media": "Social media (authentic sentence pairs)",
    "swa_bhasha_words": "Swa-Bhasha words (multi-reference)",
    "augmented_sentences_sample": "Augmented sentences (300k sample, cross-check)",
}
METHOD_LABELS = {
    "phonetic": "Phonetic (in-house)",
    "aksharamukha": "Aksharamukha",
    "uroman": "uroman",
    "nisansa_sirs_method": "Nisansa web (as published)",
    "nisansa_w": "Nisansa web (v->w preprocessed)",
}
FLAT_COLUMNS = [
    "corpus", "method", "n", "n_empty", "coverage_pct", "leak_rate_pct",
    "cer", "cer_ci95_low", "cer_ci95_high", "wilcoxon_p_vs_best",
    "cer_cased", "wer", "exact_pct", "cer_relaxed", "exact_relaxed_pct",
    "chrf", "chrf_pp", "bleu",
    "v_share", "long_vowel_per_tok", "aspiration_per_tok", "gemination_per_tok",
]


def _load(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def _r(v, nd):
    return round(v, nd) if isinstance(v, (int, float)) else ""


def _p(v):
    """Format a p-value. Zeros are float underflow, not literal zero probability."""
    if v is None:
        return ""
    return "<1e-300" if v == 0 else f"{v:.3e}"


def _corpus_key(corpus: str) -> int:
    return CORPUS_ORDER.index(corpus) if corpus in CORPUS_ORDER else 99


class Sheet:
    """Accumulates titled blocks of rows for a single CSV."""

    def __init__(self) -> None:
        self.rows: list[list] = []

    def title(self, text: str) -> None:
        if self.rows:
            self.rows.append([])
        self.rows.append([text])

    def header(self, *cells) -> None:
        self.rows.append(list(cells))

    def row(self, *cells) -> None:
        self.rows.append(list(cells))

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        # utf-8-sig so Excel picks up the encoding and renders Sinhala correctly.
        with path.open("w", encoding="utf-8-sig", newline="") as fh:
            csv.writer(fh).writerows(self.rows)


def build(metrics, sig, err, failing) -> Sheet:
    by_corpus: dict[str, list[dict]] = {}
    for m in metrics:
        by_corpus.setdefault(m["corpus"], []).append(m)
    corpora = sorted(by_corpus, key=_corpus_key)
    ranked = {c: sorted(by_corpus[c], key=lambda r: r["cer_mean"]) for c in corpora}

    s = Sheet()
    s.row("Sinhala to Romanized Singlish: transliteration method evaluation")
    s.row("Generated", date.today().isoformat())
    s.row("Primary metric", "CER, lower is better, scored against the closest accepted human variant, case-folded")
    s.row("Scoring", "All items scored. Where a method produced no output the item counts as CER 1.0, not excluded.")

    # 1. Summary
    s.title("Table 1. Summary")
    s.header("Corpus", "Items", "Best by CER", "CER", "Runner-up", "CER")
    for c in corpora:
        r = ranked[c]
        second = r[1] if len(r) > 1 else None
        s.row(CORPUS_LABELS.get(c, c), r[0]["n"],
              METHOD_LABELS.get(r[0]["method"], r[0]["method"]), _r(r[0]["cer_mean"], 4),
              METHOD_LABELS.get(second["method"], second["method"]) if second else "",
              _r(second["cer_mean"], 4) if second else "")

    # 2. Accuracy, one block per corpus
    for i, c in enumerate(corpora, start=2):
        s.title(f"Table {i}. Accuracy - {CORPUS_LABELS.get(c, c)}")
        s.header("Rank", "Method", "Items", "Coverage %", "CER", "WER",
                 "chrF", "chrF++", "BLEU", "Exact match %")
        for rank, m in enumerate(ranked[c], start=1):
            s.row(rank, METHOD_LABELS.get(m["method"], m["method"]), m["n"],
                  _r(m.get("coverage_pct", 100.0), 3), _r(m["cer_mean"], 4),
                  _r(m["wer_mean"], 4), _r(m["chrf"], 2), _r(m["chrf2"], 2),
                  _r(m["bleu"], 2), _r(m["exact_pct"], 2))

    n = len(corpora) + 2

    # 3. Significance
    s.title(f"Table {n}. Statistical significance (percentile bootstrap 95% CI on mean CER; "
            f"paired Wilcoxon vs the best method on that corpus)")
    s.header("Corpus", "Method", "CER", "CI 95% low", "CI 95% high", "p vs best")
    for c in corpora:
        best = sig.get(c, {}).get("best_method")
        for m in ranked[c]:
            e = sig.get(c, {}).get("methods", {}).get(m["method"], {})
            ci = e.get("cer_ci95") or ["", ""]
            p = e.get("wilcoxon_vs_best_p")
            s.row(CORPUS_LABELS.get(c, c), METHOD_LABELS.get(m["method"], m["method"]),
                  _r(m["cer_mean"], 4), _r(ci[0], 4), _r(ci[1], 4),
                  "best method" if m["method"] == best else _p(p))
    n += 1

    # 4. Relaxed metrics
    s.title(f"Table {n}. Relaxed metrics (both sides canonicalized for spelling style: "
            f"long vowels, w/v, aspiration, gemination)")
    s.header("Corpus", "Method", "Relaxed CER", "Relaxed exact match %")
    for c in corpora:
        for m in ranked[c]:
            s.row(CORPUS_LABELS.get(c, c), METHOD_LABELS.get(m["method"], m["method"]),
                  _r(m["cer_relaxed_mean"], 4), _r(m["exact_relaxed_pct"], 2))
    n += 1

    # 5. Case sensitivity
    s.title(f"Table {n}. Case sensitivity check (the Nisansa web form capitalizes the first letter "
            f"of its input, which is an interface artifact rather than a romanization choice)")
    s.header("Corpus", "Method", "CER case-folded (primary)", "CER case-sensitive")
    for c in corpora:
        for m in ranked[c]:
            s.row(CORPUS_LABELS.get(c, c), METHOD_LABELS.get(m["method"], m["method"]),
                  _r(m["cer_mean"], 4), _r(m["cer_mean_cased"], 4))
    n += 1

    # 6. Coverage and output defects
    s.title(f"Table {n}. Coverage and output defects")
    s.header("Corpus", "Method", "Items", "No output at all", "Coverage %",
             "Outputs containing unromanized Sinhala %")
    for c in corpora:
        for m in ranked[c]:
            prof = err.get(c, {}).get("methods", {}).get(m["method"], {})
            leak = prof.get("leak_rate")
            s.row(CORPUS_LABELS.get(c, c), METHOD_LABELS.get(m["method"], m["method"]),
                  m["n"], m.get("n_empty", 0), _r(m.get("coverage_pct", 100.0), 3),
                  _r(100 * leak, 3) if leak is not None else "")
    n += 1

    # 7. Nisansa sequences that produce no output
    if failing:
        s.title(f"Table {n}. Nisansa endpoint: sequences that return no output at all "
                f"(measured by probing the full akshara grid)")
        s.header("Sequence", "Code points")
        for seq in failing:
            s.row(seq, " ".join(f"U+{ord(ch):04X}" for ch in seq))
        n += 1

    # 8. Leaked characters, word corpus
    leaked = (err.get("swa_bhasha_words", {}).get("methods", {})
                 .get("nisansa_sirs_method", {}).get("leaked_chars", {}))
    if leaked:
        s.title(f"Table {n}. Nisansa endpoint: characters returned unromanized inside otherwise "
                f"valid output, Swa-Bhasha word corpus")
        s.header("Code point", "Character", "Occurrences")
        for key, count in leaked.items():
            code, _, ch = key.partition(" ")
            s.row(code, ch, count)
        n += 1

    # 9. Spelling conventions. The human row is the target being compared
    # against, not a method, so it is kept in its own column heading.
    s.title(f"Table {n}. Spelling-convention profile (rates over items that produced output; "
            f"the closer to the human reference row, the better the convention match)")
    s.header("Corpus", "Source", "v-preference v/(v+w)", "Long vowels per token",
             "Aspiration digraphs per token", "Geminates per token")
    for c in corpora:
        e = err.get(c)
        if not e:
            continue
        rows = [("Human reference (target)", e.get("human", {}))]
        rows += [(METHOD_LABELS.get(m["method"], m["method"]),
                  e.get("methods", {}).get(m["method"], {})) for m in ranked[c]]
        for label, p in rows:
            if not p:
                continue
            s.row(CORPUS_LABELS.get(c, c), label, _r(p.get("v_vs_w"), 4),
                  _r(p.get("long_vowel"), 4), _r(p.get("aspiration"), 4),
                  _r(p.get("gemination"), 4))
    return s


def build_flat(metrics, sig, err) -> list[dict]:
    rows = []
    for m in metrics:
        corpus, method = m["corpus"], m["method"]
        e = sig.get(corpus, {}).get("methods", {}).get(method, {})
        ci = e.get("cer_ci95") or ["", ""]
        p = e.get("wilcoxon_vs_best_p")
        prof = err.get(corpus, {}).get("methods", {}).get(method, {})
        leak = prof.get("leak_rate")
        rows.append({
            "corpus": corpus, "method": method, "n": m["n"],
            "n_empty": m.get("n_empty", 0),
            "coverage_pct": _r(m.get("coverage_pct", 100.0), 4),
            "leak_rate_pct": _r(100 * leak, 4) if leak is not None else "",
            "cer": _r(m["cer_mean"], 4),
            "cer_ci95_low": _r(ci[0], 4), "cer_ci95_high": _r(ci[1], 4),
            "wilcoxon_p_vs_best": ("" if method == sig.get(corpus, {}).get("best_method")
                                   else _p(p)),
            "cer_cased": _r(m["cer_mean_cased"], 4), "wer": _r(m["wer_mean"], 4),
            "exact_pct": _r(m["exact_pct"], 3),
            "cer_relaxed": _r(m["cer_relaxed_mean"], 4),
            "exact_relaxed_pct": _r(m["exact_relaxed_pct"], 3),
            "chrf": _r(m["chrf"], 2), "chrf_pp": _r(m["chrf2"], 2),
            "bleu": _r(m["bleu"], 2),
            "v_share": _r(prof.get("v_vs_w"), 4),
            "long_vowel_per_tok": _r(prof.get("long_vowel"), 4),
            "aspiration_per_tok": _r(prof.get("aspiration"), 4),
            "gemination_per_tok": _r(prof.get("gemination"), 4),
        })
    rows.sort(key=lambda r: (_corpus_key(r["corpus"]), r["cer"]))
    return rows


def main() -> None:
    metrics = _load(RESULTS_DIR / "metrics.json", [])
    if not metrics:
        raise SystemExit(f"{RESULTS_DIR / 'metrics.json'} missing; run run_evaluation.py first")
    sig = _load(RESULTS_DIR / "significance.json", {})
    err = _load(RESULTS_DIR / "error_analysis.json", {})
    failing = _load(ENDPOINT_DIR / "failing_sequences.json", {}).get("sequences", [])

    sheet = build(metrics, sig, err, failing)
    sheet.write(REVIEW_PATH)
    print(f"wrote {len(sheet.rows)} lines -> {REVIEW_PATH.relative_to(PROJECT_ROOT)}")

    flat = build_flat(metrics, sig, err)
    with FLAT_PATH.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FLAT_COLUMNS, restval="")
        w.writeheader()
        w.writerows(flat)
    print(f"wrote {len(flat)} rows -> {FLAT_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
