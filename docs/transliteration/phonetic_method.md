# Method 1: Deterministic Orthographic Phonetic Baseline

**Implementation:** `src/transliteration/phonetic.py`
**Output directory:** `data/romanized/phonetic/`
**Type:** Rule-based, deterministic, data-free (no external corpus, model, or dictionary)
**Direction:** Sinhala (Unicode) → Romanized Sinhala (ASCII Latin)

## 1. Purpose and role in the study

This is the project's custom, fully reproducible control condition. It requires no external library, no training data, and no network access, so its behavior is completely determined by the code in this repository. It is the natural baseline against which the three other, more sophisticated methods (Aksharamukha, Sinhala G2P with schwa rules, uroman) should be compared in the paper.

It is explicitly an **orthographic transliteration**, not a pronunciation model: it converts each written Sinhala grapheme to a fixed Latin spelling using familiar Singlish conventions (e.g. digraphs `th`, `sh`, `kh`). It does not attempt to resolve the schwa/`a` ambiguity that native pronunciation requires — every consonant with no explicit vowel sign is spelled with `a`. This is the key methodological distinction from Method 3 (Sinhala G2P).

## 2. Algorithm

Sinhala is a Brahmic abugida: a consonant letter carries an inherent vowel (commonly transcribed `/a/` or `/ə/`) unless followed by a dependent vowel sign (pilla) or the virama/hal kirima (`්`), which cancels the inherent vowel. The algorithm processes text left to right, one Unicode code point at a time:

1. Normalize the input string to Unicode NFC.
2. For each character:
   - **Zero-width joiner/non-joiner** (`\u200d`, `\u200c`): skipped (consumed silently, used for conjunct rendering such as `ර්‍ය` yansaya/rakaransaya clusters).
   - **Independent vowel** (`අ, ආ, ඇ, ...`): mapped directly via a lookup table.
   - **Consonant**: emit its base Latin consonant, then look ahead (skipping any joiner) —
     - if a **dependent vowel sign** follows, emit its vowel and advance past it;
     - else if **virama** (`්`) follows, emit nothing extra (inherent vowel suppressed) and advance past it;
     - else emit the **inherent vowel `a`** and advance one character.
   - **Special sign** (anusvara `ං`, visarga `ඃ`): mapped directly (`n`, `h`).
   - **Standalone dependent vowel sign** (malformed/detached in source text): mapped directly using the same vowel table, as a defensive recovery rather than raising an error.
   - **Standalone virama** (malformed): consumed silently.
   - **Any other Sinhala-block code point not in the tables above:** raises `ValueError` with the character's code point, index, and an 8-character context window. The method never silently drops or leaks an unrecognized Sinhala character.
   - **Non-Sinhala character** (Latin text, digits, punctuation, emoji, mentions such as `@USER`, URLs): copied through unchanged.

This "recover known malformed signs, reject unknown ones" behavior was empirically necessary: one MMLU item (`mmlu_0875`, containing `දිසිීකික්කය`, a duplicated vowel sign from a data-entry error) and one SOLD item required the recovery path rather than a hard failure, while the shared output validator (below) still guarantees zero Sinhala leakage in the final files.

## 3. Complete mapping tables (as implemented)

### Independent vowels
| Sinhala | Latin | Sinhala | Latin | Sinhala | Latin |
|---|---|---|---|---|---|
| අ | a | ඉ | i | උ | u |
| ආ | aa | ඊ | ii | ඌ | uu |
| ඇ | ae | ඍ | ru | ඎ | ruu |
| ඈ | aae | ඏ | lu | ඐ | luu |
| එ | e | ඒ | ee | ඓ | ai |
| ඔ | o | ඕ | oo | ඖ | au |

### Consonants (base, inherent vowel not included)
| Sinhala | Latin | Sinhala | Latin | Sinhala | Latin | Sinhala | Latin |
|---|---|---|---|---|---|---|---|
| ක | k | ට | t | ත | th | ප | p |
| ඛ | kh | ඨ | th | ථ | th | ඵ | ph |
| ග | g | ඩ | d | ද | d | බ | b |
| ඝ | gh | ඪ | dh | ධ | dh | භ | bh |
| ඞ | ng | ණ | n | න | n | ම | m |
| ඟ | ng | ඬ | nd | ඳ | nd | ඹ | mb |
| ච | ch | | | | | ය | y |
| ඡ | chh | | | | | ර | r |
| ජ | j | | | | | ල | l |
| ඣ | jh | | | | | ව | w |
| ඤ | ny | | | | | ශ | sh |
| ඥ | gn | | | | | ෂ | sh |
| ඦ | ndj | | | | | ස | s |
| | | | | | | හ | h |
| | | | | | | ළ | l |
| | | | | | | ෆ | f |

### Dependent vowel signs (pilla)
| Sinhala | Latin | Sinhala | Latin | Sinhala | Latin |
|---|---|---|---|---|---|
| ා | aa | ි | i | ු | u |
| ැ | ae | ී | ii | ූ | uu |
| ෑ | aae | ෘ | ru | ෲ | ruu |
| ෙ | e | ේ | ee | ෛ | ai |
| ො | o | ෝ | oo | ෞ | au |
| ෟ | ow | ෳ | luu | ් | *(nothing — cancels inherent vowel)* |

### Special signs
| Sinhala | Latin | Meaning |
|---|---|---|
| ං | n | Anusvaraya (nasalization) |
| ඃ | h | Visargaya |

Note that `ට/ත`, `ඩ/ද`, `ණ/න`, `ල/ළ`, `ශ/ෂ` are merged to the same Latin spelling (`t`, `d`, `n`, `l`, `sh`), consistent with standard casual Singlish orthography, which does not distinguish retroflex/dental or palatal/retroflex pairs. This is a deliberate simplification worth noting as a limitation in the paper: it is a many-to-one mapping and therefore not reversible.

## 4. Worked examples (generated by the current implementation)

| Sinhala input | Output | Notes |
|---|---|---|
| `වෙසක් උත්සවයේදී බෞද්ධයින් අනුගමනය කරන පූජා විධි දෙක නම්,` | `wesak uthsawayeedii bauddhayin anugamanaya karana puujaa widhi deka nam,` | Full sentence from MMLU |
| `සිංහල` | `sinhala` | Anusvara → `n` |
| `ප්‍රතිපත්ති` | `prathipaththi` | ZWJ-joined conjunct (rakaransaya) handled |
| `කොහොමද?` | `kohomada?` | Punctuation preserved |
| `තේ නෙවෙයි තෝ බීලා ඉන්නෙ ගිනි වතුර` | `thee neweyi thoo biilaa inne gini wathura` | SOLD-style informal register |
| `@USER තුනක් ...` | `@USER thunak ...` | Mentions preserved verbatim |
| `බුදුන් වහන්සේ` | `budun wahansee` | |
| `ශ්‍රී ලංකාව` | `shrii lankaawa` | |

## 5. Guarantees and validation

The shared writer (`_dataset_io.py`) used by all four methods enforces, for every generated record:
- `text_romanized` and, where present, every element of `options_romanized` contain **zero** Unicode Sinhala block characters (U+0D80–U+0DFF). Any leakage raises `ValueError` and aborts the write (via an atomic temp-file swap, so partially written files never appear).
- Record `id`, `label`, `domain`, `difficulty`, and option **count/order** are preserved unchanged from the source.
- Output files are UTF-8, one JSON object per line, `ensure_ascii=False`.

Measured on this repository's data (2026-07 run): **1,851** SinhalaMMLU records and **2,500** SOLD records processed, 0 Sinhala leakage, 0 unhandled malformed-character errors after the recovery path was added.

Throughput: ≈25,000 short strings/second on the test machine (single-threaded, pure Python, no I/O bottleneck) — by far the fastest of the four methods, because it performs no external process calls or model lookups.

## 6. Known limitations (for the Discussion/Limitations section)

- **No pronunciation modeling.** Every bare consonant gets `a`; Sinhala speech very often realizes this as a reduced `/ə/` instead (see Method 3 for the alternative that models this).
- **Lossy consonant mapping.** Retroflex/dental and palatal/retroflex consonant pairs collapse to one Latin letter each, matching common Singlish practice but discarding information that IS present in the source script.
- **No compound-word or loanword handling.** Purely code-point local; does not use any lexicon.
- **Not reversible.** Because of the above two points, the mapping Sinhala→Latin is not injective, so Latin→Sinhala reconstruction is not generally possible from this output alone.
- **No comparison to a human-produced gold standard is built in** — chrF/CER against native-speaker references must be computed separately (see the pilot-selection guidance the project used before freezing a method).

## 7. Citable characterization for the paper

This can be described in a Methods section as: *"a deterministic, rule-based grapheme-level transliterator implemented specifically for this study, following the general akshara-parsing structure common to Sinhala NLP tools (segmentation into independent vowels, consonants, dependent vowel signs, and the virama/hal-kirima), using ASCII digraph conventions standard in casual Sinhala Romanization (Singlish)."* It should be cited as an in-house baseline, not attributed to any external publication.
