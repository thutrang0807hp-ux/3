# Kho kịch bản v3

Triển khai ngày 24/10/2026 theo `design/script-library-v3/KHO_KICH_BAN_V3.md` và ảnh kèm theo. Tài liệu nhận vào là đặc tả tham khảo; phần triển khai giữ kết quả thật và các quyết định đã trao đổi.

## Giao diện

Ba cột trong cùng khung: nhóm / danh sách / chi tiết. Màu nền, viền lime, thẻ nhịp màu và mật độ theo ảnh mẫu. Cột giữa và chi tiết cuộn riêng, không đẩy toàn trang. Màn hình hẹp giữ ba cột và cuộn ngang bên trong, không làm rộng trang. Thanh điều hướng chung giữ nguyên.

- Đã đạt, Tất cả, Chờ xếp nhóm, chủ đề, sản phẩm và Thùng rác.
- Chủ đề thêm, đổi tên bằng nút hoặc nháy đúp, kéo đổi thứ tự; một chủ đề / nhiều sản phẩm mỗi công thức.
- Tìm tên và câu mẫu; sắp hiệu quả, mới dùng, tên. Đạt luôn ở đầu trong phạm vi bộ lọc.
- Thẻ có Đạt, Nhân bản, Xóa; nút hiển thị mờ và rõ khi hover/focus, không bị giấu hoàn toàn.
- Mặc định xem chi tiết, chỉ bấm Sửa mới hiện form; các nhịp gập/mở được. Có trạng thái Bỏ ẩn khỏi gợi ý.
- Tổng quan khi chưa chọn: số công thức, Đạt, đang thử, chờ xếp nhóm; top theo số video được ghi ra đơn; video đã xuất chờ ghi kết quả.
- Lịch sử, hộp ghi kết quả (Ra đơn / Tạm / Không ăn thua), số đơn/lượt xem tùy chọn, ghi chú. Cùng hộp mở từ thẻ Đã xuất trên trang chủ.
- Dùng công thức tạo phòng từ ảnh thật, dùng bộ ảnh của sản phẩm vừa chọn, sao chép nhịp và lời nếu có.

## Dữ liệu và giới hạn

Giữ bản ghi `recipe-library` đang dùng; nâng schema lên v3 và sử dụng cơ chế lưu kho SQLite/snapshot cục bộ đã có, không tạo kho SQL khác cạnh dữ liệu cũ. Bản Pages mô phỏng lưu riêng trong IndexedDB, không tạo nội dung AI hoặc gọi API.

- Giữ các công thức, phiếu và lần dùng cũ; lịch sử cũ thiếu ngày hiện Chưa ghi ngày, không tự bịa ngày hoặc bản chụp quá khứ.
- Các lần dùng mới giữ bản chụp công thức theo video; sửa công thức không đổi nhịp/lời hay bản chụp của video đã có.
- Tính lần dùng theo cặp video/công thức để không tăng lượt khi bấm lại trong cùng video. Tên video/sản phẩm lưu trong lần dùng nên vẫn đọc được khi phòng đã dọn.
- Tỉ số là số video ghi Ra đơn / số video đã ghi kết quả; số lần dùng hiển thị riêng. Chưa ghi khác 0. Tổng đơn chỉ cộng số nhập tay.
- Nhân bản không sao chép lượt dùng, phiếu, kết quả hoặc điểm AI.
- Khung sườn mới từ video mẫu/nhập video vào Chờ xếp nhóm, không tự gợi ý trong workflow trước khi phân nhóm. Vẫn có thể chủ động dùng từ kho chung.
- Xóa mềm giữ đầy đủ công thức để khôi phục; mặc định dọn sau 30 ngày, tùy chọn 7/30/90 hoặc không tự xóa. Việc dọn diễn ra khi mở/truy cập kho, không chạy daemon khi app tắt. Không xóa video hoặc lịch sử lần dùng. Tombstone vẫn ngăn tự rút lại công thức đã xóa. Các công thức bị xóa theo phiên bản cũ (chỉ còn ID) không thể dựng lại nội dung đã mất.
- Không tự gọi AI để chấm điểm/xếp nhóm. Chưa có điểm thật thì hiện AI —. Chưa làm nhắc thông báo sau nhiều ngày; có danh sách chờ ghi trong tổng quan. Không cài Langfuse.

## Kiểm tra

`PYTHONPATH=/workspace/.sceneforge-test-deps python scripts/app-shell/check_recipe_library_v3.py` kiểm migration, chỉnh sửa/validation, bản chụp phòng giữ nguyên, mẫu số chỉ tính đã ghi, xếp nhóm hàng loạt, khôi phục đầy đủ, mở lại vẫn còn, thêm chủ đề/nhân bản/Đạt, khung ổn định, trang hẹp không tràn và nút Dùng mở workflow thật đúng nhịp. Không gọi nhà cung cấp AI.

Các bài Storyboard và ổn định chuyển tab được cập nhật kỳ vọng tương ứng với thiết kế v3 (bấm Sửa mới mở form, khung ba cột thay tiêu đề cũ), giữ các kiểm tra bảo toàn dữ liệu/camera/iframe. Phần ảnh kiểm tra viewport nằm ngay sau thanh chọn Gemini/Muse cao 58 px đã có từ trước; không còn kỳ vọng thanh này không tồn tại.
