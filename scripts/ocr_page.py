import sys
import base64
import json
import requests
import os

API_KEY = "YOUR_GEMINI_API_KEY_HERE"  # Thay bằng API key thực của bạn
MODEL_ID = "gemini-flash-lite-latest"

def ocr_page(page_num):
    img_path = f"/home/kaitaku/projects/MakeFlashcard/image/N1-はじめての日本語能力試験Ｎ１単語 3000-{page_num:03d}.png"
    if not os.path.exists(img_path):
        print(f"Error: File {img_path} does not exist.")
        return None
        
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
                        "1. Extract the 'stt' (the number preceding the word, e.g. 1, 2, 3). If there is no number preceding the word (e.g. sub-words, or affixes/words in lists like 'これも覚えよう'), set 'stt' to \"\".\n"
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
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 ocr_page.py <page_num>")
        sys.exit(1)
    page_num = int(sys.argv[1])
    res = ocr_page(page_num)
    if res:
        print(json.dumps(res, ensure_ascii=False, indent=2))
