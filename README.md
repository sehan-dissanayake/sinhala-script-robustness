# Sinhala Script Robustness in LLMs

This repository contains the experiment pipeline for evaluating whether Large Language Models (LLMs) perform worse on downstream NLP tasks when the input Sinhala text is Romanized ("Singlish", e.g. `kohomada`) instead of using the native Unicode script (`කොහොමද`).

This is a zero-shot/few-shot evaluation pipeline (no model fine-tuning) designed to statistically compare LLM accuracy and F1 scores across two script conditions on two distinct tasks: Multiple Choice QA and Binary Classification.

## 📊 Datasets

We evaluate the models on two established datasets:
1. **[SinhalaMMLU](https://huggingface.co/datasets/naist-nlp/SinhalaMMLU)**: A multiple-choice QA dataset. We use a stratified sample of ~500 questions distributed proportionally across domain and difficulty.
2. **[SOLD (Sinhala Offensive Language Dataset)](https://huggingface.co/datasets/sinhala-nlp/SOLD)**: A binary hate-speech classification dataset. We use a stratified sample of ~500 items from the test split.

## 🛠️ Methodology

1. **Data Preparation**: Download and sample the raw datasets into an internal Unicode format.
2. **Transliteration**: Generate matched Romanized variants with four automatic candidates (custom phonetic, Aksharamukha, Sinhala G2P, and uroman), then select one on a separate native-speaker-reviewed pilot before downstream evaluation.
3. **Evaluation**: Query exactly 4 models (LLaMA-3.1-8B, Qwen2-7B, GPT-4o, Claude) uniformly across the dataset × script condition matrix.
4. **Analysis**: 
   - Compute standard metrics (Accuracy for MMLU, F1 for SOLD).
   - Perform paired significance testing (McNemar's test) per model per dataset to compare Unicode vs. Romanized performance.
   - Categorize errors into buckets (tokenization garbling, hallucination, hedging, etc.) via manual human-in-the-loop review.

## 📂 Repository Structure

```
sinhala-script-robustness/
├── data/
│   ├── raw/                           # Raw datasets from Hugging Face
│   ├── processed/                     # Sampled subsets (Unicode)
│   └── romanized/                     # Transliterated twins
├── src/
│   ├── data_prep/                     # Download and sampling scripts
│   ├── transliteration/               # Transliteration candidate logic and runner
│   ├── evaluation/                    # Unified model clients and prompting templates
│   ├── analysis/                      # Metrics, McNemar's test, and error analysis
│   └── webapp/                        # Streamlit app for visual inspection of transliterations
├── results/                           # Evaluation outputs, metrics, and error categories
├── notebooks/                         # Exploratory data analysis notebooks
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
   Download and sample the datasets:
   ```bash
   python src/data_prep/download_sinhala_mmlu.py
   python src/data_prep/download_sold.py
   python src/data_prep/sample_datasets.py
   ```
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