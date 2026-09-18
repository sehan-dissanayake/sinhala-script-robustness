# Sinhala Script Robustness — Full Analysis Report

> All numbers drawn live from [`intrinsic_numbers.json`](../../paper/analysis/out/intrinsic_numbers.json), [`extrinsic_numbers.json`](../../paper/analysis/out/extrinsic_numbers.json), and their source scripts [`stats_intrinsic.py`](../../paper/analysis/stats_intrinsic.py) / [`stats_extrinsic.py`](../../paper/analysis/stats_extrinsic.py).

---

## Overview

The study runs **31 language model checkpoints** (350M–14.7B parameters, 8 families) under **three script conditions** on a 500-sentence parallel corpus for intrinsic analysis, and **10 instruction-tuned checkpoints** across **three downstream tasks** (9,479 items total) for extrinsic analysis. Every result is generated from raw per-item model outputs — no number is typed by hand.

The three script conditions are:
- **Unicode (U)** — native Sinhala script
- **Romanized (R)** — Latin transliteration
- **Mixed (M)** — interleaved native and Latin tokens

---

# Part 1 — Intrinsic Tests

> Source: [`stats_intrinsic.py`](../../paper/analysis/stats_intrinsic.py), corpus: 500 parallel sentence pairs, 31 checkpoints.

---

## Test 1 — Reproduction Check (Sanity Gate)

### Intended Purpose
Before drawing any new conclusions, verify that our re-computed perplexities match the values published by the prior benchmark (Rajapakse & Weerasinghe, 2026) on their 24 shared checkpoints. If reproduction fails, differences could come from measurement error rather than metric choice — invalidating all downstream comparisons.

### How It Is Done
For each of the 24 shared checkpoints, compute the **percentage deviation** between our perplexity and the published value:

```
delta_U = 100 * (PPL_ours - PPL_pub) / PPL_pub
```

The same formula applies for Romanized and Mixed. Median absolute percentage error is reported.

### Result
| Condition | Median Absolute Deviation |
|-----------|--------------------------|
| Unicode   | **0.047%** |
| Romanized | **0.004%** |
| Mixed     | 0.387% (excl. 2 outliers) |

The two mixed-script outliers (Phi-4-14B and Mistral-Nemo-Base-2407) are flagged because our parallel-sentence scoring differs slightly from the prior work's mixed-corpus approach. Unicode and Romanized are reproduced to within machine rounding. **This confirms every finding that follows is caused by the metric, not a different experimental run.**

---

## Test 2 — Perplexity vs. BPB Rank Correlation (Core Methodological Claim)

### Intended Purpose
Demonstrate that perplexity and bits-per-byte (BPB) **induce completely different model rankings** — i.e., the metric choice is not neutral. If rho ≈ 0, then choosing PPL vs. BPB does not just re-scale the same ranking; it produces an entirely different conclusion about which models are "best" at Sinhala.

### How It Is Done
Spearman's rho is computed between every model's corpus-pooled PPL and its corpus-pooled BPB under the same script condition (n = 31). BPB is computed by pooling total NLL in nats across all 500 sentences, then dividing by `ln(2) * total_bytes` — this is different from averaging per-sentence BPB and prevents short sentences from dominating. A Top-5 overlap count is also computed.

### Result
| Pair | rho | p-value |
|------|-----|---------|
| Unicode PPL vs. Unicode BPB | **+0.077** | 0.680 |
| Romanized PPL vs. Romanized BPB | +0.131 | 0.481 |
| Mixed PPL vs. Mixed BPB | +0.133 | 0.477 |

Top-5 overlap (Unicode PPL vs. BPB): **1 of 5 models shared.**

The correlation is essentially zero. Biggest reversal: Gemma-2-9B ranks **26th by PPL** but **2nd by BPB**; Qwen3.5-9B-Base goes from **28th to 6th**.

---

## Test 3 — Tokenizer Fertility vs. Perplexity (Root Cause Analysis)

### Intended Purpose
Explain *why* PPL and BPB disagree. The hypothesis: PPL is contaminated by tokenizer fertility — models with fine-grained tokenizers that shred a Sinhala word into many tokens report low per-token loss simply because probability mass is spread over more, smaller prediction steps. No actual language understanding is required.

### How It Is Done
Tokenizer fertility = total scored tokens / total whitespace words on the 500-sentence corpus. Spearman rho is computed between fertility and perplexity across all 31 checkpoints.

### Result
| Pair | rho | p-value |
|------|-----|---------|
| Unicode tok/word vs. Unicode PPL | **–0.873** | 1.6 × 10⁻¹⁰ |
| Romanized tok/word vs. Romanized PPL | –0.666 | 4.3 × 10⁻⁵ |

Fertility ranges from **4.3** (Qwen3.5, Gemma tokenizers) to **14.2** (byte-fallback tokenizers) tokens per Sinhala word. Spreading the same total loss over 3× as many tokens lowers per-token perplexity dramatically with zero improvement in understanding. **This is the root cause of all rank reversals in Test 2.**

---

## Test 4 — Scale (Parameter Count) vs. Script Quality

### Intended Purpose
The prior benchmark reported no correlation between model size and Sinhala ability. Test whether this null result survives when using a tokenizer-independent metric (BPB) vs. the confounded metric (PPL).

### How It Is Done
Spearman rho between parameter count and per-script BPB / PPL across all 31 checkpoints.

### Result
| Pair | rho | p-value | Conclusion |
|------|-----|---------|------------|
| Params vs. Unicode PPL | +0.149 | 0.423 | No relationship |
| Params vs. Unicode BPB | **–0.550** | **0.0014** | Larger = better |
| Params vs. Romanized PPL | +0.113 | 0.546 | No relationship |
| Params vs. Romanized BPB | –0.279 | 0.128 | Still insignificant |
| Params vs. Mixed BPB | **–0.573** | **0.0008** | Larger = better |

Scale **does** predict native-script ability once the tokenizer confound is removed. It does **not** predict Romanized ability under either metric.

---

## Test 5 — Romanization Flattening (BPW Spread Analysis)

### Intended Purpose
Quantify how much model-quality variation is preserved or destroyed by the script change. BPW (bits per word) is used rather than BPB because a sentence and its transliteration share the exact same word count — making BPW a script-neutral comparison unit.

### How It Is Done
The **spread** (max − min BPW) is compared across the 31 checkpoints under each condition. A count is kept of models where BPW_romanized < BPW_unicode (models that are literally cheaper on Romanized text).

### Result
| Condition | Min BPW | Max BPW | Spread |
|-----------|---------|---------|--------|
| Unicode   | 16.3    | 34.1    | **17.7 bits** |
| Romanized | 20.3    | 25.7    | **5.4 bits** |

12 of 31 checkpoints are cheaper on Romanized than on native Sinhala. These are exactly the models that were worst natively — they had little to lose. Romanized Sinhala creates a quality ceiling where differences between models largely disappear.

---

## Test 6 — Carryover Regression (BPW)

### Intended Purpose
Quantify the *slope* at which native-script quality carries over to Romanized. A slope of 1.0 means equal improvement transfers; near 0 means almost nothing transfers.

### How It Is Done
OLS regression of Romanized BPW on Unicode BPW across 31 checkpoints: `BPW_R = alpha + beta * BPW_U`. Bootstrap confidence interval on beta: 20,000 resamples with replacement over the 31 checkpoints, taking the 2.5th and 97.5th percentiles.

### Result
```
beta = 0.136   (95% CI [0.054, 0.247])
R2 = 0.19,  p = 0.014
```

A full 1 bit/word improvement in native-script quality buys only **0.14 bits/word** on Romanized. 86% of native-script quality variation is lost in the script change.Because models lack Romanized Sinhala in pretraining, their performance is bounded by generic Latin-character statistics rather than true language comprehension.

---

## Test 7 — Cross-Script Rank Correlations

### Intended Purpose
Determine: (a) whether model rankings on Unicode are preserved under Romanization; (b) whether the BPW gap between scripts is predictable from the Unicode BPW level; (c) how Mixed-script compares to both.

### How It Is Done
Pairwise Spearman rho across all relevant combinations of Unicode BPB/BPW, Romanized BPB/BPW, Mixed BPB, and the BPW gap (d_bpw = BPW_R − BPW_U).

### Result
| Pair | rho | p-value | Interpretation |
|------|-----|---------|----------------|
| Unicode BPB vs. Romanized BPB | +0.411 | 0.022 | Weak rank preservation |
| Unicode BPB vs. Mixed BPB | **+0.938** | 7.2 × 10⁻¹⁵ | Mixed ≈ mild perturbation of native |
| Unicode BPW vs. d_bpw | **–0.876** | 1.1 × 10⁻¹⁰ | Better natively → larger gap |

The better a model is at native Sinhala, the larger its BPW gap will be when switched to Romanized. Mixed-script behaves almost identically to Unicode; fully Romanized is a fundamentally different regime.

---

## Test 8 — Per-Sentence Paired Wilcoxon Test on BPW

### Intended Purpose
Confirm the BPW ordering at the individual sentence level (not just corpus-pooled), and determine for how many models Romanization is statistically significantly worse on a per-sentence basis.

### How It Is Done
For each of the 31 checkpoints, a **paired Wilcoxon signed-rank test** on the 500 per-sentence BPW values tests H0: median(BPW_R_i − BPW_U_i) = 0. This is non-parametric and does not assume normality of the differences.

### Result
- **31 of 31** models: Wilcoxon p < 0.05 (all significant at the sentence level)
- **19 of 31** models: median per-sentence BPW is *worse* on Romanized
- **12 of 31** models: median per-sentence BPW is *better* on Romanized
- Median fraction of sentences that are worse: **59.4%**

---

## Test 9 — N-Gram Reference Baseline

### Intended Purpose
Give an absolute calibration of how much LLMs know about Sinhala in each script by comparing them to a trivial baseline with no neural parameters and no world knowledge — only character co-occurrence statistics from the same 500 sentences.

### How It Is Done
Add-alpha character n-gram models (orders 0–5, i.e., 1-gram to 6-gram) are trained using **5-fold cross-validation** — each fold of 100 sentences is scored using a model trained on the other 400 sentences only. No data leakage. BPB is computed from bits per character using the corpus bytes/character ratio. The count of LLMs achieving lower BPB than each n-gram model is tallied.

### Result — Romanized Sinhala

| Model | BPB | LLMs beaten |
|-------|-----|-------------|
| Character 1-gram | 3.977 | 24 |
| Character 2-gram (bigram) | **3.063** | **0** |
| Character 4-gram (best n-gram) | **2.636** | **0** |
| Best LLM (Qwen3.5-9B-Base) | 3.290 | — |
| Median LLM | 3.805 | — |

**Not one of 31 LLMs beats a character bigram on Romanized Sinhala.** Models know Sinhala through its script, not through its language.

### Result — Native Unicode

| Model | BPB | LLMs beaten |
|-------|-----|-------------|
| Character 3-gram (best n-gram) | **1.162** | **1** |
| Best LLM (Llama-3.1-8B) | 1.148 | — |

On native Sinhala, one LLM (Llama-3.1-8B) beats the trigram — a normal result for a model with Sinhala training data.

---

# Part 2 — Downstream (Extrinsic) Tests

> Source: [`stats_extrinsic.py`](../../paper/analysis/stats_extrinsic.py), 10 instruction-tuned checkpoints, 3 tasks, 9,479 items.

---

## Setup — Competence Screen (Poisson-Binomial Test)

### Intended Purpose
Models at chance level natively cannot lose anything from script change — a zero gap for a guessing model is not evidence that Romanization is harmless, it is evidence that the model is useless for that task. Including such models would dilute the true magnitude of the effect. The screen identifies genuine native-script signal before measuring degradation.

### How It Is Done
A **one-sided normal approximation to the Poisson-Binomial null** is used. SinhalaMMLU has 2,139 five-option items (chance = 0.20) and 4,740 four-option items (chance = 0.25), so guessing is not a simple Binomial.

```
mu = sum(p_i),   sigma = sqrt(sum(p_i * (1 - p_i))),   Z = (k - mu) / sigma
p = P(Z_standard_normal > Z)   [one-sided]
```

A model is **competent** if: (1) p < 0.01, AND (2) it does not put >90% of answers on a single option (no mode collapse).

### Result
| Task | Competent Models | Count |
|------|-----------------|-------|
| SinhalaMMLU | Qwen3.5-9B, Qwen3.5-4B, Llama-3.1-8B-Instruct, Qwen2-7B-Instruct, Hormoz-8B | **5 of 10** |
| SOLD | Qwen3.5-9B, Qwen3.5-4B, Llama-3.1-8B-Instruct, Qwen2-7B-Instruct | **4 of 10** |
| Global PIQA | — | **0 of 10** |

---

## Test 10 — McNemar's Paired Significance Test

### Intended Purpose
Determine whether each model's accuracy drop from Unicode to Romanized is **statistically significant** on the same items — ruling out random variation. A standard two-sample test would ignore the paired nature of the data (same items scored twice).

### How It Is Done
For each model × task, build a 2×2 contingency table from item-level binary outcomes:

```
                  Romanized Correct   Romanized Wrong
Unicode Correct        a (both)          b (only U)
Unicode Wrong          c (only R)        d (both wrong)
```

McNemar's test uses only the **discordant pairs** b and c:
- If b + c < 25: **exact binomial test** (p = 2 * min[P(X >= b), P(X <= b)] where X ~ Binomial(b+c, 0.5))
- If b + c >= 25: **continuity-corrected chi-squared** = (|b−c|−1)² / (b+c)

The gap (U% − R%) is reported with a **10,000-resample paired bootstrap 95% CI** (resample item pairs with replacement, recompute gap).

### Result — SinhalaMMLU
| Model | U% | R% | Gap | 95% CI | b | c | p_raw |
|-------|----|----|-----|--------|---|---|-------|
| Qwen3.5-9B | 44.1 | 28.7 | +15.5 | [14.0, 16.9] | 1892 | 828 | < 0.0001 |
| Qwen3.5-4B | 36.7 | 26.1 | +10.6 | [9.3, 12.0] | 1572 | 840 | < 0.0001 |
| Llama-3.1-8B-Instruct | 32.5 | 27.1 | +5.4 | [4.1, 6.7] | 1244 | 872 | < 0.0001 |
| Qwen2-7B-Instruct | 29.0 | 27.0 | +2.0 | [0.8, 3.2] | 901 | 763 | 0.0009 |
| Hormoz-8B | 26.0 | 25.2 | +0.8 | [−0.5, 2.0] | 964 | 912 | 0.14 |

---

## Test 11 — Holm-Bonferroni FWER Correction

### Intended Purpose
When testing 10 models on the same task, the probability of at least one spurious significant result grows with the number of tests. Holm correction controls the **Family-Wise Error Rate (FWER)** at alpha = 0.05, while being less conservative than Bonferroni.

### How It Is Done
Within each dataset, sort raw p-values ascending: p_(1) <= p_(2) <= ... <= p_(m) where m = 10. The adjusted p-value for rank i is:

```
p_Holm_(i) = min(1, max over j<=i of [(m - j + 1) * p_(j)])
```

The monotonicity constraint (running max) ensures the adjusted sequence is non-decreasing. Significant if p_Holm < 0.05.

### Result — SinhalaMMLU Competent Cohort
| Model | p_Holm | Significant |
|-------|--------|------------|
| Qwen3.5-9B | < 0.0001 | Yes |
| Qwen3.5-4B | < 0.0001 | Yes |
| Llama-3.1-8B-Instruct | < 0.0001 | Yes |
| Qwen2-7B-Instruct | 0.0047 | Yes |
| Hormoz-8B | 0.8273 | No |

4 of 5 competent models lose significantly. Hormoz-8B's result is not significant — it was only 2.5 points above chance to begin with.

---

## Test 12 — Pooled Cohort McNemar Test

### Intended Purpose
Combine all items from all competent models into one large paired test to get a single high-power estimate of the average script gap across the cohort with a narrow confidence interval.

### How It Is Done
Concatenate item-level outcomes from all 5 competent checkpoints × 6,879 items = **34,395 paired observations**. Apply the same McNemar procedure as Test 10 on this pooled set (continuity-corrected chi-squared, paired bootstrap CI).

### Result — SinhalaMMLU
```
Gap = 6.9 pp   (95% CI [6.3, 7.5]),   n = 34,395 paired observations
```

---

## Test 13 — Item-Clustered Logistic Regression (Script Main Effect)

### Intended Purpose
Test the script effect while controlling for: (a) model-level heterogeneity (different base accuracy rates per checkpoint), and (b) the repeated-measures structure (same item scored by multiple models). A clustered GLM accounts for within-item correlation that inflates standard errors if ignored.

### How It Is Done
Data is reshaped to long format: one row per (model, item, script), `correct` as binary outcome. Formula:
```
correct ~ C(script) * C(difficulty) + C(model)
```
Binomial logit GLM with **cluster-robust (sandwich) standard errors** grouped by item `id`. The coefficient on `C(script)[T.romanized]` gives the log-odds change from Unicode to Romanized (model fixed effects absorbed). Odds ratio = exp(coef).

### Result
```
Odds Ratio = exp(-0.390) = 0.677,   p = 1.4 × 10^-34
```

For a randomly selected item, the odds of answering correctly drop to 67.7% of their native-script level when the question is Romanized. This is robust to model-level differences and item-level clustering.

---

## Test 14 — Script × Difficulty Interaction Test

### Intended Purpose
Test whether the script penalty is **smaller on hard items** than easy ones. The floor-effect hypothesis predicts: models are near chance on Hard items in both scripts, so there is little room to lose — the Romanization penalty should shrink significantly for Hard vs. Easy items.

### How It Is Done
Same item-clustered logistic GLM as Test 13 with the full interaction term. The key coefficient is `C(script)[T.romanized]:C(difficulty)[T.Hard]` which tests whether the Romanized penalty shrinks for Hard vs. Easy items (reference level).

### Result
| Interaction Term | Coef | p-value |
|-----------------|------|---------|
| Romanized × Medium (vs. Easy) | +0.057 | 0.169 (n.s.) |
| **Romanized × Hard (vs. Easy)** | **+0.114** | **0.007** |

Hard items are significantly less penalized by Romanization (p = 0.007). The positive coefficient means the log-odds Romanization penalty is 0.114 smaller on Hard items than Easy items — confirming the floor effect at item level.

---

## Test 15 — MMLU Difficulty and Domain Stratification

### Intended Purpose
Break down where the script effect is concentrated to understand the pattern structurally and reveal which benchmark slices are most vs. least sensitive to script variation.

### How It Is Done
Group competent-cohort items by (1) difficulty {Easy, Medium, Hard} and (2) domain {Social Science, Humanities, STEM, Business Studies, Language, Other}. For each stratum, run McNemar's test on pooled observations across models, with Holm correction across strata.

### Result — By Difficulty
| Difficulty | Items | U% | R% | Gap | 95% CI |
|------------|-------|----|----|-----|--------|
| Easy | 1,851 | 37.7 | 29.1 | **8.6 pp** | [7.4, 9.7] |
| Medium | 2,503 | 35.9 | 28.7 | **7.2 pp** | [6.2, 8.2] |
| Hard | 2,525 | 28.5 | 23.2 | **5.2 pp** | [4.3, 6.1] |

### Result — By Domain
| Domain | Items | U% | R% | Gap |
|--------|-------|----|----|-----|
| Social Science | 1,059 | 38.5 | 26.7 | **11.8 pp** |
| Business Studies | 463 | 35.2 | 27.1 | 8.0 pp |
| STEM | 614 | 34.2 | 26.2 | 8.0 pp |
| Other | 1,014 | 32.5 | 24.5 | 8.0 pp |
| **Humanities** | **3,341** | 32.7 | 27.9 | **4.8 pp** |
| Language | 388 | 29.4 | 24.7 | 4.7 pp |

Pattern: where native accuracy is highest (Social Science, Easy items), there is the most headroom to lose — so the gap is largest. The hardest and most-underserved strata reveal the smallest script effects, which is a trap for benchmark designers.

---

## Test 16 — Floor-Effect Scaling Law (Model Level)

### Intended Purpose
Test whether the script gap is *proportional* to native-script headroom above chance — the core theoretical claim of the paper. If R² ≈ 1, knowing a model's native accuracy completely determines how much it will lose under Romanization.

### How It Is Done
Headroom = native accuracy − chance level (23.4% for SinhalaMMLU). OLS regression across the 9 parseable checkpoints:
```
gap = beta * headroom + alpha
```

### Result
```
gap = 0.778 * headroom − 0.875
R² = 0.967,   p = 1.9 × 10⁻⁶,   n = 9
```

Romanization removes ~78% of whatever native-script advantage a checkpoint had. The fit is nearly perfect across 9 very different models spanning 1.1B to 9B parameters and 5 architecture families.

---

## Test 17 — Floor-Effect Scaling Law (Cell Level — Independent Replication)

### Intended Purpose
Replicate the model-level floor law *independently* using items as the unit of analysis. The 16 non-empty domain × difficulty cells provide a completely separate data source with larger n, confirming the structural relationship is not an artifact of the small (n = 9) model sample.

### How It Is Done
For each of the 16 cells, compute headroom = U_accuracy − 23.4% chance, and gap = U_accuracy − R_accuracy. Fit OLS and Spearman rho on these 16 (headroom, gap) pairs.

### Result
```
gap = 0.576 * headroom + 1.553
R² = 0.829,   p = 9.8 × 10⁻⁷,   Spearman rho = 0.85,   n = 16
```

The slope differs from the model-level law (0.58 vs. 0.78) because cells within a single model share that model's quality. But the direction, significance, and R² = 0.83 are fully consistent — two independent decompositions agree.

---

## Test 18 — Flattening Regression (Romanized vs. Unicode Accuracy)

### Intended Purpose
Directly measure how much native-script accuracy variation "survives" when models switch to Romanized. Slope = 1 means full preservation; slope near 0 means Romanization erases all model differentiation.

### How It Is Done
OLS regression of R accuracy on U accuracy across the 9 parseable checkpoints. Bootstrap CI on slope: 5,000 resamples.

### Result
```
acc_R = 0.222 * acc_U + 19.1
slope = 0.222   (95% CI [0.121, 0.543]),   R² = 0.706,   p = 0.005
```

Only 22% of native-script accuracy differences are preserved under Romanization. A checkpoint 10 pp better on native Sinhala will be only ~2.2 pp better on Romanized.

---

## Test 19 — SOLD: MCC Bootstrap with Holm Correction

### Intended Purpose
On an imbalanced binary classification task (40.6% positive class), accuracy can remain nearly unchanged while the model's discriminatory ability collapses. Matthews Correlation Coefficient (MCC) is the appropriate metric. The test checks whether the MCC drop is statistically significant and practically meaningful.

### How It Is Done
For each checkpoint, compute MCC_U and MCC_R. Invalid/unparseable predictions are counted as the wrong class (worst-case treatment). Delta_MCC = MCC_U − MCC_R is estimated with a **10,000-resample paired item bootstrap** using vectorized weight matrices. Two-sided empirical p = 2 * min(mean(Delta <= 0), mean(Delta >= 0)). Holm correction applied across the 5 real-signal models.

### Result — Models with Real Native-Script Signal (MCC > 0.10)
| Model | MCC_U | MCC_R | Retained | p_Holm |
|-------|-------|-------|----------|--------|
| Qwen3.5-9B | 0.280 | 0.069 | **24%** | < 0.0001 |
| Qwen2-7B-Instruct | 0.148 | 0.042 | **29%** | < 0.0001 |
| Llama-3.1-8B-Instruct | 0.259 | 0.105 | **40%** | < 0.0001 |
| Hormoz-8B | 0.108 | 0.090 | 83% | 1.0 (n.s.) |
| Qwen3.5-4B | 0.219 | 0.127 | 58% | 0.0014 |

**4 of 5 models lose significantly.** Median retention: **40%**. Meanwhile accuracy changes by only 1.6–11.3 points — a system monitoring accuracy would see little alarm while over half the signal disappeared.

---

## Test 20 — SOLD: Offensive Prediction Rate (Mechanism)

### Intended Purpose
Explain *mechanistically* how MCC drops without large accuracy changes. The hypothesis: under Romanization, models retreat to predicting one class more heavily — uninformative for binary classification — rather than reading and processing the actual text.

### How It Is Done
For each model, compute the fraction of predictions labeled "OFF" (offensive) under each script condition. A large shift without a corresponding accuracy improvement indicates class-prior defaulting rather than text understanding.

### Result
| Model | OFF rate (Unicode) | OFF rate (Romanized) |
|-------|--------------------|---------------------|
| Qwen2-7B-Instruct | 10.5% | **23.4%** (+12.9 pp) |
| Hormoz-8B | 9.8% | **20.7%** (+10.9 pp) |
| Qwen3.5-9B | 52.3% | 57.1% (+4.8 pp) |
| Llama-3.1-8B-Instruct | 21.5% | 20.7% (−0.8 pp) |

Qwen2-7B-Instruct more than doubles its "offensive" prediction rate with no accuracy gain — it has stopped reading the text and is defaulting to a label prior.

---

## Test 21 — Global PIQA: Sign Test for Direction Consistency

### Intended Purpose
With only 100 items, no individual comparison can be significant. The sign test checks whether the *direction* of the effect is consistent across the 9 parseable checkpoints, even if no individual result reaches significance. This distinguishes a powered null (effect exists but dataset is too small to detect it) from evidence of no effect.

### How It Is Done
Count n_+ = checkpoints where gap > 0 (Romanized worse) and n_- = checkpoints where gap < 0. Under H0 (no consistent direction), outcomes follow Binomial(n_+ + n_-, 0.5). p = 2 × P(X >= n_+).

### Result
```
n_+ = 7,   n_- = 2,   p = 0.180
Pooled gap = 4.6 pp,   p = 0.10
```

7 of 9 checkpoints show worse Romanized accuracy, directionally consistent with MMLU and SOLD, but the sign test does not reject the null (p = 0.18). This is treated as a powered null — the 100-item set cannot detect effects of the size seen on MMLU, not evidence the effect does not exist.

---

## Test 22 — Token Fragmentation Control (Confound Elimination)

### Intended Purpose
Rule out the explanation that Romanized prompts are longer in tokens, giving models more input to process and causing worse performance through context complexity or attention dilution — not through script knowledge gaps.

### How It Is Done
Compute token ratio tau = tokens_romanized / tokens_unicode for each model on each task. Additionally, split MMLU items into terciles by tau and compare the script gap across terciles to test for monotone relationship.

### Result — Token Ratio
| Task | Median tau | Min tau | All 10 models shorter? |
|------|-----------|---------|------------------------|
| SinhalaMMLU | **0.48** | 0.31 | **Yes (10/10)** |
| SOLD | 0.54 | 0.34 | Yes (10/10) |
| Global PIQA | 0.50 | 0.31 | Yes (10/10) |

Romanized prompts are **shorter** in every single model × task combination. The token-length hypothesis predicts longer = worse; we observe shorter = worse. The confound hypothesis is falsified.

### Result — Gap by Token Tercile (MMLU)
| Tercile | Mean tau | Gap |
|---------|---------|-----|
| Low | 0.53 | 5.9 pp |
| Mid | 0.60 | 7.5 pp |
| High | 0.68 | 7.2 pp |

No monotone pattern — the gap does not grow with token ratio.

---

## Test 23 — Answer Concentration Control (Degeneration Elimination)

### Intended Purpose
Rule out the explanation that low Romanized accuracy is caused by models degenerating to always outputting the same option (e.g., always "1") — which would appear as near-chance accuracy even though the model is not actually processing text.

### How It Is Done
For each competent model and script condition, compute **top-option share** = fraction of valid responses choosing the most frequent option. A paired Wilcoxon signed-rank test compares top-option share between scripts across the 5 competent models.

### Result
| Condition | Mean Top-Option Share |
|-----------|----------------------|
| Unicode | **37.0%** |
| Romanized | **38.6%** |
| Wilcoxon p | **0.63** (n.s.) |

Top-option shares are statistically indistinguishable. Models continue distributing answers across all options under Romanization. The invalid rate (unparseable responses) stays ≤ 0.03% in both conditions. Models are not collapsing — they are simply wrong.

---

## Test 24 — Intrinsic-to-Downstream Linkage

### Intended Purpose
Determine whether a cheap intrinsic measurement (BPB on 500 sentences, ~10 minutes per model) can *predict* which models will suffer most on expensive downstream evaluations (9,479 items per task) — and critically, which intrinsic quantities are predictive vs. which are misleading.

### How It Is Done
For the 9 checkpoints measured both ways (LaMini excluded for format failure), compute Spearman rho between each intrinsic quantity and each downstream outcome. Nine intrinsic predictors × two downstream outcomes = 18 correlation tests.

### Result
| Intrinsic Predictor | MMLU Gap rho | p | SOLD Delta-MCC rho | p |
|--------------------|-------------|---|-------------------|---|
| **Unicode BPB (level)** | **−0.900** | **0.0009** | **−0.817** | **0.007** |
| Romanized BPB (level) | −0.850 | 0.004 | −0.917 | 0.001 |
| BPB Gap (Rom.−Uni.) | −0.067 | 0.865 | −0.400 | 0.286 |
| Unicode BPW (level) | −0.900 | 0.0009 | −0.817 | 0.007 |
| Perplexity ratio | −0.533 | 0.139 | −0.417 | 0.265 |
| Parameter count | +0.653 | 0.057 | +0.494 | 0.177 |

**The floor effect from the intrinsic side:** lower native BPB (better native ability) = worse downstream performance on Romanized input, because the model has more to lose. The BPB *gap* — the quantity most previous work reports as the measure of "script robustness" — predicts nothing (rho = −0.07, p = 0.86). The perplexity ratio (the widely-cited "312-fold degradation") also predicts nothing (rho = −0.53, p = 0.14). **The wrong quantity is being widely reported.**

---

## Summary Table — All 24 Tests

| # | Test | Statistic | Key Result |
|---|------|-----------|------------|
| 1 | Reproduction check | % deviation | Median < 0.05% — confirmed |
| 2 | PPL vs. BPB rank correlation | Spearman rho | rho = 0.08, p = 0.68 — uncorrelated |
| 3 | Fertility vs. PPL | Spearman rho | rho = −0.87, p < 10⁻⁹ — fully explains PPL |
| 4 | Scale vs. quality | Spearman rho | Unicode BPB: rho = −0.55, p = 0.001 |
| 5 | Flattening spread | Max − Min BPW | 17.7 bits → 5.4 bits |
| 6 | Carryover regression | OLS beta | beta = 0.14, CI [0.05, 0.25], R² = 0.19 |
| 7 | Cross-script rank correlation | Spearman rho | BPW gap vs. native: rho = −0.88 |
| 8 | Per-sentence Wilcoxon | Signed-rank | All 31 models significant |
| 9 | N-gram vs. LLM | BPB comparison | 0/31 LLMs beat bigram on Romanized |
| 10 | McNemar's paired test | chi2 / exact | Qwen3.5-9B: 15.5 pp, p < 0.0001 |
| 11 | Holm FWER correction | Step-down p | 4/5 competent models significant |
| 12 | Pooled cohort test | McNemar's | 6.9 pp, CI [6.3, 7.5], n = 34,395 |
| 13 | Clustered logistic GLM | Logit OR | OR = 0.677, p < 10⁻³⁰ |
| 14 | Script × difficulty GLM | Interaction coef | Hard × Romanized: p = 0.007 |
| 15 | Strata breakdown | McNemar's per cell | Easy: 8.6 pp, Hard: 5.2 pp |
| 16 | Floor law (model level) | OLS R² | R² = 0.97, slope = 0.78 |
| 17 | Floor law (cell level) | OLS + Spearman | R² = 0.83, rho = 0.85, n = 16 |
| 18 | Flattening regression | OLS beta | beta = 0.22, 78% of variation lost |
| 19 | SOLD MCC bootstrap | Bootstrap + Holm | Median 40% retained; 4/5 significant |
| 20 | OFF-rate shift | Proportion | Qwen2-7B: 10.5% → 23.4% |
| 21 | PIQA sign test | Binomial | 7/9 negative direction; p = 0.18 (n.s.) |
| 22 | Token length control | Ratio + terciles | All tau < 1; no monotone tercile pattern |
| 23 | Answer concentration | Top-share + Wilcoxon | 37.0% vs. 38.6%; p = 0.63 (n.s.) |
| 24 | Intrinsic–downstream linkage | Spearman rho | Native BPB: rho = −0.90; gap: rho = −0.07 |
