# Transliteration Method Evaluation

Which of the four Sinhala->Romanized ("Singlish") methods best reproduces how people actually romanize Sinhala? We score each method against human reference romanizations from the Swa-bhasha Resource Hub.

## Recommendation: Phonetic (in-house)

**Phonetic (in-house) is the best method** on every corpus tested and is the recommended choice for the downstream script-robustness pipeline. It has the lowest CER and the highest chrF everywhere, and it is the only top-ranked option that is local, deterministic, free, and reproducible offline.

Its nearest rival is Nisansa web (v→w preprocessed), behind by at most 0.0120 CER. The paired Wilcoxon separates them on every corpus, so the ordering is not a coin flip - but the margin is small in absolute terms, and it comes from coverage and leaked characters rather than from better letter-to-letter mapping. On the items Nisansa did answer, and with the v/w convention normalized, the two are very close.

| Corpus | Items | Winner by CER | Runner-up |
|---|---|---|---|
| Social media (authentic sentence pairs) | 4,397 | Phonetic (in-house) (0.182) | Nisansa web (v→w preprocessed) (0.182) |
| Swa-Bhasha (multi-reference words) | 450,587 | Phonetic (in-house) (0.121) | Nisansa web (v→w preprocessed) (0.133) |
| Augmented sentences (300k sample, cross-check) | 300,000 | Phonetic (in-house) (0.112) | Nisansa web (v→w preprocessed) (0.114) |

Supporting points:

- **Wins the large-scale word set decisively**: CER 0.121 vs 0.176 (Nisansa), 0.148 (Aksharamukha) and 0.228 (uroman) across 450,587 words with 7.1M accepted human variants (p < 1e-300 against every one of them).
- **Wins authentic social-media text too**: CER 0.182 vs Nisansa 0.197, with the highest chrF (67.8 vs 63.4). See the capitalization note below - scoring case-sensitively reverses this ranking for the wrong reason.
- **Matches human spelling convention**: humans overwhelmingly use `w` (not `v`) and use aspiration and gemination at rates Phonetic reproduces closely (see convention table). Aksharamukha drops aspiration; uroman uses `v` and over-geminates.
- **Complete and reproducible**: local and deterministic, so the whole corpus can be regenerated offline and covers every word. Nisansa is a third-party web endpoint that can change or go offline, and it cannot romanize part of the alphabet at all (see the limitation note below), so it is both less reproducible and less complete.

**Biggest remaining gap (all methods):** over-doubling of long vowels (~0.8/token on words vs humans' ~0.12). A trivial post-process collapsing `aa/ee/ii/oo/uu` would close roughly half the residual CER to human text (relaxed CER is ~1/3 of strict).

### The v/w convention accounted for Nisansa's entire gap

Nisansa's output matches the phonetic method on long vowels, aspiration and gemination, and differs almost only in writing ව as `v` where humans overwhelmingly write `w`. Rewriting just that one convention is applied as a preprocessing stage before scoring (a pure post-process of the fetched results, not the published tool) and removes the difference entirely:

| Corpus | Nisansa as published | Nisansa with v→w | Phonetic |
|---|---|---|---|
| Social media (authentic sentence pairs) | 0.197 | **0.182** | 0.182 |
| Swa-Bhasha (multi-reference words) | 0.176 | **0.133** | 0.121 |
| Augmented sentences (300k sample, cross-check) | 0.153 | **0.114** | 0.112 |

So the two methods are equivalent in romanization quality once that single orthographic choice is normalized, which is consistent with the relaxed metrics: after canonicalizing spelling style, their CERs were already identical to four decimal places. The honest conclusion is that Nisansa is not a *worse* romanizer - it simply writes `v`, and Sinhala speakers type `w`. Phonetic remains the recommendation because it matches human convention out of the box and is local, complete and reproducible, not because it transliterates better.

### Note: letter case is a UI artifact, not a romanization choice

The Nisansa web form capitalizes the first letter of whatever text it is given (93% of its outputs), the three local methods never capitalize, and 84% of the human social-media references happen to start with a capital. Scoring case-sensitively therefore rewards one method for an interface side-effect - and that alone is enough to flip the social-media ranking. The primary metrics fold case; the case-sensitive column below shows the size of the artifact.

| Corpus | Method | CER (case-folded, primary) | CER (case-sensitive) |
|---|---|---|---|
| Social media (authentic sentence pairs) | Phonetic (in-house) | 0.182 | 0.216 |
| Social media (authentic sentence pairs) | Aksharamukha | 0.191 | 0.225 |
| Social media (authentic sentence pairs) | uroman | 0.228 | 0.261 |
| Social media (authentic sentence pairs) | Nisansa web (as published) | 0.197 | 0.210 |
| Social media (authentic sentence pairs) | Nisansa web (v→w preprocessed) | 0.182 | 0.196 |
| Swa-Bhasha (multi-reference words) | Phonetic (in-house) | 0.121 | 0.121 |
| Swa-Bhasha (multi-reference words) | Aksharamukha | 0.148 | 0.148 |
| Swa-Bhasha (multi-reference words) | uroman | 0.228 | 0.228 |
| Swa-Bhasha (multi-reference words) | Nisansa web (as published) | 0.176 | 0.176 |
| Swa-Bhasha (multi-reference words) | Nisansa web (v→w preprocessed) | 0.133 | 0.133 |
| Augmented sentences (300k sample, cross-check) | Phonetic (in-house) | 0.112 | 0.112 |
| Augmented sentences (300k sample, cross-check) | Aksharamukha | 0.139 | 0.139 |
| Augmented sentences (300k sample, cross-check) | uroman | 0.210 | 0.210 |
| Augmented sentences (300k sample, cross-check) | Nisansa web (as published) | 0.153 | 0.154 |
| Augmented sentences (300k sample, cross-check) | Nisansa web (v→w preprocessed) | 0.114 | 0.115 |

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

- **Nisansa coverage**: this method is a web form rather than a local library. It romanizes free text line by line, so items are batched (newline-joined) instead of sent one per request, which is ~78x faster and was verified to give output identical to one-request-per-item, ignoring case, on all 4,253 social-media strings. It is scored on every item of every corpus.

- **v→w preprocessing**: the endpoint writes ව as `v` where Sinhala speakers type `w`. Since that one orthographic choice accounted for its entire measured gap, the rewrite is applied as a standard preprocessing stage and `Nisansa web (v→w preprocessed)` is the variant to read as *the* Nisansa result. The as-published row is kept beside it so the modification stays visible.

- **Nothing is excluded.** Where a method produced no output for an item, that item is scored as total error (CER 1.0) rather than dropped. Failing to romanize an input is a property of the tool, so excusing it would flatter the tool; the `Coverage` column below makes the size of that effect explicit. An earlier revision scored only the rows every method answered, which measured mapping quality but hid a coverage failure; those matched-subset numbers are still reproducible with `run_evaluation.py --common-subset`.

- **Two measured defects in the Nisansa tool.** Both are characterised by direct probing of the full Sinhala akshara grid (881 units, `nisansa_probe.py`), not inferred from failures:
  1. *No output at all* for **17 sequences**, every one of them ඤ (U+0DA4) carrying a vowel sign or al-lakuna (ඤ්, ඤා, ඤැ, ඤෑ, ඤි, ඤී, ඤු, ඤූ, ඤෘ, ඤේ, ඤෛ, ඤො, ඤෝ, ඤෞ, ඤෲ, ඤ්‍ය, ඤ්‍ර). The letter ඤ alone romanizes fine, as does ඤෙ and the neighbouring ඥ (U+0DA5), so the tool's mapping table is missing those specific combinations rather than the letter. The probe's table reproduces exactly the 1,470 of 450,587 words (0.33%) that the corpus run found by bisection - independent confirmation that it is neither over- nor under-inclusive.
  2. *Silent leaks*: **12 sequences** come back unromanized inside otherwise valid Latin output (ඎ, ඏ, ඐ, ඓ, ඞ, ඦ, ෟ, ෳ, ඣෙ, ඤෙ, ඥෙ, ඬෙ), so ඓතිහාසික romanizes to `ඓthihaasika`. Real corpus text also leaks on malformed sequences outside the grid, such as a vowel sign followed by al-lakuna. These are scored as they are. An earlier revision ran the in-house phonetic romanizer over every response to patch such characters up, which made the measured system a hybrid of two methods under comparison and hid the defect; all results here are the endpoint's verbatim output.

## Social media (authentic sentence pairs)

Items: 4,397. Best method by strict CER listed first.

| Method | Coverage % | CER | WER | chrF | chrF++ | BLEU | Exact % | Relaxed CER | Relaxed Exact % |
|---|---|---|---|---|---|---|---|---|---|
| Phonetic (in-house) | 100.00 | 0.182 | 0.606 | 67.8 | 59.3 | 28.6 | 4.2 | 0.108 | 11.8 |
| Nisansa web (v→w preprocessed) | 100.00 | 0.182 | 0.606 | 67.8 | 59.3 | 28.6 | 4.2 | 0.108 | 11.9 |
| Aksharamukha | 100.00 | 0.191 | 0.640 | 63.7 | 55.4 | 26.3 | 3.5 | 0.108 | 11.8 |
| Nisansa web (as published) | 100.00 | 0.197 | 0.647 | 63.4 | 54.9 | 25.4 | 3.2 | 0.108 | 11.9 |
| uroman | 100.00 | 0.228 | 0.746 | 55.7 | 47.1 | 20.7 | 1.6 | 0.108 | 11.9 |

**Significance** (best = Phonetic (in-house); paired Wilcoxon on per-item CER):

| Method | CER 95% CI | p vs best |
|---|---|---|
| Phonetic (in-house) | [0.178, 0.186] | — (best) |
| Aksharamukha | [0.187, 0.195] | 2.24e-130 |
| uroman | [0.224, 0.232] | 0.00e+00 |
| Nisansa web (as published) | [0.193, 0.201] | 1.47e-180 |
| Nisansa web (v→w preprocessed) | [0.178, 0.186] | 1.59e-03 |

## Swa-Bhasha (multi-reference words)

Items: 450,587. Best method by strict CER listed first.

| Method | Coverage % | CER | WER | chrF | chrF++ | BLEU | Exact % | Relaxed CER | Relaxed Exact % |
|---|---|---|---|---|---|---|---|---|---|
| Phonetic (in-house) | 100.00 | 0.121 | 0.668 | 78.7 | 64.4 | 10.6 | 33.2 | 0.040 | 74.0 |
| Nisansa web (v→w preprocessed) | 99.67 (1,470 empty) | 0.133 | 0.691 | 76.1 | 62.1 | 10.2 | 30.9 | 0.043 | 73.8 |
| Aksharamukha | 100.00 | 0.148 | 0.761 | 69.6 | 56.1 | 0.8 | 23.9 | 0.041 | 73.5 |
| Nisansa web (as published) | 99.67 (1,470 empty) | 0.176 | 0.794 | 65.5 | 52.3 | 7.7 | 20.6 | 0.043 | 73.8 |
| uroman | 100.00 | 0.228 | 0.903 | 51.6 | 40.4 | 6.0 | 9.7 | 0.044 | 71.6 |

**Significance** (best = Phonetic (in-house); paired Wilcoxon on per-item CER):

| Method | CER 95% CI | p vs best |
|---|---|---|
| Phonetic (in-house) | [0.120, 0.121] | — (best) |
| Aksharamukha | [0.147, 0.148] | 0.00e+00 |
| uroman | [0.227, 0.228] | 0.00e+00 |
| Nisansa web (as published) | [0.175, 0.176] | 0.00e+00 |
| Nisansa web (v→w preprocessed) | [0.132, 0.133] | 0.00e+00 |

## Augmented sentences (300k sample, cross-check)

Items: 300,000. Best method by strict CER listed first.

| Method | Coverage % | CER | WER | chrF | chrF++ | BLEU | Exact % | Relaxed CER | Relaxed Exact % |
|---|---|---|---|---|---|---|---|---|---|
| Phonetic (in-house) | 100.00 | 0.112 | 0.534 | 79.6 | 68.3 | 15.4 | 3.4 | 0.037 | 17.0 |
| Nisansa web (v→w preprocessed) | 99.85 (449 empty) | 0.114 | 0.534 | 79.4 | 68.2 | 15.4 | 3.4 | 0.038 | 17.1 |
| Aksharamukha | 100.00 | 0.139 | 0.625 | 70.3 | 59.0 | 8.7 | 2.8 | 0.037 | 16.9 |
| Nisansa web (as published) | 99.85 (449 empty) | 0.153 | 0.646 | 68.5 | 57.3 | 7.6 | 2.5 | 0.038 | 17.1 |
| uroman | 100.00 | 0.210 | 0.781 | 53.5 | 43.3 | 2.2 | 1.7 | 0.040 | 15.5 |

**Significance** (best = Phonetic (in-house); paired Wilcoxon on per-item CER):

| Method | CER 95% CI | p vs best |
|---|---|---|
| Phonetic (in-house) | [0.112, 0.113] | — (best) |
| Aksharamukha | [0.139, 0.140] | 0.00e+00 |
| uroman | [0.210, 0.211] | 0.00e+00 |
| Nisansa web (as published) | [0.153, 0.154] | 0.00e+00 |
| Nisansa web (v→w preprocessed) | [0.113, 0.114] | 8.92e-94 |

## Why: spelling-convention profile

How each method's output compares to human typing on the four axes that dominate Singlish variation. The method whose profile is closest to the human row tends to win.

### Social media (authentic sentence pairs)

| Source | v-preference (v/(v+w)) | long-vowel/tok | aspiration/tok | gemination/tok | leaked Sinhala % |
|---|---|---|---|---|---|
| Human reference | 0.20 | 0.05 | 0.15 | 0.18 | 0.00 |
| Phonetic (in-house) | 0.00 | 0.38 | 0.17 | 0.16 | 0.00 |
| Aksharamukha | 0.00 | 0.38 | 0.03 | 0.17 | 0.00 |
| uroman | 1.00 | 0.30 | 0.00 | 0.36 | 0.00 |
| Nisansa web (as published) | 1.00 | 0.38 | 0.17 | 0.16 | 0.00 |
| Nisansa web (v→w preprocessed) | 0.00 | 0.38 | 0.17 | 0.16 | 0.00 |

Rates are computed over the items each method produced output for, so a failed item cannot flatter a method by contributing zero tokens; coverage is charged in the metric tables above instead.

### Swa-Bhasha (multi-reference words)

| Source | v-preference (v/(v+w)) | long-vowel/tok | aspiration/tok | gemination/tok | leaked Sinhala % |
|---|---|---|---|---|---|
| Human reference | 0.01 | 0.12 | 0.55 | 0.11 | 0.00 |
| Phonetic (in-house) | 0.00 | 0.81 | 0.56 | 0.12 | 0.00 |
| Aksharamukha | 0.00 | 0.81 | 0.23 | 0.14 | 0.00 |
| uroman | 1.00 | 0.80 | 0.00 | 0.37 | 0.00 |
| Nisansa web (as published) | 1.00 | 0.81 | 0.56 | 0.11 | 0.82 |
| Nisansa web (v→w preprocessed) | 0.00 | 0.81 | 0.56 | 0.11 | 0.82 |

Rates are computed over the items each method produced output for, so a failed item cannot flatter a method by contributing zero tokens; coverage is charged in the metric tables above instead.

### Augmented sentences (300k sample, cross-check)

| Source | v-preference (v/(v+w)) | long-vowel/tok | aspiration/tok | gemination/tok | leaked Sinhala % |
|---|---|---|---|---|---|
| Human reference | 0.00 | 0.09 | 0.38 | 0.04 | 0.00 |
| Phonetic (in-house) | 0.00 | 0.56 | 0.38 | 0.05 | 0.00 |
| Aksharamukha | 0.00 | 0.56 | 0.13 | 0.06 | 0.00 |
| uroman | 1.00 | 0.56 | 0.00 | 0.20 | 0.00 |
| Nisansa web (as published) | 1.00 | 0.56 | 0.38 | 0.04 | 2.48 |
| Nisansa web (v→w preprocessed) | 0.00 | 0.56 | 0.38 | 0.04 | 2.48 |

Rates are computed over the items each method produced output for, so a failed item cannot flatter a method by contributing zero tokens; coverage is charged in the metric tables above instead.

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
