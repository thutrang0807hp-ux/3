# Code gọn — xem lần này đã làm gì

Luồng cần đánh giá: **Ảnh + kịch bản → một storyboard tổng → prompt từng clip →
Bộ cảnh video → xem/chốt cả bản ghép → Dựng.**

Đây là code nguyên bản của bản đã đẩy `170a49b`, kèm diff thật so với `0bff642`.
Chỉ đóng gói để đọc; không sửa hoặc rút ngắn logic app.

Đọc 3 file trước:

1. **review/LAN_NAY_SUA_GI.md**: thay đổi cụ thể và file/hàm thực hiện.
2. **scripts/photo-studio/edit-safety.js**: xử lý đổi mốc/công thức/ảnh/giọng; nạp sau story-production.js.
3. **review/DE_BAI_DANH_GIA.md**: câu hỏi để kiểm độc lập, không mặc định code đúng.

Muốn thấy đúng dòng đã thêm/sửa: **review/THAY_DOI.patch**.
Muốn lần engine/tài khoản/kho/editor: **review/BAN_DO.md** rồi mở các file gốc.
**docs/photo-story-production.md** mô tả cách dùng; đó là mô tả của người viết code,
không thay thế việc đọc code và kiểm chứng.

Gói này bỏ media/model/font, HTML đã build và các phần UI/module ngoài phạm vi.
Các file dùng chung được giữ nguyên nên vẫn có nhánh không thuộc luồng ảnh.
Đây là gói đọc code, không phải app độc lập; thiếu dependency ngoài phạm vi ở đây
không chứng minh app đầy đủ thiếu dependency. Danh sách bỏ nằm trong BAN_DO.md.
Bài test đi kèm cần app đầy đủ, Chromium/backend và media mẫu mới chạy được.

Báo cáo PHOTO_EDIT_SAFETY_CHECKS.json ghi các phép kiểm đã chạy trên app đầy đủ:
trình duyệt, SQLite và editor thật; phản hồi AI là transport fixture. Chưa thử
Windows hoặc gen online bằng tài khoản thật. Muse adapter đang là muse.ai,
chưa xác minh Meta AI. Không coi preview timeline là MP4 đã xuất.

Kiểm tính toàn vẹn sau giải nén: `python review/verify_package.py`.
Nếu cần truy vết phần đã lược bỏ, dùng gói đầy đủ đã công bố:
https://raw.githubusercontent.com/thutrang0807hp-ux/3/170a49b/downloads/SceneForge-TuAnh-DanhGia-Luong.zip
