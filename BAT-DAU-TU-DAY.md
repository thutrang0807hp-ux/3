# Bắt đầu từ đây

## Chạy để phát triển

Dùng Python 3.12. Windows: có thể chạy `local_engine/start.bat`. Script tạo `.venv`, cài core requirements rồi mở app trên loopback. Core cho phép 3.11–3.13, nhưng phần CPU khuyến nghị 3.11/3.12.

macOS/Linux hoặc chạy thủ công tại thư mục gốc:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r local_engine/requirements.txt
python -m local_engine
```

Mở URL in trên console, thường là http://127.0.0.1:8840/. Giữ tiến trình backend khi sử dụng. Có thể đặt `SCENEFORGE_OPEN_BROWSER=1` để tự mở browser. Nếu cổng đang bị dùng, đọc cổng thực tế trên console. Không bind ra Internet.

Thư viện và tài khoản mặc định ở `~/.sceneforge-local`, hoặc đường dẫn do `SCENEFORGE_LOCAL_DATA` chỉ định. Gói này không chứa dữ liệu cá nhân đó. Khi làm thử/test, dùng một thư mục dữ liệu riêng; không trỏ test vào thư viện đang làm việc.

## Sửa và dựng frontend

```sh
python scripts/demo-web/build.py
```

Đây là pipeline hiện hành, không cần npm build. Nó gọi `rebuild_current.py`: mở rộng các include từ `scripts/recovered` rồi chạy lần lượt các patcher trong `scripts/demo-web`. Frontend thực tế có cả phần append ở cuối: sửa đúng source tính năng, đừng chỉ sửa HTML trong `dist` rồi để build ghi đè.

Gói giữ các tài nguyên tĩnh và editor trong `dist/web-demo`; không xóa toàn bộ `dist` trước khi build. Build hiện hành đã được kiểm từ bản giải nén, đối chiếu byte của 7 trang production. Các trang đã dựng sẵn có thể phục vụ ngay bằng backend.

## Công cụ tùy chọn

- Cắt/đọc video và xuất MP4: cần FFmpeg **và ffprobe** trong PATH. Cài CPU dependencies từ `local_engine/requirements-cpu.txt` nếu dùng PySceneDetect/OpenCV/OCR/Whisper.
- Whisper: `local_engine/install-transcription.bat`, hoặc dùng môi trường app chạy `python -m local_engine.prepare_whisper --model base --download`. Model khoảng 150 MB; chưa kèm trong gói. Môi trường phát triển vừa qua bị nguồn Hugging Face trả HTTP 403, không coi là đã cài model ở máy đích. Có thể dùng `--from-directory` với model có sẵn hoặc nhập SRT.
- VieNeu, Flow và SDK nguồn ảnh/chat có bộ cài/adapter riêng trong `local_engine`. Không phải các engine đó đã được kèm hoặc đã xác minh chỉ vì có adapter. Xem tài liệu từng nguồn và trạng thái thực tế trong Cài đặt.
- Cửa sổ tài khoản dùng Playwright. Có thể cài Chromium bằng `python -m playwright install chromium`, hoặc đặt `SCENEFORGE_BROWSER` tới Chrome/Edge có sẵn. Không chuyển cookie giữa các miền/nhà cung cấp khác nhau.

## Kiểm các phần mới

Cài `playwright` và Chromium cho môi trường kiểm thử; nhiều test hiện dùng `/usr/bin/chromium` nên cần đổi đường dẫn khi chạy trên Windows/macOS. Chạy app tests trong thư mục gốc. Hai test chính:

```sh
python scripts/app-shell/check_prompt_pipeline.py
python scripts/app-shell/check_photo_prompt_pipeline.py
```

Các test khác và giới hạn nằm trong `docs/prompt-pipeline.md`, `docs/storyboard-modes.md`, `docs/photo-merge-export.md`, `docs/photo-input-script.md`. Báo cáo đã chạy nằm trong `docs/checks`. Provider/quality fixtures không thay thế một lượt gen online thật.

## Bộ cài Windows

Source C, PowerShell, bootstrap Python, script cross-build và bài kiểm Windows nằm trong `scripts/windows-installer`. Xem `docs/windows-installer.md` và `releases/windows-release.json`. EXE đã phát hành có Python riêng, không cần Python hệ thống. Gói code này không nhúng lại EXE/runtime 84 MB.

Để tái tạo bộ cài: tải CPython Windows 3.12.16 đúng SHA và Windows wheels được liệt kê trong release/build report; chuẩn bị Zig bằng package `ziglang` cùng `packaging` trong môi trường build. Ví dụ:

```sh
python scripts/windows-installer/build.py --python-tar DUONG_DAN_TAR --wheels THU_MUC_WINDOWS_WHEELS --zig-python DUONG_DAN_PYTHON_CO_ZIGLANG
```

`build.py` kiểm hash Python và dependency markers cho Windows trước khi tạo EXE. Cross-build đạt không có nghĩa đã chạy thử Windows; dùng `check_windows.ps1` trên Windows để kiểm runtime. Không ký số Authenticode.
