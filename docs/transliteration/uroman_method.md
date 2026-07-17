# Method 4: uroman (External Universal Romanizer)

**Implementation:** `src/transliteration/uroman_method.py`
**Output directory:** `data/romanized/uroman/`
**External dependency:** `uroman==1.3.1.1` (pinned in `requirements.txt`)
**Type:** Rule-based, deterministic, third-party, language-agnostic-by-design
**Direction:** Sinhala (Unicode) → Romanized Sinhala (ASCII/Latin)
**Source publication:** Ulf Hermjakob, Jonathan May, and Kevin Knight. 2018. *Out-of-the-box Universal Romanization Tool uroman*. In Proceedings of the 56th Annual Meeting of the Association for Computational Linguistics (ACL 2018), System Demonstrations, pages 62–67, Melbourne, Australia. https://aclanthology.org/P18-4011/

## 1. Purpose and role in the study

uroman is a widely used, general-purpose romanizer built by USC/ISI, notable for converting **any** Unicode script to Latin using heuristics rather than a per-language dictionary. It has been adopted in downstream multilingual NLP work (e.g., romanization-based massively multilingual model adaptation; Muller et al., 2023, arXiv:2304.08865). Its inclusion here provides:

1. A **second fully independent external baseline** (distinct from Aksharamukha's Indic-specific engine and this project's own rule-based methods), built on a different design philosophy (universal heuristics vs. script-specific tables).
2. Evidence for how a "naive," non-Sinhala-specialized tool — of the kind a resource-constrained team might genuinely reach for in practice — performs relative to purpose-built methods, which is directly relevant to the paper's premise that real-world Romanized Sinhala is often produced without any specialized tool at all.

## 2. How it is invoked

```python
from uroman import Uroman
_ROMANIZER = Uroman()
romanized = _ROMANIZER.romanize_string(token, lcode="sin")
```

- `lcode="sin"`: the ISO 639-3 language code for Sinhala, passed on every call so uroman can apply Sinhala-specific heuristics where it has them (the library's language-code list historically focuses on improving disambiguation for scripts shared across languages, such as Cyrillic or Arabic; Sinhala uses its own unique script block, so the practical effect of the language code for Sinhala specifically was not separately ablated in this project).
- As with the other three methods, only Sinhala-block spans (plus joiners) are routed through the romanizer; non-Sinhala text (English, mentions, punctuation, digits) is passed through unchanged by this project's tokenizer, not by uroman itself.
- Results are cached per-token (`functools.lru_cache`, 65,536 entries) since uroman's per-call overhead is non-trivial (see §5).

## 3. Post-processing implemented in this project

uroman's raw output for Sinhala is already close to plain ASCII, but two corpus-driven fixes were added after full-corpus validation surfaced two gaps:

1. **Visarga (ඃ) is left untouched by uroman itself.** This project applies a direct substitution `ඃ → h` (the standard phonetic value of visarga, matching the treatment in Methods 1, 2, and 3) before any further processing.
2. **Residual-Sinhala fallback.** After the visarga fix, if any Sinhala Unicode character still remains in uroman's output for a given token (found empirically on one malformed source string containing a rare, likely data-entry-error, detached vowel sign `ෳ` in `sold_0637`), that specific token is re-processed through this project's Method 1 deterministic phonetic parser (`phonetic.transliterate`) as a fallback, guaranteeing the shared zero-Sinhala-leakage invariant holds for every output file regardless of upstream tool coverage gaps. This fallback triggered on **1 token** across the full 2,500-record SOLD file and **0** tokens in the 1,851-record MMLU file in the 2026-07 generation run — i.e., it is a rare safety net, not a routine part of the pipeline's behavior.

Both fixes are applied inside `_romanize_token`, before the result is cached.

## 4. Design philosophy vs. the other three methods (important for the paper's comparison)

uroman does **not** use an explicit, hand-authored Sinhala consonant/vowel-sign table of the kind in Methods 1 and 3, nor a formal transliteration-scheme table of the kind Aksharamukha uses for "ISO". It is built on general Unicode-property-driven heuristics designed to work "out of the box" for scripts the tool's authors may never have specifically studied. This is precisely uroman's stated contribution (Hermjakob et al., 2018): romanization without per-language engineering.

Practically, on Sinhala specifically, this shows up as:
- **`ව → v`** rather than the Singlish-conventional `w` (contrast Methods 1, 2, 3, which all use `w`).
- **`ශ/ෂ/ස → s`** rather than distinguishing `sh` for palatal/retroflex sibilants (contrast the other three methods, which all use `sh` for ශ/ෂ).
- **No aspirate digraphs**: aspirated consonants (ඛ, ඝ, ඡ, ඣ, ඨ, ඪ, ථ, ධ, ඵ, භ) are romanized to their unaspirated base letter (e.g., ථ → `t`, not `th`), differing from Methods 1 and 2, which both preserve the aspirate digraph.
- **No inherent-vowel/schwa modeling** (as expected — that is uniquely Method 3's contribution): bare consonants get the same treatment as the other ASCII methods, i.e. `a`.

These are not implementation choices made by this project; they are uroman's own script-general heuristics for Sinhala, and should be described in the paper as uroman's native output characteristics.

## 5. Worked examples (generated by the current implementation)

| Sinhala input | uroman output | Aksharamukha (Method 2) for comparison |
|---|---|---|
| `සිංහල` | `sinhala` | `sinhala` |
| `වෙසක්` | `vesak` | `wesak` |
| `ප්‍රතිපත්ති` | `pratipatti` | `pratipatti` |
| `කොහොමද?` | `kohomada?` | `kohomada?` |
| `ශ්‍රී ලංකාව` | `srii lankaava` | `shrii lankaawa` |
| `බුදුන් වහන්සේ` | `budun vahansee` | `budun wahansee` |
| `@USER තුනක් ඕනේ නෑ...` | `@USER tunak oonee nae...` | `@USER tunak oonee naae...` |

Full sentence: `වෙසක් උත්සවයේදී බෞද්ධයින් අනුගමනය කරන පූජා විධි දෙක නම්,`
→ uroman: `vesak utsavayeedii bauddayin anugamanaya karana puujaa vidi deka nam,`
→ contrast Method 2 (Aksharamukha): `wesak utsawayeedii bauddhayin anugamanaya karana puujaa widhi deka nam,`

The systematic `v`-vs-`w` and unaspirated-vs-aspirated differences are visible throughout: `vesak`/`wesak`, `vidi`/`widhi`, `bauddayin`/`bauddhayin`. This is a useful, concrete illustration for the paper of how two independently engineered, non-Sinhala-specific-vs-Sinhala-aware transliteration approaches diverge even when both are fully deterministic and rule-based.

## 6. Guarantees and validation

Same shared writer and Sinhala-leakage validator as the other three methods. Measured on this repository's data (2026-07 run): **1,851** SinhalaMMLU + **2,500** SOLD records, **0** Sinhala leakage in final output (after the visarga fix and the one-token residual-fallback trigger described in §3).

Throughput: ≈1,000 strings/second (measured over 11,755 MMLU+SOLD strings) — roughly 3× faster than Aksharamukha but roughly 25× slower than the in-house phonetic baseline, consistent with uroman performing general Unicode-property analysis per character rather than a fixed-table lookup.

## 7. Known limitations (for Discussion/Limitations)

- **Not Sinhala-specialized.** By design, uroman does not encode Sinhala-specific orthographic or phonological knowledge; the `v`/`w` and aspirate-collapsing behaviors documented in §4 are consequences of this, not bugs, but they do mean uroman's output is furthest from natural Sri Lankan Singlish spelling conventions among the four implemented methods.
- **Coverage gaps on malformed input required a project-side fallback** (§3): two source-corpus data-entry irregularities (a rare detached vowel sign, and visarga) were not romanized by uroman itself. The fallback guarantees no Sinhala leakage in this project's output, but means a small fraction of uroman's own "native" output was actually overridden by this project's Method 1 parser — this should be disclosed as a implementation detail if uroman's outputs are analyzed character-by-character.
- **Slower than the in-house baseline**, relevant if runtime is discussed.
- **`lcode="sin"` effect not independently ablated** — this project did not compare against calling uroman without a language code, so it cannot be stated with certainty how much (if any) Sinhala-specific behavior the language code activates internally, versus uroman's script-general Brahmic-abugida handling doing most of the work regardless of the code.

## 8. Citation for the paper

> Ulf Hermjakob, Jonathan May, and Kevin Knight. 2018. Out-of-the-box Universal Romanization Tool uroman. In *Proceedings of ACL 2018, System Demonstrations*, pages 62–67, Melbourne, Australia. Association for Computational Linguistics. https://aclanthology.org/P18-4011/

Cite the paper for the tool's design and the GitHub repository (`isi-nlp/uroman`, PyPI package `uroman`, version 1.3.1.1) for the exact software version used. Note in the Methods section that this project applies a project-specific visarga fix and a residual-Sinhala fallback to the deterministic phonetic method (Method 1) — uroman's own unmodified output is described in §4–5 above for transparency, but the files in `data/romanized/uroman/` reflect the fixed/fallback-applied version.
