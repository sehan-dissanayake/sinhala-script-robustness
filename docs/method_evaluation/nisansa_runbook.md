# Nisansa romanizer — run guide

We need the Nisansa web romanizer's output for two corpora:

| Corpus | Items | Requests | Rough time | Status |
|---|---|---|---|---|
| `swa_bhasha_words` | 450,587 words | ~9,000 | ~1 hour | done |
| `augmented_sentences_sample` | 275,259 sentences | ~12,500 | ~1.2 hours | to run |

`social_media` (4,253 sentences) is **already done and does not need rerunning**:
it contains none of the sequences the endpoint fails or leaks on, so its cached
results are already the endpoint's verbatim output.

Measured throughput is ~64 items/s, so each corpus is about an hour of wall time
rather than the multi-session effort it was originally. There is **no rate
limit** — what used to look like load shedding was the ඤ bug failing whole
batches (see below). You can stop at any time; everything fetched is saved
immediately, and rerunning the same command resumes.

## Setup (once)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:PYTHONIOENCODING = "utf-8"      # or printing Sinhala crashes on cp1252
```

Use the venv's Python. System Python lacks the dependencies.

## What the runner records

The endpoint's output **verbatim**. Two upstream defects are captured rather
than smoothed over, because the evaluation counts them as the tool's genuine
errors:

- **17 sequences produce no output at all** — every one is ඤ (U+0DA4) carrying a
  vowel sign or al-lakuna. These are filtered client-side (sending one fails its
  whole batch), recorded in `unsupported.json`, and scored as an empty
  hypothesis, i.e. CER 1.0. They are *not* excluded from the comparison.
- **12 sequences leak** — they come back unromanized inside otherwise valid
  Latin output, so ඓතිහාසික becomes `ඓthihaasika`. Kept as-is.

Both tables are measured by `nisansa_probe.py` and committed under
`data/reference/nisansa_endpoint/`. You do not need to run the probe; it is
there so the tables are evidence rather than guesswork.

> **Historical note.** Results fetched before this change were passed through
> the in-house phonetic romanizer to patch leaked characters up. That made the
> measured system a hybrid of two methods under comparison, so the word corpus
> was refetched from scratch. Do not reintroduce `repair=True`.

## Run it

One command per corpus. Resumable — rerun after any interruption.

```powershell
python src/method_evaluation/nisansa_shards.py run --corpus swa_bhasha_words --all
python src/method_evaluation/nisansa_shards.py run --corpus augmented_sentences_sample --all
```

`--all` walks all 24 shards in one process. To split the work across people,
claim a shard number instead and use `--shard N`; shard *k* takes every 24th
item, so any partial result set stays a representative sample rather than an
alphabetically biased slice.

Progress and gaps:

```powershell
python src/method_evaluation/nisansa_shards.py status --corpus swa_bhasha_words
```

## Then merge and rescore

```powershell
python src/method_evaluation/nisansa_shards.py merge --corpus swa_bhasha_words
python src/method_evaluation/nisansa_shards.py merge --corpus augmented_sentences_sample
python src/method_evaluation/derive_nisansa_w.py --corpora social_media
python src/method_evaluation/run_evaluation.py
python src/method_evaluation/error_analysis.py
python src/method_evaluation/plots.py
python src/method_evaluation/generate_report.py
python src/method_evaluation/export_results_table.py
```

`merge` writes two hypothesis files: the endpoint's verbatim output, and the
same output with **v→w preprocessing** applied. That rewrite is a stage of the
method rather than an optional extra, so it happens automatically; the standalone
`derive_nisansa_w.py` call above is only for `social_media`, which has no shard
set. Both rows appear in the report, and the v→w row is the one to read as the
Nisansa result.

`merge` needs the rebuilt parallel corpus locally (`download_reference_data.py`
then `build_parallel_corpus.py` then `sample_corpus.py`); it warns if missing.

For the appendix comparison on only the rows every method answered:

```powershell
python src/method_evaluation/run_evaluation.py --common-subset
```

## Notes / gotchas

- **Don't run the same shard twice concurrently.** A lock file blocks it with a
  clear message. Two runs on one shard duplicate every request and gain nothing.
- **Failures are never faked.** A transport error is retried and never written
  as an empty result. A deterministic refusal is recorded as a refusal, so
  partial data cannot quietly turn into a wrong score. The two are kept distinct
  precisely because one is our problem and the other is the tool's.
- **Retrying a refusal is useless.** Measured across 60 failing batches with 6
  attempts each: not one succeeded later. The client raises immediately and
  bisects the batch instead of waiting.
- **Word-corpus shard results are committed** (~20 MB), so nobody has to refetch
  them and a teammate needs no dataset download to contribute. Sentence-corpus
  shards are gitignored: ~124 MB, and that corpus is a fixed-seed sample that
  regenerates exactly, so it is reproducible at the cost of one run.

## Committing word-corpus results

```powershell
git add data/reference/nisansa_shards/swa_bhasha_words
git commit -m "nisansa word corpus: raw endpoint output, no phonetic repair"
```
