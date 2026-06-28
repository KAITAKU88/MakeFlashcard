#!/usr/bin/env python3
"""
Translate Vietnamese letters to Chinese + Pinyin using OpenRouter API.
Skips letters that already have Chinese text in raw_json.
"""
import json
import os
import re
import time
import requests
from docx import Document

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
RAW_DIR = "/home/kaitaku/projects/MakeFlashcard/raw_json"
DOCX_PATH = "/home/kaitaku/projects/MakeFlashcard/999-la-thu-gui-cho-chinh-minh.docx"
BATCH_SIZE = 10
MODEL = "google/gemini-2.5-flash"


def extract_letters_from_docx():
    doc = Document(DOCX_PATH)
    all_lines = []
    for p in doc.paragraphs:
        text = p.text.strip()
        if text:
            for line in text.split('\n'):
                stripped = line.strip()
                if stripped:
                    all_lines.append(stripped)

    letter_pattern = re.compile(r'^(\d{1,3})\.\s*(.+)', re.DOTALL)
    letters = {}
    current_num = None
    current_text_parts = []

    for line in all_lines:
        m = letter_pattern.match(line)
        if m:
            num = int(m.group(1))
            if 1 <= num <= 999:
                is_new_letter = False
                if current_num is None:
                    is_new_letter = (num == 1)
                elif num not in letters and num > 0:
                    is_new_letter = True

                if is_new_letter:
                    if current_num is not None:
                        letters[current_num] = ' '.join(current_text_parts)
                    current_num = num
                    current_text_parts = [m.group(2).strip()]
                    continue

        if current_num is not None:
            if re.match(r'^Bức thư thứ \d+', line):
                continue
            if line in ['Giới thiệu', 'G iới thiệu']:
                continue
            current_text_parts.append(line)

    if current_num is not None:
        letters[current_num] = ' '.join(current_text_parts)

    return letters


def get_existing_chinese():
    """Load letters that already have Chinese text from raw_json."""
    import glob
    has_chinese = {}
    files = sorted(glob.glob(os.path.join(RAW_DIR, "page_*.json")))

    for f in files:
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)

        pt = data.get("page_type")
        if pt == "bilingual_letter":
            num = data.get("letter_number")
            ch = data.get("chinese_text", "").strip()
            py = data.get("pinyin_text", "").strip()
            if num and ch:
                has_chinese[int(num)] = {"chinese": ch, "pinyin": py}
        elif pt == "vietnamese_letters":
            for l in data.get("letters", []):
                num = l.get("letter_number")
                ch = l.get("chinese_text", "").strip()
                if num and ch:
                    has_chinese[int(num)] = {
                        "chinese": ch,
                        "pinyin": l.get("pinyin_text", "").strip()
                    }

    return has_chinese


def translate_batch(batch):
    """Translate a batch of Vietnamese letters to Chinese + Pinyin via OpenRouter."""
    letters_text = ""
    for num, viet in batch:
        letters_text += f"[Letter {num}]\n{viet}\n\n"

    prompt = (
        "You are translating Vietnamese motivational letters back to their original Chinese.\n"
        "This book '999 Lá Thư Gửi Cho Chính Mình' (999封写给自己的信) was originally written in Chinese.\n\n"
        "Style guidelines:\n"
        "- Use literary, inspirational Chinese prose\n"
        "- Use 4-character idioms (成语) where natural\n"
        "- Keep the same meaning and emotional tone as the Vietnamese\n"
        "- Pinyin must use standard Hanyu Pinyin with tone marks (ā á ǎ à, ē é ě è, etc.)\n\n"
        "Translate each letter below to Chinese and provide Pinyin.\n"
        "Return a JSON array with objects: {\"letter_number\": N, \"chinese_text\": \"...\", \"pinyin_text\": \"...\"}\n\n"
        f"{letters_text}"
    )

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.3
    }

    for attempt in range(5):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                if isinstance(parsed, list):
                    return parsed
                elif isinstance(parsed, dict):
                    if "letters" in parsed:
                        return parsed["letters"]
                    elif "result" in parsed:
                        return parsed["result"]
                    else:
                        return [parsed]
                return parsed
            else:
                print(f"  API Error {response.status_code}: {response.text[:200]}")
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")

        if attempt < 4:
            time.sleep(10 * (attempt + 1))

    return None


def save_translated(letter_num, chinese, pinyin, vietnamese):
    """Save translated letter to raw_json."""
    out_path = os.path.join(RAW_DIR, f"translated_{letter_num:03d}.json")
    data = {
        "page_type": "bilingual_letter",
        "letter_number": letter_num,
        "chinese_text": chinese,
        "pinyin_text": pinyin,
        "vietnamese_text": vietnamese,
        "source": "api_translation"
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    if not OPENROUTER_API_KEY:
        print("ERROR: OPENROUTER_API_KEY not set!")
        return

    print("Extracting Vietnamese letters from docx...")
    viet_letters = extract_letters_from_docx()
    print(f"Found {len(viet_letters)} Vietnamese letters.")

    print("Loading existing Chinese translations from raw_json...")
    existing = get_existing_chinese()
    print(f"Already have Chinese for {len(existing)} letters.")

    # Also check for already-translated files
    for num in range(1, 1000):
        trans_path = os.path.join(RAW_DIR, f"translated_{num:03d}.json")
        if os.path.exists(trans_path) and num not in existing:
            with open(trans_path, encoding="utf-8") as f:
                data = json.load(f)
            ch = data.get("chinese_text", "").strip()
            py = data.get("pinyin_text", "").strip()
            if ch:
                existing[num] = {"chinese": ch, "pinyin": py}

    missing = sorted(set(range(1, 1000)) - set(existing.keys()))
    print(f"Need to translate {len(missing)} letters.")

    if not missing:
        print("All letters already have Chinese translations!")
        return

    # Process in batches
    total_batches = (len(missing) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(missing), BATCH_SIZE):
        batch_nums = missing[i:i + BATCH_SIZE]
        batch = [(num, viet_letters[num]) for num in batch_nums if num in viet_letters]
        batch_idx = i // BATCH_SIZE + 1

        print(f"\nBatch {batch_idx}/{total_batches}: Letters {batch_nums[0]}-{batch_nums[-1]}...")

        result = translate_batch(batch)
        if result is None:
            print(f"  FAILED! Skipping batch.")
            continue

        for item in result:
            num = int(item.get("letter_number", 0))
            ch = item.get("chinese_text", "").strip()
            py = item.get("pinyin_text", "").strip()
            if num and ch:
                viet = viet_letters.get(num, "")
                save_translated(num, ch, py, viet)
                print(f"  Saved letter {num}")
            else:
                print(f"  Warning: incomplete translation for item: {item.get('letter_number')}")

        time.sleep(2)

    # Final count
    final_existing = get_existing_chinese()
    for num in range(1, 1000):
        trans_path = os.path.join(RAW_DIR, f"translated_{num:03d}.json")
        if os.path.exists(trans_path) and num not in final_existing:
            with open(trans_path, encoding="utf-8") as f:
                data = json.load(f)
            ch = data.get("chinese_text", "").strip()
            if ch:
                final_existing[num] = True

    still_missing = sorted(set(range(1, 1000)) - set(final_existing.keys()))
    print(f"\n=== DONE ===")
    print(f"Total with Chinese: {999 - len(still_missing)}/999")
    if still_missing:
        print(f"Still missing: {still_missing}")


if __name__ == "__main__":
    main()
