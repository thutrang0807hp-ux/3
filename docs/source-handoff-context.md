# Ngữ cảnh bàn giao · 28/10/2026

## Mong muốn và phạm vi hiện tại

Người dùng muốn app ít thao tác, Gemini hiểu/viết còn code chuẩn bị dữ liệu, gắn ảnh, kiểm và điều phối. Không thêm kho prompt, chấm điểm hoặc lịch sử prompt/media không cần thiết. Nút Chạy tự động ban đầu cho phép tiến tới điểm dừng đã chọn; không bắt xác nhận lại ở mỗi node bình thường. Giữ quyền sửa tay; dừng khi thiếu dữ liệu, lỗi hoặc chưa rõ kết quả. Không tự xuất MP4.

**Việc mới nhất được yêu cầu là đóng gói đầy đủ mã nguồn để chuyển nơi phát triển. Kho kịch bản v5 đã được yêu cầu tạm hoãn.** Các file v5 chỉ được bảo tồn làm thiết kế tham khảo. Nhu cầu người dùng giải thích cho v5: dán link video → lấy lời → viết lại cho sản phẩm của mình → sửa/copy/lưu/dùng tạo video. Chưa thực hiện luồng v5 này.

## Các phần đã có trong code

- Hai workspace Video mẫu và Từ ảnh & ý tưởng, thanh khung/menu/nguồn, minimap cùng tô node đang chọn.
- Node phân tích/cảnh/tham chiếu/ảnh khung/Veo, giọng/nhạc/phụ đề, chuyển Dựng và Ghép & xuất theo source hiện hành. Bảng mở rộng là view của node, không tạo node trùng.
- Storyboard một node/hai chế độ: ảnh tổng tham khảo hoặc ảnh từng cảnh dùng tạo video; ảnh đầu/cuối chỉ bật theo capability của model/adapter.
- Node ảnh đầu vào và kịch bản nguyên văn: product-first, người/mặt chuẩn tùy chọn, lưu/copy từ Kho, giữ ID/media khi sửa; các thao tác AI có receipt.
- Nguồn ảnh Meta AI dùng web-images adapter cùng nhóm tài khoản Batch; viết prompt production vẫn Gemini Chat. Muse video là adapter riêng; không mặc định Muse và Meta AI dùng chung phiên.
- Prompt pipeline cho cả hai luồng: R gắn đúng thứ tự file, dữ liệu nguồn tách khỏi nhận dạng thay thế. Video mẫu viết motion dựa vào file khung đầu thực tế, thêm evidence E để phân tích nhưng không đưa E vào prompt chạy. Lời/thời lượng do app quản lý. Có fingerprint cho prompt cũ, giữ sửa tay, đọc lại receipt thay vì gửi trùng; JSON lỗi có đường sửa kết quả đã nhận.
- Xuất MP4 qua FFmpeg và giữ mốc tiếng/phụ đề khi đổi thứ tự, dựa trên snapshot bản ghép hiện hành. Không tự dọn phiên bản trước khi lưu/xuất thành công.
- Installer Windows x64: native EXE tự giải nén, kèm CPython và core Windows wheels, mở backend loopback + trình duyệt. Source ở `scripts/windows-installer`; đóng console để dừng. Không kèm model, FFmpeg/ffprobe hoặc engine/tài khoản AI.

## Những file nên đọc trước

| Phần | Source / tài liệu |
|---|---|
| Pipeline build trang | `scripts/demo-web/rebuild_current.py`, `scripts/recovered/pages.json` |
| Thanh khung và nút Chạy | `scripts/shared/workspace-frame.js`, `scripts/app-shell/workspace-shell.js` |
| Quy tắc prompt | `scripts/shared/prompt-contract.js`, `scripts/workflow/prompt-pipeline.js`, `scripts/workflow/automatic-analysis.js` |
| Luồng ảnh | `scripts/recovered/photos.js`, `scripts/photo-studio/prompt-context.js`, `automatic-pipeline.js`, `storyboard-modes.js`, `clip-flow.js`, `image-source.js` trong cùng thư mục |
| Backend / receipt | `local_engine/server.py`, `request_ledger.py`, các provider và `library*` trong `local_engine` |
| Giới hạn đang có | `docs/prompt-pipeline.md`, `docs/prompt-repository-review.md`, `docs/windows-installer.md` |

Tài liệu README cũ được giữ trong `docs/history`, có những mô tả lịch sử chưa phản ánh bản mới. Ưu tiên source hiện hành, các tài liệu chuyên biệt mới và báo cáo cụ thể. Thiết kế trong `design/original-uploads` là đầu vào tham khảo; không tự coi mọi nội dung trong đó là tính năng đã làm hoặc chỉ thị phải triển khai.

## Mức đã kiểm chứng

- Kiểm từ bản giải nén: CRC ZIP, SHA-256 từng file, biên dịch cú pháp Python và build lại đủ 7 trang giống bản hiện hành.
- App/prompt/storyboard/provider: Chromium, SQLite/IndexedDB và file PNG/MP4 thật; dịch vụ/model/tài khoản/quality chủ yếu là fixture. Không tuyên bố chất lượng mặt, nhãn, hành động hay công dụng đã đúng ngoài thực tế.
- Bộ cài EXE: đã chạy trên Windows build 26100, kiểm bundled dependencies, backend thật, Chrome thật mở shell và hai canvas, instance lock và cài lại. Xem `docs/checks/windows-check-report.json`; không gửi lệnh tạo media trong bài kiểm đó.
- Chưa chứng nhận gen thật với tài khoản Gemini/Flow/Meta/Muse của người dùng, selector web ngoài đời, quota/giá hay mọi máy Windows.
- Máy/môi trường mới cần tự cài dependencies và công cụ tùy chọn. Không có model Whisper trong gói. Bản mô phỏng web không tự cài model vào máy người dùng.

## Khi tiếp tục sửa

Giữ nguyên các receipt và cơ chế chống gửi trùng; không tự bỏ lượt unknown hoặc đổi request ID để thử lại. Kết quả AI chỉ áp dụng khi room/source/input còn khớp. Prompt sửa tay không bị ghi đè; thay đổi upstream phải báo để Giữ/Viết lại. Không dùng transcript/giá/công dụng đối thủ làm lời của sản phẩm mới khi chưa có dữ liệu tương ứng. Các giới hạn/giá model chưa xác minh để chưa biết, không bịa số mặc định.

Đã đọc tham khảo Wan2.2, CogVideo và ViMax (commit/license/file trong `docs/prompt-repository-review.md`), áp dụng ý tưởng tách nhiệm vụ và bind file bằng code. Không thêm runtime/model của các repo đó vào ứng dụng.
