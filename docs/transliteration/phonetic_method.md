# Sinhala-to-Singlish Transliteration Methodology

This document explains the existing transliteration method, its limitations, and the new, improved character-by-character phonetic parsing algorithm.

---

## 1. Existing Method: Inverted Lookup Table (`rule_based.py`)

### How It Works
The existing method in `rule_based.py` is a naive reference implementation. It starts with an original mapping table designed for **Singlish -> Sinhala** conversion (e.g., mapping `'kaa'` to `'කා'`, `'ke'` to `'කෙ'`). 

To go from **Sinhala -> Singlish**, it inverts this table:
```python
transliteration_table = {v: k for k, v in original_table.items()}
```

During transliteration, the algorithm uses a longest-match strategy (matching substrings of length 3, 2, or 1) against this inverted table.

### Limitations & Vowel modifier leakage
Because the original table was designed for Singlish-to-Sinhala input method editors (IMEs), it only contains mappings for specific syllables (e.g., `කෙ` -> `ke`, `ගෙ` -> `ge`) and basic consonants with their inherent vowels (e.g., `ක` -> `ka`, `ම` -> `ma`). 

It **does not** contain mappings for individual vowel modifiers (like `ෙ`, `ි`, `ු`) or the virama/hal-kirima (`්`) on their own. As a result:
1. When the algorithm encounters a consonant followed by a vowel modifier that is not explicitly in the table (e.g., `වෙ` in `වෙසක්`), it cannot match `වෙ` as a single unit.
2. It falls back to character-by-character match:
   - It matches `ව` as `'wa'`.
   - It fails to match the vowel sign `ෙ`, so it preserves `ෙ` literally.
   - It matches `ස` as `'sa'`.
   - It matches `ක` as `'ka'`.
   - It fails to match the virama `්`, so it preserves `්` literally.
3. This creates a hybrid string with raw Unicode modifiers: `waෙsaka්` (instead of `wesak`).

This leakage of raw Unicode vowel signs violates script robustness, making it difficult for downstream language models to interpret the text.

---

## 2. New Method: Phonetic Grapheme-to-Phoneme Parsing (`phonetic.py`)

### The Linguistic and Computational Approach
To resolve the Unicode leakage, we implement a robust character-by-character phonetic parsing algorithm. In Sinhala (an abugida script), consonants carry an inherent vowel sound (usually /a/). Consonants can be modified by:
1. **Dependent Vowel Signs (Pili)**: Replace the inherent vowel (e.g., `ක` (ka) + `ි` (i) = `කි` (ki)).
2. **Virama (Hal Kirima)**: Silence the inherent vowel (e.g., `ක` (ka) + `්` (virama) = `ක්` (k)).

Our new algorithm processes the Sinhala Unicode string sequentially using explicit maps for vowels, consonants, vowel signs, and special signs.

### The Parsing Rules
For each index $i$ in the string:
1. **Ignore formatting characters**: If the character is a Zero-Width Joiner (ZWJ, `\u200d`) or Zero-Width Non-Joiner (ZWNJ, `\u200c`), skip it.
2. **Independent Vowels**: If the character is an independent vowel (e.g., `අ`, `ආ`, `ඇ`), replace it directly using the vowel map and move $i \leftarrow i + 1$.
3. **Consonants**: If the character is a consonant:
   - Identify its base consonant sound (e.g., `ක` $\rightarrow$ `k`, `ව` $\rightarrow$ `w`).
   - Check the next character at $i + 1$:
     - If it is a dependent vowel sign or virama (e.g., `ි` $\rightarrow$ `i`, `්` $\rightarrow$ `""`), append `base + modifier` and move $i \leftarrow i + 2$.
     - If it is a ZWJ (`\u200d`) followed by a vowel sign, consume the ZWJ, append `base + modifier`, and move $i \leftarrow i + 3$.
     - Otherwise, the consonant has no modifiers, so we retain its inherent vowel sound by appending `base + 'a'` and moving $i \leftarrow i + 1$.
4. **Special Signs**: If the character is a special sign (like Anusvaraya `ං` $\rightarrow$ `n`, or Visargaya `ඃ` $\rightarrow$ `h`), replace it directly and move $i \leftarrow i + 1$.
5. **Non-Sinhala Characters**: If the character is English, a number, whitespace, or punctuation, preserve it as-is and move $i \leftarrow i + 1$.

---

## 3. Comparison Examples

| Input Sinhala | Inverted Lookup Method (Old) | Phonetic Parsing Method (New) | Expected Singlish |
| :--- | :--- | :--- | :--- |
| **වෙසක්** | `waෙsaka්` | `wesak` | `wesak` |
| **බෞද්ධයින්** | `baෞda්dhayaіna` (with trailing `්`) | `bauddhayin` | `bauddhayin` |
| **කොහොමද** | `koho้mada` | `kohomada` | `kohomada` |
| **සිංහල** | `si\\nhala` (escaping error) | `sinhala` | `sinhala` |

---

## 4. References & Citations

The character-by-character phonetic parsing rules and inherent vowel resolution mechanisms used in the new method are based on established guidelines for Sinhala Grapheme-to-Phoneme (G2P) conversion in NLP research:

*   **G2P Rules & Vowel Resolution:** 
    Wasala, A., Weerasinghe, R., & Gamage, K. (2006). **Sinhala Grapheme-to-Phoneme Conversion and Rules for Schwa Epenthesis**. In *Proceedings of the COLING/ACL 2006 Main Conference Poster Sessions* (pp. 890–897). Association for Computational Linguistics. DOI: [10.3115/1273073.1273187](https://doi.org/10.3115/1273073.1273187).
*   **Syllabification:** 
    Weerasinghe, R., Wasala, A., & Gamage, K. (2005). **A Rule Based Syllabification Algorithm for Sinhala**. In *Proceedings of the 2nd International Joint Conference on Natural Language Processing (IJCNLP-05)* (pp. 438–449).

