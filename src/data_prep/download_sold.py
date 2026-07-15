import os
from datasets import load_dataset

def main():
    print("Downloading SOLD...")
    # Load dataset
    ds = load_dataset("sinhala-nlp/SOLD")
    
    out_dir = os.path.join("data", "raw", "sold")
    os.makedirs(out_dir, exist_ok=True)
    
    # Save dataset splits to jsonl
    for split in ds.keys():
        out_path = os.path.join(out_dir, f"{split}.jsonl")
        ds[split].to_json(out_path, orient="records", lines=True, force_ascii=False)
        print(f"Saved {split} split to {out_path}")
        
    print("SOLD download complete.")

if __name__ == "__main__":
    main()
