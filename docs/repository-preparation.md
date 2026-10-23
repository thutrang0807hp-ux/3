# Chuẩn bị repo, chưa thử tài khoản thật

Theo thống nhất, tài khoản thật để kiểm thử sau. Ollama vẫn để trống.

## Đã cài trong môi trường phát triển

| Repo / công cụ | Kết quả đã kiểm tra | Chưa hoàn tất |
| --- | --- | --- |
| flow2api `018f75539fe97d5602e0dcac6783638093bb6479` | Cài dependencies riêng, import app, đọc được 82 model từ route xác thực của repo. Adapter SceneForge đã kiểm bằng transport fixture. | Đăng nhập, credit, tạo nội dung, đa luồng dịch vụ thật. |
| muse2api `5542a479ec6ba036a9717e8776380ff5aacf3fe7` | Cài dependencies riêng, `pip check` và import app/route ảnh-video thành công. | Repo này dùng **muse.ai**, chưa xác minh đúng Meta. Chưa nối lựa chọn Muse/Meta trong app. Không chạy browser/keepalive hoặc nhập tài khoản. |
| VieNeu-TTS `04044e1b8f822f946bafb2c88b716459f4164152` | Build và cài SDK 3.8.3, `pip check`, import class `Vieneu` thành công trong chế độ offline; không có PyTorch. | Chưa tải trọng số model, chưa tổng hợp giọng thật. SDK ở môi trường riêng chưa được endpoint TTS hiện tại dùng. |
| PySceneDetect / OpenCV / RapidOCR | Đã chạy bài kiểm tra tách cut, OCR và xử lý ảnh thật trên fixture local. | Chất lượng với từng video người dùng cần rà. |
| Faster-Whisper | Có thư viện trong môi trường CPU thử nghiệm. | Chưa có model chép lời. |

Đường dẫn môi trường phát triển: `/workspace/engines/flow-managed`, `/workspace/engines/muse-ready`, `/workspace/engines/vieneu-ready`. Đây không phải bằng chứng các công cụ đã được cài trên máy người dùng.

## Bộ cài được cung cấp

- Flow: `local_engine/install-flow.bat`; sau đó `start-flow.bat` cho bước đăng nhập khi sẵn sàng. Xem `photo-flow-integration.md`.
- VieNeu SDK: `local_engine/install-voice-sdk.bat`. Chỉ chuẩn bị SDK CPU ở môi trường riêng; chưa bật tạo giọng trong app hoặc tải model.
- Repo Muse để nghiên cứu: `python -m local_engine.setup_optional_repos muse`. Cố định revision, kiểm thư viện/import, ghi trạng thái `enabled_in_app: false`. Không có nút tự mở tài khoản và không đổi ngầm thành Meta.
- Repo giọng đọc qua CLI: `python -m local_engine.setup_optional_repos voice`.

Các bộ cài cần Git/Python và mạng để lấy repo/thư viện. Không chứa tài khoản, cookie hoặc model trong ZIP. Tách môi trường tránh đổi dependencies của SceneForge. Kiểm import chạy với model hub ở chế độ offline; không khởi tạo model.

**Cài repo, có adapter và chạy được với tài khoản/model thật là ba trạng thái khác nhau.** Bản này chỉ xác nhận đúng các bước trong bảng; không tuyên bố đã hoàn tất toàn bộ pipeline AI.
