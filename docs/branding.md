# Nhận diện NEU Learning Path

Giao diện dùng xanh dương – trắng, tham khảo sắc xanh của [NEU AI Learning](https://ai.neu.edu.vn/learning) và [website NEU](https://neu.edu.vn/). Bảng màu dưới đây là lựa chọn thiết kế cho dự án; không được trình bày như thông số nhận diện chính thức của trường.

| Vai trò | Màu |
| --- | --- |
| Xanh chính, nút và điều hướng | `#00558F` |
| Xanh đậm, trạng thái hover | `#004573` |
| Chữ tiêu đề | `#18334C` |
| Nền xanh nhạt | `#EAF4FC` |
| Nền trang | `#F5F8FC` |
| Nền thẻ | `#FFFFFF` |

Logo riêng của dự án gồm khiên học thuật, sách mở và ba nút kết nối. Sách thể hiện kiến thức, các nút thể hiện quan hệ trong đồ thị và sự phát triển của lộ trình. Biểu tượng được dựng bằng SVG, giữ độ sắc nét khi thay đổi kích thước.

- `app/static/images/logo-mark.svg`: biểu tượng dùng trong thanh điều hướng và tiêu đề trên điện thoại.
- `app/static/images/logo.svg`: bản đầy đủ có chữ NEU Learning Path.
- `app/static/images/favicon.svg`: phiên bản đơn giản cho tab trình duyệt.

Màu được đồng bộ trên sidebar, banner, thẻ môn học, biểu đồ, đồ thị, hộp thoại, thông báo và tiêu đề PDF. Màu xanh lá cho hoàn thành và đỏ cho lỗi vẫn thể hiện ý nghĩa trạng thái.

Sau cập nhật, nhấn `Ctrl+F5` để tải lại giao diện. JavaScript tự đồng bộ logo khi tiến trình Flask đang giữ mẫu trang cũ, bao gồm cả logo trên điện thoại. CSS cũng giữ biểu tượng dự phòng nhìn thấy được với cấu trúc cũ. Cấu hình ứng dụng mới bật tự tải lại Jinja template và không cache HTML để tránh lặp lại tình trạng này sau các lần khởi động tiếp theo.
