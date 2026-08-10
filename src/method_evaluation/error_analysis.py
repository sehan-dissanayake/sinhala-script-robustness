"""Explain *why* a method wins: compare spelling conventions to human typing.

Singlish variation is dominated by a handful of orthographic choices. We profile
each method's output and the human references along these axes, so the ranking is
interpretable rather than a black-box score:

  * v_vs_w         - share of [vw] characters written as 'v'
  * long_vowel     - rate of doubled long vowels (aa/ee/ii/oo/uu) per token
  * aspiration     - rate of aspiration digraphs (th/dh/kh/gh/ph/bh/ch/sh) per token
  * gemination     - rate of doubled consonants per token

These are conditional on the method having produced output. An item a method
failed on contributes no tokens, so counting it would drag every rate toward
zero and make a method look *better* at the very conventions being measured. The
headline metrics in run_evaluation.py do charge those items as errors; the split
is deliberate and reported as `coverage` and `leak_rate` below:

  * coverage       - share of items the method produced any output for
  * leak_rate      - share of outputs still containing unromanized Sinhala
  * leaked_chars   - which characters leak, and how often

Outputs -> results/method_evaluation/error_analysis.json
"""

import json
import re
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PARALLEL_DIR = PROJECT_ROOT / "data" / "reference" / "parallel"
TRANSLIT_DIR = PROJECT_ROOT / "data" / "reference" / "transliterated"
RESULTS_DIR = PROJECT_ROOT / "results" / "method_evaluation"

METHODS = ["phonetic", "aksharamukha", "uroman", "nisansa_sirs_method", "nisansa_w"]
_ASP = re.compile(r"th|dh|kh|gh|ph|bh|ch|sh")
_LONG = re.compile(r"aa|ee|ii|oo|uu")
_GEM = re.compile(r"([b-df-hj-np-tv-z])\1")
_WORD = re.compile(r"[a-z]+")
_SINHALA_LO, _SINHALA_HI = "\u0d80", "\u0dff"


def profile(text: str) -> dict:
    t = text.lower()
    letters = t.split()
    ntok = max(len(letters), 1)
    v = t.count("v")
    w = t.count("w")
    return {
        "v_share": (v / (v + w)) if (v + w) else None,
        "long_vowel_per_tok": len(_LONG.findall(t)) / ntok,
        "aspiration_per_tok": len(_ASP.findall(t)) / ntok,
        "gemination_per_tok": len(_GEM.findall(t)) / ntok,
        "_tokens": ntok,
    }


def _mean_profile(texts) -> dict:
    """Convention profile over the items that produced output, plus failure rates.

    Empty outputs are excluded from the per-token rates (see module docstring)
    but counted in `coverage`, so nothing is hidden.
    """
    acc = defaultdict(float)
    vnum = vden = 0
    tot_tok = 0
    n = n_empty = n_leak = 0
    leaked: dict[str, int] = defaultdict(int)
    for t in texts:
        n += 1
        if not t:
            n_empty += 1
            continue
        leaks = [c for c in t if _SINHALA_LO <= c <= _SINHALA_HI]
        if leaks:
            n_leak += 1
            for c in leaks:
                leaked[c] += 1
        p = profile(t)
        tot_tok += p["_tokens"]
        acc["long_vowel"] += p["long_vowel_per_tok"] * p["_tokens"]
        acc["aspiration"] += p["aspiration_per_tok"] * p["_tokens"]
        acc["gemination"] += p["gemination_per_tok"] * p["_tokens"]
        low = t.lower()
        vnum += low.count("v")
        vden += low.count("v") + low.count("w")
    scored = n - n_empty
    return {
        "n": n,
        "n_scored": scored,
        "n_empty": n_empty,
        "coverage": (scored / n) if n else None,
        "leak_rate": (n_leak / scored) if scored else None,
        "leaked_chars": {f"U+{ord(c):04X} {c}": v
                         for c, v in sorted(leaked.items(), key=lambda kv: -kv[1])},
        "v_vs_w": (vnum / vden) if vden else None,
        "long_vowel": acc["long_vowel"] / tot_tok if tot_tok else None,
        "aspiration": acc["aspiration"] / tot_tok if tot_tok else None,
        "gemination": acc["gemination"] / tot_tok if tot_tok else None,
    }


def _load_refs(corpus: str) -> dict[str, list[str]]:
    refs = {}
    with (PARALLEL_DIR / f"{corpus}.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            refs[r["id"]] = r["references"]
    return refs


def _load_hyps(corpus: str, method: str) -> dict[str, str] | None:
    p = TRANSLIT_DIR / corpus / f"{method}.jsonl"
    if not p.exists():
        return None
    out = {}
    with p.open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            out[r["id"]] = r["hypothesis"]
    return out


def analyze(corpora: list[str]) -> dict:
    report = {}
    for corpus in corpora:
        refs = _load_refs(corpus)
        # Human profile: use the first (most natural) reference per item.
        human_texts = [v[0] for v in refs.values()]
        entry = {"human": _mean_profile(human_texts), "methods": {}}
        for method in METHODS:
            hyps = _load_hyps(corpus, method)
            if hyps is None:
                continue
            entry["methods"][method] = _mean_profile([hyps.get(i, "") for i in refs])
        report[corpus] = entry
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpora", nargs="+",
                        default=["social_media", "swa_bhasha_words",
                                 "augmented_sentences_sample"])
    args = parser.parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report = analyze(args.corpora)
    (RESULTS_DIR / "error_analysis.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    def fmt(x, spec=".2f"):
        return f"{x:{spec}}" if x is not None else " n/a"

    for corpus, e in report.items():
        print(f"\n=== {corpus} ===")
        print(f"  {'source':16s} v_vs_w  longV  asp   gem   coverage  leaks")
        rows = [("human", e["human"])] + list(e["methods"].items())
        for name, p in rows:
            print(f"  {name:16s} {fmt(p['v_vs_w'])}   {fmt(p['long_vowel'])}  "
                  f"{fmt(p['aspiration'])}  {fmt(p['gemination'])}  "
                  f"{fmt(p['coverage'], '7.4f')}  {fmt(p['leak_rate'], '.4f')}")
        for name, p in rows:
            if p["leaked_chars"]:
                top = ", ".join(f"{k} x{v:,}" for k, v in list(p["leaked_chars"].items())[:8])
                print(f"    {name} leaked: {top}")
