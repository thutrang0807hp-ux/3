# SceneForge · Phần "phía sau" để app chạy ổn định (chốt 23/10/2026)

> Đi cùng `DAC_TA_TONG_HOP.md` và `SceneForge_LuuTru.md`. Người dùng không thấy những phần này, nhưng thiếu thì app đứng, mất dữ liệu hoặc mất credit.
> Ký hiệu: 🔴 **phải có từ bản đầu (MVP)** · 🟠 nên có ở bản đầu · 🟡 làm sau được.
> Luật chung giữ nguyên: không nút giả, không bịa số, không lưu key dạng chữ thường, không chép mã AGPL.

---

## 1. Ổn định và an toàn

### 1.1 🔴 Bảo vệ server trên máy (127.0.0.1)
- Server Python **chỉ nghe 127.0.0.1**, không bao giờ 0.0.0.0.
- **Mọi lệnh từ giao diện phải kèm mã bí mật** do app sinh ngẫu nhiên lúc mở (đưa vào trang khi tải). Thiếu hoặc sai mã thì từ chối.
- Kiểm tra `Origin` / `Host`: chỉ nhận đúng `http://127.0.0.1:<cổng>`. Chặn kiểu tấn công đổi tên miền (DNS rebinding).
- Lý do: một trang web lạ mở trong trình duyệt **có thể gọi lén vào localhost**, ví dụ bấm tạo clip (mất credit) hoặc đọc dữ liệu.
- Động cơ (flow2api, muse2api) cũng chỉ nghe 127.0.0.1, đổi mật khẩu admin và key mặc định (đã ghi ở mục 10 bản tổng hợp).

### 1.2 🔴 Hàng chờ bền, không gửi trùng
- Mỗi việc là 1 dòng trong SQLite. **Sơ đồ trạng thái:**
  ```
  chờ → đang gửi → đã gửi (có mã việc của Flow) → đang tạo → xong
                                                           ↘ lỗi
  ```
- Mỗi việc có **mã chống trùng** (idempotency key), sinh **trước khi** gửi.
- Mất mạng, mất điện, app tắt khi việc đang ở "đang gửi" / "đã gửi" / "đang tạo": lúc mở lại **chỉ hỏi Flow trạng thái theo mã**, **không gửi lại lệnh tạo**.
- Việc lỗi không tự chạy lại (tốn credit). Việc **phân tích** (0đ) thì được tự chạy tiếp.
- Mỗi lần đổi trạng thái là **1 giao dịch SQLite**.

### 1.3 🔴 Giám sát động cơ
- Động cơ: flow2api · VieNeu · gwmr · FFmpeg (muse2api ở bản 2).
- App tự bật khi mở, kiểm tra định kỳ bằng `/health` (hoặc chạy thử lệnh nhỏ).
- Động cơ chết thì **tự khởi động lại 1 lần**, vẫn chết thì báo "Cần bạn" + Sao chép chi tiết lỗi.
- **Thoát app thì tắt sạch** mọi tiến trình con. Lần mở sau kiểm tra và dọn tiến trình sót, cổng bị chiếm.
- Cổng bị app khác chiếm thì tự chọn cổng khác và ghi lại.

### 1.4 🟠 Chỉ 1 bản app chạy
- Mở app lần 2 thì không chạy bản mới, **mà đưa cửa sổ đang có lên trước**.
- Dùng file khóa trong thư mục dữ liệu (hoặc khóa theo cổng).

### 1.5 🟠 Mất mạng
- Các bước chạy trên máy (cắt cảnh, chép lời, đọc chữ, giọng, dựng, xuất) **vẫn chạy**.
- Việc cần mạng (Gemini, Flow) **tạm dừng**, hiện "⏸ Chờ có mạng" (màu vàng nhạt, **không báo lỗi đỏ**). Có mạng lại thì tự chạy tiếp.

### 1.6 🟠 Máy ngủ / gập máy
- Khi máy thức dậy, coi như vừa mất kết nối: hỏi lại trạng thái việc, **không gửi lại**. Kiểm tra lại phiên tài khoản trước khi chạy tiếp.

### 1.7 🟠 Giao diện mất kết nối với nền
- Tiến độ đẩy liên tục qua WebSocket hoặc SSE.
- Tải lại tab / đóng mở trình duyệt thì **tự nối lại**, việc vẫn chạy nền, tiến độ hiện lại đúng.

---

## 2. Bộ nhớ và dọn dẹp

> Ổ đĩa = chỗ lưu file (mất điện vẫn còn). RAM = bộ nhớ tạm khi app chạy (đầy là máy đơ).

| | Việc | Cách làm |
|---|---|---|
| 🔴 | **Trần cỡ `cache/`** | Mặc định 10 GB, chỉnh được. Vượt trần thì **tự xóa file lâu không dùng nhất** trước |
| 🔴 | **Mô hình AI để riêng `models/`** | VieNeu, faster-whisper, RapidOCR. Dọn cache **không bao giờ** xóa `models/` |
| 🟠 | **Nhả RAM khi rảnh** | Mô hình chép lời / giọng / OCR dùng xong thì **nhả khỏi RAM sau ~5 phút không dùng**, cần thì nạp lại |
| 🟠 | **File tạm của FFmpeg** | Chỉ FFmpeg ghi vào `cache/tmp/`, không ghi vào thư mục tạm của Windows. **Dọn mỗi lần mở app** |
| 🟠 | **Ngân sách sức máy** | Việc nặng (chép lời, OCR, xuất video) **xếp lượt**, không chạy hết cùng lúc. Xuất video ưu tiên. Kiểm tra ổ trống trước mỗi việc nặng |
| 🟡 | **Bảng dung lượng** (Cài đặt → Thư mục lưu) | Chia: dữ liệu thật · video đã xuất · cache · mô hình AI · bản sao lưu. Mỗi phần có nút dọn riêng, **hiện số MB đo thật trước khi dọn** |

Thư mục (bổ sung cho `SceneForge_LuuTru.md`):
```
SceneForge/
├─ thu-vien.db   kho/   xuat/   sao-luu/
├─ cache/        ← có trần, tự dọn; cache/tmp/ dọn mỗi lần mở
├─ models/       ← mô hình AI, không bị dọn
└─ logs/         ← nhật ký, tự xoay vòng
```

---

## 3. Nhật ký (log)
- 🟠 Ghi log theo **từng dịch vụ** (app, flow2api, Gemini, VieNeu, FFmpeg…), kèm giờ, mã phòng, mã việc.
- **Tự chia file theo dung lượng** (ví dụ 5 MB / file, giữ 10 file). Dùng `logging.handlers.RotatingFileHandler`.
- **Tự che key, cookie, token** trước khi ghi.
- Nút **📋 Sao chép chi tiết lỗi** lấy đoạn log liên quan từ đây.

---

## 4. Cập nhật và dữ liệu cũ
- 🟡 **Cập nhật app:** dòng nhỏ trong Cài đặt "Có bản mới · Cập nhật". Dữ liệu giữ nguyên.
- 🟠 **Nâng cấp dữ liệu:** ghi số phiên bản cấu trúc SQLite (`PRAGMA user_version`).
  - Bản mới đổi cấu trúc thì **tự sao lưu `thu-vien.db` trước**, rồi chạy bước nâng cấp.
  - Lỗi thì quay về bản sao lưu và báo.
- 🟠 **Gỡ app:** hỏi có giữ thư mục dữ liệu không, **mặc định là giữ**.

---

## 5. Cài đặt trên Windows
- 🟠 **Đường dẫn tiếng Việt, dấu cách, đường dẫn dài:**
  - Toàn bộ dùng UTF-8.
  - File bên trong đặt theo mã hash (đã có nhờ phần lưu trữ).
  - Gọi FFmpeg bằng danh sách tham số, không ghép chuỗi lệnh.
  - **Thử ngay từ đầu** với thư mục có dấu, ví dụ `D:\Sản phẩm mới\`.
- 🟠 **Tường lửa / phần mềm diệt virus:**
  - Màn chào báo trước "Windows có thể hỏi quyền mạng · bấm Cho phép".
  - Bộ cài nên có chữ ký số để đỡ bị báo nhầm là virus.
- 🟡 **Mở app nhanh:** hiện trang chủ trước, bật động cơ ngầm sau. Chưa cần động cơ nào thì chưa bật.
- 🟠 **Cấu hình máy tối thiểu:**
  - Chạy thử trên **máy yếu** (ví dụ laptop 8GB RAM, không card đồ họa).
  - Ghi ra "máy tối thiểu", hiện ở Màn chào bước 2 nếu máy dưới mức.

---

## 6. Kiểm thử
- 🟠 **Chế độ thử (0 credit):**
  - Thay Flow bằng **"Flow giả"**: trả về clip làm từ chính khung gốc, cho chuyển động nhẹ bằng FFmpeg (zoom chậm).
  - Chạy trọn luồng khung → clip → Dựng → xuất **không tốn credit**.
  - Bật trong Cài đặt → Động cơ. Trên giao diện có nhãn "CHẾ ĐỘ THỬ" rõ ràng để không nhầm với clip thật.
- 🟠 **Bộ test tự động:**
  - 1–2 video mẫu cố định (có thư mục tiếng Việt) + Flow giả.
  - Chạy cả luồng sau mỗi lần sửa code.
  - Thêm các bài tự thử ở mục 8.11 bản tổng hợp và mục 9 file lưu trữ.

---

## 7. Video mẫu không đúng chuẩn (kiểm tra ngay lúc thả)
- 🟡 **Video ngang:** "Video ngang · cắt thành dọc 9:16?" (cắt giữa, hoặc bỏ qua).
- 🟡 **Dài quá 90 giây:** "Dài 2:10 · chỉ lấy 60 giây đầu?" (chỉnh được đoạn lấy).
- 🟡 **Không có tiếng / nhiều người nói:** ghi chú ngay trên ô Video tham khảo, không để chạy tới giữa mới lỗi.
- 🟡 **File hỏng / định dạng lạ:** báo ngay + Sao chép chi tiết lỗi.

---

## 8. Giấy phép, quyền riêng tư, pháp lý
- 🔴 **Trang "Giấy phép"** trong Cài đặt: liệt kê mọi thư viện / repo đã dùng kèm giấy phép. MIT, Apache, BSD **bắt buộc giữ thông báo bản quyền**. Thiếu trang này là vi phạm giấy phép.
- 🟠 **Không thu thập dữ liệu:** app không gửi gì về đâu. Ghi rõ 1 dòng trong Cài đặt.
- 🟠 **Quyền dùng hình người:** khi thêm ảnh người vào Bộ ảnh, hiện 1 dòng nhắc *"Chỉ dùng ảnh của người đã đồng ý cho làm video AI"*.
- 🟡 **Điều khoản Google / Meta / TikTok có thể đổi:** xem lại mỗi vài tháng. Luôn giữ đường dự phòng: nhập clip tay, key Gemini trả phí.
- Nhắc tick nhãn "Nội dung do AI tạo" khi đăng TikTok (đã có trong thông báo Xuất xong).

---

## 9. Prompt và repo giúp ích thêm

### 9.1 🔴 Sửa mẫu prompt Veo theo hướng dẫn chính thức của Google (0đ)
- **Công thức:** **Góc máy + Chủ thể + Hành động + Bối cảnh + Phong cách & ánh sáng**.
- Lời thoại để trong ngoặc kép, ví dụ: `She says in Vietnamese, Southern accent: "…"`.
- Tiếng động ghi riêng: `SFX: …`. Âm nền: `Ambient noise: …`.
- **Tả cái muốn có thay vì viết "không có…"**, ví dụ "bàn trống, chỉ có chai sản phẩm" thay vì "no clutter".
- Ảnh tham chiếu thì **gọi theo vai**: "Using the provided images for the woman and the cleanser bottle…".
- Áp vào mục 5.12 bản tổng hợp (VISUAL / MOTION & SCRIPT giữ nguyên ý, chỉ sắp lại theo thứ tự trên).
- Nguồn: https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-veo-3-1

### 9.2 🟡 Thử: nhiều cảnh trong 1 clip bằng mốc giây
- Ví dụ `[00:00-00:02] …`, `[00:02-00:05] …` trong một prompt 8 giây. Nếu ổn thì gộp 2–3 cảnh ngắn thành 1 clip, **đỡ credit**.
- Google ghi là thử nghiệm, nên phải thêm vào bảng thử thật trước khi dùng.

### 9.3 📖 awesome-video-prompts (chỉ đọc)
- https://github.com/songguoxs/awesome-video-prompts: prompt mẫu dạng JSON, có cảnh demo sản phẩm.
- **Không có giấy phép, khoảng 1 năm không cập nhật** → chỉ đọc để học cách viết, **không chép vào app**.

### 9.4 🟠 OpenReel: xem trước khi động vào tab Dựng
- https://github.com/Augani/openreel-video (MIT, khoảng 5.400 sao).
  - Trình dựng video chạy trong trình duyệt: timeline nhiều track, cắt, chuyển cảnh, phụ đề SRT, sóng âm, tự nhỏ nhạc khi có giọng, xuất MP4 (WebCodecs).
  - Công nghệ: React, TypeScript, WebCodecs, WebGPU.
- Tab Dựng hiện khoảng 70%, nhiều lỗi lặt vặt, đang phải quyết vá hay viết lại lõi timeline. **Phương án thứ 3:** lấy lõi timeline của OpenReel (MIT, chép được, giữ thông báo bản quyền) rồi gắn giao diện SceneForge.
- **Phải đánh giá trước:**
  - Chạy thử, đo độ mượt khi kéo clip và khi phát.
  - Đọc mã: có tách được lõi timeline không.
  - Xem lần cập nhật gần nhất (bản desktop còn alpha).
  - Xuất MP4 có giống y lúc xem không.

### 9.5 Đã có, không cần thêm
- Chạy hàng loạt Flow / Muse: **flow2api / muse2api + hàng chờ của app**. Không thêm repo "chạy nhanh hàng loạt" vì tăng rủi ro bị khóa tài khoản.

---

## 10. Thư viện cho phần này
| Việc | Dùng | Giấy phép |
|---|---|---|
| Quản lý tiến trình động cơ, đo RAM / CPU | **psutil** | BSD-3 |
| Log xoay vòng | `logging` (có sẵn trong Python) | — |
| Dữ liệu, nâng cấp cấu trúc | `sqlite3` + `PRAGMA user_version` (có sẵn) | Public domain |
| Đưa vào Thùng rác | Send2Trash | BSD-3 |
| Chỗ đặt dữ liệu chuẩn | platformdirs | MIT |
| Đẩy tiến độ lên giao diện | WebSocket / SSE của framework web đang dùng | — |

> Giấy phép ghi theo hiểu biết hiện tại, **kiểm lại khi cài** và ghi vào trang "Giấy phép".

---

## 11. Thứ tự làm (chen vào mục 13 của bản tổng hợp)
1. Ngay khi dựng khung app: **1.1 bảo vệ 127.0.0.1**, **1.4 chỉ 1 bản chạy**, **3 log**, **5 đường dẫn tiếng Việt**, **8 trang Giấy phép**.
2. Cùng lúc làm hàng chờ Flow: **1.2 hàng chờ bền**, **1.3 giám sát động cơ**, **1.5–1.6 mất mạng / máy ngủ**, **6 chế độ thử + Flow giả**.
3. Trước khi làm tab Dựng: **9.4 đánh giá OpenReel**.
4. Trước khi phát hành: **2 bộ nhớ**, **4 cập nhật / gỡ app**, **5 máy tối thiểu**.
