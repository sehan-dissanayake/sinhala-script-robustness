"""Draw a fixed-seed random sample from a (large) parallel corpus.

The augmented corpus has 7.2M sentence pairs. It is a *secondary* reference -
its romanizations are themselves machine-generated, so it measures agreement
with a generator as much as with human typing - and it is only used as a
cross-check on the conclusion drawn from the two primary corpora. A sample of a
few hundred thousand items gives a 95% CI on mean CER of roughly +/-0.0005,
i.e. statistically indistinguishable from scoring all 7.2M, at a fraction of the
compute. The sample is written as its own corpus so it gets its own cache and
never mixes with full-corpus artifacts.

    python -m sample_corpus --corpus augmented_sentences --n 300000 --seed 42
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PARALLEL_DIR = PROJECT_ROOT / "data" / "reference" / "parallel"


def sample(corpus: str, n: int, seed: int, suffix: str = "sample") -> Path:
    src = PARALLEL_DIR / f"{corpus}.jsonl"
    dst = PARALLEL_DIR / f"{corpus}_{suffix}.jsonl"

    total = sum(1 for _ in src.open(encoding="utf-8"))
    if n >= total:
        raise SystemExit(f"{corpus} has only {total:,} items; sampling {n:,} is pointless")

    rng = random.Random(seed)
    keep = set(rng.sample(range(total), n))

    written = 0
    with src.open(encoding="utf-8") as fin, dst.open("w", encoding="utf-8", newline="\n") as fout:
        for i, line in enumerate(fin):
            if i in keep:
                fout.write(line)
                written += 1
    print(f"{corpus}: sampled {written:,} of {total:,} (seed={seed}) -> {dst}")
    return dst


def subset_covered_by(corpus: str, method: str, suffix: str) -> Path:
    """Restrict a corpus to the items one method actually managed to romanize.

    The Nisansa endpoint refuses sustained volume, so it covers only part of the
    word corpus. Comparing methods requires identical items, so this carves out
    exactly the covered subset; every method is then scored on the same rows.
    """
    import json

    cache_path = (PROJECT_ROOT / "data" / "reference" / "cache" / corpus / f"{method}.json")
    covered = set(json.loads(cache_path.read_text(encoding="utf-8")))
    src = PARALLEL_DIR / f"{corpus}.jsonl"
    dst = PARALLEL_DIR / f"{corpus}_{suffix}.jsonl"
    kept = 0
    with src.open(encoding="utf-8") as fin, dst.open("w", encoding="utf-8", newline="\n") as fout:
        for line in fin:
            if json.loads(line)["sinhala"] in covered:
                fout.write(line)
                kept += 1
    print(f"{corpus}: kept {kept:,} items covered by {method} -> {dst}")
    return dst


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--n", type=int, default=300_000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--suffix", default="sample", help="output corpus is <corpus>_<suffix>")
    ap.add_argument("--covered-by", help="instead of sampling, keep items this method has cached")
    args = ap.parse_args()
    if args.covered_by:
        subset_covered_by(args.corpus, args.covered_by, args.suffix)
    else:
        sample(args.corpus, args.n, args.seed, args.suffix)
