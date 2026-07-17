"""Sinhala-to-Latin baseline using uroman 1.3.1.1."""

import re
import unicodedata
from functools import lru_cache

from uroman import Uroman

try:
    from ._dataset_io import process_datasets as _process_datasets
    from .phonetic import transliterate as _fallback_transliterate
except ImportError:
    from _dataset_io import process_datasets as _process_datasets
    from phonetic import transliterate as _fallback_transliterate

TOKEN_PATTERN = re.compile(r"([\u0d80-\u0dff\u200c\u200d]+|[^\u0d80-\u0dff\u200c\u200d]+)")
_ROMANIZER = Uroman()


@lru_cache(maxsize=65536)
def _romanize_token(token: str) -> str:
    # uroman leaves a few Sinhala signs untouched. Apply the deterministic
    # fallback only to residual fragments so malformed corpus text cannot leak.
    romanized = _ROMANIZER.romanize_string(token, lcode="sin").replace("ඃ", "h")
    if any("\u0d80" <= char <= "\u0dff" for char in romanized):
        romanized = _fallback_transliterate(romanized)
    return romanized


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
    _process_datasets("uroman", transliterate)


if __name__ == "__main__":
    process_datasets()