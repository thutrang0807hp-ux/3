# SceneForge · Cách lưu trữ dữ liệu (chốt 23/10/2026)

> **Thay** mục 3.3 (du-an.json mỗi phòng) và 3.4 (cây thư mục) trong `DAC_TA_TONG_HOP.md`. Các phần khác giữ nguyên.
> **Phạm vi [MVP]:** phải quyết **trước khi code**, vì đổi cách lưu về sau rất tốn công.
> Luật chung giữ nguyên: ghi an toàn, không bịa số (dung lượng phải đo thật), không lưu key dạng chữ thường.

## 1. Vì sao đổi
| Bất cập cũ | Hậu quả |
|---|---|
| Giữ mọi bản khung / clip + bản gốc trước khi bỏ logo | Ổ đầy nhanh |
| Mỗi phòng 1 `du-an.json`, nhiều luồng cùng ghi | Dễ ghi đè, hỏng file; trang chủ phải đọc hàng trăm file |
| Chép ảnh tham chiếu vào từng phòng, thả trùng video thì lưu 2 lần | Tốn chỗ vô ích |
| Thư mục đặt theo tên sản phẩm / phòng | Đổi tên là phải đổi thư mục, dễ gãy đường dẫn |
| Bản xem nhẹ, ảnh nhỏ, file tạm nằm lẫn với dữ liệu thật | Không biết cái nào xóa được |
| Xóa là mất luôn, không có sao lưu | Lỡ tay hoặc hỏng ổ là mất hết |

## 2. Cấu trúc mới
```
SceneForge/                       ← thư mục gốc (Màn chào / Cài đặt)
├─ thu-vien.db                    ← 1 file SQLite: sản phẩm, phòng, cảnh, lời, prompt, bản, việc, chi phí, công thức
├─ kho/                           ← mọi file thật, đặt tên theo mã hash (không phụ thuộc tên sản phẩm / phòng)
│  └─ ab/abcd1234….mp4
├─ xuat/                          ← video đã xuất, TÊN DỄ ĐỌC (đây là chỗ người dùng mở ra lấy)
│  └─ Son/Son-mau-7_2026-10-23.mp4
├─ cache/                         ← bản xem nhẹ, ảnh nhỏ, sóng âm, file tạm · XÓA LÚC NÀO CŨNG ĐƯỢC, app tự tạo lại
└─ sao-luu/                       ← bản sao thu-vien.db mỗi ngày
```
- Nút "Mở thư mục" trên thẻ video mở **`xuat/<sản phẩm>/`**.
- Nơi lưu file xuất vẫn chọn được trong Cài đặt → Xuất video.

## 3. Dữ liệu: 1 file SQLite
- Dùng `sqlite3` có sẵn trong Python. Bật **WAL** (`PRAGMA journal_mode=WAL`) để phân tích, hàng chờ, tự lưu cùng ghi mà không hỏng.
- Mỗi lần lưu là **1 giao dịch** (transaction): hoặc lưu hết, hoặc không lưu gì. Không có chuyện lưu dở.
- **Bảng gợi ý:**
  - `product`, `room`, `scene`, `script_line`
  - `asset` (hash, loại, cỡ, đường dẫn trong `kho/`)
  - `version` (khung / clip: phòng, cảnh, số bản, asset, ghim, đang chọn)
  - `job` (hàng chờ), `cost_log`, `formula`, `notification`
- Các trường giống mô hình dữ liệu ở mục 5.13 của bản tổng hợp, chỉ đổi từ file JSON sang bảng.
- Trang chủ đọc thẳng từ SQLite nên tải tức thì kể cả khi có hàng trăm video.
- **Mang đi / sao lưu một phòng:** xuất ra `.zip` gồm `du-an.json` + các file của phòng **[B2]**. Nhập lại được.

## 4. File theo "dấu vân tay" (chống trùng)
- Mỗi file vào app (video mẫu, ảnh tham chiếu, khung, clip, giọng) được tính **hash** bằng `hashlib`, rồi lưu vào `kho/` với tên là hash đó.
- **File giống hệt chỉ lưu 1 lần.** Thả trùng video mẫu, hay 10 phòng cùng dùng một bộ ảnh, thì vẫn chỉ có 1 bản trên ổ.
- Phòng chỉ **trỏ tới** file. Ảnh tham chiếu sửa riêng trong phòng thì sinh file mới, bộ gốc không đổi.
- Đổi tên sản phẩm / phòng **không đụng tới file**.
- Đây là cách Git / DVC chống trùng (chỉ học ý, không cần cài).

## 5. Luật giữ bản
- Mỗi cảnh luôn giữ:
  - **Bản đang chọn.**
  - **2 bản gần nhất.**
  - **Bản có 📌 ghim.**
- Bản cũ hơn **tự dọn khi video vào Lưu trữ** (hoặc khi bấm Dọn cho nhẹ). Báo trước số MB.
- **Bản gốc trước khi bỏ logo Veo** (`.goc`): giữ tới khi video **xuất xong**, rồi tự dọn. Bản nào ghim thì giữ.
- 🆕 **Nút 📌 Ghim bản** trong tab *Các bản* và trong màn phóng to.

## 6. Xóa và dọn
- **Xóa** (phòng, sản phẩm, bản) thì đưa vào **Thùng rác của Windows** bằng **Send2Trash**, khôi phục được.
- **Dọn file không dùng** (Cài đặt → Thư mục lưu): app so `kho/` với SQLite, tìm file không còn ai trỏ tới, báo trước số MB rồi mới xóa.
- **Xóa `cache/`** an toàn bất cứ lúc nào.
- File trong `xuat/` **chỉ xóa khi người dùng tự xóa**.

## 7. Sao lưu
- Mỗi ngày (hoặc khi mở app lần đầu trong ngày), chép `thu-vien.db` vào `sao-luu/`. Giữ 14 bản gần nhất. Chỉ vài MB.
- Dùng lệnh sao lưu có sẵn của SQLite (`connection.backup`), chép được cả lúc app đang ghi.
- Cài đặt → Thư mục lưu: dòng "Sao lưu gần nhất: <giờ>" + nút **Khôi phục từ bản sao lưu…** (hỏi lại trước khi khôi phục).
- **Chuyển sang ổ khác** (đã có): chép `thu-vien.db` + `kho/` + `xuat/`, kiểm tra đủ hash rồi mới xóa chỗ cũ. Bỏ qua `cache/`.

## 8. Thư viện
| Việc | Dùng | Giấy phép |
|---|---|---|
| Dữ liệu | `sqlite3` (có sẵn trong Python) | Public domain |
| Dấu vân tay file | `hashlib` (có sẵn) | — |
| Đưa vào Thùng rác | **Send2Trash** https://github.com/arsenetar/send2trash | BSD-3 |
| Chỗ đặt dữ liệu chuẩn | platformdirs | MIT |

## 9. Bài tự thử
1. Thả cùng một video 2 lần: `kho/` chỉ có 1 file.
2. Đổi tên sản phẩm: mọi phòng vẫn mở được, không mất file.
3. Tắt app đột ngột lúc đang phân tích 2 video + đang tải clip: mở lại, dữ liệu không hỏng.
4. Xóa `cache/`: app tự tạo lại, không mất gì.
5. Xóa 1 phòng: file nằm trong Thùng rác, khôi phục được.
6. Khôi phục `thu-vien.db` từ bản sao lưu hôm qua: mở được bình thường.
7. 200 video trên trang chủ: tải nhanh, cuộn mượt.
