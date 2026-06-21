# Quy tắc dự án MakeFlashcard

Dự án này dùng để trích xuất từ vựng tiếng Nhật từ hình ảnh sách giáo khoa trong thư mục `image/` và chuyển đổi thành tệp `content.csv` dùng làm flashcard.

## Quy trình làm việc (Workflow)

1. **Phân tích sách:** 
   - Đọc 5 hình ảnh đầu tiên trong thư mục `image/` để xác định cấu trúc sách (bìa, mục lục, cách tổ chức chương/phần, và định dạng từ vựng).
   - Xác định tổng số trang ảnh và phạm vi ảnh của từng chương.
2. **Trích xuất từ vựng:**
   - Đọc qua các trang ảnh tương ứng với từng chương.
   - Trích xuất từ vựng vào file tạm dạng Markdown (`temp_chX.md` hoặc trực tiếp vào `content.md`).
   - Định dạng bảng Markdown gồm 6 cột: STT, Từ vựng, Ý nghĩa, Cách đọc, Câu ví dụ, Dịch câu ví dụ.
3. **Kiểm tra và Ghép:**
   - Ghép toàn bộ dữ liệu từ vựng theo cấu trúc chương/phần vào file `content.md`.
   - Kiểm tra kỹ để đảm bảo không bỏ sót từ nào ở các trang chuyển tiếp.
   - Kiểm tra tính liên tục của Số Thứ Tự (STT).
4. **Chuyển đổi sang CSV:**
   - Chạy lệnh `python3 scripts/md_to_csv.py` để chuyển đổi `content.md` thành `content.csv`.
   - Đảm bảo file CSV được mã hóa UTF-8 BOM để Excel hiển thị đúng tiếng Việt.
5. **Dọn dẹp:**
   - Xóa các file tạm `temp_*.md` sau khi hoàn thành.
   - Báo cáo số lượng từ vựng trích xuất được.

## Quy tắc bắt buộc (Mandatory Rules)

- **Tiếng Việt có dấu đầy đủ:** Tất cả phần dịch nghĩa tiếng Việt và câu ví dụ dịch sang tiếng Việt PHẢI có dấu đầy đủ, viết đúng chính tả (ví dụ: viết "công ty" chứ không viết "cong ty", "học sinh" chứ không viết "hoc sinh").
- **Bỏ qua trang không liên quan:** Bỏ qua trang bìa, mục lục, trang bài tập, trang ôn tập và index tra cứu cuối sách.
- **Xử lý từ không có ví dụ:** Với các từ chỉ xuất hiện trong bảng từ vựng phụ không đi kèm ví dụ, hãy để trống cột Câu ví dụ và Dịch câu ví dụ.
- **Tên tệp hình ảnh:** Các hình ảnh trong `image/` được sắp xếp và đặt tên theo thứ tự trang (ví dụ: `001.jpg`, `002.jpg`, ...).
