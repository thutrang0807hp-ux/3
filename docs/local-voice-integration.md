# VieNeu CPU: model và đường tạo giọng

Đã nối endpoint `/local-api/tts` với SDK VieNeu trong môi trường riêng. Không còn yêu cầu phải cài VieNeu chung vào môi trường của app.

## Cài trên máy

1. Chạy SceneForge bằng `local_engine/start.bat` một lần để có môi trường app.
2. Chạy **`local_engine/install-voice.bat`**. Bộ này cài SDK, tải model v3 Turbo ONNX CPU fp32, tạo WAV thử rồi chạy lại thử ở chế độ offline.
3. Chỉ khi cả hai lượt thành công mới ghi `model_ready: true`. Khởi động lại SceneForge để cập nhật danh sách giọng.

Linux/CLI: `python -m local_engine.setup_optional_repos voice`, sau đó `python -m local_engine.prepare_voice`.

Mặc định SDK/model nằm trong `SCENEFORGE_LOCAL_DATA/engines/vieneu` (nếu chưa đặt biến thì dùng thư mục dữ liệu mặc định của SceneForge). Có thể dùng `--directory` cho bộ cài model; khi dùng chỗ khác, đặt `SCENEFORGE_VIENEU_DIRECTORY` cho app trỏ tới cùng thư mục engine.

`install-voice-sdk.bat` cũ vẫn chỉ cài SDK; dùng `install-voice.bat` mới để hoàn tất model. Không có yêu cầu tài khoản Flow, Muse hay Gemini cho bước giọng đọc này.

## Khi tạo giọng

- App đọc trạng thái SDK/model riêng và danh sách giọng đã thử.
- Model thiếu/chưa thử thì nút tạo giọng không được bật; API trả lỗi rõ ràng.
- Chạy CPU với hai thread, không cài PyTorch hoặc chọn GPU ngầm.
- Worker chạy riêng, dùng model cache offline; không tải thêm trong lúc render.
- Chọn preset qua tên hợp lệ, tạo từng nhịp, ghép WAV PCM và trả mốc thời gian đúng thứ tự.
- Chỉ một lượt TTS mỗi lúc; giới hạn 60 nhịp, tổng 15.000 ký tự, đầu ra tối đa 30 phút/200 MB. Hủy/timeout dừng tiến trình con và bỏ tệp chưa hoàn tất.
- Không gọi dịch vụ trả phí thay thế. Nguồn lời đọc trong app không bị ghi vào log của endpoint TTS mới.

## Tình trạng kiểm chứng thật

Trong môi trường phát triển, đã thử tải model từ Hugging Face bằng SDK. **Proxy trả HTTP 403 cả trong lần thử thông thường và lần thử quyền mạng mở rộng.** Vì vậy:

- SDK cài và import được.
- Model thật chưa tải hoàn tất, chưa khởi tạo được.
- Chưa có giọng đọc thật được tạo để nghe hoặc đánh giá chất lượng.
- Trạng thái môi trường vẫn là `model_ready: false`, phase `blocked`.

Kiểm thử `python -m local_engine.check_local_tts` dùng SDK fixture để kiểm đường subprocess, trạng thái chuẩn bị online/offline, chọn giọng, WAV/timing và chặn model thiếu/hỏng. Đây không phải chứng nhận model thật tạo giọng thành công. Các kiểm tra local API và cài đặt hiện có cũng đã qua sau thay đổi.

Bộ ZIP chứa code và bộ cài; không nhúng model tải dở, cache, tài khoản hoặc âm thanh giả làm kết quả thật.
