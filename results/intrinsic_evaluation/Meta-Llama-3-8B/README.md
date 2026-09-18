# Meta-Llama-3-8B — intrinsic run

## Why this run

`SAWithanage/SinLlama-Llama-3-8B-Merged` is `meta-llama/Meta-Llama-3-8B` plus a
Sinhala-extended tokenizer and continual pre-training on 10.7M Sinhala
sentences. The pool of 31 contains Llama-3.**1**-8B, not Llama-3-8B, so a
SinLlama-against-the-pool comparison mixes the Sinhala adaptation together with
the 3 to 3.1 model update. This run scores the exact parent, so the difference
is the adaptation and nothing else.

Everything else about the run is unchanged: same 500 parallel sentence pairs,
same 500 mixed-script sentences, same `IntrinsicEvaluator` (copied verbatim from
the recorded runs), same fp16, same two CSVs with the same columns.

## Kaggle setup

| Setting | Value |
|---|---|
| Accelerator | GPU T4 x2 |
| Internet | On |
| Secret | `HF_TOKEN`, on an account with Llama-3 access granted |
| Input | the intrinsic evaluation dataset, with `diverse_sentences.csv` and `sinhala_mixed_dataset.csv` |

`meta-llama/Meta-Llama-3-8B` is gated with manual approval, and that approval is
separate from the Llama-3.1 one. If the token has not been approved the notebook
falls back to `NousResearch/Meta-Llama-3-8B`, which mirrors the same weights
without a gate, and prints which repository it used so the provenance stays on
the record. Either is fine; the official repository is preferred.

Expect well under an hour for 1,500 scored sequences.

## The tokenizer check

Cell 10 is a guard, not a result. Llama-3 and Llama-3.1 share one tokenizer, so
this run has to reproduce the Sinhala-script fertility already recorded for
Llama-3.1-8B, 9.676 tokens per word, and the Romanized 2.229. The cell asserts
that and stops the notebook if it fails, because a wrong checkpoint would
otherwise produce plausible-looking numbers that mean nothing.

## What to commit back

Into this directory:

* `Meta-Llama-3-8B_diverse_intrinsic.csv`
* `Meta-Llama-3-8B_mixed_intrinsic.csv`
* `pilot_intrinsic_results.csv`
* the executed notebook, with its output kept

The final cell also prints every pooled number and the SinLlama contrast, so if
the CSVs are awkward to move the log alone is enough to read the result off.

## Wiring it into the analysis

Add one line to `INTRINSIC_MODELS` in `paper/analysis/common.py`:

```python
"Meta-Llama-3-8B": ("Llama-3-8B", 8.0),
```

It is deliberately **not** added yet. Adding it changes the pool from 31 to 32
checkpoints, which moves every pooled median, spread and correlation in the
paper and every claim `verify_claims.py` checks. Llama-3-8B and SinLlama both
belong in the SinLlama comparison rather than in the pool the published
benchmark used, so they are reported beside it instead.
