# Phoma: lệnh tạo được phát từ đâu?

Kết quả đọc gói `phoma_code.rar` người dùng cung cấp. Chỉ phân tích tĩnh,
không chạy Phoma hoặc gửi yêu cầu tạo video.

## Nhận dạng gói source

- `package.json`: name `client`, **version `1.6.3`**.
- Main: `electron/main.cjs`, chỉ nạp `main.jsc` qua bytenode.
- Backend JS SHA-256:
  `929a8acef0f970dbf3bf7672c165119b151cfd6be7f1e8c9c18c88a4084910bd`.

Mốc Phoma 1.6.2 trong bàn giao trước là mốc khác. Không được coi mặc nhiên
gói code này là 1.6.2, hay khẳng định nó trùng phiên bản đang chạy trên máy
người dùng. Chưa đọc được cấu hình launcher từ các file JavaScript plain-text.
Không chạy/decompile bytecode hoặc can thiệp giấy phép để tìm cấu hình.

## Call chain đã xác nhận trong source

```text
UI Phoma
  → POST /__projects/:id/generate-veo3-video
  → nếu có rotationRunId: pA → chọn worker account → ps(worker.browser, ...)
    nếu không: fg → provider browser → c1 → ps(browser, ...)
  → workspaceContext.acquire
  → ml → wy → xy
  → Hr(browser) chọn page trong browser đó
  → tạo project / điều hướng page / warmup theo execution mode
  → ps dùng chính page/project trả về từ workspace
  → đường API: upload, rồi kE cho reference-to-video
  → kE → $e(page, MZZa6b, ...)
  → page.evaluate → fetch cùng origin Flow
```

### Browser worker và tab đang xem không nhất thiết là một

- `lt(accountId)` lấy lease qua worker manager `Ca.acquireLease`.
- Manager `nf` quản lý worker theo tài khoản, có launch Chrome process và
  kết nối browser riêng; rotation worker đưa browser đó vào `ps`.
- `Hr` chọn từ `browser.pages()` của browser được truyền vào, không chọn
  theo cửa sổ/tab mà người dùng đang mở DevTools.
- `workspaceContext.acquire` trả lại page/project để dùng cho upload,
  generation và các bước sau.

Không phải mọi trường hợp đều tạo tab mới: `Hr` có thể chọn page đang có.
Vì vậy chỉ có thể kết luận source **cho phép dùng browser/page khác**; chưa
có target ID của lần chạy thật để xác nhận worker nào đã gửi.

Ở đường API, RPC generation là **browser-side fetch do backend điều khiển**,
không phải Node fetch trực tiếp. Tab xem kết quả có thể chỉ tải danh sách và
`videoplayback`, trong khi lệnh tạo được phát ở page khác hoặc trước thời
điểm tab hiện tại bắt đầu ghi.

## Cấu hình runtime quyết định có đi qua đường API không

`ir()` đọc `VEO3_FLOW_EXECUTION_MODE`:

- Không có giá trị hoặc `dom` → `dom`.
- `api` → `api`.
- Giá trị khác → lỗi.

Trong hàm video `ps` đã đọc, nhánh `dom` trả sự kiện
`VEO3_DOM_NOT_SUPPORTED` trước khi chạy đoạn upload/generation API. Nhánh API
tham chiếu ảnh dùng kE/MZZa6b. Vì launcher chính là bytecode, không suy ra
được runtime thực tế chỉ từ giá trị mặc định trong backend JS.

Nếu bản đang chạy tạo thành công qua đúng route và source này thì cần xác
nhận cấu hình launcher chọn API, hoặc xác định có backend/phiên bản khác.
**Không được kết luận Phoma đang dùng DOM chỉ vì default là DOM**, cũng không
được kết luận mọi lượt thật đều dùng MZZa6b chỉ vì hàm API có sẵn.

## Phương thức trong đường API

| Đầu vào | Hàm | RPC |
|---|---|---|
| Text-to-video | vE | YhhmEf |
| Reference-to-video | kE | MZZa6b |
| Khung đầu | IE | eb1hJf |
| Khung đầu và cuối | CE | nprQif |
| Trạng thái video | Wc | jwpduf |
| Asset detail | ci | as29s |

Đây là mapping source của đường API, chưa phải bản ghi request của một lượt
Phoma thật trên máy người dùng.

## Diễn giải lại ảnh Network đã nhận

Ảnh chứng minh project có media/video và tab đang tải/phát chúng. Nó không
xác nhận tab đó là page của worker gửi tạo hoặc được ghi đúng thời điểm tạo.
DevTools của một target không thu được Network của toàn bộ browser/worker.

Không thấy MZZa6b trong các ảnh đó **không phải bằng chứng method khác**.
Wuwl/PAGE_VIEW và NfrxTb/[14] đã xem không phải lệnh tạo video. Không yêu cầu
người dùng tiếp tục dò từng dòng tại tab này hoặc tạo thêm video chỉ để chụp.

## Nơi lấy bằng chứng tiếp theo

1. Xác nhận phiên bản Phoma đang chạy để so đúng source 1.6.3.
2. Nếu Phoma hỗ trợ DevTools cho chính cửa sổ ứng dụng, xem request local
   `generate-veo3-video` ở đó để xác nhận route, mode/model và sự kiện phản hồi.
   Không dùng DevTools của tab website Flow để suy ra worker route.
3. Backend source còn có route `GET /__app/logs`, dùng ring buffer, có các
   nhãn `Veo3 Worker`, `Veo3 Video`, `Shared Flow workspace`, `Project Veo3 Video`.
   Route chịu phiên local của app; không tìm, xuất hoặc yêu cầu token local.
   Chỉ dùng cơ chế log/viewer mà ứng dụng đã hỗ trợ.
4. Để khẳng định target thực sự gửi, cần quan sát runtime hợp lệ của worker.
   Cloud hiện không có browser/process Windows của người dùng, nên chưa làm
   được bước đó. Không tự gắn debugger vào worker hoặc sửa app Phoma để thu token.

Chỉ chia sẻ các tên route/mode/model, tên sự kiện và mã lỗi đã loại dữ liệu
đăng nhập. Không gửi raw HAR, cookie, Authorization, form at, token hoặc signed URL.

## Ảnh hưởng đến SceneForge

Chưa có bằng chứng chọn sai RPC của đường reference API; không thay MZZa6b
bằng một RPC lấy ngẫu nhiên từ danh sách Network. Các bản .44/.45 vẫn chưa
khôi phục tạo video thật. Phát hiện về vị trí phát request và phiên bản source
chưa phải bản sửa lỗi UNUSUAL_ACTIVITY; không đóng update mới từ phát hiện này.
