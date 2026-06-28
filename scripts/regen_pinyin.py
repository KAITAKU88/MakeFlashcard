#!/usr/bin/env python3
"""Regenerate Pinyin for Traditional Chinese content, saving progress incrementally."""
import csv, json, os, time, requests

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
CSV_PATH = '/home/kaitaku/projects/MakeFlashcard/content.csv'
PROGRESS_PATH = '/home/kaitaku/projects/MakeFlashcard/raw_json/pinyin_progress.json'
BATCH_SIZE = 20
MODEL = "google/gemini-2.5-flash"


def load_progress():
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH, encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_progress(progress):
    with open(PROGRESS_PATH, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False)


def call_api(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.1
    }
    for attempt in range(3):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                return json.loads(content)
            else:
                print(f"  API Error {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            time.sleep(5)
    return None


def main():
    rows = []
    with open(CSV_PATH, encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            rows.append(row)

    progress = load_progress()
    total = len(rows)
    done = len(progress)
    print(f"Total: {total}, Already done: {done}")

    to_process = [i for i in range(total) if str(i + 1) not in progress]
    total_batches = (len(to_process) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"Batches remaining: {total_batches}")

    for b in range(0, len(to_process), BATCH_SIZE):
        batch_indices = to_process[b:b + BATCH_SIZE]
        batch_idx = b // BATCH_SIZE + 1

        letters_text = ""
        for idx in batch_indices:
            stt = rows[idx][0]
            ch = rows[idx][1]
            letters_text += f"[Letter {stt}]\n{ch}\n\n"

        prompt = (
            "Generate standard Hanyu Pinyin with tone marks for each Traditional Chinese text below.\n"
            "Use Taiwan Mandarin pronunciation where applicable.\n"
            "Return JSON: {\"results\": [{\"stt\": N, \"pinyin\": \"...\"}]}\n\n"
            f"{letters_text}"
        )

        result = call_api(prompt)
        if result:
            items = result.get("results", result.get("letters", []))
            for item in items:
                stt = int(item.get("stt", item.get("letter_number", 0)))
                py = item.get("pinyin", "").strip()
                if stt and py:
                    progress[str(stt)] = py
            save_progress(progress)
            print(f"Batch {batch_idx}/{total_batches} done ({len(progress)}/{total})")
        else:
            print(f"Batch {batch_idx} FAILED, will retry next run")

        time.sleep(1.5)

    # Apply to CSV
    print("\nApplying Pinyin to CSV...")
    for r in rows:
        stt = r[0]
        if stt in progress:
            r[2] = progress[stt]

    with open(CSV_PATH, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"Saved {CSV_PATH}")

    # Rebuild MD
    MD_PATH = '/home/kaitaku/projects/MakeFlashcard/content.md'
    with open(MD_PATH, 'w', encoding='utf-8') as f:
        f.write("# 999 Lá Thư Gửi Cho Chính Mình - Song Ngữ\n\n")
        f.write("| STT | Tiếng Trung | Pinyin | Tiếng Việt |\n")
        f.write("|-----|---|---|---|\n")
        for r in rows:
            c = r[1].replace("\n", "<br/>").replace("|", "｜")
            p = r[2].replace("\n", "<br/>").replace("|", "｜")
            v = r[3].replace("\n", "<br/>").replace("|", "｜")
            f.write(f"| {r[0]} | {c} | {p} | {v} |\n")
    print(f"Saved {MD_PATH}")
    print("DONE")


if __name__ == "__main__":
    main()
