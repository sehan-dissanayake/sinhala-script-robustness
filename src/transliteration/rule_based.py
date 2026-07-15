import os
import json

# Original Singlish -> Sinhala mapping from the paper
original_table = {
    'a': 'අ', 'aa': 'ආ', 'A': 'ඇ', 'Aa': 'ඈ', 'i': 'ඉ', 'ie': 'ඊ',
    'u': 'උ', 'uu': 'ඌ', 'e': 'එ', 'ea': 'ඒ', 'I': 'ඓ', 'o': 'ඔ',
    'ka': 'ක', 'ga': 'ග', 'ma': 'ම', 'ya': 'ය', 'ra': 'ර', 'ba': 'බ',
    'ca': 'ච', 'ja': 'ජ', 'ta': 'ට', 'la': 'ල', 'Da': 'ඩ', 'wa': 'ව',
    'tha': 'ත', 'sa': 'ස', 'da': 'ද', 'ha': 'හ', 'na': 'න', 'pa': 'ප',
    'Na': 'ණ', 'La': 'ළ', 'mi': 'මි', 'thi': 'ති', 'Ka': 'ඛ', 'Ga': 'ඝ',
    'cha': 'ඡ', 'Tha': 'ඨ', 'Dha': 'ඪ', 'dha': 'ධ', 'Pa': 'ඵ', 'bha': 'භ',
    'fa': 'ෆ', 'Ba': 'ඹ', 'GNa': 'ඥ', 'KNa': 'ඤ', 'jha': 'ඣ', 'Lu': 'ළු',
    'Luu': 'ළූ', 'Sa': 'ශ', 'sha': 'ෂ',
    'ki': 'කි', 'ku': 'කු', 'ke': 'කෙ', 'ko': 'කො', 'kaa': 'කා', 'kAa': 'කෑ',
    'kie': 'කී', 'kei': 'කේ', 'gi': 'ගි', 'gu': 'ගු', 'ge': 'ගෙ', 'go': 'ගො',
    'gaa': 'ගා', 'gAa': 'ගෑ', 'gie': 'ගී', 'gei': 'ගේ', 'goe': 'ගෝ', 'guu': 'ගූ',
    'gau': 'ගෞ', '\\n': 'ං'
}

# Invert table for Sinhala -> Singlish (Romanized)
transliteration_table = {v: k for k, v in original_table.items()}

def transliterate(text: str) -> str:
    """
    Naive reference implementation for Sinhala -> Romanized transliteration.
    Uses an inverted dictionary and a longest-match strategy.
    """
    if not text:
        return ""
        
    result = ""
    i = 0
    while i < len(text):
        matched = False
        # Check substrings of decreasing length up to 3 (since some Sinhala modifiers combine into length 2-3 strings)
        for length in [3, 2, 1]:
            if i + length <= len(text):
                substring = text[i:i + length]
                if substring in transliteration_table:
                    result += transliteration_table[substring]
                    i += length
                    matched = True
                    break
        if not matched:
            result += text[i]
            i += 1
    return result

def process_datasets():
    method_name = "rule_based"
    in_dir = os.path.join("data", "processed")
    out_dir = os.path.join("data", "romanized", method_name)
    os.makedirs(out_dir, exist_ok=True)
    
    # Process MMLU
    mmlu_in = os.path.join(in_dir, "sinhala_mmlu.jsonl")
    mmlu_out = os.path.join(out_dir, "sinhala_mmlu_romanized.jsonl")
    if os.path.exists(mmlu_in):
        print(f"Transliterating MMLU...")
        with open(mmlu_in, 'r', encoding='utf-8') as fin, open(mmlu_out, 'w', encoding='utf-8') as fout:
            for line in fin:
                r = json.loads(line)
                r['text_romanized'] = transliterate(r['text_unicode'])
                r['options_romanized'] = [transliterate(opt) for opt in r['options']]
                fout.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"Saved to {mmlu_out}")

    # Process SOLD
    sold_in = os.path.join(in_dir, "sold.jsonl")
    sold_out = os.path.join(out_dir, "sold_romanized.jsonl")
    if os.path.exists(sold_in):
        print(f"Transliterating SOLD...")
        with open(sold_in, 'r', encoding='utf-8') as fin, open(sold_out, 'w', encoding='utf-8') as fout:
            for line in fin:
                r = json.loads(line)
                r['text_romanized'] = transliterate(r['text_unicode'])
                fout.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"Saved to {sold_out}")

if __name__ == "__main__":
    process_datasets()
