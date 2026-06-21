#!/usr/bin/env python3
"""Chuyển content.md (bảng markdown từ vựng) thành content.csv"""

import csv
import sys
import os

def convert(md_path="content.md", csv_path="content.csv"):
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    md_path = os.path.join(project_dir, md_path)
    csv_path = os.path.join(project_dir, csv_path)

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

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Chương", "Phần", "STT", "Từ vựng", "Ý nghĩa", "Cách đọc", "Câu ví dụ", "Dịch câu ví dụ"])
        writer.writerows(rows)

    print(f"Đã tạo {csv_path} với {len(rows)} từ vựng")

if __name__ == "__main__":
    md_file = sys.argv[1] if len(sys.argv) > 1 else "content.md"
    csv_file = sys.argv[2] if len(sys.argv) > 2 else "content.csv"
    convert(md_file, csv_file)
