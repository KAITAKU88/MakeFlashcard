import sys
import base64
import requests
import os

API_KEY = "YOUR_GEMINI_API_KEY_HERE"  # Thay bằng API key thực của bạn
MODEL_ID = "gemini-flash-lite-latest"

def ocr_text(page_num):
    img_path = f"/home/kaitaku/projects/MakeFlashcard/image/N1-はじめて of 日本語能力試験Ｎ１単語 3000-{page_num:03d}.png"
    # Find matching filename with glob to handle different name formats if any
    import glob
    matches = glob.glob(f"/home/kaitaku/projects/MakeFlashcard/image/*-{page_num:03d}.png")
    if not matches:
        print(f"Error: No image found for page {page_num}")
        return None
    img_path = matches[0]
        
    with open(img_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode("utf-8")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent?key={API_KEY}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": {
            "role": "user",
            "parts": [
                {
                    "inlineData": {
                        "mimeType": "image/png",
                        "data": img_data
                    }
                },
                {
                    "text": "Please transcribe all text from this image page. If it is a Japanese book page, maintain the layout and structure as much as possible."
                }
            ]
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return text
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 ocr_text.py <page_num>")
        sys.exit(1)
    page_num = int(sys.argv[1])
    res = ocr_text(page_num)
    if res:
        print(res)
