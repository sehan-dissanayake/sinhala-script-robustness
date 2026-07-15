import os
import json

# Independent Vowels mapping
vowels = {
    'අ': 'a', 'ආ': 'aa', 'ඇ': 'ae', 'ඈ': 'aae', 'ඉ': 'i', 'ඊ': 'ii',
    'උ': 'u', 'ඌ': 'uu', 'එ': 'e', 'ඒ': 'ee', 'ඓ': 'ai', 'ඔ': 'o',
    'ඕ': 'oo', 'ඖ': 'au', 'ඍ': 'ru', 'ඎ': 'ruu', 'ඏ': 'lu', 'ඐ': 'luu'
}

# Consonants mapping (base consonants without inherent vowel)
consonants = {
    'ක': 'k', 'ඛ': 'kh', 'ග': 'g', 'ඝ': 'gh', 'ඞ': 'n',
    'ඟ': 'ndg',
    'ච': 'c', 'ඡ': 'ch', 'ජ': 'j', 'ඣ': 'jh', 'ඤ': 'gn',
    'ඥ': 'gn', 'ඦ': 'nndj',
    'ට': 't', 'ඨ': 'th', 'ඩ': 'd', 'ඪ': 'dh', 'ණ': 'n',
    'ඬ': 'ndd',
    'ත': 'th', 'ථ': 'th', 'ද': 'd', 'ධ': 'dh', 'න': 'n',
    'ඳ': 'nd',
    'ප': 'p', 'ඵ': 'ph', 'බ': 'b', 'භ': 'bh', 'ම': 'm',
    'ඹ': 'mb',
    'ය': 'y', 'ර': 'r', 'ල': 'l', 'ව': 'w', 'ශ': 'sh',
    'ෂ': 'sh', 'ස': 's', 'හ': 'h', 'ළ': 'l', 'ෆ': 'f'
}

# Vowel signs / dependent modifiers mapping
vowel_signs = {
    '්': '',       # Hal Kirima (removes inherent vowel)
    'ා': 'aa',     # a-pilla
    'ැ': 'ae',     # ae-pilla
    'ෑ': 'aae',    # diga ae-pilla
    'ි': 'i',      # is-pilla
    'ී': 'ii',     # diga is-pilla
    'ු': 'u',      # pa-pilla
    'ූ': 'uu',     # diga pa-pilla
    'ෘ': 'ru',     # gaeta-pilla
    'ෙ': 'e',      # kombuwa
    'ේ': 'ee',     # kombuwa and hal-kirima
    'ෛ': 'ai',     # kombu deka
    'ො': 'o',      # kombuwa and a-pilla
    'ෝ': 'oo',     # kombuwa, a-pilla, and hal-kirima
    'ෞ': 'au',     # kombuwa and gayanukitta
    'ෟ': 'ow',
    'ෲ': 'ruu',
    'ෳ': 'luu'
}

# Special signs mapping
special_signs = {
    'ං': 'n',      # anusvaraya
    'ඃ': 'h',      # visargaya
}

def transliterate(text: str) -> str:
    """
    Robust character-by-character phonetic parsing for Sinhala -> Romanized transliteration.
    """
    if not text:
        return ""
        
    result = []
    i = 0
    n = len(text)
    
    while i < n:
        char = text[i]
        
        # Skip ZWJ (Zero-Width Joiner) and ZWNJ
        if char in ('\u200d', '\u200c'):
            i += 1
            continue
            
        # Independent vowel match
        if char in vowels:
            result.append(vowels[char])
            i += 1
            continue
            
        # Consonant match
        if char in consonants:
            base = consonants[char]
            next_idx = i + 1
            has_modifier = False
            
            if next_idx < n:
                next_char = text[next_idx]
                if next_char in vowel_signs:
                    modifier = vowel_signs[next_char]
                    result.append(base + modifier)
                    i += 2
                    has_modifier = True
                elif next_char == '\u200d' and next_idx + 1 < n and text[next_idx + 1] in vowel_signs:
                    # e.g., consonant + ZWJ + vowel_sign
                    modifier = vowel_signs[text[next_idx + 1]]
                    result.append(base + modifier)
                    i += 3
                    has_modifier = True
                    
            if not has_modifier:
                # Add inherent vowel 'a'
                result.append(base + 'a')
                i += 1
            continue
            
        # Special sign match
        if char in special_signs:
            result.append(special_signs[char])
            i += 1
            continue
            
        # Standalone vowel sign (fallback/erroneous input)
        if char in vowel_signs:
            result.append(vowel_signs[char])
            i += 1
            continue
            
        # Keep non-Sinhala character as is
        result.append(char)
        i += 1
        
    return "".join(result)

def process_datasets():
    method_name = "phonetic"
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
