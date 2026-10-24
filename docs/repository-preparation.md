# Chuẩn bị repo, chưa thử tài khoản thật

Theo thống nhất, tài khoản thật để kiểm thử sau. Ollama vẫn để trống.

## Đã cài trong môi trường phát triển

| Repo / công cụ | Kết quả đã kiểm tra | Chưa hoàn tất |
| --- | --- | --- |
| flow2api `018f75539fe97d5602e0dcac6783638093bb6479` | Cài dependencies riêng, import app, đọc được 82 model từ route xác thực của repo. Adapter SceneForge đã kiểm bằng transport fixture. | Đăng nhập, credit, tạo nội dung, đa luồng dịch vụ thật. |
| muse2api `5542a479ec6ba036a9717e8776380ff5aacf3fe7` | Cài dependencies riêng, `pip check` và import app/route ảnh-video thành công. | Repo này dùng **muse.ai**, chưa xác minh đúng Meta. Chưa nối lựa chọn Muse/Meta trong app. Không chạy browser/keepalive hoặc nhập tài khoản. |
| VieNeu-TTS `04044e1b8f822f946bafb2c88b716459f4164152` | Build và cài SDK 3.8.3, `pip check`, import class `Vieneu` thành công trong chế độ offline; không có PyTorch. | Đã cài model từ file người dùng cung cấp, có 25 preset và qua kiểm thử tạo giọng thật từ UI trên CPU/offline. Chưa đánh giá toàn bộ giọng hoặc máy Windows. Xem local-voice-integration.md. |
| PySceneDetect / OpenCV / RapidOCR | Đã chạy bài kiểm tra tách cut, OCR và xử lý ảnh thật trên fixture local. | Chất lượng với từng video người dùng cần rà. |
| Dịch local (M2M100 418M / CTranslate2) | Một model, 100 ngôn ngữ, dịch thẳng về Việt; worker/endpoint/bộ cài đã đổi, runtime CPU có. Argos không còn được dùng. | Trọng số bị chặn tải 403; chưa chạy model thật, chỉ kiểm thử fixture. Không báo hoàn tất model. |
| Faster-Whisper | Đã cài model base từ 6 phần RAR người dùng gửi. CPU int8/offline đã nhận dạng tiếng Việt qua API phân tích video, có mốc từng từ. | Bản base còn nghe nhầm một số chữ và tên riêng; cần người dùng rà. Chưa đánh giá trên nhiều video thật hoặc Windows. |

Đường dẫn môi trường phát triển: `/workspace/engines/flow-managed`, `/workspace/engines/muse-ready`, `/workspace/engines/vieneu-ready`. Đây không phải bằng chứng các công cụ đã được cài trên máy người dùng.

## Bộ cài được cung cấp

- Flow: `local_engine/install-flow.bat`; sau đó `start-flow.bat` cho bước đăng nhập khi sẵn sàng. Xem `photo-flow-integration.md`.
- VieNeu: `local_engine/install-voice-offline.bat` dùng model trong gói đầy đủ; `install-voice.bat` tải model khi không có file offline. Giọng đọc đã nối app và kiểm chứng model thật.
- Chép lời: `local_engine/install-transcription.bat`; xem `whisper-model-integration.md`.
- Repo Muse để nghiên cứu: `python -m local_engine.setup_optional_repos muse`. Cố định revision, kiểm thư viện/import, ghi trạng thái `enabled_in_app: false`. Không có nút tự mở tài khoản và không đổi ngầm thành Meta.
- Repo giọng đọc qua CLI: `python -m local_engine.setup_optional_repos voice`.

Các bộ cài cần Git/Python và mạng để lấy repo/thư viện. Không chứa tài khoản/cookie. ZIP công khai nhỏ không chứa model; gói đầy đủ kèm model được bàn giao riêng. Tách môi trường tránh đổi dependencies của SceneForge. Model VieNeu và Whisper đã khởi tạo/chạy thật offline; Flow/Muse vẫn chưa kiểm thử sinh nội dung với tài khoản thật.

**Cài repo, có adapter và chạy được với tài khoản/model thật là ba trạng thái khác nhau.** Bản này chỉ xác nhận đúng các bước trong bảng; không tuyên bố đã hoàn tất toàn bộ pipeline AI.
