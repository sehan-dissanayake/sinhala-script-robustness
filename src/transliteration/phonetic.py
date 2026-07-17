"""Deterministic, akshara-aware Sinhala-to-ASCII romanization baseline.

This is an orthographic phonetic approximation, not a full pronunciation model.
It deliberately uses familiar ASCII Singlish spellings and preserves all
non-Sinhala content. Input is normalized to NFC before parsing.
"""

import unicodedata

try:
    from ._dataset_io import process_datasets as _process_datasets
except ImportError:  # Direct execution: python src/transliteration/phonetic.py
    from _dataset_io import process_datasets as _process_datasets

INDEPENDENT_VOWELS = {
    "අ": "a", "ආ": "aa", "ඇ": "ae", "ඈ": "aae", "ඉ": "i", "ඊ": "ii",
    "උ": "u", "ඌ": "uu", "ඍ": "ru", "ඎ": "ruu", "ඏ": "lu", "ඐ": "luu",
    "එ": "e", "ඒ": "ee", "ඓ": "ai", "ඔ": "o", "ඕ": "oo", "ඖ": "au",
}

CONSONANTS = {
    "ක": "k", "ඛ": "kh", "ග": "g", "ඝ": "gh", "ඞ": "ng", "ඟ": "ng",
    "ච": "ch", "ඡ": "chh", "ජ": "j", "ඣ": "jh", "ඤ": "ny", "ඥ": "gn",
    "ඦ": "ndj", "ට": "t", "ඨ": "th", "ඩ": "d", "ඪ": "dh", "ණ": "n",
    "ඬ": "nd", "ත": "th", "ථ": "th", "ද": "d", "ධ": "dh", "න": "n",
    "ඳ": "nd", "ප": "p", "ඵ": "ph", "බ": "b", "භ": "bh", "ම": "m",
    "ඹ": "mb", "ය": "y", "ර": "r", "ල": "l", "ව": "w", "ශ": "sh",
    "ෂ": "sh", "ස": "s", "හ": "h", "ළ": "l", "ෆ": "f",
}

VOWEL_SIGNS = {
    "ා": "aa", "ැ": "ae", "ෑ": "aae", "ි": "i", "ී": "ii", "ු": "u",
    "ූ": "uu", "ෘ": "ru", "ෲ": "ruu", "ෙ": "e", "ේ": "ee", "ෛ": "ai",
    "ො": "o", "ෝ": "oo", "ෞ": "au", "ෟ": "ow", "ෳ": "luu",
}

SPECIAL_SIGNS = {"ං": "n", "ඃ": "h"}
VIRAMA = "්"
JOINERS = {"\u200c", "\u200d"}
SINHALA_START = "\u0d80"
SINHALA_END = "\u0dff"

def _consume_joiners(text: str, index: int) -> int:
    while index < len(text) and text[index] in JOINERS:
        index += 1
    return index


def transliterate(text: str) -> str:
    """Romanize Sinhala text deterministically using orthographic syllables."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return ""

    text = unicodedata.normalize("NFC", text)
    output: list[str] = []
    index = 0

    while index < len(text):
        char = text[index]
        if char in JOINERS:
            index += 1
            continue
        if char in INDEPENDENT_VOWELS:
            output.append(INDEPENDENT_VOWELS[char])
            index += 1
            continue
        if char in CONSONANTS:
            output.append(CONSONANTS[char])
            next_index = _consume_joiners(text, index + 1)
            if next_index < len(text) and text[next_index] in VOWEL_SIGNS:
                output.append(VOWEL_SIGNS[text[next_index]])
                index = next_index + 1
            elif next_index < len(text) and text[next_index] == VIRAMA:
                index = _consume_joiners(text, next_index + 1)
            else:
                output.append("a")
                index += 1
            continue
        if char in SPECIAL_SIGNS:
            output.append(SPECIAL_SIGNS[char])
            index += 1
            continue
        # Malformed corpora occasionally contain a detached or repeated vowel
        # sign. Romanize the known sign deterministically instead of leaking it.
        if char in VOWEL_SIGNS:
            output.append(VOWEL_SIGNS[char])
            index += 1
            continue
        if char == VIRAMA:
            index += 1
            continue
        if SINHALA_START <= char <= SINHALA_END:
            context = text[max(0, index - 8):index + 9]
            raise ValueError(
                f"Unsupported or malformed Sinhala character U+{ord(char):04X} "
                f"at index {index} near {context!r}"
            )
        output.append(char)
        index += 1

    return "".join(output)


def process_datasets() -> None:
    _process_datasets("phonetic", transliterate)


if __name__ == "__main__":
    process_datasets()