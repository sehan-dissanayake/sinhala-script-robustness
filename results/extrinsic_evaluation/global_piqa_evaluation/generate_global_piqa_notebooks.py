"""
Generate one Global PIQA evaluation notebook per model under:
  results/extrinsic_evaluation/global_piqa_evaluation/<model_label>/
  global_piqa_eval-<model_label>.ipynb

Key difference from the standard extrinsic evaluation notebooks:
  - Evaluates ONLY the global_piqa dataset (no MMLU, no SOLD).
  - T1_direct prompt is isQnA-aware:
      * isQnA=True  -> MCQ format with domain="Sri Lankan Culture"
      * isQnA=False -> paragraph-completion format (no domain/subject)
"""

import json
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# MODEL REGISTRY  (mirrors generate_model_notebooks.py)
# ---------------------------------------------------------------------------
MODELS = [
    {
        "id": "mann-e/Hormoz-8B",
        "label": "Hormoz-8B",
        "reasoning_mode": "none",
        "load_in_8bit": False,
        "prompt_template": "T1_direct",
    },
    {
        "id": "HuggingFaceTB/SmolLM3-3B",
        "label": "SmolLM3-3B",
        "reasoning_mode": "no_think",
        "load_in_8bit": False,
        "prompt_template": "T1_direct",
    },
    {
        "id": "HuggingFaceH4/zephyr-7b-beta",
        "label": "zephyr-7b-beta",
        "reasoning_mode": "none",
        "load_in_8bit": False,
        "prompt_template": "T1_direct",
    },
    {
        "id": "stabilityai/stablelm-zephyr-3b",
        "label": "stablelm-zephyr-3b",
        "reasoning_mode": "none",
        "load_in_8bit": False,
        "prompt_template": "T1_direct",
    },
    {
        "id": "MBZUAI/LaMini-GPT-1.5B",
        "label": "LaMini-GPT-1.5B",
        "reasoning_mode": "none",
        "load_in_8bit": False,
        "prompt_template": "T1_direct",
    },
    {
        "id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "label": "TinyLlama-1.1B-Chat-v1.0",
        "reasoning_mode": "none",
        "load_in_8bit": False,
        "prompt_template": "T1_direct",
    },
    {
        "id": "Qwen/Qwen3.5-4B",
        "label": "Qwen-3.5-4B",
        "reasoning_mode": "enable_thinking_false",
        "load_in_8bit": False,
        "prompt_template": "T1_direct",
    },
    {
        "id": "Qwen/Qwen3.5-9B",
        "label": "Qwen-3.5-9B",
        "reasoning_mode": "enable_thinking_false",
        "load_in_8bit": False,
        "prompt_template": "T1_direct",
    },
    {
        "id": "meta-llama/Llama-3.1-8B-Instruct",
        "label": "Llama-3.1-8B-Instruct",
        "reasoning_mode": "none",
        "load_in_8bit": False,
        "prompt_template": "T1_direct",
    },
    {
        "id": "Qwen/Qwen2-7B-Instruct",
        "label": "Qwen2-7B-Instruct",
        "reasoning_mode": "none",
        "load_in_8bit": False,
        "prompt_template": "T1_direct",
    },
    {
        "id": "microsoft/phi-4",
        "label": "Phi-4",
        "reasoning_mode": "none",
        "load_in_8bit": False,
        "prompt_template": "T1_direct",
    },
]

# ---------------------------------------------------------------------------
# NOTEBOOK CELL SOURCE BUILDERS
# ---------------------------------------------------------------------------

def cell_source_config(model):
    label = model["label"]
    model_id = model["id"]
    reasoning_mode = model["reasoning_mode"]
    load_in_8bit = model["load_in_8bit"]
    prompt_template = model["prompt_template"]
    return [
        "# ============================================================\n",
        "# MODEL CONFIGURATION\n",
        "# ============================================================\n",
        "\n",
        f'MODEL_ID    = "{model_id}"\n',
        f'MODEL_LABEL = "{label}"\n',
        f'PROMPT_TEMPLATE = "{prompt_template}"  # isQnA-aware T1_direct\n',
        "\n",
        "# Reasoning-mode flag\n",
        "# Options: \"none\" | \"no_think\" | \"enable_thinking_false\"\n",
        f'REASONING_MODE = "{reasoning_mode}"\n',
        "\n",
        "MAX_NEW_TOKENS   = 40\n",
        "TEMPERATURE      = 0.0\n",
        "MAX_INPUT_TOKENS = 4096\n",
        "\n",
        f"LOAD_IN_8BIT = {str(load_in_8bit)}\n",
        "RESUME       = True\n",
        "TIME_LIMIT_HOURS = 11.5\n",
        "\n",
        "# Dataset path (update if Kaggle dataset mount differs)\n",
        'DATA_DIR = "/kaggle/input/datasets/anon-owner-d/dataset3"\n',
        "\n",
        "import re\n",
        "OUTPUT_PREFIX = re.sub(r\"[^a-z0-9]+\", \"_\", MODEL_LABEL.lower()).strip(\"_\")\n",
        "\n",
        'print(f"Model:          {MODEL_ID}")\n',
        'print(f"Label:          {MODEL_LABEL}")\n',
        'print(f"Template:       {PROMPT_TEMPLATE} (isQnA-aware)")\n',
        'print(f"Reasoning mode: {REASONING_MODE}")\n',
        'print(f"8-bit:          {LOAD_IN_8BIT}")\n',
        'print(f"Resume:         {RESUME}")\n',
        'print(f"Time limit:     {TIME_LIMIT_HOURS} hours")\n',
        'print(f"Output:         {OUTPUT_PREFIX}_global_piqa.csv")',
    ]


def cell_source_env_setup():
    return [
        "import sys\n",
        "import os\n",
        "\n",
        "!{sys.executable} -m pip install --upgrade --quiet transformers accelerate huggingface_hub bitsandbytes\n",
        "\n",
        "import torch\n",
        "import json\n",
        "import csv\n",
        "import time\n",
        "import re\n",
        "import transformers\n",
        "from pathlib import Path\n",
        "from tqdm import tqdm\n",
        "from transformers import AutoModelForCausalLM, AutoTokenizer\n",
        "\n",
        "device_count = torch.cuda.device_count()\n",
        'print(f"PyTorch {torch.__version__} | transformers {transformers.__version__} | {device_count} GPU(s)")\n',
        "for i in range(device_count):\n",
        "    name = torch.cuda.get_device_name(i)\n",
        "    mem = torch.cuda.get_device_properties(i).total_memory / (1024**3)\n",
        '    print(f"  cuda:{i} -> {name} ({mem:.1f} GB)")\n',
        'assert device_count > 0, "No GPU detected. Enable GPU T4 x2 in Session options."',
    ]


def cell_source_auth():
    return [
        "from huggingface_hub import login\n",
        "\n",
        "try:\n",
        "    from kaggle_secrets import UserSecretsClient\n",
        "    user_secrets = UserSecretsClient()\n",
        '    HF_TOKEN = user_secrets.get_secret("HF_TOKEN")\n',
        "    login(token=HF_TOKEN)\n",
        '    print("Authenticated via Kaggle Secrets.")\n',
        "except Exception as e:\n",
        '    HF_TOKEN = ""   # Paste your token here if Kaggle Secrets is unavailable\n',
        "    if HF_TOKEN:\n",
        "        login(token=HF_TOKEN)\n",
        '        print("Authenticated via explicit token.")\n',
        "    else:\n",
        '        print(f"No HF_TOKEN found ({e}). Public models will still work.")',
    ]


def cell_source_load_model():
    return [
        'print(f"Loading {MODEL_ID}...")\n',
        "\n",
        "tokenizer = AutoTokenizer.from_pretrained(\n",
        "    MODEL_ID,\n",
        "    token=HF_TOKEN if HF_TOKEN else None,\n",
        "    trust_remote_code=True\n",
        ")\n",
        "if tokenizer.pad_token is None:\n",
        "    tokenizer.pad_token = tokenizer.eos_token\n",
        "\n",
        'has_template = hasattr(tokenizer, "chat_template") and tokenizer.chat_template is not None\n',
        'print(f"Chat template available: {has_template}")\n',
        "if not has_template:\n",
        '    print("WARNING: this model has no chat template. It will be prompted with raw text.")\n',
        'if not has_template and REASONING_MODE != "none":\n',
        '    print(f"WARNING: REASONING_MODE={REASONING_MODE!r} but no chat template -- setting has no effect.")\n',
        "\n",
        "model_kwargs = dict(\n",
        '    device_map="auto",\n',
        "    token=HF_TOKEN if HF_TOKEN else None,\n",
        "    trust_remote_code=True,\n",
        "    low_cpu_mem_usage=True,\n",
        ")\n",
        "if LOAD_IN_8BIT:\n",
        "    from transformers import BitsAndBytesConfig\n",
        '    model_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)\n',
        "else:\n",
        '    model_kwargs["torch_dtype"] = torch.float16\n',
        "\n",
        "model = AutoModelForCausalLM.from_pretrained(MODEL_ID, **model_kwargs)\n",
        "model.eval()\n",
        "model.config.use_cache = True\n",
        "\n",
        'print("Model loaded successfully.")\n',
        'print(f"Precision: {model.dtype}")\n',
        'if hasattr(model, "hf_device_map"):\n',
        '    print(f"Device map: {model.hf_device_map}")',
    ]


def cell_source_load_data():
    return [
        "def load_jsonl(filepath):\n",
        '    """Load a JSONL file into a list of dicts."""\n',
        "    data = []\n",
        '    with open(filepath, "r", encoding="utf-8") as f:\n',
        "        for line in f:\n",
        "            line = line.strip()\n",
        "            if line:\n",
        "                data.append(json.loads(line))\n",
        "    return data\n",
        "\n",
        'piqa_data = load_jsonl(os.path.join(DATA_DIR, "global_piqa.jsonl"))\n',
        "\n",
        'print(f"Global PIQA: {len(piqa_data):,} items")\n',
        "\n",
        "# isQnA distribution\n",
        'n_qna  = sum(1 for it in piqa_data if it.get("isQnA", False))\n',
        "n_comp = len(piqa_data) - n_qna\n",
        'print(f"  isQnA=True  (MCQ format):                  {n_qna:3d} items")\n',
        'print(f"  isQnA=False (paragraph-completion format): {n_comp:3d} items")',
    ]


def cell_source_prompts():
    return [
        "# ============================================================\n",
        "# isQnA-AWARE PROMPT BUILDER  (T1_direct, zero-shot)\n",
        "# ============================================================\n",
        "#\n",
        "#  isQnA=True  -> MCQ format with domain='Sri Lankan Culture'\n",
        "#  isQnA=False -> paragraph-completion format (no domain)\n",
        "\n",
        'NO_REPEAT_INSTRUCTION = "Do not repeat the question or text in your response."\n',
        'PIQA_DOMAIN = "Sri Lankan Culture"\n',
        "\n",
        "\n",
        "def _humanize_domain(domain):\n",
        "    return str(domain).replace(\"_\", \" \")\n",
        "\n",
        "\n",
        "def _mcq_options_block(options):\n",
        "    digit_labels = [str(i + 1) for i in range(len(options))]\n",
        '    options_str = "\\n".join(f"{d}. {opt}" for d, opt in zip(digit_labels, options))\n',
        "    return options_str, digit_labels\n",
        "\n",
        "\n",
        "def build_piqa_prompt(question, options, is_qna):\n",
        '    """Build a T1_direct prompt for a Global PIQA item.\n',
        "\n",
        "    Parameters\n",
        "    ----------\n",
        "    question : str  -- the Sinhala question / paragraph stem\n",
        "    options  : list -- answer option strings\n",
        "    is_qna   : bool -- True -> MCQ w/ domain; False -> paragraph-completion\n",
        '    """\n',
        "    options_str, digit_labels = _mcq_options_block(options)\n",
        "    n = len(options)\n",
        '    valid_range = "/".join(digit_labels)\n',
        "\n",
        "    if is_qna:\n",
        "        # MCQ format -- domain hint: Sri Lankan Culture\n",
        "        instruction = (\n",
        '            f"This is a multiple-choice question related to the {_humanize_domain(PIQA_DOMAIN)}. "\n',
        '            f"Choose the correct or most appropriate answer from answers {valid_range}. "\n',
        '            f"{NO_REPEAT_INSTRUCTION} Respond with only the number ({valid_range}) and nothing else."\n',
        "        )\n",
        "        prompt = (\n",
        '            f"{instruction}\\n"\n',
        '            f"Question: {question}\\n"\n',
        '            f"{options_str}\\n"\n',
        '            "Answer:"\n',
        "        )\n",
        "    else:\n",
        "        # Paragraph-completion format -- with Sri Lankan Culture domain\n",
        "        instruction = (\n",
        '            f"This is related to the {_humanize_domain(PIQA_DOMAIN)}. "\n',
        '            f"Out of the given {n} answers, which one is the best option to complete the given text? "\n',
        '            f"{NO_REPEAT_INSTRUCTION} Respond with only the number ({valid_range}) and nothing else."\n',
        "        )\n",
        "        prompt = (\n",
        '            f"{instruction}\\n"\n',
        '            f"{question}\\n"\n',
        '            f"{options_str}\\n"\n',
        '            "Answer:"\n',
        "        )\n",
        "\n",
        "    return prompt, digit_labels\n",
        "\n",
        "\n",
        "# ============================================================\n",
        "# LABEL EXTRACTION\n",
        "# ============================================================\n",
        "\n",
        "def _extract_token(generated_text, valid_tokens, keyword_pattern):\n",
        '    """Boundary-safe extractor for digit tokens."""\n',
        "    if not generated_text:\n",
        '        return "INVALID"\n',
        "    text = generated_text.strip()\n",
        '    pattern_tokens = "|".join(re.escape(t) for t in valid_tokens)\n',
        "    is_digit = valid_tokens and valid_tokens[0].isdigit()\n",
        '    boundary     = r"(?<!\\d)" if is_digit else r"\\b"\n',
        '    end_boundary = r"(?!\\d)"  if is_digit else r"\\b"\n',
        "\n",
        "    prefix_match = re.match(\n",
        '        rf"^(?:(?:the\\s+)?(?:{keyword_pattern})\\s*(?:is|=|:)?\\s*)?"\n',
        '        rf"[\\*\\(#\\[\\s]*{boundary}({pattern_tokens}){end_boundary}",\n',
        "        text, re.IGNORECASE\n",
        "    )\n",
        "    if prefix_match:\n",
        "        return prefix_match.group(1).upper()\n",
        "\n",
        "    body_match = re.search(\n",
        '        rf"(?:(?:the\\s+)?(?:{keyword_pattern})\\s*(?:is|=|:)?\\s*)"\n',
        '        rf"[\\*\\(#\\[\\s]*{boundary}({pattern_tokens}){end_boundary}",\n',
        "        text, re.IGNORECASE\n",
        "    )\n",
        "    if body_match:\n",
        "        return body_match.group(1).upper()\n",
        "\n",
        "    standalone = re.search(rf\"{boundary}({pattern_tokens}){end_boundary}\", text, re.IGNORECASE)\n",
        "    if standalone:\n",
        "        return standalone.group(1).upper()\n",
        "\n",
        '    return "INVALID"\n',
        "\n",
        "\n",
        "def extract_mcq_choice(generated_text, digit_labels):\n",
        '    return _extract_token(generated_text, digit_labels, r"correct\\s+answer|answer|option|choice")\n',
        "\n",
        "\n",
        "def digit_to_letter(digit):\n",
        '    """1->A, 2->B, ... INVALID passes through."""\n',
        "    if digit.isdigit() and 1 <= int(digit) <= 26:\n",
        "        return chr(64 + int(digit))\n",
        "    return digit\n",
        "\n",
        "\n",
        'print("isQnA-aware prompt builder and label extractors defined.")\n',
        "\n",
        "# Sanity-check both branches\n",
        'p_qna, d = build_piqa_prompt("Sample question?", ["opt1", "opt2"], is_qna=True)\n',
        'print(f"\\n--- Sample isQnA=True Prompt ---\\n{p_qna}")\n',
        'p_comp, d = build_piqa_prompt("Sample text stem,", ["opt1", "opt2"], is_qna=False)\n',
        'print(f"\\n--- Sample isQnA=False Prompt ---\\n{p_comp}")',
    ]


def cell_source_generation_engine(model):
    return [
        "@torch.inference_mode()\n",
        "def generate_response(prompt, max_new_tokens=MAX_NEW_TOKENS, temperature=TEMPERATURE):\n",
        '    """Generate a response from the instruct model."""\n',
        '    has_template = hasattr(tokenizer, "apply_chat_template") and getattr(tokenizer, "chat_template", None)\n',
        "    try:\n",
        "        if has_template:\n",
        '            if REASONING_MODE == "no_think":\n',
        "                messages = [\n",
        '                    {"role": "system", "content": "/no_think"},\n',
        '                    {"role": "user",   "content": prompt},\n',
        "                ]\n",
        "                formatted_prompt = tokenizer.apply_chat_template(\n",
        "                    messages, tokenize=False, add_generation_prompt=True\n",
        "                )\n",
        '            elif REASONING_MODE == "enable_thinking_false":\n',
        '                messages = [{"role": "user", "content": prompt}]\n',
        "                formatted_prompt = tokenizer.apply_chat_template(\n",
        "                    messages, tokenize=False, add_generation_prompt=True, enable_thinking=False\n",
        "                )\n",
        "            else:  # 'none' -- standard\n",
        '                messages = [{"role": "user", "content": prompt}]\n',
        "                formatted_prompt = tokenizer.apply_chat_template(\n",
        "                    messages, tokenize=False, add_generation_prompt=True\n",
        "                )\n",
        "        else:\n",
        "            formatted_prompt = prompt\n",
        "\n",
        "        device = next(model.parameters()).device\n",
        "        inputs = tokenizer(\n",
        "            formatted_prompt, return_tensors=\"pt\", truncation=True, max_length=MAX_INPUT_TOKENS\n",
        "        ).to(device)\n",
        '        input_len = inputs["input_ids"].shape[1]\n',
        "\n",
        "        gen_kwargs = {\n",
        '            "max_new_tokens": max_new_tokens,\n',
        '            "do_sample": temperature > 0,\n',
        '            "pad_token_id": tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id,\n',
        "        }\n",
        "        if temperature > 0:\n",
        '            gen_kwargs["temperature"] = temperature\n',
        "\n",
        "        outputs = model.generate(**inputs, **gen_kwargs)\n",
        "        generated_ids = outputs[0][input_len:]\n",
        "        generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)\n",
        "        return generated_text, input_len, len(generated_ids)\n",
        "    except Exception as e:\n",
        "        torch.cuda.empty_cache()\n",
        '        print(f"\\n[WARNING] Generation error: {e}")\n',
        '        return f"ERROR: {e}", 0, 0\n',
        "\n",
        "\n",
        'print(f"Generation engine initialized. REASONING_MODE = {REASONING_MODE!r}")\n',
        "\n",
        "# Quick sanity-check\n",
        '_sp, _ = build_piqa_prompt("Sample question?", ["opt1", "opt2"], is_qna=True)\n',
        "_so, _, _ = generate_response(_sp)\n",
        'print(f"Sample output (isQnA=True):  {repr(_so[:100])}")\n',
        '_sp2, _ = build_piqa_prompt("Sample text stem,", ["opt1", "opt2"], is_qna=False)\n',
        "_so2, _, _ = generate_response(_sp2)\n",
        'print(f"Sample output (isQnA=False): {repr(_so2[:100])}")\n',
        'if REASONING_MODE != "none" and "<think>" in (_so + _so2).lower():\n',
        '    print("WARNING: <think> block still present -- suppression flag did not take effect.")',
    ]


def cell_source_pilot():
    return [
        'print("=" * 75)\n',
        'print("PILOT RUN -- 5 items  (mix of isQnA=True and isQnA=False)")\n',
        'print(f"Prompt template: T1_direct (isQnA-aware)")\n',
        'print(f"Reasoning mode:  {REASONING_MODE}")\n',
        'print("=" * 75)\n',
        "\n",
        "for item in piqa_data[:5]:\n",
        '    for script in ["unicode", "romanized"]:\n',
        "        s = item[script]\n",
        '        is_qna = item.get("isQnA", False)\n',
        "        prompt, digits = build_piqa_prompt(s[\"text\"], s[\"options\"], is_qna=is_qna)\n",
        "        gen_text, n_in, n_out = generate_response(prompt)\n",
        "        pred_digit = extract_mcq_choice(gen_text, digits)\n",
        "        pred_label = digit_to_letter(pred_digit)\n",
        '        correct = "\\u2713" if pred_label == item["label"] else "\\u2717"\n',
        '        fmt = "MCQ " if is_qna else "COMP"\n',
        '        print(f"  [{script:9}] [{fmt}] id={item[\'id\']} | gold={item[\'label\']} pred={pred_digit}->{pred_label} {correct} | raw={gen_text[:60]!r}")\n',
        "\n",
        'print("\\n" + "=" * 75)\n',
        'print("Pilot complete. Check output above before running Section 10.")\n',
        'print("=" * 75)',
    ]


def cell_source_evaluation_runner():
    return [
        "MCQ_FIELDNAMES = [\n",
        '    "id", "gold_label", "is_qna",\n',
        '    "unicode_pred_digit", "unicode_pred_label", "unicode_correct", "unicode_raw_output",\n',
        '    "unicode_n_input_tokens", "unicode_n_output_tokens",\n',
        '    "romanized_pred_digit", "romanized_pred_label", "romanized_correct", "romanized_raw_output",\n',
        '    "romanized_n_input_tokens", "romanized_n_output_tokens",\n',
        "]\n",
        "\n",
        "GLOBAL_START_TIME = time.time()\n",
        "\n",
        "def _check_time_limit():\n",
        "    return (time.time() - GLOBAL_START_TIME) / 3600.0 >= TIME_LIMIT_HOURS\n",
        "\n",
        "\n",
        "def _find_checkpoint_file(filename):\n",
        "    if os.path.exists(filename) and os.path.getsize(filename) > 0:\n",
        "        return filename\n",
        '    input_base = "/kaggle/input"\n',
        "    if os.path.exists(input_base):\n",
        "        for root, _, files in os.walk(input_base):\n",
        "            if filename in files:\n",
        "                candidate = os.path.join(root, filename)\n",
        "                if os.path.getsize(candidate) > 0:\n",
        "                    return candidate\n",
        "    return None\n",
        "\n",
        "\n",
        "def _load_existing_progress(output_csv, fieldnames):\n",
        "    if not RESUME:\n",
        "        return set()\n",
        "    src = _find_checkpoint_file(output_csv)\n",
        "    if not src:\n",
        "        return set()\n",
        "    done_ids, rows = set(), []\n",
        "    try:\n",
        '        with open(src, "r", newline="", encoding="utf-8-sig") as f:\n',
        "            reader = csv.DictReader(f)\n",
        "            for r in reader:\n",
        '                if "id" in r and r["id"]:\n',
        '                    done_ids.add(r["id"])\n',
        "                    rows.append(r)\n",
        "        if src != output_csv and rows:\n",
        '            with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:\n',
        "                writer = csv.DictWriter(f, fieldnames=fieldnames)\n",
        "                writer.writeheader()\n",
        "                for r in rows:\n",
        "                    writer.writerow({k: r.get(k, \"\") for k in fieldnames})\n",
        "                f.flush()\n",
        '            print(f"[RESUME] Loaded {len(done_ids):,} records from {src} -> {output_csv}")\n',
        "        elif src == output_csv:\n",
        '            print(f"[RESUME] Found existing {output_csv} with {len(done_ids):,} records")\n',
        "    except Exception as e:\n",
        '        print(f"[WARNING] Could not read checkpoint from {src}: {e}")\n',
        "        return set()\n",
        "    return done_ids\n",
        "\n",
        "\n",
        "def run_piqa_evaluation(dataset, output_csv):\n",
        '    """Run isQnA-aware Global PIQA evaluation on both script conditions."""\n',
        "    done_ids = _load_existing_progress(output_csv, MCQ_FIELDNAMES)\n",
        '    mode = "a" if (os.path.exists(output_csv) and os.path.getsize(output_csv) > 0) else "w"\n',
        "\n",
        "    print(f\"\\n{'='*65}\")\n",
        '    print(f"Evaluating: Global PIQA (isQnA-aware) ({len(dataset):,} items, {len(done_ids):,} already done)")\n',
        '    print(f"Output:     {output_csv}")\n',
        "    print(f\"{'='*65}\")\n",
        "\n",
        "    remaining = [it for it in dataset if it[\"id\"] not in done_ids]\n",
        "    if not remaining:\n",
        '        print(f"All {len(dataset):,} items already completed.")\n',
        "        return output_csv\n",
        "\n",
        '    with open(output_csv, mode=mode, newline="", encoding="utf-8-sig") as f:\n',
        "        writer = csv.DictWriter(f, fieldnames=MCQ_FIELDNAMES)\n",
        '        if mode == "w":\n',
        "            writer.writeheader()\n",
        "            f.flush()\n",
        "\n",
        "        t0 = time.time()\n",
        "        n_processed = 0\n",
        "\n",
        '        for i, item in enumerate(tqdm(remaining, desc="Global PIQA")):\n',
        "            if _check_time_limit():\n",
        "                elapsed_h = (time.time() - GLOBAL_START_TIME) / 3600.0\n",
        '                print(f"\\n[TIME LIMIT GUARD] Elapsed: {elapsed_h:.2f}h >= {TIME_LIMIT_HOURS}h. Saving and exiting.")\n',
        "                break\n",
        "\n",
        '            is_qna = item.get("isQnA", False)\n',
        '            row = {"id": item["id"], "gold_label": item["label"], "is_qna": is_qna}\n',
        "\n",
        '            for script in ["unicode", "romanized"]:\n',
        "                s = item[script]\n",
        "                prompt, digits = build_piqa_prompt(s[\"text\"], s[\"options\"], is_qna=is_qna)\n",
        "                gen_text, n_in, n_out = generate_response(prompt)\n",
        "                pred_digit = extract_mcq_choice(gen_text, digits)\n",
        "                pred_label = digit_to_letter(pred_digit)\n",
        '                correct = int(pred_label == item["label"])\n',
        '                row[f"{script}_pred_digit"]      = pred_digit\n',
        '                row[f"{script}_pred_label"]      = pred_label\n',
        '                row[f"{script}_correct"]         = correct\n',
        '                row[f"{script}_raw_output"]      = gen_text.strip()[:200]\n',
        '                row[f"{script}_n_input_tokens"]  = n_in\n',
        '                row[f"{script}_n_output_tokens"] = n_out\n',
        "\n",
        "            writer.writerow(row)\n",
        "            f.flush()\n",
        "            n_processed += 1\n",
        "\n",
        "        elapsed = time.time() - t0\n",
        "\n",
        "    if n_processed:\n",
        '        print(f"Done {n_processed:,} new items in {elapsed/60:.1f} min ({elapsed/n_processed:.2f} s/item)")\n',
        "    return output_csv\n",
        "\n",
        "\n",
        'print("Evaluation runner ready with continuous flushing, checkpointing, and time guard.")',
    ]


def cell_source_run_evaluation():
    return [
        "# ============================================================\n",
        "# RUN GLOBAL PIQA EVALUATION\n",
        "# ============================================================\n",
        "\n",
        "piqa_csv = run_piqa_evaluation(\n",
        '    piqa_data, f"{OUTPUT_PREFIX}_global_piqa.csv"\n',
        ")\n",
        "\n",
        'print("\\n" + "="*65)\n',
        'print("EVALUATION FINISHED")\n',
        'print("="*65)',
    ]


def cell_source_summary():
    return [
        "import pandas as pd\n",
        "\n",
        "def summarize_piqa(csv_path):\n",
        "    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:\n",
        '        print("Global PIQA -- Not evaluated or file empty.")\n',
        "        return None\n",
        "    try:\n",
        "        df = pd.read_csv(csv_path)\n",
        "        n = len(df)\n",
        "        if n == 0:\n",
        '            print("Global PIQA n=0 (empty)")\n',
        "            return None\n",
        "\n",
        '        u_acc = df["unicode_correct"].mean() * 100\n',
        '        r_acc = df["romanized_correct"].mean() * 100\n',
        "        gap   = u_acc - r_acc\n",
        '        u_inv = (df["unicode_pred_label"] == "INVALID").mean() * 100\n',
        '        r_inv = (df["romanized_pred_label"] == "INVALID").mean() * 100\n',
        "\n",
        '        print(f"\\n{MODEL_LABEL} -- Global PIQA Evaluation (isQnA-aware T1_direct)")\n',
        '        print("-" * 80)\n',
        '        print(f"Overall  n={n:3d}  Unicode={u_acc:6.2f}%  Romanized={r_acc:6.2f}%  Gap={gap:+6.2f}pp"\n',
        '              f"  Invalid(U/R)={u_inv:.1f}%/{r_inv:.1f}%")\n',
        "\n",
        "        # Break down by isQnA\n",
        '        for qna_val, lbl in [(True, "isQnA=True  (MCQ) "), (False, "isQnA=False (COMP)")]:\n',
        '            sub = df[df["is_qna"] == qna_val]\n',
        "            if len(sub) == 0:\n",
        "                continue\n",
        '            su = sub["unicode_correct"].mean() * 100\n',
        '            sr = sub["romanized_correct"].mean() * 100\n',
        "            sg = su - sr\n",
        '            print(f"  {lbl}  n={len(sub):3d}  Unicode={su:6.2f}%  Romanized={sr:6.2f}%  Gap={sg:+6.2f}pp")\n',
        "\n",
        "        result = {\n",
        '            "Model":                  MODEL_LABEL,\n',
        '            "N":                      n,\n',
        '            "Unicode Acc (%)":         round(u_acc, 2),\n',
        '            "Romanized Acc (%)":       round(r_acc, 2),\n',
        '            "Gap (pp)":               round(gap, 2),\n',
        '            "Unicode Invalid (%)":    round(u_inv, 2),\n',
        '            "Romanized Invalid (%)":  round(r_inv, 2),\n',
        "        }\n",
        '        for qna_val, tag in [(True, "MCQ"), (False, "COMP")]:\n',
        '            sub = df[df["is_qna"] == qna_val]\n',
        "            if len(sub) > 0:\n",
        '                result[f"Unicode {tag} Acc (%)"]   = round(sub["unicode_correct"].mean() * 100, 2)\n',
        '                result[f"Romanized {tag} Acc (%)"] = round(sub["romanized_correct"].mean() * 100, 2)\n',
        "        return result\n",
        "    except Exception as e:\n",
        '        print(f"[WARNING] Could not summarize {csv_path}: {e}")\n',
        "        return None\n",
        "\n",
        "\n",
        "result = summarize_piqa(piqa_csv)\n",
        "if result:\n",
        '    summary_csv = f"{OUTPUT_PREFIX}_global_piqa_summary.csv"\n',
        "    pd.DataFrame([result]).to_csv(summary_csv, index=False)\n",
        '    print(f"\\nSummary saved to: {summary_csv}")\n',
        '    display(pd.DataFrame([result])) if "display" in globals() else print(pd.DataFrame([result]))',
    ]


def cell_source_output_listing():
    return [
        'print("Output files in working directory:")\n',
        "for fpath in [piqa_csv]:\n",
        "    if os.path.exists(fpath):\n",
        "        size = os.path.getsize(fpath) / 1024\n",
        '        print(f"  {fpath} ({size:.1f} KB)")\n',
        "    else:\n",
        '        print(f"  {fpath} (not created yet)")\n',
        "\n",
        'summary_file = f"{OUTPUT_PREFIX}_global_piqa_summary.csv"\n',
        "if os.path.exists(summary_file):\n",
        "    size = os.path.getsize(summary_file) / 1024\n",
        '    print(f"  {summary_file} ({size:.1f} KB)")\n',
        "\n",
        'print(f"\\n\\u2705 {MODEL_LABEL} Global PIQA (isQnA-aware) evaluation complete!")',
    ]


# ---------------------------------------------------------------------------
# NOTEBOOK ASSEMBLER
# ---------------------------------------------------------------------------

def make_cell(cell_type, source, cell_id):
    if cell_type == "markdown":
        return {
            "cell_type": "markdown",
            "id": cell_id,
            "metadata": {},
            "source": source,
        }
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": cell_id,
        "metadata": {},
        "outputs": [],
        "source": source,
    }


def build_notebook(model):
    label = model["label"]
    reasoning_note = model["reasoning_mode"]

    cells = [
        make_cell("markdown", [
            f"# Global PIQA Evaluation (isQnA-aware) — {label}\n",
            "## Sinhala Script Robustness — Unicode vs Romanized\n",
            "\n",
            f"**Model:** `{model['id']}`  \n",
            f"**Prompt template:** `T1_direct` (isQnA-aware)  \n",
            f"**Reasoning mode:** `{reasoning_note}`  \n",
            f"**8-bit quantization:** `{model['load_in_8bit']}`\n",
            "\n",
            "### isQnA-aware prompting\n",
            "\n",
            "The `global_piqa.jsonl` dataset contains an `isQnA` boolean flag per item:\n",
            "\n",
            "| `isQnA` | Prompt style | Domain hint |\n",
            "|---------|--------------|-------------|\n",
            "| `true`  | MCQ — `\"This is a multiple-choice question related to the Sri Lankan Culture. "
            "Choose the correct or most appropriate answer from answers {range}. "
            "... Respond with only the number ({range}) and nothing else, exactly like the examples below.\"` | `Sri Lankan Culture` |\n",
            "| `false` | Paragraph-completion — `\"Out of the given {n} answers, which one is the best option "
            "to complete the given text? ... Respond with only the number ({range}) and nothing else, "
            "exactly like the examples below.\"` | — |\n",
        ], "cell_md_title"),

        make_cell("markdown", ["## 1. Configuration"], "cell_md_01"),
        make_cell("code", cell_source_config(model), "cell_01"),

        make_cell("markdown", ["## 2. Environment Setup & Hardware Verification"], "cell_md_02"),
        make_cell("code", cell_source_env_setup(), "cell_02"),

        make_cell("markdown", ["## 3. HuggingFace Authentication"], "cell_md_03"),
        make_cell("code", cell_source_auth(), "cell_03"),

        make_cell("markdown", ["## 4. Load Model & Tokenizer"], "cell_md_04"),
        make_cell("code", cell_source_load_model(), "cell_04"),

        make_cell("markdown", ["## 5. Load Global PIQA Dataset"], "cell_md_05"),
        make_cell("code", cell_source_load_data(), "cell_05"),

        make_cell("markdown", [
            "## 6. isQnA-Aware Prompt Templates & Label Extraction\n",
            "\n",
            "- **`isQnA=True`** → MCQ format with domain `Sri Lankan Culture`  \n",
            "- **`isQnA=False`** → Paragraph-completion format (no domain)  \n",
        ], "cell_md_06"),
        make_cell("code", cell_source_prompts(), "cell_06"),

        make_cell("markdown", [
            "## 7. Generation Engine\n",
            f"`REASONING_MODE = \"{reasoning_note}\"` — applied identically to both script conditions.\n",
        ], "cell_md_07"),
        make_cell("code", cell_source_generation_engine(model), "cell_07"),

        make_cell("markdown", ["## 8. Pilot Run"], "cell_md_08"),
        make_cell("code", cell_source_pilot(), "cell_08"),

        make_cell("markdown", ["## 9. Evaluation Runner"], "cell_md_09"),
        make_cell("code", cell_source_evaluation_runner(), "cell_09"),

        make_cell("markdown", ["## 10. Run Evaluation"], "cell_md_10"),
        make_cell("code", cell_source_run_evaluation(), "cell_10"),

        make_cell("markdown", ["## 11. Summary Statistics"], "cell_md_11"),
        make_cell("code", cell_source_summary(), "cell_11"),

        make_cell("markdown", ["## 12. Output File Listing"], "cell_md_12"),
        make_cell("code", cell_source_output_listing(), "cell_12"),
    ]

    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.12.0",
            },
            "kaggle": {
                "accelerator": "nvidiaTeslaT4",
                "isInternetEnabled": True,
                "language": "python",
                "sourceType": "notebook",
                "isGpuEnabled": True,
            },
        },
        "cells": cells,
    }
    return notebook


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    script_dir = Path(__file__).parent  # global_piqa_evaluation/

    for model in MODELS:
        label = model["label"]
        out_dir = script_dir / label
        out_dir.mkdir(parents=True, exist_ok=True)
        nb_path = out_dir / f"global_piqa_eval-{label}.ipynb"

        notebook = build_notebook(model)
        with open(nb_path, "w", encoding="utf-8") as f:
            json.dump(notebook, f, indent=1, ensure_ascii=False)

        print(f"[OK] {nb_path}")

    print(f"\nDone. Generated {len(MODELS)} notebooks in {script_dir}")


if __name__ == "__main__":
    main()
