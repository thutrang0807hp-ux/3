# SceneForge v46.69 — nghe thử và chọn giọng

Cập nhật từ .68 trở lên: đóng app, chạy `SceneForge-Update-20261104-v46.69-Voice-Preview.exe`, chọn thư mục đang cài và mở lại. Updater khoảng 4 MB, giữ Data/cache/lịch sử/model/tài khoản.

Cả workflow và photos dùng bộ chọn giọng có tìm kiếm, cuộn riêng tối đa 340px. Node chỉ hiện giọng đang chọn và nút nghe thử/nghe lại. Bắt đầu Audio.play ngay sau khi gán nguồn; không phụ thuộc callback metadata để bắt đầu phát. Mẫu lưu trước khi phát; nếu trình duyệt chặn autoplay thì hiển thị lỗi rõ và nghe lại mẫu không tạo lượt TTS mới. Lỗi worker hiển thị trên đầu node, controls dùng lại được. Lỗi endpoint hiệu ứng tùy chọn không làm mất trạng thái TTS đã cài. Chọn giọng không tự tổng hợp. Mẫu không được coi là lời đọc đầy đủ.

Kèm xuất báo cáo video đọc mới GET jobs/diagnostics, kiểm request/store/room, tách dữ liệu live/cache/frontend và lỗi tra cứu. Không tự retry generation, không coi unknown_store là chưa gửi. CLI/runtime/model không thay.

Kiểm thử Chromium: 25 giọng, tìm kiếm/chọn/đóng, node gọn, WAV PCM thực có đồng hồ phát chạy, giả lập autoplay bị chặn rồi nghe lại không POST thêm, full narration lưu asset/segments, worker lỗi hiện rõ và nút mở lại. API TTS là fixture; không phải kiểm thử model VieNeu hiện tại trên Windows. Regression video và diagnostics riêng. Builder kiểm nguồn khớp byte trong payload và launcher không thay. Chưa chạy updater trực tiếp Windows.

SHA256: `ace2ded89934191277f34954716bcb0933a21f9a11f35441a617bb83e24fcf21`
