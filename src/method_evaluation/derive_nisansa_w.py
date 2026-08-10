"""The v->w preprocessing stage for the Nisansa method.

The endpoint writes ව as `v`; Sinhala speakers typing Singlish overwhelmingly
write `w` (human v-share is 0.01 on the word corpus and 0.20 on social media,
against Nisansa's 1.00). That single orthographic choice, not romanization
quality, accounted for its entire measured gap to the phonetic method, so the
rewrite is applied as a standard preprocessing step before scoring and
`nisansa_w` is the Nisansa variant reported in the headline results.

The rewrite is unambiguous on this data: `w` occurs in ~0.03% of Nisansa
outputs, so there is nothing for a v->w mapping to collide with. `apply_to` logs
the collision count each time so that stays verifiable rather than assumed.

It is still a *modified* method rather than the tool as published, and both rows
are reported side by side so the distinction is visible. No network access is
needed - it is a pure post-process of fetched results, and `nisansa_shards.py
merge` calls it automatically. Run it directly for a corpus that has no shard
set, such as social_media:

    python derive_nisansa_w.py --corpora social_media
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


def apply_to(records) -> tuple[list[dict], dict]:
    """Apply the rewrite to hypothesis records, returning them and a stats dict.

    `collisions` counts outputs that already contained a `w`. The rewrite is only
    safe to treat as isolating the v/w convention while that stays negligible, so
    it is measured on every run instead of taken on trust.
    """
    out, changed, collisions, empty = [], 0, 0, 0
    for rec in records:
        hyp = rec["hypothesis"]
        new = to_w(hyp)
        changed += new != hyp
        collisions += "w" in hyp or "W" in hyp
        empty += not hyp
        out.append({"id": rec["id"], "sinhala": rec["sinhala"], "hypothesis": new})
    return out, {"n": len(out), "changed": changed, "collisions": collisions, "empty": empty}


def write_variant(corpus: str, records: list[dict]) -> Path:
    dst = TRANSLIT_DIR / corpus / f"{DERIVED}.jsonl"
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("w", encoding="utf-8", newline="\n") as fout:
        for rec in records:
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return dst


def derive(corpus: str) -> None:
    src = TRANSLIT_DIR / corpus / f"{SOURCE}.jsonl"
    if not src.exists():
        print(f"{corpus}: no {SOURCE} output, skipping")
        return
    with src.open(encoding="utf-8") as fin:
        records = [json.loads(line) for line in fin]
    out, stats = apply_to(records)
    dst = write_variant(corpus, out)
    print(f"{corpus}: wrote {stats['n']:,} items -> {dst.name} "
          f"({stats['changed']:,} rewritten, {stats['collisions']:,} already contained w, "
          f"{stats['empty']:,} empty)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpora", nargs="+", default=["social_media", "swa_bhasha_words"],
                    help="corpora to preprocess; `nisansa_shards.py merge` does this "
                         "automatically for sharded corpora")
    args = ap.parse_args()
    for c in args.corpora:
        derive(c)
