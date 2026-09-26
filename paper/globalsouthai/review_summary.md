# Review Summary — GlobalSouthAI @ NeurIPS 2026

Paper: *Romanization Flattens the Field: Script and Metric Sensitivity in Sinhala SLM Evaluation*
Decision: **Accept** (non-archival workshop track). Three official reviews.

Reviewers, as referenced below:
R1 = sWb117, rating 8 (top 50% of accepted papers, clear accept), confidence 4
R2 = ghL415, rating 7 (good paper, accept), confidence 4
R3 = fYs913, rating 7 (good paper, accept), confidence 4

## Overall

* All three recommend acceptance. No reviewer makes a new experiment a condition of acceptance; R1 states explicitly that its main concerns are about how the result is stated rather than whether it holds, and that the key items are camera-ready edits.
* R1 names the framing as the real contribution and warns we undersell it: the argument is not that Sinhala models are bad on Romanized input, it is that a deployment metric can be chosen such that a complete loss of discriminative power is invisible. A moderation system validated on Sinhala-script text and serving Singlish users would show a five point accuracy wobble while over half the usable signal is gone. R1 considers this to generalize well past Sinhala and past this workshop.
* R1 credits unusual methodological care: the paired item-level design, the competence screen, leading with Matthews correlation on a class-imbalanced task, and reporting a control that cuts against our own convenience (Table 16, showing our transliterated text is 0.17-0.24 bits per byte harder than what native speakers typed).
* R1 verified the internal arithmetic and says the consistency made the paper much easier to check: 6,879 + 2,500 + 100 = 9,479, times eleven checkpoints times two conditions = 208,538, and pooled n = 41,274 is 6,879 across six competent checkpoints.
* R2 credits good statistical hygiene in several places: paired tests, Holm correction, paired bootstrap intervals, explicit baselines, invalid-output accounting, leave-one-out sensitivity checks.
* R2 and R3 both call the limitations section unusually candid.
* R1 asks that the ethics and licensing sections be kept in the camera-ready, including the decision not to redistribute the Romanized SinhalaMMLU adaptation under its no-derivatives clause.
* R3 finds the paper clear, relevant and technically interesting, and the main message useful for multilingual and low-resource evaluation: the choice of script and metric strongly affects the conclusions drawn about model quality.

## Abstract and Introduction

* The "exactly in two" framing invites arithmetic that does not hold, raised independently by R1 and R2. The abstract splits the 312-fold ratio into a factor of 21 and a factor of 24; a reader multiplies those and gets 504, not 312. Equation 1 is exact per checkpoint, but the two quoted factors are medians of two separate distributions, and medians do not compose.
* R2 works it through from Table 4: median total 8.29 bits (about 313x), median normalization 4.37 (about 20.7x), median per-byte 4.555 (about 23.5x), but 4.37 + 4.555 = 8.925, not 8.29. R2 calls the correction **required** in the abstract, introduction, Section 3 and the conclusions.
* R2 supplies the repair: aggregate in log space using arithmetic means, giving 14.8 x 22.7 = 335.8 exactly, or decompose a single specified representative checkpoint. R1 suggests instead stating the normalizer's median share of the total, which the appendix already computes as 39%, and reserving the two factors for a sentence that makes clear they are marginal medians.
* R1 notes this is the single most quotable sentence in the paper and the one most likely to be quoted wrongly.
* The abstract leads with the weaker of the two flattening estimates, raised by R1 and R3. We report 0.22 across 10 checkpoints and 0.45 across 16 benchmark cells (item-weighted 0.476), and lead with the checkpoint-level number, which is the more dramatic but rests on n = 10 heterogeneous checkpoints differing in family, tokenizer, corpus and instruction tuning at once. The cell-level fit has four times the units and no checkpoint confound. R1 asks for both in the abstract, or for the cell-level one to lead, and says this as someone persuaded by the finding: the conservative estimate is strong enough and leading with it removes the easiest objection.
* R2 and R3 ask that the title, abstract and novelty claims state consistently that the large downstream evaluation uses automatically Romanized inputs.
* R3 asks that the scaling conclusion be stated carefully: we correctly note the relationship is an association rather than a controlled experiment, but the title and main claims could still be read as a general scaling law.

## Existing Works

* No reviewer asked for additional related work, and none flagged a missing line of literature.
* R2 finds the relation to prior work useful, specifically that we distinguish our zero-shot diagnosis from adaptation approaches such as RomanSetu, where training on Romanized text can improve multilingual performance, and that we relate the result appropriately to real-world clinical findings across Indian languages.
* R2 independently confirmed the prior Sinhala benchmark does report a greater-than-300x Romanization gap and no model-size correlation.
* R3 notes the comparison with results from other South Asian languages is suggestive but not a direct validation of generalization.

## Methodology and Setup

* "Real per-byte loss" is too strong (R2). Bits per byte is tokenizer-independent but not representation- or encoding-independent across scripts: Sinhala characters occupy more UTF-8 bytes than Latin characters, so changing the script changes what one byte represents. R2 recommends making the change in bits per whitespace word the principal estimate of genuine cross-script degradation, since word counts are identical, and presenting the bits-per-byte decomposition as one accounting under UTF-8 rather than a unique division between artifact and real loss. R2 is explicit that this does not invalidate the main conclusion, only the precise 21x/24x attribution.
* The downstream Romanized condition is synthetic, raised by all three. It relies on deterministic transliteration rather than naturally typed Singlish, so the central downstream gaps are best understood as approximate upper bounds. R3 adds that automatic romanization may still differ from real user input in spelling variation, abbreviation, code-mixing, punctuation and ambiguity. All three ask for a human-Romanized subset of even a few hundred SinhalaMMLU or SOLD items, ideally with multiple native speakers; R1 calls that a modest amount of annotation for how much it would settle, and notes it would convert our largest limitation into a measurement.
* The transliteration control is measured where the claim is not made (R1, R2). Table 16 is the right experiment, but it runs on 6 of 31 checkpoints, all below 3.2B parameters, and none of the six passes the competence screen, so the strongest caveat in the paper is bounded only on models excluded from the headline downstream result.
* Table 17's attestation terciles help (Spearman 0.02, with the low-attestation tercile losing least) and R1 finds that argument more convincing than the bits-per-byte bound, but considers it indirect.
* Transliterator validation needs a clearer independence statement (R2). We call all 755,000 validation items "human-Romanized references" although roughly 300,000 are machine-augmented, and that wording should be corrected. R2 also asks whether the conversion rules or convention choices were developed using any of the Swa-bhasha evaluation resources, and states that a held-out split would be needed if so.
* Lexicon attestation demonstrates plausibility but is not equivalent to naturalness, particularly when the deterministic system scores as more lexicon-attested than the humans themselves (R2).
* R3 adds that character error rate, chrF and exact match do not establish that the generated Romanized text preserves the same meaning or difficulty as naturally typed Romanized Sinhala, and asks for a human evaluation of semantic equivalence and naturalness.
* No sensitivity analysis on the competence screen (R1). The screen is well motivated and the LaMini and TinyLlama cases in Table 7 show why it is needed, but the headline numbers, the pooled 6.0 point gap and the 22.4 to 6.7 compression, depend on which six of eleven checkpoints pass, and the screen has two free parameters: p < 0.01 against the Poisson-binomial null and the 90% single-option rule, neither justified against alternatives. R1 asks for a short sweep at p < 0.05 and p < 0.001 and at 80% and 95% degeneracy, costing a paragraph, to preempt the reading that the screen was tuned.
* Cohorts and inferential targets are inconsistent (R2). The competence-screened results use six models whereas the headline flattening regression uses ten parseable models, and this should be justified more clearly. R2 reconstructs the slope for the six competent models as approximately 0.12 rather than 0.22, notes the conclusion therefore appears to strengthen, but says readers should not have to work that out themselves.
* Model-level significance tests should acknowledge that checkpoints from related families are not independent (R2), with a sensitivity analysis using one checkpoint per family, or clustering by family or tokenizer.
* The prompt-template decision is reasonable but not fully convincing (R3). One template across all datasets avoids script-specific prompting differences, but the pilot shows noticeable differences between templates, especially for SOLD and Global PIQA, and a sensitivity analysis under alternative reasonable templates would be useful.
* The downstream model set is small and heterogeneous (R3). Eleven checkpoints spanning different families, training data, tokenizers and instruction-tuning procedures make it difficult to separate the effects of size, architecture, tokenizer, pretraining data and instruction tuning.
* The study is limited to one language (R3). Sinhala is a valuable case study but it is hard to know whether the flattening effect generalizes to other scripts, languages or Romanized registers.

## Results

* R2 finds the flattening result insightful: showing that strong formal-script models lose more, and that native-script rankings transfer poorly, is more informative than reporting only an average degradation.
* R2 and R3 both single out the safety-metric result as valuable. R3 calls the SOLD contrast particularly interesting, with accuracy changing only slightly while Matthews correlation drops substantially, and agrees it supports the argument that accuracy can hide important degradation under class imbalance.
* R1 asks how answers are extracted on SOLD, whether by pattern match from free generation, and how the rare unparseable outputs are scored in the Matthews correlation.
* The Global PIQA results are difficult to interpret (R3). No evaluated checkpoint passes the competence screen on Global PIQA, so no strong conclusion about script degradation is possible there. This is acknowledged in the paper, but R3 asks that the task's role in the overall downstream evidence be explained more clearly.
* Some conclusions rely on exploratory correlations (R3). The intrinsic-to-downstream correlations use only ten heterogeneous checkpoints with no held-out validation or preregistration. Labelling the analysis exploratory is appropriate, but the discussion should avoid giving these correlations too much weight.
* R3 asks for more detailed per-category and per-difficulty results for SOLD and SinhalaMMLU, especially for cases where accuracy remains stable but Matthews correlation drops.
* Figure 1 is doing heavy work for a four page body (R1). Panel (c) is where the two slopes first appear and the legend is the only place the difference is visible at a glance; R1 suggests annotating the two fits directly.
* Table 5 is dense enough that the reordering point, Gemma-2-9B second by bits per byte and 26th by perplexity, could be pulled into a two-row callout (R1).

## Conclusion and Implications

* R1 considers the five practices in Section 5 worth publishing because they are not generic advice: each is traceable to a specific measurement in the paper, which is what makes them suitable for a venue concerned with evaluation under real deployment conditions.
* R3 calls the practical recommendations clear, easy to understand and potentially useful for future low-resource language benchmarks.
* R3 asks that the generalization claims be moderated slightly and the limitations of synthetic romanization be made more prominent.
* R1 asks whether we expect the flattening slope to be steeper or shallower for frontier proprietary models, given that they start with more Sinhala-script headroom.
* R1 asks whether the checkpoint-level slope of 0.22 moves toward the cell-level 0.45 if checkpoints are weighted by item count, or if the two most extreme checkpoints are dropped.
* R1 asks, given that 44.6% of our forms match human spellings exactly and a further 27.6% match after normalizing the long-vowel convention, whether we can separate how much of the Romanized penalty is orthographic mismatch from how much is register unfamiliarity.
* R3 asks how stable the main findings are across different prompt templates, decoding settings and answer-extraction rules.

## Limitations

* R2 lists what the paper already acknowledges and credits it as unusually candid: synthetic romanization, contamination, family and size confounding, zero-shot evaluation, weak Global PIQA evidence, and the exploratory intrinsic-to-downstream association.
* R3 asks that the synthetic-romanization limitation be made more prominent, and notes that these limitations reduce the strength of the general claims without removing the value of the Sinhala case study.
* Mixed-script and code-mixed input could be better discussed (R3). The mixed-script results are treated briefly, but real users may combine Sinhala script, Romanized Sinhala, English, emoji, numbers and informal spelling in a single message, which R3 considers an important next step for deployment-oriented evaluation.
* The paper could compare against more baselines (R3): a transliteration-to-Sinhala preprocessing baseline, a model evaluated after script normalization, or models specifically adapted to Romanized Sinhala, which would separate the diagnostic finding from possible mitigation strategies.
* R3 asks whether a model trained or fine-tuned specifically on Romanized Sinhala would clarify whether the issue is mainly lack of exposure or a broader script-handling limitation, and whether the same trends would appear within a single model family where architecture and training data are more controlled.
* R3 asks how much of the flattening effect is explained by tokenizer fertility and how much remains after controlling for tokenizer characteristics.

## References

* No reviewer raised incomplete or inconsistent citations.

## Appendix

* R1 asks that the licensing appendix and its specific decisions be retained in the camera-ready, naming the choice not to redistribute the Romanized SinhalaMMLU adaptation under its no-derivatives clause.
* R1 treats Appendix Table 16 as the right experiment with the wrong coverage, and Table 17 as helpful but indirect; see Methodology above.
* No reviewer reported missing implementation details, hyperparameters or compute reporting.

## Priority, as the reviewers ranked it

* R1 separates its points explicitly. Camera-ready edits: the 21x/24x framing, leading with the conservative slope, and the presentation items on Figure 1 and Table 5. Would make the paper considerably harder to argue with if the timeline allows: extending the transliteration control to competent checkpoints, and the competence-screen sweep.
* R2 marks one item as required rather than suggested: correcting the aggregated decomposition in the abstract, introduction, Section 3 and conclusions.
* R3 identifies the synthetic transliteration of downstream data as the biggest limitation, and single-language scope as the second.
