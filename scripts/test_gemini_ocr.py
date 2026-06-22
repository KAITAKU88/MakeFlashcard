import base64
import json
import requests
import os

API_KEY = "YOUR_GEMINI_API_KEY_HERE"  # Thay bằng API key thực của bạn
MODEL_ID = "gemini-flash-lite-latest"

def test_gemini_ocr():
    img_path = "/home/kaitaku/projects/MakeFlashcard/image/N2 はじめての日本語能力試験 N2単語 2500-047.png"
    
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
                        "This is a page from the Japanese vocabulary textbook 'Hajimete no Nihongo Nouryoku Shiken N2 2500'. "
                        "If this page is a vocabulary page, extract all numbered vocabulary items. "
                        "Follow these rules:\n"
                        "1. Extract the 'stt' (the number preceding the word, e.g. 1, 2, 3). If there is no number preceding the word (e.g. sub-words, or affixes/words in lists like 'これも覚えよう'), set 'stt' to \"\".\n"
                        "2. Extract 'vocab' (the main word in Japanese, e.g. 一家).\n"
                        "3. Extract 'reading' (the reading of the word in hiragana/katakana, e.g. いっか). If there are related sub-words without a number, add them as well with \"\" stt.\n"
                        "4. Extract 'meaning' (the Vietnamese meaning from the list. Tiếng Việt phải có dấu đầy đủ và đúng chính tả, e.g. 'cả nhà, cả gia đình').\n"
                        "5. Extract 'example' (the Japanese example sentence, e.g. 兄が私達一家を支えてくれている。).\n"
                        "6. Extract 'translation' (the Vietnamese translation of the example sentence. Tiếng Việt phải có dấu đầy đủ và đúng chính tả, e.g. 'Anh trai tôi gánh vác cả gia đình chúng tôi.').\n"
                        "7. If a word does not have an example sentence or translation, leave them as empty strings.\n"
                        "8. If the page is not a vocabulary page (e.g. cover, TOC, review, exercises, index), set is_vocabulary_page to false.\n"
                        "9. Extract the 'chapter' (e.g., 'Chapter 1 人と人との関係') and 'section' (e.g., 'Section 1 家族') if visible on the page."
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
    
    print("Sending request to Google AI Studio API...")
    response = requests.post(url, headers=headers, json=payload)
    print("Status code:", response.status_code)
    
    if response.status_code == 200:
        result = response.json()
        print("Success! Response JSON:")
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        print(text)
    else:
        print("Error response:", response.text)

if __name__ == "__main__":
    test_gemini_ocr()
