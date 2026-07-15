# Alternative Sinhala-to-Singlish Transliteration Methods in NLP Research

Following the character-based phonetic G2P method (Wasala et al., 2006) implemented in `phonetic.py`, research in Sinhala Natural Language Processing has developed several other sophisticated methodologies to handle transliteration. 

Below is an analysis of the two major alternative approaches found in scientific literature: **Neural Sequence-to-Sequence (Seq2Seq) Transformers** and **Hybrid Statistical/Lexicon-Based Models (Swa-Bhasha)**.

---

## 1. Sequence-to-Sequence (Seq2Seq) Transformer Models

### Overview
Instead of deterministic rules, this method treats transliteration as a character-level machine translation problem. It maps a sequence of input characters in one script directly to a sequence of characters in another script.

```
Input Character Sequence (Singlish):  [k, o, h, o, m, a, d, a]
                                     ↓  (Transformer Encoder-Decoder)
Output Character Sequence (Sinhala): [ක, ො, හ, ො, ම, ද]
```

### Technical Architecture
- **Tokenizer:** Operates at the individual character/grapheme level (rather than word-level subwords) to handle low-level phonetic mappings.
- **Encoder:** A series of self-attention layers that compile the Romanized character context.
- **Decoder with Attention:** Generates the target Sinhala Unicode characters sequentially, utilizing cross-attention to focus on the corresponding Roman characters.
- **Beam Search:** Used during decoding to evaluate the joint probability of candidate character sequences and output the most likely spelling.

### Strengths & Weaknesses
*   **Pros:**
    - **Robustness to ad-hoc typing:** Capable of mapping highly informal, non-standardized shorthand (e.g., transliterating `khmda`, `kohomd`, or `koomda` all successfully to `කොහොමද`).
    - **No manual rules:** Automatically learns character combinations and phoneme correspondences from data.
*   **Cons:**
    - **Resource Intensive:** Requires a large parallel training corpus of paired Singlish-Sinhala text.
    - **Hallucinations:** Can generate nonsensical character combinations on out-of-vocabulary words.
    - **Computationally Heavy:** Higher latency and compute requirements compared to rule-based lookups.

### Key Literature Citation
*   De Mel, Y., Wickramasinghe, K., de Silva, N., & Ranathunga, S. (2025). **Sinhala Transliteration: A Comparative Analysis Between Rule-based and Seq2Seq Approaches**. In *Proceedings of the First Workshop on Natural Language Processing for Indo-Aryan and Dravidian Languages (IndoNLP 2025)*. arXiv preprint arXiv:[2501.00529](https://arxiv.org/abs/2501.00529).

---

## 2. Hybrid Statistical & Lexicon-Based Models (Swa-Bhasha)

### Overview
Hybrid systems combine the speed and correctness of deterministic rules with statistical language models to resolve ambiguity and suggest candidates. Swa-Bhasha is a prominent implementation of this paradigm.

```
                     ┌──────────────────┐
                     │ Input (Singlish) │
                     └────────┬─────────┘
                              │
               ┌──────────────▼──────────────┐
               │  Rule-Based Candidate Gen   │
               └──────────────┬──────────────┘
                              │ (Candidate list)
               ┌──────────────▼──────────────┐
               │ Trie Lexicon & N-Gram Model │
               └──────────────┬──────────────┘
                              │ (Probability scoring)
                    ┌─────────▼────────┐
                    │ Resolved Sinhala │
                    └──────────────────┘
```

### Technical Architecture
1.  **Candidate Generation:** A rule-based parser generates a set of candidate Sinhala word reconstructions for the input Singlish word based on phonetic tables.
2.  **Trie-based Lexicon:** A Trie data structure stores a large dictionary of valid Sinhala words, filtering out phonetically possible but non-existent word candidates.
3.  **N-gram Language Model:** An n-gram character/word probability model (often trigrams) scores the remaining candidates based on contextual frequency (e.g., resolving whether a word should end in a silent consonant or an inherent vowel).

### Strengths & Weaknesses
*   **Pros:**
    - **High accuracy for standard words:** Filters out invalid spelling reconstructions using the Trie dictionary.
    - **Moderate latency:** Faster and lighter than deep-learning models while remaining more flexible than raw rules.
*   **Cons:**
    - **Dictionary dependence:** Performance degrades significantly on out-of-vocabulary (OOV) words or slang not present in the Trie database.
    - **Complexity:** Requires maintaining both a rule parser and a statistical corpus.

### Key Literature Citation
*   Sumanathilaka, D. K., Weerasinghe, R., & Ranathunga, S. (2023). **Swa-Bhasha: Romanized Sinhala to Sinhala Reverse Transliteration using a Hybrid Approach**. *International Journal on Advances in ICT for Emerging Regions (ICTer)*.
