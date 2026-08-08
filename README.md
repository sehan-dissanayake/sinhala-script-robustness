# Sinhala Script Robustness in LLMs

This repository contains the experiment pipeline for evaluating whether Large Language Models (LLMs) perform worse on downstream NLP tasks when the input Sinhala text is Romanized ("Singlish", e.g. `kohomada`) instead of using the native Unicode script (`කොහොමද`).

This is a zero-shot evaluation pipeline (no model fine-tuning, no few-shot exemplars) designed to statistically compare LLM accuracy and F1 scores across two script conditions on three distinct tasks: 4-way and 2-way Multiple Choice QA, and Binary Classification. Zero-shot is used uniformly across all three datasets so no task gets a prompting advantage the others don't.

## 📊 Datasets

Three tasks, **4,451 evaluation items in total — every available item, no sampling** — each frozen with both script conditions in `data/eval/`:

| Dataset | Task | Items | Source |
|---|---|---|---|
| **[SinhalaMMLU](https://huggingface.co/datasets/naist-nlp/SinhalaMMLU)** | 4-way multiple-choice QA | 1,851 | the only released split |
| **[SOLD](https://huggingface.co/datasets/sinhala-nlp/SOLD)** | Binary offensive-language classification | 2,500 | full test split |
| **[Global PIQA](https://huggingface.co/datasets/mrlbenchmarks/global-piqa-nonparallel)** (`sin_sinh`) | 2-way physical/cultural commonsense | 100 | whole benchmark |

Global PIQA also publishes a `sin_latn` config. That is a *separate*, non-parallel Sinhala set authored in Latin script, not a transliteration of `sin_sinh`, so using it would confound script with content. As with the other two datasets, our Romanized condition comes from our own transliterator. See [`docs/datasets.md`](docs/datasets.md) for the full provenance, schema, and caveats.

## 🛠️ Methodology

1. **Data Preparation**: Download the raw datasets and normalise them into one Unicode schema.
2. **Transliteration**: Generate matched Romanized variants with four candidates (custom phonetic, Aksharamukha, uroman, and Nisansa Sir's web method) and select one against 755k human-romanized reference items. **The phonetic method won on every corpus** — see [`docs/method_evaluation/`](docs/method_evaluation/).
3. **Eval sets**: Freeze every item of every dataset with the Unicode and Romanized forms paired in a single record.
4. **Evaluation** *(next phase)*: Query 4 models (LLaMA-3.1-8B, Qwen2-7B, GPT-4o, Claude) uniformly across the dataset × script condition matrix.
5. **Analysis** *(next phase)*:
   - Compute standard metrics (accuracy for MMLU and Global PIQA, F1 for SOLD).
   - Perform paired significance testing (McNemar's test) per model per dataset to compare Unicode vs. Romanized performance.
   - Categorize errors into buckets (tokenization garbling, hallucination, hedging, etc.) via manual human-in-the-loop review.

## 📂 Repository Structure

```
sinhala-script-robustness/
├── data/
│   ├── raw/                           # Raw datasets from Hugging Face
│   ├── processed/                     # Full datasets in one Unicode schema
│   ├── romanized/<method>/            # Transliterated twins, one dir per method
│   ├── reference/                     # Human-romanized corpora for method selection
│   └── eval/                          # ✅ Frozen eval sets: both script conditions paired
│       ├── <dataset>.jsonl            # Every item, no sampling
│       └── manifest.json              # Counts, strata, SHA-256 per file
├── src/
│   ├── data_prep/                     # Download, normalise, and freeze eval sets
│   ├── transliteration/               # Transliteration methods and shared writer
│   ├── method_evaluation/             # Phase-2 intrinsic comparison of the methods
│   ├── evaluation/                    # Model clients and prompting templates (next phase)
│   ├── analysis/                      # Metrics, McNemar's test, error analysis (next phase)
│   └── webapp/                        # Streamlit app for visual inspection of transliterations
├── docs/                              # Dataset provenance and method-evaluation write-ups
├── results/                           # Evaluation outputs, metrics, and error categories
└── requirements.txt                   # Pipeline dependencies
```

## 🚀 Setup & Execution

1. **Clone the repository**:
   ```bash
   git clone https://github.com/sehan-dissanayake/sinhala-script-robustness.git
   cd sinhala-script-robustness
   ```

2. **Environment Setup**:
   Create a virtual environment and install the required packages:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. **Hugging Face Authentication**:
   The `SinhalaMMLU` dataset is gated. You must request access on the [Hugging Face page](https://huggingface.co/datasets/naist-nlp/SinhalaMMLU). Then, create a `.env` file in the root directory and add your token:
   ```
   HF_TOKEN=your_huggingface_token_here
   ```

4. **Data Preparation Pipeline**:
   Run from the project root; the scripts resolve paths relative to the working directory.
   On Windows, set `PYTHONIOENCODING=utf-8` first or printing Sinhala crashes on cp1252.
   ```bash
   # Download the three raw datasets
   python src/data_prep/download_sinhala_mmlu.py
   python src/data_prep/download_sold.py
   python src/data_prep/download_global_piqa.py

   # Normalise into data/processed/
   python src/data_prep/prepare_datasets.py

   # Romanize with the selected method (add other methods only to inspect them)
   python src/transliteration/phonetic.py

   # Freeze data/eval/: all items, paired script conditions
   python src/data_prep/build_eval_sets.py
   ```
   `build_eval_sets.py` validates as it goes (ids aligned, no Sinhala leaking into the
   Romanized side, labels indexing real options, exemplars disjoint from the eval set) and
   is deterministic — re-running reproduces byte-identical files and SHA-256 digests.

5. **🔍 Run the Transliteration Inspector (Web App)**:
   We include a local Streamlit app to visually inspect and compare the original Sinhala Unicode text against its four Romanized counterparts side-by-side.
   Ensure you have installed the web app dependencies: 
   ```bash
   pip install "streamlit>=1.32" pandas
   ```
   then run:
   ```bash
   streamlit run src/webapp/app.py
   ```