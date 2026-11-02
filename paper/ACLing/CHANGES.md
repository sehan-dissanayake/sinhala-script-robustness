# ACLing 2026 version: changes against the ALTA 2026 reviews

Build: `pdflatex main.tex` (run twice). Upload the whole `paper/ACLing/` folder to
Overleaf and set the compiler to pdfLaTeX. The paper is 8 pages including references,
in the unmodified ACLing 2026 / Procedia Computer Science template.

Every number in the text comes from `paper/analysis/out/` or from
`scripts/numbers.json`, which `scripts/make_numbers_and_figures.py` writes. The same
script draws both figures. `scripts/order_bibliography.py` puts the references in
order of first citation (Vancouver numbering, as the template asks) from
`scripts/bibitems.tex`. Each reference was checked against arXiv, Crossref or the
ACL Anthology.

## Reviewer V5VG

| Comment | What changed |
|---|---|
| The factors 21 and 24 do not multiply to 312 | Medians of the parts do not add up to the median of the total. Table 1 now reports **means** of log2 ratios, which add up exactly. |
| The byte-based split cannot separate tokenizer effects from real loss | Re-ran the split in bytes, code points and words. The byte split was an artifact of the byte count changing between scripts (Sinhala 43,152 bytes against Romanized 18,731). The word count is the same in both (3,035). Per word, the token count explains 99 to 102% of the mean ratio and the content term is close to zero. The old claim of "a factor of 24 real loss" is removed. The paper now says that the content term still depends on each tokenizer. |
| A higher intrinsic loss on our transliteration does not bound downstream performance on human text | Removed the "upper bound" claim. The paper now says only that our text is harder to predict (3.2 to 3.7 bits per word more than human typing), that the downstream effect on human-typed items is unknown, and that the downstream gaps apply to transliterated input. |
| Restrict conclusions to the tested conditions | Removed the extrapolation to proprietary models and "scale is not the fix". The conclusion says "under the conditions we tested". |
| Trim appendix, shorten Section 5.6, fix typos | No appendix (the 8-page limit includes everything). Section 5.6 is now one short paragraph ("Intrinsic predictors"). The typos are gone with the rewrite. |

## Reviewer mVMx

| Comment | What changed |
|---|---|
| Would bits per code point be better than bits per byte? | Section 4.1 explains this. Within one script, bytes, code points and words rank models the same way. Across scripts, only words have the same count, so cross-script comparisons use bits per word. Table 1 shows the code-point split. |
| Make clear what analysis Section 3.1 does | Section 3 starts with the design rule (only the script changes, every comparison is within one model and over the same content). Section 5 opens by stating the paired comparison. |
| What are the four romanization methods? | They are named: ours, Aksharamukha, uroman, and the Global PIQA web romanizer, with error rates. |
| "Twelve of the 31 checkpoints are cheaper": cheaper how, and what is predictable? | Now "12 of the 31 models assign fewer bits per word to the Romanized version". The "predictable" sentence now says that the models best on the Sinhala script have the largest per-word gap. |
| "The standard published metric falsely makes..." is unclear | Rewritten in the SinLlama section, with the numbers for both views. |
| Why the add-1 character n-grams? | Removed. |
| "headroom ... cannot be tested as it stands" is unclear | Removed. The paper fits Romanized against Sinhala-script accuracy and gives one sentence on why it does not fit the drop. |
| "leave one out range" is unclear | Now "refitting with one model left out at a time gives slopes between 0.17 and 0.26, so no single model drives the result". |
| "difficulty cells": what and why? | Now "the 16 non-empty domain and difficulty groups", used because ten models is a small sample. |
| "A deployment monitored on accuracy alone..." is unclear | Rewritten as a plain statement about accuracy against MCC. |
| "terciles by token inflation": why? | Explained: if token count drove the loss, the loss would change steadily across the groups, and it does not. |
| "Thin pretraining coverage" is unclear | Removed. The Limitations section says we cannot check exposure because training data are not public. |
| "output degeneration" is opaque | Now "Answer collapse": a model could reach chance by always giving the same answer, and we show this does not happen. |
| "A cheap intrinsic measurement partly substitutes..." is unclear | Rewritten as "Intrinsic predictors", one plain paragraph. |
| Writing reads as AI-smoothed | Full rewrite in plain English. No em dashes, no semicolons in the body text, short sentences, and no dramatic claims. |

## Other changes

- Global PIQA is removed. The downstream set is now SinhalaMMLU and SOLD, with 9,379 items.
- The mixed-script condition is removed, because that corpus is not parallel.
- New figures: perplexity against tokenizer fertility, per-word cost in both scripts with the SinLlama arrow, SinhalaMMLU accuracy in both scripts, and SOLD MCC.
- The paper is anonymized for double-blind review. The only link is the anonymous.4open.science repository.
