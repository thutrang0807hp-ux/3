# SceneForge · Kịch bản tốt + Storyboard cho tab Từ ảnh (chốt ý tưởng 23/10/2026)

> Phạm vi: **[B2]** (bản 2, sau khi bản đầu "Từ video mẫu" chạy trọn). Không đụng gì tới MVP.
> Đi cùng `DAC_TA_TONG_HOP.md`, mục 9 (Tab Từ ảnh, Kho kịch bản). Chưa có ảnh thiết kế.
> Luật chung giữ nguyên: không nút giả, không bịa số, không tự cào web.

## 1. Vấn đề
Ví dụ cần làm video quảng cáo **chai sữa rửa mặt** từ ảnh sản phẩm + bối cảnh + người. Khâu quyết định video có ra đơn hay không là **kịch bản và 3 giây đầu**. Phải trả lời 2 câu:
1. Làm sao có kịch bản tốt nhất?
2. Làm sao có storyboard hay?

## 2. Nói thẳng để không kỳ vọng sai
- **Không AI nào viết ra kịch bản "tối ưu nhất" ngay lần đầu.** AI chỉ học cấu trúc từ những quảng cáo đã thắng rồi viết ra **vài phương án không tệ**.
- Phương án nào thắng thật thì chỉ biết sau khi **đăng và nhìn số đơn**.
- Vì vậy làm theo vòng: **học từ quảng cáo chạy tốt → làm 2–3 phương án → đăng thử → 👍 cái ra đơn → Kho tự xếp lại**. Càng làm nhiều vòng, Kho càng hợp với sản phẩm và khách của mình.

## 3. Chi phí
- Kịch bản, prompt, storyboard đều là **chữ** do Gemini viết. Dùng key miễn phí thì 0đ.
- **Storyboard không gọi AI thêm lần nào.** Gemini trả về cùng lúc với kịch bản.
- Chỉ tốn tiền ở clip Muse / Veo, và **chỉ tạo clip cho phương án đã chọn**.

## 4. Nguồn học: quảng cáo đã chạy tốt
- **TikTok Creative Center → Top Ads** (của TikTok, miễn phí):
  - Lọc được theo ngành (làm đẹp, chăm sóc da…), khu vực, mục tiêu quảng cáo.
  - Có phần phân tích kiểu câu mở đầu, nhịp độ, chữ trên hình, chỗ đặt kêu gọi mua.
  - **Chưa kiểm tra:** có lọc riêng Việt Nam không.
- **Người dùng tự chọn và tự tải** 10–20 quảng cáo cùng loại sản phẩm. **App không tự cào web** (dễ vi phạm điều khoản).

## 5. Thêm vào Kho kịch bản
- **＋ Thêm → Từ video bạn chọn** (đã có trong mục 9.2). App rút ra:
  - **Kiểu mở đầu (hook)**: ví dụ hỏi vấn đề, trước / sau, sự thật bất ngờ, review thật.
  - Các **nhịp**: tên, giây, mục đích, kiểu cảnh, câu ví dụ **đã viết lại**. Không lưu lời gốc.
  - **Storyboard** của video đó.
- 🆕 **Ô nhập chỉ số (tùy chọn):** lượt thích, CTR… lấy từ Creative Center, người dùng gõ tay. **App không bịa và không tự đoán chỉ số.**
- **Xếp hạng công thức** theo: chỉ số đã nhập + điểm 👍 Ra đơn / 👎 Không ăn thua của chính người dùng. Điểm của người dùng được tính nặng hơn.

## 6. Thêm vào ô Kịch bản (tab Từ ảnh)
- 🆕 **Nút "3 phương án":** AI viết 3 bản theo công thức đứng đầu, **mỗi bản một kiểu mở đầu khác nhau**. Người dùng chọn 1 bản rồi mới tạo clip.
- 🆕 **Cách xem Storyboard** (gạt giữa Kịch bản / Storyboard). Mỗi nhịp là 1 ô:
  - Số thứ tự + giây (ví dụ 0–3s).
  - Ảnh minh họa: lấy clip có sẵn trong Bộ cảnh nếu khớp kiểu cảnh, không có thì để khung trống ghi kiểu cảnh.
  - Kiểu cảnh, góc máy, chuyển động.
  - Lời đọc + chữ trên hình (nếu có).
  - Sửa trực tiếp trên ô được. Sửa ở đây hay ở bảng Kịch bản là **cùng một dữ liệu**.
- Ghi chú công thức đã dùng (tên + nguồn), để sau này 👍 / 👎 cộng đúng chỗ.
- ⚠ Nhắc khi lời mới giống lời của video nguồn quá nhiều.

## 7. Phải thử thật
- Creative Center có lọc Việt Nam không, tải video về để phân tích có tiện không.
- Gemini rút "kiểu mở đầu" và nhịp từ 10 quảng cáo có ổn định không (chạy 2 lần ra giống nhau không).
- 3 phương án có thật sự khác nhau không, hay chỉ đổi vài chữ.

## Nguồn
- https://blog.gethookd.ai/learn/4-top-tiktok-creative-center-ads-library-tools-in-2026/
- https://blog.hootsuite.com/tiktok-ad-library/
- https://www.adcore.com/blog/tiktok-creative-center-how-2-find-winning-ads/
