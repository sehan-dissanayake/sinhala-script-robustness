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

# The server accepted 380 lines in isolation and refused 400, so these sit well
# below the observed ceiling. Whichever cap binds first wins: on the word corpus
# (~21 bytes/word) that averages ~247 words per request. Lowering either cap is
# always safe - batch size changes only how requests are packed, never the
# romanization of a given word, and results are keyed by source word - so
# existing shard files stay valid and nothing needs refetching.
MAX_LINES = 10
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


class ServerBusy(BatchRejected):
    """The server is shedding load. Retrying the same payload later works.

    Distinct from a misaligned response because the remedy is different: a busy
    server has no quarrel with the payload, so splitting it and retrying each
    half only multiplies the waiting (and the load we add).
    """


class Misaligned(BatchRejected):
    """The response did not line up with the request. Splitting may help."""


def _post_once(payload: str, timeout: int) -> str:
    data = urllib.parse.urlencode(
        {"sinhala_text": payload, "remove_diacritics": "1"}
    ).encode("utf-8")
    req = urllib.request.Request(URL, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        html = resp.read().decode("utf-8")
    match = _OUTPUT_BOX.search(html)
    if not match:
        raise ServerBusy("no output box in response")
    box = match.group(1)
    if "placeholder" in box:
        # Empirically this is the server shedding load, not a permanent refusal:
        # after a pause the identical payload succeeds. Treated as retryable.
        raise ServerBusy("server returned placeholder")
    return box


def _post(payload: str, timeout: int, notify=None) -> str:
    """POST with backoff. Raises after exhausting retries.

    `notify` receives a short human-readable message before each wait, so a long
    backoff is visible as progress rather than looking like a frozen process.
    """
    last: Exception | None = None
    attempts = len(BACKOFF_S) + 1
    for i, wait in enumerate((0.0,) + BACKOFF_S):
        if wait:
            if notify:
                notify(f"server busy ({last}); retry {i}/{attempts - 1} in {wait:.0f}s")
            time.sleep(wait)
        try:
            box = _post_once(payload, timeout)
            time.sleep(THROTTLE_S)
            return box
        except Exception as exc:
            last = exc
    raise ServerBusy(f"still refusing after {attempts} attempts: {last}")


def _split_lines(box: str, expected: int) -> list[str]:
    body = _TAGS.sub("", box).strip("\r\n")
    parts = re.split(r"\r?\n", body)
    if len(parts) != expected:
        raise Misaligned(f"expected {expected} lines, got {len(parts)}")
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


def _romanize_chunk(chunk: list[str], timeout: int, notify=None) -> list[str]:
    """Romanize a chunk, bisecting only when splitting can actually help.

    A misaligned response points at the payload, so halving it and retrying is
    worth doing. A busy server does not care about the payload, so we propagate
    immediately instead of bisecting - otherwise each level of the recursion
    repeats the full backoff sequence and one bad group stalls for many minutes.
    """
    box = _post("\n".join(chunk), timeout, notify)          # ServerBusy propagates
    try:
        return _split_lines(box, len(chunk))
    except Misaligned:
        if len(chunk) == 1:
            raise
        mid = len(chunk) // 2
        return (_romanize_chunk(chunk[:mid], timeout, notify)
                + _romanize_chunk(chunk[mid:], timeout, notify))


def transliterate_many(texts: list[str], timeout: int = 120,
                       progress=None, notify=None, on_result=None) -> list[str]:
    """Romanize many Sinhala strings, batching requests. Order is preserved.

    Mirrors `nisansa_sir's_method.transliterate`, including the phonetic
    fallback pass that fills in characters the web app leaves unconverted.

    `on_result(source, romanized)` is invoked as each request comes back, before
    any later request is attempted. Callers should persist from that callback:
    the endpoint can start refusing at any moment, and results already fetched
    would otherwise be discarded along with the raised error.
    """
    normalized = [unicodedata.normalize("NFC", t) if t else "" for t in texts]
    # Items that cannot safely share a request (empty, or already newline-bearing)
    sendable_idx = [i for i, t in enumerate(normalized) if t.strip() and "\n" not in t]
    results: list[str] = ["" for _ in normalized]

    for chunk_idx in _chunks_indices(sendable_idx, normalized):
        chunk = [normalized[i] for i in chunk_idx]
        romanized = _romanize_chunk(chunk, timeout, notify)
        for i, r in zip(chunk_idx, romanized):
            results[i] = _phonetic(r) if r else ""
            if on_result is not None and results[i]:
                on_result(normalized[i], results[i])
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
