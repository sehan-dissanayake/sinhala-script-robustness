# Building the paper

Two papers live here. This file is about the long one.

| directory | venue | length | compiler |
|---|---|---|---|
| `.` (`acl_latex.tex`) | ACL, archival | 8 page main body, 19 total | XeLaTeX |
| [`globalsouthai/`](globalsouthai/README.md) | GlobalSouthAI @ NeurIPS 2026, non-archival | 4 page body, 27 total | pdfLaTeX |

The workshop paper is written separately for its length rather than compressed
from this one, and reuses the same verified analysis outputs. See its own README
for the build, the page-budget check and the two Sinhala figure placeholders it
needs.

## Compiler

**XeLaTeX is required.** The paper sets Sinhala examples inline, which pdfLaTeX
cannot do. In Overleaf: Menu, then Compiler, then XeLaTeX.

```bash
xelatex acl_latex
bibtex  acl_latex
xelatex acl_latex
xelatex acl_latex
```

## Fonts

| Role | Font | Fallback |
|---|---|---|
| body | TeX Gyre Termes | metric-compatible with Times, ships with TeX Live |
| sans | TeX Gyre Heros | |
| mono | TeX Gyre Cursor | |
| Sinhala | Noto Serif Sinhala | change to `Noto Sans Sinhala` if Overleaf cannot find it |

The Sinhala face is declared once, near the top of `acl_latex.tex`:

```latex
\newfontfamily\sinhalafont{Noto Serif Sinhala}[Script=Sinhala, Scale=MatchLowercase]
```

If compilation fails with "cannot find font", that line is the only thing to
change.

## Files

```
acl_latex.tex     the paper
custom.bib        bibliography, every entry checked against a primary record
acl.sty           ACL style file, copied from acl_latex_template/
acl_natbib.bst    ACL bibliography style, same source
tables/*.tex      generated table bodies, do not edit by hand
figures/*.pdf     generated figures, do not edit by hand
analysis/         the statistics behind every number
```

`tables/` and `figures/` are generated. Regenerate them after any change to the
analysis:

```bash
cd ..                                    # repository root
python paper/analysis/stats_intrinsic.py
python paper/analysis/stats_extrinsic.py
python paper/analysis/stats_robustness.py
python paper/analysis/stats_attestation.py
python paper/tables/make_tables.py
python paper/figures/make_figures.py
python paper/analysis/verify_claims.py
```

`verify_claims.py` restates every number that appears in `acl_latex.tex` and
checks it against the frozen analysis outputs in `analysis/out/`. It prints how
many claims it checked and fails loudly if any has drifted. Run it before every
submission, together with the workshop paper's own guard rails:

```bash
python paper/globalsouthai/make_assets.py
python paper/globalsouthai/check_paper.py
```

## Page budget

The main body must be at most 8 pages. Limitations, Ethics, References and the
appendices do not count. The current build is 8 pages of main body and 19 pages
in total.

To check where the main body ends, look for the `sec:endofmain` label in
`acl_latex.aux`:

```bash
grep endofmain acl_latex.aux
```

The page number in that entry is the last page of the main body. If it exceeds 8,
the float placement parameters near the top of the preamble are the first thing
to look at, then caption length, then prose.

## Review version

`\usepackage[review]{acl}` produces the anonymous version with line numbers.
Switch to `\usepackage{acl}` for camera-ready, or `\usepackage[preprint]{acl}` for
a non-anonymous preprint.
