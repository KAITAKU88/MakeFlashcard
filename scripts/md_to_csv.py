#!/usr/bin/env python3
"""Chuyển content.md (7 cột) thành content.csv rồi tạo content_chinese.pdf.

Pipeline hoàn chỉnh:
  1. content.md  -> content.csv  (7 cột)
  2. clean_csv.py -> xác thực/làm sạch CSV
  3. md_to_pdf.py -> tạo content_chinese.pdf (7 cột)
"""

import csv
import sys
import os
import subprocess

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPTS_DIR)


def convert(md_path=None, csv_path=None):
    if md_path is None:
        md_path = os.path.join(PROJECT_DIR, "content.md")
    if csv_path is None:
        csv_path = os.path.join(PROJECT_DIR, "content.csv")

    rows = []

    if not os.path.exists(md_path):
        print(f"Error: {md_path} does not exist. Run extract_chinese_vocab.py first.")
        return md_path, csv_path

    with open(md_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Bỏ qua dòng header và phân tách bảng
            if line.startswith("|") and not (
                line.startswith("| STT") or
                line.startswith("|---|") or
                line.startswith("|-----")
            ):
                parts = [p.strip() for p in line.split("|")]
                parts = parts[1:-1]
                if len(parts) >= 7:
                    stt = parts[0].strip()
                    vocab = parts[1].replace("<br/>", "\n").replace("｜", "|")
                    pos = parts[2].replace("<br/>", "\n").replace("｜", "|")
                    pinyin = parts[3].replace("<br/>", "\n").replace("｜", "|")
                    meaning = parts[4].replace("<br/>", "\n").replace("｜", "|")
                    example = parts[5].replace("<br/>", "\n").replace("｜", "|")
                    translation = parts[6].replace("<br/>", "\n").replace("｜", "|")
                    rows.append([stt, vocab, pos, pinyin, meaning, example, translation])

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["STT", "Từ vựng gốc", "Từ loại", "Phiên âm", "Ý nghĩa", "Câu ví dụ", "Dịch câu ví dụ"])
        writer.writerows(rows)

    print(f"Đã tạo {csv_path} với {len(rows)} từ vựng.")
    return md_path, csv_path


def run_pipeline():
    md_path, csv_path = convert()

    # Bước 2: Làm sạch CSV
    clean_script = os.path.join(SCRIPTS_DIR, "clean_csv.py")
    print("Đang chạy clean_csv.py...")
    subprocess.run([sys.executable, clean_script], check=True)

    # Bước 3: Tạo PDF
    pdf_script = os.path.join(SCRIPTS_DIR, "md_to_pdf.py")
    pdf_path   = os.path.join(PROJECT_DIR, "content_chinese.pdf")
    print("Đang tạo PDF...")
    subprocess.run([sys.executable, pdf_script, md_path, pdf_path], check=True)


if __name__ == "__main__":
    run_pipeline()
