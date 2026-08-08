"""Download the Sinhala (sin_sinh) subset of Global PIQA (non-parallel split).

Global PIQA is a per-language benchmark: each language variety is its own config
of 100 hand-written examples, so only `sin_sinh` is fetched.

The dataset also ships a `sin_latn` config. That is a *separate, non-parallel*
Sinhala set written in Latin script by different contributors, not a
transliteration of `sin_sinh`. Using it would confound script with content, so
the Romanized condition is produced by our own transliterator (the same
phonetic method used for SinhalaMMLU and SOLD).

Two files are saved:
    test.jsonl            the official 100-item evaluation set (config `sin_sinh`)
    unsampled_full.jsonl  the 110-item contributed pool the official set was
                          sampled from. Rows in this pool that are absent from
                          the official set give us a few-shot exemplar source
                          that is disjoint from the evaluation set; without it
                          any Global PIQA few-shot prompt would leak test items.

Licence note: Global PIQA is CC BY-SA 4.0 and evaluation-only; the upstream
authors explicitly disallow training on it or on synthetic data seeded from it.

    python src/data_prep/download_global_piqa.py
"""

import csv
import json
import os

from datasets import load_dataset
from huggingface_hub import hf_hub_download

REPO = "mrlbenchmarks/global-piqa-nonparallel"
CONFIG = "sin_sinh"
UNSAMPLED_PATH = f"unsampled_full/unsampled_nonparallel_{CONFIG}.tsv"


def _save_unsampled_pool(out_dir):
    """Copy the contributed pool TSV into our raw layout as JSONL."""
    src = hf_hub_download(REPO, UNSAMPLED_PATH, repo_type="dataset")
    with open(src, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    out_path = os.path.join(out_dir, "unsampled_full.jsonl")
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Saved contributed pool ({len(rows)} rows) to {out_path}")


def main():
    print(f"Downloading Global PIQA ({CONFIG})...")
    ds = load_dataset(REPO, CONFIG)

    out_dir = os.path.join("data", "raw", "global_piqa")
    os.makedirs(out_dir, exist_ok=True)

    for split in ds.keys():
        out_path = os.path.join(out_dir, f"{split}.jsonl")
        ds[split].to_json(out_path, orient="records", lines=True, force_ascii=False)
        print(f"Saved {split} split ({ds[split].num_rows} rows) to {out_path}")

    _save_unsampled_pool(out_dir)
    print("Global PIQA download complete.")


if __name__ == "__main__":
    main()
