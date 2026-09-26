# Review Summary — GlobalSouthAI Paper

**Paper:** *Romanization Flattens the Field: Script and Metric Sensitivity in Sinhala SLM Evaluation*  
**Decision:** Accept

The paper received three positive reviews. All reviewers recommended acceptance, and all agreed that the work is relevant, carefully conducted, and a good fit for the GlobalSouthAI workshop. Their comments are mainly suggestions for improving the presentation and clarifying the limitations before the camera-ready version.

## Overall

The reviewers liked the central message of the paper: Sinhala language models are usually evaluated using formal Sinhala script, even though many users type Sinhala using Roman letters. The paper shows that this difference can affect both model performance and the conclusions drawn from evaluation metrics.

The reviewers particularly appreciated:

* The paper addresses a practical problem that is often overlooked.
* The paired evaluation design makes the comparison between the two scripts easier to interpret.
* The paper checks the earlier 312-fold result before challenging its interpretation.
* The downstream experiments cover several datasets and many model generations.
* The competence screen avoids including models that cannot perform the original task at all.
* The use of Matthews correlation for the imbalanced offensive-language task is appropriate.
* The paper reports limitations openly, especially the fact that most downstream Romanized data was automatically transliterated.
* The recommendations in the final section are practical and connected to the experimental findings rather than being generic advice.
* The ethics, licensing and data-distribution discussion is unusually careful and should be retained.

One reviewer described the main contribution as showing that a metric can make a serious loss of useful model behaviour appear small. This was considered relevant not only to Sinhala, but also to other languages where people use Romanized or informal forms in everyday communication.

## Introduction

The reviewers identified two issues that should be corrected in the introduction and abstract.

* The paper currently describes the 312-fold result as splitting exactly into a factor of 21 and a factor of 24. These two values come from separate medians and do not multiply back to 312. The equation is correct for each individual checkpoint, but the two summary values should not be presented as an exact combined decomposition.
* The abstract should mention both flattening estimates, or lead with the more conservative estimate based on benchmark cells rather than only the checkpoint-level estimate.
* The abstract and introduction should clearly state that the large downstream Romanized evaluation uses automatically transliterated input, not naturally typed user messages.
* Claims about model scale should continue to be described as associations, not as a general scaling law, because the models differ in family, tokenizer, training data and instruction tuning.

## Related Work

The reviewers did not identify any major missing related-work section or citation problem.

They considered the connection to Romanization studies in other South Asian languages useful, especially the distinction between evaluating a model without adaptation and training a model specifically for Romanized input. The comparison with clinical systems evaluated on Romanized Indian-language input was also seen as a useful motivation.

The paper should keep this distinction clear: the current work studies what general-purpose models do without additional training, not what a model could achieve after being adapted to Romanized Sinhala.

## Methodology and Data

The main methodological concern is the synthetic nature of the downstream Romanized data.

The reviewers understand why automatic transliteration was necessary: there is no large parallel dataset of naturally typed Romanized Sinhala for these tasks. However, automatically generated text may not fully reflect real user writing, including spelling variation, abbreviations, code-mixing, punctuation and informal conventions.

The reviewers suggested collecting and evaluating a smaller human-written subset in the future. Even a few hundred items, especially if written or checked by multiple native speakers, would make the downstream conclusion stronger. This was considered useful future work, but not a reason to reject the paper.

The transliterator evaluation was considered helpful, but the wording should be more precise:

* Not all of the validation material was written by humans; part of it was machine-augmented.
* Lexicon attestation shows that the spellings are used by people, but it does not prove that the generated sentences are fully natural.
* The paper should explicitly state that the transliteration rules were developed independently of the reference data used for evaluation.
* The existing control comparing automatically transliterated text with human-typed text should be explained more clearly, including why it covers only smaller checkpoints.

The reviewers also requested more explanation of the competence screen. In particular, they suggested checking whether the results change when the significance and output-concentration thresholds are made more or less strict. This is a relatively small analysis and can be performed using the existing saved results without running the models again.

Another issue is that different parts of the paper use different model groups. The SinhalaMMLU results use six competent models, the SOLD results use five, and the checkpoint-level flattening analysis uses ten parseable models. These groups should be named clearly whenever they are mentioned so that readers do not assume they are the same.

## Results

The reviewers considered the main results strong and interesting.

The most important finding is that Romanization does not simply reduce every model’s performance by the same amount. Instead, it compresses the differences between models: stronger models lose more of their advantage, while weaker models have less room to fall.

The SOLD result was especially well received. Accuracy changes only modestly because the dataset is imbalanced, but Matthews correlation shows that much more of the useful classification signal has been lost. The reviewers saw this as a practical warning for safety and moderation systems that rely on accuracy alone.

The following clarifications were requested:

* Explain exactly how answers are extracted from free-form generations.
* State how unparseable answers are scored, especially for Matthews correlation.
* Explain more clearly that Global PIQA is underpowered for this study because none of the models passes the competence screen there.
* Keep the intrinsic-to-downstream correlations clearly labelled as exploratory because they use a small and heterogeneous model set.
* Consider adding direct labels to the two flattening lines in Figure 1.
* Consider making the model-ranking reversal in the intrinsic results easier to notice, possibly with a small callout near the relevant table.

## Conclusion and Practical Implications

The reviewers agreed with the paper’s practical recommendations:

* Evaluation should use metrics that are not dominated by tokenizer or encoding differences.
* Models should be tested in the script and register used by real users.
* Models that are already at chance should not be mixed with genuinely competent models when measuring robustness.
* Imbalanced tasks should use metrics such as Matthews correlation or macro-F1 instead of relying on accuracy alone.
* Checkpoint selection should be performed in the intended deployment register rather than only on formal-script data.

The generalization claims should be phrased carefully. Sinhala is an important case study, but the same effect has not yet been demonstrated across multiple languages or scripts.

## Limitations

The reviewers agreed that the limitations are a strength of the paper, but asked that the synthetic-Romanization limitation be made more prominent.

Other limitations to retain or emphasize include:

* The study focuses on one language.
* The downstream Romanized inputs are mostly automatically generated.
* The model set is heterogeneous, so model size cannot be isolated from family, tokenizer and training-data effects.
* The evaluation is zero-shot and uses one prompting setup.
* Public benchmark contamination cannot be ruled out.
* The results do not cover mixed-script and code-mixed user messages in sufficient depth.
* The study does not test transliteration-then-inference, Romanized fine-tuning, or other mitigation strategies.

These limitations reduce how broadly the results should be generalized, but the reviewers agreed that they do not remove the value of the Sinhala case study.

## Appendix, Ethics and Licensing

The reviewers asked us to keep the current ethics and licensing discussion in the camera-ready version. In particular, the paper should continue to explain why the Romanized SinhalaMMLU adaptation is not redistributed and should retain the discussion of dataset restrictions and model licenses.

The appendix should also continue to include the prompting details, compute information, transliteration evaluation and complete model-level results.

## Main Camera-Ready Actions

1. Correct the wording of the 312-fold decomposition and avoid presenting the two separate median factors as an exact product.
2. Make bits per word and the unit-dependence issue clearer.
3. Mention automatic transliteration prominently in the abstract, introduction and limitations.
4. State the model cohorts consistently throughout the paper.
5. Add the competence-screen sensitivity analysis using the existing results.
6. Clarify answer extraction and invalid-output handling for SOLD.
7. Explain the limited role of Global PIQA.
8. Keep the ethics, licensing and data-distribution statements.
9. Improve Figure 1 and the intrinsic-ranking presentation if space allows.
10. Moderate claims about generalization beyond Sinhala and about model scaling.

Overall, the reviewers found the paper publishable and valuable. The camera-ready changes are mainly intended to make the claims more precise, easier to understand and harder to misinterpret.