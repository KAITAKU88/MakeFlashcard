import os
import glob
import json
import re
import sys

RAW_DIR = "/home/kaitaku/projects/MakeFlashcard/raw_json"

def clean_text(text):
    if not text:
        return ""
    return str(text).replace("\n", " ").replace("|", "｜").strip()

def strip_korean(text):
    if not text:
        return ""
    # 1. Remove Korean character blocks (Hangul syllables, Jamo)
    text = re.sub(r'[\uac00-\ud7a3\u1100-\u11ff\u3130-\u318f\u302e\u302f\u11a8-\u11f9]+', '', text)
    
    # Remove empty angle brackets <> (often left from Korean <하다>)
    text = re.sub(r'<\s*>', '', text)
    
    # 2. Clean up punctuation around deleted Korean
    # Remove empty parenthesis like (), [], or ( / ), ( - )
    text = re.sub(r'\(\s*[-/｜|·;,\s]*\)', '', text)
    text = re.sub(r'\[\s*[-/｜|·;,\s]*\]', '', text)
    
    # Remove empty bullet points left behind: e.g. "① . ②" -> "②"
    for _ in range(5):
        text = re.sub(r'[①②③④⑤⑥⑦⑧⑨⑩]\s*[\.\,\s\/\-\—]*\s*(?=[①②③④⑤⑥⑦⑧⑨⑩])', '', text)
    
    # Remove trailing empty bullet if it's empty at the very end
    text = re.sub(r'[①②③④⑤⑥⑦⑧⑨⑩]\s*[\.\,\s\/\-\—]*$', '', text)
    
    # Clean up leading/trailing slashes, dashes, spaces, and duplicate delimiters
    text = re.sub(r'\s*[/｜|·;,—~-]+\s*[/｜|·;,—~-]+\s*', ' / ', text) # normalize duplicates
    
    # Strip leading/trailing punctuation characters commonly left over
    text = text.strip(',;./\\ —|｜·-—~')
    
    # Remove wrapping parentheses or brackets if they enclose the whole string
    if text.startswith('(') and text.endswith(')'):
        text = text[1:-1].strip()
    if text.startswith('[') and text.endswith(']'):
        text = text[1:-1].strip()
    
    text = text.strip(',;./\\ —|｜·-—~')
    
    # Normalize bullet points spacing
    text = re.sub(r'\s*([①②③④⑤⑥⑦⑧⑨⑩])\s*[\.\s]*', r' \1 ', text)
    
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove double periods
    text = re.sub(r'\.\s*\.', '.', text)
    
    text = text.strip(',;./\\ —|｜·-—~')
    if text.startswith('(') and text.endswith(')'):
        text = text[1:-1].strip()
    if text.startswith('[') and text.endswith(']'):
        text = text[1:-1].strip()
    text = text.strip(',;./\\ —|｜·-—~')
    
    return text.strip()

def get_chapter_section_by_page(page_num):
    # Mapping table mapping page range limits to Chapter and Section
    # Format: (max_page_limit, chapter_title, section_title)
    mapping = [
        (83, "Chapter 4: 学校で (Ở trường)", {
            67: "Section 1: 学校 (Trường học)",
            72: "Section 2: 勉強 (Học tập)",
            76: "Section 3: 試験 (Thi cử)",
            81: "Section 4: 進学 (Học lên cao)",
            83: "Section 5: パソコン・スマホ (Máy tính, điện thoại thông minh)",
        }),
        (107, "Chapter 5: 会社で (Ở công sở / Trong công việc)", {
            91: "Section 1: 就職 (Tìm việc)",
            93: "Section 2: 企業 (Doanh nghiệp)",
            98: "Section 3: 仕事 (Công việc)",
            103: "Section 4: 上下関係 (Quan hệ cấp trên và cấp dưới)",
            107: "Section 5: 退職・転職 (Nghỉ việc - Chuyển việc)",
        }),
        (127, "Chapter 6: 私の町 (Thị trấn của tôi)", {
            112: "Section 1: 街 (Phố thị)",
            115: "Section 2: 公共 (Công cộng)",
            119: "Section 3: 交通 (Giao thông)",
            122: "Section 4: 産業 (Công nghiệp)",
            127: "Section 5: 故郷 (Quê nhà)",
        }),
        (147, "Chapter 7: 健康 (Sức khỏe)", {
            132: "Section 1: 体 và thể chất (Thể chất và cơ thể)", # Let's write Section 1: 体と体質 (Thể chất và cơ thể)
            135: "Section 2: 症状① (Triệu chứng 1)",
            138: "Section 3: 症状② (Triệu chứng 2)",
            142: "Section 4: 病気・けが (Bệnh tật và chấn thương)",
            147: "Section 5: 美容 (Làm đẹp)",
        }),
        (173, "Chapter 8: お気に入り (Sở thích/Yêu thích)", {
            153: "Section 1: 競技 (Thi đấu)",
            157: "Section 2: ファッション (Thời trang)",
            161: "Section 3: 習い事 (Học tập/Năng khiếu)",
            167: "Section 4: 本 (Sách vở)",
            173: "Section 5: エンターテインメント (Giải trí)",
        }),
        (193, "Chapter 9: 世界 (Thế giới)", {
            178: "Section 1: 旅のプラン (Kế hoạch du lịch)",
            182: "Section 2: 旅行先で (Tại điểm du lịch)",
            186: "Section 3: 地理 (Địa lý)",
            190: "Section 4: 国際関係① (Quan hệ quốc tế 1)",
            193: "Section 5: 国際関係② (Quan hệ quốc tế 2)",
        }),
        (215, "Chapter 10: 自然 (Tự nhiên)", {
            198: "Section 1: 気象 (Thời tiết/Khí tượng)",
            203: "Section 2: 災害 (Thiên tai)",
            207: "Section 3: 地球環境 (Môi trường trái đất)",
            211: "Section 4: 大自然 (Thiên nhiên hùng vĩ)",
            215: "Section 5: 動植物 (Động thực vật)",
        }),
        (237, "Chapter 11: ニュース (Tin tức)", {
            220: "Section 1: 事故 (Tai nạn)",
            224: "Section 2: 事件・トラブル (Sự cố / rắc rối)",
            229: "Section 3: 社会 (Xã hội)",
            233: "Section 4: 政治 (Chính trị)",
            237: "Section 5: 経済 (Kinh tế)",
        }),
        (255, "Chapter 12: イメージ (Hình ảnh/Ấn tượng)", {
            242: "Section 1: 性格 (Tính cách)",
            244: "Section 2: いい気分 (Tâm trạng tốt)",
            247: "Section 3: ブルーな気分 (Tâm trạng u ám)",
            250: "Section 4: プラスのイメージ (Ấn tượng tích cực)",
            255: "Section 5: マイナスのイメージ (Ấn tượng tiêu cực)",
        }),
        (271, "Chapter 13: 表現 Part 1 (Diễn đạt Part 1)", {
            258: "Section 1: 副詞① (Phó từ 1)",
            260: "Section 2: 副詞② (Phó từ 2)",
            263: "Section 3: 副詞③・その他 (Phó từ 3 - Các cụm từ khác)",
            267: "Section 4: まぎらわしい言葉① (Từ dễ gây nhầm lẫn 1)",
            271: "Section 5: まぎらわしい言葉② (Từ dễ gây nhầm lẫn 2)",
        }),
        (292, "Chapter 14: 表現 Part 2 (Diễn đạt Part 2)", {
            275: "Section 1: 慣用句：顔 (Quán dụng ngữ: Bộ phận mặt)",
            278: "Section 2: 慣用句：体 (Quán dụng ngữ: Bộ phận cơ thể)",
            281: "Section 3: 慣用句：その他 (Quán dụng ngữ: Bộ phận khác)",
            285: "Section 4: いろいろな意味を持つ言葉① (Từ đa nghĩa 1)",
            292: "Section 5: いろいろな意味を持つ言葉② (Từ đa nghĩa 2)",
        }),
    ]

    # Fix specific chapter 7 label mapping typo
    ch7_sec1 = "Section 1: 体と体質 (Thể chất và cơ thể)"

    for limit, ch_title, sections in mapping:
        if page_num <= limit:
            for sec_limit in sorted(sections.keys()):
                if page_num <= sec_limit:
                    sec_title = sections[sec_limit]
                    if "体" in sec_title and "thể chất" in sec_title:
                        sec_title = ch7_sec1
                    return ch_title, sec_title
            sec_title = sections[max(sections.keys())]
            if "体" in sec_title and "thể chất" in sec_title:
                sec_title = ch7_sec1
            return ch_title, sec_title
            
    return "", ""

def parse_all_to_md(output_file):
    json_files = sorted(glob.glob(os.path.join(RAW_DIR, "page_*.json")))
    if not json_files:
        print("No JSON files found to process.")
        return
        
    all_words = []
    
    for fpath in json_files:
        basename = os.path.basename(fpath)
        page_num = int(re.search(r'page_(\d+)\.json', basename).group(1))
        
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        current_chapter, current_section = get_chapter_section_by_page(page_num)

        if not data.get("is_vocabulary_page", False):
            continue
            
        words = data.get("words", [])
        for w in words:
            if not w.get("vocab"):
                continue
                
            word_entry = {
                "stt": clean_text(w.get("stt", "")),
                "vocab": clean_text(w.get("vocab", "")),
                "meaning": strip_korean(clean_text(w.get("meaning", ""))),
                "reading": clean_text(w.get("reading", "")),
                "example": clean_text(w.get("example", "")),
                "translation": strip_korean(clean_text(w.get("translation", ""))),
                "chapter": current_chapter,
                "section": current_section,
                "page": page_num
            }
            all_words.append(word_entry)
            
    # Group words by Chapter and Section
    grouped = {}
    for w in all_words:
        ch = w["chapter"]
        sec = w["section"]
        if ch not in grouped:
            grouped[ch] = {}
        if sec not in grouped[ch]:
            grouped[ch][sec] = []
        grouped[ch][sec].append(w)
        
    def extract_num(text):
        m = re.search(r'\d+', text)
        return int(m.group(0)) if m else 999

    # Write to Markdown
    with open(output_file, "w", encoding="utf-8") as out_f:
        for ch, sections in sorted(grouped.items(), key=lambda item: extract_num(item[0])):
            if ch:
                out_f.write(f"\n## {ch}\n")
            for sec, words in sorted(sections.items(), key=lambda item: extract_num(item[0])):
                if sec:
                    out_f.write(f"\n### {sec}\n\n")
                out_f.write("| STT | Từ vựng | Ý nghĩa | Cách đọc | Câu ví dụ | Dịch câu ví dụ |\n")
                out_f.write("|-----|---------|---------|----------|-----------|----------------|\n")
                
                seen_stts = set()
                for w in words:
                    stt = w["stt"]
                    if stt:
                        if stt in seen_stts:
                            print(f"Warning: Duplicate STT {stt} found for word {w['vocab']} in section {sec}!")
                        seen_stts.add(stt)
                    out_f.write(f"| {w['stt']} | {w['vocab']} | {w['meaning']} | {w['reading']} | {w['example']} | {w['translation']} |\n")
                    
    print(f"Successfully generated Markdown output: {output_file}")
    print(f"Total vocabulary items: {len(all_words)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 json_to_md.py <output_file>")
        sys.exit(1)
    parse_all_to_md(sys.argv[1])
