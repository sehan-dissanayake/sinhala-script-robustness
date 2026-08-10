"""Batched client for the Nisansa web romanizer.

The upstream form (`sinhala_romaniser.php`) accepts free text and romanizes it
line by line, so many items can be romanized in a single POST by joining them
with newlines and splitting the response back apart. Measured on the word set
this is ~70x faster than one request per item (~4.5 ms/item vs ~317 ms/item),
which is what makes the 450k-word and 275k-sentence corpora feasible at all.

Two distinct endpoint defects show up on this data, and they are handled
differently because they are different kinds of failure:

*Hard failures.* Certain aksharas make the endpoint return its empty
placeholder instead of output, deterministically, regardless of payload size,
request rate or time of day. All known cases involve U+0DA4 (ඤ) followed by a
vowel sign or al-lakuna. The set is not guessable, so it is measured directly by
`nisansa_probe.py` and read from disk (see `failing_sequences`); the hard-coded
table below is only a fallback for a fresh clone. Because a batch fails if any
of its items contains such a sequence, sending them wastes a bisection per
affected batch, so they are held back locally and reported as failures. A failed
item yields an empty hypothesis, which the evaluation scores as a genuine error
rather than excluding.

*Leaks.* Other characters (e.g. ඓ U+0D93) come back unromanized, embedded in
otherwise valid Latin output. This is silent: the request succeeds. Leaks are
recorded verbatim, because a leftover Sinhala character in the output *is* the
tool's answer and scoring it as an error is the point.

Earlier revisions ran the in-house phonetic romanizer over every response to
patch leaks up. That made the measured system "Nisansa plus phonetic repair"
and quietly hid the leak defect behind the output of one of the competing
methods, so `repair` now defaults to False. It is kept only to reproduce the
older numbers.

Safety properties:
  * Requests containing a known-failing sequence are never sent; callers get
    them back via `unsupported`.
  * A placeholder response is treated as "this payload contains something the
    endpoint cannot process", not as a transient error, so it is never retried -
    retrying is provably useless here (60 failing batches, 6 attempts each: not
    one ever succeeded on a later attempt). Multi-item payloads are bisected
    immediately, with no waiting, to isolate the offending item.
  * If a response does not split into exactly as many lines as we sent, the
    chunk is bisected and retried, down to single items, so a single awkward
    item can never shift the alignment of its neighbours.
  * Items that cannot be sent at all (empty, newline-bearing) are handled
    separately so they can never collapse a line and shift the alignment.
  * An item that comes back as a blank line is recorded as a failure rather
    than left unresolved, so a resumable run cannot loop on it forever.

Batching does not change the romanization itself: verified identical to
one-item-per-request output (case-insensitively) on both the 4,253 social-media
strings and a 200-word sample. The single difference is that the form
capitalizes the first letter of whatever text it is given, so in batch mode only
the first line of a chunk gets that capital. Casing is a UI artifact rather than
a romanization choice, and the evaluation folds case, so this is immaterial.
"""

from __future__ import annotations

import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRANSLIT_SRC = PROJECT_ROOT / "src" / "transliteration"
sys.path.insert(0, str(TRANSLIT_SRC))
from phonetic import transliterate as _phonetic  # noqa: E402

URL = "https://nisansads.staff.uom.lk/CodeSamples/sinhala_romaniser.php"

# Written by nisansa_probe.py; committed, so a fresh clone gets the measured
# table without probing the endpoint again.
SUPPORT_DIR = PROJECT_ROOT / "data" / "reference" / "nisansa_endpoint"
FAILING_PATH = SUPPORT_DIR / "failing_sequences.json"

MAX_LINES = 250
MAX_BYTES = 6000         # payload bytes of the joined chunk
THROTTLE_S = 0.1         # polite pause between successful requests

SINHALA_RANGE = ("\u0d80", "\u0dff")

# Fallback only. The probe found this table incomplete: ඤී, ඤේ, ඤො and ඤෝ fail
# too, which is why the real table is measured rather than hand-written.
FALLBACK_FAILING = (
    "\u0DA4\u0DCA",   # ඤ් nya + al-lakuna
    "\u0DA4\u0DCF",   # ඤා nya + aa
    "\u0DA4\u0DD2",   # ඤි nya + i
    "\u0DA4\u0DD4",   # ඤු nya + u
)

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


@lru_cache(maxsize=1)
def failing_sequences() -> tuple[str, ...]:
    """Sequences the endpoint cannot romanize, longest first.

    Measured by `nisansa_probe.py`. Falls back to the hand-written table if the
    probe has never been run in this checkout.
    """
    if FAILING_PATH.exists():
        seqs = json.loads(FAILING_PATH.read_text(encoding="utf-8"))["sequences"]
        if seqs:
            return tuple(sorted(seqs, key=len, reverse=True))
    return FALLBACK_FAILING


def has_sinhala(text: str) -> bool:
    return any(SINHALA_RANGE[0] <= c <= SINHALA_RANGE[1] for c in text)


def unsupported_reason(text: str) -> str | None:
    """Why the endpoint cannot romanize `text`, or None if it should be fine."""
    for seq in failing_sequences():
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


def romanize_raw(text: str, timeout: int = 60) -> str:
    """Romanize one string and return the endpoint's output verbatim.

    No phonetic repair, no case folding: exactly what the tool produced, leaked
    Sinhala characters included. Raises `Unprocessable` on a hard failure.
    Used by `nisansa_probe.py` to characterise the endpoint.
    """
    box = _post(unicodedata.normalize("NFC", text), timeout)
    return _TAGS.sub("", box).strip()


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
    item would otherwise cost us every other item sharing its request: known
    failing sequences are filtered up front, but bisecting keeps that from being
    load-bearing if the endpoint has blind spots the probe has not catalogued.
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
                       unsupported: dict | None = None,
                       repair: bool = False) -> list[str]:
    """Romanize many Sinhala strings, batching requests. Order is preserved.

    Returns the endpoint's output verbatim. Items the endpoint cannot handle
    come back as "" and are recorded in `unsupported` with a reason; the caller
    is expected to score those as errors, not to drop them.

    `repair=True` reinstates the old behaviour of running the in-house phonetic
    romanizer over each response to patch leaked Sinhala characters. That makes
    this a hybrid of two methods under test and hides the leak defect, so it is
    off by default and kept only for reproducing earlier results.

    `on_result(source, romanized)` is invoked as each request comes back, before
    any later request is attempted. Callers should persist from that callback:
    the endpoint can start refusing at any moment, and results already fetched
    would otherwise be discarded along with the raised error.
    """
    normalized = [unicodedata.normalize("NFC", t) if t else "" for t in texts]
    results: list[str] = ["" for _ in normalized]

    def fail(text: str, reason: str) -> None:
        if unsupported is not None:
            unsupported[text] = reason

    # Held back: empty, newline-bearing (would break line alignment), or known
    # to fail. Sending the last kind would fail the whole request it travels in.
    sendable_idx: list[int] = []
    multiline_idx: list[int] = []
    for i, t in enumerate(normalized):
        if not t.strip():
            if progress is not None:
                progress(1)
            continue
        reason = unsupported_reason(t)
        if reason:
            fail(t, reason)
            if progress is not None:
                progress(1)
            continue
        (multiline_idx if "\n" in t else sendable_idx).append(i)

    for chunk_idx in _chunks_indices(sendable_idx, normalized):
        chunk = [normalized[i] for i in chunk_idx]
        romanized = _romanize_chunk(chunk, timeout, notify, unsupported)
        for i, r in zip(chunk_idx, romanized):
            src = normalized[i]
            if not r:
                # Either bisected down to a rejected item (already recorded) or
                # a blank line for non-blank input. Record so a resumable run
                # treats it as resolved instead of retrying it forever.
                if unsupported is not None and src not in unsupported:
                    fail(src, "endpoint returned a blank line")
                continue
            results[i] = _phonetic(r) if repair else r
            if on_result is not None:
                on_result(src, results[i])
        if progress is not None:
            progress(len(chunk))

    # Multi-line items cannot share a request, so they go one at a time.
    for i in multiline_idx:
        src = normalized[i]
        try:
            box = _post(src, timeout, notify)
            raw = _TAGS.sub("", box).strip()
            results[i] = (_phonetic(raw) if repair else raw) if raw else ""
            if results[i] and on_result is not None:
                on_result(src, results[i])
            elif not results[i]:
                fail(src, "endpoint returned a blank line")
        except Unprocessable:
            if unsupported is None:
                raise
            fail(src, "rejected by endpoint")
        if progress is not None:
            progress(1)
    return results


def _chunks_indices(idx: list[int], normalized: list[str]) -> list[list[int]]:
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
