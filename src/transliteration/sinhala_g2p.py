"""Rule-based Sinhala G2P with explicit schwa epenthesis.

Implements the ordered mapping and eight schwa rules in Wasala, Weerasinghe,
and Gamage (COLING/ACL 2006). Output is a readable Latin phonemic
transcription; `ə` is intentionally retained because ASCII `a` would erase the
paper's /ə/ versus /a/ distinction. This is a G2P condition, not colloquial
ASCII Singlish.
"""

import re
import unicodedata

try:
    from ._dataset_io import process_datasets as _process_datasets
except ImportError:
    from _dataset_io import process_datasets as _process_datasets

SCHWA = "ə"
VOWELS = {"a", "aa", "ae", "aae", "i", "ii", "u", "uu", "ri", "ru", "ruu", "lu", "luu", "e", "ee", "ai", "o", "oo", "au", SCHWA}
INDEPENDENT_VOWELS = {
    "අ": "a", "ආ": "aa", "ඇ": "ae", "ඈ": "aae", "ඉ": "i", "ඊ": "ii",
    "උ": "u", "ඌ": "uu", "ඍ": "ri", "ඎ": "ruu", "ඏ": "lu", "ඐ": "luu",
    "එ": "e", "ඒ": "ee", "ඓ": "ai", "ඔ": "o", "ඕ": "oo", "ඖ": "au",
}
VOWEL_SIGNS = {
    "ා": "aa", "ැ": "ae", "ෑ": "aae", "ි": "i", "ී": "ii", "ු": "u",
    "ූ": "uu", "ෘ": "ru", "ෲ": "ruu", "ෙ": "e", "ේ": "ee", "ෛ": "ai",
    "ො": "o", "ෝ": "oo", "ෞ": "au", "ෟ": "lu", "ෳ": "luu",
}
CONSONANTS = {
    "ක": "k", "ඛ": "k", "ග": "g", "ඝ": "g", "ඞ": "ng", "ඟ": "ng",
    "ච": "ch", "ඡ": "ch", "ජ": "j", "ඣ": "j", "ඤ": "ny", "ඥ": "jny",
    "ඦ": "nj", "ට": "ṭ", "ඨ": "ṭ", "ඩ": "ḍ", "ඪ": "ḍ", "ණ": "n",
    "ඬ": "nd", "ත": "t", "ථ": "t", "ද": "d", "ධ": "d", "න": "n",
    "ඳ": "nd", "ප": "p", "ඵ": "p", "බ": "b", "භ": "b", "ම": "m",
    "ඹ": "mb", "ය": "y", "ර": "r", "ල": "l", "ව": "w", "ශ": "sh",
    "ෂ": "sh", "ස": "s", "හ": "h", "ළ": "l", "ෆ": "f",
}
NO_INHERENT_VOWEL = {"ඞ"}
SPECIAL_SIGNS = {"ං": "ng", "ඃ": "h"}
CONSONANT_PHONEMES = set(CONSONANTS.values())
VIRAMA = "්"
JOINERS = {"\u200c", "\u200d"}
TOKEN_PATTERN = re.compile(r"([\u0d80-\u0dff\u200c\u200d]+|[^\u0d80-\u0dff\u200c\u200d]+)")


def _is_consonant(value: str) -> bool:
    return value in CONSONANT_PHONEMES


def _consume_joiners(text: str, index: int) -> int:
    while index < len(text) and text[index] in JOINERS:
        index += 1
    return index


def _map_word(word: str) -> list[str]:
    units: list[str] = []
    index = 0
    while index < len(word):
        char = word[index]
        if char in JOINERS:
            index += 1
        elif char in INDEPENDENT_VOWELS:
            units.append(INDEPENDENT_VOWELS[char])
            index += 1
        elif char in CONSONANTS:
            units.append(CONSONANTS[char])
            next_index = _consume_joiners(word, index + 1)
            if next_index < len(word) and word[next_index] in VOWEL_SIGNS:
                units.append(VOWEL_SIGNS[word[next_index]])
                index = next_index + 1
            elif next_index < len(word) and word[next_index] == VIRAMA:
                index = _consume_joiners(word, next_index + 1)
            else:
                if char not in NO_INHERENT_VOWEL:
                    units.append(SCHWA)
                index += 1
        elif char in SPECIAL_SIGNS:
            units.append(SPECIAL_SIGNS[char])
            index += 1
        elif char in VOWEL_SIGNS:
            units.append(VOWEL_SIGNS[char])
            index += 1
        elif char == VIRAMA:
            index += 1
        else:
            raise ValueError(f"Unsupported Sinhala G2P character U+{ord(char):04X}")
    return units


def _rule_1(units: list[str]) -> None:
    try:
        nucleus = next(i for i, value in enumerate(units) if value in VOWELS)
    except StopIteration:
        return
    if units[nucleus] != SCHWA:
        return
    starts_sw = len(units) >= 2 and units[:2] == ["s", "w"]
    starts_kar = len(units) >= 3 and units[:3] == ["k", SCHWA, "r"]
    single_cv = len(units) == 2 and _is_consonant(units[0])
    if not (starts_sw or starts_kar or single_cv):
        units[nucleus] = "a"


def _rule_2(units: list[str]) -> None:
    # The paper's 2(b) and 2(c) swap the same context and would oscillate if
    # blindly repeated. Each matching position is therefore transformed once.
    for index in range(1, len(units) - 2):
        if not (_is_consonant(units[index - 1]) and units[index] == "r"):
            continue
        vowel, following = units[index + 1], units[index + 2]
        if not _is_consonant(following):
            continue
        if vowel == SCHWA:
            units[index + 1] = "a"
        elif vowel == "a" and following != "h":
            units[index + 1] = SCHWA


def _rule_3(units: list[str]) -> None:
    triggers = {"a", "e", "ae", "o", SCHWA}
    for index in range(len(units) - 2):
        if units[index] in triggers and units[index + 1] == "h" and units[index + 2] == SCHWA:
            units[index + 2] = "a"


def _rule_4(units: list[str]) -> None:
    for index in range(len(units) - 2):
        if units[index] == SCHWA and _is_consonant(units[index + 1]) and _is_consonant(units[index + 2]):
            units[index] = "a"


def _rule_5(units: list[str]) -> None:
    exceptions = {"r", "b", "ḍ", "ṭ"}
    if len(units) >= 2 and units[-2] == SCHWA and _is_consonant(units[-1]) and units[-1] not in exceptions:
        units[-2] = "a"


def _rule_6(units: list[str]) -> None:
    if len(units) >= 3 and units[-3:] == [SCHWA, "y", "i"]:
        units[-3] = "a"


def _rule_7(units: list[str]) -> None:
    for index in range(len(units) - 3):
        if units[index] == "k" and units[index + 1] == SCHWA and units[index + 2] in {"r", "l"} and units[index + 3] == "u":
            units[index + 1] = "a"


def _rule_8(units: list[str]) -> None:
    for index in range(len(units) - 2):
        if units[index:index + 3] != ["k", "a", "l"]:
            continue
        tail = units[index + 3:]
        if len(tail) >= 2 and tail[0] in {"aa", "ee", "oo"} and tail[1] == "y":
            units[index + 1] = SCHWA
        elif len(tail) >= 3 and tail[0] == "e" and tail[1] in {"m", "h"} and tail[2] in {"u", "i"}:
            units[index + 1] = SCHWA
        elif len(tail) >= 3 and tail[:2] == [SCHWA, "h"] and tail[2] in {"u", "i"}:
            units[index + 1] = SCHWA
            units[index + 3] = "e"
        elif tail == [SCHWA]:
            units[index + 1] = SCHWA


def _map_diphthongs(units: list[str]) -> list[str]:
    mappings = {
        ("i", "w", "u"): "iu", ("e", "w", "u"): "eu",
        ("ae", "w", "u"): "aeu", ("o", "w", "u"): "ou",
        ("a", "w", "u"): "au", ("u", "y", "i"): "ui",
        ("e", "y", "i"): "ei", ("ae", "y", "i"): "aei",
        ("o", "y", "i"): "oi", ("a", "y", "i"): "ai",
    }
    result: list[str] = []
    index = 0
    while index < len(units):
        triple = tuple(units[index:index + 3])
        if triple in mappings:
            result.append(mappings[triple])
            index += 3
        else:
            result.append(units[index])
            index += 1
    return result


def transcribe_word(word: str) -> str:
    units = _map_word(word)
    _rule_1(units)
    _rule_2(units)
    _rule_3(units)
    _rule_4(units)
    _rule_5(units)
    _rule_6(units)
    _rule_7(units)
    _rule_8(units)
    units = _map_diphthongs(units)
    return "".join(units).replace("ṭ", "t").replace("ḍ", "d")


def transliterate(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    return "".join(
        transcribe_word(token) if any("\u0d80" <= char <= "\u0dff" for char in token) else token
        for token in TOKEN_PATTERN.findall(text)
    )


def process_datasets() -> None:
    _process_datasets("sinhala_g2p_schwa", transliterate)


if __name__ == "__main__":
    process_datasets()