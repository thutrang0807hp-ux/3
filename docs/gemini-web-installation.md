# Gemini web SDK: đã cài repo, chưa nối tài khoản thật

Repo: https://github.com/HanaokaYuzu/Gemini-API . Revision cố định `1ad0d4a93e505e77c79769d78ef2997641f973c8`, giấy phép AGPL-3.0. Tài liệu kiểm repo trước đó và yêu cầu “cài đi” được dùng làm phạm vi cài SDK; không tự đăng nhập hoặc gửi nội dung.

## Đã làm thật

- Clone revision đã đọc, build wheel và cài dependencies vào môi trường riêng `/workspace/engines/gemini-web/venv`; không nâng Pydantic/curl hoặc thư viện trong app.
- `pip check` qua. SDK build từ checkout shallow hiện báo version `0.0.post1`; revision Git ở trên là định danh chính xác, không gọi đó là phiên bản phát hành mới nhất.
- `check_gemini_web_sdk.py` chạy bằng SDK đã cài: import, tạo client/hội thoại không init, kiểm đối số file qua wrapper `send_message`, kiểu ảnh được tạo, setter metadata và khôi phục metadata hội thoại. Transport/phản hồi fixture; chặn đường HTTP trong bài kiểm. Không dùng test upstream cần account/ảnh sinh thật.
- Không tải model, Chromium hoặc Torch; không cài browser-cookie3, không đọc cookie của trình duyệt, không init Google, không đăng nhập hoặc gửi prompt/file thật.
- Tổng thư mục repo và môi trường Python khoảng **155 MiB (~163 MB)** trên Linux phát triển, đã gồm dependencies/venv; không suy ra đúng số này cho Windows. Gói ZIP app chỉ thêm bộ cài/tài liệu, không nhét venv vào.
- Ghi `installation.json`: dependencies/import/sdk_contract true; account_verified/generation_verified/enabled_in_app false. Runtime chưa có cookie.

## Cài trên máy người dùng

Cần Git, Python 3.11 trở lên; khuyến nghị 3.11/3.12 để tương thích các engine khác. Chạy `local_engine/install-gemini-web.bat` hoặc:

```
python -m local_engine.setup_optional_repos gemini
```

Mặc định cài dưới `SCENEFORGE_LOCAL_DATA/engines/gemini-web` (hoặc thư mục dữ liệu mặc định SceneForge). CLI hỗ trợ `--directory` và `--source` để dùng checkout revision đã có. Không đụng vào môi trường app hoặc ghi đè checkout revision khác.

Bộ cài cần mạng tải repo/thư viện; không yêu cầu Gemini API key hoặc model GB. SDK theo phiên web/tài khoản, hạn mức và quyền tạo ảnh vẫn do Google quyết định. “Không dùng AI Studio key” không đồng nghĩa không giới hạn.

## Chưa làm

- Chưa có adapter SceneForge tự gửi ảnh/prompt qua SDK và nhận kết quả vào đúng phòng. Nút Gemini Chat hiện tại vẫn là sao chép/dán thủ công, không đổi ngầm thành tự động.
- Chưa có UI đăng nhập Google cho engine này hoặc quản lý cookie qua kho mã hóa của app. Repo upstream có lưu cache cookie; trước khi dùng tài khoản cần chủ động nối chỗ lưu, không coi tên cache đã hash là mã hóa cookie.
- Chưa tắt/kiểm soát cơ chế retry/watchdog của upstream để tránh tạo trùng tác vụ, chưa kiểm đồng thời tài khoản/hội thoại thật.
- Chưa xác minh tạo ảnh/giọng/video, quota hay giữ hội thoại qua phiên Google thực tế. Không coi kiểm hợp đồng fixture là Google đã trả kết quả.

AGPL cho phép dùng thương mại nhưng tích hợp/phân phối cần đáp ứng nghĩa vụ giấy phép thích hợp; bản audit giữ LICENSE và revision. Không suy ra video thành phẩm phải công khai chỉ vì runtime dùng AGPL.
