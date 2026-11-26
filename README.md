# NEU Learning Path

Ứng dụng tư vấn lộ trình học tập chạy cục bộ bằng **Flask + SQLite + NetworkX**, với giao diện tiếng Việt, tông xanh dương – trắng và logo học thuật riêng. Bố cục lộ trình theo ảnh tham khảo. Không cần Docker hoặc Neo4j. Xem [bảng màu và logo](docs/branding.md).

## Chạy ngay trong thư mục này

```powershell
python run.py
```

Mở **http://127.0.0.1:5000**. Trang lộ trình là màn hình mặc định; trang giới thiệu ở `/home`. Ứng dụng tự tạo database và bộ dữ liệu demo nếu chưa có. Database cục bộ nằm ở `instance/learning.db`.

## Tài khoản demo khách hàng

Bản bàn giao đã chuẩn bị hai tài khoản dùng thử; email và mật khẩu cũng hiển thị trên form đăng nhập, có nút điền nhanh:

| Vai trò | Email | Mật khẩu |
| --- | --- | --- |
| Quản trị viên | `admin@neu-demo.test` | `Admin@123456` |
| Sinh viên Trần Thị Thu Hà| `user@neu-demo.test` | `User@123456` |

Sinh viên có 3 lộ trình đã lưu (Backend, Data Analyst, Full-stack), 4 môn hoàn thành và 2 môn đang học; lộ trình chính hiển thị tiến độ 40%. Admin có 1 lộ trình tư vấn AI và 2 đề xuất quan hệ đang chờ kiểm duyệt. 15 học phần có nội dung, chuẩn đầu ra và dự án thực hành riêng. Đây là tài khoản công khai và dữ liệu giả lập phục vụ trình diễn. [Kịch bản demo](docs/demo-guide.md).

Nếu tạo database mới, chạy `python scripts/prepare_demo.py` sau khi khởi tạo. Lệnh chạy lại không tạo trùng và giữ các chỉnh sửa. Dùng `python scripts/prepare_demo.py --reset` để khôi phục mật khẩu, hồ sơ, tiến độ và các lộ trình mẫu đã gắn nhãn của hai tài khoản này.

## Cài trên máy mới

Yêu cầu Python 3.11 trở lên. Bản triển khai được kiểm tra trên Windows với Python 3.14.2.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe scripts/init_db.py
.\.venv\Scripts\python.exe scripts/prepare_demo.py
.\.venv\Scripts\python.exe run.py
```

Không cần bật quyền chạy PowerShell để kích hoạt môi trường; có thể gọi trực tiếp `.venv\Scripts\python.exe`. Nếu đã kích hoạt venv thì dùng `python` bình thường. Lần cài thư viện đầu tiên cần Internet; sau đó bộ dữ liệu minh họa, font, icon, đồ thị, biểu đồ và xuất PDF đều hoạt động không cần Internet.

`SECRET_KEY` rỗng sẽ dùng khóa ngẫu nhiên lưu tại `instance/.secret_key`, ổn định qua các lần khởi động. Thư mục `instance`, `.env`, khóa bí mật và cache không được đưa vào Git. `HOST`, `PORT` và nguồn/timeout NEU cấu hình trong `.env`.

## Các chức năng đã có

- Lộ trình dạng timeline theo giai đoạn hoặc học kỳ dự kiến; danh sách 10 môn được chọn và 5 môn còn lại.
- 15 ảnh chụp thật theo chủ đề môn học, lưu cục bộ dưới dạng WebP; dùng nhất quán trong danh mục, lộ trình và chi tiết. Không cần kết nối dịch vụ ảnh khi chạy.
- Trang định hướng nghề nghiệp có banner và ảnh công việc thật cho từng thẻ, 5 nhóm lĩnh vực, tìm theo tên nghề/kỹ năng có hỗ trợ từ khóa không dấu, phần tìm hiểu nghề và lựa chọn định hướng trực tiếp.
- 5 cấu hình ngành/chương trình, 4 khóa demo, 15 định hướng nghề nghiệp, 18 kỹ năng, 15 học phần minh họa có quan hệ tiên quyết và nội dung mẫu.
- Xét đủ 3.003 tổ hợp 10/15, tối ưu mức bao phủ kỹ năng, kiểm tra môn đã học, đóng tiên quyết trong nhóm, phá hòa xác định và sắp xếp topo.
- Giải thích từ cạnh thật trong đồ thị; 5 thành phần điểm, mức bao phủ và đường nghề → kỹ năng ← môn.
- Đồ thị Cytoscape lấy từ backend, giao diện xanh trắng NEU với banner giải thích, chú giải và số lượng quan hệ, bảng thông tin kết nối; tìm nút với danh sách kết quả, kéo/zoom, chọn nút/cạnh, làm nổi bật kết nối và xem nguồn. Bố cục thích ứng cho máy tính, tablet và điện thoại.
- Biểu đồ kỹ năng Chart.js; phân biệt độ bao phủ nội dung với năng lực cá nhân.
- Đăng ký, đăng nhập, đăng xuất, hồ sơ và đổi mật khẩu; mật khẩu băm scrypt, kiểm tra quyền phía backend, CSRF cho thao tác thay đổi.
- Lưu nhiều lộ trình, đổi tên, xóa có xác nhận, theo dõi tiến độ cá nhân và tính lại lộ trình sau khi cập nhật.
- So sánh hai hướng nghề nghiệp; tải PDF tiếng Việt bằng font cục bộ.
- Quản trị nghề, kỹ năng, 5 cấu hình chương trình, nhóm môn, nút/cạnh đồ thị, kiểm duyệt cạnh, trọng số và vai trò người dùng. Các biểu mẫu dữ liệu nâng cao dùng JSON có kiểm tra phía backend.
- Đồng bộ danh mục NEU; đồng bộ thông tin 5 chương trình theo khóa; nhật ký nguồn/lỗi và giữ cache khi nguồn lỗi. Đồng bộ đề cương bằng ID đã xác minh có giao diện Admin và kiểm thử mock.

## Phân biệt dữ liệu demo và dữ liệu NEU

**Dữ liệu minh họa – không phải chương trình đào tạo chính thức.** Mã `DEMO-*`, nội dung đề cương, kỹ năng, tiên quyết và trọng số nghề trong bộ demo do tác giả cấu hình để kiểm thử thuật toán. 5 chương trình demo có cùng tập môn thử nghiệm; không đại diện cho khác biệt của 5 chương trình thật.

Trong hộp tạo lộ trình có thể chọn nguồn chương trình. Nguồn NEU chỉ tạo được gợi ý khi chương trình được xác minh, nhóm có đúng 15 môn tự chọn, quy tắc chọn là 10 và các liên kết kỹ năng đã có bằng chứng/kiểm duyệt. Nếu chưa đủ dữ liệu, API trả lỗi 422 với lý do. Không tự gán demo vào NEU hoặc chọn thêm môn ngoài nhóm.

Nguồn chính đã truy cập được và ứng dụng đã lưu danh mục môn cùng thông tin 5 chương trình K66. **Ánh xạ ID đề cương, nhóm tự chọn và quy tắc theo từng chương trình/khóa chưa được xác minh đầy đủ. Vì vậy chưa thể coi đây là bản tư vấn chính thức hoàn chỉnh theo mọi yêu cầu trong tệp đề bài.** Xem [báo cáo API](docs/neu-api-report.md) cho kết quả thật, giới hạn và bước xác minh còn lại.

```powershell
python scripts/inspect_neu_api.py
python scripts/sync_neu.py --query "lập trình"
python scripts/sync_neu.py --curricula --cohort "K66 - 2024"
```

Mirror nội bộ cần mạng tương ứng. Nguồn dự phòng hiện trả 404 ở route được cung cấp; không giả định schema giống nguồn chính. `.env` có `NEU_FALLBACK_SEARCH_PATH` nhưng adapter dự phòng chủ động từ chối cho đến khi có schema đã quan sát và triển khai adapter đúng.

## Tạo quản trị viên

```powershell
python scripts/create_admin.py
```

Nhập email, tên và mật khẩu tối thiểu 12 ký tự tại console; mật khẩu được nhập ẩn. Lệnh này tạo tài khoản quản trị riêng ngoài hai tài khoản dùng thử nêu trên. Đăng nhập rồi mở `/admin`.

Trong Admin:

1. **Đồng bộ dữ liệu:** chọn danh mục môn hoặc 5 chương trình NEU, khóa và từ khóa phù hợp.
2. **Chương trình → Nhóm học phần:** nhập danh sách `course_id` với `group=elective/required` và nguồn bằng chứng. Thay đổi nhóm sẽ đặt lại trạng thái xác minh.
3. **Môn học → Đề cương:** cung cấp `syllabus_id` đã đối chiếu. Không dùng mã môn làm ID khi chưa có bằng chứng.
4. **Nghề nghiệp / Kỹ năng / Nút / Quan hệ:** thêm cấu hình, nguồn và trọng số. Quan hệ suy luận cần `approved=false` trước khi được duyệt. Thêm nghề mới chưa có cạnh `REQUIRES` sẽ chưa tạo được gợi ý.
5. **Trọng số:** chỉnh 5 hệ số, tổng bằng 1. Hệ thống không nhận điểm gợi ý do người dùng tự gửi.

## Kiểm thử

```powershell
python -m playwright install chromium
python -m pytest tests -q
python -m pytest tests -q --cov=app --cov-report=term --cov-report=json:docs/coverage.json --junitxml=docs/test-results.xml
```

Kiểm thử trình duyệt khởi tạo server và SQLite riêng trong thư mục tạm, không tạo tài khoản thử trong database đang sử dụng. Xem [báo cáo kiểm thử](docs/verification.md). HTTP nguồn ngoài trong test tự động dùng mock; những lần gọi NEU thật được ghi riêng trong báo cáo API. Có kiểm tra giao diện 1440/768/390px và chế độ demo chặn mọi request tài nguyên bên ngoài.

## Migration

`scripts/init_db.py` nâng schema từ Alembic baseline `0001` rồi seed demo theo cách idempotent. Với database phát triển đã có trước migration, script stamp baseline tương ứng; không xóa dữ liệu. Khi thay đổi model về sau:

```powershell
$env:DB_AUTO_INIT="0"
$env:FLASK_APP="run:app"
python -m flask db migrate -m "mo ta thay doi"
python -m flask db upgrade
Remove-Item Env:DB_AUTO_INIT
```

Sao lưu `instance/learning.db` trước khi áp dụng thay đổi schema trên dữ liệu đang dùng. Baseline đã được kiểm thử nâng cấp trên database trống.

## Cấu trúc và tài liệu

- `app/models`: 15 bảng SQLAlchemy; schema thu gọn có giải thích trong [kiến trúc và ERD](docs/architecture.md).
- `app/services`: API/adapters, đồng bộ, đồ thị, khai phá từ khóa, thuật toán và PDF.
- `app/routes`: REST API, quyền truy cập và trang Jinja2.
- `app/static`: toàn bộ CSS, JavaScript, font và thư viện cục bộ.
- [API request/response](docs/api.md), [nguồn và giấy phép tài nguyên](docs/third-party.md), `docs/screenshots`: ảnh kiểm chứng.

## Lỗi thường gặp và giới hạn

- Cổng 5000 bận: đặt `PORT=5001` trong `.env` và mở cổng tương ứng.
- PowerShell in sai dấu: đặt `$env:PYTHONUTF8="1"` trước khi chạy script. Giao diện và dữ liệu luôn dùng UTF-8.
- Thiếu Chromium: chạy lệnh cài Playwright ở trên. Bản demo web không cần cài Chromium, chỉ bộ test UI cần.
- CSRF lỗi: tải lại trang, không dùng token của phiên cũ hoặc mở tab sau khi đã đăng xuất.
- Đồng bộ không có dữ liệu: kiểm tra `sync_jobs`, nguồn/mạng và tệp JSON khảo sát. Cache và dữ liệu demo được giữ riêng.
- Nhóm chính thức thiếu 15 môn hoặc chương trình có quy tắc khác: hệ thống chủ động từ chối thuật toán 10/15. Chưa triển khai bộ tối ưu tổng quát cho mọi quy chế khác.
- Chưa có lịch mở lớp chính thức, ràng buộc học phần tương đương/nhóm con hoặc tải tín chỉ tối đa theo học kỳ. Bản demo có một nhóm tự chọn; các ràng buộc bổ sung cần dữ liệu và triển khai tương ứng trước khi dùng cho đăng ký học thực tế.
- Lịch sử lộ trình giữ snapshot kết quả; cập nhật tiến độ tính lại hành trình hiện tại, không ghi đè nội dung các snapshot cũ. Lịch sử từng thay đổi tiến độ chưa có bảng sự kiện riêng.
- Không có tác vụ đồng bộ định kỳ; đồng bộ được kích hoạt thủ công từ CLI/Admin. Đồ thị giới hạn theo nghề/chương trình để tránh tải toàn bộ graph lớn.
