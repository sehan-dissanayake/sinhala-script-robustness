"""Guard rails for the workshop paper.

Two checks, both cheap enough to run on every edit:

1. The content ends within the four page limit. GlobalSouthAI counts references,
   appendices and the NeurIPS checklist separately, so the test is the page that
   \\label{sec:endofmain} lands on, read out of main.aux.

2. The workshop paper introduces no number that has not already been verified.
   Every numeric token in main.tex and checklist.tex must also appear in
   ../acl_latex.tex, whose 251 numeric claims are checked against the frozen
   analysis outputs by paper/analysis/verify_claims.py. Anything that cannot be
   matched that way needs an entry in ALLOW with a reason.

Run from the repository root, after compiling:

    python paper/globalsouthai/check_paper.py
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = os.path.dirname(HERE)

PAGE_LIMIT = 4

# Numbers that legitimately appear only in this version. Each one is either a
# structural constant of this document or a value verified elsewhere.
ALLOW = {
    # Document structure and the venue's own numbers.
    "2026": "NeurIPS 2026, the venue year",
    "40": "\"40th Conference on Neural Information Processing Systems\", set by the style file",
    "1": "checklist item numbering and \"1-2 sentence\" in the retained guidelines",
    "2": "checklist guidelines text",
    "3": "checklist guidelines text",
    "4": "checklist guidelines text",
    "96": "\"96% CI\" inside a checklist guideline we must keep verbatim",
    "1.8": "the \\sinword placeholder height, a typesetting length",
    "2.0": "the \\sinword placeholder height, a typesetting length",
    "0.25": "the \\sinword placeholder baseline shift, a typesetting length",
    "0.94": "\\includegraphics width fraction, a typesetting length",
    "15": "\\textfloatsep, a typesetting length",
    "14": "\\floatsep, a typesetting length",
    # Analysis values printed at a different precision than the long version.
    "0.174": "synthetic-vs-human minimum, verify_claims checks it as 0.17",
    "0.240": "synthetic-vs-human maximum, verify_claims checks it as 0.24",
    "0.219": "synthetic-vs-human median, in synthetic_vs_human.json",
    "45": "median Matthews retention, verify_claims checks mcc_retained_pct",
    "55": "the complement of that retention, stated in a figure caption",
}

# Values this version states in prose that the long version only puts in a
# generated table. These are checked against the analysis outputs directly.
DIRECT = [
    ("Hormoz-8B SOLD offensive rate, Sinhala", "sold:Hormoz-8B:u_off_rate", 9.8),
    ("Hormoz-8B SOLD offensive rate, Romanized", "sold:Hormoz-8B:r_off_rate", 20.7),
    ("Swa-bhasha lexicon words", "attest:lexicon_words", 449598),
    ("Swa-bhasha lexicon spellings", "attest:lexicon_spellings", 7075844),
    ("SOLD attestation tercile gap, low", "tercile:low", 5.0),
    ("SOLD attestation tercile gap, middle", "tercile:mid", 7.2),
    ("SOLD attestation tercile gap, high", "tercile:high", 7.3),
]

NUM = re.compile(r"\d+(?:\.\d+)?")


def numbers(text: str) -> list[tuple[str, int]]:
    """Numeric tokens with their line numbers, thousands separators removed."""
    out = []
    for i, line in enumerate(text.split("\n"), 1):
        if line.lstrip().startswith("%"):
            continue
        line = line.replace("{,}", "").replace("\\,", "")
        for m in NUM.finditer(line):
            out.append((m.group(0), i))
    return out


def page_check() -> list[str]:
    aux = os.path.join(HERE, "main.aux")
    if not os.path.exists(aux):
        return ["main.aux is missing, compile main.tex first"]
    m = re.search(r"\\newlabel\{sec:endofmain\}\{\{[^}]*\}\{(\d+)\}", open(aux).read())
    if not m:
        return ["sec:endofmain is not in main.aux, run pdflatex twice"]
    page = int(m.group(1))
    if page > PAGE_LIMIT:
        return [f"content runs to page {page}, the limit is {PAGE_LIMIT}"]
    print(f"content ends on page {page} of {PAGE_LIMIT}")
    return []


def number_check() -> list[str]:
    acl = open(os.path.join(PAPER, "acl_latex.tex"), encoding="utf-8").read()
    known = {n for n, _ in numbers(acl)}
    known |= set(ALLOW)
    for _, _, v in DIRECT:
        known |= {f"{v:g}", f"{v:.1f}", str(v)}

    problems = []
    for fn in ("main.tex", "checklist.tex"):
        text = open(os.path.join(HERE, fn), encoding="utf-8").read()
        for tok, line in numbers(text):
            if tok not in known:
                problems.append(f"{fn}:{line}: {tok} is not verified anywhere")
    if not problems:
        print("every number in main.tex and checklist.tex is a verified value")
    return problems


def direct_check() -> list[str]:
    """Check the handful of prose values against the frozen analysis outputs."""
    import json

    sys.path.insert(0, os.path.join(PAPER, "analysis"))
    import pandas as pd

    import common as C

    at = json.load(open(os.path.join(C.OUT_DIR, "attestation_numbers.json")))
    sd = pd.read_csv(os.path.join(C.OUT_DIR, "sold_detail.csv")).set_index("model")

    problems = []
    for claim, key, printed in DIRECT:
        kind, *rest = key.split(":")
        if kind == "sold":
            value = float(sd.loc[rest[0], rest[1]])
        elif kind == "attest":
            value = float(at["attestation"][rest[0]])
        else:
            value = float(at["downstream"][rest[0]]["gap"])
        if abs(value - printed) > 0.05:
            problems.append(f"{claim}: paper says {printed}, analysis gives {value}")
    if not problems:
        print(f"{len(DIRECT)} prose-only values match the analysis outputs")
    return problems


def main() -> None:
    problems = page_check() + number_check() + direct_check()
    if problems:
        print(f"\n{len(problems)} PROBLEM(S):")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("workshop paper checks pass")


if __name__ == "__main__":
    main()
