import sys
import base64
import json
import requests
import os
import glob
import time

API_KEY = "YOUR_GEMINI_API_KEY_HERE"  # Thay bằng API key thực của bạn
MODEL_ID = "gemini-flash-lite-latest"
RAW_DIR = "/home/kaitaku/projects/MakeFlashcard/raw_json"

def ocr_page(img_path):
    with open(img_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode("utf-8")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent?key={API_KEY}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": {
            "role": "user",
            "parts": [
                {
                    "inlineData": {
                        "mimeType": "image/png",
                        "data": img_data
                    }
                },
                {
                    "text": (
                        "This is a page from the Japanese vocabulary textbook 'Hajimete no Nihongo Nouryoku Shiken N1 3000'. "
                        "If this page is a vocabulary page, extract all numbered vocabulary items. "
                        "Follow these rules:\n"
                        "1. Extract the 'stt' (the number preceding the word, e.g. 395, 396). If there is no number preceding the word (e.g. sub-words, or affixes/words in lists like 'これも覚えよう'), set 'stt' to \"\".\n"
                        "2. Extract 'vocab' (the main word in Japanese).\n"
                        "3. Extract 'reading' (the reading of the word in hiragana/katakana).\n"
                        "4. Extract 'meaning' (the Vietnamese meaning from the list. Tiếng Việt phải có dấu đầy đủ và đúng chính tả).\n"
                        "5. Extract 'example' (the Japanese example sentence).\n"
                        "6. Extract 'translation' (the Vietnamese translation of the example sentence. Tiếng Việt phải có dấu đầy đủ và đúng chính tả).\n"
                        "7. If a word does not have an example sentence or translation, leave them as empty strings.\n"
                        "8. If the page is not a vocabulary page (e.g. cover, TOC, review, exercises, index), set is_vocabulary_page to false.\n"
                        "9. Extract the 'chapter' (e.g. 'Chapter 4 学校で') and 'section' (e.g. 'Section 1 学校') if visible on the page."
                    )
                }
            ]
        },
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "is_vocabulary_page": {"type": "BOOLEAN"},
                    "chapter": {"type": "STRING"},
                    "section": {"type": "STRING"},
                    "words": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "stt": {"type": "STRING"},
                                "vocab": {"type": "STRING"},
                                "reading": {"type": "STRING"},
                                "meaning": {"type": "STRING"},
                                "example": {"type": "STRING"},
                                "translation": {"type": "STRING"}
                              },
                              "required": ["vocab", "reading", "meaning", "example", "translation"]
                        }
                    }
                },
                "required": ["is_vocabulary_page", "chapter", "section", "words"]
            }
        }
    }
    
    for attempt in range(5):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
            elif response.status_code == 429:
                print(f"Rate limited. Waiting 20s (attempt {attempt+1}/5)...")
                time.sleep(20)
            else:
                print(f"HTTP Error {response.status_code}: {response.text}. Waiting 5s...")
                time.sleep(5)
        except Exception as e:
            print(f"Exception: {e}. Waiting 10s...")
            time.sleep(10)
    return None

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 ocr_to_json.py <start_page> <end_page>")
        sys.exit(1)
        
    start_page = int(sys.argv[1])
    end_page = int(sys.argv[2])
    
    os.makedirs(RAW_DIR, exist_ok=True)
    
    for page_num in range(start_page, end_page + 1):
        out_path = os.path.join(RAW_DIR, f"page_{page_num:03d}.json")
        
        # Check if already processed
        if os.path.exists(out_path):
            print(f"Page {page_num} already exists, skipping.")
            continue
            
        matches = glob.glob(f"/home/kaitaku/projects/MakeFlashcard/image/*-{page_num:03d}.png")
        if not matches:
            print(f"No image found for page {page_num}, skipping.")
            continue
            
        img_path = matches[0]
        basename = os.path.basename(img_path)
        
        print(f"Processing page {page_num} ({basename})...")
        data = ocr_page(img_path)
        if data:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved to {out_path}")
        else:
            print(f"Failed to process page {page_num}")
            
        time.sleep(6) # Free tier limits

if __name__ == "__main__":
    main()
