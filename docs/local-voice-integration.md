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

Model đã được cài từ các file người dùng cung cấp, gồm 13 file VieNeu/MOSS. Hai decoder, encoder MOSS, tokenizer, các graph acoustic/backbone và đầu ra tiếng nói đã chạy thật trên CPU.

- Đã giải nén và kiểm tra đủ 7 phần backbone cùng heads; kiểm tra CRC/SHA256 và kích thước.
- Đã tạo WAV từ câu tiếng Việt mới, sau đó khởi động lại worker và tạo lại trong chế độ offline.
- Có 25 preset giọng; không cần thu âm mẫu để dùng các preset.
- `scripts/app-shell/check_voice_local.py` đã chạy bằng model thật: bấm Tạo giọng trong trình duyệt → endpoint TTS → CPU → WAV 48 kHz mono, lưu vào dự án và mở lại. Hai nhịp có thời lượng 2,96 và 2,48 giây; một yêu cầu TTS, không gọi Flow/Muse/Gemini.
- Đã kiểm đường chọn giọng, cập nhật thời lượng từng nhịp và giữ file sau reload. Chưa đánh giá chất lượng phát âm toàn bộ 25 giọng hoặc tốc độ trên Windows/GPU.

Nguồn tải Hugging Face trong môi trường này vẫn bị proxy 403, nhưng model hiện đã đủ nhờ file gửi lên và chạy trực tiếp từ thư mục offline; không cần giả lập cache hay revision Hub.

## Gói model offline

`artifacts/VieNeu-CPU-Offline.zip` chứa 13 file model, manifest SHA256 và thông tin nguồn. Không kèm tài khoản, cache trình duyệt hoặc Python venv. Chạy `install-voice-offline.bat` và kéo ZIP model vào BAT nếu dùng riêng. Gói đầy đủ đặt ZIP sẵn ở `models/VieNeu-CPU-Offline.zip` để dùng một bộ tải.

Bộ cài SDK/Python dependencies vẫn cần mạng lần đầu; trọng số model được lấy hoàn toàn từ ZIP, không tải từ Hugging Face. Import chỉ đọc danh sách 13 tên file cho phép, xác minh kích thước/SHA256 và không ghi đè bộ trọng số khác đã có. `prepare_voice --offline` chỉ đánh dấu sẵn sàng sau khi tạo WAV thật thành công.

Kiểm thử `python -m local_engine.check_local_tts` vẫn dùng SDK fixture cho các nhánh lỗi. Bằng chứng model thật nằm ở bài trình duyệt `check_voice_local.py` và mẫu `artifacts/voices/SceneForge-HaiDang-CPU.wav`.
