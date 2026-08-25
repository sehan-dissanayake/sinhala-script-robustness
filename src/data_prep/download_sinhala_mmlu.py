"""Ingest or verify the full SinhalaMMLU dataset.

Note: The full SinhalaMMLU dataset is private (obtained with author permissions)
and is not downloaded from HuggingFace.

Collaborators: Place the unified `train.jsonl` (6,879 records) into
`data/raw/sinhala_mmlu/train.jsonl`.
"""

import json
import os
from pathlib import Path


def ingest_from_source_dir(source_dir: str | Path, output_file: str | Path) -> int:
    """Flatten and validate all TEST/*.json files from source directory into a single JSONL."""
    source_dir = Path(source_dir)
    test_dir = source_dir / "TEST" if (source_dir / "TEST").exists() else source_dir
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    records = []
    dropped_null = 0

    for diff in ["easy", "medium", "hard"]:
        diff_dir = test_dir / diff
        if not diff_dir.exists():
            continue
        for fpath in sorted(diff_dir.glob("*.json")):
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                ans = item.get("answer")
                if ans is None:
                    dropped_null += 1
                    print(f"  [skip] Dropping unanswerable item (answer=None): {fpath.name} q_no={item.get('q_no')}")
                    continue

                meta = dict(item.get("metadata") or {})
                meta["difficulty"] = diff.lower()

                records.append({
                    "q_no": item.get("q_no"),
                    "subject": item.get("subject"),
                    "category": item.get("category"),
                    "question": item.get("question"),
                    "choices": item.get("choices"),
                    "answer": ans,
                    "metadata": meta,
                })

    with open(output_file, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Ingested {len(records)} questions (dropped {dropped_null} null answers) -> {output_file}")
    return len(records)


def main():
    project_root = Path(__file__).resolve().parents[2]
    raw_dir = project_root / "data" / "raw" / "sinhala_mmlu"
    raw_file = raw_dir / "train.jsonl"
    source_dir = project_root / "full-sinhala-mmlu"

    if source_dir.exists():
        print(f"Found source dataset directory at {source_dir}. Ingesting...")
        ingest_from_source_dir(source_dir, raw_file)
    elif raw_file.exists():
        with open(raw_file, "r", encoding="utf-8") as f:
            count = sum(1 for line in f if line.strip())
        print(f"SinhalaMMLU dataset is already present at {raw_file} ({count:,} records).")
    else:
        print(f"WARNING: Neither {source_dir} nor {raw_file} found.")
        print("Please obtain the private `train.jsonl` file and place it at:")
        print(f"  {raw_file}")


if __name__ == "__main__":
    main()

