# SceneForge .171 — Universal Reference Image Edit V5.2

Cập nhật trên nền .170 (6794c13), chỉ thay prompt dựng sẵn và kiểm thử liên quan. Giữ node ảnh mới, upstream sender/decoder, backend, cách gắn reference, primary reference, kích thước đầu ra và ảnh kết quả. Không lấy code .144 cũ đè lên .170.

Ghép hai đoạn người dùng gửi: hoàn thiện duy nhất câu Do not enlarge the replacement product for advertising emphasis or label readability. rồi nối các khối tiếp theo, không lặp PHYSICAL_SCALE hoặc đoạn đầu. COLOR_MATERIAL_LOCK được giữ theo V5.2: hue/saturation/gradient/material, transparency/translucency/roughness/gloss; môi trường thay ánh sáng/white balance nhưng không áp độ bão hòa/độ bóng đồng loạt cho mọi sản phẩm. LIGHTING_MATCH bổ sung giữ màu nội tại; NEGATIVE_CONSTRAINTS bổ sung tránh bạc màu/quá màu/thay chất liệu không có căn cứ.

Phần nối tiếp bị cắt trong FINAL_VALIDATION sau hai dòng đầu và dấu gạch đầu dòng trống. Bản này giữ nguyên toàn bộ FINAL_VALIDATION của V5.1; không tự bịa phần còn thiếu. Đây không phải tuyên bố đã nhận đủ nguyên văn toàn bộ V5.2 của người dùng. Có thể thay riêng phần đó khi có đoạn hoàn chỉnh.

Nguồn mới scripts/prompts/universal_reference_image_edit_v5_2.md; module frame_universal_v52.js. Giữ slot HTML lịch sử frame-universal-v51 để không đụng các cầu nối. Giữ tài liệu/module V5.1 làm bản gốc. Prompt managed V5.1 nguyên bản được nhận diện để điền slot và dùng bản mới; prompt thực sự sửa tay giữ nguyên. Lượt ảnh đang có được owner hiện tại nhận kết quả, không tạo lượt thay thế do cập nhật template.

Điền sáu slot từ bindings/cảnh/thông số/continuity/output; giữ nhánh lựa chọn product/person/outfit/background và clothing-from-person. Không product thì các khóa product không ép thay người/trang phục. Không ghép lớp IMAGE EDIT CONTRACT v2/FRAME IDENTITY vào prompt đã dựng. Writer tùy chọn chỉ tối ưu SCENE_ACTION.

Kiểm thử Node: khối tĩnh đúng nguồn, đủ slot, một câu hoàn thiện thang kích thước, các vai trò/continuity/background, canonical V5.1 và manual prompt, FINAL_VALIDATION đúng fallback. Kiểm thử contract xác nhận sender/backend/ref packing không đổi. Kiểm thử Chromium sau khởi tạo workflow: một image POST V5.2, hai ảnh đúng bindings, một ảnh nhận về, không gọi text writer và không gửi trùng kết quả khớp. Kiểm tra cú pháp và nội dung nhúng gói. Chưa gọi Gemini thật/chạy trình cài Windows. Bộ test cũ check_frame_direct.py dùng selector node trước .164 nên không áp dụng cho giao diện hiện tại; dùng test chủ sở hữu mới. Race render khởi động sẵn có ở .170 nằm ngoài phạm vi prompt này.

Đóng app trước cập nhật. Tạo lượt mới hoặc xem prompt English để thấy header V5.2. Prompt sửa tay tùy chỉnh không tự bị ghi đè. Cộng dồn .62 trở lên.

SHA-256: 023fea742a1732dacc8f8d2cf86e1a2693eaaff89da0a1a4ff79b5a2d24872d5
