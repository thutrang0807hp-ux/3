# SceneForge — bàn giao chat tiếp (04/11/2026)

## Bắt đầu ở đây

Tôi đang phát triển SceneForge Windows. Hãy đọc bản bàn giao này và code đúng nhánh trước khi sửa; tiếp tục từ bản .62, không làm lại engine. Người dùng đã yêu cầu sửa và đóng gói EXE trực tiếp, thích ít thao tác và không muốn bị hỏi xác nhận lặp lại.

- Repo ứng dụng: https://github.com/thutrang0807hp-ux/3
- Nhánh chứa code/phần mềm: **gh-pages**, KHÔNG mặc định suy ra nhánh main.
- Commit phát hành .62: `2f5d9a0d1f0d635637bc12d321e9ab28acbb3b7e`.
- Repo tham chiếu chạy được của người dùng: https://github.com/thutrang0807hp-ux/5gdfgfd
- Ghi chép kỹ thuật chi tiết: `docs/gflow-integration-20261103.md` (các mục .60/.61/.62 ở cuối).
- Đặc tả giao diện người dùng đã gửi: `DAC_TA_NODE_VIDEO_VEO.md`; thiết kế lưới clip, bấm mở video trái/prompt phải. File đính kèm chat cũ có thể không còn trong chat mới; bố cục đã được code trong workflow.html.

## Các bản tải

**.60 là gói có CLI + runtime**, khoảng 88 MB, cập nhật trên .52 trở lên:
https://github.com/thutrang0807hp-ux/3/raw/refs/heads/gh-pages/downloads/v46-bundled-cli/SceneForge-Update-20261104-v46.60-Bundled-Original-CLI.exe

**.62 là bản vá mới nhất**, khoảng 4 MB, cần đã có .60; bao gồm giao diện/tối ưu .61. Không yêu cầu cài lần lượt .61:
https://github.com/thutrang0807hp-ux/3/raw/refs/heads/gh-pages/downloads/v46-create-button-fix/SceneForge-Update-20261104-v46.62-Create-Button-Fix.exe

Các EXE này là **updater cho SceneForge đã cài**, không phải bộ cài đầy đủ trên máy trắng. .62 chỉ thay workflow.html, giữ engine/runtime/account của .60. Mỗi thư mục phát hành có README, patch-build.json và SHA256. Không ghi đè âm thầm bản đã phát hành; sửa tiếp dùng số mới (.63).

## Điều phải giữ trong kiến trúc

- Gọi **CLI gốc** bằng Python đi kèm: `python.exe -m gflow_cli video r2v/i2v ...`. Không quay lại worker SDK tự viết, không subclass/ghi đè session methods, không đổi channel thành executable_path.
- CLI nguyên bản **0.92.1**, SDK revision `1619429f12e31a806590a19e1a3f3218f291d582`.
- Portable upstream revision `09ab05b190ddad0b3bbed80439ecbc6739d5abce`, archive SHA256 `03ae9541fefa55e4f917f87db794cd2b26f61d5d215a754b333b5dfc3d686292`.
- .60 nhúng archive vào `app/vendor/gflow-original.zip`; giải nén runtime cục bộ vào Data/flow-engine. Mặc định không dò Downloads, không cài pip/Python/GFlow riêng.
- CLI dùng profile Chrome của tài khoản SceneForge đang chọn qua junction dưới Data/flow-cli. Không copy cookie/session. Tôn trọng email/profile binding; alias không được đổi sang tài khoản khác.
- Không truyền `--duration 8`: account/model thật không có ô chọn 8s, từng gây exit 11. Không thêm resolution/giá credit/xóa logo chưa được xác minh. x1 kết quả.
- Ingredients dùng r2v; Frames dùng i2v. Quality cần Frames. Tỉ lệ 9:16 hoặc 16:9 theo cấu hình đã chốt lúc gửi.
- Một ảnh upload, một clip mỗi request. Giữ ledger/receipt, chữ ký ảnh-prompt-cấu hình, room/scene/part binding; không tự gửi lại lệnh tạo khi kết quả chưa rõ.
- Exit 6 MediaDownloadError có ID thì chỉ dùng `data download` để tải lại đúng ID, không tạo video mới.

## Tình trạng và thay đổi gần nhất

Người dùng xác nhận tạo/tải/nhận video đã hoạt động. Sau đó muốn giao diện gọn, tự nhận clip, tiến độ và bớt lag. Chưa có phản hồi người dùng xác nhận bản .62 chạy trên máy họ.

- Node lưới, nhóm a/b, lọc Tất cả/Cần xem; cửa sổ video/prompt, phiên bản, video mẫu, 0.5x/lặp. Tải hợp lệ thì tự gắn đúng cảnh. **Duyệt chất lượng vẫn là bước riêng** trước Dựng.
- ID sớm và trạng thái thật lấy từ log JSON của CLI. CLI không trả %: phần trăm theo bước ghi rõ **ước tính**; 100% chỉ khi nhập/lưu xong. Không coi missing là chưa gửi.
- .61 bỏ cấu hình chân node, chỉ giữ dock trên thanh workflow. Nút Tạo toàn bộ clip còn thiếu không phụ thuộc bộ lọc; tự viết prompt còn thiếu qua Gemini hiện có, chạy tuần tự. Clip đã có không tạo lại. Phần nối b chờ duyệt a; đổi đầu vào/tài khoản/cấu hình hoặc kết quả chưa rõ thì dừng gửi thêm.
- .61 giữ DOM ảnh/video, cập nhật phần thay đổi, lazy diagnostics, bỏ lưu toàn bộ dự án trên poll giống nhau và tránh vòng poll cũ vẽ lại canvas. Durable intent trước POST vẫn giữ. Benchmark local 18 ảnh: click handler từ ~43ms xuống ~1ms; không phải cam kết hiệu năng trên máy người dùng.
- **Lỗi cuối người dùng báo:** nút Tạo bị disabled với dòng “Đối soát lịch sử lượt cũ trước khi tạo thêm” ở cảnh 6a, phần dài 4.2s. Đây là legacy-history gate, không phải thiếu thời lượng của model.
- **.62 đã sửa:** tự đọc receipt cũ khi mở clip. Chỉ tự mở khóa nếu đúng request/store/room/scene/part và backend xác nhận submitted=false + failed/not_submitted. Lịch sử chưa rõ không bị xóa hoặc tự coi là chưa gửi.
- Nếu legacy là lý do chặn duy nhất, nút **Kiểm tra lượt cũ rồi tạo video** bấm được. Có nút đọc lại/xem lịch sử/xác nhận trong inspector. Còn chưa rõ thì cần người dùng xác nhận đối soát, sau đó xác nhận tạo mới bình thường. Hủy không gửi gì; tạo mới dùng ID mới, giữ ID cũ. Các chặn hợp lệ khác vẫn giữ.

## Vị trí code và kiểm tra

- `workflow.html`: frontend thực tế; phần SFVeoNode ở script cuối, schema job vẫn **43**. Không đánh đồng schema với số bản EXE.
- `veo-node-v46/local_engine/flow_gflow_cli.py`: gọi CLI gốc, kết quả, download recovery.
- `flow_cli_bundle.py`: runtime cục bộ, nối profile và kiểm email; `flow_gflow_runtime.py`: kiểm checksum/giải nén.
- `flow_cli_progress.py`: đọc log allowlist, phân biệt ID ảnh và ID video, đúng project, không dựng % từ Flow.
- `simple_flow.py`, `flow_native_pipeline.py`: admission/receipt/preparation. Native pre-upload được bỏ cho đường CLI để tránh hai ảnh.
- `scripts/analysis/check_veo_redesign_ui.py`: Chromium + endpoint giả lập + MP4 thật cục bộ. Bao gồm lỗi khóa legacy .62, receipt sai cảnh, hủy xác nhận, đúng một request mới, queue/filter/auto-prompt/continuity/nhận clip/không redraw.
- Các check JS: `check_flow_config_create_ui.js`, `check_flow_auto_settings.js`, `check_cli_report_ui.js`; benchmark `measure_veo_node.py`.
- `veo-node-v46/tests/test_gflow_cli.py`: 24 test CLI/bundled/profile, local process fixtures.
- Build .60: `veo-node-v46/scripts/windows-installer/build_bundled_cli_patch.py --archive <upstream zip>`; cần dnfile. EXE lớn mở rộng PE resource, giữ nguyên mã launcher.
- Build .62: `build_legacy_create_fix_patch.py`; UI-only, minimum .60. Dùng launcher template đã kiểm checksum và kiểm lại byte các tệp nhúng.

**Giới hạn đã công bố:** kiểm tra fixture cục bộ và cấu trúc/tệp trong EXE; chưa chạy updater/NTFS junction trực tiếp trên Windows hoặc xác minh Flow thật. Không tuyên bố “đã test Flow thành công” dựa trên mock. Nếu người dùng báo lỗi tiếp, lấy message/receipt đúng lượt, tái hiện rồi sửa hẹp; giữ phần tạo video đang chạy được.
