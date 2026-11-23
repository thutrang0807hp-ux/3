SCENEFORGE 1.8.0 — GEMINI TỰ KẾT NỐI

1. Cập nhật app .164.
2. Cài tiện ích: giải nén, Chrome/Edge → chrome://extensions hoặc edge://extensions → Chế độ nhà phát triển → Tải tiện ích đã giải nén. Nếu đã cài SceneForge, thay file trong thư mục cũ rồi bấm Tải lại ⟳.
3. Mở SceneForge và Chrome/Edge đã đăng nhập Gemini. Tiện ích tự tìm app và nối Gemini. Không tạo mã, không nhập mã, không xuất cookie sang SDK. Nếu chưa đăng nhập, vào gemini.google.com/app đăng nhập một lần.

Tài khoản trình duyệt tự xuất hiện trong app. Node, prompt, ảnh tham khảo và bước duyệt giữ nguyên. Giữ trình duyệt mở trong lúc tạo. Nếu app dùng cổng khác 8840, mở địa chỉ app đó một lần trong Chrome/Edge để tiện ích tự nhận cổng, vẫn không dùng mã. Chrome có thể đánh thức tiện ích sau tối đa khoảng 30 giây khi đã tạm ngưng nền.

Flow: luồng Flow hiện có được giữ. Nếu cần kết nối Flow bằng mã, phần đó nằm trong mục Flow nâng cao của popup. Gemini không dùng mục này.

Googleusercontent dùng nhận ảnh trong trình duyệt. Quyền lưu trữ dùng giữ kết quả đang gửi nếu mất kết nối; ảnh tạm được bỏ sau khi app nhận. Không đóng gói tài khoản hay model.

Ảnh đã tạo nhưng chưa nhận về: giữ tab của lượt đó mở và dùng Nhận/Tải lại ảnh trong cảnh. Bản 1.7.2 đọc lại khi Gemini thay phần tử phản hồi hoặc ảnh chỉ tải lúc được cuộn vào khung nhìn. Nhận lại không gửi prompt mới.

NODE ẢNH KHUNG MỚI .164
Node mới giữ khung prompt và ảnh tham khảo hiện có. Gửi/đọc ảnh dùng hàm generateInGemini của test-gemoni-chat0.2.2, không bật bước viết lại prompt của repo. Phần thêm chỉ đính kèm ảnh do node chuẩn bị. Kết nối tài khoản tự động giữ nguyên. Lượt node cũ còn trong lịch sử; chỉ tạo lượt mới khi bạn bấm và xác nhận nếu có lượt cũ chưa rõ.
