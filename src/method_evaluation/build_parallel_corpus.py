"""Normalise the raw reference corpora into one common JSONL schema.

Output schema (one JSON object per line):
    {
        "id":         "<source>_<n>",
        "source":     "social_media" | "swa_bhasha_words" | "augmented_sentences",
        "level":      "sentence" | "word",
        "sinhala":    "<NFC Sinhala text>",
        "references": ["<human romanization>", ...]   # >=1 accepted variant
    }

Grouping by the Sinhala side lets word-level sources expose *multiple* accepted
romanizations (multi-reference), which is essential for scoring deterministic
methods against non-standard "Singlish".
"""

import json
import sys
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "reference" / "raw"
OUT_DIR = PROJECT_ROOT / "data" / "reference" / "parallel"

SINHALA_START, SINHALA_END = "\u0d80", "\u0dff"

# The set of linguistically valid Sinhala characters, taken from the phonetic
# mapper. Some corpus rows contain unassigned codepoints (e.g. U+0DFE/U+0DFF)
# that are data corruption; entries containing them are dropped so every method
# is scored on identical, clean input.
sys.path.insert(0, str(PROJECT_ROOT / "src" / "transliteration"))
import phonetic as _phonetic  # noqa: E402

_VALID_SINHALA = (
    set(_phonetic.INDEPENDENT_VOWELS)
    | set(_phonetic.CONSONANTS)
    | set(_phonetic.VOWEL_SIGNS)
    | set(_phonetic.SPECIAL_SIGNS)
    | {_phonetic.VIRAMA}
    | _phonetic.JOINERS
    | {"\u0df3", "\u0df4"}  # kunddaliya / punctuation
)


def _has_sinhala(text: str) -> bool:
    return any(SINHALA_START <= ch <= SINHALA_END for ch in text)


def _is_valid_sinhala(text: str) -> bool:
    return all(
        not (SINHALA_START <= ch <= SINHALA_END) or ch in _VALID_SINHALA
        for ch in text
    )


def _clean(text: str) -> str:
    return unicodedata.normalize("NFC", text.strip().strip('"').strip())


def build_social_media() -> list[dict]:
    """Authentic social-media sentence pairs (UTF-16, tab-delimited, quoted)."""
    src = RAW_DIR / "social_media" / "Romanized Sinhala- sinhala cleaned data.txt"
    text = src.read_bytes().decode("utf-16")
    records: list[dict] = []
    for i, line in enumerate(text.splitlines()):
        tokens = [t.strip() for t in line.split("\t")]
        tokens = [t for t in tokens if t and t.strip('"').strip()]
        if len(tokens) < 2:
            continue
        romanized = _clean(tokens[0])
        sinhala = next((_clean(t) for t in reversed(tokens) if _has_sinhala(t)), "")
        if not sinhala or not romanized or not _has_sinhala(sinhala):
            continue
        if not _is_valid_sinhala(sinhala):
            continue
        # Reference must contain Latin letters (the romanization), not be pure Sinhala.
        if not any(c.isascii() and c.isalpha() for c in romanized):
            continue
        records.append({
            "id": f"social_media_{i}",
            "source": "social_media",
            "level": "sentence",
            "sinhala": sinhala,
            "references": [romanized],
        })
    return records


def build_swa_bhasha_words() -> list[dict]:
    """Word-level adhoc transliterals: many romanizations per Sinhala word."""
    src = RAW_DIR / "swa_bhasha_adhoc" / "Swa Bhasha D 1.txt"
    groups: dict[str, list[str]] = {}
    order: list[str] = []
    with src.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if "/" not in line:
                continue
            romanized, sinhala = line.rsplit("/", 1)
            romanized = _clean(romanized)
            sinhala = _clean(sinhala)
            if not sinhala or not romanized or not _has_sinhala(sinhala):
                continue
            if not _is_valid_sinhala(sinhala):
                continue
            if sinhala not in groups:
                groups[sinhala] = []
                order.append(sinhala)
            if romanized not in groups[sinhala]:
                groups[sinhala].append(romanized)
    return [
        {
            "id": f"swa_bhasha_words_{i}",
            "source": "swa_bhasha_words",
            "level": "word",
            "sinhala": sinhala,
            "references": groups[sinhala],
        }
        for i, sinhala in enumerate(order)
    ]


def build_augmented_sentences():
    """Large augmented sentence pairs (HF). Streamed to avoid buffering 7.2M rows."""
    src = RAW_DIR / "augmented_sentences" / "data.jsonl"
    if not src.exists():
        return
    with src.open(encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            row = json.loads(line)
            sinhala = _clean(row.get("Sinhala") or "")
            romanized = _clean(row.get("RomanizedSinhala") or "")
            if not sinhala or not romanized or not _has_sinhala(sinhala):
                continue
            if not _is_valid_sinhala(sinhala):
                continue
            yield {
                "id": f"augmented_sentences_{i}",
                "source": "augmented_sentences",
                "level": "sentence",
                "sinhala": sinhala,
                "references": [romanized],
            }


def write_jsonl(records, name: str) -> None:
    """Stream records (list or generator) to disk, counting as we go."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{name}.jsonl"
    n_items = n_refs = 0
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n_items += 1
            n_refs += len(rec["references"])
    print(f"{name}: {n_items:,} items, {n_refs:,} references -> {out}")
    return n_items


BUILDERS = {
    "social_media": build_social_media,
    "swa_bhasha_words": build_swa_bhasha_words,
    "augmented_sentences": build_augmented_sentences,
}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", choices=list(BUILDERS), default=list(BUILDERS))
    args = parser.parse_args()
    for name in args.only:
        n = write_jsonl(BUILDERS[name](), name)
        if not n:
            print(f"{name}: no records written (raw data missing?)")
