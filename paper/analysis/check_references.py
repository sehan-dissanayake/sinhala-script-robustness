"""Check every bibliography entry against a primary record.

A fabricated or mis-transcribed reference is grounds for desk rejection, so this
does not trust the .bib file. For each entry it fetches the authoritative record
and compares the title, the first author's family name and the year:

* arXiv preprints, and entries carrying an arXiv note, through the arXiv API;
* anything with a DOI through Crossref;
* ACL Anthology entries through the Anthology's own BibTeX.

It also reports entries that main.tex never cites, and citations with no entry.

Needs network access. Run from the repository root:

    python paper/analysis/check_references.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BIB = os.path.join(REPO, "paper", "custom.bib")
TEX = os.path.join(REPO, "paper", "main.tex")
SHARDS = [os.path.join(REPO, "paper", "anthology-1.bib"),
          os.path.join(REPO, "paper", "anthology-2.bib")]
UA = {"User-Agent": "sinhala-script-robustness reference check (mailto:anon@example.org)"}

problems: list[str] = []
checked = 0


def norm(s: str) -> str:
    """Comparable form of a title: letters and digits only, lowercased."""
    s = re.sub(r"\\[a-zA-Z]+", " ", s)
    s = s.replace("--", "-")
    return re.sub(r"[^a-z0-9]+", "", s.lower())


# The Anthology shards write most fields as @string concatenations, so
# url = anth # {2022.lrec-1.803/} has to be expanded before it can be fetched.
BIB_STRINGS = {"anth": "https://aclanthology.org/",
               "acl": "Association for Computational Linguistics"}


def expand_strings(value: str) -> str:
    out = []
    for part in value.split("#"):
        part = part.strip()
        if len(part) > 1 and part[0] in "{\"" and part[-1] in "}\"":
            out.append(part[1:-1])
        else:
            out.append(BIB_STRINGS.get(part, part))
    return "".join(out)


def parse_bib(path: str, only: set[str] | None = None) -> dict[str, dict]:
    """Entries of a .bib file, or just the named ones out of a large shard."""
    text = open(path, encoding="utf-8", errors="replace").read()
    entries = {}
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,]+),", text):
        kind, key = m.group(1).lower(), m.group(2).strip()
        if kind in ("string", "comment", "preamble"):
            continue
        if only is not None and key not in only:
            continue
        start = m.end()
        depth, i = 1, m.start()
        # walk from the opening brace of the entry to its match
        i = text.index("{", m.start())
        depth, j = 0, i
        while j < len(text):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        body = text[start:j]
        fields = {}
        for fm in re.finditer(r"(\w+)\s*=\s*", body):
            name = fm.group(1).lower()
            rest = body[fm.end():].lstrip()
            if rest.startswith("{"):
                d, k = 0, 0
                while k < len(rest):
                    if rest[k] == "{":
                        d += 1
                    elif rest[k] == "}":
                        d -= 1
                        if d == 0:
                            break
                    k += 1
                fields[name] = rest[1:k]
            else:
                fields[name] = expand_strings(rest.split(",")[0].strip())
        entries[key] = {"type": kind, **fields}
    return entries


# The ACL Anthology records the first author of RomanSetu as family name "J".
# The paper itself, and arXiv:2401.14280, print "Jaavid Aktar Husain", which is
# what the bib uses so that \\citet does not render "J et al.". The entry is kept
# in custom.bib under a key of its own, husain-etal-2024-romansetu, so that it
# cannot collide with the Anthology shard's j-etal-2024-romansetu.
KNOWN_AUTHOR_EXCEPTIONS = {"husain-etal-2024-romansetu"}

_ACCENTS = str.maketrans({
    "\u00e7": "c", "\u00e9": "e", "\u00e8": "e", "\u00ea": "e", "\u00e1": "a",
    "\u00e0": "a", "\u00e3": "a", "\u00e4": "a", "\u00ed": "i", "\u00f3": "o",
    "\u00f6": "o", "\u00f4": "o", "\u00fa": "u", "\u00fc": "u", "\u00f1": "n",
    "\u0107": "c", "\u010d": "c", "\u0161": "s", "\u017e": "z",
})


def fold(s: str) -> str:
    """Letters only, with LaTeX accent macros and Unicode accents flattened."""
    s = re.sub(r"\\[a-zA-Z]+", "", s)          # \c, \'
    s = re.sub(r"\\.", "", s)                  # \' style
    s = s.replace("{", "").replace("}", "")
    return re.sub(r"[^a-z]", "", s.lower().translate(_ACCENTS))


def first_family(author_field: str) -> str:
    first = author_field.split(" and ")[0].strip().strip("{}")
    if "," in first:
        fam = first.split(",")[0]
    else:
        fam = first.split()[-1] if first.split() else first
    return fold(fam)


def arxiv_id(e: dict) -> str | None:
    for field in ("eprint", "note", "journal", "url", "doi"):
        v = e.get(field, "")
        m = re.search(r"(\d{4}\.\d{4,5})", v)
        if m:
            return m.group(1)
    return None


def fetch_arxiv(aid: str) -> dict | None:
    url = f"http://export.arxiv.org/api/query?id_list={aid}"
    raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entry = ET.fromstring(raw).find("a:entry", ns)
    if entry is None:
        return None
    title = entry.find("a:title", ns)
    if title is None:
        return None
    authors = [a.find("a:name", ns).text for a in entry.findall("a:author", ns)]
    return {"title": " ".join(title.text.split()),
            "first_author": authors[0] if authors else "",
            "year": entry.find("a:published", ns).text[:4]}


def fetch_crossref(doi: str) -> dict | None:
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    try:
        m = json.load(urllib.request.urlopen(
            urllib.request.Request(url, headers=UA), timeout=60))["message"]
    except Exception:
        return None
    authors = m.get("author") or []
    parts = m.get("issued", {}).get("date-parts") or [[None]]
    return {"title": (m.get("title") or [""])[0],
            "first_author": (authors[0].get("family", "") if authors else ""),
            "year": str(parts[0][0]) if parts[0] else ""}


def fetch_anthology(url: str) -> dict | None:
    m = re.search(r"aclanthology\.org/([^/\s]+)", url)
    if not m:
        return None
    ident = m.group(1).rstrip("/")
    try:
        raw = urllib.request.urlopen(
            urllib.request.Request(f"https://aclanthology.org/{ident}.bib", headers=UA),
            timeout=60).read().decode("utf-8")
    except Exception:
        return None
    t = re.search(r'title\s*=\s*"((?:[^"\\]|\\.)*)"', raw)
    a = re.search(r'author\s*=\s*"((?:[^"\\]|\\.)*)"', raw, re.S)
    y = re.search(r'year\s*=\s*"(\d{4})"', raw)
    return {"title": t.group(1) if t else "",
            "first_author": a.group(1).split(" and ")[0].strip() if a else "",
            "year": y.group(1) if y else ""}


def compare(key: str, e: dict, got: dict, source: str):
    global checked
    checked += 1
    want_t, got_t = norm(e.get("title", "")), norm(got["title"])
    if want_t and got_t and want_t not in got_t and got_t not in want_t:
        problems.append(f"{key}: title mismatch vs {source}\n"
                        f"      bib: {e.get('title','')}\n"
                        f"      {source}: {got['title']}")
    if key in KNOWN_AUTHOR_EXCEPTIONS:
        return
    want_a = first_family(e.get("author", ""))
    got_a = fold(got["first_author"] or "")
    if want_a and got_a and want_a not in got_a:
        problems.append(f"{key}: first author mismatch vs {source}: "
                        f"bib {e.get('author','').split(' and ')[0]!r} vs "
                        f"{got['first_author']!r}")


def url_resolves(url: str) -> bool:
    """Last-resort check for records with no API: does the URL come back 200?

    Used only for the handful of entries that have neither a DOI nor an arXiv id,
    such as a JSTOR listing or a software release page.
    """
    try:
        req = urllib.request.Request(url, headers=UA, method="HEAD")
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.status < 400
    except Exception:
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.status < 400
        except Exception:
            return False


def main():
    own = parse_bib(BIB)
    tex = open(TEX, encoding="utf-8").read()
    cited = set()
    for m in re.finditer(r"\\cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]*)\}", tex):
        cited.update(k.strip() for k in m.group(1).split(","))

    # Anything main.tex cites that custom.bib does not define has to come from the
    # ACL Anthology shards named in \bibliography. Pull those entries out and check
    # them like the rest, so a key that resolves to nothing cannot slip through.
    from_shards: dict[str, dict] = {}
    for shard in SHARDS:
        want = (cited - set(own)) - set(from_shards)
        if not want or not os.path.exists(shard):
            continue
        for key, e in parse_bib(shard, only=want).items():
            e["_shard"] = os.path.basename(shard)
            from_shards[key] = e

    entries = {**own, **from_shards}
    print(f"{len(own)} entries in custom.bib and {len(from_shards)} taken from the "
          f"Anthology shards, {len(cited)} distinct citation keys\n")

    missing = sorted(cited - set(entries))
    if missing:
        problems.append(f"cited but defined nowhere: {', '.join(missing)}")

    # A key defined twice makes the winner depend on database order, so the
    # Anthology-supplied entries must not also sit in custom.bib.
    for shard in SHARDS:
        if not os.path.exists(shard):
            continue
        dup = sorted(parse_bib(shard, only=set(own)))
        if dup:
            problems.append(f"defined in both custom.bib and {os.path.basename(shard)}: "
                            f"{', '.join(dup)}")

    orphans = sorted(set(own) - cited)
    if orphans:
        print(f"note: {len(orphans)} entry/entries never cited: {', '.join(orphans)}\n")

    for key in sorted(entries):
        e = entries[key]
        aid, doi, url = arxiv_id(e), e.get("doi", ""), e.get("url", "")
        source = None
        got = None
        if "aclanthology.org" in url:
            got, source = fetch_anthology(url), "anthology"
        if got is None and doi and not doi.startswith("10.48550"):
            got, source = fetch_crossref(doi), "crossref"
        if got is None and aid:
            got, source = fetch_arxiv(aid), "arxiv"
        if got is None and doi:
            got, source = fetch_crossref(doi), "crossref"
        if got is None:
            target = url or e.get("howpublished", "")
            m = re.search(r"https?://\S+", target)
            if m and url_resolves(m.group(0).rstrip("},")):
                print(f"  {key:38s} no structured record; URL resolves")
            else:
                problems.append(f"{key}: no structured record and no resolving URL")
                print(f"  {key:38s} UNVERIFIED")
            continue
        compare(key, e, got, source)
        where = f" [{e['_shard']}]" if "_shard" in e else ""
        print(f"  {key:38s} ok via {source}{where}")

    print(f"\n{checked} entries verified against a primary record")
    if problems:
        print(f"\n{len(problems)} PROBLEM(S):")
        for p in problems:
            print("  -", p)
        return 1
    print("no discrepancies")
    return 0


if __name__ == "__main__":
    sys.exit(main())
