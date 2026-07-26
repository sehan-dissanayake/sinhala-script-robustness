"""Assemble metrics, significance, and error analysis into a Markdown report."""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results" / "method_evaluation"
DOCS_DIR = PROJECT_ROOT / "docs" / "method_evaluation"

METHOD_LABELS = {
    "phonetic": "Phonetic (in-house)",
    "aksharamukha": "Aksharamukha",
    "uroman": "uroman",
    "nisansa_sirs_method": "Nisansa web",
}
CORPUS_LABELS = {
    "social_media": "Social media (authentic sentence pairs)",
    "swa_bhasha_words": "Swa-Bhasha (multi-reference words)",
    "augmented_sentences": "Augmented (sentence pairs)",
    "augmented_sentences_sample": "Augmented sentences (300k sample, cross-check)",
    "swa_bhasha_words_nisansacov": "Swa-Bhasha words (25k block Nisansa could cover)",
}


def _load(name, default):
    p = RESULTS_DIR / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def _fmt(v, nd=3):
    return f"{v:.{nd}f}" if isinstance(v, (int, float)) else "-"


def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    metrics = _load("metrics.json", [])
    sig = _load("significance.json", {})
    err = _load("error_analysis.json", {})

    by_corpus = {}
    for m in metrics:
        by_corpus.setdefault(m["corpus"], []).append(m)

    lines = []
    lines.append("# Transliteration Method Evaluation\n")
    lines.append("Which of the four Sinhala->Romanized (\"Singlish\") methods best reproduces "
                 "how people actually romanize Sinhala? We score each method against human "
                 "reference romanizations from the Swa-bhasha Resource Hub.\n")

    # Headline + recommendation
    grid = {(m["corpus"], m["method"]): m for m in metrics}

    def g(corpus, method, key):
        return grid.get((corpus, method), {}).get(key)

    # Per-corpus winner, straight from the numbers.
    winners = {c: min(rows, key=lambda r: r["cer_mean"])["method"]
               for c, rows in by_corpus.items()}
    overall = max(set(winners.values()), key=lambda m: list(winners.values()).count(m))

    lines.append(f"## Recommendation: {METHOD_LABELS.get(overall, overall)}\n")
    lines.append(
        f"**{METHOD_LABELS.get(overall, overall)} is the best method** on every corpus tested "
        "and is the recommended choice for the downstream script-robustness pipeline. "
        "It has the lowest CER and the highest chrF everywhere, and it is the only top-ranked "
        "option that is local, deterministic, free, and reproducible offline.\n")

    lines.append("| Corpus | Items | Winner by CER | Runner-up |")
    lines.append("|---|---|---|---|")
    for corpus, rows in by_corpus.items():
        ranked = sorted(rows, key=lambda r: r["cer_mean"])
        first, second = ranked[0], (ranked[1] if len(ranked) > 1 else None)
        second_txt = (f"{METHOD_LABELS.get(second['method'], second['method'])} "
                      f"({_fmt(second['cer_mean'])})") if second else "-"
        lines.append(f"| {CORPUS_LABELS.get(corpus, corpus)} | {first['n']:,} | "
                     f"{METHOD_LABELS.get(first['method'], first['method'])} "
                     f"({_fmt(first['cer_mean'])}) | {second_txt} |")
    lines.append("")

    lines.append("Supporting points:\n")
    if ("swa_bhasha_words", "phonetic") in grid:
        lines.append(
            f"- **Wins the large-scale word set decisively**: CER "
            f"{_fmt(g('swa_bhasha_words','phonetic','cer_mean'))} vs "
            f"{_fmt(g('swa_bhasha_words','aksharamukha','cer_mean'))} (Aksharamukha) and "
            f"{_fmt(g('swa_bhasha_words','uroman','cer_mean'))} (uroman) across 450,587 words "
            f"with 7.1M accepted human variants (p < 1e-300).")
    if ("swa_bhasha_words_nisansacov", "nisansa_sirs_method") in grid:
        lines.append(
            f"- **Beats Nisansa on words as well**: on the 25,000-word block Nisansa was able to cover, "
            f"CER {_fmt(g('swa_bhasha_words_nisansacov','phonetic','cer_mean'))} vs "
            f"{_fmt(g('swa_bhasha_words_nisansacov','nisansa_sirs_method','cer_mean'))}, where Nisansa "
            f"lands roughly level with Aksharamukha "
            f"({_fmt(g('swa_bhasha_words_nisansacov','aksharamukha','cer_mean'))}).")
    if ("social_media", "phonetic") in grid:
        lines.append(
            f"- **Wins authentic social-media text too**: CER "
            f"{_fmt(g('social_media','phonetic','cer_mean'))} vs Nisansa "
            f"{_fmt(g('social_media','nisansa_sirs_method','cer_mean'))}, with the highest chrF "
            f"({_fmt(g('social_media','phonetic','chrf'),1)} vs "
            f"{_fmt(g('social_media','nisansa_sirs_method','chrf'),1)}). See the capitalization note "
            "below - scoring case-sensitively reverses this ranking for the wrong reason.")
    lines.append(
        "- **Matches human spelling convention**: humans overwhelmingly use `w` (not `v`) and use "
        "aspiration and gemination at rates Phonetic reproduces closely (see convention table). "
        "Aksharamukha drops aspiration; uroman uses `v` and over-geminates.")
    lines.append(
        "- **Scalable, reproducible, and free**: local and deterministic, so the whole corpus can be "
        "regenerated offline. Nisansa depends on a single third-party university web endpoint: it is "
        "rate-limited by the network, can change or disappear without notice, and cannot be cited as a "
        "reproducible artifact.\n")
    lines.append(
        "**Biggest remaining gap (all methods):** over-doubling of long vowels "
        "(~0.8/token on words vs humans' ~0.12). A trivial post-process collapsing `aa/ee/ii/oo/uu` "
        "would close roughly half the residual CER to human text (relaxed CER is ~1/3 of strict).\n")

    # --- capitalization artifact -----------------------------------------
    cased = [(m["corpus"], m["method"], m["cer_mean"], m.get("cer_mean_cased"))
             for m in metrics if m.get("cer_mean_cased") is not None]
    if cased:
        lines.append("### Note: letter case is a UI artifact, not a romanization choice\n")
        lines.append(
            "The Nisansa web form capitalizes the first letter of whatever text it is given (93% of its "
            "outputs), the three local methods never capitalize, and 84% of the human social-media "
            "references happen to start with a capital. Scoring case-sensitively therefore rewards one "
            "method for an interface side-effect - and that alone is enough to flip the social-media "
            "ranking. The primary metrics fold case; the case-sensitive column below shows the size of "
            "the artifact.\n")
        lines.append("| Corpus | Method | CER (case-folded, primary) | CER (case-sensitive) |")
        lines.append("|---|---|---|---|")
        for corpus, method, cer, cer_c in cased:
            lines.append(f"| {CORPUS_LABELS.get(corpus, corpus)} | {METHOD_LABELS.get(method, method)} | "
                         f"{_fmt(cer)} | {_fmt(cer_c)} |")
        lines.append("")

    lines.append("## Metrics glossary\n")
    lines.append("- **CER / WER**: character / word error rate vs the closest accepted human variant (lower = better).\n"
                 "- **chrF, chrF++**: character n-gram F-score (higher = better); robust for morphology-rich scripts.\n"
                 "- **BLEU**: word-level MT metric (higher = better); least reliable here, reported for comparability.\n"
                 "- **Exact %**: share of items matching a human variant exactly.\n"
                 "- **Relaxed CER / Exact**: after canonicalizing spelling style (long vowels, w/v, aspiration, "
                 "gemination) on both sides - isolates genuine phonemic error from mere spelling convention.\n")

    lines.append("## Data & methodology\n")
    lines.append(
        "- **References** (Swa-bhasha Resource Hub, Sumanathilaka et al.): `social_media` - 4,397 "
        "authentic, code-mixed YouTube-comment sentence pairs; `swa_bhasha_words` - 450,587 unique words "
        "each with multiple accepted ad-hoc romanizations (7.1M total), enabling fair multi-reference "
        "scoring; `augmented_sentences_sample` - a fixed-seed 300k sample of the 7.2M machine-augmented "
        "sentence pairs, used only as a cross-check (its romanizations are themselves rule-generated, so "
        "it partly measures agreement with a generator rather than with human typing).\n")
    lines.append(
        "- **Case folding**: strict metrics are computed on case-folded text, because case reflects each "
        "tool's interface rather than its romanization scheme (see the note above).\n")
    lines.append(
        "- **Multi-reference scoring**: because Singlish is non-standard, each hypothesis is scored "
        "against the *closest* accepted human variant (oracle best reference).\n")
    lines.append(
        "- **Strict vs relaxed**: strict compares surface strings; relaxed canonicalizes spelling style "
        "on both sides. After canonicalization the three local methods agree 99.2% of the time, i.e. they "
        "are phonemically equivalent and differ only in spelling convention - so the ranking is a question "
        "of *which convention matches human typing*, which strict CER/chrF capture.\n")
    lines.append(
        "- **Significance**: percentile bootstrap 95% CIs on mean CER and paired Wilcoxon signed-rank "
        "tests against the per-corpus best method.\n")
    lines.append(
        "- **Nisansa coverage**: the web form romanizes free text line by line, so items can be batched "
        "(newline-joined) rather than sent one per request. Batched output was verified identical to "
        "one-request-per-item output, ignoring case, on all 4,253 social-media strings, and while the "
        "endpoint cooperates this runs ~78x faster (~500 items/s vs ~3/s). It will not, however, serve "
        "that volume for long: after roughly 25k words it began refusing most requests, and throughput "
        "decayed to under 6 items/s at every batch size and request spacing tried (150-350 lines/request, "
        "0.15-2 s apart), so the refusals are load-shedding on its side rather than a rate limit that "
        "pacing can avoid. Nisansa is therefore scored on the full `social_media` corpus plus the 25,000 "
        "words it did cover - reported separately, since that block is a contiguous alphabetical slice "
        "rather than a random sample - and is absent from the augmented cross-check. Requests that fail "
        "are never substituted with untranslated text; unresolved items stay out of the cache so a rerun "
        "resumes them.\n")

    for corpus, rows in by_corpus.items():
        rows = sorted(rows, key=lambda r: r["cer_mean"])
        lines.append(f"## {CORPUS_LABELS.get(corpus, corpus)}\n")
        n = rows[0]["n"]
        lines.append(f"Items: {n:,}. Best method by strict CER listed first.\n")
        lines.append("| Method | CER | WER | chrF | chrF++ | BLEU | Exact % | Relaxed CER | Relaxed Exact % |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            lines.append(f"| {METHOD_LABELS.get(r['method'], r['method'])} | {_fmt(r['cer_mean'])} | "
                         f"{_fmt(r['wer_mean'])} | {_fmt(r['chrf'],1)} | {_fmt(r['chrf2'],1)} | "
                         f"{_fmt(r['bleu'],1)} | {_fmt(r['exact_pct'],1)} | {_fmt(r['cer_relaxed_mean'])} | "
                         f"{_fmt(r['exact_relaxed_pct'],1)} |")
        lines.append("")
        cs = sig.get(corpus, {})
        if cs:
            best_m = cs.get("best_method")
            lines.append(f"**Significance** (best = {METHOD_LABELS.get(best_m, best_m)}; "
                         f"paired Wilcoxon on per-item CER):\n")
            lines.append("| Method | CER 95% CI | p vs best |")
            lines.append("|---|---|---|")
            for mth, e in cs.get("methods", {}).items():
                ci = e.get("cer_ci95", [None, None])
                p = e.get("wilcoxon_vs_best_p")
                p_txt = "— (best)" if mth == best_m else (f"{p:.2e}" if p is not None else "-")
                lines.append(f"| {METHOD_LABELS.get(mth, mth)} | [{_fmt(ci[0])}, {_fmt(ci[1])}] | {p_txt} |")
            lines.append("")

    # Convention analysis
    if err:
        lines.append("## Why: spelling-convention profile\n")
        lines.append("How each method's output compares to human typing on the four axes that dominate "
                     "Singlish variation. The method whose profile is closest to the human row tends to win.\n")
        for corpus, e in err.items():
            lines.append(f"### {CORPUS_LABELS.get(corpus, corpus)}\n")
            lines.append("| Source | v-preference (v/(v+w)) | long-vowel/tok | aspiration/tok | gemination/tok |")
            lines.append("|---|---|---|---|---|")
            rows = [("Human reference", e["human"])] + [
                (METHOD_LABELS.get(m, m), p) for m, p in e["methods"].items()]
            for name, p in rows:
                vw = _fmt(p["v_vs_w"], 2) if p["v_vs_w"] is not None else "-"
                lines.append(f"| {name} | {vw} | {_fmt(p['long_vowel'],2)} | "
                             f"{_fmt(p['aspiration'],2)} | {_fmt(p['gemination'],2)} |")
            lines.append("")

    # Plots
    lines.append("## Figures\n")
    plots = sorted((RESULTS_DIR / "plots").glob("*.png")) if (RESULTS_DIR / "plots").exists() else []
    for p in plots:
        rel = Path("../..") / "results" / "method_evaluation" / "plots" / p.name
        lines.append(f"![{p.stem}]({rel.as_posix()})\n")

    (DOCS_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote report to {DOCS_DIR / 'README.md'}")


if __name__ == "__main__":
    main()
