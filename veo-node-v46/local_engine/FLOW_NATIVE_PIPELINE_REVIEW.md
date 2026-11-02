# Duyệt code: phiên → upload nhận ID → gửi → nhận video

Thay đổi này nằm **sau bản v46.43**, chưa có trong EXE v46.43 đã tải trước đó.
Code được duyệt tại `b590750`; sau khi người dùng yêu cầu đóng gói, đã tạo bản
thử **v46.44**. Chưa xác minh tạo video Google thật hoặc chạy trên Windows.

## Luồng mới

Một lần bấm **Tạo 1 video**, sau xác nhận của người dùng:

```text
RequestLedger cũ claim request_id và ghim account/room/scene/part
  → mở đúng profile đăng nhập hiện có
  → dùng lại project của account/room, hoặc tạo bằng jHPbke đúng một lần
  → chuẩn bị workspace: NfrxTb → ve2Lsc → DTaVef → nzlxg
  → upload maseQ trực tiếp với byte ảnh đã duyệt
  → đọc mediaId tại đúng slot response [0][0], lưu trước bước đọc chi tiết
  → as29s xác minh đúng mediaId + project + tài nguyên ảnh
  → ghim hash prompt và cấu hình Ingredients/Lite/9:16/x1 vào receipt
  → xác minh lại receipt trước gửi
  → MZZa6b đúng một lần
  → lưu mediaId/projectId/workflowId video ngay khi phản hồi hợp lệ
  → jwpduf → as29s → stream + ffprobe/hash → trả video về cảnh
```

Không bấm Upload media, không tìm chip ảnh, không điền prompt hoặc đọc settings
trong composer cho luồng mới. Prompt và cấu hình được gửi trong payload; các
trường report có `settings_evidence`/`prompt_evidence` phân biệt việc đó với
đọc lại giao diện. Không báo đã gắn chip khi không thực hiện thao tác này.

## Phần phiên giữ và phần đã thay

Giữ AccountWebSession, tài khoản đang chọn, profile hiện có, kiểm email và
trình duyệt Chrome/Edge đang hỗ trợ. Không sao chép profile hoặc quản lý
tài khoản sang một hệ thống khác.

Thay phần chuẩn bị project và upload bằng lớp NativeProjectSession. Mỗi thao
tác kiểm binding trước/sau và kiểm đường dẫn project trong trang. Context
request và xác minh thông thường được xử lý trong trang; không đưa giá trị
token/cookie sang report, log hoặc SQLite.

Mã Phoma có những phần preload/can thiệp xác minh. Các phần đó **không được
chuyển sang SceneForge**. Vì vậy đây là áp dụng kiến trúc và cấu trúc giao
thức, không tuyên bố phiên hai ứng dụng hoàn toàn giống nhau hay chắc chắn
giải quyết được `PUBLIC_ERROR_UNUSUAL_ACTIVITY`.

## Nơi sửa

- [flow_native_pipeline.py](flow_native_pipeline.py): project, session RPC,
  warmup, upload, resolve ID ảnh, receipt và lưu trạng thái upload.
- [flow_native_reference.py](flow_native_reference.py): chọn receipt ảnh trực
  tiếp, xác minh action bình thường, gửi tạo và ghi rõ kết quả gửi trong report.
- [simple_flow.py](simple_flow.py): giữ RequestLedger làm nơi duy nhất claim
  lượt; nối toàn luồng trong task backend, trả trạng thái cho frontend.
- [flow_pair_generation.py](flow_pair_generation.py): kiểm hash/cảnh/account/
  project cho receipt native, không yêu cầu DOM composer.
- [flow_pair_trial.py](flow_pair_trial.py): route chuẩn bị riêng vẫn có để tương
  thích/chẩn đoán; khi native được bật thì dùng cùng lớp upload mới.
- [flow_task_protocol.py](flow_task_protocol.py): hỗ trợ response rỗng chỉ khi
  caller yêu cầu cho bootstrap, và project ID dạng scalar chỉ cho jHPbke.
  MZZa6b vẫn từ chối response rỗng hoặc chỉ có scalar ID.
- `workflow.html`: một nút tạo tự chạy backend pipeline, không gọi route chuẩn
  bị riêng; không gắn nhãn “đã gửi tạo” chỉ vì backend nhận job.

SceneStore/SceneWorkflow trong bản nháp trước vẫn là tài liệu thử nghiệm,
**không cấp quyền gửi và không được sử dụng song song với RequestLedger**.

## Các chốt bảo toàn

- Request ID cũ chỉ trả bản ghi cũ, không upload hoặc tạo lại.
- Lưu `creating` trước RPC tạo project. Nếu mất kết quả thì giữ `unknown`,
  không tự tạo project khác. Khi đã nhận ID, lưu trước điều hướng; lỗi điều
  hướng không làm mất project đã biết.
- Chỉ một upload trong một lượt. Lưu ranh giới `upload_dispatching` trước
  request; timeout/mất kết nối giữ `upload_uncertain` và không gửi tạo.
- Lưu ID ảnh trước các lần đọc resolve. ID/project/URL không khớp thì dừng.
- Không tự chuyển sang đường upload/gửi qua giao diện nếu native thất bại.
- Đổi account/project chặn bước tiếp theo. Không reset dữ liệu, lịch sử hoặc
  tự mở khóa các lượt video `unknown` đã có.
- Trạng thái `generation_dispatching` có `generation_submitted=null`; chỉ
  phản hồi ID hợp lệ mới ghi true. RPC từ chối ghi false; mất kết quả không
  được mô tả thành “chưa gửi”.
- Bộ build .43 được chặn nếu source đã khác nội dung release .43, tránh
  đóng nhầm code mới dưới tên cũ hoặc bỏ thiếu module mới trong payload.

## Bằng chứng đã chạy

51 kiểm thử Python offline đạt, gồm 11 ca mới về shape upload/detail, binding,
tạo/lưu/dùng lại project, timeout khi tạo project, lỗi điều hướng, chặn method
generation qua cổng bootstrap. Các ca còn lại là tracker/protocol và bản nháp.

Chromium + RequestLedger + tệp video mẫu/ffprobe thực, toàn bộ HTTP dùng fixture:

- Full pipeline trên trang **không có composer/settings/chip/Generate**:
  một upload, một generation, nhận đúng ID và video về đúng scene/part.
- Upload bị RPC từ chối hoặc mất kết nối: không có generation.
- Đổi tài khoản/project sau upload hoặc detail trả project khác: không có generation.
- Generation bị RPC từ chối: không poll hoặc tải.
- Lỗi đọc, lỗi tải và dừng sau gửi: không generation lần hai.
- Đọc lại request ID cũ không upload/generate lại.

Chromium với workflow HTML thật và API local fixture: một nút Tạo, không cần
nút Thử ảnh + prompt; hủy xác nhận không post job; xác nhận post đúng một job
native cùng ảnh/prompt/cảnh; không có pageerror.

Đã chạy riêng hàm upload thuần Go từ code Phoma với các dependency stub và
UUID cố định để đối chiếu đủ 12 slot payload. Khớp cấu trúc implementation
mới; không chạy backend/bộ cài Phoma hoặc thực hiện request Google thật.

## Chưa chứng minh

Schema Flow hiện tại, metadata/site key của trang thật, việc normal Enterprise
API cho phép yêu cầu, quota/model và toàn luồng thật trên tài khoản người dùng.
Nếu Flow trả `UNUSUAL_ACTIVITY`, app sẽ báo và giữ lượt; code này chưa được
coi là sửa xong lỗi đó. Chưa mở hàng đợi nhiều cảnh, chưa thêm resume tác vụ
đang chạy sau khi khởi động lại app. ID/receipt đã lưu không đồng nghĩa có
chức năng resume được kiểm chứng trên Flow thật.

Bản thử .44 chứa đầy đủ các module thay đổi và workflow HTML. Có bổ sung tải
báo cáo của lượt lỗi upload mà không mở trình duyệt hoặc gửi lại. Không tái dùng
EXE .43 để đại diện cho thay đổi này.
