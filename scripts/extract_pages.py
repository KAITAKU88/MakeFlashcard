import sys
import base64
import json
import requests
import os
import re
import time
import glob

API_KEY = "YOUR_GEMINI_API_KEY_HERE"  # Thay bằng API key thực của bạn
MODEL_ID = "gemini-flash-lite-latest"

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

def extract_range(start_page, end_page, output_file):
    print(f"Extracting pages {start_page} to {end_page} to {output_file}...")
    
    current_chapter = ""
    current_section = ""
    
    # Let's see if file already has content to figure out headers
    file_exists = os.path.exists(output_file)
    
    with open(output_file, "a", encoding="utf-8") as out_f:
        for page_num in range(start_page, end_page + 1):
            # Find image path
            matches = glob.glob(f"/home/kaitaku/projects/MakeFlashcard/image/*-{page_num:03d}.png")
            if not matches:
                print(f"Warning: No image found for page {page_num}, skipping.")
                continue
            img_path = matches[0]
            basename = os.path.basename(img_path)
            
            print(f"Processing page {page_num} ({basename})...")
            
            # API call
            data = ocr_page(img_path)
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
                
            chapter = data.get("chapter", "").strip()
            section = data.get("section", "").strip()
            
            print(f"Page {page_num}: Found {len(words)} words. Chapter: '{chapter}', Section: '{section}'")
            
            # Detect new Chapter or Section
            need_chapter_header = False
            need_section_header = False
            
            if chapter and chapter != current_chapter:
                current_chapter = chapter
                need_chapter_header = True
                
            if section and section != current_section:
                current_section = section
                need_section_header = True
                
            if need_chapter_header:
                out_f.write(f"\n## {current_chapter}\n")
                
            if need_section_header:
                out_f.write(f"\n### {current_section}\n\n")
                out_f.write("| STT | Từ vựng | Ý nghĩa | Cách đọc | Câu ví dụ | Dịch câu ví dụ |\n")
                out_f.write("|-----|---------|---------|----------|-----------|----------------|\n")
            elif need_chapter_header:
                # Chapter header printed but section didn't change (e.g. first page has both)
                out_f.write("| STT | Từ vựng | Ý nghĩa | Cách đọc | Câu ví dụ | Dịch câu ví dụ |\n")
                out_f.write("|-----|---------|---------|----------|-----------|----------------|\n")
                
            for w in words:
                stt = w.get("stt", "")
                if stt is None:
                    stt = ""
                vocab = w.get("vocab", "").replace("\n", " ").replace("|", "｜").strip()
                reading = w.get("reading", "").replace("\n", " ").replace("|", "｜").strip()
                meaning = w.get("meaning", "").replace("\n", " ").replace("|", "｜").strip()
                example = w.get("example", "").replace("\n", " ").replace("|", "｜").strip()
                translation = w.get("translation", "").replace("\n", " ").replace("|", "｜").strip()
                
                # Double-check constraints
                # - Vietnamese diacritics should remain intact
                
                out_f.write(f"| {stt} | {vocab} | {meaning} | {reading} | {example} | {translation} |\n")
                
            out_f.flush()
            print(f"Page {page_num} completed. Sleeping 6s...")
            time.sleep(6)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 extract_pages.py <start_page> <end_page> <output_file>")
        sys.exit(1)
        
    start_page = int(sys.argv[1])
    end_page = int(sys.argv[2])
    output_file = sys.argv[3]
    
    extract_range(start_page, end_page, output_file)
