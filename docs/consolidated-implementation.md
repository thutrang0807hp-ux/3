# Bản tổng hợp 22/10/2026 · đối chiếu và triển khai

## Tệp và phạm vi

Nguồn yêu cầu mới: `design/consolidated-received/extracted/SceneForge_BanTongHop/DAC_TA_TONG_HOP.md`, 26 ảnh chuẩn và workbook. ZIP nhận được giữ nguyên trong `design/consolidated-received/SceneForge_BanTongHop.zip`; SHA-256 `3f31fd6efb4c95a304369d78edfc0e4b6d8a6976d75efc67986a39cb2db8e6d3`. Không chạy mã từ tài liệu và không chép nguồn Concat/AGPL. Danh mục/hash tệp nằm trong `consolidated-file-audit.json`.

Đặc tả mới là cơ sở đối chiếu. Không xóa chức năng/dự án từ ảnh đã chạy ở Gói 6 chỉ vì tài liệu xếp chúng sang B2. Workbook 27 dòng trùng byte với bản tổng hợp Gói 6 (SHA-256 `518dae72abdf5807e5f36b705466e46feb378cc2b50e5828e39c6619db0c2768`); giữ bảng trong app 30 mục và kết quả cũ, không lùi/xóa D9–D11. Không biến kiểm thử dữ liệu tổng hợp thành “Đạt” các bài thử Flow/Gemini/VieNeu/gwmr thật.

## Đánh giá bốn vấn đề Dựng trước khi sửa

| Vấn đề | Hiện trạng trước lượt này | Quyết định và bằng chứng |
|---|---|---|
| Kéo clip khựng/chồng/đẩy xa | Lõi đã dùng ghost compositor; chỉ commit model khi nhả chuột, magnetic reorder giữ khít; không gọi updateStage mỗi lần pointermove | Giữ lõi. Đo lại 3/30/100 clip: median ~16,7 ms, p95 ~16,7/16,8/16,8 ms; 100 clip có một long task ~148 ms. Không khẳng định hết khựng trên máy Windows hoặc nguồn video nặng. Test reorder, nhóm, Esc, undo/redo và join resize đạt. |
| Phát qua điểm cắt/chuyển cảnh | Có preload decoder gần vạch, dissolve hai nguồn; chưa có chứng nhận mọi nguồn | Kiểm thử 12 giây/3 clip trên Chromium tại 1366×768, đổi cả bốn bố cục trong lúc phát: không có mẫu thiếu nguồn hình đã sẵn sàng; test pixel chuyển cảnh cũ đạt. Không viết lại player khi chưa có lỗi tái hiện. |
| Reload mất tư liệu | Autosave đã lưu Blob + payload trong một transaction IndexedDB | Test nhập video thật, chờ lưu, reload/khôi phục rồi giải mã lại đúng 720×1280 đạt. Giữ cơ chế và kho cũ. JSON xuất riêng không nhúng tư liệu; vẫn cần nối tệp khi chỉ mang JSON sang máy khác. |
| Xuất MP4 trực tiếp | Chỉ MediaRecorder → FFmpeg đổi bản ghi; không phải render timeline nền | Bổ sung renderer FFmpeg nhận manifest + byte nguồn, không gọi MediaRecorder/captureStream và không phát lại video. Đường cũ vẫn có để giữ các hiệu ứng chưa hỗ trợ. |

Không thay lõi timeline và không đổi giao diện chuyển cảnh người dùng đã duyệt.

## Triển khai mới

- `local_engine/timeline_export.py`: job nhận timeline, upload từng tư liệu, xếp hàng/mã hóa CPU, tiến độ đọc FFmpeg, ETA ước tính từ tiến độ/thời gian thực, hủy, tải MP4. Làn xuất dùng chung lock với bộ chuyển bản ghi cũ, không chạy hai mã hóa cùng lúc.
- Chỉ nhận byte video MP4/WebM, ảnh PNG/JPEG/WebP, audio WAV/MP3/M4A tương thích; không nhận đường dẫn/URL/playlist. Kiểm header cùng app/origin, ID, giá trị hữu hạn, kích thước, dung lượng đĩa; tối đa 120 mục, 10 phút, 512 MB tổng byte nguồn mỗi job. Một số codec trong các container này vẫn phụ thuộc bản FFmpeg trên máy.
- Mã hóa H.264/AAC/yuv420p/faststart 30/60 fps, 720/1080 từ UI. Chạy CPU ngay từ đầu; chưa có nhánh GPU nên không phát sinh lượt retry GPU. Cân âm lượng tùy chọn bằng loudnorm. Video có thể không có audio nếu bản dựng không có luồng tiếng nghe được.
- Hình: contain/cover, vị trí, zoom/xoay/lật/opacity tĩnh; layer theo đúng thứ tự timeline. Cắt thẳng, qua đen, dissolve, slide/wipe tuyến tính. Chuyển cảnh nằm quanh điểm cắt cũ, không rút ngắn/tăng tổng thời lượng. Source thiếu handle được giữ khung biên, cùng cách preview kẹp thời gian nguồn.
- Chữ tĩnh raster một lần bằng canvas/phông hiện dùng, đúng nội dung, xuống dòng, viền, nền, vị trí/xoay/kích thước; FFmpeg ghép lớp PNG trong suốt. Đây không phải ghi lại video trong trình duyệt. Lớp giao diện vùng che TikTok không được đưa vào file.
- Tiếng: trim, offset, tăng/giảm âm lượng đến 20×, vào/ra dần, tốc độ giữ hoặc đổi cao độ, mix nhiều track, mute clip/track. Không tự tắt tiếng các dự án Flow cũ.
- Hộp xuất mở rộng theo ảnh 21: ảnh xem trước bên trái; tên/cách xuất/độ phân giải/fps bên phải; cân âm lượng, checkbox SRT, kiểm tra trước khi xuất. Mất tư liệu chặn xuất; chữ gần mép/vùng che và khoảng trống hình là cảnh báo bấm để nhảy tới vị trí. Chưa phân tích méo tiếng/clipping offline; UI nói rõ.
- Bộ ghi trình duyệt vẫn là đường xuất thật ở bản web tĩnh. FFmpeg chỉ hiện khả dụng khi chạy companion localhost có FFmpeg/ffprobe, không giả backend trên GitHub Pages.
- Đóng hộp tiến độ/chuyển tab trình duyệt không dừng FFmpeg; có thẻ tiến độ, mở lại, hủy. Bản dựng/phòng đang xuất vẫn được giữ, chưa cho đổi phòng hoặc đóng ứng dụng để tránh mất đường nhận kết quả. Backend có thể tiếp tục nếu giao diện mất nhưng chưa có UI nhận lại job sau khởi động lại.
- File chỉ công bố sau khi FFmpeg thành công và ffprobe xác nhận codec/kích thước. Ghi `output.part.mp4` rồi đổi tên `output.mp4`; hủy/lỗi dọn input và file dở. Tệp tạm quá hạn của riêng renderer được dọn, không đụng thư mục phòng/bản xuất của người dùng. Tải về dùng cơ chế trình duyệt; việc chọn nơi lưu/trùng tên tuân theo trình duyệt. App vẫn lưu Blob và mirror sang `7-xuat` theo cơ chế có sẵn; chưa có hộp ghi đè riêng cho native renderer.

## Giới hạn đường FFmpeg mới, không được âm thầm làm mất hiệu ứng

Keyframe, chữ động, bộ lọc màu, audio EQ/compressor/pan nâng cao và easing chuyển cảnh phi tuyến **chưa có parity**: báo rõ, không tự rơi sang ghi màn hình và không tự bỏ hiệu ứng. Dùng “Bộ ghi trình duyệt” cho các bản dựng đó. Chuyển cảnh hai nguồn còn tiếng gốc yêu cầu mute clip và dùng track tiếng riêng ở đường FFmpeg; chưa render audio handle crossfade trực tiếp. Không coi đây là bản renderer đáp ứng toàn bộ mục 8.

Chưa có xuất nền qua nhiều phòng/khôi phục job sau reload, chọn thư mục xuất riêng/đối thoại trùng tên native, đo clipping offline, bitrate/dung lượng dự báo, proxy file lớn, ducking tự động, chữ tự cập nhật từ kịch bản, 30/60 fps cho mọi bước snap/keyframe của editor cũ. Các chức năng này không được đánh dấu đã xong.

## Đối chiếu phần còn lại của đặc tả

| Nhóm | Giữ phần đã có / còn cần làm |
|---|---|
| Khung app/trang chủ/sản phẩm/phòng | Giữ 4 cột, menu sản phẩm, tên nối tiếp, bộ ảnh chép riêng, mirror thư mục, hàng phân tích hai phòng, Gallery Gói 6. Thùng rác hiện trong app, chưa phải OS trash; nguyên tắc giữ bản xuất không đổi. |
| Phân tích local + Gemini | Giữ cắt cảnh/CPU/OCR/motion/quality, lời nghi bịa cách ly, ID cảnh/câu giữ thời gian nguồn, opt-in Google/chi phí chưa rõ. Whisper thật cần model; không có key thật nên D8 chưa xác nhận. Không dùng mô tả ảnh để bịa lời. |
| Khung/clip/Flow/tài khoản | Giữ gallery, phiên bản, duyệt chất lượng, nhập clip thủ công, bảng tài khoản mã hóa. Adapter tạo/credit Flow và Nano Banana 2K chưa nối thật; A3 chưa đạt nên đường nhập clip thủ công vẫn là fallback theo tài liệu. Không tự gửi lệnh tạo lại/tiêu credit. |
| Kịch bản → giọng đọc | Đặc tả mới muốn track VieNeu chung, đo từng câu/giữ mốc nguồn. Hiện voice-over video mẫu vẫn là nhập tay/mô hình thô; adapter VieNeu cũ phục vụ Từ ảnh, chưa hoàn tất track chung này. Chưa cài/kiểm chứng model VieNeu v3 thật; không chứng nhận C1. Không tự đổi hoặc mute tiếng các phòng cũ. |
| Xử lý logo | Giữ bản gốc và công cụ hiện có; chưa có adapter gwmr được kiểm chứng trên clip Veo thật. C2 chưa đạt; không bảo đảm logo/SynthID biến mất. |
| Cài đặt/Thông báo/Màn chào | Giữ cài đặt thật hiện có và lỗi nhà cung cấp có redaction. Chưa có trình cài/tải model/tự khởi động toàn bộ engine Windows hay kiểm credit thật. Các số ví dụ trong ảnh không được nạp thành số tài khoản thật. |
| B2/Từ ảnh/Kho kịch bản | Giữ mã, dữ liệu và giao diện Gói 6 đã chạy. Không xóa khỏi app hoặc di chuyển dữ liệu vì phân kỳ mới. Không bổ sung dịch vụ trả phí hoặc tài khoản chat làm API. |

Môi trường thực thi vẫn là companion `127.0.0.1:8840`; địa chỉ `8000/studio` và đường dẫn mã trong tài liệu tham khảo là kiến trúc cũ, không triển khai lại máy chủ cũ.

## Kiểm chứng

- `python scripts/native-preview/measure_timeline.py` → `docs/timeline-measurements.json`.
- `python scripts/native-preview/check_magnetic_reorder.py`.
- `python scripts/native-preview/check_timeline_interactions.py` (cả PNG/WebM pixel blend).
- `python scripts/native-preview/check_design_panels.py`.
- `python scripts/native-preview/check_consolidated_playback.py`.
- `python scripts/native-preview/check_consolidated.py`: companion thật + trình duyệt, cấm MediaRecorder/captureStream; MP4 720×1280/H.264/AAC + SRT tiếng Việt; đóng hộp và giả lập trang ẩn vẫn xuất; media nhập được lưu/khôi phục và decode sau reload.
- `python -m local_engine.check_timeline_export`: FFmpeg thật, 5 chuyển cảnh, pixel đầu/cuối/giữa dissolve/đen qua cắt, lớp ảnh trong suốt, thời lượng không đổi, AAC, header/path/effect/playlist rejection và hủy dọn tệp.
- `python scripts/native-preview/check_package5.py`, `python scripts/native-preview/check_audio_preservation.py`: đường ghi cũ + SRT và âm thanh yên +20 dB cho RMS khoảng 10×; bảng audio/legacy EQ giữ nguyên.
- `python -m local_engine.check_aggregate`: đường finishing cũ; Google transport giả, không dùng dịch vụ thật.

Kiểm thử bằng video tổng hợp/bundled trên Linux Chromium/FFmpeg. Chưa chứng nhận Windows, video TikTok thật 45 giây/nặng hoặc quy trình đầu-cuối có tài khoản Flow/Gemini/VieNeu/gwmr thật. Bản này là bổ sung có kiểm chứng, chưa phải hoàn thành toàn bộ MVP.
