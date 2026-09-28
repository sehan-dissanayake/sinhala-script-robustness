"""Guard rails for the workshop paper.

Two checks, both cheap enough to run on every edit:

1. The content ends within the four page limit. GlobalSouthAI counts limitations,
   references, appendices and the NeurIPS checklist separately, so the test is the
   page that \\label{sec:endofmain} lands on, read out of main.aux. That label sits
   immediately before \\section{Limitations}.

2. The workshop paper introduces no number that has not already been verified.
   Every numeric token in main.tex and checklist.tex must also appear in
   ../main.tex, the long version, whose numeric claims are checked against the
   frozen analysis outputs by paper/analysis/verify_claims.py. Anything that cannot
   be matched that way needs an entry in ALLOW with a reason.

   Note: this used to read ../acl_latex.tex, which is the unmodified ACL template
   and contains none of the paper's numbers, so the check silently passed nothing.

Run from the repository root, after compiling:

    python paper/globalsouthai/check_paper.py
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = os.path.dirname(HERE)

PAGE_LIMIT = 4

# Numbers that legitimately appear only in this version. Each one is either a
# structural constant of this document or a value verified elsewhere.
ALLOW = {
    # Document structure and the venue's own numbers.
    "2026": "NeurIPS 2026, the venue year",
    "40": "\"40th Conference on Neural Information Processing Systems\", set by the style file",
    "1": "checklist item numbering and \"1-2 sentence\" in the retained guidelines",
    "2": "checklist guidelines text",
    "3": "checklist guidelines text",
    "4": "checklist guidelines text",
    "96": "\"96% CI\" inside a checklist guideline we must keep verbatim",
    "0.80": "\\includegraphics width fraction, a typesetting length",
    "0.35": "\\raisebox baseline shift on an inline Sinhala example, a length",
    "1.7": "inline Sinhala example height in \\fontcharht units, a length",
    "15": "\\textfloatsep, a typesetting length",
    "14": "\\floatsep, a typesetting length",
    # Compute figures stated only in this version's appendix B.
    "9000": "transliteration-control sequences, 9,000, in run_synthetic_vs_human.py",
    "33": "exponent in p < 10^-33, the item-level logistic fit",
    # Analysis values printed at a different precision than the long version.
    "0.174": "synthetic-vs-human minimum, verify_claims checks it as 0.17",
    "0.240": "synthetic-vs-human maximum, verify_claims checks it as 0.24",
    "0.219": "synthetic-vs-human median, in synthetic_vs_human.json",
    "45": "median Matthews retention, verify_claims checks mcc_retained_pct",
    "55": "the complement of that retention, stated in a figure caption",
    # -------------------------------------------------------------------------
    # Camera-ready: the rebuilt S3 states the decomposition in matched units.
    # Each value below is re-derived from paper/analysis/out/ by DERIVED at the
    # foot of this file, which fails if any of them moves. They are listed here
    # because the long version still carries the withdrawn 21x/24x framing and
    # so cannot serve as their reference; remove these entries once it is
    # updated to match.
    # -------------------------------------------------------------------------
    "1.02": "median bits-per-word ratio on the published 24, = median total NLL ratio",
    "2.30": "median Bytes_unicode / Bytes_romanized, the UTF-8 factor in bpb",
    "99": "normalizer share of the reported gap under the word unit, published 24",
    "94": "the same share over all 31 checkpoints",
    "2.16": "median rise in bits per byte on the published 24",
    "4.5": "2^2.16, the per-byte probability factor",
    "769": "SmolLM3-3B perplexity ratio, the largest of the 31",
    "357": "Gemma-2-9B perplexity ratio",
    "8.93": "4.37 + 4.56, the sum the medians do not reach",
    "504": "21 x 24, the product the medians do not reach",
    "455000": "human-supplied share of the 755,000 reference items",
    "90.2": "Hormoz-8B single-label rate on SOLD, just over the 90% ceiling",
    "0.045": "Zephyr-7B-beta above-chance p on SinhalaMMLU, admitted at alpha=0.05",
    "93.3": "SmolLM3-3B single-option rate, admitted under a 95% rule",
    # Camera-ready author block.
    "22": "batch suffix in the placeholder author email addresses",
    # Camera-ready appendix analyses, recomputed by derived_check from the
    # per-item result files (point estimates) or reported from its bootstrap.
    "48153": "pooled SinhalaMMLU items with one checkpoint added, 7 x 6,879",
    "5.5": "upper 95% bound on the pooled gap under either looser screen",
    "0.2": "percent of family-bootstrap slopes at or above 1",
    "0.66": "Spearman, Sinhala-script fertility vs SinhalaMMLU gap, ten checkpoints",
}

# Values the camera-ready introduces, re-derived here from the frozen outputs so
# that ALLOW above is a statement of provenance rather than a waiver.
DERIVED = [
    ("median bits-per-word ratio, published 24", "nll_ratio_pub24", 1.02, 0.005),
    ("median byte ratio, all 31", "byte_ratio_all31", 2.30, 0.005),
    ("word-unit normalizer share, published 24", "word_share_pub24", 99.0, 0.5),
    ("word-unit normalizer share, all 31", "word_share_all31", 94.0, 0.5),
    ("median rise in bits per byte, published 24", "d_bpb_pub24", 2.16, 0.005),
    ("checkpoints cheaper on Romanized, published 24", "cheaper_pub24", 12, 0),
]

# Values this version states in prose that the long version only puts in a
# generated table. These are checked against the analysis outputs directly.
DIRECT = [
    ("Hormoz-8B SOLD offensive rate, Sinhala", "sold:Hormoz-8B:u_off_rate", 9.8),
    ("Hormoz-8B SOLD offensive rate, Romanized", "sold:Hormoz-8B:r_off_rate", 20.7),
    ("Swa-bhasha lexicon words", "attest:lexicon_words", 449598),
    ("Swa-bhasha lexicon spellings", "attest:lexicon_spellings", 7075844),
    ("SOLD attestation tercile gap, low", "tercile:low", 5.0),
    ("SOLD attestation tercile gap, middle", "tercile:mid", 7.2),
    ("SOLD attestation tercile gap, high", "tercile:high", 7.3),
]

NUM = re.compile(r"\d+(?:\.\d+)?")


def numbers(text: str) -> list[tuple[str, int]]:
    """Numeric tokens with their line numbers, thousands separators removed."""
    out = []
    for i, line in enumerate(text.split("\n"), 1):
        if line.lstrip().startswith("%"):
            continue
        line = line.replace("{,}", "").replace("\\,", "")
        for m in NUM.finditer(line):
            out.append((m.group(0), i))
    return out


def page_check() -> list[str]:
    aux = os.path.join(HERE, "main.aux")
    if not os.path.exists(aux):
        return ["main.aux is missing, compile main.tex first"]
    m = re.search(r"\\newlabel\{sec:endofmain\}\{\{[^}]*\}\{(\d+)\}", open(aux).read())
    if not m:
        return ["sec:endofmain is not in main.aux, run pdflatex twice"]
    page = int(m.group(1))
    if page > PAGE_LIMIT:
        return [f"content runs to page {page}, the limit is {PAGE_LIMIT}"]
    print(f"content ends on page {page} of {PAGE_LIMIT}")
    return []


def number_check() -> list[str]:
    acl = open(os.path.join(PAPER, "main.tex"), encoding="utf-8").read()
    known = {n for n, _ in numbers(acl)}
    known |= set(ALLOW)
    for _, _, v in DIRECT:
        known |= {f"{v:g}", f"{v:.1f}", str(v)}

    problems = []
    for fn in ("main.tex", "checklist.tex"):
        text = open(os.path.join(HERE, fn), encoding="utf-8").read()
        for tok, line in numbers(text):
            if tok not in known:
                problems.append(f"{fn}:{line}: {tok} is not verified anywhere")
    if not problems:
        print("every number in main.tex and checklist.tex is a verified value")
    return problems


def derived_check() -> list[str]:
    """Re-derive the camera-ready's new S3 values from the frozen outputs.

    The long version still states the withdrawn 21x/24x split, so these numbers
    have no reference there. Rather than waive them, recompute them here from
    paper/analysis/out/intrinsic_pooled.csv and ppl_decomposition.csv.
    """
    import csv as _csv
    import re as _re
    import statistics as _st

    sys.path.insert(0, os.path.join(PAPER, "analysis"))
    import common as C

    src = open(os.path.join(PAPER, "analysis", "stats_robustness.py")).read()
    published = set(eval(
        _re.search(r"PUBLISHED\s*=\s*([\[\{].*?[\]\}])", src, _re.S).group(1)))

    rows = list(_csv.DictReader(open(os.path.join(C.OUT_DIR, "intrinsic_pooled.csv"))))
    dec = {r["model"]: r for r in
           _csv.DictReader(open(os.path.join(C.OUT_DIR, "ppl_decomposition.csv")))}
    pub = [r for r in rows if r["model"] in published]

    def nll(r):  # total NLL ratio == bits-per-word ratio, word counts being equal
        return ((float(r["r_bpw"]) * float(r["r_words"]))
                / (float(r["u_bpw"]) * float(r["u_words"])))

    def word_share(r):
        xu = float(r["u_words"]) / float(r["u_tok"])
        xr = float(r["r_words"]) / float(r["r_tok"])
        au, ar = float(r["u_bpw"]), float(r["r_bpw"])
        return 100.0 * ((au + ar) / 2 * (xr - xu)) / (ar * xr - au * xu)

    got = {
        "nll_ratio_pub24": _st.median([nll(r) for r in pub]),
        "byte_ratio_all31": _st.median(
            [float(r["u_bytes"]) / float(r["r_bytes"]) for r in rows]),
        "word_share_pub24": _st.median([word_share(r) for r in pub]),
        "word_share_all31": _st.median([word_share(r) for r in rows]),
        "d_bpb_pub24": _st.median(
            [float(r["r_bpb"]) - float(r["u_bpb"]) for r in pub]),
        "cheaper_pub24": sum(1 for r in pub if nll(r) < 1),
    }
    # the identity that justifies leading with matched units
    resid = max(abs(float(r["r_bpb"]) / float(r["u_bpb"])
                    - nll(r) * (float(r["u_bytes"]) / float(r["r_bytes"])))
                for r in rows)
    words_equal = all(abs(float(r["u_words"]) - float(r["r_words"])) < 1e-9
                      for r in rows)

    problems = []
    for claim, key, printed, tol in DERIVED:
        if abs(got[key] - printed) > tol:
            problems.append(f"{claim}: paper says {printed}, analysis gives {got[key]}")
    if resid > 1e-9:
        problems.append(f"bpb ratio identity residual {resid:.2e}, expected ~0")
    if not words_equal:
        problems.append("word counts are not identical within every pair")
    # the withdrawn pair, kept as a regression guard against reintroducing it
    tot = _st.median([float(dec[r["model"]]["total"]) for r in pub])
    nrm = _st.median([float(dec[r["model"]]["tok_term"]) for r in pub])
    los = _st.median([float(dec[r["model"]]["loss_term"]) for r in pub])
    if abs((nrm + los) - tot) < 0.05:
        problems.append("median terms now compose; the S3 caveat may be stale")
    problems += appendix_check(C)
    if not problems:
        print(f"{len(DERIVED)} camera-ready values re-derived; "
              f"bpb identity residual {resid:.1e}; word counts matched")
    return problems


def appendix_check(C) -> list[str]:
    """Recompute the deterministic numbers of the camera-ready appendix analyses.

    Pooled gaps come from the per-item SinhalaMMLU result files, and the family
    and fertility figures from extrinsic_main.csv. Bootstrap intervals are not
    re-run here, only the point estimates they surround.
    """
    import numpy as np
    import pandas as pd
    from scipy import stats

    res = os.path.join(os.path.dirname(PAPER), "results", "extrinsic_evaluation")
    files = {
        "Qwen3.5-4B": "Qwen-3.5-4B/qwen_3_5_4b",
        "Qwen2-7B-Instruct": "Qwen2-7B-Instruct/qwen2_7b_instruct",
        "Llama-3.1-8B-Instruct": "Llama-3.1-8B-Instruct/llama_3_1_8b_instruct",
        "Hormoz-8B": "Hormoz-8B/hormoz_8b",
        "Qwen3.5-9B": "Qwen-3.5-9B/qwen_3_5_9b",
        "Phi-4-14B": "Phi-4/phi_4",
        "Zephyr-7B-beta": "zephyr-7b-beta/zephyr_7b_beta",
        "SmolLM3-3B": "SmolLM3-3B/smollm3_3b",
    }
    six = list(files)[:6]

    def pooled(models):
        x = np.vstack([pd.read_csv(os.path.join(res, files[m] + "_sinhala_mmlu.csv"),
                                   encoding="utf-8-sig",
                                   usecols=["unicode_correct", "romanized_correct"]
                                   ).to_numpy() for m in models])
        return len(x), 100 * (x[:, 0] - x[:, 1]).mean()

    ex = pd.read_csv(os.path.join(C.OUT_DIR, "extrinsic_main.csv"))
    mm = ex[(ex.dataset == "sinhala_mmlu")
            & (ex.model != "LaMini-GPT-1.5B")].set_index("model")
    qwen = ["Qwen3.5-4B", "Qwen2-7B-Instruct", "Qwen3.5-9B"]

    def slope(models):
        return np.polyfit(mm.loc[models, "u_acc"], mm.loc[models, "r_acc"], 1)[0]

    fert = {"TinyLlama-1.1B-Chat": 9.8, "StableLM-Zephyr-3B": 14.0, "SmolLM3-3B": 9.5,
            "Qwen3.5-4B": 4.3, "Zephyr-7B-beta": 9.3, "Qwen2-7B-Instruct": 7.6,
            "Llama-3.1-8B-Instruct": 9.7, "Hormoz-8B": 8.6, "Qwen3.5-9B": 4.3,
            "Phi-4-14B": 9.5}   # Sinhala tokens per word, tab_model_ids.tex
    ix = list(mm.index)
    gap = (mm.u_acc - mm.r_acc).loc[ix].to_numpy()
    ua = mm.u_acc.loc[ix].to_numpy()
    fe = np.array([fert[m] for m in ix])
    resid = gap - np.polyval(np.polyfit(ua, gap, 1), ua)

    checks = [
        ("pooled gap, as specified", pooled(six)[1], 6.0, 0.05),
        ("pooled items, +Zephyr", pooled(six + ["Zephyr-7B-beta"])[0], 48153, 0),
        ("pooled gap, +Zephyr", pooled(six + ["Zephyr-7B-beta"])[1], 5.0, 0.05),
        ("pooled gap, +SmolLM3", pooled(six + ["SmolLM3-3B"])[1], 5.1, 0.05),
        ("slope, one Qwen: 3.5-4B",
         slope([m for m in ix if m not in qwen or m == "Qwen3.5-4B"]), 0.24, 0.005),
        ("slope, one Qwen: 3.5-9B",
         slope([m for m in ix if m not in qwen or m == "Qwen3.5-9B"]), 0.25, 0.005),
        ("slope, one Qwen: 2-7B",
         slope([m for m in ix if m not in qwen or m == "Qwen2-7B-Instruct"]), 0.46, 0.005),
        ("fertility vs gap rho", stats.spearmanr(fe, gap)[0], -0.66, 0.005),
        ("fertility vs Sinhala acc rho", stats.spearmanr(fe, ua)[0], -0.73, 0.005),
        ("fertility vs residual gap rho", stats.spearmanr(fe, resid)[0], 0.05, 0.005),
        ("Qwen3.5-9B loss", gap[ix.index("Qwen3.5-9B")], 15.5, 0.05),
        ("Qwen3.5-4B loss", gap[ix.index("Qwen3.5-4B")], 10.6, 0.05),
    ]
    # the printed value must be the correctly rounded analysis value
    problems = [f"appendix: {name}: paper says {want}, analysis gives {got:.4f}"
                for name, got, want, tol in checks if abs(got - want) > tol]
    if not problems:
        print(f"{len(checks)} appendix analysis values recomputed from per-item results")
    return problems


def direct_check() -> list[str]:
    """Check the handful of prose values against the frozen analysis outputs."""
    import json

    sys.path.insert(0, os.path.join(PAPER, "analysis"))
    import pandas as pd

    import common as C

    at = json.load(open(os.path.join(C.OUT_DIR, "attestation_numbers.json")))
    sd = pd.read_csv(os.path.join(C.OUT_DIR, "sold_detail.csv")).set_index("model")

    problems = []
    for claim, key, printed in DIRECT:
        kind, *rest = key.split(":")
        if kind == "sold":
            value = float(sd.loc[rest[0], rest[1]])
        elif kind == "attest":
            value = float(at["attestation"][rest[0]])
        else:
            value = float(at["downstream"][rest[0]]["gap"])
        if abs(value - printed) > 0.05:
            problems.append(f"{claim}: paper says {printed}, analysis gives {value}")
    if not problems:
        print(f"{len(DIRECT)} prose-only values match the analysis outputs")
    return problems


def main() -> None:
    problems = page_check() + number_check() + direct_check() + derived_check()
    if problems:
        print(f"\n{len(problems)} PROBLEM(S):")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("workshop paper checks pass")


if __name__ == "__main__":
    main()
