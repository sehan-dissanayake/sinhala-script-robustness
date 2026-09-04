#!/usr/bin/env bash
# Rebuild the inline Sinhala snippets of ../acl_latex.tex.
#
# The paper is pdfLaTeX and cannot set the Sinhala script, so each snippet is
# compiled here, once, by a Unicode engine into a tightly cropped PDF that the
# paper includes as an inline graphic. The PDFs are committed, so building the
# paper needs pdfLaTeX and nothing else. Run this only when a snippet changes.
#
#   ./build.sh              # LuaLaTeX, the default
#   ENGINE=xelatex ./build.sh
#
# Requires the Noto Serif Sinhala face. On Debian/Ubuntu:
#   apt-get install fonts-noto-serif-sinhala
# On Fedora/Amazon Linux:
#   dnf install google-noto-serif-sinhala-fonts
# On Overleaf both Noto Sinhala faces are already present.
set -euo pipefail
cd "$(dirname "$0")"

ENGINE="${ENGINE:-lualatex}"
command -v "$ENGINE" >/dev/null || { echo "$ENGINE not found" >&2; exit 1; }

for src in si-*.tex; do
  [ "$src" = "si-common.tex" ] && continue
  echo "== $src"
  "$ENGINE" -interaction=nonstopmode -halt-on-error "$src" >/dev/null
done

rm -f si-*.aux si-*.log
echo
echo "Snippet page boxes, which must all be identical:"
for pdf in si-*.pdf; do
  printf '  %-16s ' "$pdf"
  pdfinfo "$pdf" 2>/dev/null | sed -n 's/^Page size: *//p' || echo '(pdfinfo unavailable)'
done
