# Downstream evaluation datasets

Status: **final**. `data/eval/` is frozen and ready for the LLM experiment phase.
Everything here is reproducible from the raw sources with no randomness involved;
`data/eval/manifest.json` records the counts, strata, and a SHA-256 per file.

## What is in data/eval/

One record per evaluation item, with both script conditions side by side:

```json
{
  "id": "mmlu_0002",
  "dataset": "sinhala_mmlu",
  "task": "mcq",
  "label": "C",
  "strata": {"domain": "Humanities", "difficulty": "Easy"},
  "unicode":   {"text": "හින්දු භක්තිකයින්ගේ …", "options": ["නත්තල් උත්සවය", "…"]},
  "romanized": {"text": "hindu bhakthikayingee …", "options": ["naththal uthsawaya", "…"]},
  "n_options": 4
}
```

`task` is `mcq` (SinhalaMMLU, Global PIQA) or `binary` (SOLD). MCQ records carry `n_options`
and a letter `label` indexing `options`; SOLD carries `label` in `{"NOT", "OFF"}` and no options.
Global PIQA records additionally carry `example_id`, `culturally_specific`, `llm_assisted`, and
`eng_options` (upstream English translations, useful for error analysis).

Pairing both conditions in one record is deliberate: the planned McNemar test is a *paired*
test, so the runner must not be able to score mismatched subsets against each other.

| File | Items | Task | Coverage |
|---|---|---|---|
| `sinhala_mmlu.jsonl` | 1,851 | 4-way MCQ | the entire released split |
| `sold.jsonl` | 2,500 | Binary | the entire test split |
| `global_piqa.jsonl` | 100 | 2-way MCQ | all of `sin_sinh` |

4,451 items × 2 script conditions = **8,902 prompts per model**.

**No sampling, no few-shot.** Every available item is evaluated and every prompt is zero-shot —
no demonstrations shown to the model before the real question. Zero-shot is used uniformly
across all three datasets so none of them gets a prompting advantage the others don't; running
two datasets few-shot and one zero-shot would make the cross-dataset comparison uninterpretable.
There is no randomness anywhere in this step. Label distributions are the source distributions:
MMLU A/B/C/D = 473/501/507/370, SOLD NOT/OFF = 1485/1015, Global PIQA A/B = 49/51. `strata` is
still recorded on every item and summarised in the manifest, since the analysis phase will want
per-domain and per-class breakdowns.

## Script conditions

The Unicode condition is the source text as published (NFC-normalised).
The Romanized condition is produced by the **phonetic** method, which won every corpus in the
phase-2 intrinsic evaluation (CER 0.182 social media / 0.121 words / 0.112 augmented sentences).
See [`method_evaluation/`](method_evaluation/) for that comparison and
[`transliteration/phonetic_method.md`](transliteration/phonetic_method.md) for the method itself.

`data/romanized/` keeps all four candidate methods for all datasets so the Streamlit inspector
can still be used to compare them, but only `phonetic` feeds `data/eval/`. To evaluate with a
different method: `python src/data_prep/build_eval_sets.py --method uroman`.

## Sources and provenance

**SinhalaMMLU** (`naist-nlp/SinhalaMMLU`, gated — needs `HF_TOKEN`). Only a `train` split is
released, 1,851 questions, all 4-way. Two things to know:

* Every row is labelled `difficulty=Easy`, so difficulty carries no information. The builder
  detects constant strata fields, drops them from the reported breakdown, and says so rather
  than implying a difficulty analysis is possible. The field is still kept on each record.
* One upstream row (`mmlu_0854`, `q_no` 64, "how many standard time zones is the Earth divided
  into") stores the answer *value* `24` in the `answer` field instead of the 1-based index `3`.
  That previously produced the uninterpretable label `"24"`. `prepare_datasets.py` now recovers
  the index by matching the value against the choices (giving `C`) and raises if that match is
  ambiguous, so a similar upstream slip cannot pass silently.

**SOLD** (`sinhala-nlp/SOLD`). The full 2,500-item `test` split is evaluated. The dataset also
ships a 7,500-item `train` split, meant for fine-tuning a model; it is downloaded (by
`download_sold.py`) but otherwise unused here, since nothing in this project is fine-tuned.

**Global PIQA** (`mrlbenchmarks/global-piqa-nonparallel`, config `sin_sinh`). 100 hand-written
items, each a prompt plus two candidate solutions, 77 of them culturally specific. Two decisions:

The dataset also publishes a `sin_latn` config. That is a **separate, non-parallel** Sinhala set
authored in Latin script by different contributors — not a transliteration of `sin_sinh`. Using
it as the Romanized condition would vary content and authorship along with script and make the
comparison uninterpretable, so we transliterate `sin_sinh` ourselves, exactly as for the other
two datasets.

Licence note: Global PIQA is CC BY-SA 4.0 and **evaluation-only** — the authors explicitly
disallow training on it, or on synthetic data seeded from it. This project does no training,
so that is satisfied, but any future fine-tuning work must exclude it.

## Caveats for the analysis phase

* **Global PIQA power.** With n = 100 and two options, chance is 50% and McNemar's test on this
  dataset can only detect fairly large script effects. Treat it as a third task that either
  corroborates or fails to corroborate MMLU and SOLD, not as an independently conclusive result.
  Reporting the exact discordant-pair counts alongside the p-value is worth doing here.
* **Cultural specificity is a confound worth checking.** 77% of Global PIQA `sin_sinh` items are
  culturally specific. If Romanized performance drops there, it may reflect thin Romanized
  Sinhala coverage of cultural vocabulary rather than a script effect per se; `strata` carries
  the flag so this can be split out.
* **SOLD text contains placeholders.** Posts use `@USER` and similar tokens, which pass through
  transliteration untouched (by design) and appear identically in both conditions.
* **MMLU domain skew.** Humanities is 63% of the benchmark (1,162 of 1,851). Domain-level
  breakdowns outside it are thinner: Social Science 370, STEM 164, Language 155.
* **Cost.** 8,902 prompts per model, ~35.6k across four models. Worth checking against your
  API budget and rate limits before starting, and worth making the runner resumable so a
  partial run is not lost.

## Regenerating

```bash
python src/data_prep/download_sinhala_mmlu.py     # needs HF_TOKEN in .env
python src/data_prep/download_sold.py
python src/data_prep/download_global_piqa.py
python src/data_prep/prepare_datasets.py
python src/transliteration/phonetic.py            # add --datasets to limit scope
python src/data_prep/build_eval_sets.py
```

If a label or metadata fix changes `data/processed/` you must refresh the romanized twins.
Re-running a local method is the normal route. The Nisansa method costs one HTTP request per
string (~4,500 for the full set), so when only metadata changed use:

```bash
python src/transliteration/resync_metadata.py --method nisansa_sirs_method
```

which copies the non-Romanized fields across and refuses to run if the Sinhala text itself
differs — in that case the romanization really is stale and the method must be re-run.
