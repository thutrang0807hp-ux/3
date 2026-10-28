# SceneForge · bộ cài Windows x64

Mở `SceneForge-Setup-Windows-x64.exe`. Bộ cài giải nén ứng dụng và Python riêng vào `%LOCALAPPDATA%\SceneForge\releases\2026.10.28.42599ab`, tạo shortcut rồi mở ứng dụng. Không yêu cầu cài Python hệ thống hoặc quyền quản trị. Giao diện mở trong trình duyệt tại địa chỉ loopback; giữ cửa sổ console của SceneForge trong khi dùng, đóng cửa sổ để dừng.

Dữ liệu và tài khoản vẫn ở thư mục người dùng `.sceneforge-local` theo cơ chế cũ, hoặc `SCENEFORGE_LOCAL_DATA` do người dùng đặt. Cài lại cùng gói không thay thư mục phiên bản đã xác nhận hoặc xóa dữ liệu. Nếu thư mục phiên bản đã có nhưng thiếu/sai marker thì dừng, không ghi đè. Không có gỡ cài đặt tự động hay tự dọn phiên bản cũ.

Gói gồm Python 3.12.16 Windows x64 từ python-build-standalone 20261026, các Windows wheel của core backend, launcher PE x64 và giao diện hiện tại. `BUNDLED-COMPONENTS.json` ghi URL/hash Python và hash/version từng wheel. Các giấy phép đi kèm runtime và wheel được giữ nguyên. ZIP payload được kiểm SHA-256 trước khi giải nén. Chưa có chữ ký số Authenticode.

Whisper/VieNeu, FFmpeg/ffprobe, engine Flow và tài khoản AI không được đóng kèm. App hiển thị tình trạng thiếu thực tế. Start Menu có `SceneForge - Cai Whisper`: dùng Python trong gói để cài CPU dependencies và tải model base khoảng 150 MB; cần mạng và vẫn cần FFmpeg/ffprobe cho video. Khởi động thông thường không pip install hoặc tải model.

Launcher nhận diện Chrome/Edge đã cài cho cửa sổ đăng nhập của Playwright nếu người dùng chưa đặt `SCENEFORGE_BROWSER`. Chất lượng và khả năng tạo ảnh/video bằng tài khoản thật chưa được chứng nhận bởi kiểm bộ cài.

Nguồn bộ cài: `scripts/windows-installer/`. `build.py` kiểm hash Python, audit dependency markers bằng môi trường Windows, cài Windows wheels vào runtime riêng, biên dịch C bằng Zig cross-toolchain rồi gắn ZIP payload. Core app không được biến đổi để đóng băng vào launcher; các worker `sys.executable -m local_engine...` vẫn dùng Python đi kèm.

`build-report.json` chỉ chứng nhận cross-build, CRC payload và PE x64. Kiểm Windows thật là báo cáo riêng `windows-check-report.json` từ workflow `SceneForge Windows installer check`: chạy bộ cài, dùng Python riêng, mở server/route thật, kiểm phiên và instance lock, cài lại không mất dữ liệu. Không coi kiểm header PE trên Linux là đã chạy thử Windows. Báo cáo kiểm không thay thế việc dùng thử trên máy người dùng hoặc thử tài khoản AI online.

Kho kịch bản v5 đang tạm hoãn, không nằm trong thay đổi này.

## Kết quả kiểm Windows thật

Đã chạy bộ cài có SHA-256 `a68cb20b90ea09e3b31bf9f73c09f349a1b2d48b9ef086209ebd5a28faa9814f` trên Windows build 26100, bằng runtime đi kèm. Cài/giải nén thành công, pip check đạt, server loopback chạy, Chrome thật mở shell và cả hai canvas không có lỗi JavaScript hay lệnh tạo media, lần mở thứ hai dùng lại instance, cài lại cùng gói giữ thư mục phiên bản và dữ liệu. Báo cáo: [windows-check-report.json](windows-check-report.json); lượt chạy: https://github.com/thutrang0807hp-ux/3/actions/runs/40684138576. Không kiểm bằng tài khoản AI online, không cài model/FFmpeg trong lượt này.
