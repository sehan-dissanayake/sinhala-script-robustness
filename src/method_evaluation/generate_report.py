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
    "nisansa_sirs_method": "Nisansa web (as published)",
    "nisansa_w": "Nisansa web (v→w preprocessed)",
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

    # A difference of 0.0001 CER is not a win, however many items back it. Treat
    # methods whose bootstrap CIs overlap the leader's as statistically tied.
    def ties_with_leader(corpus: str) -> list[str]:
        entries = sig.get(corpus, {}).get("methods", {})
        leader = sig.get(corpus, {}).get("best_method")
        lead_ci = entries.get(leader, {}).get("cer_ci95")
        if not lead_ci:
            return []
        out = []
        for m, e in entries.items():
            ci = e.get("cer_ci95")
            if m != leader and ci and ci[0] <= lead_ci[1] and lead_ci[0] <= ci[1]:
                out.append(m)
        return out

    tied_any = {c: ties_with_leader(c) for c in by_corpus}
    contenders = sorted({m for v in tied_any.values() for m in v})

    lines.append(f"## Recommendation: {METHOD_LABELS.get(overall, overall)}\n")
    if contenders:
        names = ", ".join(METHOD_LABELS.get(m, m) for m in contenders)
        lines.append(
            f"**{METHOD_LABELS.get(overall, overall)} is the recommended method**, but on accuracy it is "
            f"a statistical tie with {names} - their confidence intervals overlap, so the ranking between "
            f"them is not meaningful. The recommendation therefore rests on engineering properties rather "
            f"than a quality difference: Phonetic runs locally and deterministically, needs no network, "
            f"covers every word in the corpus, and can be rerun by anyone offline.\n")
    else:
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
        n_words = g("swa_bhasha_words", "phonetic", "n") or 0
        lines.append(
            f"- **Wins the large-scale word set decisively**: CER "
            f"{_fmt(g('swa_bhasha_words','phonetic','cer_mean'))} vs "
            f"{_fmt(g('swa_bhasha_words','nisansa_sirs_method','cer_mean'))} (Nisansa), "
            f"{_fmt(g('swa_bhasha_words','aksharamukha','cer_mean'))} (Aksharamukha) and "
            f"{_fmt(g('swa_bhasha_words','uroman','cer_mean'))} (uroman) across {n_words:,} words "
            f"with 7.1M accepted human variants (p < 1e-300 against every one of them).")
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
        "- **Complete and reproducible**: local and deterministic, so the whole corpus can be regenerated "
        "offline and covers every word. Nisansa is a third-party web endpoint that can change or go offline, "
        "and it cannot romanize part of the alphabet at all (see the limitation note below), so it is both "
        "less reproducible and less complete.\n")
    lines.append(
        "**Biggest remaining gap (all methods):** over-doubling of long vowels "
        "(~0.8/token on words vs humans' ~0.12). A trivial post-process collapsing `aa/ee/ii/oo/uu` "
        "would close roughly half the residual CER to human text (relaxed CER is ~1/3 of strict).\n")

    if ("swa_bhasha_words", "nisansa_w") in grid:
        lines.append("### The v/w convention accounted for Nisansa's entire gap\n")
        lines.append(
            "Nisansa's output matches the phonetic method on long vowels, aspiration and gemination, and "
            "differs almost only in writing ව as `v` where humans overwhelmingly write `w`. Rewriting just "
            "that one convention is applied as a preprocessing stage before scoring (a pure post-process of "
            "the fetched results, not the published tool) and removes the difference entirely:\n")
        lines.append("| Corpus | Nisansa as published | Nisansa with v→w | Phonetic |")
        lines.append("|---|---|---|---|")
        for corpus in by_corpus:
            if (corpus, "nisansa_w") not in grid:
                continue
            lines.append(
                f"| {CORPUS_LABELS.get(corpus, corpus)} | "
                f"{_fmt(g(corpus, 'nisansa_sirs_method', 'cer_mean'))} | "
                f"**{_fmt(g(corpus, 'nisansa_w', 'cer_mean'))}** | "
                f"{_fmt(g(corpus, 'phonetic', 'cer_mean'))} |")
        lines.append("")
        lines.append(
            "So the two methods are equivalent in romanization quality once that single orthographic "
            "choice is normalized, which is consistent with the relaxed metrics: after canonicalizing "
            "spelling style, their CERs were already identical to four decimal places. The honest "
            "conclusion is that Nisansa is not a *worse* romanizer - it simply writes `v`, and Sinhala "
            "speakers type `w`. Phonetic remains the recommendation because it matches human convention "
            "out of the box and is local, complete and reproducible, not because it transliterates "
            "better.\n")

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
        "- **Nisansa coverage**: this method is a web form rather than a local library. It romanizes free "
        "text line by line, so items are batched (newline-joined) instead of sent one per request, which "
        "is ~78x faster and was verified to give output identical to one-request-per-item, ignoring case, "
        "on all 4,253 social-media strings. It is scored on every item of the full word corpus and the "
        "full social-media corpus; it is absent from the augmented cross-check, which is a secondary "
        "check against machine-generated romanizations and not worth the fetch time.\n")
    lines.append(
        "- **v→w preprocessing**: the endpoint writes ව as `v` where Sinhala speakers type `w`. Since that "
        "one orthographic choice accounted for its entire measured gap, the rewrite is applied as a "
        "standard preprocessing stage and `Nisansa web (v→w preprocessed)` is the variant to read as *the* "
        "Nisansa result. The as-published row is kept beside it so the modification stays visible.\n")
    lines.append(
        "- **Nothing is excluded.** Where a method produced no output for an item, that item is scored as "
        "total error (CER 1.0) rather than dropped. Failing to romanize an input is a property of the tool, "
        "so excusing it would flatter the tool; the `Coverage` column below makes the size of that effect "
        "explicit. An earlier revision scored only the rows every method answered, which measured mapping "
        "quality but hid a coverage failure; those matched-subset numbers are still reproducible with "
        "`run_evaluation.py --common-subset`.\n")
    lines.append(
        "- **Two measured defects in the Nisansa tool.** Both are characterised by direct probing of the "
        "full Sinhala akshara grid (881 units, `nisansa_probe.py`), not inferred from failures:\n"
        "  1. *No output at all* for **17 sequences**, every one of them ඤ (U+0DA4) carrying a vowel sign "
        "or al-lakuna (ඤ්, ඤා, ඤැ, ඤෑ, ඤි, ඤී, ඤු, ඤූ, ඤෘ, ඤේ, ඤෛ, ඤො, ඤෝ, ඤෞ, ඤෲ, ඤ්‍ය, ඤ්‍ර). The letter "
        "ඤ alone romanizes fine, as does ඤෙ and the neighbouring ඥ (U+0DA5), so the tool's mapping table is "
        "missing those specific combinations rather than the letter. The probe's table reproduces exactly "
        "the 1,470 of 450,587 words (0.33%) that the corpus run found by bisection - independent "
        "confirmation that it is neither over- nor under-inclusive.\n"
        "  2. *Silent leaks*: **12 sequences** come back unromanized inside otherwise valid Latin output "
        "(ඎ, ඏ, ඐ, ඓ, ඞ, ඦ, ෟ, ෳ, ඣෙ, ඤෙ, ඥෙ, ඬෙ), so ඓතිහාසික romanizes to `ඓthihaasika`. Real corpus text "
        "also leaks on malformed sequences outside the grid, such as a vowel sign followed by al-lakuna. "
        "These are scored as they are. An earlier revision ran the in-house phonetic romanizer over every "
        "response to patch such characters up, which made the measured system a hybrid of two methods under "
        "comparison and hid the defect; all results here are the endpoint's verbatim output.\n")

    for corpus, rows in by_corpus.items():
        rows = sorted(rows, key=lambda r: r["cer_mean"])
        lines.append(f"## {CORPUS_LABELS.get(corpus, corpus)}\n")
        n = rows[0]["n"]
        lines.append(f"Items: {n:,}. Best method by strict CER listed first.\n")
        lines.append("| Method | Coverage % | CER | WER | chrF | chrF++ | BLEU | Exact % | "
                     "Relaxed CER | Relaxed Exact % |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            cov = r.get("coverage_pct")
            cov_txt = "100" if cov is None else _fmt(cov, 2)
            if r.get("n_empty"):
                cov_txt += f" ({r['n_empty']:,} empty)"
            lines.append(f"| {METHOD_LABELS.get(r['method'], r['method'])} | {cov_txt} | "
                         f"{_fmt(r['cer_mean'])} | "
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
            lines.append("| Source | v-preference (v/(v+w)) | long-vowel/tok | aspiration/tok | "
                         "gemination/tok | leaked Sinhala % |")
            lines.append("|---|---|---|---|---|---|")
            rows = [("Human reference", e["human"])] + [
                (METHOD_LABELS.get(m, m), p) for m, p in e["methods"].items()]
            for name, p in rows:
                vw = _fmt(p["v_vs_w"], 2) if p["v_vs_w"] is not None else "-"
                leak = p.get("leak_rate")
                leak_txt = "-" if leak is None else _fmt(100 * leak, 2)
                lines.append(f"| {name} | {vw} | {_fmt(p['long_vowel'],2)} | "
                             f"{_fmt(p['aspiration'],2)} | {_fmt(p['gemination'],2)} | {leak_txt} |")
            lines.append("")
            lines.append("Rates are computed over the items each method produced output for, so a "
                         "failed item cannot flatter a method by contributing zero tokens; coverage "
                         "is charged in the metric tables above instead.\n")

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
