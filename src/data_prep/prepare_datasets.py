import json
import os

def map_answer(ans):
    mapping = {1: "A", 2: "B", 3: "C", 4: "D"}
    return mapping.get(ans, str(ans))

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
            "label": map_answer(r['answer']),
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

def main():
    prepare_mmlu()
    prepare_sold()

if __name__ == "__main__":
    main()
