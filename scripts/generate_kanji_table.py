import os
import sys
import json
import time
import requests
import re

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
MODEL_ID = "google/gemini-2.5-flash"

RAW_KANJI_PATH = "/home/kaitaku/projects/MakeFlashcard/raw_kanji.txt"
PROGRESS_PATH = "/home/kaitaku/projects/MakeFlashcard/kanji_progress.json"
OUTPUT_MD_PATH = "/home/kaitaku/projects/MakeFlashcard/kanji.md"

def parse_raw_kanji(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    entries = []
    for i in range(0, len(lines), 3):
        if i + 2 < len(lines):
            kanji = lines[i]
            han_viet = lines[i+1]
            mean = lines[i+2]
            entries.append({
                "kanji": kanji,
                "han_viet": han_viet,
                "mean": mean,
                "han_viet_mean": f"{han_viet} ({mean})"
            })
    return entries

def call_openrouter_api(batch_entries, is_healing=False):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt_kanjis = [{"kanji": e["kanji"], "han_viet": e["han_viet"], "mean": e["mean"]} for e in batch_entries]
    
    if is_healing:
        prompt = (
            "You are an expert Japanese teacher. The examples generated previously for these Kanjis were malformed, incomplete, or missing the Japanese words.\n"
            "For each Kanji in the input list, please regenerate and provide exactly three common examples of words using this Kanji.\n"
            "Each of the 3 examples MUST follow the exact format: 'KanjiWord (reading_in_hiragana_or_katakana): Vietnamese_meaning'.\n"
            "Example: '設立 (せつりつ): Thành lập'.\n"
            "CRITICAL: Do not omit the Japanese word or its parenthesized reading. Every single example must have 'KanjiWord (reading): Meaning'.\n\n"
            "Input Kanji list:\n"
            + json.dumps(prompt_kanjis, ensure_ascii=False)
            + "\n\nOutput MUST be a valid JSON array of objects, containing fields: 'kanji', 'onyomi', 'kunyomi', 'examples'."
        )
    else:
        prompt = (
            "You are an expert Japanese teacher. For each Kanji in the input list, provide:\n"
            "1. Onyomi (in Katakana, separated by comma if multiple, or '-' if none)\n"
            "2. Kunyomi (in Hiragana, separated by comma if multiple, or '-' if none)\n"
            "3. Three common examples of words using this Kanji. Each of the 3 examples MUST follow the exact format: 'KanjiWord (reading_in_hiragana_or_katakana): Vietnamese_meaning'.\n"
            "Example: '設立 (せつりつ): Thành lập'.\n"
            "CRITICAL: Every single example must contain the Japanese word, parenthesized reading, and Vietnamese meaning.\n"
            "Ensure all Vietnamese translations have correct spelling and proper diacritics.\n\n"
            "Input Kanji list:\n"
            + json.dumps(prompt_kanjis, ensure_ascii=False)
            + "\n\nOutput MUST be a valid JSON array of objects, containing fields: 'kanji', 'onyomi', 'kunyomi', 'examples'."
        )
    
    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }
    
    for attempt in range(5):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                res_json = response.json()
                text = res_json["choices"][0]["message"]["content"]
                return json.loads(text)
            elif response.status_code == 429:
                print(f"Rate limit hit. Waiting 15s (attempt {attempt+1}/5)...")
                time.sleep(15)
            else:
                print(f"OpenRouter API Error {response.status_code}: {response.text}")
                time.sleep(5)
        except Exception as e:
            print(f"Exception during request (attempt {attempt+1}/5): {e}")
            time.sleep(5)
            
    return None

def normalize_example(ex):
    if isinstance(ex, str):
        return ex
    if isinstance(ex, dict):
        word = ex.get("kanji_word") or ex.get("word") or ex.get("kanji") or ex.get("vocab") or ""
        reading = ex.get("reading") or ex.get("hiragana") or ex.get("reading_in_hiragana") or ""
        meaning = ex.get("vietnamese_meaning") or ex.get("meaning") or ex.get("translation") or ex.get("vietnamese") or ""
        
        word = str(word).strip()
        reading = str(reading).strip()
        meaning = str(meaning).strip()
        
        if word and reading and meaning:
            return f"{word} ({reading}): {meaning}"
        elif word and meaning:
            return f"{word}: {meaning}"
        elif meaning:
            return meaning
    return str(ex)

def is_valid_example(ex):
    if not isinstance(ex, str):
        return False
    # Must contain parenthesis for reading and a colon for meaning
    # e.g., "設立 (せつりつ): Thành lập" or similar
    if "(" not in ex or ")" not in ex or ":" not in ex:
        return False
    # Check if there is a Japanese word before the parenthesis
    parts = ex.split("(")
    if not parts[0].strip():
        return False
    return True

def validate_kanji_data(kanji, data):
    if not data:
        return False
    examples = data.get("examples", [])
    if len(examples) != 3:
        return False
    for ex in examples:
        if not is_valid_example(ex):
            return False
    return True

def main():
    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY environment variable is not set.")
        sys.exit(1)
        
    entries = parse_raw_kanji(RAW_KANJI_PATH)
    print(f"Parsed {len(entries)} Kanjis from raw file.")
    
    # Load progress if exists
    progress = {}
    if os.path.exists(PROGRESS_PATH):
        try:
            with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
                progress = json.load(f)
            # Normalize loaded progress examples
            for k in progress:
                if "examples" in progress[k]:
                    progress[k]["examples"] = [normalize_example(ex) for ex in progress[k]["examples"]]
            print(f"Loaded progress: {len(progress)} Kanjis already processed.")
        except Exception as e:
            print("Failed to load progress file, starting fresh:", e)
            progress = {}
            
    # Process remaining kanjis in batches
    to_process = [e for e in entries if e["kanji"] not in progress]
    print(f"Remaining to process: {len(to_process)} Kanjis.")
    
    if to_process:
        batch_size = 20
        for i in range(0, len(to_process), batch_size):
            batch = to_process[i:i+batch_size]
            kanjis_in_batch = [e["kanji"] for e in batch]
            print(f"Processing batch {i//batch_size + 1}/{(len(to_process)-1)//batch_size + 1} for Kanjis: {', '.join(kanjis_in_batch)}")
            
            res = call_openrouter_api(batch)
            if not res:
                print("Failed to process batch. Stopping.")
                sys.exit(1)
            
            items_list = []
            if isinstance(res, dict):
                for val in res.values():
                    if isinstance(val, list):
                        items_list = val
                        break
                if not items_list:
                    items_list = [res]
            elif isinstance(res, list):
                items_list = res
                
            for item in items_list:
                kanji = item.get("kanji")
                if kanji:
                    examples = [normalize_example(ex) for ex in item.get("examples", [])]
                    progress[kanji] = {
                        "onyomi": item.get("onyomi"),
                        "kunyomi": item.get("kunyomi"),
                        "examples": examples
                    }
                    
            with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
                
            time.sleep(3)
            
    # HEALING LOOP: Check for malformed examples and fix them
    print("Starting self-healing loop for malformed examples...")
    for pass_num in range(3):
        # Always normalize current progress to make sure
        for k in progress:
            if "examples" in progress[k]:
                progress[k]["examples"] = [normalize_example(ex) for ex in progress[k]["examples"]]
                
        malformed_entries = []
        for entry in entries:
            k = entry["kanji"]
            data = progress.get(k)
            if not validate_kanji_data(k, data):
                malformed_entries.append(entry)
                
        if not malformed_entries:
            print("All Kanji entries are valid!")
            break
            
        print(f"Pass {pass_num+1}: Found {len(malformed_entries)} malformed Kanji entries: {', '.join([e['kanji'] for e in malformed_entries])}")
        
        # Process malformed in batches of 10 for more focus
        heal_batch_size = 10
        for i in range(0, len(malformed_entries), heal_batch_size):
            batch = malformed_entries[i:i+heal_batch_size]
            print(f"Healing batch {i//heal_batch_size + 1}/{(len(malformed_entries)-1)//heal_batch_size + 1}...")
            
            res = call_openrouter_api(batch, is_healing=True)
            if not res:
                print("Healing batch failed. Continuing to next batch.")
                continue
                
            items_list = []
            if isinstance(res, dict):
                for val in res.values():
                    if isinstance(val, list):
                        items_list = val
                        break
                if not items_list:
                    items_list = [res]
            elif isinstance(res, list):
                items_list = res
                
            for item in items_list:
                kanji = item.get("kanji")
                if kanji:
                    existing = progress.get(kanji, {})
                    onyomi = item.get("onyomi") or existing.get("onyomi") or "-"
                    kunyomi = item.get("kunyomi") or existing.get("kunyomi") or "-"
                    examples = [normalize_example(ex) for ex in (item.get("examples") or [])]
                    
                    progress[kanji] = {
                        "onyomi": onyomi,
                        "kunyomi": kunyomi,
                        "examples": examples
                    }
                    
            with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
                
            time.sleep(3)
            
    # Now generate the Markdown file
    print("Writing markdown table...")
    with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as out_f:
        out_f.write("| Chữ Kanji | Âm Hán Việt & Ý nghĩa | Âm On (Onyomi) | Âm Kun (Kunyomi) | 3 Ví dụ và Ý nghĩa |\n")
        out_f.write("|---|---|---|---|---|\n")
        
        for entry in entries:
            k = entry["kanji"]
            han_viet_mean = entry["han_viet_mean"]
            
            data = progress.get(k, {})
            onyomi = data.get("onyomi", "-")
            kunyomi = data.get("kunyomi", "-")
            examples_list = data.get("examples", [])
            
            # Format examples ensuring they start with '* ' and separate with <br>
            formatted_examples = []
            for ex in examples_list:
                ex = str(ex).strip()
                if not ex:
                    continue
                if not ex.startswith("*") and not ex.startswith("-"):
                    ex = f"* {ex}"
                # Ensure spacing is correct, e.g. '* word'
                if ex.startswith("*") and not ex.startswith("* "):
                    ex = "* " + ex[1:].strip()
                formatted_examples.append(ex)
                
            examples_str = "<br>".join(formatted_examples)
            
            # Escape pipes to avoid breaking markdown tables
            han_viet_mean_esc = han_viet_mean.replace("|", "｜")
            onyomi_esc = str(onyomi).replace("|", "｜")
            kunyomi_esc = str(kunyomi).replace("|", "｜")
            examples_esc = examples_str.replace("|", "｜")
            
            out_f.write(f"| {k} | {han_viet_mean_esc} | {onyomi_esc} | {kunyomi_esc} | {examples_esc} |\n")
            
    print(f"Finished generating markdown file: {OUTPUT_MD_PATH}")

if __name__ == "__main__":
    main()
