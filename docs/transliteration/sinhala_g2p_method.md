# Method 3: Rule-Based Sinhala G2P with Schwa Epenthesis

**Implementation:** `src/transliteration/sinhala_g2p.py`
**Output directory:** `data/romanized/sinhala_g2p_schwa/`
**Type:** Rule-based, deterministic, implements a published academic algorithm
**Direction:** Sinhala (Unicode) → Latin phonemic transcription (retains `ə`, not ASCII-only)
**Source publication:** Asanka Wasala, Ruvan Weerasinghe, and Kumudu Gamage. 2006. *Sinhala Grapheme-to-Phoneme Conversion and Rules for Schwa Epenthesis*. In Proceedings of the COLING/ACL 2006 Main Conference Poster Sessions, pages 890–897, Sydney, Australia. Association for Computational Linguistics. https://aclanthology.org/P06-2114/

## 1. Purpose and role in the study

This is the only implemented method that models Sinhala **pronunciation** rather than pure **orthography**. Written Sinhala does not mark whether a bare consonant is pronounced with a full `/a/` or a reduced schwa `/ə/`; native readers resolve this from context and phonological rules. Wasala et al. (2006) formulated an explicit, ordered set of rules for this resolution, evaluated at 98% accuracy against 30,000 expert-transcribed words from the UCSC Sinhala Corpus.

This method is included so the paper can distinguish two hypotheses about LLM degradation on Romanized Sinhala:
1. Degradation caused by **script change alone** (addressed by Methods 1, 2, 4 — orthographic transliteration).
2. Degradation caused by **loss of the schwa/`a` phonemic distinction** specifically (addressed by comparing this method against the others).

**Important framing note for the paper:** because this method retains the phoneme `ə` (schwa) as a distinct character rather than collapsing it to ASCII `a`, its output is not ordinary ASCII Singlish that a Sri Lankan would type on a keyboard. It should be presented as a **linguistically motivated phonemic transcription condition**, separate from the "naturalistic Singlish" methods. If a pure-ASCII variant is needed for an LLM prompt-compatibility reason, `ə` can be mapped to `a` as a final step, but doing so exactly reproduces Method 1's schwa handling and would defeat the purpose of including this method — this tradeoff should be stated explicitly if that substitution is made.

## 2. Algorithm overview

The implementation follows the paper's two-stage architecture:

**Stage A — Grapheme-to-phoneme mapping** (`_map_word`): each Sinhala word is scanned left to right and converted to a list of phoneme units using the paper's Table 4 mapping (reproduced in §3 below). Every consonant with no explicit vowel sign and no virama receives a schwa `ə` by default (not `a` — this is the paper's key design decision: schwa is the *default*, subsequently corrected to `/a/` where the rules require it). The Zero-Width Joiner and the hal-kirima/virama (`්`) do not themselves produce output units, matching the paper's Figure 1 example exactly.

**Stage B — Schwa epenthesis rules** (`_rule_1` through `_rule_8`): applied in the fixed order specified in the paper, each rule scanning the phoneme list and converting specific `ə → a` (or, for rule 8, `a → ə`) contexts.

**Stage C — Diphthong mapping**: the resulting phoneme sequence is scanned for five vowel+`w`+`u` and five vowel+`y`+`i` sequences (paper's Table 5) and each matching triple is collapsed to a single diphthong unit.

## 3. G2P mapping table (paper's Table 4, as implemented)

| Sinhala | Phoneme | Sinhala | Phoneme | Sinhala | Phoneme |
|---|---|---|---|---|---|
| අ | a | ඔ, ො | o | ඬ | nd |
| ආ, ා | aa | ඕ, ෝ | oo | ෆ | f |
| ඇ, ැ | ae | ඖ, ෞ | au | ත, ථ | t |
| ඈ, ෑ | aae | ක, ඛ | k | ද, ධ | d |
| ඉ, ි | i | ග, ඝ | g | ඳ | nd |
| ඊ, ී | ii | ඞ, ං | ng | ප, ඵ | p |
| උ, ු | u | ඟ | ng | බ, භ | b |
| ඌ, ූ | uu | ච, ඡ | ch | ම | m |
| ඍ (word-initial) | ri | ජ, ඣ | j | ඹ | mb |
| ෘ (elsewhere) | ru | ඤ | ny | ය | y |
| ඏ | lu | ඥ | jny | ර | r |
| ඐ | luu | ඦ | nj | ල, ළ | l |
| එ, ෙ | e | ට, ඨ | ṭ | ව | w |
| ඒ, ේ | ee | ඩ, ඪ | ḍ | ශ, ෂ | sh |
| ඓ, ෛ | ai | ණ | n | ස | s |
| | | න | n | හ, ඃ | h |

Notes on the implementation vs. the paper's phonetic symbols:
- The paper's IPA-style symbols (`/˝/`, `/ʈ/`, `/Ɖ/`, etc.) are rendered here in readable Latin form; **retroflex stops ට/ඨ and ඩ/ඪ are kept distinct from dental ත/ථ and ද/ධ** using `ṭ`/`ḍ` internally (unlike Methods 1 and 2, which collapse this distinction) — this preserves one more phonemic contrast than the ASCII methods, then `ṭ→t` and `ḍ→d` are applied only as the very last formatting step for readability, after all rules have run. If the retroflex/dental distinction is relevant to the paper's analysis, the pre-formatting `ṭ`/`ḍ` forms can be exposed by removing that final substitution.
- `ණ`/`න` and `ල`/`ළ` are collapsed to `n`/`l` respectively at the mapping stage, per the paper's own statement that these letter pairs "are pronounced as their respective alveolar counterparts."
- `ඞ` (velar nasal in onset position) never receives an epenthetic vowel (`NO_INHERENT_VOWEL` set), per the paper's Section 5.1 exclusion list, together with anusvara `ං` and visarga `ඃ`, since these never carry a vowel modifier or hal kirima.

## 4. The eight schwa rules (as implemented, applied in this order)

Per the paper: *"Each rule given below is applied from left to right, and the presented order of the rules is to be preserved."* The implementation applies each rule exactly once per word (not repeated to a fixed point), which is a simplification from the paper's statement that rules 2, 3, 4, and 7 are applied repeatedly until no longer applicable; see §6 for why and its effect.

| Rule | Condition | Action |
|---|---|---|
| **1** | The first syllable's vowel nucleus is `ə` | Change to `a`, **except** if: (a) the syllable starts `sw-`; (b) the word starts `kər-`; (c) the word is a single CV syllable |
| **2** | `r` is preceded by a consonant and followed by a vowel, itself followed by another consonant | If the vowel is `ə` → `a`; if the vowel is `a` and the following consonant isn't `h` → `ə` (paper's 2a–2d; implementation applies each position once to avoid the oscillation the raw rule text would otherwise cause — see §6) |
| **3** | `{a, e, ae, o, ə}` + `h` + `ə` | The second `ə` (after `h`) → `a` |
| **4** | `ə` followed by two consecutive consonants (a cluster) | `ə` → `a` |
| **5** | Word-final: `ə` before the last consonant | → `a`, **unless** that final consonant is `r`, `b`, `ḍ`, or `ṭ` |
| **6** | Word-final sequence `ə, y, i` | The `ə` → `a` |
| **7** | `k` + `ə` + (`r` or `l`) + `u` | The `ə` → `a` |
| **8** | The verbal-stem exception set around `kal-` (four sub-patterns from the paper, covering `kal(aa/ee/oo)y`, `kale(m/h)(u/i)`, `kaləh(u/i)`, and bare `kalə`) | `a` → `ə` (reverses rule 1's general tendency for this specific stem) |

## 5. Diphthong mapping (paper's Table 5, as implemented)

| Phoneme sequence | Diphthong |
|---|---|
| i + w + u | iu |
| e + w + u | eu |
| ae + w + u | aeu |
| o + w + u | ou |
| a + w + u | au |
| u + y + i | ui |
| e + y + i | ei |
| ae + y + i | aei |
| o + y + i | oi |
| a + y + i | ai |

## 6. Implementation deviations from the paper (must be disclosed in Methods/Limitations)

1. **Rules are applied once per word, not iterated to a fixed point.** The paper states rules 2, 3, 4, and 7 apply repeatedly "until the conditions ... are satisfied," implying possible multiple passes within one word. This implementation applies a single left-to-right pass per rule. This was a deliberate choice, not an oversight: the paper's own text for rule 2 sub-cases (b) and (c) describes contexts that are exact mirror images of each other (`ə → a` and `a → ə` under overlapping consonant-`r`-vowel-consonant conditions); naively repeating such a rule to a fixed point would oscillate indefinitely on some inputs. The implementation instead visits each qualifying position exactly once. This is a reasonable and documented resolution of an underspecified part of the published algorithm, but it means results may differ from a literal from-scratch reimplementation on words with multiple, chained rule-2 contexts.
2. **No exception lexicon.** The paper's architecture includes a final lookup against "an exception lexicon" for irregular words (compounds, direct English loanwords such as "fashion" → ෆැෂන්, and homographs like වන/කල/කර, which the paper explicitly lists as genuinely ambiguous without a lexicon or context). No such lexicon is implemented here; this is the primary source of the paper's own reported 2% residual error rate, so this implementation's accuracy on ambiguous/compound words should be assumed comparable or slightly worse than the paper's evaluated 98%, not verified independently against a Sinhala-phonetics expert in this project.
3. **No compound-word segmentation.** The paper attributes 382 of 636 error words (60%) in its own error analysis to unsegmented compound words. This implementation has no compounding module, so multi-morpheme words are treated as a single unit, which is exactly the condition the paper identifies as its main error source.
4. **Vocalic-ṝ context rule not implemented.** The paper's error analysis (§6) separately notes that ෘ/ඍ is pronounced `/ri/` word-initially and usually `/ru/` mid-word, with 13 documented exceptions pronounced `/ur/`. The mapping table implementation captures the initial-`ri`-vs-medial-`ru` distinction structurally (independent-vowel vs. vowel-sign mapping), but does not implement the 13-word exception list from the paper's error analysis.
5. **No syllabification module.** The paper mentions its G2P is normally paired with a separate syllabification algorithm (Weerasinghe, Wasala, and Gamage, 2005, *A Rule Based Syllabification Algorithm for Sinhala*) for full TTS use. This project only needs phoneme output for text comparison, not syllable boundaries, so that companion algorithm was not implemented.

None of these deviations affect the core mapping table or the eight rules' conditions/actions themselves, which are implemented as literally as the paper's text permits.

## 7. Worked examples (generated by the current implementation)

| Sinhala input | Output (retains ə) | Compare: Method 1 (ASCII `a` only) |
|---|---|---|
| `සිංහල` | `singhələ` | `sinhala` |
| `කොහොමද?` | `kohomədə?` | `kohomada?` |
| `අම්ම` (mother) | `ammə` | `amma` |
| `කර` (do/did) | `kərə` | `kara` |
| `වන` | `wanə` | `wana` |
| `කල` | `kələ` | `kala` |
| `ප්‍රතිපත්ති` | `prətipatti` | `prathipaththi` |
| `වෙසක් උත්සවයේදී...` | `wesak utsəwəyeedii bauddəyin anugəmənəyə kərənə puujaa widi dekə nam,` | `wesak uthsawayeedii bauddhayin anugamanaya karana puujaa widhi deka nam,` |

Observe `කර → kərə` and `වන → wanə`: both end in schwa because they are common verb-stem/participle forms, illustrating rule 1's general `ə→a` tendency being *overridden* for cases the paper's exceptions cover — a linguistically meaningful contrast that the pure-ASCII methods (1, 2, 4) cannot express at all, since they always spell the bare inherent vowel as `a`.

The paper itself gives the example `අම්ම (mother) → /ammə/ → /amma:/` as one of its documented **known errors** (word-final long vowel not marked by a modifier sign, §6 "Other" error category, 37 words affected in the paper's test set). This implementation reproduces the paper's algorithm faithfully and therefore reproduces this exact same known error (`ammə` rather than the fully correct `ammaa`) — this is expected and matches the published accuracy ceiling, not a bug in this implementation.

## 8. Guarantees and validation

Same shared writer and Sinhala-leakage validator as the other three methods. Measured on this repository's data (2026-07 run): **1,851** SinhalaMMLU + **2,500** SOLD records, **0** Sinhala leakage, **0** unhandled characters (the mapping table's coverage of the Sinhala Unicode block was verified against the same corpus used for Methods 1/2/4).

Throughput: ≈7,500 strings/second — slower than the plain phonetic baseline (more processing per word: 8 rule passes + diphthong pass) but far faster than Aksharamukha or uroman (no external process/library calls).

Eight targeted unit tests (one per rule, plus the diphthong mapper) were run against minimal synthetic phoneme sequences during development to confirm each rule's condition and action fire correctly in isolation, e.g. confirming rule 5's exception list (`r, b, ḍ, ṭ`) is respected and rule 8 correctly reverses rule 1 for the `kal-` stem family.

## 9. Known limitations (for Discussion/Limitations)

- Not ASCII-only Singlish; retains `ə` as a distinct symbol (see §1 framing note — this is intentional, not a defect).
- No exception lexicon, no compound-word segmentation, no vocalic-r exception list — inherits the paper's own documented ~2% error sources, without the paper's optional lexicon-based mitigation.
- Rules applied once per word rather than iterated to a fixed point (see §6.1); differences vs. a literal from-scratch reimplementation are most likely on words with chained rule-2 contexts, which were not separately quantified in this project.
- No independent phonetic-expert validation was performed; accuracy claims in this document describe the published algorithm's evaluated accuracy (98% on the authors' 30,000-word test set), not a re-verification on SinhalaMMLU/SOLD text specifically.

## 10. Citation for the paper

> Asanka Wasala, Ruvan Weerasinghe, and Kumudu Gamage. 2006. Sinhala Grapheme-to-Phoneme Conversion and Rules for Schwa Epenthesis. In *Proceedings of the COLING/ACL 2006 Main Conference Poster Sessions*, pages 890–897, Sydney, Australia. Association for Computational Linguistics. https://aclanthology.org/P06-2114/ DOI via ACL Anthology page: https://doi.org/10.3115/1273073.1273187

Describe this method in the paper as: *"a from-scratch reimplementation, in Python, of the mapping table and eight-rule schwa epenthesis algorithm of Wasala et al. (2006), with the documented deviations in Section 6 [of this document] (no exception lexicon, no compound segmentation, single-pass rule application)."* Do not describe it as using the authors' original code or as independently re-validated against expert transcriptions.
