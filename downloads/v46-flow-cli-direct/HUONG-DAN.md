# SceneForge v46.50 — gọi CLI gốc

Chạy `SceneForge-Update-20261103-v46.50-Direct-Flow-CLI.exe` để cập nhật bản .48
hoặc .49 hiện có. Gói chỉ thay SimpleFlow và bộ gọi CLI, không thay frontend
hoặc module chuẩn bị ảnh/prompt/upload.

Bấm Tạo video như trước. SceneForge tự tìm bản GFlow Studio/5gdfgfd trong Downloads
(tối đa ba lớp thư mục), dùng profile của bản đó khớp email Flow đã chọn, rồi gọi:

```
<runtime/python.exe hoặc py> -m gflow_cli video r2v --ref <ảnh> --aspect 9:16 --duration 8 --model veo-lite --count 1 --project <dự án> --profile <phiên> --out-dir <kết quả> --json -- <prompt>
```

cwd là thư mục bản gốc tìm được. Bản portable dùng nguyên runtime và đường dẫn
profile của MO-UNG-DUNG.bat. Không tải/cài runtime khác. Không chạy worker SDK,
không ghi đè hàm session, không thay channel/executable_path của SDK. Giữ cả
stdout và stderr trong báo cáo sau khi che dữ liệu nhạy cảm.

Bản gốc cần được giải nén và còn trong Downloads. Không tự chọn phiên khác email
đã chọn, không tự tạo lại lượt không rõ kết quả.

Đã chạy CLI gốc --help, bốn kiểm tra tiến trình CLI và bốn kịch bản dispatch qua
mã lấy từ EXE. Chưa chạy Windows hoặc tạo video Flow thật với bản trên máy bạn.

SHA256: `129bb57936ed049d94005d276d73918e25ba1fe500ae7795f59435fded1eed09`
