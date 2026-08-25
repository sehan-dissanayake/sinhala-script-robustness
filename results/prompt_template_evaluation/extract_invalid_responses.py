"""
Script to extract all invalid responses from the raw prompt pilot outputs
and save them into model-separated CSV files, including the original question.

Run from the project root:
    python results/prompt_template_evaluation/extract_invalid_responses.py
Outputs (all under ./results/prompt_template_evaluation/results/invalid_responses/):
    {model}_invalid_responses.csv
"""

import json
from pathlib import Path
import pandas as pd

# Paths are relative to the project root, matching analyze_prompt_pilot.py
RAW_DIR = Path("./results/prompt_template_evaluation/results/raw")
OUT_DIR = Path("./results/prompt_template_evaluation/results/invalid_responses")
JSONL_FILES = [
    Path("./results/prompt_template_evaluation/sold_prompt_selection.jsonl"),
    Path("./results/prompt_template_evaluation/global_piqa_prompt_selection.jsonl"),
    Path("./results/prompt_template_evaluation/sinhala_mmlu_prompt_selection.jsonl"),
]

def load_questions(jsonl_paths):
    questions_dict = {}
    for p in jsonl_paths:
        if p.exists():
            with open(p, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip(): continue
                    obj = json.loads(line)
                    questions_dict[obj['id']] = obj
        else:
            print(f"Warning: Dataset file not found: {p}")
    return questions_dict

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Loading original questions from JSONL files...")
    questions_dict = load_questions(JSONL_FILES)
    
    paths = sorted(RAW_DIR.glob("*_prompt_pilot_raw.csv"))
    if not paths:
        print(f"No raw CSVs found in {RAW_DIR.resolve()}")
        return

    total_invalid = 0
    files_created = 0

    print(f"Searching for invalid responses in {len(paths)} raw files...")

    for p in paths:
        df = pd.read_csv(p, encoding="utf-8-sig")
        
        # Filter for invalid responses
        if "pred" not in df.columns:
            print(f"Skipping {p.name}: 'pred' column not found.")
            continue
            
        invalid_df = df[df["pred"] == "INVALID"].copy()
        
        if not invalid_df.empty:
            # Safely determine the model name
            if "model" in invalid_df.columns and not invalid_df["model"].empty:
                model_name = str(invalid_df["model"].iloc[0]).replace("/", "_").replace("\\", "_")
            else:
                model_name = p.name.replace("_prompt_pilot_raw.csv", "")

            # Add original question
            def get_original_question(row):
                qid = row.get('id')
                script = row.get('script')
                
                if qid not in questions_dict:
                    return "Question not found"
                    
                obj = questions_dict[qid]
                script_data = obj.get(script, {})
                text = script_data.get('text', '')
                options = script_data.get('options', [])
                
                if options:
                    options_str = " | ".join(options)
                    return f"{text}\nOptions: {options_str}"
                return text

            # Insert original_question right after 'id' column if possible, otherwise at the end
            invalid_df['original_question'] = invalid_df.apply(get_original_question, axis=1)
            
            # Reorder columns to make original_question prominent
            cols = list(invalid_df.columns)
            cols.insert(cols.index('id') + 1, cols.pop(cols.index('original_question')))
            invalid_df = invalid_df[cols]

            out_path = OUT_DIR / f"{model_name}_invalid_responses.csv"
            invalid_df.to_csv(out_path, index=False, encoding="utf-8-sig")
            
            print(f"  -> Saved {len(invalid_df):5,} invalid responses for {model_name} to {out_path.name}")
            total_invalid += len(invalid_df)
            files_created += 1

    print("-" * 60)
    print(f"Total invalid responses extracted: {total_invalid:,}")
    print(f"Model-separated CSVs created: {files_created}")
    print(f"Outputs saved to: {OUT_DIR.resolve()}")

if __name__ == "__main__":
    main()
