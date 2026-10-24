# Chép lời Whisper base — model đã chạy thật

Đã ghép 6 phần `model.part1.rar` đến `model.part6.rar` của người dùng. `model.bin`: 145.217.532 byte, SHA256 `d01c3014881c9c6f3133c182f3d2887eb6ca1c789a7538c5c007196857a0a6a9`. Giữ nguyên các file gốc. Bộ model gồm `model.bin`, `config.json`, `tokenizer.json`, `vocabulary.txt`; không bắt buộc có preprocessor_config.json với bản này.

## Đã xác minh

- Chạy model CPU int8, hai thread, hoàn toàn offline; không cài PyTorch/CUDA.
- Chép đoạn tiếng Việt được tạo mới bằng VieNeu (5,44 giây), trả lời và mốc từng từ. Lượt thử trực tiếp khoảng 1,94 giây trên môi trường phát triển; không suy ra tốc độ máy người dùng.
- `python -m local_engine.check_whisper_real`: ghép lời thử vào video dọc, gửi API `/local-api/analysis/local/jobs` với `transcribe:true`, worker riêng chạy FFmpeg/PySceneDetect/OpenCV/Faster-Whisper, nhận hai đoạn lời tiếng Việt cùng timestamp từ, không có yêu cầu nhà cung cấp, dọn file tạm.
- Có lỗi tương thích thật giữa faster-whisper 1.2.1 và PyAV 19 (`metadata_errors`); đã cố định PyAV `>=16,<17`, kiểm thử với 16.1.0.

Đây là model base nhẹ, chưa phải chứng nhận chất lượng. Lượt thử còn nghe nhầm “giọng đọc”, “kịch bản” và tên SceneForge. Người dùng cần rà bản lời; tên riêng, giọng nhỏ, nhạc nền hoặc nhiều người nói có thể sai. Chưa kiểm thử Windows và tập video thực tế đa dạng.

## Cài trên máy

Giải nén gói đầy đủ, chạy `local_engine/install-transcription.bat`, sau đó mở lại SceneForge. Cần Python 3.10–3.12 và FFmpeg/ffprobe. Lần đầu tải thư viện từ pip, nhưng model có sẵn trong `models/faster-whisper`, không tải lại Hugging Face. Gói app nhỏ không kèm model: BAT sẽ chủ động tải model khi chạy.

Thư mục đích: `SCENEFORGE_LOCAL_DATA/models/faster-whisper`, mặc định `.sceneforge-local/models/faster-whisper` trong thư mục người dùng. Có thể nhập model thủ công:

```
python -m local_engine.prepare_whisper --from-directory models/faster-whisper
```

Bộ cài kiểm tra file, nạp model thật, kiểm đường đọc âm thanh/VAD offline trước khi ghi sẵn sàng, không ghi đè model khác. Mặc định dùng im lặng để kiểm cơ chế; muốn kiểm nhận dạng lời mới thêm `--probe duong-dan.wav`. Không đánh đồng kiểm tra im lặng với chất lượng nhận dạng lời.

Trong node Phân tích của video mẫu, chọn đo CPU và bật chép lời. Khi phân tích không tự tải model hoặc chuyển sang API trả phí. Chạy CPU nguyên bộ phân tích trong môi trường app; cài bên môi trường phát triển không tự cài vào máy người dùng.
