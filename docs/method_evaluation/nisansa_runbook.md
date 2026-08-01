# Nisansa romanizer — team run guide

We need the Nisansa web romanizer's output for all **450,587** words in the
Swa-Bhasha corpus. The endpoint only serves roughly **25,000 words before it
starts refusing traffic**, so the work is split into **24 shards** that we run
between us, across as many sessions as it takes.

You can stop at any time. Everything fetched is saved immediately.

## Setup (once)

```bash
git clone <repo> && cd sinhala-script-robustness
python -m venv .venv
.venv\Scripts\activate          # Windows;  source .venv/bin/activate on mac/linux
pip install -r requirements.txt
```

You do **not** need to download any dataset. The word list ships with the repo
(`data/reference/nisansa_shards/swa_bhasha_words/manifest.txt.gz`, 2 MB).

> Use the venv's Python. Running with system Python will fail on missing
> packages.

## 1. See what needs doing

```bash
python src/method_evaluation/nisansa_shards.py status
```

```
 shard   done /  total   pct  state
    0   1,312 / 18,775    7.0  partial
    1   1,041 / 18,775    5.5  partial
   ...
overall: 25,271 / 450,587 (5.6%)
```

Every shard starts at ~1,041 done because results we already had were seeded in.

## 2. Claim a shard

Put your name next to a shard in the table at the bottom of this file, commit,
and push — so two people don't spend hours on the same shard.

## 3. Run it

```bash
python src/method_evaluation/nisansa_shards.py run --shard 7
```

Optional: `--limit 5000` to stop after 5,000 words this session.

**What you'll see.** A progress bar. When the server gets busy it shows
`server busy ...; retry 3/6 in 5s` — that is normal and it is still working, not
frozen. If the server refuses three groups in a row it stops cleanly:

```
  endpoint appears to be refusing traffic; stopping cleanly.
wrote 4,812 results. 12,922 items left in this shard.
Rate limited or interrupted? Just run the same command again - it resumes
```

**That is expected, not a failure.** Wait a while (an hour, or try the next day)
and run the same command again. It skips everything already done.

You can also stop it yourself with Ctrl+C at any point — results already
fetched are on disk.

## 4. Commit your results

```bash
git add data/reference/nisansa_shards/swa_bhasha_words/shard-07.jsonl
git commit -m "nisansa shard 07: <n> words"
git push
```

You only ever touch **your own** shard file, so this never conflicts with
anyone else's work. Repeat step 3 whenever you have time until your shard
reaches 100%.

## 5. When all 24 shards are complete (one person does this)

```bash
python src/method_evaluation/nisansa_shards.py merge
python src/method_evaluation/run_evaluation.py     # rescore with full coverage
python src/method_evaluation/plots.py
python src/method_evaluation/generate_report.py
```

`merge` needs the rebuilt parallel corpus locally (`download_reference_data.py`
then `build_parallel_corpus.py`); it warns if it is missing.

## Notes / gotchas

- **Don't run two shards at once on one machine, and don't run the same shard
  twice.** A lock file blocks the latter with a clear message. Parallel runs
  from one machine just add load to the bottleneck and slow everyone down.
- **Whether running from 6 different networks actually helps is unproven.** The
  evidence suggests the server sheds load globally rather than limiting per IP
  (it returns normal empty responses rather than HTTP 429, and slowing down
  didn't help). Worth having two people test simultaneously and comparing
  throughput against one person alone before everyone commits their evening
  to it.
- **Shards are interleaved, not contiguous** (shard *k* takes every 24th word).
  The corpus is alphabetically sorted, so contiguous blocks would give each
  person one initial letter, and a partly finished run would be an
  alphabetically biased sample. With the stride, whatever we finish stays a
  representative sample of the whole corpus.
- **Failures are never faked.** A failed request is retried, never written as an
  empty or untranslated result, so partial data can't quietly turn into a wrong
  score.

## Shard claim table

| Shard | Assigned to | Status |
|---|---|---|
| 0 |Sehan | partial |
| 1 | Sehan| partial |
| 2 | Sehan| |
| 3 | Sehan| |
| 4 | Dasun| |
| 5 |Dasun | |
| 6 | Dasun| |
| 7 | Dasun| |
| 8 | Eshin| |
| 9 | Eshin| |
| 10 | Eshin| |
| 11 | Eshin| |
| 12 | Shanil| |
| 13 | Shanil| |
| 14 | Shanil| |
| 15 | Shanil| |
| 16 | Dilhara| |
| 17 | Dilhara| |
| 18 | Dilhara| |
| 19 | Dilhara| |
| 20 | Chehan| |
| 21 | Chehan| |
| 22 | Chehan| |
| 23 | Chehan| |

Run `status` for live numbers; this table is only for claiming.
