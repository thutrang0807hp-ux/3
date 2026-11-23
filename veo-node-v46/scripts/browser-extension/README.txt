GEMINI BROWSER · SceneForge 1.7.0

Cài bản app .161 trở lên. Trong Chrome/Edge mở Gemini đã đăng nhập, giữ tab này mở. Trong SceneForge: Cài đặt → Tài khoản → Gemini Chat → Kết nối bằng mã tiện ích → Tạo mã. Chọn tab Gemini, bấm tiện ích, nhập mã và đúng cổng app rồi Kết nối. App sẽ chọn kết nối trình duyệt mới.

Prompt, ảnh nguồn và ảnh tham khảo do node SceneForge chuẩn bị. Tiện ích chỉ gửi trên tab Gemini và lấy kết quả về. Không chuyển cookie Gemini hoặc dùng Python SDK cho kết nối mới. Mỗi lượt mở tab riêng để không nhầm kết quả giữa các cảnh. Nếu chưa nhận được ảnh, giữ tab lỗi để nhận lại; không tự gửi tạo thêm. Không đổi nick trong tab đã kết nối; đổi nick thì kết nối lại rõ ràng.

Quyền googleusercontent dùng tải ảnh; unlimitedStorage chỉ giữ tạm kết quả đang chuyển nếu kết nối app bị ngắt. Sau khi app nhận xong, tiện ích bỏ dữ liệu ảnh tạm. Ảnh nguồn nhỏ vẫn chỉ có độ phân giải nguồn. Cơ chế tham khảo từ test-gemoni-chat 0.2.2 của cùng chủ repo; không thay node hoặc luồng prompt SceneForge.

Hướng dẫn Flow cũ (giữ tương thích):

SceneForge — Kết nối phiên trình duyệt

Cài một lần trên Chrome hoặc Edge đang đăng nhập tài khoản của bạn:
1. Chrome: mở chrome://extensions — Edge: mở edge://extensions.
2. Bật Chế độ nhà phát triển (Developer mode).
3. Bấm Tải tiện ích đã giải nén (Load unpacked).
4. Chọn thư mục có manifest.json này. Nếu tải ZIP thì giải nén trước.
5. Có thể ghim tiện ích SceneForge vào thanh công cụ.

Kết nối:
1. Đăng nhập Gemini/Flow trong trình duyệt bình thường này.
2. Trong SceneForge → Tài khoản → nguồn muốn nối → Kết nối → Tạo mã.
3. Bấm tiện ích SceneForge, nhập mã 8 số. Giữ cổng 8840 hoặc nhập cổng app ghi cạnh mã.
4. Bấm Kết nối, quay lại app xem kết quả kiểm tra phiên.

Không cần proxy. Không nhập mật khẩu vào SceneForge. Tiện ích chỉ đọc cookie
của nguồn được ghép đôi khi bạn bấm nút, và chỉ gửi về 127.0.0.1 trên máy.
Không có mã chạy nền, content script, máy chủ bên ngoài hoặc chức năng tự đọc
phiên định kỳ. Không lưu cookie vào storage của tiện ích.

App phải đang mở. Mã dùng một lần, hết hạn sau 3 phút. Nếu đóng app hoặc mã
đã dùng/hết hạn, kiểm tra mục Tài khoản trong app rồi tạo mã khác khi cần.

Nhận/kiểm tra phiên không chứng minh được quota hay tạo ảnh/video thành công.
Cần thử tạo thật bằng tài khoản của bạn sau khi kết nối. Tiện ích này chưa phát
hành trên cửa hàng Chrome; việc nạp thư mục lần đầu cần bạn thao tác.

Phiên bản 1.1.0: một mã có thể nối cả Gemini Chat và Flow, hoặc chỉ một dịch vụ.
Sau khi cập nhật app, mở trang quản lý tiện ích và bấm tải lại ⟳ một lần.
Không cần gỡ tiện ích. Nếu có nhiều nick Google, kiểm tra nick đang mở riêng
trên Gemini và Flow; cùng một trình duyệt không tự chứng minh cùng email.

Phiên bản 1.2.0 bổ sung quyền đọc phiên flow.google.com hiện tại (OSID),
khắc phục bản cũ chỉ đọc Google/Labs. Sau cập nhật, tải lại tiện ích và
chấp nhận quyền Flow nếu trình duyệt hỏi. Đăng nhập tại https://flow.google.com/
trong cùng trình duyệt rồi tạo mã mới trong app. Không gửi cookie qua chat.

Phiên bản 1.3.0: lấy đủ cookie theo đường dẫn của Flow (kể cả /_/),
giữ User-Agent trình duyệt và authuser nếu URL Flow có chỉ định.
Không đổi quyền truy cập, không chạy nền, không tự gửi tạo nội dung.
Sau cập nhật app: tải lại tiện ích. Nếu dùng thư mục ZIP riêng, thay bằng ZIP mới.

1.4.0 có phép kiểm chỉ đọc ngay trong tab Flow, cần quyền scripting trên miền Flow.
Mở Flow rồi bấm tiện ích → Kiểm tra Flow → Kiểm tra trong tab Flow → Chép báo cáo.
Không cần tạo mã hoặc kết nối lại để kiểm tra. Không gửi tạo ảnh/video.
Báo cáo không chứa giá trị cookie, token, HTML, email hoặc nội dung phản hồi.
Đây là công cụ chẩn đoán, chưa phải sửa lỗi 401 của engine.

1.5.0: Flow chạy qua tab Flow đã nối bằng worker nền; cần storage/alarms để duy trì kết nối trong lần mở trình duyệt.
Không lưu cookie trong tiện ích. Khóa kết nối chỉ ở storage.session, tự hết khi đóng trình duyệt.
Giữ tab và trình duyệt mở. Đóng trình duyệt hoặc đổi nick thì nối lại bằng mã mới.
Giữ nguyên phiên Gemini; hai nguồn vẫn nối chung hoặc riêng.
