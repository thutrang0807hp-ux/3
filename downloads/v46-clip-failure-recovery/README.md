# SceneForge v46.68 — phân biệt lỗi tạo và lỗi tải, giữ nút xử lý lỗi

Đóng app, chạy `SceneForge-Update-20261104-v46.68-Clip-Failure-Recovery.exe` trên .67, mở lại. Khoảng 4 MB. Giữ Data/tài khoản/lịch sử. Đây là updater, không phải bộ cài đầy đủ.

Báo cáo người dùng có generation_status=MEDIA_GENERATION_STATUS_FAILED, succeeded=false, local_path=null (CLI exit 1), sau đó kiểm tra cũ lại chạy data download và báo exit 7/no signed media URL. ID media không chứng minh video đã hoàn tất. Báo cáo không có failure_reasons chi tiết; không suy ra nguyên nhân Flow thất bại hoặc khẳng định video tạo thành công.

- Chỉ phân loại thất bại chắc chắn khi JSON kết quả video của CLI có succeeded=false + đúng trạng thái FAILED + ID khớp provider_task association_confirmed + đúng project chuẩn. Lượt mới đi nhánh FlowGenerationFailed có sẵn; không cố tải video đã được báo tạo thất bại.
- Bản ghi unknown cũ được đối soát bằng chính chứng cứ gốc khi bấm Kiểm tra clip cũ. Giữ submitted=true, ID/lịch sử/log cũ; không giả là chưa gửi. Không kết luận thất bại chỉ từ mã thoát/lỗi tải/ID.
- Nút đọc trạng thái, kiểm tra clip cũ, tải báo cáo JSON, lịch sử nằm ngoài vùng gập. Kiểm tra lỗi mạng xong thì nút bật lại; message/lỗi hiện trong cửa sổ clip, không chỉ ở node phía sau.
- Kiểm tra clip trong cửa sổ chỉ kiểm đúng lượt đang xem. Kiểm tra không tự tải JSON; xuất JSON là nút riêng. Clip chỉ được nhập khi có kết quả video thật được backend kiểm tra.
- Lượt đã xác nhận failed cho phép chuẩn bị lượt mới thủ công nếu mọi điều kiện khác hợp lệ. Hủy xác nhận không gửi; đồng ý mới tạo đúng một ID mới, giữ ID cũ. Unknown hoặc chứng cứ lệch vẫn không được tự tạo lại.

Kiểm thử: 27 test CLI (gồm status failed không download, đối soát unknown cũ không subprocess, sai ID/project/association không phân loại; hồi phục tải video thành công không đổi); Chromium lỗi mạng lặp lại vẫn bật nút, lỗi provider hiển thị rõ, không có video giả/duyệt giả, JSON riêng, không POST tự động, hủy không gửi, xác nhận tạo đúng một ID mới; UI hồi quy và 3 JS checks đạt. Fixture cục bộ, chưa xác minh Flow thật hoặc GUI updater Windows. Bản sửa không làm một video Flow đã thất bại trở thành thành công.

Chỉ thay workflow.html và adapter app/local_engine/flow_gflow_cli.py. CLI gốc 0.92.1, SDK/runtime/account/profile và pipeline đang chạy giữ nguyên. Không đưa báo cáo riêng của người dùng vào repo/gói.

SHA256: `786651f1b6807df9684d562de1bdc1475252846a0c372d0afdfee607faecb0f7`
