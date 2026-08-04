"""Explain *why* a method wins: compare spelling conventions to human typing.

Singlish variation is dominated by a handful of orthographic choices. We profile
each method's output and the human references along these axes, so the ranking is
interpretable rather than a black-box score:

  * v_vs_w         - share of [vw] characters written as 'v'
  * long_vowel     - rate of doubled long vowels (aa/ee/ii/oo/uu) per token
  * aspiration     - rate of aspiration digraphs (th/dh/kh/gh/ph/bh/ch/sh) per token
  * gemination     - rate of doubled consonants per token

We also report CER by word length (word corpus) to show where methods struggle.
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
    acc = defaultdict(float)
    vnum = vden = 0
    tot_tok = 0
    for t in texts:
        p = profile(t)
        tot_tok += p["_tokens"]
        acc["long_vowel"] += p["long_vowel_per_tok"] * p["_tokens"]
        acc["aspiration"] += p["aspiration_per_tok"] * p["_tokens"]
        acc["gemination"] += p["gemination_per_tok"] * p["_tokens"]
        low = t.lower()
        vnum += low.count("v")
        vden += low.count("v") + low.count("w")
    return {
        "v_vs_w": (vnum / vden) if vden else None,
        "long_vowel": acc["long_vowel"] / tot_tok,
        "aspiration": acc["aspiration"] / tot_tok,
        "gemination": acc["gemination"] / tot_tok,
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
            entry["methods"][method] = _mean_profile([hyps[i] for i in refs])
        report[corpus] = entry
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpora", nargs="+", default=["social_media", "swa_bhasha_words"])
    args = parser.parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report = analyze(args.corpora)
    (RESULTS_DIR / "error_analysis.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for corpus, e in report.items():
        print(f"\n=== {corpus} ===")
        print(f"  {'source':14s} v_vs_w  longV  asp   gem")
        rows = [("human", e["human"])] + list(e["methods"].items())
        for name, p in rows:
            vw = f"{p['v_vs_w']:.2f}" if p["v_vs_w"] is not None else " n/a"
            print(f"  {name:14s} {vw}   {p['long_vowel']:.2f}  {p['aspiration']:.2f}  {p['gemination']:.2f}")
