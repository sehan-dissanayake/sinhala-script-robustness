"""Freeze the downstream-evaluation sets: one file per dataset, both script conditions.

Every available item is used - no sampling, no few-shot exemplars (all three
datasets are run zero-shot, so no dataset gets a prompting advantage the others
don't). Phase 2 selected the `phonetic` transliterator, so each item is emitted
once with its Unicode and Romanized forms side by side:

    {
      "id": "mmlu_0123", "dataset": "sinhala_mmlu", "task": "mcq",
      "label": "C", "strata": {"domain": "Humanities"},
      "unicode":   {"text": ..., "options": [...]},
      "romanized": {"text": ..., "options": [...]}
    }

Pairing the two conditions in a single record is what makes the planned
McNemar test valid: the two script conditions are the same item, so the LLM
runner cannot accidentally score mismatched subsets against each other.

    python src/data_prep/build_eval_sets.py
    python src/data_prep/build_eval_sets.py --method uroman
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
ROMANIZED_DIR = PROJECT_ROOT / "data" / "romanized"
OUT_DIR = PROJECT_ROOT / "data" / "eval"

SINHALA_START, SINHALA_END = "\u0d80", "\u0dff"


@dataclass(frozen=True)
class EvalSpec:
    name: str
    processed: str
    romanized: str
    task: str                    # "mcq" | "binary"
    strata_fields: tuple[str, ...]
    labels: tuple[str, ...]


SPECS: tuple[EvalSpec, ...] = (
    EvalSpec("sinhala_mmlu", "sinhala_mmlu.jsonl", "sinhala_mmlu_romanized.jsonl",
             task="mcq", strata_fields=("domain", "difficulty"), labels=("A", "B", "C", "D")),
    EvalSpec("sold", "sold.jsonl", "sold_romanized.jsonl",
             task="binary", strata_fields=("label",), labels=("NOT", "OFF")),
    EvalSpec("global_piqa", "global_piqa.jsonl", "global_piqa_romanized.jsonl",
             task="mcq", strata_fields=("culturally_specific",), labels=("A", "B")),
)


# --------------------------------------------------------------------------- #
# Loading and validation
# --------------------------------------------------------------------------- #

def _read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _has_sinhala(text: str) -> bool:
    return any(SINHALA_START <= ch <= SINHALA_END for ch in text)


def load_paired(spec: EvalSpec, method: str) -> list[dict]:
    """Join a processed file to its Romanized twin on `id`, validating both sides."""
    processed_path = PROCESSED_DIR / spec.processed
    romanized_path = ROMANIZED_DIR / method / spec.romanized
    for path in (processed_path, romanized_path):
        if not path.exists():
            raise SystemExit(
                f"missing {path}\nRun src/data_prep/prepare_datasets.py and "
                f"src/transliteration/{method}.py first."
            )

    romanized = {r["id"]: r for r in _read_jsonl(romanized_path)}
    paired = []
    for base in _read_jsonl(processed_path):
        rid = base["id"]
        rom = romanized.get(rid)
        if rom is None:
            raise SystemExit(f"{rid}: present in {processed_path.name} but not in "
                             f"{romanized_path.name}; re-run the transliterator")

        text_uni, text_rom = base["text_unicode"], rom["text_romanized"]
        if not _has_sinhala(text_uni):
            raise SystemExit(f"{rid}: Unicode side contains no Sinhala")
        if not text_rom.strip():
            raise SystemExit(f"{rid}: Romanized side is empty")
        if _has_sinhala(text_rom):
            raise SystemExit(f"{rid}: Sinhala leaked into the Romanized side")

        record = {
            "id": rid,
            "dataset": spec.name,
            "task": spec.task,
            "label": base["label"],
            "strata": {f: base[f] for f in spec.strata_fields if f in base},
            "unicode": {"text": text_uni},
            "romanized": {"text": text_rom},
        }

        if spec.task == "mcq":
            options_uni = base["options"]
            options_rom = rom["options_romanized"]
            if len(options_uni) != len(options_rom):
                raise SystemExit(f"{rid}: {len(options_uni)} options but "
                                 f"{len(options_rom)} Romanized options")
            if any(_has_sinhala(o) for o in options_rom):
                raise SystemExit(f"{rid}: Sinhala leaked into a Romanized option")
            if base["label"] not in spec.labels[:len(options_uni)]:
                raise SystemExit(f"{rid}: label {base['label']!r} does not index "
                                 f"{len(options_uni)} options")
            record["unicode"]["options"] = options_uni
            record["romanized"]["options"] = options_rom
            record["n_options"] = len(options_uni)
        elif base["label"] not in spec.labels:
            raise SystemExit(f"{rid}: label {base['label']!r} not in {spec.labels}")

        # Carry through the extra Global PIQA metadata that error analysis wants.
        for extra in ("example_id", "culturally_specific", "llm_assisted",
                      "eng_options", "domain", "difficulty"):
            if extra in base and extra not in record["strata"]:
                record[extra] = base[extra]

        paired.append(record)
    return paired


def _stratum_key(record: dict, fields: tuple[str, ...]) -> str:
    return "|".join(f"{f}={record['strata'][f]}" for f in fields
                    if f in record["strata"])


def _effective_fields(records: list[dict], fields: tuple[str, ...]) -> tuple[str, ...]:
    """Drop strata fields that take a single value across the corpus.

    SinhalaMMLU's only released split labels every question `difficulty=Easy`, so
    reporting a breakdown by it would imply information that isn't there.
    """
    keep = []
    for field in fields:
        values = {r["strata"][field] for r in records if field in r["strata"]}
        if len(values) > 1:
            keep.append(field)
        else:
            print(f"  note: strata field {field!r} is constant "
                  f"({values or 'absent'}), excluded from the reported breakdown")
    return tuple(keep)


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #

def write_jsonl(records: list[dict], path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for record in records:
            line = json.dumps(record, ensure_ascii=False) + "\n"
            fh.write(line)
            digest.update(line.encode("utf-8"))
    return digest.hexdigest()


def build(method: str) -> None:
    manifest = {
        "transliteration_method": method,
        "sampling": "none: every available item is evaluated",
        "prompting": "zero-shot only",
        "script_conditions": ["unicode", "romanized"],
        "datasets": {},
    }

    for spec in SPECS:
        print(f"\n=== {spec.name} ===")
        records = load_paired(spec, method)
        fields = _effective_fields(records, spec.strata_fields)

        path = OUT_DIR / f"{spec.name}.jsonl"
        digest = write_jsonl(records, path)
        strata_counts = Counter(_stratum_key(r, fields) or "all" for r in records)
        label_counts = Counter(r["label"] for r in records)
        print(f"  all {len(records):,} items -> {path.relative_to(PROJECT_ROOT)}")
        print(f"  labels: {dict(sorted(label_counts.items()))}")
        print(f"  strata: {dict(sorted(strata_counts.items()))}")

        manifest["datasets"][spec.name] = {
            "task": spec.task,
            "file": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "sha256": digest,
            "n": len(records),
            "strata_fields": list(fields),
            "strata_counts": dict(sorted(strata_counts.items())),
            "label_counts": dict(sorted(label_counts.items())),
        }

    manifest_path = OUT_DIR / "manifest.json"
    with manifest_path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    total = sum(d["n"] for d in manifest["datasets"].values())
    print(f"\n{total:,} items x 2 script conditions = {total * 2:,} prompts per model")
    print(f"Wrote {manifest_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--method", default="phonetic",
                        help="transliteration method under data/romanized/ (default: the "
                             "phase-2 winner, phonetic)")
    args = parser.parse_args()

    build(method=args.method)
