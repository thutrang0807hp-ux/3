# SceneForge v46.60 — CLI gốc và runtime đi kèm

Đóng SceneForge, chạy `SceneForge-Update-20261104-v46.60-Bundled-Original-CLI.exe`, mở lại và tạo video. Cập nhật trên .52 trở lên, gồm .58/.59. Gói khoảng 88 MB vì đã chứa runtime, không yêu cầu cài Python/GFlow hay tìm thư mục trong Downloads.

- Mặc định gọi trực tiếp Python đi kèm qua `-m gflow_cli video r2v/i2v`, nguyên bản 0.92.1 trong repo người dùng gửi.
- Runtime gốc được ghim SHA256 và nhúng trong EXE. Lần đầu dùng sẽ giải nén tự động từ tệp cục bộ vào Data/flow-engine, không tải phụ thuộc từ mạng.
- CLI dùng cùng profile Chrome đã đăng nhập của tài khoản SceneForge đang chọn, qua NTFS junction trong Data/flow-cli. Không sao chép cookie, không đóng gói tài khoản và không ghi đè các hàm session của SDK. Kiểm tra email/profile trước khi gọi.
- Các cấu hình, trạng thái/ID sớm, tải phục hồi theo ID và nhập đúng cảnh vẫn dùng luồng đã có. Không tự gửi lại lệnh tạo.
- Giữ nguyên các phiên bản/dữ liệu người dùng. Google Chrome vẫn là trình duyệt hệ thống mà CLI gốc dùng cho profile Chrome này.

Nguồn runtime: https://github.com/thutrang0807hp-ux/5gdfgfd/tree/09ab05b190ddad0b3bbed80439ecbc6739d5abce
Archive upstream SHA256: `03ae9541fefa55e4f917f87db794cd2b26f61d5d215a754b333b5dfc3d686292`. Toàn bộ runtime/CLI và license bên trong được giữ nguyên; không sử dụng worker SDK tự viết. Gói upstream không có profile/dữ liệu đăng nhập.

Đã kiểm tra 10 tệp nhúng trong EXE và checksum từng tệp; cấu trúc PE/CLR đọc được, mã launcher giữ nguyên, vùng resource được mở rộng để chứa runtime. 24 kiểm thử CLI/profile qua, gồm Python đi kèm, không gọi bộ dò Downloads, tải lại video, cùng profile và chặn email/alias khác. Tuyến backend thật với CLI giả lập vẫn tạo/tải/nhận đúng. Runtime nguyên bản lấy từ EXE giải nén được khi mạng bị chặn.

Các kiểm tra chạy cục bộ trên Linux với fixture, chưa chạy bộ cài/NTFS junction trực tiếp trên Windows hoặc tạo video trên Flow thật. Không khẳng định đã xác minh tài khoản người dùng.

SHA256 EXE: `24b2b26b0fbd2a30490737124f2d5b837538f5008945ad069040f150ca50782e`
