"""Download the Sinhala (sin_sinh) subset of Global PIQA (non-parallel split).

Global PIQA is a per-language benchmark: each language variety is its own config
of 100 hand-written examples, so only `sin_sinh` is fetched.

The dataset also ships a `sin_latn` config. That is a *separate, non-parallel*
Sinhala set written in Latin script by different contributors, not a
transliteration of `sin_sinh`. Using it would confound script with content, so
the Romanized condition is produced by our own transliterator (the same
phonetic method used for SinhalaMMLU and SOLD).

Licence note: Global PIQA is CC BY-SA 4.0 and evaluation-only; the upstream
authors explicitly disallow training on it or on synthetic data seeded from it.

    python src/data_prep/download_global_piqa.py
"""

import os

from datasets import load_dataset

REPO = "mrlbenchmarks/global-piqa-nonparallel"
CONFIG = "sin_sinh"


def main():
    print(f"Downloading Global PIQA ({CONFIG})...")
    ds = load_dataset(REPO, CONFIG)

    out_dir = os.path.join("data", "raw", "global_piqa")
    os.makedirs(out_dir, exist_ok=True)

    for split in ds.keys():
        out_path = os.path.join(out_dir, f"{split}.jsonl")
        ds[split].to_json(out_path, orient="records", lines=True, force_ascii=False)
        print(f"Saved {split} split ({ds[split].num_rows} rows) to {out_path}")

    print("Global PIQA download complete.")


if __name__ == "__main__":
    main()
