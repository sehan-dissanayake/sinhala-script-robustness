#!/usr/bin/env python3
"""Reproduce the margin test in ACL's pubcheck, which rejects a paper for a bleed.

aclpubcheck itself needs Python 3.10, so this repeats just the margin check with
pdfplumber. The text block edges are read off the typeset page rather than
assumed: justified body text ends exactly on the right edge, so the 98th
percentile of word x1 over the whole document is that edge, and the 2nd
percentile of x0 is the left one. A word past either by more than a rounding
tolerance is a real bleed and ACL will report it.

Run on the PDF without line numbers, which is what the checker expects:

    sed 's/\\[review\\]{acl}/{acl}/' paper/main.tex > final.tex && pdflatex final
    python paper/analysis/check_margins.py final.pdf
"""
from __future__ import annotations

import statistics
import sys

import pdfplumber

TOL = 2.0  # points, for glyph side bearings and rounding


def main(path: str) -> int:
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_words())

    xs1 = sorted(w["x1"] for words in pages for w in words)
    xs0 = sorted(w["x0"] for words in pages for w in words)
    right = statistics.quantiles(xs1, n=100)[97]
    left = statistics.quantiles(xs0, n=100)[1]
    print(f"{path}: text block from {left:.1f} to {right:.1f}")

    bad = 0
    for n, words in enumerate(pages, 1):
        for w in words:
            if w["x1"] > right + TOL:
                over, side = w["x1"] - right, "RIGHT"
            elif w["x0"] < left - TOL:
                over, side = left - w["x0"], "LEFT"
            else:
                continue
            bad += 1
            print(f"  page {n}: {side} margin by {over:5.2f}pt  {w['text'][:40]!r}  "
                  f"x0={w['x0']:.1f} x1={w['x1']:.1f}")

    print(f"{bad} margin violation(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
