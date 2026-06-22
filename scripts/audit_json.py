import os
import json
import glob
import re

RAW_DIR = "/home/kaitaku/projects/MakeFlashcard/raw_json"

def has_hangul(text):
    if not text:
        return False
    return bool(re.search(r'[\uac00-\ud7a3\u1100-\u11ff\u3130-\u318f]', text))

def audit():
    json_files = sorted(glob.glob(os.path.join(RAW_DIR, "page_*.json")))
    print(f"Auditing {len(json_files)} JSON files...")
    
    for fpath in json_files:
        basename = os.path.basename(fpath)
        with open(fpath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"[{basename}] Invalid JSON: {e}")
                continue
                
        is_vocab = data.get("is_vocabulary_page", False)
        chapter = data.get("chapter", "")
        section = data.get("section", "")
        
        # Check chapter/section anomalies
        if is_vocab:
            # Chapter should match Chapter 4, 5, 6, etc.
            if chapter and not re.match(r'^(Chapter\s*\d+|[456])$', chapter, re.IGNORECASE):
                print(f"[{basename}] Suspect chapter: '{chapter}'")
            if not chapter:
                # print(f"[{basename}] Missing chapter")
                pass
                
        words = data.get("words", [])
        for i, w in enumerate(words):
            vocab = w.get("vocab", "")
            stt = w.get("stt", "")
            meaning = w.get("meaning", "")
            example = w.get("example", "")
            translation = w.get("translation", "")
            
            # Check for Korean
            korean_in_meaning = has_hangul(meaning)
            korean_in_trans = has_hangul(translation)
            
            if korean_in_meaning or korean_in_trans:
                print(f"[{basename}] Word {stt} ({vocab}) has Korean: meaning='{meaning}', trans='{translation}'")
                
            # Check for missing translation if example exists
            if example and not translation:
                print(f"[{basename}] Word {stt} ({vocab}) has example but empty translation")
                
            # Check for empty meaning
            if not meaning:
                print(f"[{basename}] Word {stt} ({vocab}) has empty meaning")
                
            # Check for strange characters (like Indian chars etc)
            # Devanagari range: \u0900-\u097f
            if re.search(r'[\u0900-\u097f]', example) or re.search(r'[\u0900-\u097f]', translation) or re.search(r'[\u0900-\u097f]', meaning):
                print(f"[{basename}] Word {stt} ({vocab}) has Devanagari characters: example='{example}', trans='{translation}'")

if __name__ == "__main__":
    audit()
