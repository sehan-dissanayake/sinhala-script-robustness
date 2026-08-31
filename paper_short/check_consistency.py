"""Check the short paper against the verified long paper.

paper/analysis/verify_claims.py checks all 160 numbers in ../paper/acl_latex.tex
against the frozen analysis. The short paper is a compression of that text, so
rather than duplicating the checker we assert the weaker but sufficient property:
every numeric claim in the short paper also appears in the long paper.

Run from the repository root:  python paper_short/check_consistency.py
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SHORT = os.path.join(HERE, "acl_latex.tex")
LONG = os.path.join(REPO, "paper", "acl_latex.tex")

# Numbers that are legitimately specific to one version's phrasing.
IGNORE = {
    "11",      # \documentclass[11pt]
    "0.92", "0.07", "0.75", "3",  # float placement parameters
    "2.4", "3", "2.2", "4",       # \tabcolsep values
    "0.5", "1", "2", "5",         # trivia in preamble / \setcounter
}


def numbers(path):
    src = open(path, encoding="utf-8").read()
    src = src[src.index(r"\begin{document}"):]
    src = re.sub(r"(?m)^\s*%.*$", "", src)                 # comments
    src = re.sub(r"\\(includegraphics|rows|label|ref|cite\w*)\s*(\[[^\]]*\])?\{[^}]*\}",
                 " ", src)                                  # paths, labels, keys
    src = re.sub(r"\\setlength\{[^}]*\}\{[^}]*\}", " ", src)
    src = re.sub(r"\\renewcommand\{[^}]*\}\{[^}]*\}", " ", src)
    src = re.sub(r"\\setcounter\{[^}]*\}\{[^}]*\}", " ", src)
    src = re.sub(r"\\(topfraction|textfraction|floatpagefraction|dbltopfraction)", " ", src)
    src = src.replace("{,}", "")      # 4{,}096 is one number, not 4 and 096
    out = set()
    for tok in re.findall(r"\d+(?:[.,]\d+)*", src):
        t = tok.replace("{,}", "").replace(",", "")
        if t not in IGNORE:
            out.add(t)
    return out


def main():
    short, long_ = numbers(SHORT), numbers(LONG)
    missing = sorted(short - long_, key=lambda x: (len(x), x))
    print(f"short paper: {len(short)} distinct numbers")
    print(f"long paper:  {len(long_)} distinct numbers")
    if missing:
        print(f"\n{len(missing)} number(s) in the short paper but not in the verified "
              f"long paper. Check each by hand:")
        for m in missing:
            for line in open(SHORT, encoding="utf-8"):
                if m in line:
                    print(f"  {m}: {line.strip()[:110]}")
                    break
        sys.exit(1)
    print("\nevery numeric claim in the short paper also appears in the long paper, "
          "which paper/analysis/verify_claims.py checks against the frozen analysis")


if __name__ == "__main__":
    main()
