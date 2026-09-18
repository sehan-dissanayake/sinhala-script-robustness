"""Remove author-identifying strings from the repository.

Why this exists
---------------
The evaluation notebooks were run on Kaggle, so they carry dataset paths of the
form ``/kaggle/input/datasets/<owner>/...``. The owner slugs, and the university
index numbers used as some of those slugs, identify the authors and their
institution. Any anonymous mirror of this repository, for example one created
for double-blind review through anonymous.4open.science, would leak them.

The strings are replaced with neutral placeholders that keep every path the same
shape, so the notebooks stay readable and their history stays intelligible. The
mapping is deliberately not recorded anywhere in the repository.

Usage
-----
    python tools/anonymize.py --check     # report only, exit 1 if anything is left
    python tools/anonymize.py             # rewrite in place

Run ``--check`` as the last step before publishing an anonymous mirror. It is
also worth running after adding any new notebook.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Identifying string -> placeholder. Kaggle owner slugs first, then the index
# numbers that were used as slugs.
SUBSTITUTIONS = {
    "dasunillangasinghe": "anon-owner-a",
    "sehandissanayake": "anon-owner-b",
    "shanilpraveen": "anon-owner-c",
    "uom220131a": "anon-owner-d",
    "uom220165f": "anon-owner-e",
    "uom220538d": "anon-owner-f",
}

# Anything matching these is reported by --check even if it is not in the table
# above, so a new collaborator's slug or identifying institution cannot slip
# through unnoticed.
SUSPICIOUS = [
    re.compile(r"uom\d{6}[a-z]", re.I),                  # university index numbers
    re.compile(r"github\.com/[A-Za-z0-9_-]+/sinhala", re.I),
    re.compile(r"staff\.uom\.lk", re.I),
    re.compile(r"cse\.mrt\.ac\.lk", re.I),
    re.compile(r"\bnisansads\b", re.I),
    re.compile(r"\bNisansa(?:\s+Sir)?\b", re.I),
    re.compile(r"\b(sehandissanayake|dasunillangasinghe|shanilpraveen)\b", re.I),
]

SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules", ".playwright-mcp", ".idea", ".vscode"}
# Large untracked caches, raw reference data, and credentials
SKIP_PATHS = {
    os.path.normpath(p)
    for p in [
        os.path.join("data", "reference", "raw"),
        os.path.join("data", "reference", "cache"),
        os.path.join("data", "reference", "parallel"),
        os.path.join("results", "method_evaluation", "per_item"),
        "kaggle.json",
    ]
}
TEXT_EXT = {".py", ".ipynb", ".md", ".txt", ".json", ".tex", ".csv", ".yml",
            ".yaml", ".cfg", ".toml", ".sh"}


def candidate_files():
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel_root = os.path.normpath(os.path.relpath(root, REPO))
        if any(rel_root == p or rel_root.startswith(p + os.sep) for p in SKIP_PATHS):
            continue
        for fn in files:
            rel_file = os.path.normpath(os.path.relpath(os.path.join(root, fn), REPO))
            if rel_file in SKIP_PATHS:
                continue
            if os.path.splitext(fn)[1].lower() in TEXT_EXT:
                yield os.path.join(root, fn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report without rewriting, exit 1 if anything is found")
    args = ap.parse_args()

    hits: dict[str, dict[str, int]] = {}
    suspicious: dict[str, list[str]] = {}
    changed = 0

    for path in candidate_files():
        rel = os.path.relpath(path, REPO)
        if rel == os.path.join("tools", "anonymize.py"):
            continue
        try:
            text = open(path, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue

        found = {k: text.count(k) for k in SUBSTITUTIONS if k in text}
        extra = sorted({m.group(0) for pat in SUSPICIOUS for m in pat.finditer(text)}
                       - set(SUBSTITUTIONS))
        if found:
            hits[rel] = found
        if extra:
            suspicious[rel] = extra

        if found and not args.check:
            for old, new in SUBSTITUTIONS.items():
                text = text.replace(old, new)
            open(path, "w", encoding="utf-8").write(text)
            changed += 1

    if hits:
        verb = "found" if args.check else "rewrote"
        print(f"{verb} identifying strings in {len(hits)} file(s):")
        for rel, found in sorted(hits.items()):
            print(f"  {rel}: " + ", ".join(f"{k} x{v}" for k, v in sorted(found.items())))
    else:
        print("no known identifying strings present")

    if suspicious:
        print("\nunrecognised strings that look identifying, add them to "
              "SUBSTITUTIONS if they are:")
        for rel, extra in sorted(suspicious.items()):
            print(f"  {rel}: {', '.join(extra)}")

    if args.check and (hits or suspicious):
        sys.exit(1)
    if not args.check:
        print(f"\n{changed} file(s) rewritten. Re-run with --check to confirm.")


if __name__ == "__main__":
    main()
