"""How far is our transliterator's output from what people actually type, and
does the difference make the downstream gap bigger or smaller?

The Romanized side of the downstream sets is produced by our transliterator
rather than typed by people. That is the main external-validity limit on the
downstream results, so this script measures it four ways, none of which needs
any new model inference.

  A. Aligned agreement. The intrinsic parallel corpus has a Romanized side that
     native speakers typed. We run our transliterator over its native side and
     compare word by word against what the humans wrote.

  B. Attestation. The Swa-bhasha word list records every Romanized spelling a
     human supplied for each Sinhala word, so a word usually has several
     accepted spellings. We measure how often our spelling is one of them, and
     we measure the same rate for the human-typed side of the parallel corpus.
     That second number is the reference point: it says how often a real
     person's spelling is attested, so it tells us whether our rate is unusual.

  C. Does the residual matter downstream? For SOLD, whose text we may
     redistribute, we score every item for attestation and ask whether the
     Romanized penalty concentrates on the items whose spellings are least
     human-like. This runs on the competent cohort, so it speaks to the
     checkpoints that actually carry the downstream result.

The direction and size of the residual error is measured separately, by scoring
our transliteration directly, in run_synthetic_vs_human.py.

Blocks B and C need the Swa-bhasha word list, which is not redistributed here.
Fetch it first with:
    python src/method_evaluation/download_reference_data.py
or place "Swa Bhasha D 1.txt" in data/reference/raw/swa_bhasha_adhoc/.
Block A runs from data already in the repository.

Run from the repository root:  python paper/analysis/stats_attestation.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "src", "transliteration"))

import numpy as np
import pandas as pd
from scipy import stats

import common as CM
from phonetic import transliterate

RNG = np.random.default_rng(20260902)
WORDLIST = os.path.join(CM.REPO, "data", "reference", "raw", "swa_bhasha_adhoc",
                        "Swa Bhasha D 1.txt")
PARALLEL = os.path.join(CM.REPO, "data", "raw", "intrinsic_evaluation_datasets",
                        "diverse_sentences.csv")

SINHALA = re.compile(r"^[\u0d80-\u0dff\u200c\u200d]+$")
STRIP = re.compile(r"^[^\w\u0d80-\u0dff]+|[^\w\u0d80-\u0dff]+$")
# Sinhala speakers write long vowels inconsistently. Collapsing runs of one
# Latin vowel removes that single convention from both sides of a comparison so
# the rest of the spelling can be judged on its own.
DOUBLE_VOWEL = re.compile(r"([aeiou])\1+", re.I)


def norm(w) -> str:
    return STRIP.sub("", unicodedata.normalize("NFC", str(w)).strip().casefold())


def collapse(w: str) -> str:
    return DOUBLE_VOWEL.sub(r"\1", w)


def cer(hyp: str, ref: str) -> float:
    """Character error rate, edit distance over reference length."""
    a, b = ref, hyp
    if not a:
        return 0.0 if not b else 1.0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1] / len(a)


def tokens(text) -> list[str]:
    return [t for t in unicodedata.normalize("NFC", str(text)).split() if t]


def align(native, rom_words: list[str]) -> list[tuple[str, str]]:
    """Pair each purely Sinhala native token with its Romanized counterpart.

    The transliterator is word preserving, so whitespace tokens line up. Pairs
    are dropped when the counts disagree, which happens when the source text
    itself contains stray spacing.
    """
    nat = tokens(native)
    if len(nat) != len(rom_words):
        return []
    out = []
    for n, r in zip(nat, rom_words):
        n = STRIP.sub("", unicodedata.normalize("NFC", n))
        if n and SINHALA.match(n) and r:
            out.append((n, r))
    return out


def load_parallel() -> pd.DataFrame:
    d = pd.read_csv(PARALLEL, encoding="utf-8-sig")
    d.columns = [c.lstrip("\ufeff") for c in d.columns]
    d["ours"] = [transliterate(str(s)) for s in d.sinhala_unicode]
    return d


# ------------------------------------------------------- the human lexicon ---
def load_lexicon() -> dict[str, set[str]] | None:
    """Sinhala word -> every Romanized spelling a human supplied for it."""
    if not os.path.exists(WORDLIST):
        print(f"[lexicon] missing {WORDLIST}; skipping blocks B and D")
        return None
    lex: dict[str, set[str]] = {}
    rows = 0
    with open(WORDLIST, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if "/" not in line:
                continue
            rom, sin = line.rsplit("/", 1)
            sin = STRIP.sub("", unicodedata.normalize("NFC", sin.strip()))
            rom = norm(rom)
            if not sin or not rom or not SINHALA.match(sin):
                continue
            rows += 1
            lex.setdefault(sin, set()).add(rom)
    print(f"[lexicon] {rows:,} usable pairs -> {len(lex):,} Sinhala words, "
          f"{sum(len(v) for v in lex.values()):,} accepted spellings")
    return lex


# -------------------------------------------------- A. agreement with humans -
def aligned_agreement(par: pd.DataFrame) -> dict:
    ok, mism, pairs, exact, exact_c = 0, 0, 0, 0, 0
    sent_cer, sent_cer_c = [], []
    for _, row in par.iterrows():
        a = [norm(w) for w in str(row.ours).split()]
        b = [norm(w) for w in str(row.sinhala_romanized).split()]
        a = [w for w in a if w]; b = [w for w in b if w]
        sent_cer.append(cer(" ".join(a), " ".join(b)))
        sent_cer_c.append(cer(collapse(" ".join(a)), collapse(" ".join(b))))
        if len(a) != len(b):
            mism += 1
            continue
        ok += 1
        for x, y in zip(a, b):
            pairs += 1
            exact += int(x == y)
            exact_c += int(collapse(x) == collapse(y))
    return {
        "n_sentences": int(len(par)),
        "n_sentences_word_aligned": ok,
        "n_sentences_token_count_mismatch": mism,
        "n_word_pairs": pairs,
        "word_exact_match_pct": 100.0 * exact / pairs,
        "word_exact_match_vowel_collapsed_pct": 100.0 * exact_c / pairs,
        "sentence_cer_mean": float(np.mean(sent_cer)),
        "sentence_cer_median": float(np.median(sent_cer)),
        "sentence_cer_vowel_collapsed_mean": float(np.mean(sent_cer_c)),
        "mismatch_profile": _mismatch_profile(par),
    }


# ----------------------------------------------------- B. attestation rates ---
def _attest(pairs: list[tuple[str, str]], lex) -> dict:
    cov = hit = hit_c = 0
    nref = []
    for s, r in pairs:
        acc = lex.get(s)
        if not acc:
            continue
        cov += 1
        nref.append(len(acc))
        hit += int(r in acc)
        hit_c += int(collapse(r) in {collapse(a) for a in acc})
    return {"n_tokens": len(pairs), "n_covered": cov,
            "coverage_pct": 100.0 * cov / max(1, len(pairs)),
            "attested_pct": 100.0 * hit / max(1, cov),
            "attested_vowel_collapsed_pct": 100.0 * hit_c / max(1, cov),
            "mean_accepted_spellings_per_covered_word": float(np.mean(nref)) if nref else float("nan")}


def attestation(par: pd.DataFrame, lex) -> dict:
    out = {"lexicon_words": len(lex),
           "lexicon_spellings": sum(len(v) for v in lex.values()),
           "lexicon_mean_spellings_per_word": float(np.mean([len(v) for v in lex.values()]))}

    ours, human = [], []
    for _, row in par.iterrows():
        uni = str(row.sinhala_unicode)
        ours += align(uni, [norm(w) for w in str(row.ours).split()])
        human += align(uni, [norm(w) for w in str(row.sinhala_romanized).split()])
    out["parallel_ours"] = _attest(ours, lex)
    out["parallel_human"] = _attest(human, lex)

    for ds in ("sold", "global_piqa"):
        p = os.path.join(CM.REPO, "data", "eval", f"{ds}.jsonl")
        if not os.path.exists(p):
            out[ds] = {"skipped": "eval file not redistributed"}
            continue
        pr = []
        for line in open(p, encoding="utf-8"):
            rec = json.loads(line)
            fields = [(rec["unicode"]["text"], rec["romanized"]["text"])]
            if "options" in rec["unicode"]:
                fields += list(zip(rec["unicode"]["options"], rec["romanized"]["options"]))
            for su, sr in fields:
                pr += align(su, [norm(w) for w in str(sr).split()])
        out[ds] = _attest(pr, lex)
    return out


# ------------------------------- C. which direction does the residual point? --
def _mismatch_profile(par: pd.DataFrame) -> dict:
    """Split every word-level disagreement with the humans into two channels.

    Channel one is the long-vowel writing convention, which our transliterator
    applies uniformly and people apply erratically. Channel two is everything
    else. Separating them matters because they have different consequences for
    a model: the first only changes vowel length, the second changes which
    string the model sees entirely.
    """
    exact = vowel_only = residual = 0
    res_counter: dict[tuple[str, str], int] = {}
    for _, row in par.iterrows():
        a = [w for w in (norm(w) for w in str(row.ours).split()) if w]
        b = [w for w in (norm(w) for w in str(row.sinhala_romanized).split()) if w]
        if len(a) != len(b):
            continue
        for x, y in zip(a, b):
            if x == y:
                exact += 1
            elif collapse(x) == collapse(y):
                vowel_only += 1
            else:
                residual += 1
                res_counter[(x, y)] = res_counter.get((x, y), 0) + 1
    tot = exact + vowel_only + residual
    top = sorted(res_counter.items(), key=lambda kv: -kv[1])[:25]
    return {"n_pairs": tot,
            "exact_pct": 100.0 * exact / tot,
            "vowel_convention_only_pct": 100.0 * vowel_only / tot,
            "residual_pct": 100.0 * residual / tot,
            "top_residual_mismatches": [
                {"ours": k[0], "human": k[1], "n": v} for k, v in top]}


# ------------------------- D. does attestation predict the SOLD penalty? -----
def downstream_dependence(lex) -> dict:
    p = os.path.join(CM.REPO, "data", "eval", "sold.jsonl")
    if not os.path.exists(p) or lex is None:
        return {"skipped": "needs sold.jsonl and the word list"}

    rows = []
    for line in open(p, encoding="utf-8"):
        rec = json.loads(line)
        cov = hit = 0
        for s, r in align(rec["unicode"]["text"],
                          [norm(w) for w in str(rec["romanized"]["text"]).split()]):
            acc = lex.get(s)
            if not acc:
                continue
            cov += 1
            hit += int(r in acc)
        rows.append({"id": rec["id"], "n_cov": cov,
                     "attest": hit / cov if cov else np.nan})
    A = pd.DataFrame(rows)

    NE = json.load(open(os.path.join(CM.OUT_DIR, "extrinsic_numbers.json")))
    cohort = NE["competent_models"]["sold"]
    frames = []
    for m in cohort:
        d = CM.load_items(m, "sold")
        uc = (d["unicode_pred"].astype(str) == d["label"].astype(str)) & CM.validity(d, "unicode", "sold")
        rc = (d["romanized_pred"].astype(str) == d["label"].astype(str)) & CM.validity(d, "romanized", "sold")
        frames.append(pd.DataFrame({"id": d["id"].astype(str), "model": m,
                                    "u": uc.astype(int), "r": rc.astype(int)}))
    P = pd.concat(frames, ignore_index=True).merge(A, on="id", how="left")
    P = P[P.n_cov >= 3].copy()

    q = P.groupby("id").attest.first().quantile([1 / 3, 2 / 3]).to_list()
    P["tercile"] = np.where(P.attest <= q[0], "low",
                            np.where(P.attest <= q[1], "mid", "high"))

    out = {"n_items_scored": int(P.id.nunique()), "cohort": cohort,
           "median_item_attestation_pct": float(P.groupby("id").attest.first().median() * 100)}
    for t in ("low", "mid", "high"):
        g = P[P.tercile == t]
        diff = (g.u - g.r).to_numpy(float)
        boot = diff[RNG.integers(0, len(diff), size=(4000, len(diff)))].mean(axis=1) * 100
        out[t] = {"n_items": int(g.id.nunique()),
                  "mean_attestation_pct": float(g.attest.mean() * 100),
                  "u_acc": float(g.u.mean() * 100), "r_acc": float(g.r.mean() * 100),
                  "gap": float((g.u.mean() - g.r.mean()) * 100),
                  "gap_lo": float(np.percentile(boot, 2.5)),
                  "gap_hi": float(np.percentile(boot, 97.5))}
    per_item = P.groupby("id").agg(attest=("attest", "first"), u=("u", "mean"),
                                   r=("r", "mean"))
    per_item["loss"] = per_item.u - per_item.r
    rho = stats.spearmanr(per_item.attest, per_item.loss)
    out["item_spearman_attest_vs_loss"] = {"rho": float(rho.statistic),
                                           "p": float(rho.pvalue), "n": int(len(per_item))}
    out["gap_range_across_terciles"] = float(
        max(out[t]["gap"] for t in ("low", "mid", "high"))
        - min(out[t]["gap"] for t in ("low", "mid", "high")))
    A.to_csv(os.path.join(CM.OUT_DIR, "sold_attestation.csv"), index=False)
    return out


def main():
    CM.ensure_dirs()
    par = load_parallel()
    lex = load_lexicon()
    out = {"aligned": aligned_agreement(par)}
    if lex is not None:
        out["attestation"] = attestation(par, lex)
        out["downstream"] = downstream_dependence(lex)
    with open(os.path.join(CM.OUT_DIR, "attestation_numbers.json"), "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
