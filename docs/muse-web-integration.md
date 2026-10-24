# Muse trong SceneForge

SceneForge có adapter tạo **clip video Muse**, tham khảo giao thức SDK tìm được trong tool người dùng cung cấp. Giao diện và backend nối do SceneForge viết riêng. Không sao chép ứng dụng hoặc bộ bridge của tool.

## Đã làm

- Cài SDK `minhquan130599/MuseAI-API` bản `bf964f7c022f11a3574e2e17a8ec57e7c9b0e596` vào môi trường riêng trên máy phát triển: `/workspace/engines/muse-web`. Import và `pip check` thành công. Không có model AI local.
- Adapter `/local-api/muse/*`, tiến trình SDK riêng, phiên lưu trong vault AES-GCM. Cookie/OTP không nằm trong dòng lệnh, nhật ký hay phản hồi trạng thái. SDK chỉ dùng tệp phiên tạm trong lúc thao tác, dọn khi thao tác kết thúc bình thường; không phải mã hóa trong RAM. Nếu máy/tiến trình bị cưỡng bức tắt, tệp tạm có thể còn lại trong thư mục `muse-work-*` của dữ liệu SceneForge.
- Tài khoản → Muse → Kết nối: email/OTP hoặc nhập JSON cookie của `muse.ai`. Kiểm tra phiên không tự tạo video hoặc bịa số dư.
- Từ ảnh & ý tưởng → **Video: Muse → Kết nối Muse → Tạo clip còn thiếu**. Rà prompt/ảnh trước khi gửi; **Kiểm tra kết quả** nhận clip vào đúng nhịp và giữ các phiên bản cũ. Chuyển sang Flow vẫn dùng adapter Flow cũ.
- Tối đa 3 tác vụ dịch vụ cùng lúc, **mỗi tài khoản một tác vụ**. Có thể chọn một tài khoản hoặc tự chia việc giữa các tài khoản đã kiểm tra. Chỉ dự phòng được chuyển khi bị từ chối rõ ràng trước khi nhận việc; không gửi lại sau lỗi mạng/kết quả chưa rõ.
- **Lựa chọn dùng chung:** bấm dùng tài khoản A trong Cài đặt thì thanh tạo clip dùng A. Đổi lựa chọn trên thanh cũng cập nhật Cài đặt, áp dụng cho mọi phòng; lựa chọn cũ lưu riêng trong phòng không còn được dùng để gửi việc. Tài khoản đầu tiên kiểm tra thành công được chọn mặc định; đăng nhập thêm B không thay A.
- Trong Cài đặt → Tài khoản → Muse, chọn **Dùng riêng / Dự phòng theo thứ tự / Chia việc** cùng chế độ ở thanh tạo clip. Tắt thì chỉ tài khoản đã chọn nhận việc; bật thì chia các việc mới giữa tài khoản đủ điều kiện. Đây không phải chuyển tài khoản để gửi lại một lượt đã lỗi.
- Bảng rà hiển thị tài khoản/chế độ thực tế. Đổi lựa chọn, tắt hoặc xóa tài khoản trong khi bảng rà đang mở làm lượt rà cũ hết hiệu lực; backend từ chối trước khi nhận việc. Việc đã nhận giữ tài khoản đã giao, đổi lựa chọn chỉ áp dụng việc mới. Tài khoản bị tắt trước khi việc bắt đầu thì việc dừng, không âm thầm chuyển sang tài khoản khác.
- Mã yêu cầu bền vững ngăn gửi trùng. Sau khi đứt kết nối/khởi động lại, lượt chưa rõ kết quả không tự phát lại. Cần kiểm tra lịch sử Muse trước khi chủ động tạo lượt mới.
- Chỉ nhận kết quả gắn được với một hội thoại mới; bỏ fallback upstream chọn hội thoại gần nhất. Phải ffprobe đọc được video trước khi ghi hoàn tất.

## Cài trên máy người dùng

1. Mở bản cục bộ SceneForge. Cần Python 3.11+ và Git trong PATH.
2. Chạy `local_engine/install-muse-web.bat`. Trình cài tải SDK/thư viện, không đăng nhập, gửi OTP hoặc tạo nội dung.
3. Quay lại SceneForge → Video: Muse → Kết nối Muse. Đăng nhập bằng tài khoản của bạn.
4. Rà một cảnh, gửi, rồi kiểm tra kết quả trước khi chạy nhiều cảnh.

SDK mặc định ở thư mục dữ liệu SceneForge `engines/muse-web`; có thể đặt `SCENEFORGE_MUSE_WEB_DIRECTORY`. Dữ liệu phiên được lưu cùng vault hiện có. Xóa tài khoản sẽ xóa phiên tương ứng; phải đợi việc đang chạy kết thúc.

## Giới hạn xác minh

**Chưa thử tài khoản thật, gửi OTP thật hoặc tạo video thật.** Đã kiểm tra adapter với dữ liệu giả lập và video FFmpeg thật trên Linux, cùng các kiểu dữ liệu/parser của SDK đã cài. Không suy kết quả đó thành chứng nhận dịch vụ hiện hoạt động hoặc Windows đã được thử.

Nguồn trong code là `https://muse.ai`, gateway WebSocket `hatch.metaaivm.com`. Chưa chứng minh tài khoản này tương đương tài khoản `meta.ai`. Đây là giao thức web không chính thức, phụ thuộc thay đổi dịch vụ và hạn mức tài khoản. Không phải tạo không giới hạn.

Ảnh/storyboard tự động và chat viết prompt Muse **chưa nối**; các bước này vẫn chép yêu cầu/nhập kết quả. Luồng đã nối ở đây là tạo clip video từ prompt và ảnh.

SDK chưa có LICENSE rõ ràng trong snapshot kiểm tra. Gói SceneForge chỉ chứa adapter tự viết và trình cài trỏ về repo, không kèm nguồn/wheel SDK hoặc code của tool được gửi. Cần làm rõ quyền trước khi phân phối lại SDK.

SDK đọc dữ liệu video RPC vào bộ nhớ; không phải tải streaming hoàn toàn, nên clip lớn có thể tốn RAM. Adapter giới hạn ảnh đầu vào 8 ảnh/24 MB và chỉ chấp nhận tệp video tối đa 500 MB sau khi tải. Chưa chứng nhận xử lý video lớn hoặc tải bị ngắt có thể tiếp tục mà không tạo lại.

## Kiểm thử

- `python -m local_engine.check_muse_provider`: giả lập OTP/cookie, mã hóa, API JSON, song song nhiều tài khoản, ngăn gửi trùng, kiểm tra video thật bằng ffprobe, phục hồi sau ngắt và không lọt bí mật vào log.
- `python -m local_engine.check_muse_selection`: chọn tài khoản/bật chia việc qua route Cài đặt tác động trực tiếp tới bộ gửi; từ chối lựa chọn cũ trước khi claim; không đổi tài khoản của việc đã nhận; giữ lựa chọn sau mở lại và không dùng tài khoản khác khi tài khoản đã chọn bị tắt. Dịch vụ Muse được giả lập.
- Python của venv Muse chạy `-m local_engine.check_muse_worker`: kiểu dữ liệu/parser SDK thật, fake transport, phiên OTP và chặn nhầm hội thoại/URL.
- Trình duyệt Chromium: chọn Muse, bảng OTP, rà gửi, nhận video thử vào đúng nhịp và không nhập trùng khi kiểm tra lại. Tài khoản/kết quả dịch vụ được giả lập.

## Cập nhật tài khoản dự phòng

Xem [multi-account-dispatch.md](multi-account-dispatch.md). Flow có wrapper ghim tài khoản, cần launcher mới. Muse chỉ chuyển khi từ chối có cấu trúc, không suy quota từ mọi lỗi 429.
