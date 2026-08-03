"""Batched client for the Nisansa web romanizer.

The upstream form (`sinhala_romaniser.php`) accepts free text and romanizes it
line by line, so many items can be romanized in a single POST by joining them
with newlines and splitting the response back apart. Measured on the word set
this is ~70x faster than one request per item (~4.5 ms/item vs ~317 ms/item),
which is what makes the 450k-word and sampled-sentence corpora feasible at all.

The endpoint cannot romanize one specific sequence: U+0DA4 (nya) followed by
U+0DCA (al-lakuna), i.e. ඤ්. Any request containing it returns the page's empty
placeholder instead of output, deterministically and regardless of payload size,
request rate or time of day. Measured directly: ඤ alone works, every other
consonant + al-lakuna works, all 41 consonants tested, only ඤ් breaks. It occurs
in 1,144 of the 450,587 corpus words (0.254%), and because a batch fails if any
of its items contains it, a 250-word batch fails ~30-47% of the time. That is the
entire cause of what looked like rate limiting or load shedding: retrying,
slowing down and shrinking batches never helped because nothing was ever
throttled. Such words are filtered out locally instead of being sent.

Safety properties:
  * Requests containing a known-broken sequence are never sent (see
    BROKEN_SEQUENCES); callers get them back via `unsupported`.
  * A placeholder response is treated as "this payload contains something the
    endpoint cannot process", not as a transient error, so it is never retried -
    retrying is provably useless here (60 failing batches, 6 attempts each: not
    one ever succeeded on a later attempt). Multi-item payloads are bisected
    immediately, with no waiting, to isolate the offending item.
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
MAX_LINES = 50
MAX_BYTES = 6000         # payload bytes of the joined chunk
THROTTLE_S = 0.1         # polite pause between successful requests

# Input the endpoint cannot process. Sending it wastes a request and takes the
# whole batch down with it, so it is filtered client-side.
BROKEN_SEQUENCES = ("\u0DA4\u0DCA",)     # ඤ් : nya + al-lakuna

# Retries exist only for genuine transport errors (dropped connection, timeout).
# A placeholder response is deterministic and never retried.
BACKOFF_S = (0.5, 1.5, 4.0)
_OUTPUT_BOX = re.compile(r'<div class="output-box"[^>]*>(.*?)</div>', re.DOTALL)
_TAGS = re.compile(r"<[^>]+>")


class BatchRejected(RuntimeError):
    """The server did not return a usable, correctly aligned response."""


class Unprocessable(BatchRejected):
    """The endpoint returned its empty placeholder for this payload.

    Deterministic: the payload contains something the romanizer cannot handle.
    Never retried - measured across 60 failing batches with 6 attempts each,
    not one succeeded on a later attempt. Multi-item payloads are bisected to
    find the culprit; a single item that triggers this is unromanizable.
    """


class Misaligned(BatchRejected):
    """The response did not line up with the request. Splitting may help."""


def unsupported_reason(text: str) -> str | None:
    """Why the endpoint cannot romanize `text`, or None if it should be fine."""
    for seq in BROKEN_SEQUENCES:
        if seq in text:
            return "contains " + " ".join(f"U+{ord(c):04X}" for c in seq)
    return None


def _post_once(payload: str, timeout: int) -> str:
    data = urllib.parse.urlencode(
        {"sinhala_text": payload, "remove_diacritics": "1"}
    ).encode("utf-8")
    req = urllib.request.Request(URL, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        html = resp.read().decode("utf-8")
    match = _OUTPUT_BOX.search(html)
    if not match:
        raise Unprocessable("no output box in response")
    box = match.group(1)
    if "placeholder" in box:
        raise Unprocessable("endpoint returned its empty placeholder")
    return box


def _post(payload: str, timeout: int, notify=None) -> str:
    """POST, retrying only genuine transport failures.

    A placeholder response is deterministic, so it is raised immediately instead
    of being retried; only dropped connections and timeouts get another attempt.
    """
    last: Exception | None = None
    for i, wait in enumerate((0.0,) + BACKOFF_S):
        if wait:
            if notify:
                notify(f"network error ({last}); retry {i} in {wait:.0f}s")
            time.sleep(wait)
        try:
            box = _post_once(payload, timeout)
            time.sleep(THROTTLE_S)
            return box
        except Unprocessable:
            raise                      # deterministic - retrying cannot help
        except Exception as exc:
            last = exc
    raise BatchRejected(f"transport failed after {len(BACKOFF_S) + 1} attempts: {last}")


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


def _romanize_chunk(chunk: list[str], timeout: int, notify=None,
                    unsupported: dict | None = None) -> list[str]:
    """Romanize a chunk, isolating any item the endpoint cannot process.

    Both failure modes are handled by bisecting, which costs ~2*log2(n) extra
    requests and no waiting at all. This matters because a single unromanizable
    item would otherwise cost us every other item sharing its request: the known
    broken sequence is filtered up front, but bisecting keeps that from being
    load-bearing if the endpoint has other blind spots we have not catalogued.
    """
    try:
        box = _post("\n".join(chunk), timeout, notify)
        return _split_lines(box, len(chunk))
    except (Unprocessable, Misaligned):
        if len(chunk) == 1:
            if unsupported is not None:
                unsupported[chunk[0]] = "rejected by endpoint"
                return [""]
            raise
        mid = len(chunk) // 2
        return (_romanize_chunk(chunk[:mid], timeout, notify, unsupported)
                + _romanize_chunk(chunk[mid:], timeout, notify, unsupported))


def transliterate_many(texts: list[str], timeout: int = 120, progress=None,
                       notify=None, on_result=None,
                       unsupported: dict | None = None) -> list[str]:
    """Romanize many Sinhala strings, batching requests. Order is preserved.

    Mirrors `nisansa_sir's_method.transliterate`, including the phonetic
    fallback pass that fills in characters the web app leaves unconverted.

    `on_result(source, romanized)` is invoked as each request comes back, before
    any later request is attempted. Callers should persist from that callback:
    the endpoint can start refusing at any moment, and results already fetched
    would otherwise be discarded along with the raised error.
    """
    normalized = [unicodedata.normalize("NFC", t) if t else "" for t in texts]
    results: list[str] = ["" for _ in normalized]

    # Held back: empty, newline-bearing (would break line alignment), or known to
    # be unromanizable by this endpoint. Sending the last kind would fail the
    # whole request it travels in.
    sendable_idx = []
    for i, t in enumerate(normalized):
        if not t.strip() or "\n" in t:
            continue
        reason = unsupported_reason(t)
        if reason:
            if unsupported is not None:
                unsupported[t] = reason
            if progress is not None:
                progress(1)
            continue
        sendable_idx.append(i)

    for chunk_idx in _chunks_indices(sendable_idx, normalized):
        chunk = [normalized[i] for i in chunk_idx]
        romanized = _romanize_chunk(chunk, timeout, notify, unsupported)
        for i, r in zip(chunk_idx, romanized):
            results[i] = _phonetic(r) if r else ""
            if on_result is not None and results[i]:
                on_result(normalized[i], results[i])
        if progress is not None:
            progress(len(chunk))

    # Multi-line items cannot share a request, so they go one at a time.
    sendable = set(sendable_idx)
    for i, t in enumerate(normalized):
        if i in sendable or not t.strip() or unsupported_reason(t):
            continue
        if "\n" in t:
            try:
                box = _post(t, timeout, notify)
                results[i] = _phonetic(_TAGS.sub("", box).strip())
                if on_result is not None and results[i]:
                    on_result(t, results[i])
            except Unprocessable:
                if unsupported is None:
                    raise
                unsupported[t] = "rejected by endpoint"
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
