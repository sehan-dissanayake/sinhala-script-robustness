"""Batched client for the Nisansa web romanizer.

The upstream form (`sinhala_romaniser.php`) accepts free text and romanizes it
line by line, so many items can be romanized in a single POST by joining them
with newlines and splitting the response back apart. Measured on the word set
this is ~70x faster than one request per item (~4.5 ms/item vs ~317 ms/item),
which is what makes the 450k-word and sampled-sentence corpora feasible at all.

Safety properties:
  * The server silently rejects oversized payloads (it returns the "Your
    romanised text will appear here." placeholder). We cap each request by both
    line count and payload bytes, and treat a placeholder response as failure.
  * If a response does not split into exactly as many lines as we sent, the
    chunk is bisected and retried, down to single items, so a single awkward
    item can never shift the alignment of its neighbours.
  * Items whose romanization would be empty are never sent (they would collapse
    a line and break alignment); they are handled directly.

Batching does not change the romanization itself: verified identical to
one-item-per-request output (case-insensitively) on both the 4,253 social-media
strings and a 200-word sample. The single difference is that the form
capitalizes the first letter of whatever text it is given, so in batch mode only
the first line of a chunk gets that capital. Casing is a UI artifact rather than
a romanization choice, and the evaluation folds case, so this is immaterial.
"""

from __future__ import annotations

import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TRANSLIT_SRC = Path(__file__).resolve().parents[1] / "transliteration"
sys.path.insert(0, str(TRANSLIT_SRC))
from phonetic import transliterate as _phonetic  # noqa: E402

URL = "https://nisansads.staff.uom.lk/CodeSamples/sinhala_romaniser.php"

MAX_LINES = 300          # server tolerated 380 in isolation; stay just clear
MAX_BYTES = 6000         # payload bytes of the joined chunk
THROTTLE_S = 0.1         # polite pause between successful requests

# The endpoint refuses roughly a third of requests regardless of how slowly we
# send them (measured at 150 and 350 lines/request, 0.15s to 2s apart), so the
# refusals are load-shedding on its side rather than a rate limit we can pace
# around. Retrying quickly is therefore both faster and no less polite than
# waiting: the first waits are short, and only a persistent problem escalates.
BACKOFF_S = (0.5, 1.0, 2.0, 5.0, 10.0, 20.0)
_OUTPUT_BOX = re.compile(r'<div class="output-box"[^>]*>(.*?)</div>', re.DOTALL)
_TAGS = re.compile(r"<[^>]+>")


class BatchRejected(RuntimeError):
    """The server did not return a usable, correctly aligned response."""


def _post_once(payload: str, timeout: int) -> str:
    data = urllib.parse.urlencode(
        {"sinhala_text": payload, "remove_diacritics": "1"}
    ).encode("utf-8")
    req = urllib.request.Request(URL, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        html = resp.read().decode("utf-8")
    match = _OUTPUT_BOX.search(html)
    if not match:
        raise BatchRejected("no output box in response")
    box = match.group(1)
    if "placeholder" in box:
        # Empirically this is the server shedding load, not a permanent refusal:
        # after a pause the identical payload succeeds. Treated as retryable.
        raise BatchRejected("server returned placeholder")
    return box


def _post(payload: str, timeout: int) -> str:
    """POST with backoff. Raises BatchRejected only after exhausting retries."""
    last: Exception | None = None
    for wait in (0.0,) + BACKOFF_S:
        if wait:
            time.sleep(wait)
        try:
            box = _post_once(payload, timeout)
            time.sleep(THROTTLE_S)
            return box
        except Exception as exc:
            last = exc
    raise BatchRejected(f"failed after {len(BACKOFF_S) + 1} attempts: {last}")


def _split_lines(box: str, expected: int) -> list[str]:
    body = _TAGS.sub("", box).strip("\r\n")
    parts = re.split(r"\r?\n", body)
    if len(parts) != expected:
        raise BatchRejected(f"expected {expected} lines, got {len(parts)}")
    return [p.strip() for p in parts]


def _chunks(items: list[str]) -> list[list[str]]:
    out: list[list[str]] = []
    cur: list[str] = []
    size = 0
    for it in items:
        b = len(it.encode("utf-8")) + 1
        if cur and (len(cur) >= MAX_LINES or size + b > MAX_BYTES):
            out.append(cur)
            cur, size = [], 0
        cur.append(it)
        size += b
    if cur:
        out.append(cur)
    return out


def _romanize_chunk(chunk: list[str], timeout: int) -> list[str]:
    """Romanize a chunk, bisecting on any alignment/rejection failure."""
    try:
        box = _post("\n".join(chunk), timeout)
        return _split_lines(box, len(chunk))
    except BatchRejected:
        if len(chunk) == 1:
            raise
        mid = len(chunk) // 2
        return (_romanize_chunk(chunk[:mid], timeout)
                + _romanize_chunk(chunk[mid:], timeout))


def transliterate_many(texts: list[str], timeout: int = 120,
                       progress=None) -> list[str]:
    """Romanize many Sinhala strings, batching requests. Order is preserved.

    Mirrors `nisansa_sir's_method.transliterate`, including the phonetic
    fallback pass that fills in characters the web app leaves unconverted.
    """
    normalized = [unicodedata.normalize("NFC", t) if t else "" for t in texts]
    # Items that cannot safely share a request (empty, or already newline-bearing)
    sendable_idx = [i for i, t in enumerate(normalized) if t.strip() and "\n" not in t]
    results: list[str] = ["" for _ in normalized]

    for chunk_idx in _chunks_indices(sendable_idx, normalized):
        chunk = [normalized[i] for i in chunk_idx]
        romanized = _romanize_chunk(chunk, timeout)
        for i, r in zip(chunk_idx, romanized):
            results[i] = _phonetic(r) if r else ""
        if progress is not None:
            progress(len(chunk))

    # anything held back (blank / multi-line) goes through the single-item path
    for i, t in enumerate(normalized):
        if i not in set(sendable_idx) and t.strip():
            box = _post(t, timeout)
            results[i] = _phonetic(_TAGS.sub("", box).strip())
            if progress is not None:
                progress(1)
    return results


def _chunks_indices(idx: list[str], normalized: list[str]) -> list[list[int]]:
    out: list[list[int]] = []
    cur: list[int] = []
    size = 0
    for i in idx:
        b = len(normalized[i].encode("utf-8")) + 1
        if cur and (len(cur) >= MAX_LINES or size + b > MAX_BYTES):
            out.append(cur)
            cur, size = [], 0
        cur.append(i)
        size += b
    if cur:
        out.append(cur)
    return out
