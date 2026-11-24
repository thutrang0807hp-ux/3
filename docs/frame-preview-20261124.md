# SceneForge .167 — vùng xem ảnh kết quả lớn

Đóng app → chạy cập nhật → mở lại một cảnh ở node Ảnh khung. Không cần cài lại tiện ích hoặc đăng nhập lại.

- Vùng ảnh không còn bị các trường phía dưới ép co nhỏ. Ảnh dùng chiều cao màn hình, không méo/cắt ảnh.
- Mặc định xem toàn bộ kết quả. Các nút Kết quả / Gốc / So sánh nằm ngay trên ảnh.
- Mở ảnh lớn dùng tệp gốc đang có trong dự án (nếu có). Escape hoặc nút × để quay lại cảnh; không gửi tạo ảnh.
- Kích thước yêu cầu nằm trong mục thu gọn ở dưới ảnh, vẫn đổi được như .166. Kích thước chung trên node được giữ.
- Giữ prompt, yêu cầu chung, tiến độ, ảnh/lịch sử và cơ chế Gemini của .166. Không đổi tệp ảnh thật hay tăng độ phân giải kết quả.

Kiểm tra với node thật trên Chromium và backend/Gemini mô phỏng: vùng ảnh tối thiểu 320px, xem kết quả, mở/đóng ảnh lớn bằng Escape, so sánh và thay kích thước trong mục thu gọn; toàn bộ luồng gửi/nhận cùng các lựa chọn chung/riêng tiếp tục chạy. Cumulative builder xác nhận mọi tệp runtime ngoài workflow.html giống .166. Chưa chạy bộ cập nhật trên Windows máy bạn.

Root cause: the flex column had a capped height and all children could shrink, so the fixed-height comparison stage collapsed under the settings form. A later equal-specificity preview image rule also overrode height:100%. The stage/children now opt out of shrinking and a scoped image rule fills the stage. The size form is collapsed by default and the full-image dialog is independent of the scene editor, so opening it neither rerenders the editor nor submits another request. Background refresh defers while the lightbox is open.
