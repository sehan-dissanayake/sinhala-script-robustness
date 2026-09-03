# Publishing an anonymous mirror

The paper is submitted under double-blind review, so the artifact link in it must
not identify the authors. Getting this wrong is a desk reject, so the checks below
are worth doing slowly.

## Why a mirror is needed

This GitHub repository is public under an account that names one of the authors,
so it cannot be linked from the submission. The usual solution is
[anonymous.4open.science](https://anonymous.4open.science), which serves a
read-only copy of a repository behind an opaque URL.

It mirrors the repository **as it is**, including the README, commit messages and
notebook contents. Anything identifying in those leaks.

## Before creating the mirror

1. **Run the scrubber.** It must exit zero.

   ```bash
   python tools/anonymize.py --check
   ```

   It looks for the Kaggle account slugs and university index numbers that the
   evaluation notebooks used in their dataset paths, and flags anything else that
   matches the same shape. If it reports an unrecognised string, decide whether it
   identifies anyone and add it to `SUBSTITUTIONS` in `tools/anonymize.py` if so.

2. **Check the README.** It must not contain a clone URL with the account name in
   it, an institution, or author names. The current README has no such URL.

3. **Check for stray files.** `.env`, `kaggle.json`, and anything under
   `data/reference/raw/` are git-ignored and should not appear in the mirror.
   Confirm with `git ls-files | grep -iE "env|kaggle|token"`.

4. **Check commit messages and author metadata.** 4open.science does not usually
   expose git history, but do not rely on that. If any commit message names a
   person, mirror from a squashed orphan branch instead:

   ```bash
   git checkout --orphan anon-submission
   git add -A
   git commit -m "Anonymous submission snapshot"
   git push origin anon-submission
   ```

   Then point 4open.science at that branch. This also removes any chance of the
   history being walked.

5. **Confirm SinhalaMMLU is absent.** Its authors asked that the full set not be
   made public and its licence forbids distributing adaptations, so neither the
   items nor their Romanized twin may appear:

   ```bash
   git ls-files | grep sinhala_mmlu     # should print nothing under data/
   ```

## After creating the mirror

6. **Open the anonymous URL in a private window** and read the rendered README,
   then open two or three notebooks and search the page for the account slugs and
   for `uom`. A mirror is only as anonymous as its least careful page.

7. **Put the URL in the paper.** Replace the placeholder in `paper/acl_latex.tex`:

   ```latex
   \newcommand{\anonrepo}{\url{https://anonymous.4open.science/r/XXXXXXXX}}
   ```

8. **Leave the package name out.** The transliterator is on PyPI, and the project
   page there carries a maintainer name and a link back to this repository. The
   paper deliberately says only that it is released as a pip-installable package.
   Do not add the name until the camera-ready version.

## At camera-ready

Reverse the withholding, all at once:

* replace `\anonrepo` with the real repository URL,
* name the PyPI package and link it,
* switch `\usepackage[review]{acl}` to `\usepackage{acl}`,
* restore the Acknowledgments section, keeping the uroman acknowledgement, which
  its licence requires in any publication that uses it.

The scrubbed Kaggle slugs are cosmetic and need not be restored. Placeholders in
notebook paths are harmless, and student index numbers do not belong in a public
research repository in any case.
