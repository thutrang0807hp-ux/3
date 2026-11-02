# SceneForge v46.37 — báo cáo cấu trúc media và iframe

1. Đóng SceneForge, chạy SceneForge-Update-20261102-v46.37-Media-Structure.exe, chọn thư mục có SceneForge.exe và install-settings.json. Yêu cầu v46.7 trở lên.
2. Mở đúng phòng và tài khoản đã gửi video. Không chọn mã hoặc tạo lại.
3. Trong node Veo, bấm **Tự kiểm tra video đã gửi và tải báo cáo** ở phần Video đã gửi chưa nhận được kết quả.
4. Gửi file SceneForge-theo-doi-video.json. Báo cáo .37 thêm media_structure: vùng bao quanh thumbnail/media, nhãn và nút, từng iframe hiển thị, shadow DOM mở. Iframe ẩn/lỗi hoặc hết budget có ghi lý do riêng.

Quét cấu trúc chỉ khi người dùng tải báo cáo; theo dõi định kỳ vẫn dùng snapshot nhẹ. Không click Generate, không tải hoặc tự xác nhận video nào thuộc lượt cũ, không đổi unknown hoặc mở retry. Nhiều lượt unknown được gộp một file như .36.

Đã kiểm tra Chromium với cấu trúc mô phỏng, iframe, shadow DOM, giới hạn thời gian và ledger giữ nguyên. Chưa xác minh trên Flow thật hoặc chạy installer Windows. Đây là bản bổ sung chẩn đoán, chưa sửa dứt điểm việc nhận video.
