# Transliteration Method Evaluation

Which of the four Sinhala->Romanized ("Singlish") methods best reproduces how people actually romanize Sinhala? We score each method against human reference romanizations from the Swa-bhasha Resource Hub.

## Recommendation: Phonetic (in-house)

**Phonetic (in-house) is the recommended method**, but on accuracy it is a statistical tie with Nisansa web + v→w - their confidence intervals overlap, so the ranking between them is not meaningful. The recommendation therefore rests on engineering properties rather than a quality difference: Phonetic runs locally and deterministically, needs no network, covers every word in the corpus, and can be rerun by anyone offline.

| Corpus | Items | Winner by CER | Runner-up |
|---|---|---|---|
| Social media (authentic sentence pairs) | 4,397 | Phonetic (in-house) (0.182) | Nisansa web + v→w (0.182) |
| Swa-Bhasha (multi-reference words) | 449,117 | Phonetic (in-house) (0.120) | Nisansa web + v→w (0.120) |
| Augmented sentences (300k sample, cross-check) | 300,000 | Phonetic (in-house) (0.112) | Aksharamukha (0.139) |

Supporting points:

- **Wins the large-scale word set decisively**: CER 0.120 vs 0.163 (Nisansa), 0.147 (Aksharamukha) and 0.227 (uroman) across 449,117 words with 7.1M accepted human variants (p < 1e-300 against every one of them).
- **Wins authentic social-media text too**: CER 0.182 vs Nisansa 0.197, with the highest chrF (67.8 vs 63.4). See the capitalization note below - scoring case-sensitively reverses this ranking for the wrong reason.
- **Matches human spelling convention**: humans overwhelmingly use `w` (not `v`) and use aspiration and gemination at rates Phonetic reproduces closely (see convention table). Aksharamukha drops aspiration; uroman uses `v` and over-geminates.
- **Complete and reproducible**: local and deterministic, so the whole corpus can be regenerated offline and covers every word. Nisansa is a third-party web endpoint that can change or go offline, and it cannot romanize part of the alphabet at all (see the limitation note below), so it is both less reproducible and less complete.

**Biggest remaining gap (all methods):** over-doubling of long vowels (~0.8/token on words vs humans' ~0.12). A trivial post-process collapsing `aa/ee/ii/oo/uu` would close roughly half the residual CER to human text (relaxed CER is ~1/3 of strict).

### The v/w convention accounted for Nisansa's entire gap

Nisansa's output matches the phonetic method on long vowels, aspiration and gemination, and differs almost only in writing ව as `v` where humans overwhelmingly write `w`. Rewriting just that one convention in its output (`nisansa_w`, a post-process of the cached results - not the published tool) removes the difference entirely:

| Corpus | Nisansa as published | Nisansa with v→w | Phonetic |
|---|---|---|---|
| Social media (authentic sentence pairs) | 0.197 | **0.182** | 0.182 |
| Swa-Bhasha (multi-reference words) | 0.163 | **0.120** | 0.120 |

So the two methods are equivalent in romanization quality once that single orthographic choice is normalized, which is consistent with the relaxed metrics: after canonicalizing spelling style, their CERs were already identical to four decimal places. The honest conclusion is that Nisansa is not a *worse* romanizer - it simply writes `v`, and Sinhala speakers type `w`. Phonetic remains the recommendation because it matches human convention out of the box and is local, complete and reproducible, not because it transliterates better.

### Note: letter case is a UI artifact, not a romanization choice

The Nisansa web form capitalizes the first letter of whatever text it is given (93% of its outputs), the three local methods never capitalize, and 84% of the human social-media references happen to start with a capital. Scoring case-sensitively therefore rewards one method for an interface side-effect - and that alone is enough to flip the social-media ranking. The primary metrics fold case; the case-sensitive column below shows the size of the artifact.

| Corpus | Method | CER (case-folded, primary) | CER (case-sensitive) |
|---|---|---|---|
| Social media (authentic sentence pairs) | Phonetic (in-house) | 0.182 | 0.216 |
| Social media (authentic sentence pairs) | Aksharamukha | 0.191 | 0.225 |
| Social media (authentic sentence pairs) | uroman | 0.228 | 0.261 |
| Social media (authentic sentence pairs) | Nisansa web | 0.197 | 0.210 |
| Social media (authentic sentence pairs) | Nisansa web + v→w | 0.182 | 0.196 |
| Swa-Bhasha (multi-reference words) | Phonetic (in-house) | 0.120 | 0.120 |
| Swa-Bhasha (multi-reference words) | Aksharamukha | 0.147 | 0.147 |
| Swa-Bhasha (multi-reference words) | uroman | 0.227 | 0.227 |
| Swa-Bhasha (multi-reference words) | Nisansa web | 0.163 | 0.170 |
| Swa-Bhasha (multi-reference words) | Nisansa web + v→w | 0.120 | 0.128 |
| Augmented sentences (300k sample, cross-check) | Phonetic (in-house) | 0.112 | 0.112 |
| Augmented sentences (300k sample, cross-check) | Aksharamukha | 0.139 | 0.139 |
| Augmented sentences (300k sample, cross-check) | uroman | 0.210 | 0.210 |

## Metrics glossary

- **CER / WER**: character / word error rate vs the closest accepted human variant (lower = better).
- **chrF, chrF++**: character n-gram F-score (higher = better); robust for morphology-rich scripts.
- **BLEU**: word-level MT metric (higher = better); least reliable here, reported for comparability.
- **Exact %**: share of items matching a human variant exactly.
- **Relaxed CER / Exact**: after canonicalizing spelling style (long vowels, w/v, aspiration, gemination) on both sides - isolates genuine phonemic error from mere spelling convention.

## Data & methodology

- **References** (Swa-bhasha Resource Hub, Sumanathilaka et al.): `social_media` - 4,397 authentic, code-mixed YouTube-comment sentence pairs; `swa_bhasha_words` - 450,587 unique words each with multiple accepted ad-hoc romanizations (7.1M total), enabling fair multi-reference scoring; `augmented_sentences_sample` - a fixed-seed 300k sample of the 7.2M machine-augmented sentence pairs, used only as a cross-check (its romanizations are themselves rule-generated, so it partly measures agreement with a generator rather than with human typing).

- **Case folding**: strict metrics are computed on case-folded text, because case reflects each tool's interface rather than its romanization scheme (see the note above).

- **Multi-reference scoring**: because Singlish is non-standard, each hypothesis is scored against the *closest* accepted human variant (oracle best reference).

- **Strict vs relaxed**: strict compares surface strings; relaxed canonicalizes spelling style on both sides. After canonicalization the three local methods agree 99.2% of the time, i.e. they are phonemically equivalent and differ only in spelling convention - so the ranking is a question of *which convention matches human typing*, which strict CER/chrF capture.

- **Significance**: percentile bootstrap 95% CIs on mean CER and paired Wilcoxon signed-rank tests against the per-corpus best method.

- **Nisansa coverage**: this method is a web form rather than a local library. It romanizes free text line by line, so items are batched (newline-joined) instead of sent one per request, which is ~78x faster and was verified to give output identical to one-request-per-item, ignoring case, on all 4,253 social-media strings. It is scored on the full word corpus and the full social-media corpus; it is absent from the augmented cross-check.

- **A limitation of the Nisansa tool**: it cannot romanize the letter ඤ (U+0DA4) when that letter carries certain vowel signs - specifically followed by al-lakuna, ā, i or u. Such input returns an empty result. Verified by direct probing: ඤ alone, ඤ+ඤ, ක+ඤ, ඤ+ka and ඤ+e all succeed, as does the neighbouring letter ඥ (U+0DA5), so the tool's mapping table is missing those combinations rather than the letter itself. This affects 1,470 of 450,587 words (0.33%). Those items are excluded from **all** methods so that every method is scored on exactly the same rows; substituting another method's output would be worse, because the natural stand-in is the phonetic method that is itself under comparison, and its answers would inflate the score of whichever method borrowed them. The effect either way is far below the margin between methods.

## Social media (authentic sentence pairs)

Items: 4,397. Best method by strict CER listed first.

| Method | CER | WER | chrF | chrF++ | BLEU | Exact % | Relaxed CER | Relaxed Exact % |
|---|---|---|---|---|---|---|---|---|
| Phonetic (in-house) | 0.182 | 0.606 | 67.8 | 59.3 | 28.6 | 4.2 | 0.108 | 11.8 |
| Nisansa web + v→w | 0.182 | 0.606 | 67.8 | 59.3 | 28.6 | 4.2 | 0.108 | 11.9 |
| Aksharamukha | 0.191 | 0.640 | 63.7 | 55.4 | 26.3 | 3.5 | 0.108 | 11.8 |
| Nisansa web | 0.197 | 0.647 | 63.4 | 54.9 | 25.4 | 3.2 | 0.108 | 11.9 |
| uroman | 0.228 | 0.746 | 55.7 | 47.1 | 20.7 | 1.6 | 0.108 | 11.9 |

**Significance** (best = Phonetic (in-house); paired Wilcoxon on per-item CER):

| Method | CER 95% CI | p vs best |
|---|---|---|
| Phonetic (in-house) | [0.178, 0.186] | — (best) |
| Aksharamukha | [0.187, 0.195] | 2.24e-130 |
| uroman | [0.224, 0.232] | 0.00e+00 |
| Nisansa web | [0.193, 0.201] | 1.47e-180 |
| Nisansa web + v→w | [0.178, 0.186] | 1.59e-03 |

## Swa-Bhasha (multi-reference words)

Items: 449,117. Best method by strict CER listed first.

| Method | CER | WER | chrF | chrF++ | BLEU | Exact % | Relaxed CER | Relaxed Exact % |
|---|---|---|---|---|---|---|---|---|
| Phonetic (in-house) | 0.120 | 0.667 | 78.8 | 64.6 | 10.6 | 33.3 | 0.039 | 74.3 |
| Nisansa web + v→w | 0.120 | 0.666 | 78.7 | 64.4 | 10.4 | 33.4 | 0.039 | 74.1 |
| Aksharamukha | 0.147 | 0.760 | 69.7 | 56.2 | 0.8 | 24.0 | 0.040 | 73.8 |
| Nisansa web | 0.163 | 0.776 | 67.9 | 54.3 | 7.9 | 22.4 | 0.039 | 74.1 |
| uroman | 0.227 | 0.903 | 51.7 | 40.5 | 6.1 | 9.7 | 0.044 | 71.8 |

**Significance** (best = Phonetic (in-house); paired Wilcoxon on per-item CER):

| Method | CER 95% CI | p vs best |
|---|---|---|
| Phonetic (in-house) | [0.120, 0.120] | — (best) |
| Aksharamukha | [0.147, 0.148] | 0.00e+00 |
| uroman | [0.227, 0.228] | 0.00e+00 |
| Nisansa web | [0.163, 0.164] | 0.00e+00 |
| Nisansa web + v→w | [0.120, 0.120] | 1.08e-05 |

## Augmented sentences (300k sample, cross-check)

Items: 300,000. Best method by strict CER listed first.

| Method | CER | WER | chrF | chrF++ | BLEU | Exact % | Relaxed CER | Relaxed Exact % |
|---|---|---|---|---|---|---|---|---|
| Phonetic (in-house) | 0.112 | 0.534 | 79.6 | 68.3 | 15.4 | 3.4 | 0.037 | 17.0 |
| Aksharamukha | 0.139 | 0.625 | 70.3 | 59.0 | 8.7 | 2.8 | 0.037 | 16.9 |
| uroman | 0.210 | 0.781 | 53.5 | 43.3 | 2.2 | 1.7 | 0.040 | 15.5 |

**Significance** (best = Phonetic (in-house); paired Wilcoxon on per-item CER):

| Method | CER 95% CI | p vs best |
|---|---|---|
| Phonetic (in-house) | [0.112, 0.113] | — (best) |
| Aksharamukha | [0.139, 0.140] | 0.00e+00 |
| uroman | [0.210, 0.211] | 0.00e+00 |

## Why: spelling-convention profile

How each method's output compares to human typing on the four axes that dominate Singlish variation. The method whose profile is closest to the human row tends to win.

### Social media (authentic sentence pairs)

| Source | v-preference (v/(v+w)) | long-vowel/tok | aspiration/tok | gemination/tok |
|---|---|---|---|---|
| Human reference | 0.20 | 0.05 | 0.15 | 0.18 |
| Phonetic (in-house) | 0.00 | 0.38 | 0.17 | 0.16 |
| Aksharamukha | 0.00 | 0.38 | 0.03 | 0.17 |
| uroman | 1.00 | 0.30 | 0.00 | 0.36 |
| Nisansa web | 1.00 | 0.38 | 0.17 | 0.16 |
| Nisansa web + v→w | 0.00 | 0.38 | 0.17 | 0.16 |

### Swa-Bhasha (multi-reference words)

| Source | v-preference (v/(v+w)) | long-vowel/tok | aspiration/tok | gemination/tok |
|---|---|---|---|---|
| Human reference | 0.01 | 0.12 | 0.55 | 0.11 |
| Phonetic (in-house) | 0.00 | 0.81 | 0.56 | 0.12 |
| Aksharamukha | 0.00 | 0.81 | 0.23 | 0.14 |
| uroman | 1.00 | 0.80 | 0.00 | 0.37 |
| Nisansa web | 1.00 | 0.81 | 0.56 | 0.11 |
| Nisansa web + v→w | 0.00 | 0.81 | 0.56 | 0.11 |

### Augmented sentences (300k sample, cross-check)

| Source | v-preference (v/(v+w)) | long-vowel/tok | aspiration/tok | gemination/tok |
|---|---|---|---|---|
| Human reference | 0.00 | 0.09 | 0.38 | 0.04 |
| Phonetic (in-house) | 0.00 | 0.56 | 0.38 | 0.05 |
| Aksharamukha | 0.00 | 0.56 | 0.13 | 0.06 |
| uroman | 1.00 | 0.56 | 0.00 | 0.20 |

## Figures

![case_sensitivity_artifact](../../results/method_evaluation/plots/case_sensitivity_artifact.png)

![cer_by_method](../../results/method_evaluation/plots/cer_by_method.png)

![cer_distribution_augmented_sentences_sample](../../results/method_evaluation/plots/cer_distribution_augmented_sentences_sample.png)

![cer_distribution_social_media](../../results/method_evaluation/plots/cer_distribution_social_media.png)

![cer_distribution_swa_bhasha_words](../../results/method_evaluation/plots/cer_distribution_swa_bhasha_words.png)

![exact_match](../../results/method_evaluation/plots/exact_match.png)

![heatmap_augmented_sentences_sample](../../results/method_evaluation/plots/heatmap_augmented_sentences_sample.png)

![heatmap_social_media](../../results/method_evaluation/plots/heatmap_social_media.png)

![heatmap_swa_bhasha_words](../../results/method_evaluation/plots/heatmap_swa_bhasha_words.png)

![quality_metrics](../../results/method_evaluation/plots/quality_metrics.png)

![strict_vs_relaxed_cer](../../results/method_evaluation/plots/strict_vs_relaxed_cer.png)
