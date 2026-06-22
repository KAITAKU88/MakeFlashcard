import json
import os
import re
import time
import glob
import requests

API_KEY = "YOUR_GEMINI_API_KEY_HERE"  # Thay bằng API key thực của bạn
MODEL_ID = "gemini-flash-lite-latest"
RAW_DIR = "/home/kaitaku/projects/MakeFlashcard/raw_json"

def has_hangul(text):
    if not text:
        return False
    return bool(re.search(r'[\uac00-\ud7a3\u1100-\u11ff\u3130-\u318f]', text))

def translate_to_vietnamese(vocab, example):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent?key={API_KEY}"
    headers = {
        "Content-Type": "application/json"
    }
    
    prompt = (
        f"Bạn là một biên dịch viên tiếng Nhật sang tiếng Việt chuyên nghiệp. "
        f"Hãy dịch từ vựng tiếng Nhật và câu ví dụ tiếng Nhật sau đây sang tiếng Việt chuẩn, tự nhiên, có dấu đầy đủ và đúng chính tả.\n\n"
        f"Từ vựng: {vocab}\n"
        f"Câu ví dụ: {example}\n\n"
        f"Trả về kết quả dưới dạng JSON có cấu trúc như sau (chỉ trả về JSON, không kèm giải thích hay markdown):\n"
        f"{{\n"
        f"  \"meaning\": \"nghĩa tiếng Việt ngắn gọn, chính xác của từ\",\n"
        f"  \"translation\": \"câu dịch tiếng Việt tự nhiên của câu ví dụ (để trống nếu câu ví dụ trống)\"\n"
        f"}}"
    )
    
    payload = {
        "contents": {
            "role": "user",
            "parts": [
                {
                    "text": prompt
                }
            ]
        },
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    for attempt in range(5):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
            else:
                print(f"HTTP Error {response.status_code}. Waiting 5s...")
                time.sleep(5)
        except Exception as e:
            print(f"Exception during translation: {e}. Waiting 5s...")
            time.sleep(5)
    return None

def fix_all_files():
    json_files = sorted(glob.glob(os.path.join(RAW_DIR, "page_*.json")))
    print(f"Checking {len(json_files)} JSON files for translation issues...")
    
    for fpath in json_files:
        basename = os.path.basename(fpath)
        with open(fpath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"Error parsing {basename}: {e}")
                continue
            
        if not data.get("is_vocabulary_page", False):
            continue
            
        words = data.get("words", [])
        updated = False
        
        for w in words:
            vocab = w.get("vocab", "")
            meaning = w.get("meaning", "")
            example = w.get("example", "")
            translation = w.get("translation", "")
            stt = w.get("stt", "")
            
            # Clean up Korean first to check if they are effectively empty
            clean_m = re.sub(r'[\uac00-\ud7a3\u1100-\u11ff\u3130-\u318f]+', '', meaning).strip()
            clean_t = re.sub(r'[\uac00-\ud7a3\u1100-\u11ff\u3130-\u318f]+', '', translation).strip()
            
            need_fix_meaning = not clean_m
            need_fix_trans = example and not clean_t
            
            if need_fix_meaning or need_fix_trans:
                print(f"[{basename}] Translating word {stt} ({vocab})...")
                res = translate_to_vietnamese(vocab, example)
                if res:
                    if need_fix_meaning:
                        new_m = res.get("meaning", "").strip()
                        print(f"  Old meaning: '{meaning}' -> New: '{new_m}'")
                        w["meaning"] = new_m
                    if need_fix_trans:
                        new_t = res.get("translation", "").strip()
                        print(f"  Old trans: '{translation}' -> New: '{new_t}'")
                        w["translation"] = new_t
                    updated = True
                    time.sleep(2) # delay to avoid rate limit
                else:
                    print(f"  Failed to translate {vocab}")
                    
        if updated:
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved changes to {basename}")

def fix_page_97_stts():
    fpath = os.path.join(RAW_DIR, "page_097.json")
    if os.path.exists(fpath):
        print("Fixing page_097.json STTs...")
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        words = data.get("words", [])
        expected_vocabs = ["オファー", "立腹", "軽減", "労力", "ノルマ", "新入り", "弱音", "マンネリ"]
        
        updated = False
        for i, w in enumerate(words):
            v = w.get("vocab", "").strip()
            if v in expected_vocabs:
                idx = expected_vocabs.index(v)
                new_stt = str(604 + idx)
                if w.get("stt") != new_stt:
                    w["stt"] = new_stt
                    print(f"  Assigned STT {new_stt} to {v}")
                    updated = True
                    
        if updated:
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("Saved page_097.json STTs changes.")

if __name__ == "__main__":
    fix_page_97_stts()
    fix_all_files()
