# MakeFlashcard - Trích xuất từ vựng tiếng Trung từ ảnh

## Mục đích dự án
Trích xuất từ vựng tiếng Trung từ ảnh sách giáo khoa (trong thư mục `image/`) và tạo:
- `content.csv` — file CSV chuẩn để làm flashcard (UTF-8, có BOM để hỗ trợ Excel tiếng Việt)
- `content_chinese.pdf` — file PDF khổ A4 nằm ngang, có đánh số trang và footer, hiển thị duy nhất bảng 7 cột từ vựng không có tiêu đề chapter hay section.

---

## Quy trình thực hiện

Khi có ảnh mới trong `image/` và cần trích xuất từ vựng, thực hiện các bước sau:

### Bước 1: Xác định phạm vi trang ảnh
- Xác định các trang ảnh chứa từ vựng trong thư mục `image/`.
- Bỏ qua: trang bìa, mục lục, trang bài tập, trang ôn tập, trang index cuối sách.

### Bước 2: Trích xuất từ vựng
- Chạy kịch bản:
  ```bash
  python3 scripts/extract_chinese_vocab.py <start_page> <end_page> content.md
  ```
- Kịch bản này sẽ tự động:
  - OCR các trang ảnh từ `image/`.
  - Phân tích và trích xuất từ vựng với cấu trúc 7 cột: `STT | Từ vựng gốc | Từ loại | Phiên âm | Ý nghĩa | Câu ví dụ | Dịch câu ví dụ`.
  - **Tự động sinh/bổ sung** ý nghĩa, câu ví dụ hoặc bản dịch câu ví dụ nếu trong ảnh bị thiếu hoặc không đầy đủ, đảm bảo văn phong tự nhiên và chuẩn xác.
  - Định dạng và ghi tiếp trực tiếp vào bảng Markdown liên tục trong `content.md`.

### Bước 3: Kiểm tra
- Kiểm tra tiếng Việt có dấu đầy đủ và đúng chính tả.
- Kiểm tra STT liên tục không bị gián đoạn.
- Đảm bảo trong `content.md` chỉ chứa duy nhất một bảng từ vựng Markdown, không chứa bất kỳ tiêu đề `#`, `##` hay `###` nào khác.

### Bước 4: Tạo CSV & PDF (chạy 1 lệnh duy nhất)
```bash
python3 scripts/md_to_csv.py
```
Lệnh này tự động:
1. Chuyển `content.md` → `content.csv` (7 cột)
2. Gọi `scripts/clean_csv.py` để định dạng lại và xác thực tính hợp lệ của CSV
3. Gọi `scripts/md_to_pdf.py` để tạo `content_chinese.pdf`

### Bước 5: Dọn dẹp
- Báo cáo tổng số từ vựng đã trích xuất.

---

## Thông số kỹ thuật file PDF (`content_chinese.pdf`)

### Trang
- Khổ giấy: **A4 nằm ngang (Landscape)**
- Lề trái: 42pt | Lề phải: 14pt | Lề trên: 14pt | Lề dưới: 32pt

### Font chữ (dual-font)
- Ký tự tiếng Trung (Hán tự) -> **NotoSansSC**
  - Path: `/home/kaitaku/projects/MakeFlashcard/fonts/NotoSansSC-Variable.ttf` (hoặc NotoSansCJKsc)
- Ký tự Latin/tiếng Việt/Phiên âm Pinyin -> **DejaVu Sans**
  - Path: `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`
  - Bold: `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`

### Chiều rộng cột (Tổng cộng ~785pt khả dụng)
| Cột | Chiều rộng (pt) | Mô tả |
|-----|-----------|---|
| STT | 30 pt | Số thứ tự |
| Từ vựng gốc | 80 pt | Chữ Hán giản thể/phồn thể |
| Từ loại | 60 pt | Danh từ, động từ, tính từ, v.v. |
| Phiên âm | 90 pt | Pinyin có dấu thanh |
| Ý nghĩa | 130 pt | Nghĩa tiếng Việt đầy đủ |
| Câu ví dụ | 200 pt | Ví dụ bằng chữ Hán |
| Dịch câu ví dụ | 195 pt | Dịch nghĩa ví dụ sang tiếng Việt |

### Footer (mỗi trang)
- Góc phải: "Trang X" (xám #555555)
- Canh trái, dòng 1: `Nơi mua các tài liệu khác: ` + `https://templatestores.com/` (màu đỏ #CC0000)
- Canh trái, dòng 2: `Học tập thông minh với hàng nghìn bộ flashcard: ` + `https://ankiva.cc/` (màu đỏ #CC0000)

---

## Thông số kỹ thuật file CSV (`content.csv`)

- Encoding: **UTF-8 with BOM** (hỗ trợ hiển thị đúng tiếng Việt có dấu trên Microsoft Excel)
- Tiêu đề cột: `STT, Từ vựng gốc, Từ loại, Phiên âm, Ý nghĩa, Câu ví dụ, Dịch câu ví dụ`

---

## Cấu trúc thư mục
```
MakeFlashcard/
├── CLAUDE.md              # File quy trình này
├── image/                 # Thư mục chứa ảnh sách giáo khoa (001.jpg, 002.jpg, ...)
├── content.md             # Từ vựng dạng markdown (nguồn chính, 7 cột)
├── content.csv            # Output CSV (7 cột)
├── content_chinese.pdf    # Output PDF A4 Landscape
└── scripts/
    ├── extract_chinese_vocab.py # Trích xuất và bổ sung từ vựng tiếng Trung từ ảnh
    ├── md_to_csv.py       # Chuyển content.md → content.csv
    ├── clean_csv.py       # Định dạng/xác thực file CSV
    └── md_to_pdf.py       # Tạo content_chinese.pdf từ content.md
```
