#!/usr/bin/env python3
import base64
import json
import requests
import os
import glob
import time
import re

# API Keys and endpoints
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

RAW_DIR = "/home/kaitaku/projects/MakeFlashcard/raw_json"
IMAGE_DIR = "/home/kaitaku/projects/MakeFlashcard/image"

def call_google_api(img_data, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
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
                    "text": prompt
                }
            ]
        },
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=60)
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
                            "url": f"data:image/png;base64,{img_data}"
                        }
                    }
                ]
            }
        ],
        "response_format": {
            "type": "json_object"
        }
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    if response.status_code == 200:
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return json.loads(content)
    else:
        raise Exception(f"OpenRouter API Error {response.status_code}: {response.text}")

def ocr_page(img_path, page_num):
    # Determine page type and customize the prompt to guide the model
    if (4 <= page_num <= 45) or (107 <= page_num <= 305):
        prompt = (
            f"This is page {page_num} of the bilingual book '999 Letters to Myself'. "
            "It contains a single letter in both Chinese and Vietnamese, along with its Pinyin. "
            "Extract the details into this JSON format:\n"
            "{\n"
            "  \"page_type\": \"bilingual_letter\",\n"
            "  \"letter_number\": <integer>,\n"
            "  \"chinese_text\": \"original Chinese title (if present) and body text\",\n"
            "  \"pinyin_text\": \"original Pinyin text\",\n"
            "  \"vietnamese_text\": \"original Vietnamese title and translation\"\n"
            "}\n"
            "Ensure the Vietnamese translations are spelled correctly with all proper diacritics. "
            "Do not output markdown code block syntax. Return only the JSON object."
        )
    elif 49 <= page_num <= 106:
        prompt = (
            f"This is page {page_num} of the book '999 Letters to Myself'. "
            "It contains one or more letters translated ONLY in Vietnamese. "
            "Extract the details into this JSON format:\n"
            "{\n"
            "  \"page_type\": \"vietnamese_letters\",\n"
            "  \"letters\": [\n"
            "    {\n"
            "      \"letter_number\": <integer>,\n"
            "      \"vietnamese_text\": \"original Vietnamese text of this letter\"\n"
            "    }\n"
            "  ],\n"
            "  \"text_before_first_header\": \"any text at the top of the page before the first letter header. This is usually the continuation of the last letter from the previous page. Leave as empty string if none.\"\n"
            "}\n"
            "Ensure the Vietnamese translations are spelled correctly with all proper diacritics. "
            "Do not output markdown code block syntax. Return only the JSON object."
        )
    else:
        # Cover, TOC, title pages, or duplicate pages (like page 306)
        prompt = (
            f"This is page {page_num} of the book '999 Letters to Myself'. "
            "It is a cover, Table of Contents (Mục lục), or title/introductory page. "
            "Confirm it is a non-letter page and return this JSON:\n"
            "{\n"
            "  \"page_type\": \"non_letter\"\n"
            "}\n"
            "Do not output markdown code block syntax. Return only the JSON object."
        )

    with open(img_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode("utf-8")

    # Try Google Gemini first, fallback to OpenRouter
    for attempt in range(5):
        try:
            if GEMINI_API_KEY:
                return call_google_api(img_data, prompt)
            elif OPENROUTER_API_KEY:
                return call_openrouter_api(img_data, prompt)
            else:
                raise Exception("No API Key configured. Please set GEMINI_API_KEY or OPENROUTER_API_KEY.")
        except Exception as e:
            print(f"  Attempt {attempt+1} failed for page {page_num}: {e}")
            if attempt < 4:
                time.sleep(10 * (attempt + 1))
            else:
                return None

def process_all(start_page=1, end_page=306):
    os.makedirs(RAW_DIR, exist_ok=True)
    images = sorted(glob.glob(os.path.join(IMAGE_DIR, "*.png")))
    
    print(f"Found {len(images)} images in {IMAGE_DIR}")
    
    for img_path in images:
        basename = os.path.basename(img_path)
        # Extract page number (e.g. "...-004.png" -> 4)
        match = re.search(r'-(\d+)\.png$', basename)
        if not match:
            continue
            
        page_num = int(match.group(1))
        if page_num < start_page or page_num > end_page:
            continue
            
        out_path = os.path.join(RAW_DIR, f"page_{page_num:03d}.json")
        if os.path.exists(out_path):
            print(f"Page {page_num} ({basename}) already processed, skipping.")
            continue
            
        print(f"Processing page {page_num} ({basename})...")
        data = ocr_page(img_path, page_num)
        if data:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"  Saved page {page_num} to {out_path}")
        else:
            print(f"  ERROR: Failed to process page {page_num}")
            
        # Sleep to avoid rate limits
        if OPENROUTER_API_KEY and not GEMINI_API_KEY:
            time.sleep(2)  # OpenRouter is less strict on free tier
        else:
            time.sleep(5)  # Native Google API free tier has 15 RPM limit

if __name__ == "__main__":
    import sys
    start = 1
    end = 306
    if len(sys.argv) >= 2:
        start = int(sys.argv[1])
    if len(sys.argv) >= 3:
        end = int(sys.argv[2])
    process_all(start, end)
