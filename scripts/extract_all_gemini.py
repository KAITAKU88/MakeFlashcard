import base64
import json
import requests
import os
import re
import time
import glob

API_KEY = "YOUR_GEMINI_API_KEY_HERE"  # Thay bằng API key thực của bạn
MODEL_ID = "gemini-flash-lite-latest"
IMAGE_DIR = "/home/kaitaku/projects/MakeFlashcard/image"
OUTPUT_MD = "/home/kaitaku/projects/MakeFlashcard/content.md"

def extract_from_image(img_path):
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
                        "Follow these rules STRICTLY:\n"
                        "1. Extract 'vocab' (the main word in Japanese, e.g. 一家).\n"
                        "2. Extract 'reading' (the reading of the word in hiragana/katakana, e.g. いっか).\n"
                        "3. Extract 'meaning': Extract ONLY the Vietnamese meaning. Ignore English or Chinese translations. Tiếng Việt phải có dấu đầy đủ và đúng chính tả.\n"
                        "4. If the page is not a vocabulary page (e.g. cover, TOC, review, exercises, index), set is_vocabulary_page to false.\n"
                        "5. Extract the 'chapter' (e.g., 'Chapter 1 人と人との関係') and 'section' (e.g., 'Section 1 家族') ONLY if they are explicitly visible on the page. If the chapter name is not printed on the page, set the 'chapter' field to \"\". Do not guess the chapter number based on the section number."
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
                                "vocab": {"type": "STRING"},
                                "reading": {"type": "STRING"},
                                "meaning": {"type": "STRING"}
                            },
                            "required": ["vocab", "reading", "meaning"]
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
                print(f"Rate limited on {os.path.basename(img_path)}. Waiting 30s...")
                time.sleep(30)
            else:
                print(f"Error {response.status_code} on {os.path.basename(img_path)}: {response.text}")
                time.sleep(5)
        except Exception as e:
            print(f"Exception on {os.path.basename(img_path)}: {e}")
            time.sleep(10)
            
    return None

def process_all():
    images = sorted(glob.glob(os.path.join(IMAGE_DIR, "*.png")))
    
    current_chapter = ""
    current_section = ""
    
    with open(OUTPUT_MD, "w", encoding="utf-8") as out_f:
        
        for img_path in images:
            basename = os.path.basename(img_path)
            # Extract page number from filename (e.g. "page-001.png" -> 1)
            num_match = re.search(r'(\d+)\.png$', basename)
            if not num_match:
                continue
            
            print(f"Processing {basename}...")
            data = extract_from_image(img_path)
            if not data:
                print(f"Failed to process {basename}")
                continue
                
            if not data.get("is_vocabulary_page", False):
                print(f"  -> Skipped (Not a vocabulary page)")
                continue
                
            words = data.get("words", [])
            if not words:
                print(f"  -> Skipped (No words found)")
                continue
                
            chapter = data.get("chapter", "").strip()
            section = data.get("section", "").strip()
            
            chapter_normalized = re.sub(r'\s+', ' ', chapter)
            section_normalized = re.sub(r'\s+', ' ', section)
            
            need_chapter = False
            need_section = False
            
            # Extract chapter number, e.g. "2" from "Chapter 2 暮らし" or "Chapter 2"
            curr_ch_num = re.search(r'Chapter\s*(\d+)', current_chapter)
            new_ch_num = re.search(r'Chapter\s*(\d+)', chapter_normalized)
            
            if chapter_normalized and "Chapter" in chapter_normalized:
                if curr_ch_num and new_ch_num:
                    if curr_ch_num.group(1) != new_ch_num.group(1):
                        current_chapter = chapter_normalized
                        need_chapter = True
                elif chapter_normalized != current_chapter:
                    current_chapter = chapter_normalized
                    need_chapter = True
                    
            # Extract section number, e.g. "4" from "Section 4 買い物" or "Section 4"
            curr_sec_num = re.search(r'Section\s*(\d+)', current_section)
            new_sec_num = re.search(r'Section\s*(\d+)', section_normalized)
            
            if section_normalized and "Section" in section_normalized:
                if curr_sec_num and new_sec_num:
                    if curr_sec_num.group(1) != new_sec_num.group(1):
                        current_section = section_normalized
                        need_section = True
                elif section_normalized != current_section:
                    current_section = section_normalized
                    need_section = True
                
            if need_chapter:
                out_f.write(f"\n## {current_chapter}\n\n")
                
            if need_section:
                out_f.write(f"### {current_section}\n\n")
                
            if need_chapter or need_section:
                out_f.write("| Từ vựng | Cách đọc | Ý nghĩa tiếng Việt |\n")
                out_f.write("|---|---|---|\n")
            
            for w in words:
                vocab = w.get("vocab", "").replace("\n", " ").replace("|", "｜")
                reading = w.get("reading", "").replace("\n", " ").replace("|", "｜")
                meaning = w.get("meaning", "").replace("\n", " ").replace("|", "｜")
                
                # Format to Markdown table row (3 columns)
                out_f.write(f"| {vocab} | {reading} | {meaning} |\n")
                
            out_f.flush()
            time.sleep(5) # Strict 5s delay to stay within 12 RPM (Free tier is 15 RPM)

if __name__ == "__main__":
    process_all()
