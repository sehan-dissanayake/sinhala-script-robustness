"""Normalise each raw dataset into the shared processed schema.

Every processed record carries at least:
    id, dataset, text_unicode, label
Multiple-choice datasets (SinhalaMMLU, Global PIQA) additionally carry `options`
(a list of strings) and a letter label indexing into it. That shared shape is
what src/transliteration/_dataset_io.py romanizes and what the downstream LLM
runner consumes, so the two MCQ tasks need no special-casing.
"""

import json
import os

LETTERS = "ABCDEFGH"


def map_answer(ans, choices, q_id=""):
    """Map SinhalaMMLU's 1-based answer index to a letter.

    One upstream row (q_no 64, "how many standard time zones is the Earth divided
    into") stores the answer *value* 24 instead of its index, which silently
    produced the bogus label "24". Where the field is out of range we recover the
    index by matching it against the choices, and fail loudly if that is
    ambiguous, rather than writing a label no downstream scorer can interpret.
    """
    if ans in (1, 2, 3, 4):
        return LETTERS[ans - 1]
    matches = [i for i, c in enumerate(choices) if str(c).strip() == str(ans).strip()]
    if len(matches) == 1:
        return LETTERS[matches[0]]
    raise ValueError(
        f"{q_id}: answer {ans!r} is not a 1-4 index and matches "
        f"{len(matches)} of the choices {choices!r}"
    )

def prepare_mmlu():
    print("Processing SinhalaMMLU...")
    data_dir = os.path.join("data", "raw", "sinhala_mmlu")
    records = []
    for file in os.listdir(data_dir):
        if file.endswith(".jsonl"):
            with open(os.path.join(data_dir, file), 'r', encoding='utf-8') as f:
                for line in f:
                    records.append(json.loads(line))
                    
    output_records = []
    for idx, r in enumerate(records, 1):
        domain = str(r.get('category', 'unknown')).title()
        diff = r.get('metadata', {}).get('difficulty', 'unknown').capitalize()
        output_records.append({
            "id": f"mmlu_{idx:04d}",
            "dataset": "sinhala_mmlu",
            "text_unicode": r['question'],
            "options": r['choices'],
            "label": map_answer(r['answer'], r['choices'], f"mmlu_{idx:04d}"),
            "domain": domain,
            "difficulty": diff
        })
        
    out_dir = os.path.join("data", "processed")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sinhala_mmlu.jsonl")
    with open(out_path, 'w', encoding='utf-8') as f:
        for r in output_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Saved {len(output_records)} MMLU full records to {out_path}")

def prepare_sold():
    print("Processing SOLD...")
    test_path = os.path.join("data", "raw", "sold", "test.jsonl")
    records = []
    if os.path.exists(test_path):
        with open(test_path, 'r', encoding='utf-8') as f:
            for line in f:
                records.append(json.loads(line))
                
    output_records = []
    for idx, r in enumerate(records, 1):
        output_records.append({
            "id": f"sold_{idx:04d}",
            "dataset": "sold",
            "text_unicode": r['text'],
            "label": r['label']
        })
        
    out_dir = os.path.join("data", "processed")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sold.jsonl")
    with open(out_path, 'w', encoding='utf-8') as f:
        for r in output_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Saved {len(output_records)} SOLD full records to {out_path}")


def _read_jsonl(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def _piqa_record(row, record_id, dataset):
    """Map one Global PIQA row to the shared processed schema.

    `label` is a 0/1 index into [solution0, solution1] upstream (a string in the
    TSV pool, an int in the HF config), so it is normalised to a letter here.
    Upstream metadata is kept for stratification and error analysis; the English
    translation fields are already Latin script, so the transliteration step
    passes them through untouched.
    """
    label_idx = int(row['label'])
    if label_idx not in (0, 1):
        raise ValueError(f"{record_id}: unexpected label {row['label']!r}")
    return {
        "id": record_id,
        "dataset": dataset,
        "text_unicode": row['prompt'],
        "options": [row['solution0'], row['solution1']],
        "label": LETTERS[label_idx],
        "example_id": row['example_id'],
        "culturally_specific": bool(int(row.get('approx_cultural_score', 0) or 0)),
        "llm_assisted": bool(int(row.get('llm_used', 0) or 0)),
        "eng_options": [
            row.get('eng_translated0') or row.get('gemini_translated0') or '',
            row.get('eng_translated1') or row.get('gemini_translated1') or '',
        ],
    }


def _write_processed(output_records, filename, description):
    out_dir = os.path.join("data", "processed")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)
    with open(out_path, 'w', encoding='utf-8') as f:
        for r in output_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Saved {len(output_records)} {description} records to {out_path}")


def prepare_global_piqa():
    print("Processing Global PIQA (sin_sinh)...")
    raw_dir = os.path.join("data", "raw", "global_piqa")
    test_path = os.path.join(raw_dir, "test.jsonl")
    if not os.path.exists(test_path):
        print(f"  skipped: {test_path} not found "
              "(run src/data_prep/download_global_piqa.py first)")
        return

    official = _read_jsonl(test_path)
    _write_processed(
        [_piqa_record(r, f"piqa_{i:04d}", "global_piqa") for i, r in enumerate(official, 1)],
        "global_piqa.jsonl", "Global PIQA",
    )


def main():
    prepare_mmlu()
    prepare_sold()
    prepare_global_piqa()

if __name__ == "__main__":
    main()
