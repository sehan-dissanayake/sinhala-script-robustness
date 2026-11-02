"""Put the reference list of main.tex in order of first citation (Vancouver style).

Reads scripts/bibitems.tex, finds the order in which keys are first cited in
main.tex, and rewrites the thebibliography block. Fails if a cited key has no
entry or an entry is never cited.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEX = HERE.parent / "main.tex"

src = TEX.read_text()
body = src.split(r"\begin{thebibliography}")[0]
order = []
for group in re.findall(r"\\cite[pt]?\{([^}]*)\}", body):
    for key in (k.strip() for k in group.split(",")):
        if key not in order:
            order.append(key)

items = {}
for chunk in re.split(r"\n(?=\\bibitem\{)", (HERE / "bibitems.tex").read_text()):
    m = re.match(r"\\bibitem\{([^}]+)\}", chunk)
    if m:
        items[m.group(1)] = chunk.strip()

missing = [k for k in order if k not in items]
unused = [k for k in items if k not in order]
if missing or unused:
    sys.exit(f"missing entries: {missing}\nuncited entries: {unused}")

block = ("\\begin{thebibliography}{%d}\n\n" % len(order)
         + "\n\n".join(items[k] for k in order) + "\n\n\\end{thebibliography}")
new = re.sub(r"\\begin\{thebibliography\}.*?\\end\{thebibliography\}",
             lambda _: block, src, flags=re.S)
TEX.write_text(new)
print(f"{len(order)} references written in citation order")
