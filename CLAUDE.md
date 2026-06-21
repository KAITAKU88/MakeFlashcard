# MakeFlashcard - Trích xuất từ vựng tiếng Nhật từ ảnh

## Mục đích dự án
Trích xuất từ vựng tiếng Nhật từ ảnh sách giáo khoa (trong thư mục `image/`) và tạo:
- `content.csv` — file CSV chuẩn để làm flashcard (UTF-8, không BOM)
- `content_N3.pdf` — file PDF khổ A4 nằm ngang, có đánh số trang và footer

---

## Quy trình thực hiện

Khi user yêu cầu trích xuất từ vựng (hoặc bỏ ảnh mới vào `image/`), thực hiện **đầy đủ 6 bước** sau:

### Bước 1: Phân tích cấu trúc sách
- Đọc 5 ảnh đầu tiên để xác định: bìa, mục lục, cấu trúc chương/section
- Xác định tổng số ảnh, phạm vi ảnh của từng chương
- Xác định format từ vựng trong sách (STT, từ, nghĩa, ví dụ...)
- Bỏ qua: trang bìa, mục lục, trang bài tập, trang ôn tập, trang index cuối sách

### Bước 2: Trích xuất từ vựng
- Đọc các trang ảnh tương ứng với từng chương
- Trích xuất từ vựng vào file tạm dạng Markdown (`temp_chX.md`)
- **Định dạng bảng Markdown gồm 6 cột:**
  ```
  | STT | Từ vựng | Ý nghĩa | Cách đọc | Câu ví dụ | Dịch câu ví dụ |
  |-----|---------|---------|----------|-----------|----------------|
  ```
- **Bắt buộc**: Tiếng Việt phải có dấu đầy đủ, đúng chính tả
- Từ không có câu ví dụ: để trống cột "Câu ví dụ" và "Dịch câu ví dụ"

### Bước 3: Kiểm tra & ghép
- Kiểm tra tiếng Việt có dấu đầy đủ và đúng chính tả
- Kiểm tra STT liên tục không bị gián đoạn
- Ghép tất cả dữ liệu theo cấu trúc chương/phần vào `content.md`:
  ```markdown
  ## Chapter X Tên chương
  ### Section Y Tên phần
  | STT | Từ vựng | ...
  ```

### Bước 4: Tạo CSV & PDF (chạy 1 lệnh duy nhất)
```bash
python3 scripts/md_to_csv.py
```
Lệnh này tự động:
1. Chuyển `content.md` → `content.csv` (có cột Chương, Phần — tạm thời)
2. Gọi `scripts/clean_csv.py` để xóa cột Chương/Phần, giữ từ STT trở đi
3. Gọi `scripts/md_to_pdf.py` để tạo `content_N3.pdf`

### Bước 5: Dọn dẹp
- Xóa tất cả file tạm: `rm temp_ch*.md`
- Báo cáo tổng số từ vựng đã trích xuất

---

## Thông số kỹ thuật file PDF (`content_N3.pdf`)

### Trang
- Khổ giấy: **A4 nằm ngang (Landscape)**
- Lề trái: 42pt | Lề phải: 14pt | Lề trên: 14pt | Lề dưới: 32pt

### Font chữ
| Thành phần | Font | Cỡ |
|------------|------|----|
| Header bảng | DejaVu Sans Bold | 13pt |
| STT | DejaVu Sans | 12pt |
| Từ vựng (dòng 1) | IPAGothic (CJK) / DejaVu Sans (Latin) | 12pt |
| Cách đọc (dòng 2) | IPAGothic (CJK) / DejaVu Sans (Latin) | 11pt, màu #444444 |
| Ý nghĩa, Câu ví dụ, Dịch | Mixed font | 12pt |
| Footer số trang | DejaVu Sans | 8pt |
| Footer promo | DejaVu Sans | 8pt |

### Chiến lược font (dual-font)
- Ký tự CJK (kanji, hiragana, katakana, U+3000–U+9FFF) → **IPAGothic**
  - Path: `/usr/share/fonts/truetype/fonts-japanese-gothic.ttf`
- Ký tự Latin/tiếng Việt → **DejaVu Sans**
  - Path: `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`
  - Bold: `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`

### Cấu trúc bảng
Cột Từ vựng hiển thị 2 dòng:
```
父親        ← dòng 1: từ vựng (12pt)
ちちおや    ← dòng 2: cách đọc (11pt, xám)
```

### Chiều rộng cột (fixed pt)
| Cột | Chiều rộng |
|-----|-----------|
| STT | 46pt |
| Từ vựng + Cách đọc | 145pt |
| Ý nghĩa | 108pt |
| Câu ví dụ | ~248pt (50% phần còn lại) |
| Dịch câu ví dụ | ~248pt (50% phần còn lại) |

### Footer (mỗi trang)
- Góc phải: "Trang X" (xám #555555)
- Canh trái, dòng 1: `Nơi mua các tài liệu khác: ` + `https://templatestores.com/` (màu đỏ #CC0000)
- Canh trái, dòng 2: `Học tập thông minh với hàng nghìn bộ flashcard: ` + `https://ankiva.cc/` (màu đỏ #CC0000)

---

## Thông số kỹ thuật file CSV (`content.csv`)

- Encoding: **UTF-8** (không BOM)
- Cấu trúc cột: `STT, Từ vựng, Ý nghĩa, Cách đọc, Câu ví dụ, Dịch câu ví dụ`
- Không có cột Chương/Phần (đã được `clean_csv.py` xóa)
- Các dòng không có STT hợp lệ bị loại bỏ

---

## Cấu trúc thư mục
```
MakeFlashcard/
├── CLAUDE.md              # File quy trình này
├── image/                 # Thư mục chứa ảnh sách giáo khoa (001.jpg, 002.jpg, ...)
├── content.md             # Từ vựng dạng markdown (nguồn chính)
├── content.csv            # Output CSV (STT, Từ vựng, Ý nghĩa, Cách đọc, Câu ví dụ, Dịch)
├── content_N3.pdf         # Output PDF A4 Landscape
└── scripts/
    ├── md_to_csv.py       # Chuyển content.md → content.csv (gọi 2 script dưới)
    ├── clean_csv.py       # Xóa cột Chương/Phần khỏi CSV
    └── md_to_pdf.py       # Tạo content_N3.pdf từ content.md
```

---

## Lưu ý quan trọng
- Tiếng Việt **PHẢI** có dấu đầy đủ (không được viết "cong ty" mà phải viết "công ty")
- Bỏ qua trang bìa, mục lục, trang bài tập/ôn tập, trang index cuối sách
- Ảnh được đặt tên theo thứ tự (`001.jpg`, `002.jpg`, ...) tương ứng với thứ tự trang sách
- **Sau khi hoàn thành**, xóa file tạm: `rm temp_ch*.md`
