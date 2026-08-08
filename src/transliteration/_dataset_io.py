"""Shared JSONL dataset writer for transliteration methods."""

import json
from pathlib import Path
from typing import Callable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SINHALA_START = "\u0d80"
SINHALA_END = "\u0dff"


def _validate_output(value: str, record_id: str) -> None:
    leaked = sorted({char for char in value if SINHALA_START <= char <= SINHALA_END})
    if leaked:
        rendered = " ".join(f"{char} (U+{ord(char):04X})" for char in leaked)
        raise ValueError(f"Sinhala leakage in {record_id}: {rendered}")


def _transform_file(source: Path, destination: Path, fn: Callable[[str], str]) -> int:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    count = 0
    try:
        with source.open(encoding="utf-8") as reader, temporary.open("w", encoding="utf-8", newline="\n") as writer:
            for line_number, line in enumerate(reader, 1):
                record = json.loads(line)
                record_id = str(record.get("id", f"line {line_number}"))
                text = record.get("text_unicode")
                if not isinstance(text, str):
                    raise TypeError(f"{source}:{line_number}: text_unicode must be a string")
                record["text_romanized"] = fn(text)
                _validate_output(record["text_romanized"], record_id)
                if "options" in record:
                    if not isinstance(record["options"], list) or not all(isinstance(x, str) for x in record["options"]):
                        raise TypeError(f"{source}:{line_number}: options must be a list of strings")
                    record["options_romanized"] = [fn(option) for option in record["options"]]
                    for option in record["options_romanized"]:
                        _validate_output(option, record_id)
                writer.write(json.dumps(record, ensure_ascii=False) + "\n")
                count += 1
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return count


DATASET_FILES = (
    ("sinhala_mmlu.jsonl", "sinhala_mmlu_romanized.jsonl"),
    ("sold.jsonl", "sold_romanized.jsonl"),
    ("global_piqa.jsonl", "global_piqa_romanized.jsonl"),
    # Held-out rows, used only as few-shot exemplar pools. They need the same
    # Romanized twin as the evaluation items so an exemplar is never shown in a
    # different script from the item being scored.
    ("sold_heldout.jsonl", "sold_heldout_romanized.jsonl"),
    ("global_piqa_heldout.jsonl", "global_piqa_heldout_romanized.jsonl"),
)


DATASET_NAMES = tuple(source.removesuffix(".jsonl") for source, _ in DATASET_FILES)


def process_datasets(method_name: str, fn: Callable[[str], str],
                     datasets: Sequence[str] | None = None) -> None:
    """Romanize every processed dataset (or only the named ones) with `fn`.

    `datasets` exists so a single dataset can be regenerated without recomputing
    the rest. That matters for the network-bound Nisansa method, where the full
    set is thousands of requests to a third-party endpoint.
    """
    if datasets:
        unknown = sorted(set(datasets) - set(DATASET_NAMES))
        if unknown:
            raise ValueError(f"unknown dataset(s) {unknown}; choose from {list(DATASET_NAMES)}")
    input_dir = PROJECT_ROOT / "data" / "processed"
    output_dir = PROJECT_ROOT / "data" / "romanized" / method_name
    for source_name, destination_name in DATASET_FILES:
        if datasets and source_name.removesuffix(".jsonl") not in datasets:
            continue
        source = input_dir / source_name
        if source.exists():
            count = _transform_file(source, output_dir / destination_name, fn)
            print(f"Transliterated {count} records -> {output_dir / destination_name}")


def cli(method_name: str, fn: Callable[[str], str]) -> None:
    """Entry point for `python src/transliteration/<method>.py [--datasets ...]`."""
    import argparse

    parser = argparse.ArgumentParser(description=f"Romanize the processed datasets with {method_name}.")
    parser.add_argument("--datasets", nargs="+", choices=list(DATASET_NAMES),
                        help="limit the run to these processed datasets (default: all)")
    args = parser.parse_args()
    process_datasets(method_name, fn, args.datasets)