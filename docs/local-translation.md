# Dịch local Trung → Việt: tùy chọn, chưa kiểm chứng model thật

Hướng dùng trước hiện là Gemini Chat qua sao chép/dán; xem `chat-translation.md`. Không cài M2M100/NLLB trong lượt cập nhật này.

Model chọn: hai gói Argos Translate `translate-zh_en-1_9` và `translate-en_vi-1_9`, chạy trực tiếp bằng CTranslate2 CPU int8 và SentencePiece. Kho index chính thức đã đọc không có gói trực tiếp zh → vi, nên dùng zh → en → vi. Đây là dịch máy chuyên dụng, không phải LLM/Ollama. Không gọi API trả phí, không dùng tài khoản AI.

## Tình trạng thực tế

Đã cài runtime SentencePiece và có CTranslate2 trong môi trường CPU phát triển; đã nối endpoint, worker, bộ cài và nút trong bảng Kịch bản. Hai gói model CHƯA tải được: host argos-net.com trả proxy 403, kể cả lượt kiểm tra quyền mở rộng. Không có bằng chứng dịch thật hoặc đo RAM/thời gian; không báo model sẵn sàng. Kiểm thử hiện tại dùng fixture để xác nhận đường dữ liệu và bảo toàn bản lời.

Ước lượng lựa chọn: model mức vài trăm MB và RAM khoảng 1–2 GB khi chạy; chưa có số đo thực tế. Chỉ nạp một chặng tại một thời điểm, hai CPU thread; thoát tiến trình khi xong. Bản dịch qua tiếng Anh có thể sai/mất sắc thái; lỗi nhận dạng Whisper có thể truyền sang dịch. Không quảng cáo tương đương Gemini hoặc dịch chính xác tuyệt đối.

## Cài

`local_engine/install-translation.bat` cài runtime và chủ động tải hai gói khi chạy. Dịch trong workflow không tải model. Nếu tải riêng, đặt hai file dưới thư mục `models` cạnh `local_engine`:

- https://argos-net.com/v1/translate-zh_en-1_9.argosmodel
- https://argos-net.com/v1/translate-en_vi-1_9.argosmodel

Hoặc chạy CLI:

```
python -m local_engine.prepare_translation --zh-en /path/translate-zh_en-1_9.argosmodel --en-vi /path/translate-en_vi-1_9.argosmodel
```

Thư mục đích là `SCENEFORGE_LOCAL_DATA/models/translation` (mặc định thư mục dữ liệu SceneForge). Bộ nhập kiểm cặp ngôn ngữ, giới hạn giải nén, đường dẫn, chỉ lấy model/tokenizer/metadata, không chạy mã trong gói. Chỉ ghi model sau khi nạp và dịch thử có kết quả. Không ghi đè thư mục model có sẵn; gói tải bị lỗi không được báo hoàn tất.

## Sử dụng

Sau khi Whisper chép lời, mở Kịch bản → Dịch Việt · trên máy. Chọn tiếng Trung/Anh, mặc định bỏ qua câu đã có bản dịch. Xem kết quả rồi áp dụng vào cột Dịch sát. Không tự thay lời mới gửi Flow, giữ nguyên lời gốc, ID, mốc câu, clip và timeline. Nguồn thay đổi trong lúc dịch thì chặn áp dụng. Muốn dùng bản dịch làm lời đọc, sửa/chọn lời mới sau khi rà. Đây là nút dịch hàng loạt, chưa tự động dịch sau mỗi lượt phân tích.

Giới hạn 300 câu, 3.000 ký tự/câu, tổng 30.000 ký tự; xử lý worker riêng tối đa 300 giây, không log lời nguồn; dùng ngân sách CPU chung để không chạy cùng công việc nặng khác. Câu dài chia thành các đoạn không quá 192 token để không lặng lẽ cắt bỏ phần sau. Kết quả sai ID hoặc rỗng thì không áp dụng. Không có model/lỗi thì trả lỗi, không chuyển ngầm sang Gemini/OpenAI.

## Kiểm thử

- `python -m local_engine.check_local_translation`: thiếu model, dữ liệu đầu vào, hợp đồng kết quả worker, dọn file tạm, ZIP có đường dẫn không an toàn. Model/transport giả lập.
- `python scripts/workflow/check_local_translation.py`: giao diện xem trước/áp dụng, giữ lời mới nhập tay và mốc, bỏ qua bản dịch cũ, chặn nguồn đã đổi, không gọi route AI trả phí. Model phản hồi giả lập.

Chưa kiểm chất lượng Trung/Việt thực tế hoặc gói tải thật vì thiếu model. Gói app có mã/bộ cài, không chứa hai model dịch này.
