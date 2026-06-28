#!/usr/bin/env python3
import json
import os
import glob
import re
import csv

RAW_DIR = "/home/kaitaku/projects/MakeFlashcard/raw_json"
OUTPUT_MD = "/home/kaitaku/projects/MakeFlashcard/content.md"
OUTPUT_CSV = "/home/kaitaku/projects/MakeFlashcard/content.csv"

_VIET_PREFIX_RE = re.compile(
    r'^(Bức\s+[Tt]hư(\s+[Tt]hứ)?[\s\S]*?Viết\s+Cho\s+Chính\s+Mình[.\s]*'
    r'|Bức\s+[Tt]hư\s+\d+[.\s]*)$',
    re.IGNORECASE,
)
_VIET_FOOTER_RE = re.compile(
    r'\n*999\s*LÁ\s*THƯ.*$', re.DOTALL
)
_CH_TITLE_RE = re.compile(
    r'^写给自己的第.{1,10}封信[\s\n]*'
)
_CH_BRACKET_RE = re.compile(
    r'\s*\[\d+\]\s*$'
)


def clean_chinese(text):
    text = _CH_TITLE_RE.sub('', text)
    text = _CH_BRACKET_RE.sub('', text)
    return text.strip()


def clean_vietnamese(text):
    lines = text.split("\n")
    while lines and _VIET_PREFIX_RE.match(lines[0].strip()):
        lines.pop(0)
    text = "\n".join(lines).strip()
    text = _VIET_FOOTER_RE.sub('', text).strip()
    return text

# Known typos or page duplicate overrides
DUPLICATE_PAGES_TO_SKIP = {306} # 306 is duplicate of 302

def get_override_letter_number(page_num, extracted_num):
    # Page 303 has typo "809" printed on the page, but is actually Bức thư 808
    if page_num == 303 and extracted_num == 809:
        return 808
    return extracted_num

def reconstruct():
    json_files = sorted(glob.glob(os.path.join(RAW_DIR, "page_*.json")))
    print(f"Found {len(json_files)} processed JSON pages.")
    
    all_letters = {}
    last_letter_num = None
    
    for file_path in json_files:
        basename = os.path.basename(file_path)
        match = re.search(r'page_(\d+)\.json$', basename)
        if not match:
            continue
        page_num = int(match.group(1))
        
        if page_num in DUPLICATE_PAGES_TO_SKIP:
            print(f"Skipping duplicate page {page_num}")
            continue
            
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        page_type = data.get("page_type")
        
        if page_type == "bilingual_letter":
            ext_num = data.get("letter_number")
            if ext_num is None:
                print(f"Warning: Page {page_num} is bilingual_letter but letter_number is null!")
                continue
                
            letter_num = get_override_letter_number(page_num, int(ext_num))
            
            chinese = data.get("chinese_text", "").strip()
            pinyin = data.get("pinyin_text", "").strip()
            vietnamese = data.get("vietnamese_text", "").strip()
            
            # Format letter number prefix for Vietnamese translation if not already present
            prefix = f"Bức thư {letter_num}"
            if prefix not in vietnamese and f"Bức thư thứ {letter_num}" not in vietnamese:
                # Add the title at the top of Vietnamese translation
                vietnamese = f"Bức thư {letter_num}\n{vietnamese}"
                
            all_letters[letter_num] = {
                "chinese": chinese,
                "pinyin": pinyin,
                "vietnamese": vietnamese,
                "source_page": page_num
            }
            last_letter_num = letter_num
            
        elif page_type == "vietnamese_letters":
            # 1. Handle spanned text from previous page first
            spanned_text = data.get("text_before_first_header", "").strip()
            spanned_ch = data.get("chinese_text_before_first_header", "").strip()
            spanned_py = data.get("pinyin_text_before_first_header", "").strip()
            if spanned_text and last_letter_num is not None:
                if last_letter_num in all_letters:
                    print(f"Appending spanned text to Letter {last_letter_num} from Page {page_num}")
                    all_letters[last_letter_num]["vietnamese"] += "\n" + spanned_text
                    if spanned_ch:
                        all_letters[last_letter_num]["chinese"] += "\n" + spanned_ch
                    if spanned_py:
                        all_letters[last_letter_num]["pinyin"] += "\n" + spanned_py
                else:
                    print(f"Warning: Page {page_num} has spanned text but Letter {last_letter_num} is not in dictionary!")

            # 2. Process letters on this page
            letters = data.get("letters", [])
            for w in letters:
                ext_num = w.get("letter_number")
                if ext_num is None:
                    continue
                letter_num = int(ext_num)
                viet_text = w.get("vietnamese_text", "").strip()
                ch_text = w.get("chinese_text", "").strip()
                py_text = w.get("pinyin_text", "").strip()

                # Format prefix
                prefix = f"Bức thư {letter_num}"
                if prefix not in viet_text and f"Bức thư thứ {letter_num}" not in viet_text:
                    viet_text = f"Bức thư {letter_num}\n{viet_text}"

                all_letters[letter_num] = {
                    "chinese": ch_text,
                    "pinyin": py_text,
                    "vietnamese": viet_text,
                    "source_page": page_num
                }
                last_letter_num = letter_num
                
        else:
            # non_letter
            continue

    # Sort letters by number
    sorted_letter_nums = sorted(all_letters.keys())
    print(f"\nReconstructed {len(sorted_letter_nums)} letters.")
    
    # Run diagnostic to find gaps in sequence
    if sorted_letter_nums:
        # Check Part 1 (1 to 42)
        part1 = [n for n in sorted_letter_nums if n <= 42]
        missing_part1 = [n for n in range(1, 43) if n not in part1]
        if missing_part1:
            print(f"Missing letters in Part 1 (1-42): {missing_part1}")
            
        # Check Part 2 (562 to 695)
        part2 = [n for n in sorted_letter_nums if 562 <= n <= 695]
        missing_part2 = [n for n in range(562, 696) if n not in part2]
        if missing_part2:
            print(f"Missing letters in Part 2 (562-695): {missing_part2}")
            
        # Check Part 3 (806 to 999)
        part3 = [n for n in sorted_letter_nums if 806 <= n <= 999]
        missing_part3 = [n for n in range(806, 1000) if n not in part3]
        if missing_part3:
            print(f"Missing letters in Part 3 (806-999): {missing_part3}")

    # Output to content.md (Markdown table with 3 columns)
    # Replaces newlines with <br/> for table cell formatting
    with open(OUTPUT_MD, "w", encoding="utf-8") as md_f:
        md_f.write("# 999 Lá Thư Gửi Cho Chính Mình - Song Ngữ\n\n")
        md_f.write("| Tiếng Trung | Pinyin | Tiếng Việt |\n")
        md_f.write("|---|---|---|\n")
        
        for num in sorted_letter_nums:
            l = all_letters[num]
            ch_clean = clean_chinese(l["chinese"])
            vi_clean = clean_vietnamese(l["vietnamese"])
            ch_escaped = ch_clean.replace("\n", "<br/>").replace("|", "｜")
            py_escaped = l["pinyin"].replace("\n", "<br/>").replace("|", "｜")
            vi_escaped = vi_clean.replace("\n", "<br/>").replace("|", "｜")
            md_f.write(f"| {ch_escaped} | {py_escaped} | {vi_escaped} |\n")
            
    print(f"Saved Markdown table to {OUTPUT_MD}")

    # Output to content.csv (standard CSV format with multiline cells)
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as csv_f:
        writer = csv.writer(csv_f)
        writer.writerow(["Tiếng Trung", "Pinyin", "Tiếng Việt"])
        
        for num in sorted_letter_nums:
            l = all_letters[num]
            ch_clean = clean_chinese(l["chinese"])
            vi_clean = clean_vietnamese(l["vietnamese"])
            writer.writerow([ch_clean, l["pinyin"], vi_clean])
            
    print(f"Saved CSV file to {OUTPUT_CSV}")

if __name__ == "__main__":
    reconstruct()
