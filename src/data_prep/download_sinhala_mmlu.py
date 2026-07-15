import os
from datasets import load_dataset
from dotenv import load_dotenv

def main():
    load_dotenv()
    print("Downloading SinhalaMMLU...")
    # Load dataset
    token = os.environ.get("HF_TOKEN")
    ds = load_dataset("naist-nlp/SinhalaMMLU", token=token)
    
    out_dir = os.path.join("data", "raw", "sinhala_mmlu")
    os.makedirs(out_dir, exist_ok=True)
    
    # Save dataset splits to jsonl
    for split in ds.keys():
        out_path = os.path.join(out_dir, f"{split}.jsonl")
        ds[split].to_json(out_path, orient="records", lines=True, force_ascii=False)
        print(f"Saved {split} split to {out_path}")
        
    print("SinhalaMMLU download complete.")

if __name__ == "__main__":
    main()
