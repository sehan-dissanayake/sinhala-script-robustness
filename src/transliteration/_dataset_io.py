"""Shared JSONL dataset writer for transliteration methods."""

import json
from pathlib import Path
from typing import Callable

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


def process_datasets(method_name: str, fn: Callable[[str], str]) -> None:
    input_dir = PROJECT_ROOT / "data" / "processed"
    output_dir = PROJECT_ROOT / "data" / "romanized" / method_name
    for source_name, destination_name in (("sinhala_mmlu.jsonl", "sinhala_mmlu_romanized.jsonl"), ("sold.jsonl", "sold_romanized.jsonl")):
        source = input_dir / source_name
        if source.exists():
            count = _transform_file(source, output_dir / destination_name, fn)
            print(f"Transliterated {count} records -> {output_dir / destination_name}")