#!/usr/bin/env python3
import base64
import json
import requests
import os
import re
import time
import glob
import sys

# API Keys and endpoints
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
MODEL_ID = "gemini-1.5-flash"

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMAGE_DIR = os.path.join(BASE_DIR, "image")

def call_google_api(img_data, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent?key={GEMINI_API_KEY}"
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": {
            "role": "user",
            "parts": [
                {
                    "inlineData": {
                        "mimeType": "image/jpeg",
                        "data": img_data
                    }
                },
                {
                    "text": prompt
                }
            ]
        },
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "is_vocabulary_page": {"type": "BOOLEAN"},
                    "words": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "stt": {"type": "STRING"},
                                "vocab": {"type": "STRING"},
                                "pos": {"type": "STRING"},
                                "pinyin": {"type": "STRING"},
                                "meaning": {"type": "STRING"},
                                "example": {"type": "STRING"},
                                "translation": {"type": "STRING"}
                            },
                            "required": ["stt", "vocab", "pos", "pinyin", "meaning", "example", "translation"]
                        }
                    }
                },
                "required": ["is_vocabulary_page", "words"]
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=90)
    if response.status_code == 200:
        result = response.json()
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    else:
        raise Exception(f"Google API Error {response.status_code}: {response.text}")

def call_openrouter_api(img_data, prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "google/gemini-2.5-flash",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_data}"
                        }
                    }
                ]
            }
        ],
        "response_format": {
            "type": "json_object"
        },
        "max_tokens": 2048
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=90)
    if response.status_code == 200:
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return json.loads(content)
    else:
        raise Exception(f"OpenRouter API Error {response.status_code}: {response.text}")

def ocr_page(img_path, page_num):
    if not GEMINI_API_KEY and not OPENROUTER_API_KEY:
        print("Error: Neither GEMINI_API_KEY nor OPENROUTER_API_KEY environment variable is set.")
        return None

    with open(img_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode("utf-8")
        
    prompt = (
        f"This is page {page_num} of a Chinese vocabulary learning book. "
        "Your task is to extract all vocabulary words listed on this page. "
        "Strictly follow these rules:\n"
        "1. Extract 'stt' (the sequence number preceding the word, e.g. 1, 2, 3). If there is no number, set it to \"\".\n"
        "2. Extract 'vocab' (the original Chinese word in simplified/traditional characters, e.g. 学习).\n"
        "3. Extract 'pos' (part of speech / từ loại, e.g. Động từ, Danh từ, Tính từ, v.v. Translate POS to Vietnamese if possible).\n"
        "4. Extract 'pinyin' (the Hanyu Pinyin pronunciation with tone marks, e.g. xuéxí).\n"
        "5. Extract 'meaning' (the Vietnamese meaning of the word. Tiếng Việt phải có dấu đầy đủ và đúng chính tả).\n"
        "6. Extract 'example' (the Chinese example sentence using the word).\n"
        "7. Extract 'translation' (the Vietnamese translation of the example sentence. Tiếng Việt phải có dấu đầy đủ và đúng chính tả).\n\n"
        "CRITICAL REQUIREMENT:\n"
        "- If the image does NOT provide 'pos' (part of speech), 'meaning' (Vietnamese meaning), 'example' (Chinese example sentence), or 'translation' (Vietnamese translation of the example), "
        "you MUST automatically generate these fields. Ensure the generated meaning, example sentence, and translation are natural, contextually accurate, and grammatically correct.\n"
        "- The Vietnamese translations and meanings MUST use proper diacritics and correct spelling.\n"
        "- If this page is not a vocabulary page (e.g. cover, table of contents, index, exercise, review, introductory page), set 'is_vocabulary_page' to false.\n\n"
        "Return the extracted details in this JSON format:\n"
        "{\n"
        "  \"is_vocabulary_page\": true/false,\n"
        "  \"words\": [\n"
        "    {\n"
        "      \"stt\": \"sequence number or empty string\",\n"
        "      \"vocab\": \"original Chinese word\",\n"
        "      \"pos\": \"part of speech in Vietnamese\",\n"
        "      \"pinyin\": \"Pinyin pronunciation\",\n"
        "      \"meaning\": \"Vietnamese meaning\",\n"
        "      \"example\": \"Chinese example sentence\",\n"
        "      \"translation\": \"Vietnamese translation of the example\"\n"
        "    }\n"
        "  ]\n"
        "}"
    )

    for attempt in range(5):
        try:
            if GEMINI_API_KEY:
                return call_google_api(img_data, prompt)
            elif OPENROUTER_API_KEY:
                return call_openrouter_api(img_data, prompt)
        except Exception as e:
            print(f"Attempt {attempt+1} failed for page {page_num}: {e}")
            if attempt < 4:
                time.sleep(15)
            else:
                return None
    return None

def extract_range(start_page, end_page, output_file):
    print(f"Extracting Chinese vocabulary from pages {start_page} to {end_page} to {output_file}...")
    
    # Ensure directory of output file exists
    out_dir = os.path.dirname(os.path.abspath(output_file))
    os.makedirs(out_dir, exist_ok=True)
    
    # Write header if file is new or empty
    write_header = not os.path.exists(output_file) or os.path.getsize(output_file) == 0
    
    with open(output_file, "a", encoding="utf-8") as out_f:
        if write_header:
            out_f.write("| STT | Từ vựng gốc | Từ loại | Phiên âm | Ý nghĩa | Câu ví dụ | Dịch câu ví dụ |\n")
            out_f.write("|-----|-------------|---------|----------|---------|-----------|----------------|\n")

        for page_num in range(start_page, end_page + 1):
            # Find image path supporting both .png and .jpg/jpeg
            img_patterns = [
                os.path.join(IMAGE_DIR, f"*-{page_num:03d}.png"),
                os.path.join(IMAGE_DIR, f"*-{page_num:03d}.jpg"),
                os.path.join(IMAGE_DIR, f"{page_num:03d}.png"),
                os.path.join(IMAGE_DIR, f"{page_num:03d}.jpg"),
                os.path.join(IMAGE_DIR, f"{page_num}.png"),
                os.path.join(IMAGE_DIR, f"{page_num}.jpg"),
            ]
            
            img_path = None
            for pattern in img_patterns:
                matches = glob.glob(pattern)
                if matches:
                    img_path = matches[0]
                    break
                    
            if not img_path:
                print(f"Warning: No image found for page {page_num}, skipping.")
                continue
                
            basename = os.path.basename(img_path)
            print(f"Processing page {page_num} ({basename})...")
            
            data = ocr_page(img_path, page_num)
            if not data:
                print(f"Error: Failed to process page {page_num}")
                continue
                
            is_vocab = data.get("is_vocabulary_page", False)
            if not is_vocab:
                print(f"Page {page_num}: Skipped (Not a vocabulary page)")
                continue
                
            words = data.get("words", [])
            if not words:
                print(f"Page {page_num}: Skipped (No words extracted)")
                continue
                
            print(f"Page {page_num}: Found {len(words)} words.")
            
            for w in words:
                stt = w.get("stt", "")
                if stt is None:
                    stt = ""
                vocab = w.get("vocab", "").replace("\n", " ").replace("|", "｜").strip()
                pos = w.get("pos", "").replace("\n", " ").replace("|", "｜").strip()
                pinyin = w.get("pinyin", "").replace("\n", " ").replace("|", "｜").strip()
                meaning = w.get("meaning", "").replace("\n", " ").replace("|", "｜").strip()
                example = w.get("example", "").replace("\n", " ").replace("|", "｜").strip()
                translation = w.get("translation", "").replace("\n", " ").replace("|", "｜").strip()
                
                out_f.write(f"| {stt} | {vocab} | {pos} | {pinyin} | {meaning} | {example} | {translation} |\n")
                
            out_f.flush()
            print(f"Page {page_num} completed. Sleeping 6s...")
            time.sleep(6)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 extract_chinese_vocab.py <start_page> <end_page> <output_file>")
        sys.exit(1)
        
    start = int(sys.argv[1])
    end = int(sys.argv[2])
    outfile = sys.argv[3]
    
    extract_range(start, end, outfile)
