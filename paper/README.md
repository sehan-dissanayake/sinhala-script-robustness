# ACL submission

`acl_latex.tex` is the paper. **It must be compiled with XeLaTeX**, not pdfLaTeX,
because it sets Sinhala examples. In Overleaf: Menu → Compiler → XeLaTeX.

Current state: 8 pages of content (§1–§7 end at the bottom of page 8), then
Limitations, Ethics, References and four appendices. Zero LaTeX errors, zero
overfull boxes. Anonymous review mode.

## Layout

| Path | What it is |
|---|---|
| `acl_latex.tex` | the paper |
| `custom.bib` | bibliography, every entry checked against a primary record |
| `acl.sty`, `acl_natbib.bst` | unmodified copies from `acl_latex_template/` |
| `analysis/` | statistics; writes everything the paper cites into `analysis/out/` |
| `tables/` | generates the LaTeX table bodies from `analysis/out/` |
| `figures/` | generates the figures from `analysis/out/` |

## Regenerating everything

Run from the repository root, in this order:

```bash
python paper/analysis/stats_intrinsic.py     # 31 checkpoints, ~5 min
python paper/analysis/stats_extrinsic.py     # 10 checkpoints x 3 tasks, ~10 min
python paper/tables/make_tables.py
python paper/figures/make_figures.py
python paper/analysis/verify_claims.py       # must print "all claims ... match"
```

Then build:

```bash
cd paper && xelatex acl_latex && bibtex acl_latex && xelatex acl_latex && xelatex acl_latex
```

## Why the numbers cannot drift

No number in the paper is typed by hand twice. Table bodies under `tables/*.tex`
are generated from `analysis/out/`, and `analysis/verify_claims.py` restates every
number that appears in the prose, the abstract and the captions and checks it
against the same source. If a re-run moves a value, `verify_claims.py` fails and
names the claim that has gone stale. It currently checks 160 claims.

`\input` breaks LaTeX's alignment scanner inside a `tabular`, so the generated
bodies are pulled in with `\rows{...}`, defined in the preamble over the TeX
primitive. Use `\rows`, not `\input`, for anything inside a table.

## Before camera-ready

1. Switch `\usepackage[review]{acl}` to `\usepackage{acl}`.
2. Replace `\author{Anonymous ACL submission}` with the real author block.
3. Fill in `\anonrepo` and `\pkgurl` in the preamble, and publish the package.
4. Resolve the `TODO` comment in §2 about `chamikara-sumanathilaka-2026`: that is
   the one bibliography entry whose metadata could not be verified against a
   primary record, so it is currently cited nowhere. Confirm it or delete it.
5. Add the Phi-4 downstream results. Everything needed is parameterised: add the
   entry to `EXTRINSIC_MODELS` in `analysis/common.py`, re-run the five commands
   above, and update the two places in the prose that say "ten" checkpoints and
   "1.1B to 9B" (search for `1.1B to 9B`). The tables and figures update
   themselves.
