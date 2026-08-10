"""Sinhala-to-ASCII adapter over Aksharamukha 2.3's ISO romanizer."""

import re
import unicodedata
from functools import lru_cache

from aksharamukha import transliterate as aksharamukha

try:
    from ._dataset_io import cli as _cli, process_datasets as _process_datasets
except ImportError:
    from _dataset_io import cli as _cli, process_datasets as _process_datasets

TOKEN_PATTERN = re.compile(r"([\u0d80-\u0dff\u200c\u200d]+|[^\u0d80-\u0dff\u200c\u200d]+)")
REPLACEMENTS = (
    ("r̥̄", "ruu"), ("l̥̄", "luu"), ("r̥", "ru"), ("l̥", "lu"),
    ("ǣ", "aae"), ("æ", "ae"), ("ā", "aa"), ("ī", "ii"),
    ("ū", "uu"), ("ē", "ee"), ("ō", "oo"), ("ṁ", "n"),
    ("ḥ", "h"), ("ṅ", "ng"), ("ñ", "ny"), ("ṭ", "t"),
    ("ḍ", "d"), ("ṇ", "n"), ("ś", "sh"), ("ṣ", "sh"), ("ḷ", "l"),
    ("n̆", "n"), ("m̆", "m"),
)


def _ascii_projection(value: str) -> str:
    for source, target in REPLACEMENTS:
        value = value.replace(source, target)
    value = "".join(
        char for char in unicodedata.normalize("NFD", value)
        if unicodedata.category(char) != "Mn"
    )
    # ISO c and v correspond to familiar Sinhala Singlish ch and w here.
    return value.replace("c", "ch").replace("v", "w")


@lru_cache(maxsize=65536)
def _romanize_token(token: str) -> str:
    iso = aksharamukha.process("Sinhala", "ISO", token, nativize=False)
    return _ascii_projection(iso)


def transliterate(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    return "".join(
        _romanize_token(token) if any("\u0d80" <= char <= "\u0dff" for char in token) else token
        for token in TOKEN_PATTERN.findall(text)
    )


def process_datasets() -> None:
    _process_datasets("aksharamukha", transliterate)


if __name__ == "__main__":
    _cli("aksharamukha", transliterate)