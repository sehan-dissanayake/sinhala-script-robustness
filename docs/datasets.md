# Downstream evaluation datasets

Status: **final**. `data/eval/` is frozen and the evaluation has been run against it.
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

Pairing both conditions in one record is deliberate: the McNemar test is a *paired*
test, so the runner must not be able to score mismatched subsets against each other.

| File | Items | Task | Coverage |
|---|---|---|---|
| `sinhala_mmlu.jsonl` | 6,879 | 4-way and 5-way MCQ | the full set, obtained from the authors |
| `sold.jsonl` | 2,500 | Binary | the entire test split |
| `global_piqa.jsonl` | 100 | 2-way MCQ | all of `sin_sinh` |

9,479 items x 2 script conditions = **18,958 prompts per model**.

**No sampling, no few-shot.** Every available item is evaluated and every prompt is zero-shot —
no demonstrations shown to the model before the real question. Zero-shot is used uniformly
across all three datasets so none of them gets a prompting advantage the others don't; running
two datasets few-shot and one zero-shot would make the cross-dataset comparison uninterpretable.
There is no randomness anywhere in this step. Label distributions are the source distributions:
MMLU A/B/C/D/E = 1524/1658/1692/1516/489, SOLD NOT/OFF = 1485/1015, Global PIQA A/B = 49/51. `strata` is
still recorded on every item and summarised in the manifest, since the analysis uses
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

**SinhalaMMLU** (`naist-nlp/SinhalaMMLU`, gated — needs `HF_TOKEN`). The public release is a
1,851-item sample. The full 6,879-item set was obtained from the authors by email in August
2026, and **is not redistributed here**: they asked that it not be made public, and the
CC BY-NC-ND licence separately forbids distributing adaptations, which our Romanized twin is.
`data/eval/sinhala_mmlu.jsonl` is git-ignored. What is released is the code that rebuilds it,
the item identifiers, and the SHA-256 digest in `manifest.json`, so a reader with their own copy
of the full set can confirm they have reproduced our file exactly. Two things to know:

* The full set carries real `difficulty` strata (Easy, Medium, Hard) and six domains, unlike the
  public sample, in which every row is labelled `difficulty=Easy`. The builder detects constant
  strata fields and drops them from the reported breakdown rather than implying an analysis is
  possible, so it behaves correctly on either input.
* One upstream row (`mmlu_0854`, `q_no` 64, "how many standard time zones is the Earth divided
  into") stores the answer *value* `24` in the `answer` field instead of the 1-based index `3`.
  That previously produced the uninterpretable label `"24"`. `prepare_datasets.py` now recovers
  the index by matching the value against the choices (giving `C`) and raises if that match is
  ambiguous, so a similar upstream slip cannot pass silently.

**SOLD** (`sinhala-nlp/SOLD`). The full 2,500-item `test` split is evaluated. The dataset also
ships a 7,500-item `train` split, meant for fine-tuning a model; it is downloaded (by
`download_sold.py`) but otherwise unused here, since nothing in this project is fine-tuned.

**Global PIQA** (`mrlbenchmarks/global-piqa-nonparallel`, config `sin_sinh`). 100 hand-written
items, each a prompt plus two candidate solutions. The source paper describes 110 items created
and verified by its two authors, of which the public non-parallel release carries 100. 77 of the
100 carry `approx_cultural_score = 1` in the release, which is the field this project reads as
"culturally specific"; the source paper itself gives a qualitative three-way split (general
common sense, specifically Sri Lankan, and the Sri Lankan version of a shared concept) without
per-class counts. Two decisions:

The dataset also publishes a `sin_latn` config, and we do **not** use it as the Romanized
condition. It is the same 100 items — all 200 English glosses match `sin_sinh` exactly — but
written in a scholarly transliteration with diacritics, in the style of ISO 15919: `Hēn
govithæna karannē kumana piḷivelaṭada?`. Only 86.4% of its characters are ASCII and 61.1% of its
words carry at least one non-ASCII character (ā, ṭ, æ, ē, ī, ḷ, ḍ, ṇ, ū, ō, ǣ, a combining breve
and ZWJ), costing 1.178 bytes per character against 1.000 for ours.

That matters for three reasons. It is not the register this project is about: Romanized Sinhala
as people actually type it is plain ASCII with no diacritics, which is what our transliterator
produces. Its diacritics and ZWJ are rare characters that tokenizers fragment, so using it would
put back the byte-and-token confound the whole paper exists to remove. And it exists for Global
PIQA only — SinhalaMMLU and SOLD have no Latin-script twin — so using it for one dataset and our
transliterator for the other two would make the script condition mean different things across
the three tasks. We therefore transliterate `sin_sinh` ourselves, exactly as for the other two
datasets. Note also that `sin_latn` is registered as its own language in the release, with its
own `example_id` group and its own answer shuffling, so it is not a drop-in paired twin either.

Licence note: Global PIQA is CC BY-SA 4.0 and **evaluation-only** — the authors explicitly
disallow training on it, or on synthetic data seeded from it. This project does no training,
so that is satisfied, but any future fine-tuning work must exclude it.

## Caveats for the analysis phase

* **Global PIQA power.** With n = 100 and two options, chance is 50% and McNemar's test on this
  dataset can only detect fairly large script effects. Treat it as a third task that either
  corroborates or fails to corroborate MMLU and SOLD, not as an independently conclusive result.
  Reporting the exact discordant-pair counts alongside the p-value is worth doing here.
* **Cultural specificity is a confound worth checking.** 77 of the 100 Global PIQA `sin_sinh`
  items are flagged culturally specific. If Romanized performance drops there, it may reflect thin Romanized
  Sinhala coverage of cultural vocabulary rather than a script effect per se; `strata` carries
  the flag so this can be split out.
* **SOLD text contains placeholders.** Posts use `@USER` and similar tokens, which pass through
  transliteration untouched (by design) and appear identically in both conditions.
* **MMLU domain skew.** Humanities is the largest domain at 3,341 of 6,879 items. Domain-level
  breakdowns outside it are thinner: Social Science 1,059, Other 1,014, STEM 614, Business
  Studies 463, Language 388.
* **Cost.** 18,958 prompts per checkpoint, 208,538 across the eleven evaluated. The runners are
  resumable, which matters on a hosted notebook with a hard session timeout.

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
