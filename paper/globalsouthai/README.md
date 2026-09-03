# GlobalSouthAI @ NeurIPS 2026 submission

A four page short paper for the non-archival GlobalSouthAI workshop. It is written
for this length rather than compressed from `../acl_latex.tex`: the framing leads
with what the Sinhala case study says about evaluating Global South languages, and
the venue-specific section 5 has no counterpart in the long version.

This directory is self-contained. Uploading it to Overleaf and setting the compiler
to pdfLaTeX is enough.

```
main.tex           the paper
checklist.tex      the NeurIPS checklist, filled in, \input at the end of main.tex
neurips_2026.sty   the official style file, unmodified
custom.bib         copy of ../custom.bib
figures/           regenerated at NeurIPS page geometry, not scaled down
tables/            row bodies only, column specs live in main.tex
make_assets.py     regenerates figures/ and tables/
fill_checklist.py  writes the checklist answers, in document order
check_paper.py     page budget and numeric-claim guard rails
```

## Build

```bash
pdflatex main && bibtex main && pdflatex main && pdflatex main
python paper/globalsouthai/check_paper.py     # from the repository root
```

`check_paper.py` does two things. It reads the page that `\label{sec:endofmain}`
lands on out of `main.aux` and fails if the content runs past page 4, and it
asserts that every numeric token in `main.tex` and `checklist.tex` also appears in
`../acl_latex.tex`, whose 251 numeric claims are checked against the frozen
analysis outputs by `paper/analysis/verify_claims.py`. A handful of values that
this version states in prose while the long version only puts them in a generated
table are checked against the analysis outputs directly.

Run both, in this order, after any change to the analysis:

```bash
python paper/analysis/verify_claims.py
python paper/globalsouthai/check_paper.py
```

## Regenerating figures and tables

```bash
python paper/globalsouthai/make_assets.py
```

Sixteen table bodies are copied from `../tables/`. Two are specific to this paper:

- `tab_gs_decomp.tex`, a compact summary of the perplexity decomposition
- `tab_gs_intrinsic.tex`, all 31 checkpoints in one block narrow enough for a
  5.5 inch page

The figures are regenerated at 5.5 inch text width rather than scaled down from
the two-column versions, which would shrink their labels below legibility. Figure 1
is also built shorter than in the long version, through `make_figures.H1`, because
a four page budget cannot afford 2.6 inches of figure. Reducing the height rather
than the width keeps the label sizes intact.

## Sinhala script

pdfLaTeX cannot set Sinhala, so the two inline Sinhala snippets go through the
`\sinword` macro, which prints a visible grey placeholder until the PDF images
exist. Supply these two files, cropped tight with no white margin:

| file | content | romanization | used in |
| --- | --- | --- | --- |
| `figures/sin-kohomada.pdf` | one word | `kohomada` | section 1 |
| `figures/sin-wesak.pdf` | three words | `wesak uthsawayeedii bauddhayin` | section 2 |

Then change `\sinhalafigsfalse` to `\sinhalafigstrue` in the preamble. Those are
the only two slots in the paper. The macro sets them at `height=2.0ex` with a
`-0.25ex` baseline shift, so a tight crop matters more than the source resolution.

Adding the images makes the two lines slightly narrower than the placeholders, so
the page budget has headroom rather than the reverse. Re-run `check_paper.py`
anyway.

## Style file options

`main.tex` uses the plain `\usepackage{neurips_2026}` default, which is anonymous
with line numbers and the "Submitted to 40th Conference..." footer. The
`[dblblindworkshop]` option additionally requires `\workshoptitle` and looks
near-identical at submission time. Use `[final]` for a camera-ready version.
