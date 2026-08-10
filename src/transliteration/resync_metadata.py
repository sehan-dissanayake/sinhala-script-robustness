"""Refresh the non-Romanized fields of a romanized dataset from data/processed/.

Romanized files are copies of the processed records plus `text_romanized` (and
`options_romanized`), so any correction to a label or a metadata field in
data/processed/ leaves them stale. For the local methods the fix is simply to
re-run them. The Nisansa method costs one HTTP request per string (~4,500 for
the full set), so re-fetching unchanged text to pick up a label fix is wasteful
and rude to a third-party endpoint.

This script copies every field except the Romanized ones from the processed
record onto the existing romanized record, and refuses to touch a file whose
Sinhala text no longer matches - if the source text changed, the romanization is
genuinely out of date and the method must actually be re-run.

    python src/transliteration/resync_metadata.py --method nisansa_sirs_method
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from ._dataset_io import DATASET_FILES, DATASET_NAMES, PROJECT_ROOT
except ImportError:  # Direct execution
    from _dataset_io import DATASET_FILES, DATASET_NAMES, PROJECT_ROOT

ROMANIZED_KEYS = ("text_romanized", "options_romanized")


def resync_file(processed: Path, romanized: Path) -> tuple[int, int]:
    with processed.open(encoding="utf-8") as fh:
        base = {json.loads(line)["id"]: json.loads(line) for line in fh if line.strip()}

    updated = changed = 0
    lines: list[str] = []
    with romanized.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            record = json.loads(line)
            source = base.get(record["id"])
            if source is None:
                raise SystemExit(f"{record['id']} is in {romanized.name} but not "
                                 f"{processed.name}; re-run the transliterator")
            if source["text_unicode"] != record["text_unicode"]:
                raise SystemExit(
                    f"{record['id']}: Sinhala text differs between {processed.name} "
                    f"and {romanized.name}. The romanization is stale, not just the "
                    f"metadata - re-run the transliterator instead."
                )
            merged = {k: v for k, v in source.items()}
            merged.update({k: record[k] for k in ROMANIZED_KEYS if k in record})
            changed += merged != record
            updated += 1
            lines.append(json.dumps(merged, ensure_ascii=False) + "\n")

    temporary = romanized.with_suffix(romanized.suffix + ".tmp")
    temporary.write_text("".join(lines), encoding="utf-8", newline="\n")
    temporary.replace(romanized)
    return updated, changed


def main(method: str, datasets: list[str] | None) -> None:
    processed_dir = PROJECT_ROOT / "data" / "processed"
    romanized_dir = PROJECT_ROOT / "data" / "romanized" / method
    for source_name, destination_name in DATASET_FILES:
        if datasets and source_name.removesuffix(".jsonl") not in datasets:
            continue
        processed, romanized = processed_dir / source_name, romanized_dir / destination_name
        if not (processed.exists() and romanized.exists()):
            continue
        n, changed = resync_file(processed, romanized)
        print(f"{destination_name}: {n:,} records checked, {changed:,} updated")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--method", required=True, help="directory under data/romanized/")
    parser.add_argument("--datasets", nargs="+", choices=list(DATASET_NAMES),
                        help="limit to these processed datasets (default: all)")
    args = parser.parse_args()
    main(args.method, args.datasets)
