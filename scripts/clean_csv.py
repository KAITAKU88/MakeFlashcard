#!/usr/bin/env python3
import csv, os

# Paths are relative to this script location
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
INPUT_CSV = os.path.join(BASE_DIR, 'content.csv')

def clean_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as fin:
        reader = csv.reader(fin)
        rows = list(reader)
    if not rows:
        return
    # Keep columns from STT onward (index 2 onward)
    header = rows[0][2:]
    cleaned = [header]
    for row in rows[1:]:
        if len(row) < 3:
            continue
        stt = row[2].strip()
        # Skip rows without a valid STT number
        if not stt or stt == '' or stt == '---':
            continue
        cleaned.append(row[2:])
    # Overwrite the original file
    with open(path, 'w', newline='', encoding='utf-8-sig') as fout:
        writer = csv.writer(fout)
        writer.writerows(cleaned)

if __name__ == '__main__':
    clean_csv(INPUT_CSV)
