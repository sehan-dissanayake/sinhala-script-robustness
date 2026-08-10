"""Characterise what the Nisansa web romanizer can and cannot do, by measurement.

Two defects affect the evaluation, and both were originally found by accident
rather than by measurement, which is a bad way to know the shape of a bug:

  hard failure - the endpoint returns its empty placeholder and produces no
                 output at all. Every known case is U+0DA4 (ඤ) plus a vowel
                 sign or al-lakuna, but the hand-written table used until now
                 listed only four such sequences and the corpus run discovered
                 more by bisection (ඤී, ඤේ, ඤො, ඤෝ). A partial table is worse
                 than none: items outside it fail a whole batch, and items
                 wrongly inside it would be scored as failures without ever
                 being sent.

  leak         - the request succeeds but a Sinhala character comes back
                 unromanized inside otherwise valid Latin output (ඓ, as in
                 ඓතිහාසික). Silent, and previously masked because the client ran
                 the in-house phonetic romanizer over every response.

This walks the Sinhala akshara grid one item per request (a batch would confound
the two defects, since one failing item fails its whole batch) and records the
verbatim output for each. The result is committed so nobody has to re-probe, and
`nisansa_batch` reads the failing table from it instead of guessing.

    python src/method_evaluation/nisansa_probe.py            # full grid
    python src/method_evaluation/nisansa_probe.py --report    # re-derive tables
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nisansa_batch import (SUPPORT_DIR, URL, Unprocessable, has_sinhala,  # noqa: E402
                           romanize_raw)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROBE_PATH = SUPPORT_DIR / "probe_results.json"
FAILING_PATH = SUPPORT_DIR / "failing_sequences.json"
LEAKING_PATH = SUPPORT_DIR / "leaking_sequences.json"

INDEPENDENT_VOWELS = "අආඇඈඉඊඋඌඍඎඏඐඑඒඓඔඕඖ"
CONSONANTS = ("කඛගඝඞඟචඡජඣඤඥඦටඨඩඪණඬතථදධනඳපඵබභමඹයරලවශෂසහළෆ")
VOWEL_SIGNS = "ාැෑිීුූෘෲෙේෛොෝෞෟෳ"
SPECIAL_SIGNS = "ංඃ"
AL_LAKUNA = "\u0DCA"
ZWJ = "\u200D"

# A neutral carrier for context probes: ක romanizes cleanly on its own, so any
# failure or leak in "ක<unit>ක" is attributable to the unit.
CARRIER = "ක"


def build_grid() -> list[tuple[str, str]]:
    """(kind, text) pairs covering the orthography actually used by the corpora."""
    grid: list[tuple[str, str]] = []
    for v in INDEPENDENT_VOWELS:
        grid.append(("independent_vowel", v))
    for c in CONSONANTS:
        grid.append(("consonant", c))
    for s in SPECIAL_SIGNS:
        grid.append(("special_sign", s))
    for c in CONSONANTS:
        for v in VOWEL_SIGNS:
            grid.append(("akshara", c + v))
        grid.append(("akshara_hal", c + AL_LAKUNA))
    # The two common ligature forms, which are written with a joiner and are
    # frequent enough in the corpora to be worth covering explicitly.
    for c in CONSONANTS:
        grid.append(("conjunct_ra", c + AL_LAKUNA + ZWJ + "ර"))
        grid.append(("conjunct_ya", c + AL_LAKUNA + ZWJ + "ය"))
    return grid


def codes(text: str) -> str:
    return " ".join(f"U+{ord(c):04X}" for c in text)


def classify(text: str, raw: str | None, error: str | None) -> dict:
    if error is not None:
        return {"verdict": "fail", "raw": "", "detail": error}
    assert raw is not None
    if not raw:
        return {"verdict": "fail", "raw": "", "detail": "blank output"}
    leaked = "".join(dict.fromkeys(c for c in raw if has_sinhala(c)))
    if leaked:
        return {"verdict": "leak", "raw": raw, "leaked": leaked,
                "detail": f"unromanized {codes(leaked)}"}
    return {"verdict": "ok", "raw": raw, "detail": ""}


def load_results() -> dict:
    if PROBE_PATH.exists():
        return json.loads(PROBE_PATH.read_text(encoding="utf-8"))
    return {"url": URL, "units": {}}


def save_results(data: dict) -> None:
    SUPPORT_DIR.mkdir(parents=True, exist_ok=True)
    PROBE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True),
                          encoding="utf-8")


def probe(units: list[tuple[str, str]], data: dict, timeout: int) -> None:
    todo = [(kind, text) for kind, text in units if text not in data["units"]]
    print(f"{len(units):,} units in grid | {len(units) - len(todo):,} already probed | "
          f"{len(todo):,} to do")
    if not todo:
        return
    since_save = 0
    with tqdm(total=len(todo), unit="unit") as bar:
        for kind, text in todo:
            try:
                rec = classify(text, romanize_raw(text, timeout), None)
            except Unprocessable as exc:
                rec = classify(text, None, str(exc))
            except Exception as exc:               # transport: leave unrecorded
                tqdm.write(f"  ! {codes(text)} transport error ({exc}); skipped")
                bar.update(1)
                continue
            rec["kind"] = kind
            rec["codes"] = codes(text)
            data["units"][text] = rec
            if rec["verdict"] != "ok":
                tqdm.write(f"  {rec['verdict']:4s} {text}  {rec['codes']}  {rec['detail']}")
            bar.update(1)
            since_save += 1
            if since_save >= 50:
                save_results(data)
                since_save = 0
    save_results(data)


def context_probes(data: dict, timeout: int) -> list[tuple[str, str]]:
    """Re-probe every non-ok unit inside a word, to rule out an input-length quirk.

    A defect that only shows up for a bare one-akshara submission would not
    affect corpus items; one that persists inside `ක<unit>ක` does.
    """
    suspect = [t for t, r in data["units"].items()
               if r["verdict"] != "ok" and not r["kind"].startswith("context")]
    return [("context", CARRIER + t + CARRIER) for t in suspect]


def derive(data: dict) -> tuple[list[str], list[str], list[dict]]:
    """Reduce the grid to the tables the client and the evaluation need.

    Leaks need care. Taking the union of every character seen unromanized would
    include most vowel signs, because an akshara whose *base* is unsupported
    leaks whole - ``ඦ්‍ර`` comes back carrying U+0DA6 and U+0DCA even though
    al-lakuna is fine after any supported consonant. Flagging al-lakuna would
    then match nearly every word in the corpus and make the targeted refetch
    pointless.

    Nor is a per-character table enough in the other direction: U+0DD9 (ෙ) leaks
    after ඣ, ඤ, ඥ and ඬ but romanizes fine after ක, so the gap is in specific
    base+sign combinations, not in the sign. What comes out is therefore a
    minimal set of *sequences*, matched against corpus items by substring, in
    the same way as the hard-failure table: a sign that leaks after every
    consonant collapses to the bare sign, and anything already covered by a
    shorter sequence is dropped.
    """
    units = data["units"]
    failing = []
    for text, rec in units.items():
        if rec["kind"] == "context":
            continue
        if rec["verdict"] == "fail":
            failing.append(text)

    # Only keep a failing sequence if it also fails inside a word; a bare-input
    # quirk would never be triggered by a corpus item.
    confirmed = []
    for text in failing:
        ctx = units.get(CARRIER + text + CARRIER)
        if ctx is None or ctx["verdict"] == "fail":
            confirmed.append(text)

    leaking_units = [
        {"unit": t, "codes": r["codes"], "raw": r["raw"], "leaked": r.get("leaked", "")}
        for t, r in units.items()
        if r["verdict"] == "leak" and r["kind"] != "context"
    ]
    leaks = {u["unit"] for u in leaking_units}

    # A sign that leaks after every consonant is unsupported in itself, so it
    # stands in for all 41 pairs.
    seqs: set[str] = {t for t in leaks if len(t) == 1}
    for sign in VOWEL_SIGNS + AL_LAKUNA:
        pairs = [c + sign for c in CONSONANTS]
        if all(p in leaks for p in pairs):
            seqs.add(sign)

    # Everything else is kept as the specific sequence, unless a shorter
    # accepted sequence already covers it.
    for t in sorted(leaks, key=len):
        if t in seqs:
            continue
        if not any(s in t for s in seqs):
            seqs.add(t)
    return sorted(confirmed), sorted(seqs, key=lambda s: (len(s), s)), leaking_units


def write_tables(data: dict) -> None:
    failing, leaking, leaking_units = derive(data)
    covered = sum(1 for u in leaking_units if any(s in u["unit"] for s in leaking))
    assert covered == len(leaking_units), (
        f"{len(leaking_units) - covered} leaking unit(s) not covered by the derived table")
    SUPPORT_DIR.mkdir(parents=True, exist_ok=True)
    FAILING_PATH.write_text(json.dumps({
        "description": "Sequences the Nisansa endpoint cannot romanize at all "
                       "(returns its empty placeholder). Measured by nisansa_probe.py.",
        "url": URL,
        "n_units_probed": len(data["units"]),
        "sequences": failing,
        "sequences_readable": [f"{s}  {codes(s)}" for s in failing],
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    LEAKING_PATH.write_text(json.dumps({
        "description": "Minimal set of sequences the Nisansa endpoint returns unromanized "
                       "inside otherwise valid output. Match by substring. Scored as "
                       "errors, not repaired. Derived by nisansa_probe.py from "
                       "leaking_units, which lists every probed unit that leaked.",
        "url": URL,
        "sequences": leaking,
        "sequences_readable": [f"{s}  {codes(s)}" for s in leaking],
        "leaking_units": leaking_units,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    counts: dict[str, int] = {}
    for rec in data["units"].values():
        counts[rec["verdict"]] = counts.get(rec["verdict"], 0) + 1
    print(f"\nprobed {len(data['units']):,} units: "
          + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))
    print(f"\n{len(failing)} failing sequence(s) - no output at all:")
    for s in failing:
        print(f"  {s}   {codes(s)}")
    print(f"\n{len(leaking)} leaking sequence(s) - output keeps the Sinhala:")
    for c in leaking:
        ex = next((u for u in leaking_units if c in u["unit"]), None)
        sample = f"   e.g. {ex['unit']} -> {ex['raw']!r}" if ex else ""
        print(f"  {c}   {codes(c)}{sample}")
    print(f"\n{len(leaking_units)} of {len(data['units'])} probed units leak.")
    print(f"\nwrote {FAILING_PATH.relative_to(PROJECT_ROOT)}"
          f"\n      {LEAKING_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true",
                    help="re-derive the tables from a saved probe, no requests")
    ap.add_argument("--timeout", type=int, default=60)
    args = ap.parse_args()

    data = load_results()
    if not args.report:
        t0 = time.time()
        probe(build_grid(), data, args.timeout)
        probe(context_probes(data, args.timeout), data, args.timeout)
        data["seconds"] = round(time.time() - t0, 1)
        save_results(data)
    write_tables(data)
