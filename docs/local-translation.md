# Một model dịch đa ngôn ngữ M2M100

Theo chốt triển khai: bỏ đường Argos Trung → Anh → Việt, dùng **facebook/m2m100_418M** với CTranslate2 CPU int8. Một bộ model dịch trực tiếp các ngôn ngữ hỗ trợ về tiếng Việt; không tải từng cặp. Whisper vẫn là bộ chép lời, không thay bằng M2M100. Gemini Chat giữ làm lựa chọn thủ công, không tự gửi hoặc làm fallback.

## Đã triển khai / chưa hoàn tất

- Worker, endpoint, bộ cài, danh sách 100 mã ngôn ngữ (có Trung `zh`, Ý `it`, Việt `vi`) đã chuyển sang M2M100. Không còn tải/chạy gói Argos trong đường tích hợp hiện tại. Dữ liệu/bản dịch đã có giữ nguyên.
- Runtime CTranslate2 4.8.x và SentencePiece đã có ở môi trường CPU phát triển. Mỗi lượt dùng worker riêng, CPU int8, hai thread; dùng chung ngân sách tài nguyên với Whisper và xuất video.
- Nguồn chính thức Hugging Face và Meta đều bị proxy trả 403, kể cả kiểm tra quyền mở rộng. **Chưa có trọng số M2M100, chưa tạo được bản dịch thật hoặc đo RAM/tốc độ.** Không báo cài xong hoặc chứng nhận chất lượng. Các bài kiểm hiện dùng fixture có ghi nhãn.
- Không cài Torch/Transformers lớn trong môi trường phát triển vì nguồn model đang bị chặn. Chỉ đường chuẩn bị/chuyển đổi dùng các thư viện này trong môi trường tách biệt; runtime dịch không cần chúng.

## Dung lượng

Ước lượng trước khi chạy: bộ int8 khoảng 450–800 MB; RAM dịch khoảng 1–2 GB hoặc hơn tùy câu/bộ chạy. Chưa đo thực tế. **Bộ gốc tải để chuyển đổi lớn hơn (cỡ 1,9 GB)**; cùng cache và thư viện chuẩn bị có thể chiếm vài GB. Không được hiểu “model int8 vài trăm MB” là toàn bộ lượt cài chỉ tải chừng đó. Chuyển đổi cần thêm RAM; nếu máy yếu nên chuẩn bị bộ CT2 int8 trên máy khác rồi nhập.

## Cài trên máy

Python 3.10–3.12. Chạy `local_engine/install-translation.bat` rồi khởi động lại SceneForge.

- Nếu đã có bộ CT2 int8 tại `models/m2m100-418m-int8` cạnh `local_engine`, bộ cài nhập offline, không tải lại hoặc cần Torch.
- Nếu chưa có, kiểm tra truy cập nguồn trước. Truy cập được mới tạo `.venv-translation-setup`, cài Torch CPU và Transformers, tải bộ gốc chính thức rồi chuyển CT2 int8. Không tải CUDA, không gọi API trả phí.
- Nếu nguồn bị chặn thì dừng, không báo hoàn tất hoặc đổi ngầm sang Gemini.

Thư mục dùng lâu dài: `SCENEFORGE_LOCAL_DATA/models/translation/m2m100-418m-int8`, mặc định dưới thư mục dữ liệu SceneForge. Bộ nhập giữ model khác đã có, không ghi đè. Tệp model Argos cũ nếu người dùng từng tự cài không bị xóa âm thầm; code mới không đọc chúng.

Nhập bộ CT2 đã có:

```
python -m local_engine.prepare_translation --from-directory models/m2m100-418m-int8
```

Cần `model.bin`, `config.json`, `shared_vocabulary.json`, `sentencepiece.bpe.model`. Bộ cài chỉ ghi ready sau khi nạp và dịch thử câu Trung, câu Ý có đầu ra khác nguồn; đây là kiểm cơ chế, chưa chứng nhận chất lượng. Marker ghi hash/kích thước. Không dùng cờ trust_remote_code.

Nguồn bộ gốc: https://huggingface.co/facebook/m2m100_418M/tree/main . Không yêu cầu người dùng chia/gửi hàng chục phần RAR nếu có thể chạy bộ cài trên máy truy cập được nguồn.

## Dùng trong workflow

Kịch bản → **Dịch Việt · local**. Mặc định lấy ngôn ngữ Whisper đã nhận; thiếu thì yêu cầu chọn, không tự đoán Trung. Có danh sách ngôn ngữ để sửa khi nhận sai; mã không hỗ trợ được báo lỗi. Bộ này không tự nhận ngôn ngữ từ bản chữ, không hứa hỗ trợ mọi tiếng.

Mặc định dịch câu chưa có bản dịch; có lựa chọn dịch lại. Xem rồi Áp dụng vào cột Dịch sát. Giữ lời gốc, ID, mốc câu, lời mới nhập tay, clip và timeline; nguồn thay đổi thì chặn áp dụng. Không tự viết quảng cáo hoặc xác minh công dụng.

Giới hạn 300 câu, 3.000 ký tự/câu, tổng 30.000 ký tự; worker tối đa 300 giây. Câu dài được chia thành các phần không quá 192 token, không cắt mất đuôi câu theo mặc định CT2. Giữ source language prefix / EOS và target `__vi__` theo tokenizer M2M100. Không log lời nguồn; dọn file tạm sau kết thúc. Dịch là thao tác hàng loạt có nút, chưa tự chạy sau mọi lượt chép lời.

## Kiểm tra

- `python -m local_engine.check_local_translation`: 100 mã ngôn ngữ, tag Trung/Ý → Việt trực tiếp, giữ đủ token câu dài, unload engine, thiếu model không fallback, sai ID, dọn file, import/marker và không ghi đè. Model/tokenizer/transport fixture.
- `python scripts/workflow/check_local_translation.py`: chọn tiếng Ý, xem/áp dụng, giữ lời nhập tay/mốc và bản dịch cũ, chặn nguồn thay đổi; không gọi route trả phí. Phản hồi model fixture.
- `python scripts/workflow/check_chat_translation.py`: đường Chat tùy chọn còn hoạt động thủ công, không tự gửi.

Giữ thông tin thật về kiểm chứng: chưa chạy model M2M100 thật vì chưa tải được trọng số; giấy phép model card cụ thể và chất lượng cần đối chiếu khi nhận bộ nguồn. Tài liệu Fairseq đã xác minh hỗ trợ 100 ngôn ngữ; không dùng giấy phép mã runtime để suy diễn giấy phép của mọi bộ trọng số bên thứ ba.
