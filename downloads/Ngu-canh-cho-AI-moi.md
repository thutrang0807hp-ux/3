# DÁN NỘI DUNG NÀY CHO AI / LẬP TRÌNH VIÊN MỚI

Tôi đang làm SceneForge. Đừng tạo lại từ đầu. Hãy đọc gói đính kèm, nhất là START_HERE.md, NGU_CANH_VA_LICH_SU.md, TRANG_THAI_KY_THUAT.md và source/docs/editor-feature-audit.md, rồi tiếp tục từ mã nguồn hiện tại.

## Mục tiêu sản phẩm

Tải video tham khảo → tự phân tích/tách cảnh → viết prompt Visual + Motion & Script chi tiết từng cảnh → tạo các clip AI theo hàng đợi → tự ghép đúng thứ tự thành video hoàn chỉnh và xuất, nhưng vẫn cho tôi sửa tay trong trình dựng. Tôi không muốn mỗi lần render clip ngắn lại phải tải xuống rồi sang phần mềm khác ghép.

Tôi muốn tiết kiệm, dùng mã nguồn GitHub và chỉ trả phí API cần thiết. Không muốn mua SaaS đắt. Tôi từng nói dùng OpenAI/ChatGPT, Veo và “Muse của Meta”, nhưng Muse chưa xác định được API cụ thể. Không giả vờ chỉ cần bất kỳ API key nào cũng chạy. Chưa có kiểm chứng API trả phí thật trong bản bàn giao.

## Giao diện đã chốt

- Giữ web SceneForge với thanh tab bên trái: Tổng quan, Thư viện, Phân tích, Hàng đợi, Dựng video, Thiết lập. Không biến toàn bộ website thành giao diện editor.
- Chỉ tab Dựng video dùng bố cục tối gần Concat/CapCut: tư liệu trái, preview giữa, thuộc tính phải, timeline rộng phía dưới. Dựng là một workspace tương tác thật, không phải ảnh chụp có vùng bấm giả.
- Mặc định video dọc 9:16. Tôi đã yêu cầu cho đổi 16:9, 1:1, 4:5 hoặc tùy chỉnh. Đã có xem trước và xuất theo tỉ lệ.
- Chữ và phụ đề tích hợp chung trong editor, chung timeline; không tách thành ứng dụng/tab cấp cao riêng. Giữ 4 kiểu phụ đề, nhập SRT/VTT và xuất SRT/ASS.
- Phân tích video ở tab riêng. Các cảnh xếp ngang thành card có nguồn/kết quả và Visual Prompt + Motion & Script. Cần sửa mới mở drawer/panel. Không ép đọc các cột chữ dài hoặc video dọc khổng lồ chiếm hết chỗ.
- Thư viện có vùng tải lên ở trên và danh sách video đã thêm ở dưới. Chức năng xóa logo đã được tôi yêu cầu bỏ khỏi điều hướng hiện tại.

## Bản cuối cần giữ

Link: https://thutrang0807hp-ux.github.io/3/?v=335c391#editor
Repo: https://github.com/thutrang0807hp-ux/3
Nhánh bản tĩnh: gh-pages, commit 335c39137d35726c53cf87ea8db5d6c38dd0d587.
Concat tham khảo: https://github.com/jub0t/concat. Nguồn native trong gói đang pin v0.2.7, commit 14b5998d793d90858ac982926374044bba4bf39f.

Editor web thực tế đang build bằng `python scripts/demo-web/build.py` trong source. File kết quả chính là `dist/web-demo/native/index.html`, được nhúng một lần trong shell web. Sửa các file `scripts/demo-lite/`, `scripts/native-preview/editor-integration.js`, `timeline-interactions.js`, `editing-controls.js`, `editor-integration.css`; không sửa nhầm trang phụ đề một video hoặc ảnh native reference cũ.

## Yêu cầu âm thanh mới nhất — rất quan trọng

Tôi đã yêu cầu BỎ bảng preset/EQ/effect âm thanh màu mè ở lượt trước. Đừng thêm lại mẫu điện thoại, nhạc nổi, EQ, graph hoặc panel âm thanh to.

Bản cuối đã sửa:
- Thanh mini nằm ngay phía trên timeline, phía phải, khi chọn clip video/âm thanh.
- Âm lượng 0–2.000%, không còn giới hạn 100%. Có những đoạn nguồn rất nhỏ, cần khuếch đại thật.
- Mute/bật tiếng giữ nguyên mức gain.
- Nút chỉnh nhỏ mở vào/ra dần, tốc độ, về 100%, tách tiếng và mốc âm lượng.
- Chọn audio thì không hiện bảng thuộc tính âm thanh lớn bên phải; preview có thêm chỗ.
- Đoạn nhỏ có thể cắt riêng để tăng hoặc đặt mốc âm lượng. Keyframe volume >100% phải được lưu/khôi phục đúng.
- Các preset/EQ cũ được tắt khi đọc dự án cũ; gain cũ chuyển thành phần trăm nhìn thấy được, không giữ effect ẩn.
- Đã dùng âm thanh nhỏ thật để xuất WebM rồi giải mã đo RMS: 1.000% tăng khoảng 10 lần và 2.000% khoảng 20 lần về biên độ. Đừng chỉ đổi con số UI.

## Yêu cầu chuyển cảnh mới nhất

Không chỉ là huy hiệu nhỏ ở mép trên. Tôi muốn một vùng chuyển cảnh phủ chiều cao clip, nằm giữa hai cảnh, bề rộng ứng với thời lượng như hình đã gửi. Đã có khối trong suốt, viền, nhãn thời lượng và tay nắm hai mép.

- Kéo ngắn/dài trực tiếp; có undo và giới hạn theo hai clip.
- Nhãn ◇ mở bảng chuyển cảnh có ảnh hai clip, loại, thời lượng, hướng, easing, xem thử và bỏ.
- Giữ cắt mép/di chuyển clip hoạt động, tránh overlay che toàn bộ thao tác.
- Hòa hai hình thực, slide/push và wipe có hai nguồn cùng hiện; không giả crossfade bằng tối xuống đen. Fade qua đen vẫn là lựa chọn riêng.

## Timeline và thao tác đã có, đừng làm mất

- Kéo tệp/tư liệu vào timeline; tải nhiều video tự có track.
- Nhấc clip lên/khe giữa track để tạo track mới; không giam clip trong một hàng.
- Chèn, đổi chỗ, ghi đè, lớp riêng; không đè mất clip ngầm ở chế độ chèn.
- Cắt mép, cắt tại vạch, chọn nhiều, quét vùng, Shift thêm/bớt, kéo nhóm, undo/redo.
- Tự cuộn sát biên khi giữ chuột, gộp cập nhật kéo bằng requestAnimationFrame.
- Esc phải hủy kéo và khôi phục trước thao tác. Đã có một lỗi thứ tự handler phím; đã sửa, cần giữ bài kiểm tra này.
- Nút Cắt và Phát có nhãn rõ. Space/K phát-dừng, Ctrl/Cmd+B cắt, mũi tên tua frame, Ctrl+Z hoàn tác; không ăn phím khi gõ chữ/ô số. Phím phải hoạt động cả từ shell sau khi bấm sidebar.
- Hình–tiếng tách ra được tự liên kết, di chuyển/cắt cùng nhau; có bỏ liên kết.
- Cắt điểm nối (rolling trim) giữ tổng thời lượng; chưa hỗ trợ rolling đồng thời cả cặp hình–tiếng liên kết.
- Hộp xếp clip nối tiếp cho đổi thứ tự, đặt chuyển cảnh, di chuyển tiếng liên kết và undo cả lần. Chưa tự nhận kết quả hàng đợi AI.

## Chất lượng prompt

Tôi muốn prompt chi tiết cỡ tệp `references/prompt-example-user.txt`: định danh nhân vật/bối cảnh/sản phẩm, kích thước tương đối, bố cục, máy quay, ánh sáng, tính nhất quán, hành động và trạng thái đầu-cuối. Tách Visual và Motion & Script. Tham khảo quy trình GitHub nhưng không chỉ gắn vài nhãn OpenAI/Gemini rồi trả ví dụ chung chung.

Phải phân biệt điều nhìn thấy trong video với yêu cầu sáng tạo. Không tự bịa người, sản phẩm, chuyển động, lời thoại hoặc thông tin không quan sát được. Video mẫu núi minh họa trong demo không phải kết quả AI phân tích video thật. Cần OpenAI/Gemini/Claude hoặc API tương thích tùy chỉnh model/key/cách viết/nguồn tham khảo, nhưng hiện backend viết lại chỉ có phần OpenAI, UI nhiều nhà cung cấp chưa là tích hợp thật.

## Phần còn thiếu cần nói thật

- Chưa nối hoàn chỉnh AI upload → phân tích → prompt → generation queue → assembly vào web tĩnh.
- Muse/Meta API chưa tích hợp; không coi là xong chỉ vì có ô nhập key.
- Browser export đã kiểm được WebM; MP4 chưa bảo đảm mọi trình duyệt. Tối đa 2 phút, 24 fps, render thời gian thực.
- Chưa có proxy tự động, xuất nền native trên web, nhận giọng nói/Whisper, TTS/voice cloning, tracking/mask AI, speed ramp/graph editor và toàn bộ Concat/CapCut.
- Source native Concat và backend Python có sẵn nhưng là luồng riêng. Không khẳng định web chính là engine Rust.
- Mở lại dự án dùng tệp local cần chọn lại nguồn; chưa lưu blob media bền vững.

## Cách làm việc với tôi

Làm trực tiếp, giữ các quyết định đã chốt, không hỏi lại những gì đã có dữ liệu. Trước khi đổi hướng lớn thì thảo luận. Báo cụ thể thêm được gì, thiếu gì; không báo % hoàn thiện tưởng tượng. Đừng xóa các tab khác, đừng rút gọn nguồn GitHub thành ảnh/mock rồi nói đã sao chép đầy đủ. Kiểm thử đúng bản sẽ đưa lên web. Tôi muốn bấm xem hoạt động trước khi tải xuống, không muốn màn hình in nguyên HTML hoặc một bản tải về không mở được.

Hãy xác nhận bạn đã đọc được source và xác định đúng entry point, rồi tiếp tục yêu cầu tiếp theo của tôi.
