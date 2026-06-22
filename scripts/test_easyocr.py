import easyocr
import time

def test_easyocr():
    print("Initializing EasyOCR reader for Japanese and English...")
    t0 = time.time()
    reader = easyocr.Reader(['ja', 'en'])
    print(f"Reader initialized in {time.time() - t0:.2f} seconds")
    
    img_path = "/home/kaitaku/projects/MakeFlashcard/image/N2 はじめての日本語能力試験 N2単語 2500-011.png"
    print(f"Running OCR on: {img_path}")
    t0 = time.time()
    result = reader.readtext(img_path)
    print(f"OCR finished in {time.time() - t0:.2f} seconds")
    
    print("\n--- Detected Text Blocks ---")
    for i, (bbox, text, prob) in enumerate(result):
        print(f"Block {i+1}: {text} (prob: {prob:.2f})")

if __name__ == "__main__":
    test_easyocr()
