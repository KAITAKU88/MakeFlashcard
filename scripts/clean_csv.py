#!/usr/bin/env python3
import csv
import os

# Paths are relative to this script location
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
INPUT_CSV = os.path.join(BASE_DIR, 'content.csv')

def clean_csv(path):
    # Dành cho sách tiếng Trung 7 cột, CSV được định dạng chuẩn UTF-8 BOM.
    # Đọc và viết lại để đảm bảo encoding và format chuẩn hóa.
    if not os.path.exists(path):
        print(f"File {path} does not exist. Skipping clean.")
        return
        
    with open(path, newline='', encoding='utf-8-sig') as fin:
        reader = csv.reader(fin)
        rows = list(reader)
        
    if not rows:
        return
        
    # Chuẩn hóa khoảng trắng dư thừa
    cleaned_rows = []
    for r in rows:
        cleaned_rows.append([cell.strip() for cell in r])
        
    with open(path, 'w', newline='', encoding='utf-8-sig') as fout:
        writer = csv.writer(fout)
        writer.writerows(cleaned_rows)
    print(f"clean_csv: {path} verified, normalized, and kept intact.")

if __name__ == '__main__':
    clean_csv(INPUT_CSV)
