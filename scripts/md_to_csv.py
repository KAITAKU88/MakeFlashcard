#!/usr/bin/env python3
"""Chuyển content.md thành content.csv rồi tạo content_N3.pdf.

Pipeline hoàn chỉnh:
  1. content.md  -> content.csv  (tạm có cột Chương/Phần)
  2. clean_csv.py -> xóa cột Chương/Phần, chỉ giữ từ STT trở đi
  3. md_to_pdf.py -> tạo content_N3.pdf
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
    chapter = ""
    section = ""

    with open(md_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("## Chapter"):
                chapter = line.replace("## ", "")
            elif line.startswith("### Section"):
                section = line.replace("### ", "")
            elif line.startswith("|") and not line.startswith("| STT") and not line.startswith("|---"):
                parts = [p.strip() for p in line.split("|")]
                parts = parts[1:-1]
                if len(parts) == 6:
                    rows.append([chapter, section] + parts)

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Chuong", "Phan", "STT", "Tu vung", "Y nghia", "Cach doc", "Cau vi du", "Dich cau vi du"])
        writer.writerows(rows)

    print(f"Da tao {csv_path} voi {len(rows)} tu vung")
    return md_path, csv_path


def run_pipeline():
    md_path, csv_path = convert()

    # Buoc 2: Xoa cot Chuong/Phan khoi CSV
    clean_script = os.path.join(SCRIPTS_DIR, "clean_csv.py")
    print("Dang lam sach CSV (xoa cot Chuong/Phan)...")
    subprocess.run([sys.executable, clean_script], check=True)

    # Buoc 3: Tao PDF
    pdf_script = os.path.join(SCRIPTS_DIR, "md_to_pdf.py")
    pdf_path   = os.path.join(PROJECT_DIR, "content_N3.pdf")
    print("Dang tao PDF...")
    subprocess.run([sys.executable, pdf_script, md_path, pdf_path], check=True)


if __name__ == "__main__":
    run_pipeline()
