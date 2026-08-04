"""Derive a `nisansa_w` variant: Nisansa's output with every v rewritten as w.

The convention analysis showed Nisansa matches the phonetic method on long
vowels, aspiration and gemination, and differs almost only in writing ව as `v`
where humans overwhelmingly write `w` (human v-share is 0.01 on the word corpus
and 0.20 on social media, against Nisansa's 1.00). This isolates that one
variable: if the v/w convention were the whole story, `nisansa_w` should close
the gap to phonetic.

The rewrite is unambiguous on this data: `w` occurs in 159 of 449,117 Nisansa
outputs (0.03%), so there is nothing for a v->w mapping to collide with.

This is a *modified* method, not the Nisansa tool as published, and is reported
as such. No network access is needed - it is a pure post-process of the cached
results.

    python derive_nisansa_w.py --corpora social_media swa_bhasha_words
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRANSLIT_DIR = PROJECT_ROOT / "data" / "reference" / "transliterated"

SOURCE = "nisansa_sirs_method"
DERIVED = "nisansa_w"


def to_w(text: str) -> str:
    """Rewrite the v/w convention, preserving case."""
    return text.replace("v", "w").replace("V", "W")


def derive(corpus: str) -> None:
    src = TRANSLIT_DIR / corpus / f"{SOURCE}.jsonl"
    if not src.exists():
        print(f"{corpus}: no {SOURCE} output, skipping")
        return
    dst = TRANSLIT_DIR / corpus / f"{DERIVED}.jsonl"
    n = changed = 0
    with src.open(encoding="utf-8") as fin, dst.open("w", encoding="utf-8", newline="\n") as fout:
        for line in fin:
            rec = json.loads(line)
            new = to_w(rec["hypothesis"])
            changed += new != rec["hypothesis"]
            n += 1
            fout.write(json.dumps({"id": rec["id"], "sinhala": rec["sinhala"],
                                   "hypothesis": new}, ensure_ascii=False) + "\n")
    print(f"{corpus}: wrote {n:,} items ({changed:,} rewritten) -> {dst.name}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpora", nargs="+", default=["social_media", "swa_bhasha_words"])
    args = ap.parse_args()
    for c in args.corpora:
        derive(c)
