# MakeFlashcard - Trích xuất từ vựng tiếng Nhật từ ảnh

## Mục đích dự án
Trích xuất từ vựng tiếng Nhật từ ảnh sách giáo khoa (trong thư mục `image/`) và tạo file `content.csv` để làm flashcard.

## Quy trình thực hiện

Khi user yêu cầu trích xuất từ vựng (hoặc bỏ ảnh mới vào `image/`), thực hiện các bước sau:

### Bước 1: Phân tích cấu trúc sách
- Đọc 5 ảnh đầu tiên để xác định: bìa, mục lục, cấu trúc chương/section
- Xác định tổng số ảnh, phạm vi ảnh của từng chương
- Xác định format từ vựng trong sách (STT, từ, nghĩa, ví dụ...)

### Bước 2: Trích xuất song song
- Chia ảnh thành 5 nhóm theo chương (mỗi nhóm ~2 chương)
- Spawn 5 agent chạy song song, mỗi agent:
  - Đọc tất cả ảnh trong phạm vi được giao
  - Trích xuất từ vựng vào file tạm `temp_chX_Y.md`
  - Format: bảng markdown với cột: STT, Từ vựng, Ý nghĩa, Cách đọc, Câu ví dụ, Dịch câu ví dụ
- **Quan trọng**: Yêu cầu agent viết tiếng Việt CÓ DẤU đầy đủ

### Bước 3: Kiểm tra & ghép
- Kiểm tra vùng chuyển tiếp giữa các nhóm agent (ảnh ở ranh giới) để không bỏ sót từ
- Đọc tất cả file tạm, kiểm tra:
  - Tiếng Việt có dấu đầy đủ không → nếu thiếu dấu, viết lại phần đó
  - Số thứ tự liên tục không bị gián đoạn
- Ghép tất cả vào `content.md` theo thứ tự chương

### Bước 4: Tạo CSV
- Chạy `python3 scripts/md_to_csv.py` để chuyển `content.md` → `content.csv`
- Hoặc nếu script chưa có, chuyển thủ công bằng Python:
  - Encoding: UTF-8 BOM (để Excel đọc đúng)
  - Cột: Chương, Phần, STT, Từ vựng, Ý nghĩa, Cách đọc, Câu ví dụ, Dịch câu ví dụ

### Bước 5: Dọn dẹp
- Xóa tất cả file tạm `temp_*.md`
- Báo cáo tổng số từ đã trích xuất

## Cấu trúc thư mục
```
MakeFlashcard/
├── CLAUDE.md          # File này
├── image/             # Thư mục chứa ảnh sách giáo khoa
├── content.md         # Từ vựng dạng markdown (output)
├── content.csv        # Từ vựng dạng CSV (output chính)
└── scripts/
    └── md_to_csv.py   # Script chuyển md → csv
```

## Lưu ý quan trọng
- Tiếng Việt PHẢI có dấu đầy đủ (không được viết "cong ty" mà phải viết "công ty")
- Bỏ qua trang bìa, mục lục, trang bài tập/ôn tập, trang index cuối sách
- Một số từ chỉ có trong bảng minh họa (không có câu ví dụ) → để trống cột ví dụ
- Ảnh được đặt tên theo thứ tự (001, 002, ...) tương ứng với thứ tự trang trong sách
