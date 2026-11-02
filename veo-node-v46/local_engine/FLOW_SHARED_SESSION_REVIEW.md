# Duyệt thay đổi lớp session/RPC dùng chung sau .44

Đây là source để duyệt, **chưa nằm trong EXE .44, chưa đóng bản update mới**.
Mục đích là bỏ sự lệch giữa các hàm chuẩn bị/upload/gửi/read đã xác nhận
trong cuộc đối chiếu Phoma. Không coi đây là fix đã được chứng minh cho
`PUBLIC_ERROR_UNUSUAL_ACTIVITY`.

## Đã thay đổi

Thêm [flow_batch_session.py](flow_batch_session.py), sinh ba script có quyền
riêng nhưng dùng cùng phần đọc context, dựng request và đọc response:

| Cổng | Phương thức được phép |
|---|---|
| Bootstrap/upload | jHPbke, NfrxTb, ve2Lsc, DTaVef, nzlxg, maseQ, as29s |
| Generation | Chỉ MZZa6b |
| Read tracker | Chỉ jwpduf và as29s; không chứa code gửi tạo/upload |

Các phần đồng bộ theo cơ chế thông thường trong source Phoma:

- Context lấy từ WIZ của trang hiện tại. Khi thiếu build/session metadata,
  dùng request batchexecute đã quan sát ở **cùng origin, cùng source project**;
  CSRF có thể lấy từ input/meta của trang. Không lấy dữ liệu từ project khác.
- Chuẩn bị phiên, preflight upload/video, upload, generation và tracker dùng
  chung reader; bỏ chốt readiness WIZ-only khiến fallback không thể hoạt động.
- Generation có `hl`, explicit project referrer và credentials include như
  transport Phoma; upload/read cũng qua cùng cách dựng request.
- `_reqid` dùng base context và sequence của trang/project, luôn tăng ngay cả
  khi clock hoặc request quan sát không đổi. Không dùng nó như idempotency key.
- Metadata, cookie và token không được xuất sang Python/report. Response vẫn
  giới hạn 2 MiB, có timeout và không tự retry generation.

Payload tạo ảnh tham chiếu một cảnh vẫn giữ model Lite, portrait và schema đã
đối chiếu; không đổi tài khoản, profile, model hoặc ảnh để thử vận may.

## Không tuyên bố đã chép toàn bộ môi trường Phoma

Giữ profile và browser manager SceneForge đã có. Không chép fingerprint
injection, preload/can thiệp xác minh hay thu hồi cookie ra ngoài trang từ
Phoma. Xác minh vẫn dùng API thông thường của trang.

Phoma còn có fallback sâu hơn trong bootstrap HTML và cách quản lý trình
duyệt/workspace riêng. Context reader ở đây giới hạn nguồn rõ ràng trong
project hiện tại. Vì vậy không gọi hai runtime là giống hoàn toàn, và việc
payload/metadata fixture khớp không chứng minh token được Google chấp nhận.

## Sửa báo cáo, không thay chính sách gửi lại

Receipt không còn giữ `generation_ready=true` sau khi bắt đầu gửi. Message
đổi theo accepted/rejected/unconfirmed thay vì tiếp tục ghi “sẵn sàng gửi”.
Nếu script trả not_sent từ các chốt trước fetch thì lưu rõ generation_not_sent.
Mất kết quả sau khi bắt đầu gửi vẫn giữ unknown; không reset sent trong lỗi mạng.

## Kết quả kiểm tra

- 58 kiểm thử Python/Node fixture: gồm 7 ca transport mới về credentials/
  referrer/locale, fallback đúng project, chống dùng metadata project khác,
  sequence, ACL read/bootstrap, action upload không thể dùng để tạo video,
  và response quá dung lượng không tự retry.
- Chromium + ledger + video mẫu: pipeline thành công, metadata fallback,
  upload bị từ chối, generation bị từ chối, lỗi read, đổi project, đường cũ.
- Ca Chromium bổ sung kiểm cookie giả và referrer thực tế trên từng RPC,
  không xuất cookie/token giả ra report; receipt sau gửi không còn ready.
- Chạy riêng transport và builder tương ứng từ source Phoma có hash đã kiểm
  với stub fetch: payload khớp; danh sách query, headers, credentials mode và
  explicit referrer của generation hiện khớp ở fixture.
  Kết quả: [flow-shared-transport-audit-20261103.json](../../../docs/flow-shared-transport-audit-20261103.json).

Toàn bộ HTTP thử nghiệm là fixture. Chưa gửi Google thật, chưa chứng minh
việc chuẩn hóa transport làm Flow chấp nhận tạo, chưa chạy Windows updater.
Không thay EXE .43/.44 đã phát hành. Nếu đóng bản mới cần thêm module
flow_batch_session.py cùng các caller đã đổi; các builder release cũ sẽ chặn
source lệch để tránh tạo gói thiếu dependency dưới tên bản cũ.

## Các file cần xem

- [flow_batch_session.py](flow_batch_session.py)
- [flow_native_reference.py](flow_native_reference.py)
- [flow_native_pipeline.py](flow_native_pipeline.py)
- [flow_task_tracker.py](flow_task_tracker.py)
- [check_flow_batch_session.py](check_flow_batch_session.py)
- [check_flow_task_integration.py](check_flow_task_integration.py)

Ưu tiên tiếp theo vẫn là một lượt được Flow chấp nhận, không mở rộng queue
hoặc sửa download để che lỗi gửi. Nếu còn bị từ chối, cần quan sát an toàn
một request Phoma thành công và SceneForge thất bại trên máy người dùng;
không suy ra nguyên nhân chỉ từ mã lỗi chung.
