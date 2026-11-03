# SceneForge .52 — nhận lại video đã tạo, không tạo lại

Cập nhật từ .50 hoặc .51. Giữ nguyên phần gửi tạo đang chạy được.

Báo cáo hiện tại là MediaDownloadError/HTTP 302: video đã được tạo nhưng CLI
không tải được link media. Bản này lưu ID và dùng CLI gốc:

```
python -m gflow_cli data download <media_id> --profile <profile> --out <output> --json
```

- Lượt mới gặp lỗi tải: tự thử một lần tải lại đúng ID, không gọi lại video r2v.
- Lượt cũ đang lỗi: mở đúng cảnh, bấm **Kiểm tra video cũ / Tải báo cáo theo dõi
  video**. Phần mềm dùng ID trong báo cáo đã lưu để tải lại, rồi nhập về cảnh.
- Không bấm Tạo video mới để lấy lại clip cũ.
- Nếu tải lại vẫn lỗi, giữ ID và ghi cli_download_diagnostics; không tự tạo lại.

Đã kiểm tra bảy kịch bản CLI cục bộ, API/ledger/ffprobe/file thực và đồng bộ UI
trên mã trích từ EXE. CLI/browser trong các kiểm tra dùng fixture; chưa xác minh
việc tải clip thật trên máy người dùng hoặc chạy updater trên Windows.

SHA256 EXE: `ce111ff1713aec5f531c2111544aba0869f7a4c13ea898214ad889ec474038b8`
