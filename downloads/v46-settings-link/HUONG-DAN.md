# SceneForge v46.38 — mở và đọc chi tiết video cũ

1. Đóng SceneForge, chạy SceneForge-Update-20261102-v46.38-Video-Detail.exe, chọn thư mục có SceneForge.exe và install-settings.json. Yêu cầu v46.7 trở lên.
2. Mở đúng phòng và tài khoản của lượt cũ. Không tạo lại video.
3. Bấm **Tự kiểm tra video đã gửi và tải báo cáo**. Với lượt unknown đã dừng, app tự tìm thẻ flow-video-tile và chỉ mở khi có duy nhất thumbnail phù hợp đang hiển thị. Lượt đang chạy chỉ thu thập cấu trúc, không mở viewer.
4. File SceneForge-theo-doi-video.json thêm video_detail_probe và media_structure_after_detail: vùng chi tiết, trường prompt có nhãn, kết quả đối chiếu, cấu trúc sau khi mở. Gửi file đó trong chat.

Không click Reuse prompt/Generate/Download, không tự nhận video, không đổi unknown và không mở retry. Prompt khớp vẫn chưa chứng minh video thuộc chính lượt cũ. Nhiều thumbnail hoặc viewer đang mở thì không click chọn đại.

Đã kiểm tra Chromium với cấu trúc mô phỏng, video DOM tái sử dụng, prompt có nhãn và ledger giữ nguyên. Cấu trúc vùng chi tiết/trường prompt chưa xác minh trên Flow thật; nếu không nhận diện được thì báo cáo ghi rõ. Chưa chạy installer Windows.
