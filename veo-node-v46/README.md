# v46 — bản thử tạo clip chạy nền bằng tài khoản web đã chọn

## Bằng chứng và phạm vi

Người dùng đã gửi kết quả BACKGROUND_SESSION_OK từ công cụ kiểm tra trên máy Windows của mình: phiên đã lưu đọc được đúng danh tính khi mở nền. Đây là xác minh đăng nhập nền trên máy đó, **không phải xác minh tạo/tải video Google thật**.

v46 nối cơ chế chạy nền vào bộ chạy Veo. Đây là **bản thử một clip**, chưa coi là bản đã sửa hết lỗi Flow. Trang xem thử mặc định trên GitHub vẫn giữ v45 đã giao trước đó.

## Cài và dùng

1. Đóng SceneForge và cửa sổ đăng nhập Flow do app mở nếu còn. Không cần đóng Chrome/Edge cá nhân. Chạy **SceneForge-Update-20261101-v46.exe**, chọn bản cài có SceneForge.exe cùng install-settings.json; theo đường dẫn đã cung cấp là `D:\4\releases\2026.10.28.2`.
2. Updater kiểm baseline v2, tối thiểu patch v14 và sao lưu các file thay. Giữ runtime/model/dự án/tài khoản/profile; không cần cài lại hoặc chạy công cụ kiểm tra nền lần nữa.
3. Mở lại. Giữ tài khoản đăng nhập web đã chọn ở tab Tài khoản. Không mở trang Flow để tạo clip. Nếu sau này cần đăng nhập/xác minh, xử lý tại tab Tài khoản, rồi đóng cửa sổ đăng nhập sau khi app nhận tài khoản.
4. Node phải hiện **Veo v46**. Chọn ảnh đã duyệt và prompt, bấm **Tạo clip cảnh này** cho đúng một clip. Xác nhận có thể dùng credit Flow; không dùng Veo API/key hoặc đổi nguồn tính phí.
5. App mở đúng profile ở chế độ headless, chuẩn bị dự án của phòng và xử lý nền. Khi nhận video về, xem rồi bấm Dùng clip này cho workflow như trước.
6. Nếu báo lỗi, xem **Xem bước Flow đang vướng** ngay trong node nếu có ảnh. Không phải mở web để bấm tiếp. Ảnh nằm trong Data trên máy; không tự gửi lên GitHub hoặc dịch vụ khác. Lỗi sau khi có thể đã bấm Tạo vẫn giữ chưa rõ kết quả, không tự tạo lại.

Tài khoản trong tab Tài khoản là nguồn duy nhất. Node không có nút kết nối, không tạo profile đăng nhập thứ hai, không cần endpoint/cửa sổ CDP của v45 đang mở. Sau mỗi lượt, browser nền được đóng để giải phóng profile. Nếu profile vẫn do cửa sổ đăng nhập dùng, app dừng và nhắc đóng riêng cửa sổ đó một lần; không kill trình duyệt cá nhân hoặc xóa khóa profile.

## Cách hoạt động

- AccountWebSession lấy account_id/email/profile_key từ registry đăng nhập web cũ. BackgroundFlowSession mở profile đó bằng Chrome/Edge đã cài với headless=True; không sao chép cookie, không thay nhận diện trình duyệt hay xử lý CAPTCHA.
- Kiểm tài khoản và thử thách trước các thao tác. Dự án riêng được tạo qua nút New project được nhận diện duy nhất khi phòng/tài khoản chưa có ánh xạ; URL hợp lệ lưu trong vault theo cặp account/room. Lượt sau dùng lại. Không chọn bừa một dự án trong danh sách. Tạo dự án không đồng nghĩa bấm tạo video; bước chuẩn bị lỗi không tự gửi video.
- Tải một ảnh, xác minh preview, điền prompt; chỉ bấm Generate một lần khi kiểm được Lite, 8s, 9:16, x1 và chế độ từ khung. Các tab/option đang hiện nhưng chưa được chọn không được coi là cài đặt hiện tại. Nếu chưa xử lý được thì dừng và lưu ảnh lỗi trong node, không chuyển sang chuỗi thao tác tay trên một web khác.
- Theo dõi thẻ mới khớp prompt, loại thẻ cũ/nhiều kết quả. Chỉ hiển thị phần trăm đọc được từ thẻ đó. Khi có đúng video, đọc tài nguyên media của thẻ qua trang đã đăng nhập và stream từng đoạn tối đa 256 KiB xuống file, tổng tối đa 100 MiB. Chỉ nhận blob của origin Flow hoặc HTTPS từ các host media Google được cho phép; không gọi RPC tạo video riêng. Không phụ thuộc bấm nút tải/native download manager hoặc nạp toàn bộ video thành base64 trong RAM.
- Kiểm ffprobe, container MP4/WebM, 8s, 9:16, dung lượng và hash rồi nhập đúng phòng/cảnh/phần clip. Giữ ID/cổng/dây node và schema job v43. Không tự retry khi có thể đã gửi. URL media có chữ ký không đưa ra API trạng thái/log; kết quả chỉ lưu file và hash.
- Lỗi của job lưu từ bản trước được gắn nhãn rõ. CancelledError mới có lý do dừng và phân biệt trước/sau bước tạo; lịch sử cũ không bị xóa hay tự coi là chưa gửi.

## Kiểm tra

- check_background_veo_v46: Chromium headless thật, profile fixture có phiên lưu sẵn; không đọc endpoint cửa sổ, hai lượt liên tiếp dùng lại dự án, đúng ảnh/prompt/một click, tiến độ 37%, stream blob video thực và ffprobe/hash; đóng profile sau lượt; chặn nguồn lạ/quá dung lượng/sai nick/cài đặt chưa kiểm; lỗi trước gửi có ảnh, không checkpoint thao tác web. Trang và dữ liệu Google đều là fixture, DNS ngoài bị chặn. Kiểm tab hiện nhưng chưa chọn không làm giả settings_ready.
- check_account_api_v46: lựa chọn tài khoản dùng chung, background flag, chặn đăng nhập riêng/chuyển mode cũ; ảnh chẩn đoán cần phiên local và không cache.
- check_account_ui_v46, check_veo_node_v46: giữ bảng/sơ đồ Tài khoản cũ, đồng bộ lựa chọn sang node, không có nút kết nối, hiển thị ảnh lỗi trong app, giữ cổng/dây/clip/giọng/phụ đề và chống nhập trùng. Đã chạy bằng frontend lấy từ payload giao.
- check_simple_flow và check_simple_flow_v44: hồi quy đường cũ và bộ kiểm video dùng chung; các test constructor cũ không đại diện cách đăng nhập của v46. check_lightweight_start kiểm không khởi động engine cũ mặc định.
- So khớp từng file/hash của ZIP nhúng EXE với nguồn; kiểm ZIP integrity và compile Python. Không tuyên bố tất cả test UI lịch sử áp dụng cho v46.

**Chưa kiểm việc tạo/tải một video Google thật từ v46 và chưa chạy updater v46 trên Windows.** Đăng nhập nền đã có kết quả người dùng; selector/cài đặt/tài nguyên media/CORS của Flow thật vẫn cần thử một clip. Nếu UI hoặc nguồn tải không hỗ trợ, v46 báo rõ và không tự đổi model, tài khoản hay gửi lại. Không khẳng định mọi tài khoản Google đều chạy nền được.

## Sửa tải ảnh Ingredients

Giữ chế độ Ingredients (không ép Frames). Worker chỉ điền prompt sau khi xác nhận có đúng một ảnh xem trước mới trong vùng tạo, ảnh đã tải xong và không còn trạng thái tải/lỗi. Việc gán tệp vào input hoặc hộp chọn tệp chưa được coi là gắn ảnh thành công. Input ảnh được giới hạn trong composer hoặc hộp tải đang mở để tránh chọn nhầm input ở khu vực khác.

Ở chế độ nền, không xác nhận được ảnh thì dừng trước prompt/Tạo, lưu ảnh chẩn đoán tại node và không yêu cầu tải thủ công. Kiểm tra lại ảnh và cấu hình ngay trước gửi; giao diện Tài khoản giữ nguyên.

Kiểm thử trên bản nguồn đầy đủ (ZIP v46 giải nén, chép đè các file local_engine v46 đã sửa): `python3 -m local_engine.check_reference_upload_v46`, `python3 -m local_engine.check_background_veo_v46`, `python3 -m local_engine.check_simple_flow_v44`, `python3 -m local_engine.check_account_api_v46`. Dùng Chromium và fixture, không chứng nhận Google thật. Bản EXE cập nhật 2026.11.01.46.1 đã đóng gói tại downloads/v46-ingredients-fix; gói source ZIP và EXE v46 cũ giữ nguyên.

## v46.2 — chờ vùng tạo Flow tải xong

Ảnh chẩn đoán người dùng cho thấy dự án vẫn ở Loading. Worker chờ tối đa 90 giây cho ô nhập có thể sửa và nút tạo xuất hiện (nút có thể chưa bật); trong thời gian này vẫn kiểm tra tài khoản và hủy tác vụ, chưa tải ảnh hoặc điền prompt. Hết hạn báo lỗi tải trang riêng, giữ ảnh chẩn đoán. Không tự reload hoặc gửi lại. Đã kiểm thử Loading kéo dài, trang tải xong trễ, nút tạo chưa bật và luồng nền tạo/nhận clip bằng fixture Chromium. EXE v46.2 ở downloads/v46-loading-fix; chưa kiểm thử Windows hoặc Google thật.

## v46.3 — sửa trình cập nhật

Hai bản hotfix trước ghi phiên bản 5 phần không hợp lệ với System.Version. Bản mới dùng 2026.11.01.463 (4 phần); updater chấp nhận metadata 5 phần cũ chỉ trong phép kiểm tra baseline tối thiểu, vẫn chặn bản thấp hơn v14. Kiểm thử check_patch_versions.ps1 đạt bằng PowerShell 7.4.6 trên Linux; chưa chạy giao diện cài đặt Windows. Payload ứng dụng giữ nguyên v46.2. EXE tại downloads/v46-installer-fix.

## v46.4 — tải ảnh qua portal và composer lồng nhau

Bổ sung nút icon add_2/add_circle, tìm composer nhỏ nhất có nút tạo thay vì lấy hàng prompt bên trong. Khi chính thao tác thêm/tải ảnh mở input ngoài composer, chỉ chọn input ảnh mới được tạo, không dùng input không liên quan đã tồn tại. Ngăn giao tệp đồng thời qua chooser và input. Chờ ảnh gắn tối đa 30 giây; thông báo phân biệt chưa giao tệp và đã giao nhưng chưa thấy preview. Không bỏ điều kiện ảnh gắn trước prompt. Chromium fixture kiểm tra các bố cục này đã đạt; chưa xác minh đường tải của tài khoản Google thật. EXE ở downloads/v46-upload-fix, phiên bản 2026.11.01.464 hợp lệ với System.Version.

## v46.5 — đối chiếu rtrtr4

Đã đọc repo thutrang0807hp-ux/rtrtr4 ở commit db5aa529c5203bee37cd05d4925b622419616b02. Khôi phục đường tìm input ảnh ẩn có sẵn trên toàn trang từ flow_engine.py: ưu tiên input trong vùng tạo, nếu không có thì dùng duy nhất một input ảnh toàn trang. Không bắt buộc input phải mới được tạo. Bước tìm nút + không phụ thuộc nút Generate. Adapter đã vượt qua cả 5 test_upload.py của repo tham chiếu khi thay hàm upload_reference bằng adapter v46.5. Xác nhận ảnh trước prompt vẫn tự động trong chế độ nền. Không tuyên bố đã chạy Google thật. EXE tại downloads/v46-simpleflow-upload.

## v46.6 — tự kiểm tra lượt chạy

GET /local-api/flow/simple/diagnostics/{rid} đối chiếu store_id đã lưu, bản ghi, transport và phòng với backend hiện tại, trả kết luận rõ ràng. Không tìm trong các thư mục khác, không tự khôi phục lịch sử, không khẳng định lượt chưa gửi và không tự retry. Node tự gọi khi đọc lượt trả 404; thêm nút Kiểm tra lỗi tự động và Tải báo cáo lỗi JSON (mã lượt/kho, đường dẫn dữ liệu, trạng thái, không xuất cookie/token/prompt). API kiểm thử các trường hợp đối chiếu và quyền truy cập đã đạt; UI Chromium kiểm tra tự chẩn đoán, tải JSON, giữ lịch sử và không phát sinh lượt mới. Giao diện Tài khoản giữ nguyên. EXE ở downloads/v46-diagnostics.

## v46.7 — bản thử chỉ tải ảnh

Thân hàm upload_reference được sao chép nguyên văn từ flow_engine.py của rtrtr4 db5aa529; xác minh AST và 5 kiểm thử upstream. POST /flow/simple/upload-only nhận ảnh và tài khoản chung, mở dự án rồi gọi trực tiếp hàm đó. Không cấu hình Ingredients, không dùng điều kiện preview trong composer, không điền prompt, không Generate, không ghi lượt video. UI có nút Chỉ tải ảnh lên dự án Flow và khóa tạo video trong bản thử; giữ lịch sử cũ. Kết quả delivered_unverified chỉ nghĩa là giao tệp, không tuyên bố đã lưu vào thư viện. Giữ browser và ảnh nguồn sau giao tệp để không cắt ngang tải mạng; ảnh chụp sau tải hiển thị và có thể xem lại trong node. API status chỉ giữ lần thử hiện tại trong bộ nhớ; JSON báo cáo và ảnh chụp lưu trong flow-results. Giao diện Tài khoản không đổi. Đã kiểm thử Chromium fixture và UI; chưa kiểm chứng Flow thật hoặc GUI updater Windows. EXE ở downloads/v46-upload-only.

## v46.8 — nút thêm trên thanh dự án

Ảnh người dùng cho thấy nút + trên toolbar dự án, không có + cạnh prompt. Wrapper upload_to_project chọn duy nhất nút Add có nhãn rõ ràng trên hàng đầu phía phải, mở menu rồi gọi upload_reference giữ nguyên; nếu không xác định duy nhất thì không đoán nút. Không bấm + Library/sidebar hoặc Start/End. Trường hợp toolbar mở filechooser trực tiếp cũng nhận ảnh. Báo cáo ghi vị trí/nhãn các nút Add tìm thấy. Kiểm thử Chromium bố cục toolbar/sidebar/composer đã đạt; chưa kiểm chứng Google thật. EXE là delta 2 file, yêu cầu v46.7 (2026.11.01.467) trở lên, tại downloads/v46-project-upload. Giữ giao diện bản thử chỉ tải ảnh, không tạo video.

## v46.9 — đối chiếu báo cáo nút thêm ảnh

Hai báo cáo người dùng có delivered=false và cùng reference_sha256; báo cáo v46.8 có add_controls=[] nên bộ lọc chưa nhận ra nút. Wrapper phân tích nhãn aria/title/text riêng và icon thay vì ghép mọi nhãn rồi regex; ghi toàn bộ toolbar_controls. Với nút không nhãn, desktop >=1000px, chỉ xét nút nhỏ duy nhất trong vùng nút + đã thấy ở screenshot (tâm x 72–78%, hàng trên), không bấm nút có tên khác hoặc nhiều ứng viên. Kiểm thử SVG không nhãn và không chạm + sidebar đã đạt. Giữ nguyên upload_reference gốc; thêm Tải báo cáo thử ảnh trong node. Chưa chứng minh upload trên Google thật. Delta 3 file yêu cầu v46.7+, EXE ở downloads/v46-toolbar-upload.

## v46.10 — chờ và nhận diện ảnh mới

Giữ nguyên upload_to_project/rtrtr4 đã chạy được. Trước upload ghi baseline định danh ảnh thư viện; sau giao tệp chờ tối đa 60 giây cho duy nhất một asset mới, ảnh load xong, không có aria-busy/progress/data-state tải đã biết, thumbnail khớp ảnh nguồn bằng đối chiếu pixel chuẩn hóa và định danh ổn định >=0.75s. Không dùng ảnh cũ giống hệt, ảnh trong form/dialog, blob/data preview không có media ID hoặc nguồn URL chỉ đổi query token. Ghi uploaded_asset và room/scene/part/reference_sha256 để nối prompt sau. Đây là bằng chứng UI sẵn sàng, không cam kết lưu bền phía server. Hết hạn chỉ báo delivered_unverified, giữ phiên, không điền prompt hoặc Generate. Kiểm thử worker upload chậm hơn 3 giây, các ca nhận nhầm và UI/Accounts đã đạt; chưa xác minh Google thật. Delta 3 file yêu cầu v46.7+, EXE tại downloads/v46-upload-ready.

## v46.11 — nối ảnh mới vào Ingredients và prompt

Thêm nút Tải ảnh → Ingredients → điền prompt. Request chụp cố định ảnh/prompt/room/scene/part cùng selection token; UI khóa chỉnh scene/prompt khi đang chạy và nút Generate vẫn bị khóa. Sau image_ready, chỉ chọn đúng key asset vừa upload. Chọn chế độ Ingredients bằng lựa chọn rõ ràng, mở menu của đúng ảnh và chỉ dùng action Add to prompt/Use as ingredient tương đương chính xác. Không dùng Animate/Frames hoặc bấm Generate. Xác nhận một ảnh tham khảo mới đúng nội dung trong composer, không còn progress, rồi mới điền prompt và đọc lại nội dung. Không xóa ảnh tham khảo hoặc ghi đè prompt cũ khác; UI/menu không hỗ trợ thì dừng ở image_ready và ghi preparation_error/menu vào báo cáo, giữ ảnh đã tải. Report chứa attached_asset_key và prompt SHA thay cho toàn bộ prompt. Chuẩn hóa URL giữ query định danh asset, chỉ bỏ token/kích thước tạm thời. Worker/adapter/UI/API và hồi quy Accounts đã đạt bằng Chromium fixture; chưa chạy Flow thật hoặc GUI updater Windows. Delta 3 file yêu cầu v46.7+, EXE tại downloads/v46-ingredients-prompt.

## v46.12 — chuyển bước sau upload và chẩn đoán timeout

Báo cáo thực tế đã xác nhận image_ready và một media mới khớp, nhưng TimeoutError trước marker ingredients, chưa ghi đủ để xác định action lỗi. Helper gửi Escape sau ảnh sẵn sàng để đóng popover upload, dùng live locator chọn mode thay danh sách locator nth lưu qua lúc React đổi DOM; đọc trạng thái mode bằng một lần evaluate_all. Ghi preparation_stage trước từng thao tác, composer_controls/mode_trigger và error_stage/timeout_detail, lược nội dung prompt. Không force click hoặc bỏ xác nhận ảnh. Chromium fixture: overlay đóng bằng Escape + nút remount thành công; overlay không đóng phải timeout đúng open_mode_menu, vẫn giữ image_ready và không prompt/Generate. Chưa chứng minh nguyên nhân trên Google thật. Delta 3 file yêu cầu v46.7+, EXE tại downloads/v46-prompt-transition.

## v46.13 — đúng accessible name nút chế độ

Báo cáo thực tế v46.12 có composer_controls: nút text Video · 720p · 8s/crop_16_9/x2 mang aria-label Settings trigger. get_by_role(name bắt đầu Video) không thể khớp vì aria-label thay tên hiển thị. Thêm nhận diện chính xác Settings trigger trong composer và dùng control này khi xác định ancestor không có form, bỏ Start/End làm dấu nhận diện vùng cấu hình. Không thay đường upload. Chromium tái hiện đúng aria-label trên form và div composer đều đạt, cùng hồi quy ghép ảnh/prompt và timeout overlay. Chưa xác minh Google thật. Delta 3 file v46.7+, EXE tại downloads/v46-settings-trigger.

## v46.14 — đầy đủ cài đặt và đọc lại Flow

Thêm simple_flow_settings.py: mở Settings trigger trong composer, tìm panel Video/Image + các nhóm cấu hình; chọn Video, Ingredients, Veo 3.1 Lite, 9:16 và x1, đọc lại toàn bộ, kiểm tra summary 8s/x1. Dùng aria/data-state khi có; với dark UI người dùng đã cung cấp, so nền sáng hơn trong đúng nhóm lựa chọn khi không có trạng thái ngữ nghĩa; không đọc rõ thì dừng. Chọn model trước ratio/output để sửa reset mặc định. Không toggle lại các lựa chọn đã đúng. Sau gắn ảnh đọc/sửa lại cấu hình lần nữa rồi xác minh ảnh vẫn còn và đúng trước prompt.

Giữ nguyên upload_to_project/rtrtr4. Dùng nút More options trong đúng media card (không dùng menu đầu trang); hỗ trợ Add to prompt mở hộp tài nguyên bằng chọn đúng media_id/source_key, không chọn video cũ giống thumbnail. UI hiện dòng cấu hình đã kiểm tra chỉ khi prompt_ready. Report có project_url, verified_settings/settings_controls và lỗi ở từng bước. Cơ chế account+workflow -> project hiện có được giữ, kiểm thử mở lại hai lần chỉ tạo một dự án. Không Generate. Chưa đổi sang direct-composer upload.

Đã kiểm thử Chromium full worker, settings CSS/aria, mode/model reset, picker ảnh đúng, không ghi đè ảnh/prompt khác, upload-only/readiness và UI/API Accounts; chưa xác minh Google thật hoặc GUI updater Windows. Delta 4 file, v46.7+, EXE ở downloads/v46-flow-settings.
