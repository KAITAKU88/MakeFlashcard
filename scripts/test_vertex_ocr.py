import base64
import json
import os
import subprocess
import requests

PROJECT_ID = "gen-lang-client-0806761869"
LOCATION = "us-central1"
MODEL_ID = "gemini-2.5-flash"

def get_access_token():
    return subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode("utf-8").strip()

def test_ocr():
    token = get_access_token()
    img_path = "/home/kaitaku/projects/MakeFlashcard/image/N2 はじめての日本語能力試験 N2単語 2500-011.png"
    
    with open(img_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode("utf-8")
        
    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{MODEL_ID}:generateContent"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    payload = {
        "contents": {
            "role": "USER",
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
                        "1. Extract the 'stt' (the number preceding the word, e.g. 1, 2, 3).\n"
                        "2. Extract 'vocab' (the main word in Japanese, e.g. 一家).\n"
                        "3. Extract 'reading' (the reading of the word in hiragana/katakana, e.g. いっか).\n"
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
                                "stt": {"type": "INTEGER"},
                                "vocab": {"type": "STRING"},
                                "reading": {"type": "STRING"},
                                "meaning": {"type": "STRING"},
                                "example": {"type": "STRING"},
                                "translation": {"type": "STRING"}
                            },
                            "required": ["stt", "vocab", "reading", "meaning", "example", "translation"]
                        }
                    }
                },
                "required": ["is_vocabulary_page", "chapter", "section", "words"]
            }
        }
    }
    
    print("Sending request to Vertex AI...")
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
    test_ocr()
