# Sinhala Script Robustness in Language Models

Do language models get worse when Sinhala is typed in Latin letters ("Singlish",
`kohomada`) instead of the Sinhala script (`කොහොමද`)? This repository holds the
full pipeline and results behind that question: a tokenizer-independent
re-measurement of 31 open-weight checkpoints, and the first downstream evaluation
of Sinhala script variation across three tasks.

Everything is zero-shot. No model is fine-tuned and no few-shot exemplars are
shown. Every downstream item is evaluated twice, once per script condition, so
all comparisons are paired.

## Headline results

* **Perplexity was measuring the tokenizer.** Across 31 checkpoints, Sinhala-script
  perplexity and bits per byte are unrelated (Spearman 0.08), while perplexity is
  almost fully explained by tokenizer fertility (−0.87).
* **The reported 312-fold degradation splits exactly in two.** On the same 24
  checkpoints prior work used, a factor of 21 comes from identical content being
  cut into a different number of tokens, and a factor of 24 from a real rise in
  per-byte loss.
* **Romanization flattens the field.** A 22.4 point spread in Sinhala-script
  accuracy becomes 6.7 points, and Romanized accuracy rises with Sinhala-script
  accuracy at a slope of only 0.22.
* **Accuracy hides the damage.** On offensive-language detection accuracy moves by
  a few points while Matthews correlation loses more than half its value.

## Datasets

Three tasks, **9,479 evaluation items in total, every available item with no
sampling**, each frozen with both script conditions in `data/eval/`:

| Dataset | Task | Items | Baseline |
|---|---|---|---|
| **[SinhalaMMLU](https://huggingface.co/datasets/naist-nlp/SinhalaMMLU)** | 4-way and 5-way multiple choice | 6,879 | 23.4% chance |
| **[SOLD](https://huggingface.co/datasets/sinhala-nlp/SOLD)** | binary offensive-language | 2,500 | 59.4% majority |
| **[Global PIQA](https://huggingface.co/datasets/mrlbenchmarks/global-piqa-nonparallel)** (`sin_sinh`) | 2-way physical commonsense | 100 | 50.0% chance |

9,479 items x 2 script conditions = **18,958 prompts per checkpoint**.

Two 500-sentence intrinsic corpora, released with the benchmark this work
extends, support the language-modelling measurements. The Romanized side of the
parallel corpus was typed by native speakers, so the intrinsic results do not
depend on our transliterator.

**SinhalaMMLU is not redistributed here.** The public Hugging Face release is a
1,851-item sample. We obtained the full 6,879-item set from the authors, who asked
that it not be made public, and its CC BY-NC-ND licence separately forbids
distributing adaptations. `data/eval/sinhala_mmlu.jsonl` is therefore
git-ignored. What is released is the code that rebuilds it, the item identifiers,
and a SHA-256 digest in `data/eval/manifest.json`, so anyone with their own copy
of the full set can reproduce our file byte for byte. SOLD and Global PIQA are
released in full with their Romanized side attached, so those results are
reproducible by anyone. See [`docs/datasets.md`](docs/datasets.md).

Global PIQA also publishes a `sin_latn` config. That is a *separate*,
non-parallel Sinhala set authored in Latin script, not a transliteration of
`sin_sinh`, so using it would confound script with content. Our Romanized
condition comes from our own transliterator for all three datasets.

## Pipeline

1. **Data preparation.** Download the raw datasets and normalise them into one
   Sinhala-script schema.
2. **Transliteration.** Generate matched Romanized variants with four candidates
   (in-house phonetic, Aksharamukha, uroman, and a web romanizer) and select one
   against 755k human-romanized reference items. **The phonetic method won on every
   corpus.** See [`docs/method_evaluation/`](docs/method_evaluation/).
3. **Frozen eval sets.** Freeze every item with both script forms paired in a
   single record. Deterministic, with SHA-256 digests.
4. **Intrinsic evaluation.** Score 31 checkpoints on 1,500 sequences each, in the
   Sinhala script, Romanized and mixed-script conditions. Notebooks and per-item
   outputs in `results/intrinsic_evaluation/`.
5. **Downstream evaluation.** Run 11 instruction-tuned checkpoints over all 18,958
   prompts, greedy and zero-shot. Notebooks and per-item generations in
   `results/extrinsic_evaluation/`.
6. **Analysis.** Corpus-pooled bits per byte, character and word; paired McNemar
   tests with Holm correction; bootstrap intervals; a competence screen; and the
   robustness refits. All in `paper/analysis/`.

## The papers

`paper/` holds two write-ups of this work and everything that generates them: the
full ACL submission, and a four page short paper for the non-archival
GlobalSouthAI workshop at NeurIPS 2026 that leads with what the case study says
about evaluating Global South languages. The short one is written for its length
rather than compressed, and reuses the same verified analysis outputs.

```
paper/
├── acl_latex.tex          # the full paper (compile with pdfLaTeX)
├── custom.bib             # every entry checked against a primary record
├── sinhala/               # the inline Sinhala examples, prebuilt as PDF images
├── globalsouthai/         # the four page workshop paper (compile with pdfLaTeX)
│   ├── main.tex
│   ├── checklist.tex      # the NeurIPS checklist, filled in
│   ├── make_assets.py     # its figures and tables, at NeurIPS page geometry
│   └── check_paper.py     # page budget and numeric-claim guard rails
├── analysis/              # statistics, one script per block, writes out/*.json
│   ├── stats_intrinsic.py
│   ├── stats_extrinsic.py
│   ├── stats_robustness.py      # reproduction, decomposition, refits, pilot
│   ├── stats_attestation.py     # transliterator fidelity
│   ├── run_synthetic_vs_human.py  # scores our transliteration against human typing
│   └── verify_claims.py         # checks every number in the paper
├── tables/make_tables.py  # generates every LaTeX table body
└── figures/make_figures.py
```

No number in either paper is typed by hand. `verify_claims.py` re-derives every
figure quoted in the text from the frozen analysis outputs and fails if any has
moved. `check_paper.py` then asserts that the workshop version introduces no
number that verification has not already covered, and that its content still fits
in four pages:

```bash
python paper/analysis/verify_claims.py       # 251 claims checked
python paper/globalsouthai/check_paper.py    # page budget and numbers
```

See [`paper/README.md`](paper/README.md) and
[`paper/globalsouthai/README.md`](paper/globalsouthai/README.md) for how to build
the PDFs.

## Repository layout

```
sinhala-script-robustness/
├── data/
│   ├── raw/            # raw datasets as downloaded
│   ├── processed/      # normalised into one Sinhala-script schema
│   ├── romanized/      # transliterated twins, one directory per method
│   ├── reference/      # human-romanized corpora used to pick the method
│   └── eval/           # frozen eval sets, both conditions paired, + manifest
├── src/
│   ├── data_prep/          # download, normalise, freeze
│   ├── transliteration/    # the four methods and a shared writer
│   ├── method_evaluation/  # how the method was chosen
│   ├── evaluation/         # model clients and prompt templates
│   └── analysis/           # metrics and significance helpers
├── paper/              # both write-ups, their analysis, tables and figures
├── results/            # notebooks, per-item outputs, aggregated metrics
├── docs/               # dataset provenance and method write-ups
├── tools/anonymize.py  # strips author-identifying strings before publishing
└── requirements.txt
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

SinhalaMMLU is gated. Request access on its
[Hugging Face page](https://huggingface.co/datasets/naist-nlp/SinhalaMMLU), then
put your token in a `.env` file at the repository root:

```
HF_TOKEN=your_huggingface_token_here
```

Python 3.10 or newer. On Windows set `PYTHONIOENCODING=utf-8` first, or printing
Sinhala fails on cp1252.

## Reproducing

Run from the repository root. Steps 1 to 3 rebuild the data, step 4 reproduces
every number and figure from the per-item outputs already in `results/`.

```bash
# 1. fetch
python src/data_prep/download_sinhala_mmlu.py     # needs HF_TOKEN
python src/data_prep/download_sold.py
python src/data_prep/download_global_piqa.py

# 2. normalise and romanize
python src/data_prep/prepare_datasets.py
python src/transliteration/phonetic.py

# 3. freeze the eval sets (validates as it goes, byte-identical on re-run)
python src/data_prep/build_eval_sets.py

# 4. analysis, tables, figures, and the claim check
python paper/analysis/stats_intrinsic.py
python paper/analysis/stats_extrinsic.py
python paper/analysis/stats_robustness.py
python paper/analysis/stats_attestation.py        # needs the Swa-bhasha word list
python paper/tables/make_tables.py
python paper/figures/make_figures.py
python paper/analysis/verify_claims.py
```

`build_eval_sets.py` validates as it goes: ids aligned, no Sinhala leaking into
the Romanized side, labels indexing real options, exemplars disjoint from the eval
set. It is deterministic, so re-running reproduces byte-identical files and
SHA-256 digests.

To inspect transliterations side by side:

```bash
pip install "streamlit>=1.32" pandas
streamlit run src/webapp/app.py
```

## Compute

Total wall-clock time was about 80 hours: roughly 10 hours for the intrinsic runs
(46,500 scored sequences) and 70 for the downstream runs (208,538 generations), of
which about 25 hours were Phi-4-14B alone. All runs used commodity dual T4 GPUs in
fp16 except Phi-4-14B, which ran on a single 16 GB RTX 4070 Ti SUPER.

## Licences

Each dataset and tool keeps its own licence, and what we do and do not
redistribute is set out per source in the paper's licence appendix and in
[`docs/datasets.md`](docs/datasets.md). Two obligations worth repeating here:
Global PIQA is CC BY-SA 4.0 and **evaluation only**, its authors disallow training
on it or on synthetic data seeded from it, and any publication using uroman must
acknowledge it, which the paper does.

## Anonymity

The evaluation notebooks were run on Kaggle and originally carried dataset paths
containing account slugs that identify the authors. Those have been replaced with
neutral placeholders. Before publishing an anonymous mirror for double-blind
review, run:

```bash
python tools/anonymize.py --check
```

It exits non-zero if any known or suspicious identifying string is present. See
[`ANONYMITY.md`](ANONYMITY.md) for the full checklist.
