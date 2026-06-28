# Quy tắc dự án MakeFlashcard

Dự án này dùng để trích xuất từ vựng tiếng Trung từ hình ảnh sách giáo khoa trong thư mục `image/` và chuyển đổi thành tệp `content.csv` cũng như `content_chinese.pdf` dùng làm flashcard.

## Quy trình làm việc (Workflow)

1. **Phân tích sách:**
   - Xác định các trang ảnh chứa từ vựng trong thư mục `image/`.
   - Bỏ qua các trang không chứa từ vựng (ví dụ: bìa, mục lục, bài tập, trang index).
2. **Trích xuất từ vựng:**
   - Chạy kịch bản `python3 scripts/extract_chinese_vocab.py` để trích xuất từ vựng từ các trang ảnh.
   - Trích xuất trực tiếp vào `content.md`.
   - Định dạng bảng Markdown gồm 7 cột duy nhất, **không có tiêu đề chương (Chapter) hay phần (Section)**:
     `| STT | Từ vựng gốc | Từ loại | Phiên âm | Ý nghĩa | Câu ví dụ | Dịch câu ví dụ |`
   - Nếu từ vựng nào thiếu ý nghĩa, câu ví dụ và dịch câu ví dụ trong ảnh, hệ thống/AI PHẢI tự động thêm vào, đảm bảo văn phong thật tự nhiên, chính xác.
3. **Kiểm tra và Ghép:**
   - Đảm bảo toàn bộ dữ liệu từ vựng nằm trong một bảng Markdown liên tục duy nhất trong `content.md`.
   - Kiểm tra kỹ để đảm bảo không bỏ sót từ nào ở các trang chuyển tiếp.
   - Kiểm tra tính liên tục của Số Thứ Tự (STT).
4. **Chuyển đổi sang CSV & PDF:**
   - Chạy lệnh `python3 scripts/md_to_csv.py` để chuyển đổi `content.md` thành `content.csv` và tạo `content_chinese.pdf`.
   - Đảm bảo file CSV được mã hóa UTF-8 BOM để Excel hiển thị đúng tiếng Việt.
   - Đảm bảo file PDF được hiển thị khổ A4 nằm ngang, không bị lỗi font tiếng Trung hay tiếng Việt.
5. **Dọn dẹp:**
   - Xóa các file tạm sau khi hoàn thành.
   - Báo cáo số lượng từ vựng trích xuất được.

## Quy tắc bắt buộc (Mandatory Rules)

- **Tiếng Việt có dấu đầy đủ:** Tất cả phần dịch nghĩa tiếng Việt và câu ví dụ dịch sang tiếng Việt PHẢI có dấu đầy đủ, viết đúng chính tả (ví dụ: viết "công ty" chứ không viết "cong ty", "học sinh" chứ không viết "hoc sinh").
- **Bỏ qua trang không liên quan:** Bỏ qua trang bìa, mục lục, trang bài tập, trang ôn tập và index tra cứu cuối sách.
- **Tên tệp hình ảnh:** Các hình ảnh trong `image/` được sắp xếp và đặt tên theo thứ tự trang (ví dụ: `001.jpg`, `002.jpg`, ... hoặc `001.png`, `002.png`, ...).
- **Tự động bổ sung thông tin:** Đối với các từ chỉ có chữ Hán mà thiếu phiên âm, ý nghĩa, câu ví dụ hoặc bản dịch ví dụ, AI phải tự tìm hiểu/suy luận để bổ sung đầy đủ và tự nhiên nhất.
