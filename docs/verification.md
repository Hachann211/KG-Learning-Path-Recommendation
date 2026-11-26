# Kết quả kiểm chứng — 21/10/2026

Chuẩn bị demo khách hàng: đã tạo hai tài khoản công khai `admin@neu-demo.test` / `user@neu-demo.test`, hiển thị thông tin dùng thử và nút điền nhanh ngay trên form login. Đăng nhập mở đúng trang theo vai trò và lộ trình riêng của tài khoản, không giữ lộ trình của tài khoản trước. Sinh viên có 3 lộ trình đã lưu, 4 môn hoàn thành, 2 môn đang học, tiến độ 40%; admin có 1 lộ trình tư vấn AI và 2 đề xuất quan hệ chờ duyệt. 15 môn minh họa đã có chuẩn đầu ra/nội dung thực hành riêng. 40 môn NEU đã đồng bộ được giữ nguyên.

Lần kiểm thử toàn bộ mới nhất: **81 passed, 0 failed, 0 skipped**, không có cảnh báo, trong **39,76 giây**; coverage **95,06%** (1.001/1.053 câu lệnh). Có **11 lượt E2E**, thêm luồng dùng tài khoản mẫu, chuyển admin/sinh viên, kiểm tra tiến độ/lộ trình/hồ sơ và quyền truy cập. Kiểm thử backend xác minh mật khẩu băm, tài khoản/lộ trình không tạo trùng, giữ chỉnh sửa khi chạy lại, khôi phục dữ liệu mẫu, từ chối ghi đè tài khoản trùng email và từ chối đóng gói tài khoản cá nhân. Đã khắc phục kiểm thử bấm cạnh chưa ổn định bằng cách chờ khung hình sau thay đổi bảng thông tin rồi chọn cạnh đang hiển thị nổi bật, tránh vùng nhãn nút.

Kiểm tra trực tiếp trên ứng dụng đang chạy: đăng nhập thành công bằng cả hai tài khoản, user bị chặn `/admin` với 403, admin thấy 2 người dùng và 2 quan hệ chờ duyệt, chuyển tài khoản mở đúng lộ trình riêng; form login không tràn trên điện thoại 390px. Không có lỗi JavaScript hoặc request tài nguyên bên ngoài. `node --check app/static/js/app.js` đạt; database không có lỗi khóa ngoại. Bản ZIP cho phép hai tài khoản demo đã gắn nhãn; không chứa `.env`, khóa phiên hay tài khoản cá nhân khác. [Login](screenshots/demo-login.png) · [Login điện thoại](screenshots/demo-login-mobile.png) · [Sinh viên](screenshots/demo-student.png) · [Lộ trình đã lưu](screenshots/demo-saved.png) · [Quản trị](screenshots/demo-admin.png) · [Nội dung học phần](screenshots/demo-course-content.png). [Kịch bản demo và khôi phục dữ liệu](demo-guide.md).

Cập nhật trang Đồ thị tri thức: banner giải thích môn học → kỹ năng ← nghề nghiệp, khung đồ thị xanh trắng NEU, chú giải kèm số lượng nút/quan hệ thực tế, bảng thông tin nút/cạnh, danh sách kết quả tìm kiếm và nút thu phóng. Cùng khung mới được dùng trong tab đồ thị của lộ trình. `node --check app/static/js/app.js` đạt; `python -m pytest tests/e2e -q` đạt **10/10** trong 22,11 giây. Bổ sung kiểm thử tìm kiếm Python, chọn kết quả/mở chi tiết môn, không có kết quả, đặt lại tìm kiếm và thu phóng. Kiểm thử bấm đường nối dùng vùng bao gồm cả nhãn nút để tránh bấm chồng lên tên môn. Kiểm tra thêm trên ứng dụng đang chạy: 26 nút, 55 quan hệ cho Backend; bảng nguồn/trọng số/tin cậy hiển thị đúng; không có lỗi JavaScript, request ngoài localhost hoặc tràn ngang ở 1440px/768px/390px. [Máy tính](screenshots/graph-desktop.png) · [Tablet](screenshots/graph-tablet.png) · [Điện thoại](screenshots/graph-mobile.png) · [Chọn môn](screenshots/graph-selected.png) · [Chọn quan hệ](screenshots/graph-relation.png).

Cập nhật trang Khám phá môn học: thêm banner ảnh thật, đồng bộ bố cục với trang nghề nghiệp, bố trí lại thanh tìm kiếm/nguồn học phần và thẻ môn học trên điện thoại. `node --check app/static/js/app.js` đạt; `python -m pytest tests/e2e -q` đạt **9/9** trong 23,10 giây. Kiểm tra trực tiếp tại `/courses`: ảnh banner tải/giải mã thành công; tìm Python cho 1 kết quả; trạng thái không có kết quả và xóa tìm kiếm hoạt động; đổi nguồn hiển thị đúng 15 học phần minh họa / 40 học phần NEU đã đồng bộ, số lượng banner cập nhật theo nguồn. Không có lỗi JavaScript, request ngoài localhost hay tràn ngang ở 1440px/768px/390px. [Desktop](screenshots/courses-banner.png) · [Tablet](screenshots/courses-banner-tablet.png) · [Điện thoại](screenshots/courses-banner-mobile.png).

Cập nhật trang nghề nghiệp: `python -m pytest tests/e2e -q` đạt **9/9** trong 22,56 giây. Kiểm tra thêm trên ứng dụng đang chạy: 15 thẻ có 15 ảnh khác nhau và tải/giải mã thành công; bộ lọc Dữ liệu & AI cho 3 kết quả; tìm kiếm, xóa từ khóa, trạng thái không có kết quả và đặt lại danh sách hoạt động; cửa sổ tìm hiểu nghề mở ảnh đúng và chuyển sang tạo lộ trình với nghề đã chọn. Không có lỗi JavaScript, request bên ngoài hoặc tràn ngang ở 768px/390px. [Desktop](screenshots/careers.png) · [Điện thoại](screenshots/careers-mobile.png) · [Thẻ trên điện thoại](screenshots/careers-mobile-cards.png) · [Chi tiết nghề](screenshots/career-detail.png).

Cập nhật ảnh môn học: `python -m pytest tests/e2e -q` đạt **9/9** trong 22,67 giây. Kiểm tra trực tiếp trên ứng dụng đang chạy: 15 ảnh khác nhau, cả 15 tệp tải/giải mã thành công; ảnh trong hộp chi tiết hiển thị đúng; không phát sinh request ngoài localhost, không có lỗi JavaScript hoặc tràn ngang ở 390px. Ảnh được lưu cục bộ dạng WebP, tổng dung lượng khoảng 1,46 MB. [Danh mục sau cập nhật](screenshots/course-photos.png) · [Điện thoại](screenshots/course-photos-mobile.png) · [Chi tiết](screenshots/course-photo-detail.png).

Đã khắc phục trường hợp Flask giữ mẫu HTML cũ trong khi CSS mới làm mất biểu tượng logo. Kiểm chứng trực tiếp tại `http://127.0.0.1:5000`: ảnh SVG tải thành công, logo máy tính/điện thoại hiển thị, không có lỗi JavaScript hoặc tràn ngang. Có kiểm thử hồi quy chủ động trả mẫu HTML cũ để xác minh logo được đồng bộ đúng. `node --check app/static/js/app.js` đạt. Ảnh sau sửa: [logo-fixed.png](screenshots/logo-fixed.png).

Lần chạy toàn bộ bộ kiểm thử sau sửa logo:

```powershell
python -m pytest tests -q --cov=app --cov-report=term --cov-report=json:docs/coverage.json --junitxml=docs/test-results.xml
```

**75 passed, 0 failed, 0 skipped**, thời gian 29,14 giây. Coverage Python: **94,97%** (906/954 câu lệnh). Báo cáo máy đọc ở [test-results.xml](test-results.xml), [coverage.json](coverage.json).

| Phạm vi | Kết quả đã kiểm tra |
| --- | --- |
| Thuật toán | Đúng 10 mã môn duy nhất trong nhóm 15; đúng 5 môn còn lại; xét 3.003 tổ hợp; kiểm chứng độc lập hàm mục tiêu; phá hòa xác định; nghề khác nhau cho tập môn khác nhau |
| Tiên quyết | Đóng tiên quyết trong nhóm; thứ tự topo; học kỳ dự kiến; phát hiện chu trình; giữ môn đã hoàn thành; từ chối thiếu ứng viên |
| Đồ thị | 8 loại nút, 9 quan hệ; lưu/khôi phục từ SQLite; đường giải thích có cạnh thật; quan hệ chưa duyệt không tham gia gợi ý; không bịa lý do khi thiếu đường đi |
| Dữ liệu | Không trộn DEMO/NEU; không tự áp dụng 10/15 cho chương trình chưa xác minh; không tự điền tín chỉ/ID đề cương; đồng bộ idempotent và chống mã trùng |
| API / bảo mật | Quyền Student/Admin và chủ sở hữu; băm mật khẩu; CSRF; chặn tự nâng quyền/sửa điểm; xử lý SQL injection và HTML escaping; hồ sơ và đổi mật khẩu |
| Nguồn ngoài (mock) | Nguồn chính hoạt động/timeout/500; mirror hoạt động; cả nguồn lỗi; cache được giữ; JSON sai/rỗng/thiếu trường/quá lớn; 400 không chuyển nguồn mù quáng; schema dự phòng chưa xác minh bị từ chối |
| Database | Migration baseline nâng cấp database trống; FK; khóa duy nhất; bản ghi và quan hệ sau cập nhật membership |
| PDF | Trả file PDF thực, font Be Vietnam Pro nhúng hỗ trợ tiếng Việt; trình duyệt tải được tệp |
| Giao diện | Chromium thật, SQLite và Flask server tạm; không có JavaScript pageerror trong các luồng được kiểm tra |

Có **9 lượt kiểm thử E2E**: logo với mẫu HTML cũ trên máy tính/điện thoại; responsive 1440px, 768px, 390px; tạo lộ trình/chi tiết/đồ thị/cạnh/so sánh/PDF; đăng ký/đăng nhập/lưu/tiến độ/đổi tên/xác nhận xóa; tìm môn và lọc nghề; Admin đồng bộ và sửa nhóm môn; demo chặn mọi request ngoài localhost. Dịch vụ NEU trong luồng Admin E2E được **mock** để kết quả xác định, không gọi đó là kiểm thử API NEU thật.

Ảnh kiểm chứng:

- [Desktop 1440px](screenshots/final-desktop.png)
- [Mobile 390px](screenshots/final-mobile.png)
- [Tablet 768px](screenshots/viewport-768.png)
- [Đồ thị](screenshots/graph.png)
- [Quản trị](screenshots/admin.png)
- [Từ chối gợi ý chính thức khi chưa đủ dữ liệu](screenshots/official-validation.png)

Ngoài bộ test tự động, đã chạy HTTPX thật để đồng bộ danh mục môn và 5 thông tin chương trình K66 vào database bàn giao. Đã mở website tham khảo và danh mục bằng Chromium. Đã kiểm tra thủ công tại máy: trang chủ HTTP 200; nguồn NEU chưa xác minh trả thông báo nghiệp vụ đúng; màn hình mobile không tràn ngang. Chạy `node --check` cho cả hai file JavaScript đều đạt.

**Chưa kiểm chứng / chưa hoàn thiện theo toàn bộ đề bài:** ánh xạ ID đề cương thật và teaching-plans, membership nhóm tự chọn chính thức theo từng khóa, quy chế nhóm con/học phần tương đương, tải tín chỉ tối đa và lịch mở lớp. Xem [báo cáo API](neu-api-report.md). Bộ tối ưu hiện hỗ trợ trường hợp 10/15 với một nhóm tự chọn; các quy chế khác bị từ chối rõ ràng. Lịch sử lộ trình là snapshot, chưa có nhật ký sự kiện riêng cho mọi lần cập nhật tiến độ. Không công bố bản demo là hệ tư vấn chính thức đã hoàn tất toàn bộ đề tài.

Trình duyệt tích hợp trong ứng dụng Codex không khả dụng trong phiên làm việc này; kiểm thử dùng Playwright Chromium cục bộ sau khi đã kiểm tra kết nối trình duyệt tích hợp.
