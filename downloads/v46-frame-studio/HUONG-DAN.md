# Node Ảnh khung dựng lại — app .164 + tiện ích1.8.0

Đóng app, chạy cập nhật .164 rồi mở lại. Giải nén ZIP tiện ích mới đè vào thư mục cũ → chrome://extensions hoặc edge://extensions → Tải lại ⟳. Không đổi phần kết nối tài khoản; tiện ích tiếp tục tự kết nối như trước.

Node Ảnh khung mới: chọn cảnh → xem prompt hiện tại hoặc sửa/lưu nếu cần → Tạo ảnh. Ảnh nguồn và tham khảo được lấy theo cảnh. Kết quả hiện bên cạnh ảnh nguồn, được lưu vào cảnh và chưa tự duyệt. Có thể xem các bản ảnh hoặc bấm Duyệt ảnh theo quy trình kiểm hiện có. Tạo ảnh còn thiếu chạy lần lượt, một cảnh mỗi lượt. AI tối ưu prompt vẫn tùy chọn.

Khung prompt giữ nguyên: vai trò ảnh, giữ người/đồ/sản phẩm, chữ nhãn, ánh sáng, chất lượng và khung chuẩn dùng chung. Không dùng bước viết lại prompt của repo lúc tạo ảnh.

Luồng mới có một chủ điều khiển. Các lượt node cũ vẫn nằm trong lịch sử; chúng không tự chặn hoặc nhập đè kết quả node mới. Nếu cảnh có lượt cũ chưa rõ, app hỏi trước khi tạo lượt mới vì có thể dùng thêm hạn mức. Hủy xác nhận giữ nguyên lượt cũ. Không tự gửi lại prompt sau khi dừng/chưa rõ kết quả. Bấm Nhận ảnh của lượt này để đọc lại lượt mới đã gửi.

Nguồn gửi/đọc: test-gemoni-chat0.2.2 của bạn. Hàm generateInGemini được giữ nguyên, chỉ bỏ export để nạp trong tiện ích; lớp ghép thêm chỉ đính kèm ảnh trước khi gọi và nhận kết quả vào cảnh.

Đã kiểm thử bằng backend/SQLite ledger/node thật, với trang Gemini và dây tiện ích mô phỏng. Kiểm tra prompt gửi đi giữ nguyên, hai ảnh đính kèm, một lần gửi, nhập đúng cảnh, không tự duyệt, chặn bấm trùng và giữ lịch sử cũ. Chưa thử tài khoản Google hoặc bộ cập nhật Windows thật.
