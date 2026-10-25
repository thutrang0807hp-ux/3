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

Đợt mới đã xử lý job chuẩn bị thất bại, dự phòng ổ của unknown, biên nhận lưu/dọn, checkpoint CPU, ảnh evidence, hash Worker và chia clip. Đọc `docs/reference-flow-improvements.md` cùng `review/REFERENCE_FLOW_FIX_CHECKS.json`; không suy từ mô tả rằng mọi tình huống đã được chứng minh.

- **Job và dung lượng:** thử hết ổ/đứt trong preparing, kiểm submitted chỉ xuất hiện sau chuẩn bị. Unknown giữ bằng chứng nhưng không giữ 500 MB vĩnh viễn. Kiểm lại admission trước download và canonical copy, không tự gửi lại khi kết quả chưa rõ.
- **Lưu/dọn:** mất ACK đã có receipt trong cùng transaction và so digest local. Kiểm trường hợp sửa thêm trong cache, khác library ID, receipt hết vòng lưu, nhiều lượt dọn và file bị khóa. Không chấp nhận cách sửa ghi đè local chỉ vì revision khác.
- **CPU tiếp tục:** checkpoint theo nguồn/options, scene và đoạn ASR 30 giây. Kiểm timeout/cancel/restart, mốc từ tuyệt đối và overlap không lặp; các bước chưa xong vẫn phải chạy lại. Dữ liệu tạm tối đa 7 ngày, không tự giữ vô hạn.
- **Ảnh viết prompt:** đã ưu tiên evidence lớn thay thumbnail, vẫn fallback khi chưa có. Kiểm chất lượng nhãn/sản phẩm và giới hạn số ảnh; bài 768 px chỉ chứng minh đường dữ liệu, không chứng minh prompt luôn tốt.
- **RAM:** đã dùng Worker theo khối để xác minh nguồn; kiểm đỉnh RAM thực tế nhiều phòng. Chưa có benchmark 10 video trên PC người dùng.
- **Hiểu chuyển động:** LK + RANSAC đo nền/camera, không hiểu toàn chuỗi tay/người. Các mẫu đầu/giữa/cuối vẫn có thể bỏ lỡ thao tác ngắn. Truy dữ liệu thực sự Gemini nhận, không suy tên nút thành đã gửi toàn video.
- **Chia clip:** mới có cân mốc câu/hành động nhập tay, tùy chọn đuôi tĩnh và nối từ khung cuối đã duyệt. Không tự đọc đủ duration của mọi model; thời lượng dựng không đồng nghĩa model tạo được đúng thời lượng. Kiểm chuỗi phụ thuộc, lời ở biên và bảo toàn layout/lời của clip cũ.
- **Muse đúng dịch vụ chưa:** SDK vẫn dùng muse.ai, chưa xác nhận Meta AI. Không đánh dấu đã hỗ trợ Meta vì tên Muse giống nhau.
- **Tài khoản và credit:** kiểm selection token, tài khoản thực ghim, giới hạn đồng thời, nhận request nhưng mất response, timeout/restart, kết quả lệch thứ tự. Fixture không chứng minh hạn mức hay phiên thật.

## Cách trả kết quả đánh giá

Với mỗi lỗi/nghi vấn: nêu mức P0/P1/P2, file/hàm/dòng, tình huống tái hiện, dữ liệu bị ảnh hưởng, đề xuất nhỏ nhất và phép kiểm chứng. Phân biệt rõ lỗi đã tái hiện, rủi ro suy từ code và hạn chế có chủ ý. Ưu tiên mất dữ liệu, mất credit, sai cảnh/sai tài khoản, thiếu nội dung trước chuyện giao diện.

Kết luận xem có đủ dùng thử một video ngắn hay chưa và điều kiện còn thiếu. Không yêu cầu cài model nặng hoặc thêm dịch vụ có phí nếu chưa chứng minh cần thiết.

## Bằng chứng và giới hạn của gói

`BUILD_AND_BOOT_CHECK.json` và các báo cáo kèm ghi kết quả trước đó; ngày/snapshot từng báo cáo phải được đọc riêng, không coi mọi bài đã chạy lại lúc đóng gói. Đợt này chỉ kiểm đóng gói, hash, dựng sạch và khởi động app với dữ liệu rỗng. Không tự sửa logic để che nghi vấn, không gửi generation, không chứa model/tài khoản/cookie/dữ liệu dự án thật. Windows và vòng tạo online hoàn chỉnh chưa được chứng nhận.
