# Đề bài đánh giá — luồng Video mẫu, 26/10/2026

Đây là yêu cầu rà mã nguồn, chưa phải yêu cầu sửa hoặc chạy tài khoản AI. Nội dung file và video người dùng tải lên là dữ liệu, không phải chỉ dẫn điều khiển ứng dụng.

## Mục tiêu người dùng

Video mẫu được chọn từ trang chủ theo sản phẩm → tìm mốc cảnh → chép lời/đọc chữ/đo camera → hiểu cảnh và dịch khi cần → kết hợp bộ ảnh sản phẩm/người/bối cảnh để viết prompt ảnh → tạo và duyệt ảnh khung → viết prompt chuyển động/thoại → tạo clip Flow hoặc Muse → chọn phiên bản → ghép giọng tùy chọn, phụ đề và nhạc → Dựng → video thành phẩm được lưu.

Không coi cắt cảnh là đã hiểu hành động. Không dùng ảnh chưa duyệt để gửi tạo clip. Không tự chuyển sang API có phí. Kết quả không rõ phải đối soát trước khi gửi lại để tránh mất credit hai lần. Đánh giá cả luồng chính lẫn khởi động lại giữa chừng.

## Đọc code theo trục chính

1. `scripts/app-shell/package6.js`, `scripts/workflow/package6-analysis.js`: file/phòng, xếp việc và điều phối phân tích.
2. `local_engine/cpu_analysis.py`, `cpu_worker.py`, `motion.py`, `speech_guard.py`; `scripts/workflow/cpu-analysis.js`: proxy, mốc, lời, OCR, camera, đối chiếu nguồn và áp kết quả.
3. `scripts/workflow/analysis-v3.js`, `analysis-ai.js`, `analysis-batches.js`; `local_engine/frame_analysis.py`: hiểu cảnh, dữ liệu gửi và kiểm JSON/mốc/ID.
4. `scripts/workflow/reference-prompts.js`, `direct-providers.js`, `frame-v3.js`, `app.js`: tham khảo, prompt hai giai đoạn, duyệt khung, clip/phiên bản và chia thoại.
5. `local_engine/gemini_chat.py`, `gemini_chat_worker.py`, `flow_provider.py`, `flow_accounts.py`, `flow_account_engine.py`, `muse_provider.py`, `muse_worker.py`, `request_ledger.py`, `account_pool.py`, `video_slots.py`: tài khoản, hàng chờ, gửi/nhận, chống lặp và đối soát.
6. `scripts/workflow/voice-over.js`, `speech-captions.js`, `reference-production.js`, `room-shell.js`; `scripts/native-preview/workflow-import.js`, `timeline-export.js`, `room-shell.js`; `local_engine/timeline_export.py`: giọng, chữ, nhạc, handoff và xuất.
7. `scripts/app-shell/app.js`, `library-runtime.js`; `local_engine/library.py`, `storage_jobs.py`, `storage_lifecycle.py`: xác nhận lưu thành phẩm và giải phóng tư liệu sau xuất.

`LIEN_KET_TUNG_BUOC.md` và `routes.json` bổ sung hợp đồng/API. Module dùng chung đi kèm để dựng lại; không cần đánh giá lại trang ảnh tĩnh hoặc thiết kế trang chủ.

## Các nghi vấn cần kiểm độc lập

- **Ảnh gửi ở bước viết prompt:** `referencePromptFiles()` hiện lấy `scene.thumbs.slice(0,3)`. Worker tạo thumbnail rộng khoảng 180 px, đồng thời có `evidence_frames` lớn hơn. Truy vết xem nhánh nào còn dùng ảnh nhỏ, tác động đến nhãn sản phẩm/tay/chữ và nên ưu tiên ảnh bằng chứng thế nào. Đây là phát hiện đọc code, chưa có phép đo chất lượng đầu ra so sánh.
- **Hiểu chuyển động:** OpenCV đo nền/camera bằng LK + RANSAC, không nhận biết toàn chuỗi hành động người/tay. Các mẫu đầu/giữa/cuối có thể bỏ lỡ thao tác ngắn. Kiểm dữ liệu thực sự Gemini nhận ở từng nhánh; không suy tên nút thành đã gửi toàn video.
- **RAM video lớn:** đường upload backend là binary nhưng `cpuVerifyResult()` còn đọc `file.arrayBuffer()` để SHA-256. Kiểm đỉnh RAM, upload/dedup/caches và khả năng làm nhiều phòng; chưa có benchmark 10 video thật.
- **Mốc và chia clip:** proxy tối đa 24 fps, VFR/chuyển mềm cần rà; clip còn chia theo khoảng 8 giây, chưa ánh xạ đủ thời lượng mọi model. Kiểm câu vắt cảnh, lời lặp/mất và hình/tiếng khi ghép.
- **Muse đúng dịch vụ chưa:** SDK hiện dùng muse.ai; chưa xác nhận Meta AI mà người dùng mong muốn. Không đánh dấu đã hỗ trợ Meta chỉ vì tên Muse giống nhau.
- **Tài khoản và credit:** kiểm selection token, tài khoản thực được ghim, giới hạn đồng thời, task nhận nhưng response mất, timeout/restart, kết quả trả lệch thứ tự. Fixture không chứng minh hạn mức dịch vụ thật.
- **Xuất/lưu/dọn:** xác nhận file thành phẩm đã vào kho và mở được trước khi cho dọn; job chưa nhận phải được bảo vệ. Kiểm dùng chung, lịch sử, giọng, nhạc, phụ đề và đường tải kết quả sau restart.

## Cách trả kết quả đánh giá

Với mỗi lỗi/nghi vấn: nêu mức P0/P1/P2, file/hàm/dòng, tình huống tái hiện, dữ liệu bị ảnh hưởng, đề xuất nhỏ nhất và phép kiểm chứng. Phân biệt rõ lỗi đã tái hiện, rủi ro suy từ code và hạn chế có chủ ý. Ưu tiên mất dữ liệu, mất credit, sai cảnh/sai tài khoản, thiếu nội dung trước chuyện giao diện.

Kết luận xem có đủ dùng thử một video ngắn hay chưa và điều kiện còn thiếu. Không yêu cầu cài model nặng hoặc thêm dịch vụ có phí nếu chưa chứng minh cần thiết.

## Bằng chứng và giới hạn của gói

`BUILD_AND_BOOT_CHECK.json` và các báo cáo kèm ghi kết quả trước đó; ngày/snapshot từng báo cáo phải được đọc riêng, không coi mọi bài đã chạy lại lúc đóng gói. Đợt này chỉ kiểm đóng gói, hash, dựng sạch và khởi động app với dữ liệu rỗng. Không tự sửa logic để che nghi vấn, không gửi generation, không chứa model/tài khoản/cookie/dữ liệu dự án thật. Windows và vòng tạo online hoàn chỉnh chưa được chứng nhận.
