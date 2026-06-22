#!/usr/bin/env python3
import os

def remove_duplicates(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()
    new_lines = []
    i = 0
    n = len(lines)
    
    while i < n:
        # Check duplicate for 147-153 (index difference is 11)
        if i + 22 < n and lines[i].startswith("| 147 | 奥 |") and lines[i+11].startswith("| 147 | 奥 |"):
            match = True
            for offset in range(11):
                l1 = "".join(lines[i+offset].split())
                l2 = "".join(lines[i+11+offset].split())
                if l1 != l2:
                    match = False
                    break
            if match:
                print("Removing duplicate block 147-153 at line", i+1)
                new_lines.extend(lines[i:i+11])
                i += 22
                continue

        # Check duplicate for 382 onwards (8 rows)
        if i + 16 < n and (lines[i].startswith("| 382 | 一変 |") or lines[i].startswith("| 382 | 一変する |")) and (lines[i+8].startswith("| 382 | 一変 |") or lines[i+8].startswith("| 382 | 一変する |")):
            match = True
            for offset in range(8):
                l1 = "".join(lines[i+offset].split())
                l2 = "".join(lines[i+8+offset].split())
                # Allow minor differences in '一変（する）' vs '一変する'
                l1 = l1.replace("（する）", "").replace("する", "")
                l2 = l2.replace("（する）", "").replace("する", "")
                if l1 != l2:
                    match = False
                    break
            if match:
                print("Removing duplicate block 382-384 at line", i+1)
                new_lines.extend(lines[i:i+8])
                i += 16
                continue

        new_lines.append(lines[i])
        i += 1

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")

if __name__ == "__main__":
    remove_duplicates("/home/kaitaku/projects/MakeFlashcard/content.md")
