# Inline Sinhala for a pdfLaTeX paper

`../acl_latex.tex` is compiled with pdfLaTeX, which cannot set the Sinhala script.
The five Sinhala examples in the paper are therefore built here, once, by a Unicode
engine into tightly cropped one-line PDFs, and the paper includes them as inline
graphics. The PDFs are committed, so **building the paper needs pdfLaTeX and
nothing else** — no fontspec, no font installation, no Overleaf compiler change.

These files are the only ones in `paper/` that contain Sinhala codepoints.
`../acl_latex.tex` is pure ASCII.

## The five examples

| snippet | romanized | IPA | used in |
| --- | --- | --- | --- |
| `si-kohomada` | `kohomada` | kɒhɒmʌðʌ | §1, the spelling-variation example |
| `si-tha` | `th` | θʌ | §3.2, the digraph conventions |
| `si-wa` | `w` | vʌ | §3.2, the digraph conventions |
| `si-wesak` | `wesak` | vɛsʌk | §3.2, the worked example |
| `si-uthsawayeedii` | `uthsawayeedii` | ʊθsʌvʌjeːðiː | §3.2, the worked example |
| `si-bauddhayin` | `bauddhayin` | baʊððʰʌjɪn | §3.2, the worked example |
| `si-nya` | — | ɲʌ | §F.1, the sequences the web romanizer drops |

The three-word phrase of §3.2 is one file per word, not one file for the phrase,
so the paper can still break a line between words the way it could when the phrase
was live text. A single 134pt image cannot break anywhere and forced a badly
stretched line in a 228pt column.

Pronunciations come from the [Sinhala transliteration
tables](https://www.nongnu.org/sinhala/doc/transliteration/sinhala-transliteration_4.html).
The paper does **not** take the IPA from these PDFs: it sets it natively with
`tipa`, in the Times-companion `xipa10` face, so it stays selectable, searchable
text that scales with the surrounding font. Each `.tex` here repeats its IPA in a
comment so the two cannot drift apart unnoticed.

## Rebuilding

Only needed when a snippet changes.

```bash
./build.sh                  # LuaLaTeX, the default
ENGINE=xelatex ./build.sh   # XeLaTeX works too
```

The script compiles every `si-*.tex` except the shared preamble, removes the `.aux`
and `.log` files, and prints the page box of each result. **Those boxes must all be
the same height**; that is the invariant the paper depends on, and the next section
says why.

It needs the Noto Serif Sinhala face:

```bash
apt-get install fonts-noto-serif-sinhala      # Debian, Ubuntu
dnf install google-noto-serif-sinhala-fonts   # Fedora, Amazon Linux
```

Overleaf already has it. If a machine has only Noto Sans Sinhala, change the one
`\newfontfamily` line in `si-common.tex`.

## The sizing contract

`si-common.tex` carries the long version. In short:

- Each snippet is set at the paper's body size with the Sinhala face scaled to the
  x-height of the paper's body font, so its natural size is already correct and the
  paper never rescales it to fit.
- `standalone` crops to the TeX box, so a word with no descender would crop shorter
  than one with a descender, and forcing every file to a common height would then
  set the same script at different sizes. Every snippet therefore carries one
  invisible strut, 0.90 of the body size up and 0.30 down. All crops come out
  13.14pt tall with the baseline a quarter of that height above the bottom edge.
- The paper places any of them with one rule and no per-file tuning:

  ```latex
  \raisebox{-0.25\height}{%
    \includegraphics[height=1.2\dimexpr\f@size pt\relax]{sinhala/<name>}}
  ```

  which is what `\sinhalaglyph` in `../acl_latex.tex` does. Measuring against
  `\f@size` rather than `1em` holds the scale factor at exactly 1 whichever Times
  each document loads, and still lets an example follow the surrounding size.
- The strut is deliberately not roomier than it needs to be. At 9.86pt above the
  baseline it still fits under the 13.6pt leading of the body text next to a
  previous line's descender, so an example never pushes its line off the baseline
  grid. `\sinhala` raises a hard error if a snippet outgrows the strut, rather than
  letting the crop clip it silently.

## Adding an example

1. Copy any `si-*.tex`, put the Sinhala in `\sinhala{...}`, and record the
   romanization and IPA in the header comment.
2. Run `./build.sh` and check that the new page box matches the others.
3. In `../acl_latex.tex`, add a named macro next to the other five, e.g.
   `\newcommand{\sifoo}{\siex{si-foo}{...}}`, with the IPA in `tipa` input syntax.
   Use the macro in the body, so the paper stays ASCII.
4. Add a row to the table above.
