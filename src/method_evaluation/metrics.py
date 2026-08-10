"""Transliteration-quality metrics for Sinhala -> Romanized-Sinhala.

Because "Singlish" is not standardised, every item may carry several accepted
human romanizations. We therefore score each hypothesis against the *closest*
reference (oracle best-reference selection) for edit-based metrics.

Two regimes are reported:
  * strict  - hypothesis vs reference as written, case-folded.
  * relaxed - both sides mapped to a canonical form that folds the systematic
              stylistic differences between formal phonetic romanization and
              ad-hoc typing (long-vowel doubling, w/v, aspiration digraphs,
              gemination). This isolates genuine phonemic errors from mere
              spelling-convention differences.

Case is folded in the strict regime because letter case is not a Singlish
spelling convention: it reflects each tool's interface rather than its
romanization scheme. The Nisansa web form capitalizes the first letter of
whatever text it is handed (93% of its outputs), while the three local methods
never capitalize; 84% of the human social-media references happen to start with
a capital. Scoring case-sensitively therefore credits one method for a UI
side-effect - enough to reverse the social-media ranking on its own. The
case-sensitive mean CER is still reported as `cer_mean_cased` so the size of
that artifact stays visible.

An empty hypothesis means the method produced no output for that item, which is
scored as total error (CER and WER 1.0, no exact match) in every regime rather
than excluded. Scoring it is the honest treatment: failing to romanize an input
is a property of the tool, not of the evaluation. Handling it explicitly also
avoids a degenerate case in the relaxed regime, where a reference that
canonicalizes to the empty string would otherwise award a perfect score to a
method that returned nothing. `n_empty` and `coverage_pct` report how much of
each method's score comes from outright failure.

Edit-based metrics use rapidfuzz (C++). chrF/chrF++/BLEU use sacrebleu.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from rapidfuzz.distance import Levenshtein

# --- canonicalisation ------------------------------------------------------

_ASPIRATES = [("th", "t"), ("dh", "d"), ("kh", "k"), ("gh", "g"),
              ("ph", "p"), ("bh", "b"), ("ch", "c"), ("sh", "s")]
_LONG_VOWELS = [("aa", "a"), ("ee", "e"), ("ii", "i"), ("oo", "o"), ("uu", "u")]
_dup = re.compile(r"(.)\1+")
_nonalnum = re.compile(r"[^a-z0-9\s]")


def canonicalize(text: str, keep_spaces: bool = True) -> str:
    """Fold systematic Singlish spelling variation to a phonemic skeleton."""
    text = text.lower()
    for src, dst in _ASPIRATES:
        text = text.replace(src, dst)
    text = text.replace("w", "v")
    for src, dst in _LONG_VOWELS:
        text = text.replace(src, dst)
    text = _nonalnum.sub(" " if keep_spaces else "", text)
    text = _dup.sub(r"\1", text)              # collapse remaining gemination
    text = re.sub(r"\s+", " ", text).strip() if keep_spaces else text.replace(" ", "")
    return text


# --- primitive scores ------------------------------------------------------

def _cer(hyp: str, ref: str) -> float:
    if not ref:
        return 0.0 if not hyp else 1.0
    return Levenshtein.distance(hyp, ref) / len(ref)


def _wer(hyp: str, ref: str) -> float:
    ref_tok, hyp_tok = ref.split(), hyp.split()
    if not ref_tok:
        return 0.0 if not hyp_tok else 1.0
    return Levenshtein.distance(hyp_tok, ref_tok) / len(ref_tok)


def best_cer(hyp: str, refs: list[str]) -> tuple[float, str]:
    """Minimum CER over accepted references and the winning reference."""
    scored = [(_cer(hyp, r), r) for r in refs]
    return min(scored, key=lambda x: x[0])


@dataclass
class ItemScore:
    cer: float
    wer: float
    exact: bool
    cer_relaxed: float
    exact_relaxed: bool
    best_ref: str            # strict best reference (for corpus chrF/BLEU)
    level: str = "sentence"
    cer_cased: float = 0.0   # case-sensitive CER, kept as a sensitivity check
    empty: bool = False      # method produced no output at all


def score_item(hypothesis: str, references: list[str], level: str = "sentence",
               fold_case: bool = True) -> ItemScore:
    if not hypothesis and any(references):
        # No output: total error under every regime. The longest reference is
        # handed to the corpus-level chrF/BLEU accumulators so an empty
        # hypothesis costs recall there too.
        return ItemScore(cer=1.0, wer=1.0, exact=False, cer_relaxed=1.0,
                         exact_relaxed=False, best_ref=max(references, key=len),
                         level=level, cer_cased=1.0, empty=True)

    keep_spaces = level == "sentence"
    raw_hyp, raw_refs = hypothesis, references
    if fold_case:
        hypothesis = hypothesis.lower()
        references = [r.lower() for r in references]

    cer, best_ref = best_cer(hypothesis, references)
    wer = min(_wer(hypothesis, r) for r in references)
    exact = any(hypothesis == r for r in references)
    cer_cased = best_cer(raw_hyp, raw_refs)[0] if fold_case else cer

    h_can = canonicalize(hypothesis, keep_spaces)
    refs_can = [canonicalize(r, keep_spaces) for r in references]
    cer_relaxed = min(_cer(h_can, r) for r in refs_can)
    exact_relaxed = any(h_can == r for r in refs_can)

    return ItemScore(cer, wer, exact, cer_relaxed, exact_relaxed, best_ref, level,
                     cer_cased=cer_cased)


# --- corpus aggregation ----------------------------------------------------

@dataclass
class CorpusResult:
    corpus: str
    method: str
    n: int
    n_empty: int          # items with no output at all
    coverage_pct: float   # 100 * (1 - n_empty / n)
    cer_mean: float
    cer_mean_cased: float
    wer_mean: float
    exact_pct: float
    cer_relaxed_mean: float
    exact_relaxed_pct: float
    chrf: float
    chrf2: float          # chrF++ (word n-grams included)
    bleu: float
    per_item_cer: list[float] = field(default_factory=list)
    per_item_cer_relaxed: list[float] = field(default_factory=list)

    def summary(self) -> dict:
        d = self.__dict__.copy()
        d.pop("per_item_cer")
        d.pop("per_item_cer_relaxed")
        return d


def aggregate(corpus: str, method: str, hypotheses: list[str],
              references: list[list[str]], level: str,
              fold_case: bool = True) -> CorpusResult:
    import sacrebleu

    scores = [score_item(h, refs, level, fold_case) for h, refs in zip(hypotheses, references)]
    n = len(scores)
    best_refs = [s.best_ref for s in scores]
    hyps = [h.lower() for h in hypotheses] if fold_case else list(hypotheses)

    chrf = sacrebleu.corpus_chrf(hyps, [best_refs], word_order=0).score
    chrf2 = sacrebleu.corpus_chrf(hyps, [best_refs], word_order=2).score
    bleu = sacrebleu.corpus_bleu(hyps, [best_refs], tokenize="13a").score

    n_empty = sum(s.empty for s in scores)

    return CorpusResult(
        corpus=corpus,
        method=method,
        n=n,
        n_empty=n_empty,
        coverage_pct=100.0 * (1 - n_empty / n) if n else 0.0,
        cer_mean=sum(s.cer for s in scores) / n,
        cer_mean_cased=sum(s.cer_cased for s in scores) / n,
        wer_mean=sum(s.wer for s in scores) / n,
        exact_pct=100.0 * sum(s.exact for s in scores) / n,
        cer_relaxed_mean=sum(s.cer_relaxed for s in scores) / n,
        exact_relaxed_pct=100.0 * sum(s.exact_relaxed for s in scores) / n,
        chrf=chrf,
        chrf2=chrf2,
        bleu=bleu,
        per_item_cer=[s.cer for s in scores],
        per_item_cer_relaxed=[s.cer_relaxed for s in scores],
    )
