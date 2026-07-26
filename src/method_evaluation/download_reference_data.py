"""Download the reference Sinhala<->Romanized-Sinhala parallel corpora.

Sources (Swa-bhasha Resource Hub, Sumanathilaka et al.):
  * Kaggle  tgdeshank/romanized-sinhala-sinhala-social-media-dataset  (sentence pairs, authentic)
  * Kaggle  tgdeshank/swa-bhasha-dataset                              (word-level adhoc transliterals)
  * HF      deshanksuman/Augmented_SinhalatoRomanizedSinhala_Dataset  (sentence pairs, augmented)
  * HF      deshanksuman/Swabhasha_RomanizedSinhala_Dataset           (word-level lexicon)

Downloads only. Normalisation into a common schema happens in build_parallel_corpus.py.
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "reference" / "raw"

# Ensure Kaggle reads credentials from the project root (kaggle.json lives there, git-ignored).
os.environ.setdefault("KAGGLE_CONFIG_DIR", str(PROJECT_ROOT))

KAGGLE_DATASETS = {
    "social_media": "tgdeshank/romanized-sinhala-sinhala-social-media-dataset",
    "swa_bhasha_adhoc": "tgdeshank/swa-bhasha-dataset",
}

HF_DATASETS = {
    "augmented_sentences": "deshanksuman/Augmented_SinhalatoRomanizedSinhala_Dataset",
    "lexicon_words": "deshanksuman/Swabhasha_RomanizedSinhala_Dataset",
}


def download_kaggle() -> None:
    import kaggle

    api = kaggle.KaggleApi()
    api.authenticate()
    for name, ref in KAGGLE_DATASETS.items():
        dest = RAW_DIR / name
        dest.mkdir(parents=True, exist_ok=True)
        print(f"[kaggle] {ref} -> {dest}")
        api.dataset_download_files(ref, path=str(dest), unzip=True, quiet=False)


def download_hf() -> None:
    from datasets import load_dataset

    for name, ref in HF_DATASETS.items():
        dest = RAW_DIR / name
        dest.mkdir(parents=True, exist_ok=True)
        print(f"[hf] {ref} -> {dest}")
        ds = load_dataset(ref, split="train")
        out = dest / "data.jsonl"
        ds.to_json(str(out), orient="records", lines=True, force_ascii=False)
        print(f"       wrote {out} ({len(ds)} rows)")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["kaggle", "hf", "all"], default="all")
    args = parser.parse_args()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if args.source in ("kaggle", "all"):
        download_kaggle()
    if args.source in ("hf", "all"):
        download_hf()
    print("Done.")
