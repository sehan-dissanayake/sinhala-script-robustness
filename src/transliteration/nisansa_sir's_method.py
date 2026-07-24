"""HTTP POST-based transliteration using Nisansa Sir's web method.

This script interacts with the web app at:
https://nisansads.staff.uom.lk/CodeSamples/sinhala_romaniser.php
via HTTP POST to perform romanization with 'Remove diacritics' checked.
"""

import unicodedata
import urllib.request
import urllib.parse
import re

try:
    from ._dataset_io import process_datasets as _process_datasets
    from .phonetic import transliterate as phonetic_transliterate
except ImportError:  # Direct execution
    from _dataset_io import process_datasets as _process_datasets
    from phonetic import transliterate as phonetic_transliterate

def transliterate(text: str) -> str:
    """Romanize Sinhala text using Nisansa Sir's web method via HTTP POST."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return ""

    text = unicodedata.normalize("NFC", text)
    
    url = "https://nisansads.staff.uom.lk/CodeSamples/sinhala_romaniser.php"
    data = urllib.parse.urlencode({
        "sinhala_text": text,
        "remove_diacritics": "1"
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=data)
    
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch transliteration from {url}: {e}")
        
    match = re.search(r'<div class="output-box"[^>]*>(.*?)</div>', html, re.DOTALL)
    if match:
        result = match.group(1).strip()
        # Remove any HTML tags that might be inside (e.g., spans)
        result = re.sub(r'<[^>]+>', '', result).strip()
        # Fallback to baseline phonetic transliteration for characters the web app missed (e.g. ඓ)
        return phonetic_transliterate(result)
    else:
        raise ValueError("Could not find the output box in the HTML response.")

def process_datasets() -> None:
    _process_datasets("nisansa_sirs_method", transliterate)

if __name__ == "__main__":
    process_datasets()

    # Example usage:
    #print(f"Testing: 'ඇමරිකා ඓතිහාසික එක්සත් ජනපදය'\nTransliteration: {transliterate(' ඇමරිකා ඓතිහාසික එක්සත් ජනපදය')}")
