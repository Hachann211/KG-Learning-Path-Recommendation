# Kịch bản demo NEU Learning Path

Mở `http://127.0.0.1:5000`, nhấn Ctrl + F5 để nhận giao diện mới nhất, sau đó chọn biểu tượng tài khoản ở góc trên bên phải. Form login hiển thị sẵn hai tài khoản; nút **Dùng tài khoản** chỉ điền thông tin, nhấn **Đăng nhập** để tiếp tục.

| Vai trò | Email | Mật khẩu |
| --- | --- | --- |
| Admin | `admin@neu-demo.test` | `Admin@123456` |
| Sinh viên | `user@neu-demo.test` | `User@123456` |

## Luồng sinh viên — khoảng 5 phút

1. Đăng nhập tài khoản sinh viên. Trang Tổng quan chào **Nguyễn Minh Anh**, ngành Công nghệ thông tin, khóa K66, mục tiêu Backend Developer. Có 10 môn gợi ý, tổng 30 tín chỉ và tiến độ **40%**.
2. Mở **Lộ trình của tôi**: 4 môn hoàn thành là Python, Cơ sở dữ liệu, Cấu trúc dữ liệu và giải thuật, Lập trình hướng đối tượng; 2 môn đang học là Phát triển ứng dụng web và Hệ quản trị cơ sở dữ liệu. Mở chi tiết để trình bày nội dung môn, chuẩn đầu ra, quan hệ tiên quyết, điểm phù hợp và giải thích lựa chọn.
3. Chọn **Môn được gợi ý** để xem điểm và lý do chọn 10/15 môn. Chọn **Kỹ năng mục tiêu** để xem biểu đồ mức bao phủ nội dung theo nghề nghiệp.
4. Mở **Đồ thị tri thức**, tìm Python, chọn kết quả hoặc nút trên đồ thị. Chọn một đường nối để xem quan hệ, trọng số, nguồn và độ tin cậy; thử thu phóng và đặt lại.
5. Mở **Lộ trình đã lưu**: có sẵn Backend, Data Analyst và Full-stack. Nhấn **Tiếp tục** trên một hướng khác để so sánh lựa chọn môn. Từ lộ trình, có thể chọn **So sánh định hướng** và xuất PDF tiếng Việt.
6. Mở **Khám phá môn học**: tìm Python hoặc SQL, mở ảnh và nội dung chi tiết. Chuyển nguồn NEU để xem danh mục đã đồng bộ. Mở **Định hướng nghề nghiệp** để xem ảnh công việc, lọc nhóm nghề và tạo lộ trình mới.

## Luồng quản trị — khoảng 3 phút

1. Vào **Hồ sơ học tập → Đăng xuất tài khoản**. Đăng nhập bằng tài khoản admin; ứng dụng chuyển thẳng đến `/admin`.
2. Trình bày thống kê người dùng, môn học, đồ thị và **2 quan hệ chờ duyệt**. Trong **Người dùng**, xem hai tài khoản và vai trò tương ứng.
3. Mở **Quan hệ** để xem hai đề xuất `course:DEMO-API → skill:requirements` và `course:DEMO-DA → skill:ui`, đều có `approved: false` và nguồn ghi rõ giả lập. Các đề xuất này chưa tham gia gợi ý. Có thể dùng **Chỉnh sửa** để minh họa quy trình kiểm duyệt.
4. Mở **Chương trình**, xem ngành/khóa và **Nhóm học phần**. Mở **Trọng số** để trình bày 5 thành phần điểm phù hợp.
5. Mở **Đồng bộ dữ liệu** để xem nhật ký NEU đã lưu. Gọi đồng bộ mới cần kết nối đến API; các chức năng demo và tài nguyên hình ảnh chạy cục bộ.

## Dữ liệu đã chuẩn bị

- 2 hồ sơ giả lập; sinh viên có 3 lộ trình, admin có 1 lộ trình mẫu AI.
- 6 bản ghi tiến độ sinh viên: 4 hoàn thành, 2 đang học.
- 15 học phần minh họa có ảnh thật, mỗi môn 3 chuẩn đầu ra và 4 phần nội dung riêng, tổng 45 tiết minh họa/môn.
- 15 nghề nghiệp, 18 kỹ năng, 5 ngành × 4 khóa minh họa, đồ thị kiến thức và trọng số.
- 2 đề xuất quan hệ giả lập để trình bày kiểm duyệt, không thay đổi kết quả gợi ý trước khi duyệt.
- Danh mục môn học NEU và thông tin chương trình đã đồng bộ từ trước được giữ nguyên.

Các tài khoản, tên người học và tiến độ trên là dữ liệu giả lập. Phần NEU chỉ phản ánh dữ liệu đã đồng bộ; nhóm môn và đề cương chính thức chưa xác minh đầy đủ vẫn giữ giới hạn hiện có. Không trình bày bộ môn DEMO như chương trình chính thức của NEU.

## Chuẩn bị lại trước một buổi demo

```powershell
python scripts/prepare_demo.py
```

Lệnh bổ sung bản ghi còn thiếu, không tạo trùng tài khoản/lộ trình và giữ chỉnh sửa hiện tại. Để đưa các bản ghi mẫu trở lại trạng thái ban đầu:

```powershell
python scripts/prepare_demo.py --reset
```

Lệnh reset chỉ phục hồi hai hồ sơ đã gắn nhãn demo, mật khẩu công khai, tiến độ ban đầu, bốn lộ trình mẫu và hai đề xuất giả lập. Các môn đã cập nhật thêm trong hai tài khoản demo trở về chưa bắt đầu. Không ghi đè tài khoản có email trùng nhưng không thuộc bộ demo. Đăng xuất rồi đăng nhập lại để mở lại lộ trình chính.

```powershell
python scripts/package_project.py
```

Tạo lại `neu-learning-path.zip` với database demo. Công cụ chỉ cho phép hai tài khoản công khai đã gắn nhãn; nếu có tài khoản cá nhân khác thì dừng trước khi thay tệp ZIP cũ. `.env` và khóa phiên cục bộ không nằm trong bản đóng gói.
