> Đây là bản đối chiếu ở lần triển khai Gói 5. Các bổ sung Gemini/MP4/cân âm/timeline sau đó nằm trong `aggregate-implementation.md`.

# Gói 5 — triển khai và đối chiếu

Đặc tả gốc: `design/package-5-spec/SceneForge_Goi5/DAC_TA_GOI_5.md`, hai ảnh trong cùng thư mục. Không thay ảnh gốc hay xóa các gói 1–4. Tổng 44 tệp thiết kế/đặc tả đã đối chiếu SHA-256 với ZIP được nhận.

## Đã triển khai

- Cài đặt bảy mục, menu trái, khung động cơ bên phải ở mục AI. Không đổi lại bố cục trang chủ đã đo theo ảnh Gói 4. Lựa chọn riêng được lưu; bản demo dùng database riêng.
- Gemini: chọn cách sử dụng miễn phí/trả phí; key chỉ lưu mã hóa trong companion. Kiểm tra key bằng yêu cầu thật đọc danh sách mô hình Google, kèm giờ và kết quả; kiểm tra này **không chứng nhận quota tạo nội dung**. Đổi key xóa kết quả kiểm tra cũ. Không nhúng/hiện lại key đã lưu.
- Đếm lượt gọi/429 từ nhật ký tháng UTC. Phí chưa xác minh giữ “Chưa đọc”; không coi việc chọn “miễn phí” trong app là bằng chứng key không bị tính phí.
- Chỉ tự thử lại khi Google xác nhận HTTP 429 và chế độ miễn phí; tối đa hai lần, mỗi lần ≤30 giây. 403, mất kết nối, kết quả không rõ hoặc key trả phí không tự gửi lại. Có nhật ký từng lần bị giới hạn.
- Trạng thái/version gói Python và FFmpeg thực tế, dung lượng trống ổ chứa companion, sao chép chẩn đoán có che trường nhạy cảm. Không hiển thị nút cập nhật/khởi động giả.
- Thư mục: dùng lại bộ chọn và cơ chế bản sao phòng đã có; quét file đệ quy theo thư mục để đo tổng và từng nhánh, không dùng quota trình duyệt làm dung lượng ổ đĩa. Dọn tất cả đi qua bảng xem trước và quy tắc bảo toàn timeline cũ. Khi giữ bản xử lý logo, bộ dọn giữ cả bản gốc phụ thuộc.
- VieNeu: giữ nguồn chạy máy; thử giọng qua route TTS thật khi có SDK. Tốc độ 0.8–1.3× áp dụng nghe thử bằng phát âm thanh, **chưa là tốc độ suy luận giọng mặc định**. Không tạo danh sách giọng/vùng miền giả.
- Xuất: mặc định 720/1080p, yêu cầu 30/60 fps, mặc định tự xử lý logo, tùy chọn SRT. Hộp Xuất vẫn sửa được; thay cài đặt không ghi đè lựa chọn xuất người dùng vừa chỉnh. SRT lấy từ phụ đề thật trên timeline, tải cạnh video, lưu cùng `7-xuat/` khi có thư mục/phòng. Số khung thực phụ thuộc nguồn và máy, bộ xuất vẫn MediaRecorder chạy thời gian thực.
- Chuông: ba mức Cần bạn/Xong việc/Thông tin; badge chỉ đếm Cần bạn chưa xem; gộp theo loại trong ba phút, giữ nút đến từng phòng; bộ lọc, đánh dấu đã xem, giữ 30 ngày. Tiếng báo chọn/nghe thử chỉ cho Cần bạn. Desktop Notification xin quyền khi bật; Cần bạn và xuất xong có thể báo khi trình duyệt còn chạy. Xuất xong nhắc nhãn nội dung AI TikTok.
- Màn chào năm bước, chọn thư mục bắt buộc để tiếp tục bước 1; các bước khác bỏ qua được; không chặn bản demo, không chặn các phòng đã có. Kiểm tra máy là trạng thái đo được, không giả tiến độ tải model. Có thể mở lại từ Cài đặt.
- Tab video mẫu theo bố cục gộp: node Ảnh khung chứa các cảnh, Video Veo chứa các cảnh, bốn tham chiếu gộp chung. Prompt đầy đủ, duyệt, nhập khung/clip, lỗi và phiên bản vẫn truy cập riêng từng cảnh. Kéo node, lưu vị trí, chọn sáng/minimap giữ hoạt động. Workflow từ ảnh và phiên bản storyboard cũ vẫn giữ riêng.
- Sang Dựng: lấy lời có mốc giây thành phụ đề, chọn bốn mẫu chữ dùng chung với Dựng. Khi đổi thứ tự cảnh, mốc phụ đề được ánh xạ lại theo cảnh. Có nhập nhạc như trước. Tiếng từ Flow vẫn mặc định; voice-over riêng là tùy chọn.
- Xử lý logo tự động trên **bản sao clip nhập mới**, tuần tự, trước handoff; giữ nguyên nguồn và mọi phiên bản. Khi nhận diện không chắc hoặc lỗi thì dùng nguồn, chỉ hiện cảnh báo vàng/Thử lại. Không còn nút xử lý logo thường trực. Bản xử lý mới chỉ được thêm vào Kho của bản dựng cũ, không ghi đè timeline đã sửa.

## Các phần chưa hoàn tất — không giả là đã chạy

- Worker tạo video, đọc credit/quota, cài/cập nhật/tự khởi động flow2api/muse2api; kiểm chứng thực trên Windows. Repo muse2api được chỉ định dùng muse.ai, chưa xác minh là Meta AI.
- Tải mô hình VieNeu kèm %, liệt kê giọng/vùng miền từ SDK, chọn giọng mặc định nữ Nam; V4 và voice clone.
- Chuyển thư mục sang ổ khác có kiểm chứng đầy đủ/trước xóa nguồn; kiểm tra trống đúng ổ dự án khi dùng File System Access trong trình duyệt.
- Tự cân âm lượng khi xuất, tự duck nhạc theo lời và thư mục xuất chung; chưa hiện công tắc giả cho các thao tác này.
- Thông báo khi trình duyệt đã đóng; engine lifecycle/background desktop service.
- OCR, chép lời và phân tích ngữ nghĩa video tự động đầy đủ trong workflow node vẫn chưa nối; dò cảnh cục bộ và nhập kết quả/SRT vẫn hoạt động. Không gọi đó là phân tích AI hoàn tất.
- Công cụ logo đang dùng bản JS đã kiểm tra/giữ giấy phép từ GargantuaX/gemini-watermark-remover. **Chưa tích hợp gwmr** mới chỉ vì được gợi ý; chưa kiểm chứng clip thật tải Flow 720/1080p, mọi kiểu chữ/logo Veo hoặc thời gian clip 8 giây. Đã kiểm tra video kiểm soát 720×1280, 2 giây, logo alpha tương thích: sai khác vùng logo MAE 17.26 → 1.68; AAC giữ nguyên từng gói. Kết quả này không bảo đảm logo khác xử lý được. Không loại SynthID.

## Kiểm tra

- `scripts/app-shell/check_package5.py`: cài đặt/lưu lại, key demo bị khóa, thông báo/phân loại/lọc/đã xem, node gộp/giữ tham chiếu/không đè/chi tiết/minimap.
- `local_engine/check_package5.py` (chạy `python -m local_engine.check_package5`): cài đặt hợp lệ, đo health/disk, che chẩn đoán, chi phí chưa biết, 429 có giới hạn và không gửi lại lỗi mơ hồ. Google được giả lập, không gọi key thật.
- `scripts/workflow/check_package5.py`: xử lý logo bằng engine thật trên video kiểm soát, audio packets không đổi, chọn bản sao, nguồn được giữ, thất bại hiện vàng, phụ đề đổi thứ tự đúng và tải lại còn phiên bản.
- `scripts/native-preview/check_package5.py`: xuất video thật ngắn và SRT, kiểm tra độ phân giải, mặc định fps và giữ chỉnh tay.
- Hồi quy: mốc giao diện trang chủ, hai workflow/legacy, âm thanh gain xuất thật, dọn phòng và bảo toàn clip cũ.
