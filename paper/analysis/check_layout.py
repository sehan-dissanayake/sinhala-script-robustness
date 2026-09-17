"""Layout guard rails for the compiled paper.

Three things this catches that a LaTeX run does not complain about.

Two of them are ours and make the check fail:

* widows, meaning a paragraph whose last line holds only a word or two;
* the page budget, since the main body has to end inside eight pages while
  references and appendices do not count.

The third is reported but does not fail, because it is in the template and we are
not allowed to edit acl.sty: its `review' option numbers lines through lineno,
which chooses a margin per column and gets the side wrong for the first lines of a
column, printing a grey line number on top of a word. There is no LaTeX error and
no overfull box. The unmodified paper does it 74 times, and the count moves with
pagination, so the number is worth watching but a non-zero value is not a defect
this repository introduced. Loading subcaption makes it worse, which is why the
paper references figure panels through a plain macro instead.

Needs a compiled PDF and pdftotext. Run from the repository root:

    python paper/analysis/check_layout.py paper/build/main.pdf
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile

SHORT_LINE_CHARS = 14
# Count for the paper with none of our changes, for reference only.
TEMPLATE_BASELINE = 74
SKIP = re.compile(r"^(References|Limitations|Abstract|[A-Z]\s|\d+(\.\d+)*\s)")


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def page_count(pdf: str) -> int:
    info = run(["pdfinfo", pdf])
    m = re.search(r"^Pages:\s+(\d+)", info, re.M)
    return int(m.group(1)) if m else 0


# ------------------------------------------------------- line-number overlaps --

def boxes(pdf: str, page: int):
    xml = run(["pdftotext", "-bbox", "-f", str(page), "-l", str(page), pdf, "-"])
    out = []
    for m in re.finditer(
            r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">'
            r'([^<]*)</word>', xml):
        x0, y0, x1, y1, t = m.groups()
        out.append((t, float(x0), float(y0), float(x1), float(y1)))
    return out


def overlaps(pdf: str, n_pages: int):
    """Words whose bounding box genuinely intersects another word's box.

    Two pieces of text can only share the same rectangle if one was placed on top
    of the other, so this needs no threshold and no guessing.
    """
    bad = []
    for page in range(1, n_pages + 1):
        ws = boxes(pdf, page)
        for i, (t, x0, y0, x1, y1) in enumerate(ws):
            if not re.fullmatch(r"\d{1,4}", t):
                continue
            for u, ux0, uy0, ux1, uy1 in ws:
                if u == t and (ux0, uy0) == (x0, y0):
                    continue
                if re.fullmatch(r"\d{1,4}", u):
                    continue
                # vertical overlap of at least half a line and any horizontal overlap
                vo = min(y1, uy1) - max(y0, uy0)
                ho = min(x1, ux1) - max(x0, ux0)
                if vo > 3 and ho > 0.5:
                    bad.append((page, t, u, round(x0, 1)))
                    break
    return bad


# ------------------------------------------------------------------- widows ----

def body_lines(pages: list[str]):
    seen = {}
    for page in pages:
        for raw in page.split("\n"):
            m = re.match(r"^\s*(\d{1,4})\s{2,}(.*\S)\s*$", raw)
            if m:
                seen.setdefault(int(m.group(1)), m.group(2).strip())
            else:
                m = re.match(r"^\s*(.*\S)\s{2,}(\d{1,4})\s*$", raw)
                if m:
                    seen.setdefault(int(m.group(2)), m.group(1).strip())
    return sorted(seen.items())


def prose_pages(pages: list[str]) -> list[str]:
    """Pages before the reference list.

    A short final line inside a bibliography entry, or in an appendix table note,
    is normal typesetting. The check is about running prose, so everything from the
    References heading onwards is dropped.
    """
    out = []
    for page in pages:
        # The heading is the only place this word appears outside a citation.
        if re.search(r"\bReferences\b", page):
            break
        out.append(page)
    return out


def widows(lines):
    hits = []
    for i, (n, text) in enumerate(lines):
        if not re.search(r"[.!?]$", text) or len(text) > SHORT_LINE_CHARS:
            continue
        if SKIP.match(text):
            continue
        nxt = lines[i + 1][1] if i + 1 < len(lines) else ""
        if nxt[:1].isupper() or nxt == "":
            hits.append((n, text))
    return hits


def page_budget(aux: str, limit: int = 8):
    """Page the main body ends on, read from the label after the conclusion."""
    try:
        text = open(aux, encoding="utf-8").read()
    except OSError:
        return None, None
    m = re.search(r"\\newlabel\{sec:endofmain\}\{\{[^}]*\}\{(\d+)\}", text)
    if not m:
        return None, None
    return int(m.group(1)), limit


def main():
    pdf = sys.argv[1] if len(sys.argv) > 1 else "paper/build/main.pdf"
    n = page_count(pdf)
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        out = f.name
    run(["pdftotext", "-layout", pdf, out])
    pages = open(out, encoding="utf-8").read().split("\f")

    print(f"{pdf}: {n} pages")
    problems = 0

    ov = overlaps(pdf, n)
    if ov:
        print(f"\nnote: {len(ov)} line number(s) printed over body text, "
              f"template baseline is {TEMPLATE_BASELINE}")
        for page, num, word, x in ov[:8]:
            print(f"  page {page}: {num} over {word!r} (x={x})")
        print("  acl.sty's review line numbering does this on its own; not a failure")
    else:
        print("no line numbers printed over text")

    prose = prose_pages(pages)
    lines = body_lines(prose)
    w = widows(lines)
    if w:
        problems += 1
        print(f"\n{len(w)} short paragraph-final line(s) in the prose "
              f"({len(prose)} pages checked):")
        for num, t in w:
            print(f"  line {num}: {t!r}")
    else:
        print("no short paragraph-final lines")

    end, limit = page_budget(re.sub(r"\.pdf$", ".aux", pdf))
    if end is None:
        print("\nno .aux beside the PDF, page budget not checked")
    elif end > limit:
        problems += 1
        print(f"\nmain body ends on page {end}, over the {limit}-page limit")
    else:
        print(f"main body ends on page {end} of {limit}")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
