"""HTTP POST-based transliteration using an external rule-based web romanizer tool.

The live endpoint URL is omitted for double-blind review. Configure via WEB_TOOL_URL
environment variable if reproducing network calls against a live endpoint.
"""

import os
import unicodedata
import urllib.request
import urllib.parse
import re

try:
    from ._dataset_io import cli as _cli, process_datasets as _process_datasets
    from .phonetic import transliterate as phonetic_transliterate
except ImportError:  # Direct execution
    from _dataset_io import cli as _cli, process_datasets as _process_datasets
    from phonetic import transliterate as phonetic_transliterate

DEFAULT_URL = os.environ.get(
    "WEB_TOOL_URL", "https://anonymous-web-tool.example.org/sinhala_romaniser.php"
)

def transliterate(text: str) -> str:
    """Romanize Sinhala text using the external web tool via HTTP POST."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return ""

    text = unicodedata.normalize("NFC", text)
    
    url = DEFAULT_URL
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
    _process_datasets("web_tool", transliterate)

if __name__ == "__main__":
    # One HTTP request per string, so use --datasets to regenerate a single
    # dataset rather than re-fetching all ~4,500 records.
    _cli("web_tool", transliterate)

    # Example usage:
    #print(f"Testing: 'ඇමරිකා ඓතිහාසික එක්සත් ජනපදය'\nTransliteration: {transliterate(' ඇමරිකා ඓතිහාසික එක්සත් ජනපදය')}")

