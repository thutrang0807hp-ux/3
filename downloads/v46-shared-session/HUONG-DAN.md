# SceneForge v46.45 — bản thử session/RPC dùng chung

Yêu cầu **v46.42 trở lên**, cài được trên .43 hoặc .44. Bản mới ghi
`2026.11.03.4645` trong `app-build.json`.

## Cài và thử một cảnh

1. Đóng SceneForge. Chạy `SceneForge-Update-20261103-v46.45-Native-Pipeline-Trial.exe`.
2. Chọn đúng thư mục có `SceneForge.exe` và `install-settings.json`. Updater
   kiểm baseline/phiên bản và sao lưu file thay. Giữ tài khoản, profile, dữ
   liệu, model và runtime hiện có.
3. Mở lại app, chọn tài khoản web đang dùng và **một cảnh** cần làm, ảnh đã
   duyệt và prompt. Giữ Ingredients · Lite · 9:16 · x1.
4. Bấm **Tạo 1 video** một lần, xác nhận. Không cần bước Thử ảnh + prompt.
   Nếu Flow chấp nhận, yêu cầu có thể dùng credit.
5. Nếu lỗi hoặc chưa rõ kết quả, không bấm tạo lặp lại. Bấm **Tải báo cáo
   theo dõi video** rồi gửi JSON cùng thông báo lỗi. Báo cáo tải được cả khi
   upload thất bại và không tự gửi thêm job.

Các lượt `unknown` cũ vẫn giữ nguyên; bản này không tự mở khóa hoặc gửi lại.

## Khác .44

Upload, generation và tracker dùng cùng module context/transport. Generation
có locale, project referrer, credentials mode và sequence nhất quán với các
bước còn lại. Có fallback metadata trong cùng trang/project; không lấy context
từ project khác. Các cổng read/bootstrap/generation có whitelist riêng.

Giữ cách xác minh thông thường của trang, không chép can thiệp browser/xác
minh từ Phoma. Đây không phải bản sao toàn bộ môi trường Phoma. Báo cáo không
còn ghi “sẵn sàng gửi” sau khi đã gửi hoặc bị từ chối.

## Kiểm chứng và giới hạn

Gói chứa 10 file payload, gồm module mới `flow_batch_session.py` và workflow
HTML. Đã kiểm hash từng file, ZIP integrity và mã Python trích từ EXE. Backend
và UI trích từ gói đã chạy kiểm thử offline/Chromium với HTTP fixture và video
mẫu, gồm thành công, RPC từ chối, metadata fallback và tải báo cáo upload lỗi.

**Chưa xác minh tạo video trên Flow thật hoặc chạy updater trên Windows. Chưa
khẳng định sửa được PUBLIC_ERROR_UNUSUAL_ACTIVITY.** Việc payload/metadata
fixture khớp Phoma không chứng minh Google chấp nhận phiên thực tế.

Không có tự resume tác vụ sau restart hoặc hàng đợi nhiều cảnh trong bản thử.
Nếu Flow đã nhận yêu cầu nhưng app mất kết quả thì vẫn cần đối soát lượt cũ.
