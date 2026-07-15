import json
import os
import random

def map_answer(ans):
    mapping = {1: "A", 2: "B", 3: "C", 4: "D"}
    return mapping.get(ans, str(ans))

def sample_mmlu():
    print("Processing SinhalaMMLU...")
    data_dir = os.path.join("data", "raw", "sinhala_mmlu")
    records = []
    for file in os.listdir(data_dir):
        if file.endswith(".jsonl"):
            with open(os.path.join(data_dir, file), 'r', encoding='utf-8') as f:
                for line in f:
                    records.append(json.loads(line))
    
    # Group by domain and difficulty
    groups = {}
    for r in records:
        domain = str(r.get('category', 'unknown')).title()
        diff = r.get('metadata', {}).get('difficulty', 'unknown').capitalize()
        key = (domain, diff)
        if key not in groups:
            groups[key] = []
        groups[key].append(r)
        
    target_n = 500
    frac = target_n / len(records)
    
    sampled_records = []
    random.seed(42)
    for key, group_records in groups.items():
        n_sample = max(1, int(round(len(group_records) * frac)))
        if n_sample > len(group_records):
            n_sample = len(group_records)
        sampled = random.sample(group_records, n_sample)
        
        for r in sampled:
            domain = str(r.get('category', 'unknown')).title()
            diff = r.get('metadata', {}).get('difficulty', 'unknown').capitalize()
            sampled_records.append({
                "dataset": "sinhala_mmlu",
                "text_unicode": r['question'],
                "options": r['choices'],
                "label": map_answer(r['answer']),
                "domain": domain,
                "difficulty": diff
            })
            
    output_records = []
    for idx, r in enumerate(sampled_records, 1):
        r['id'] = f"mmlu_{idx:04d}"
        output_records.append(r)
        
    out_dir = os.path.join("data", "processed")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sinhala_mmlu_sample.jsonl")
    with open(out_path, 'w', encoding='utf-8') as f:
        for r in output_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Saved {len(output_records)} MMLU samples to {out_path}")

def sample_sold():
    print("Processing SOLD...")
    test_path = os.path.join("data", "raw", "sold", "test.jsonl")
    records = []
    with open(test_path, 'r', encoding='utf-8') as f:
        for line in f:
            records.append(json.loads(line))
            
    groups = {}
    for r in records:
        lbl = r.get('label', 'unknown')
        if lbl not in groups:
            groups[lbl] = []
        groups[lbl].append(r)
        
    target_n = 500
    frac = target_n / len(records)
    
    sampled_records = []
    random.seed(42)
    for lbl, group_records in groups.items():
        n_sample = max(1, int(round(len(group_records) * frac)))
        if n_sample > len(group_records):
            n_sample = len(group_records)
        sampled = random.sample(group_records, n_sample)
        
        for r in sampled:
            sampled_records.append({
                "dataset": "sold",
                "text_unicode": r['text'],
                "label": r['label']
            })
            
    output_records = []
    for idx, r in enumerate(sampled_records, 1):
        r['id'] = f"sold_{idx:04d}"
        output_records.append(r)
        
    out_dir = os.path.join("data", "processed")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sold_sample.jsonl")
    with open(out_path, 'w', encoding='utf-8') as f:
        for r in output_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Saved {len(output_records)} SOLD samples to {out_path}")

def main():
    sample_mmlu()
    sample_sold()

if __name__ == "__main__":
    main()
