"""Freeze the downstream-evaluation sets: one file per dataset, both script conditions.

Every available item is used - no sampling. Phase 2 selected the `phonetic`
transliterator, so each item is emitted once with its Unicode and Romanized forms
side by side:

    {
      "id": "mmlu_0123", "dataset": "sinhala_mmlu", "task": "mcq",
      "label": "C", "strata": {"domain": "Humanities"},
      "unicode":   {"text": ..., "options": [...]},
      "romanized": {"text": ..., "options": [...]}
    }

Pairing the two conditions in a single record is what makes the planned
McNemar test valid: the two script conditions are the same item, so the LLM
runner cannot accidentally score mismatched subsets against each other.

Few-shot exemplars come from explicit held-out pools (`*_heldout.jsonl`), never
from the evaluation set itself, and are label-balanced so demonstrations neither
leak test items nor skew the answer distribution. SinhalaMMLU releases only one
split, so it has no disjoint pool and must be run zero-shot. Zero-shot runs can
simply ignore data/eval/fewshot/.

    python src/data_prep/build_eval_sets.py
    python src/data_prep/build_eval_sets.py --method uroman
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
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
    fewshot_pool: str | None = None   # processed file to draw exemplars from
    fewshot_romanized: str | None = None


SPECS: tuple[EvalSpec, ...] = (
    EvalSpec("sinhala_mmlu", "sinhala_mmlu.jsonl", "sinhala_mmlu_romanized.jsonl",
             task="mcq", strata_fields=("domain", "difficulty"), labels=("A", "B", "C", "D")),
    EvalSpec("sold", "sold.jsonl", "sold_romanized.jsonl",
             task="binary", strata_fields=("label",), labels=("NOT", "OFF"),
             fewshot_pool="sold_heldout.jsonl",
             fewshot_romanized="sold_heldout_romanized.jsonl"),
    EvalSpec("global_piqa", "global_piqa.jsonl", "global_piqa_romanized.jsonl",
             task="mcq", strata_fields=("culturally_specific",), labels=("A", "B"),
             fewshot_pool="global_piqa_heldout.jsonl",
             fewshot_romanized="global_piqa_heldout_romanized.jsonl"),
)


# --------------------------------------------------------------------------- #
# Loading and validation
# --------------------------------------------------------------------------- #

def _read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _has_sinhala(text: str) -> bool:
    return any(SINHALA_START <= ch <= SINHALA_END for ch in text)


def load_paired(spec: EvalSpec, method: str, processed_name: str,
                romanized_name: str) -> list[dict]:
    """Join a processed file to its Romanized twin on `id`, validating both sides."""
    processed_path = PROCESSED_DIR / processed_name
    romanized_path = ROMANIZED_DIR / method / romanized_name
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


# --------------------------------------------------------------------------- #
# Stratified sampling
# --------------------------------------------------------------------------- #

def _stratum_key(record: dict, fields: tuple[str, ...]) -> str:
    return "|".join(f"{f}={record['strata'][f]}" for f in fields
                    if f in record["strata"])


def _effective_fields(records: list[dict], fields: tuple[str, ...]) -> tuple[str, ...]:
    """Drop strata fields that take a single value across the corpus.

    SinhalaMMLU's only released split labels every question `difficulty=Easy`, so
    stratifying on it does nothing; saying so beats silently pretending the
    sample is balanced on difficulty.
    """
    keep = []
    for field in fields:
        values = {r["strata"][field] for r in records if field in r["strata"]}
        if len(values) > 1:
            keep.append(field)
        else:
            print(f"  note: strata field {field!r} is constant "
                  f"({values or 'absent'}), excluded from stratification")
    return tuple(keep)


def label_balanced_sample(records: list[dict], k: int, labels: tuple[str, ...],
                          seed: int) -> list[dict]:
    """Pick k exemplars spread as evenly as possible over the label values."""
    by_label: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_label[record["label"]].append(record)

    rng = random.Random(seed)
    picked: list[dict] = []
    present = [lab for lab in labels if by_label[lab]]
    if not present:
        return []
    per_label = k // len(present)
    extra = k - per_label * len(present)
    for i, label in enumerate(present):
        want = per_label + (1 if i < extra else 0)
        pool = sorted(by_label[label], key=lambda r: r["id"])
        picked.extend(rng.sample(pool, min(want, len(pool))))
    rng.shuffle(picked)         # avoid a fixed label order in the prompt
    return picked


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


def build(method: str, seed: int, fewshot_k: int) -> None:
    manifest = {
        "transliteration_method": method,
        "seed": seed,
        "fewshot_k": fewshot_k,
        "sampling": "none: every available item is evaluated",
        "script_conditions": ["unicode", "romanized"],
        "datasets": {},
    }

    for spec in SPECS:
        print(f"\n=== {spec.name} ===")
        records = load_paired(spec, method, spec.processed, spec.romanized)
        fields = _effective_fields(records, spec.strata_fields)
        eval_ids = {r["id"] for r in records}

        path = OUT_DIR / f"{spec.name}.jsonl"
        digest = write_jsonl(records, path)
        strata_counts = Counter(_stratum_key(r, fields) or "all" for r in records)
        label_counts = Counter(r["label"] for r in records)
        print(f"  all {len(records):,} items -> {path.relative_to(PROJECT_ROOT)}")
        print(f"  labels: {dict(sorted(label_counts.items()))}")
        print(f"  strata: {dict(sorted(strata_counts.items()))}")

        # Few-shot exemplars come from a held-out pool only. Because the eval set
        # is now the whole dataset, there is no leftover to fall back on: a
        # dataset without a pool has to be run zero-shot rather than quietly
        # demonstrating with items it is scored on.
        if spec.fewshot_pool:
            pool = load_paired(spec, method, spec.fewshot_pool, spec.fewshot_romanized)
            pool_source = spec.fewshot_pool
        else:
            pool, pool_source = [], None

        exemplars = label_balanced_sample(pool, fewshot_k, spec.labels, seed)
        overlap = eval_ids & {r["id"] for r in exemplars}
        if overlap:
            raise SystemExit(f"{spec.name}: exemplars overlap the eval set: {sorted(overlap)}")

        fewshot_digest = fewshot_path = None
        if exemplars:
            fewshot_path = OUT_DIR / "fewshot" / f"{spec.name}.jsonl"
            fewshot_digest = write_jsonl(exemplars, fewshot_path)
            print(f"  {len(exemplars)} few-shot exemplars from {len(pool):,}-item "
                  f"held-out pool -> {fewshot_path.relative_to(PROJECT_ROOT)}")
        else:
            print("  no held-out exemplar pool: this dataset must be run zero-shot")

        manifest["datasets"][spec.name] = {
            "task": spec.task,
            "file": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "sha256": digest,
            "n": len(records),
            "strata_fields": list(fields),
            "strata_counts": dict(sorted(strata_counts.items())),
            "label_counts": dict(sorted(label_counts.items())),
            "fewshot": {
                "file": (str(fewshot_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
                         if fewshot_path else None),
                "sha256": fewshot_digest,
                "n": len(exemplars),
                "pool": pool_source,
                "pool_size": len(pool),
            },
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
    parser.add_argument("--seed", type=int, default=42,
                        help="seed for few-shot exemplar selection only; the eval sets "
                             "are complete and involve no randomness")
    parser.add_argument("--fewshot-k", type=int, default=8)
    args = parser.parse_args()

    build(method=args.method, seed=args.seed, fewshot_k=args.fewshot_k)
