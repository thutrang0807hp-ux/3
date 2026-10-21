# Thiết kế lại Tài khoản theo ảnh tham chiếu

Thay bảng cũ bằng dashboard nền tối/nhấn chanh, mở rộng khoảng đọc và bố cục theo ảnh thứ hai. Giữ nguyên các mục khác của app.

- Trên: tiêu đề, tab Flow/Muse, động cơ, các nhãn số tài khoản theo trạng thái. Cookie sắp hết hạn được ghi riêng, không tự xem đó là phiên đã xác minh.
- Giữa: sơ đồ kết nối có đúng một đường sáng khi có một tài khoản được chọn; nhật ký dịch vụ đặt bên phải. Tài khoản quá 5 vẫn đầy đủ trong bảng, sơ đồ chỉ hiện nhóm đầu. Không chạy đường nét đứt chuyển động.
- Dưới: bảng đủ ưu tiên, tên, trạng thái, hạn phiên, credit, thành công/thất bại, lần dùng, ghi chú, công tắc bật và thao tác. Kéo tay nắm hoặc dùng mũi tên để đổi ưu tiên; menu ba chấm đổi tên/ghi chú/gỡ. Tắt tài khoản đang dùng bỏ chọn, không tự đổi sang tài khoản khác. Bật lại không biến tài khoản chưa kiểm chứng thành sẵn sàng.
- Biểu đồ 7/30 ngày chỉ cộng tác vụ hoàn tất có phí xác nhận và **cost_unit=credit**, chia theo ngày/sản phẩm. Tác vụ đang chạy/ước tính/tiền API không được cộng làm credit đã trừ. Khi chưa có số thì hiện chưa đọc, không vẽ số bịa. Không tuyên bố cập nhật động cơ hay đọc quota thật khi adapter chưa nối.
- Xóa nhật ký chỉ xóa dịch vụ đang xem, giữ nhật ký Gemini và dịch vụ khác; hộp xác nhận nói rõ ảnh hưởng đến biểu đồ.
- Demo `?demo=1&accounts=flow`: 5 tài khoản giả và biểu đồ có nhãn minh họa; thao tác lưu riêng trong IndexedDB của demo, không gửi account/API request. Tab Muse giữ tên muse.ai, không tự nhận là Meta. Chuyển/xoay vòng/kết nối thật không được giả là hoạt động.
- Bản làm việc: lấy tài khoản + nhật ký thật từ companion, không nạp dữ liệu minh họa. Kết nối/lưu phiên/dùng/gỡ dùng luồng cũ; rename/note/enable và order có endpoint kiểm tra dữ liệu mới. Thứ tự ghi giao dịch nguyên tử theo từng dịch vụ; không cho sửa credit/trạng thái qua metadata API.
- Mở Cài đặt → Tài khoản đi thẳng dashboard mới; modal khác dọn class riêng. Màn hình nhỏ xếp sơ đồ trên nhật ký, chỉ bảng ngang được cuộn, không tràn toàn màn hình.

## Kiểm tra

`python scripts/app-shell/check_accounts_dashboard.py`: Chromium thật, bố cục 2 cột, sơ đồ/nhật ký, 7/30 ngày, ưu tiên, bật/tắt/tên, hai tab, mobile, reset modal và không gọi API trong demo.

`python -m local_engine.check_account_settings`: metadata/order thật qua FastAPI và vault; credit/state không sửa giả, tắt không xoay, bật không xác minh, ưu tiên giữa dịch vụ giữ nguyên, xóa log theo dịch vụ, bảo vệ POST. Không gọi provider.

Chưa nối adapter Flow/Muse để đọc credit/quota, xác minh phiên, kiểm tra cập nhật hoặc thực thi xoay vòng. Các nút cần adapter vẫn được ghi/khóa đúng trạng thái. Không tạo phiên/account thật chỉ để thử giao diện.
