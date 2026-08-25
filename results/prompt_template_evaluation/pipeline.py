# %% [markdown]
# # Prompt Template Selection — Extrinsic Evaluation
# Pick the single prompt template (per dataset) to standardize on for the full 11-model
# extrinsic evaluation, using 20-item mini subsets so this stays cheap on Kaggle's free
# T4 x2 session.
# 
# **What varies (the actual experiment):** the prompt template text — byte-identical
# across all 11 models, per dataset:
# - `T1_direct` — ask for the answer only, nothing else.
# - `T2_fewshot` — 2 fixed exemplars (authored separately, not drawn from the mini set
#   and not from the exemplars themselves), answered exactly in the target output format,
#   then the real question.
# - `T3_answer_first` — ask the model to state the answer first and reason afterwards, so
#   that even a model which insists on reasoning still emits the answer inside the token
#   budget.
# 
# **What is held fixed per model, not part of the experiment:** whether native chain-of-
# thought is suppressed at the chat-template level. 3 of the 11 models default to emitting
# a `<think>...</think>` block regardless of prompt wording (confirmed for SmolLM3-3B from
# production data; documented behavior for Qwen-3.5-4B/9B). Suppressing it is a decoding-
# config fix, not a template being tested — it is applied identically across all three
# templates and both script conditions for those 3 models only, so the template comparison
# stays single-variable. See `REASONING_MODE` in each model's config cell.
# 
# **Metrics:** for each (dataset, template), pooled across all models and both script
# conditions — `invalid_rate`, `accuracy_among_valid`, and `overall_accuracy` (accuracy
# treating INVALID as wrong — the metric actually used to pick the winner).

# %% [markdown]
# ## 1. Configuration

# %%
# ============================================================
# PATHS & HYPERPARAMETERS — set once for the whole pilot
# ============================================================
from pathlib import Path

# Mini datasets (20 items each), already paired unicode/romanized. Update this if your
# Kaggle dataset mount differs.
MINI_DATA_DIR = Path("/kaggle/input/prompt-template-evaluation")
MINI_DATA_FILES = {
    "sinhala_mmlu": MINI_DATA_DIR / "sinhala_mmlu_prompt_selection.jsonl",
    "sold": MINI_DATA_DIR / "sold_prompt_selection.jsonl",
    "global_piqa": MINI_DATA_DIR / "global_piqa_prompt_selection.jsonl",
}

# Everything this notebook writes goes here.
OUTPUT_DIR = Path("/kaggle/working/prompt_template_evaluation")
RAW_DIR = OUTPUT_DIR / "raw"
SUMMARY_DIR = OUTPUT_DIR / "summaries"
for d in (RAW_DIR, SUMMARY_DIR):
    d.mkdir(parents=True, exist_ok=True)

MAX_NEW_TOKENS = 40      # matches the production extrinsic-evaluation budget
TEMPERATURE = 0.0        # greedy, deterministic
MAX_INPUT_TOKENS = 4096

TEMPLATES = ["T1_direct", "T2_fewshot", "T3_answer_first"]
SCRIPTS = ["unicode", "romanized"]

print(f"Mini data dir:  {MINI_DATA_DIR}")
print(f"Output dir:     {OUTPUT_DIR}")
print(f"Templates:      {TEMPLATES}")
print(f"Max new tokens: {MAX_NEW_TOKENS}")

# %% [markdown]
# ## 2. Environment Setup & Hardware Verification

# %%
import sys

!{sys.executable} -m pip install --upgrade --quiet transformers accelerate huggingface_hub bitsandbytes

import gc
import json
import re
import time

import pandas as pd
import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

device_count = torch.cuda.device_count()
print(f"PyTorch {torch.__version__} | transformers {transformers.__version__} | {device_count} GPU(s)")
for i in range(device_count):
    name = torch.cuda.get_device_name(i)
    mem = torch.cuda.get_device_properties(i).total_memory / (1024**3)
    print(f"  cuda:{i} -> {name} ({mem:.1f} GB)")
assert device_count > 0, "No GPU detected. Enable GPU T4 x2 in Session options."

# %%
# HuggingFace authentication - needed for gated models (Llama-3.1-8B-Instruct).
from huggingface_hub import login

try:
    from kaggle_secrets import UserSecretsClient
    user_secrets = UserSecretsClient()
    HF_TOKEN = user_secrets.get_secret("HF_TOKEN")
    login(token=HF_TOKEN)
    print("Authenticated via Kaggle Secrets.")
except Exception as e:
    import os
    HF_TOKEN = os.environ.get("HF_TOKEN", "")   # Fallback to env var, or paste your token here
    if HF_TOKEN:
        login(token=HF_TOKEN)
        print("Authenticated via explicit token or env var.")
    else:
        print(f"No HF_TOKEN found ({e}). Public models will still work.")

# %% [markdown]
# ## 3. Load Mini Evaluation Datasets
# 20 items per dataset, already paired unicode/romanized (same schema as `data/eval/*.jsonl`).

# %%
def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

MINI_DATASETS = {name: load_jsonl(path) for name, path in MINI_DATA_FILES.items()}

for name, items in MINI_DATASETS.items():
    print(f"{name:14} : {len(items)} items (task={items[0]['task']})")

# %% [markdown]
# ## 4. Few-Shot Exemplars (fixed, authored separately from the mini sets)
# 2 exemplars per dataset, per script condition, answered exactly in the target output
# format. None of these items appear in `MINI_DATASETS` above, so `T2_fewshot` tests format
# transfer, not memorization of the pilot set.

# %%
FEWSHOT_EXAMPLES = {
    "sinhala_mmlu": {
        "unicode": [
            {"question": "ලෝකයේ විශාලතම මහාද්වීපය කුමක්ද?",
             "options": ["ආසියාව", "අප්‍රිකාව", "යුරෝපය", "ඕස්ට්‍රේලියාව"],
             "answer_digit": "1"},
            {"question": "දිනකට පැය කීයක් තිබේද?",
             "options": ["12", "24", "48", "60"],
             "answer_digit": "2"},
        ],
        "romanized": [
            {"question": "lookayee wishaalathama mahaadwiipaya kumakda?",
             "options": ["aasiyaawa", "aprikaawa", "yuroopaya", "oostreeliyaawa"],
             "answer_digit": "1"},
            {"question": "dinakata paeya kiiyak thibeeda?",
             "options": ["12", "24", "48", "60"],
             "answer_digit": "2"},
        ],
    },
    "global_piqa": {
        "unicode": [
            {"question": "අත් සෝදා ගැනීමට වඩාත් සුදුසු දෙය කුමක්ද?",
             "options": ["සබන් හා වතුර භාවිතා කිරීම", "වැලි හා ගල් භාවිතා කිරීම"],
             "answer_digit": "1"},
            {"question": "රෑට කියවීමට වඩාත් සුදුසු ආලෝකය කුමක්ද?",
             "options": ["අඳුර", "පහන් එළිය"],
             "answer_digit": "2"},
        ],
        "romanized": [
            {"question": "ath soodaa gaeniimata wadaath sudusu deya kumakda?",
             "options": ["saban haa wathura bhaawithaa kiriima", "waeli haa gal bhaawithaa kiriima"],
             "answer_digit": "1"},
            {"question": "raaeta kiyawiimata wadaath sudusu aalookaya kumakda?",
             "options": ["andura", "pahan eliya"],
             "answer_digit": "2"},
        ],
    },
    "sold": {
        "unicode": [
            {"text": "අද කාලගුණය හොඳයි. එළියට ගිහින් ඇවිදින්න පුළුවන්.", "answer": "NOT"},
            {"text": "උඹ හරිම මෝඩයෙක්. කිසි දෙයක් තේරෙන්නෙ නෑ.", "answer": "OFF"},
        ],
        "romanized": [
            {"text": "ada kaalagunaya hondayi. eliyata gihin aewidinna puluwan.", "answer": "NOT"},
            {"text": "umba harima moodayek. kisi deyak theerennee naae.", "answer": "OFF"},
        ],
    },
}

print("Few-shot exemplars defined for:", list(FEWSHOT_EXAMPLES.keys()))

# %% [markdown]
# ## 5. Prompt Templates
# All three templates share the same anti-leak instruction ("do not repeat the question")
# and end with the same `Answer:` generation cue, requested so the extractor always has a
# consistent anchor to search from. Only the instruction body differs between templates.

# %%
# ============================================================
# SHARED FRAGMENTS
# ============================================================

NO_REPEAT_INSTRUCTION = "Do not repeat the question or text in your response."


def _humanize_domain(domain):
    return str(domain).replace("_", " ")


def _mcq_options_block(options):
    digit_labels = [str(i + 1) for i in range(len(options))]
    options_str = "\n".join(f"{d}. {opt}" for d, opt in zip(digit_labels, options))
    return options_str, digit_labels


# ============================================================
# T1 — DIRECT: answer only, nothing else
# ============================================================

def build_mcq_prompt_t1(question, options, subject=None):
    options_str, digit_labels = _mcq_options_block(options)
    n = len(options)
    valid_range = "/".join(digit_labels)
    if subject is not None:
        prompt = (
            f"This is a multiple-choice question related to the {_humanize_domain(subject)}. "
            f"Choose the correct or most appropriate answer from answers {valid_range} for the "
            f"following question. {NO_REPEAT_INSTRUCTION} Respond with only the number "
            f"({valid_range}) and nothing else.\n"
            f"Question: {question}\n"
            f"{options_str}\n"
            f"Answer:"
        )
    else:
        prompt = (
            f"Out of the given {n} answers, which one is the best option to complete the given "
            f"text? {NO_REPEAT_INSTRUCTION} Respond with only the number ({valid_range}) and "
            f"nothing else.\n"
            f"{question}\n"
            f"{options_str}\n"
            f"Answer:"
        )
    return prompt, digit_labels


def build_sold_prompt_t1(text):
    return (
        f"Classify the following Sinhala text as either 'NOT' (not offensive) or 'OFF' "
        f"(offensive). {NO_REPEAT_INSTRUCTION} Respond with only \'NOT\' or \'OFF\' and "
        f"nothing else.\n"
        f"Text: {text}\n"
        f"Answer:"
    )


# ============================================================
# T2 — FEW-SHOT: 2 fixed exemplars answered in the exact target format
# ============================================================

def build_mcq_prompt_t2(question, options, dataset_key, script, subject=None):
    options_str, digit_labels = _mcq_options_block(options)
    n = len(options)
    valid_range = "/".join(digit_labels)
    examples = FEWSHOT_EXAMPLES[dataset_key][script]

    if subject is not None:
        instruction = (
            f"This is a multiple-choice question related to the {_humanize_domain(subject) if subject else ''}. "
            f"Choose the correct or most appropriate answer from answers {valid_range}. "
            f"{NO_REPEAT_INSTRUCTION} Respond with only the number ({valid_range}) and nothing else, "
            f"exactly like the examples below."
        )
    else:
        instruction = (
            f"Out of the given {n} answers, which one is the best option to complete the given text? "
            f"{NO_REPEAT_INSTRUCTION} Respond with only the number ({valid_range}) and nothing else, "
            f"exactly like the examples below."
        )

    shots = []
    for ex in examples:
        ex_options_str, _ = _mcq_options_block(ex["options"])
        shots.append(
            f"Question: {ex['question']}\n{ex_options_str}\nAnswer: {ex['answer_digit']}"
        )
    shots_block = "\n\n".join(shots)

    prompt = (
        f"{instruction}\n\n"
        f"{shots_block}\n\n"
        f"Question: {question}\n"
        f"{options_str}\n"
        f"Answer:"
    )
    return prompt, digit_labels


def build_sold_prompt_t2(text, script):
    examples = FEWSHOT_EXAMPLES["sold"][script]
    instruction = (
        "Classify the following Sinhala text as either 'NOT' (not offensive) or 'OFF' "
        f"(offensive). {NO_REPEAT_INSTRUCTION} Respond with only 'NOT' or 'OFF' and nothing "
        "else, exactly like the examples below."
    )
    shots = [f"Text: {ex['text']}\nAnswer: {ex['answer']}" for ex in examples]
    shots_block = "\n\n".join(shots)
    return (
        f"{instruction}\n\n"
        f"{shots_block}\n\n"
        f"Text: {text}\n"
        f"Answer:"
    )


# ============================================================
# T3 — ANSWER FIRST: state the answer before any reasoning
# ============================================================

def build_mcq_prompt_t3(question, options, subject=None):
    options_str, digit_labels = _mcq_options_block(options)
    n = len(options)
    valid_range = "/".join(digit_labels)
    if subject is not None:
        prompt = (
            f"This is a multiple-choice question related to the {_humanize_domain(subject)}. "
            f"Choose the correct or most appropriate answer from answers {valid_range} for the "
            f"following question. {NO_REPEAT_INSTRUCTION} State the answer number "
            f"({valid_range}) FIRST, before any explanation. You may briefly explain your "
            f"reasoning only after giving the number.\n"
            f"Question: {question}\n"
            f"{options_str}\n"
            f"Answer:"
        )
    else:
        prompt = (
            f"Out of the given {n} answers, which one is the best option to complete the given "
            f"text? {NO_REPEAT_INSTRUCTION} State the answer number ({valid_range}) FIRST, "
            f"before any explanation. You may briefly explain your reasoning only after giving "
            f"the number.\n"
            f"{question}\n"
            f"{options_str}\n"
            f"Answer:"
        )
    return prompt, digit_labels


def build_sold_prompt_t3(text):
    return (
        f"Classify the following Sinhala text as either 'NOT' (not offensive) or 'OFF' "
        f"(offensive). {NO_REPEAT_INSTRUCTION} State \'NOT\' or \'OFF\' FIRST, before any "
        f"explanation. You may briefly explain your reasoning only after giving the label.\n"
        f"Text: {text}\n"
        f"Answer:"
    )


# ============================================================
# Dispatch
# ============================================================

def build_mcq_prompt(template, question, options, dataset_key, script, subject=None):
    if template == "T1_direct":
        return build_mcq_prompt_t1(question, options, subject=subject)
    if template == "T2_fewshot":
        return build_mcq_prompt_t2(question, options, dataset_key, script, subject=subject)
    if template == "T3_answer_first":
        return build_mcq_prompt_t3(question, options, subject=subject)
    raise ValueError(f"Unknown template: {template}")


def build_sold_prompt(template, text, script):
    if template == "T1_direct":
        return build_sold_prompt_t1(text)
    if template == "T2_fewshot":
        return build_sold_prompt_t2(text, script)
    if template == "T3_answer_first":
        return build_sold_prompt_t3(text)
    raise ValueError(f"Unknown template: {template}")


print("Prompt template builders defined.")
print("\n--- Sample T1 MMLU ---")
p, d = build_mcq_prompt("T1_direct", "Sample question?", ["opt1", "opt2", "opt3", "opt4"],
                         "sinhala_mmlu", "unicode", subject="Social_Science")
print(p)
print("\n--- Sample T2 PIQA ---")
p, d = build_mcq_prompt("T2_fewshot", "Sample question?", ["opt1", "opt2"],
                         "global_piqa", "unicode")
print(p)
print("\n--- Sample T3 SOLD ---")
print(build_sold_prompt("T3_answer_first", "Sample text", "unicode"))

# %% [markdown]
# ## 6. Label Extraction
# Unchanged from `extrinsic-evaluation.ipynb` — the extractor is not part of what is being
# tested here; only the prompt text varies between templates.

# %%
def _extract_token(generated_text, valid_tokens, keyword_pattern):
    """Shared boundary-safe extractor for digit tokens ("1".."4") and word tokens
    ("NOT"/"OFF")."""
    if not generated_text:
        return "INVALID"
    text = generated_text.strip()
    pattern_tokens = "|".join(re.escape(t) for t in valid_tokens)
    is_digit = valid_tokens and valid_tokens[0].isdigit()
    boundary = r"(?<!\d)" if is_digit else r"\b"
    end_boundary = r"(?!\d)" if is_digit else r"\b"

    prefix_match = re.match(
        rf"^(?:(?:the\s+)?(?:{keyword_pattern})\s*(?:is|=|:)?\s*)?"
        rf"[\*\(#\[\s]*{boundary}({pattern_tokens}){end_boundary}",
        text, re.IGNORECASE
    )
    if prefix_match:
        return prefix_match.group(1).upper()

    body_match = re.search(
        rf"(?:(?:the\s+)?(?:{keyword_pattern})\s*(?:is|=|:)?\s*)"
        rf"[\*\(#\[\s]*{boundary}({pattern_tokens}){end_boundary}",
        text, re.IGNORECASE
    )
    if body_match:
        return body_match.group(1).upper()

    standalone_match = re.search(rf"{boundary}({pattern_tokens}){end_boundary}", text, re.IGNORECASE)
    if standalone_match:
        return standalone_match.group(1).upper()

    return "INVALID"


def extract_mcq_choice(generated_text, digit_labels):
    return _extract_token(generated_text, digit_labels, r"correct\s+answer|answer|option|choice")


def digit_to_letter(digit):
    if digit.isdigit() and 1 <= int(digit) <= 26:
        return chr(64 + int(digit))
    return digit


def extract_sold_label(generated_text):
    return _extract_token(generated_text, ["NOT", "OFF"], "label|answer|classification")


print("Extraction functions defined.")

# %% [markdown]
# ## 7. Generation Engine
# `REASONING_MODE` is the one per-model decoding-config switch: `"none"` (no chat-template
# change), `"no_think"` (SmolLM3-style `/no_think` system message), or
# `"enable_thinking_false"` (Qwen3.5-style kwarg). It is set once in each model's config
# cell and applied identically across every template and script condition for that model.

# %%
@torch.inference_mode()
def generate_response(prompt, reasoning_mode="none", max_new_tokens=MAX_NEW_TOKENS,
                       temperature=TEMPERATURE):
    """Generate a response from the instruct model given a plain-text prompt."""
    has_template = hasattr(tokenizer, "apply_chat_template") and getattr(tokenizer, "chat_template", None)

    if has_template:
        if reasoning_mode == "no_think":
            messages = [
                {"role": "system", "content": "/no_think"},
                {"role": "user", "content": prompt},
            ]
            formatted_prompt = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        elif reasoning_mode == "enable_thinking_false":
            messages = [{"role": "user", "content": prompt}]
            formatted_prompt = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
            )
        else:
            messages = [{"role": "user", "content": prompt}]
            formatted_prompt = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
    else:
        formatted_prompt = prompt

    device = next(model.parameters()).device
    inputs = tokenizer(
        formatted_prompt, return_tensors="pt", truncation=True, max_length=MAX_INPUT_TOKENS
    ).to(device)
    input_len = inputs["input_ids"].shape[1]

    gen_kwargs = {
        "max_new_tokens": max_new_tokens,
        "do_sample": temperature > 0,
        "pad_token_id": tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id,
    }
    if temperature > 0:
        gen_kwargs["temperature"] = temperature

    outputs = model.generate(**inputs, **gen_kwargs)
    generated_ids = outputs[0][input_len:]
    generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)
    return generated_text, input_len, len(generated_ids)

print("Generation engine defined.")

# %% [markdown]
# ## 8. Unified Evaluation Function
# Runs all 3 templates x 2 script conditions x 3 datasets x 20 items for one loaded model.
# Saves per-row raw output to `RAW_DIR` and a per-model summary (with the best template per
# dataset for this model) to `SUMMARY_DIR`.

# %%
def _metrics(rows):
    """invalid_rate, accuracy_among_valid, overall_accuracy for a list of row dicts."""
    n = len(rows)
    if n == 0:
        return {"n": 0, "invalid_rate": float("nan"), "accuracy_among_valid": float("nan"),
                "overall_accuracy": float("nan")}
    n_invalid = sum(1 for r in rows if r["pred"] == "INVALID")
    n_valid = n - n_invalid
    n_correct = sum(1 for r in rows if r["correct"] == 1)
    invalid_rate = n_invalid / n
    accuracy_among_valid = (n_correct / n_valid) if n_valid > 0 else float("nan")
    overall_accuracy = n_correct / n   # INVALID counted as wrong
    return {"n": n, "invalid_rate": invalid_rate,
            "accuracy_among_valid": accuracy_among_valid, "overall_accuracy": overall_accuracy}


def run_prompt_pilot(model_label, reasoning_mode):
    """Evaluate the currently-loaded `model`/`tokenizer` across all templates, scripts,
    and mini datasets. Returns (raw_df, summary_df, best_template_by_dataset)."""
    raw_rows = []
    t0 = time.time()

    for dataset_key, items in MINI_DATASETS.items():
        task = items[0]["task"]
        for template in TEMPLATES:
            for item in items:
                strata = item.get("strata", {})
                subject = strata.get("domain") if dataset_key == "sinhala_mmlu" else None
                for script in SCRIPTS:
                    s = item[script]
                    if task == "mcq":
                        prompt, digits = build_mcq_prompt(
                            template, s["text"], s["options"], dataset_key, script, subject=subject
                        )
                    else:
                        prompt = build_sold_prompt(template, s["text"], script)

                    gen_text, n_in, n_out = generate_response(prompt, reasoning_mode=reasoning_mode)

                    if task == "mcq":
                        pred_digit = extract_mcq_choice(gen_text, digits)
                        pred_label = digit_to_letter(pred_digit)
                        correct = int(pred_label == item["label"])
                        pred_for_metrics = pred_digit
                    else:
                        pred_label = extract_sold_label(gen_text)
                        correct = int(pred_label == item["label"])
                        pred_for_metrics = pred_label

                    raw_rows.append({
                        "model": model_label, "dataset": dataset_key, "template": template,
                        "script": script, "id": item["id"], "gold_label": item["label"],
                        "pred": pred_for_metrics, "pred_label": pred_label, "correct": correct,
                        "raw_output": gen_text.strip()[:200],
                        "n_input_tokens": n_in, "n_output_tokens": n_out,
                    })

    elapsed = time.time() - t0
    raw_df = pd.DataFrame(raw_rows)
    raw_path = RAW_DIR / f"{model_label}_prompt_pilot_raw.csv"
    raw_df.to_csv(raw_path, index=False, encoding="utf-8-sig")

    summary_records = []
    best_template_by_dataset = {}
    for dataset_key in MINI_DATASETS:
        best_acc, best_template = -1.0, None
        for template in TEMPLATES:
            rows = [r for r in raw_rows if r["dataset"] == dataset_key and r["template"] == template]
            m = _metrics(rows)
            summary_records.append({"model": model_label, "dataset": dataset_key,
                                     "template": template, **m})
            if m["overall_accuracy"] > best_acc:
                best_acc, best_template = m["overall_accuracy"], template
        best_template_by_dataset[dataset_key] = best_template

    summary_df = pd.DataFrame(summary_records)
    summary_path = SUMMARY_DIR / f"{model_label}_prompt_pilot_summary.csv"
    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")

    print(f"\n{'='*78}\n{model_label} — prompt pilot ({elapsed/60:.1f} min, "
          f"{len(raw_rows)} generations)\n{'='*78}")
    for dataset_key in MINI_DATASETS:
        sub = summary_df[summary_df["dataset"] == dataset_key]
        print(f"\n{dataset_key}:")
        print(sub[["template", "n", "invalid_rate", "accuracy_among_valid",
                    "overall_accuracy"]].to_string(index=False, float_format=lambda x: f"{x:.3f}"))
        print(f"  -> best template for this model: {best_template_by_dataset[dataset_key]}")

    print(f"\nSaved: {raw_path.relative_to(OUTPUT_DIR)}")
    print(f"Saved: {summary_path.relative_to(OUTPUT_DIR)}")
    return raw_df, summary_df, best_template_by_dataset

print("run_prompt_pilot() defined.")

# %% [markdown]
# ## 9. Per-Model Evaluation
# One load / run / cleanup group per model, 11 in total. `REASONING_MODE` is the only
# setting that differs from the "default" pattern, and only for the 3 models that default
# to chain-of-thought output. Everything else (prompt templates, extractor, metrics) is
# identical across all 11.

# %%
# ============================================================
# EVALUATION LOOP
# ============================================================
MODELS_TO_EVALUATE = [
    {"id": "microsoft/phi-4", "label": "Phi-4", "reasoning_mode": "none"},
    {"id": "mann-e/Hormoz-8B", "label": "Hormoz-8B", "reasoning_mode": "none"},
    {"id": "HuggingFaceTB/SmolLM3-3B", "label": "SmolLM3-3B", "reasoning_mode": "no_think"},
    {"id": "HuggingFaceH4/zephyr-7b-beta", "label": "zephyr-7b-beta", "reasoning_mode": "none"},
    {"id": "stabilityai/stablelm-zephyr-3b", "label": "stablelm-zephyr-3b", "reasoning_mode": "none"},
    {"id": "MBZUAI/LaMini-GPT-1.5B", "label": "LaMini-GPT-1.5B", "reasoning_mode": "none"},
    {"id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0", "label": "TinyLlama-1.1B-Chat-v1.0", "reasoning_mode": "none"},
    {"id": "Qwen/Qwen3.5-4B", "label": "Qwen-3.5-4B", "reasoning_mode": "enable_thinking_false"},
    {"id": "Qwen/Qwen3.5-9B", "label": "Qwen-3.5-9B", "reasoning_mode": "enable_thinking_false"},
    {"id": "meta-llama/Llama-3.1-8B-Instruct", "label": "Llama-3.1-8B-Instruct", "reasoning_mode": "none"},
    {"id": "Qwen/Qwen2-7B-Instruct", "label": "Qwen2-7B-Instruct", "reasoning_mode": "none"},
]

for model_cfg in MODELS_TO_EVALUATE:
    MODEL_ID = model_cfg["id"]
    MODEL_LABEL = model_cfg["label"]
    REASONING_MODE = model_cfg["reasoning_mode"]
    
    expected_raw_path = RAW_DIR / f"{MODEL_LABEL}_prompt_pilot_raw.csv"
    expected_summary_path = SUMMARY_DIR / f"{MODEL_LABEL}_prompt_pilot_summary.csv"
    
    if expected_raw_path.exists() and expected_summary_path.exists():
        print(f"\nSkipping {MODEL_LABEL}, already evaluated.")
        continue

    print(f"\n{'='*78}\nEvaluating {MODEL_ID}...\n{'='*78}")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_ID, token=HF_TOKEN if HF_TOKEN else None, trust_remote_code=True
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        has_template = hasattr(tokenizer, "chat_template") and tokenizer.chat_template is not None
        print(f"Chat template available: {has_template}")
        if not has_template and REASONING_MODE != "none":
            print(f"WARNING: REASONING_MODE={REASONING_MODE!r} but this model has no chat "
                  f"template - the setting will have no effect.")
        
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            device_map="auto",
            torch_dtype=torch.float16,
            token=HF_TOKEN if HF_TOKEN else None,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )
        model.eval()
        model.config.use_cache = True
        
        print("Model loaded.")
        print(f"Precision: {model.dtype}")
        if hasattr(model, "hf_device_map"):
            print(f"Device map: {model.hf_device_map}")
            
        # Quick sanity check
        _sample_item = MINI_DATASETS["sinhala_mmlu"][0]
        _sample_prompt, _ = build_mcq_prompt(
            "T1_direct", _sample_item["unicode"]["text"], _sample_item["unicode"]["options"],
            "sinhala_mmlu", "unicode", subject=_sample_item.get("strata", {}).get("domain")
        )
        _sample_out, _, _ = generate_response(_sample_prompt, reasoning_mode=REASONING_MODE)
        print(f"Sample output ({MODEL_LABEL}, REASONING_MODE={REASONING_MODE!r}):")
        print(repr(_sample_out[:150]))
        if REASONING_MODE != "none" and "<think>" in _sample_out.lower():
            print("WARNING: <think> still present - the suppression flag did not take effect "
                  "for this model/transformers version. Investigate before trusting this model's "
                  "pilot results.")
                  
        _ = run_prompt_pilot(MODEL_LABEL, REASONING_MODE)
        
    except Exception as e:
        print(f"ERROR during evaluation of {MODEL_ID}: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Free GPU memory before loading the next model
        if 'model' in locals():
            del model
        if 'tokenizer' in locals():
            del tokenizer
        gc.collect()
        torch.cuda.empty_cache()
        print("Memory freed. Ready for the next model.")

# %% [markdown]
# ## 10. Cross-Model Aggregation and Final Template Recommendation
# Pools every model's raw generations (all 11, both script conditions, all 20 items per
# dataset) and picks, per dataset, the template with the highest pooled `overall_accuracy`.
# Also reports the per-model breakdown so a template that wins on average but fails badly
# for a specific model doesn't go unnoticed.

# %%
raw_paths = sorted(RAW_DIR.glob("*_prompt_pilot_raw.csv"))
print(f"Found {len(raw_paths)} per-model raw result files:")
for p in raw_paths:
    print(f"  {p.name}")

if not raw_paths:
    print("No raw files found for any model. Exiting cross-model aggregation.")
    import sys
    sys.exit(0)

all_raw = pd.concat([pd.read_csv(p, encoding="utf-8-sig") for p in raw_paths], ignore_index=True)
print(f"\nTotal pooled generations: {len(all_raw):,}")

# %%
def pooled_metrics(df):
    n = len(df)
    n_invalid = (df["pred"] == "INVALID").sum()
    n_correct = df["correct"].sum()
    n_valid = n - n_invalid
    return pd.Series({
        "n": n,
        "invalid_rate": n_invalid / n if n else float("nan"),
        "accuracy_among_valid": (n_correct / n_valid) if n_valid else float("nan"),
        "overall_accuracy": (n_correct / n) if n else float("nan"),
    })


pooled = (
    all_raw.groupby(["dataset", "template"])
    .apply(pooled_metrics, include_groups=False)
    .reset_index()
)

print("Pooled metrics (all models, both scripts):")
print(pooled.to_string(index=False, float_format=lambda x: f"{x:.3f}"))

# %%
best_template_per_dataset = {}
for dataset_key in pooled["dataset"].unique():
    sub = pooled[pooled["dataset"] == dataset_key]
    winner = sub.loc[sub["overall_accuracy"].idxmax(), "template"]
    best_template_per_dataset[dataset_key] = winner

print("\nRecommended template per dataset (pooled overall_accuracy):")
for dataset_key, template in best_template_per_dataset.items():
    print(f"  {dataset_key:14} -> {template}")

# %%
# Per-model breakdown for the recommended template per dataset - diagnostic only, to
# check the winner is not carried by one or two strong models.
per_model = (
    all_raw.groupby(["dataset", "template", "model"])
    .apply(pooled_metrics, include_groups=False)
    .reset_index()
)

for dataset_key, template in best_template_per_dataset.items():
    print(f"\n{dataset_key} / {template} - per-model overall_accuracy:")
    sub = per_model[(per_model["dataset"] == dataset_key) & (per_model["template"] == template)]
    print(sub[["model", "n", "invalid_rate", "overall_accuracy"]]
          .sort_values("overall_accuracy")
          .to_string(index=False, float_format=lambda x: f"{x:.3f}"))

# %%
# Save final artifacts.
pooled_path = OUTPUT_DIR / "pooled_template_metrics.csv"
per_model_path = OUTPUT_DIR / "per_model_template_metrics.csv"
recommendation_path = OUTPUT_DIR / "final_template_recommendation.csv"

pooled.to_csv(pooled_path, index=False, encoding="utf-8-sig")
per_model.to_csv(per_model_path, index=False, encoding="utf-8-sig")
pd.DataFrame(
    [{"dataset": k, "recommended_template": v} for k, v in best_template_per_dataset.items()]
).to_csv(recommendation_path, index=False, encoding="utf-8-sig")

print("Saved:")
print(f"  {pooled_path}")
print(f"  {per_model_path}")
print(f"  {recommendation_path}")
print("\nPrompt template selection complete.")


