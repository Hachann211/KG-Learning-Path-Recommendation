# Khảo sát nguồn NEU — 21/10/2026

Khảo sát trực tiếp bằng HTTPX và Chromium/Playwright. Phản hồi mẫu, mã HTTP và thời gian ở [api_samples/inspection.json](api_samples/inspection.json). Ảnh tham khảo ở `screenshots/neu-reference.png`, `screenshots/neu-catalog.png`.

| Nguồn / endpoint | Kết quả thực tế | Cách sử dụng |
| --- | --- | --- |
| `https://courses.neu.edu.vn/api/search` | HTTP 200, JSON array, bản ghi subject có `subjectCode`, `name`, `curriculums[].year` | Adapter danh mục môn, lọc `type=subject` |
| `/search/curriculum` | HTTP 200, JSON array; mẫu chỉ có 20 bản ghi | Không suy ra toàn bộ chương trình từ mẫu này |
| `/search/major` | HTTP 200, JSON array, có `majorCode`, `id`, `name` | Đối chiếu tên ngành |
| `/curriculum-curricula` | HTTP 200, object `data[].attributes`, `meta.pagination`; tham số lấy từ request thật của website | Đã đồng bộ thông tin đúng 5 chương trình K66 |
| Mirror `http://10.2.11.23:1340/api` | ConnectTimeout với 3 endpoint tìm kiếm | Cần mạng nội bộ tương ứng để kiểm tra lại |
| Dự phòng `http://101.96.66.222:8025/api/v1` | HTTP 404 ở 3 route thử tìm kiếm | Chưa biết route/schema đúng; adapter chủ động từ chối import |
| `/public/d3-syllabus/syllabus/{id}` và `/teaching-plans` | Chưa có ID đề cương được xác minh | Có client, kiểm thử mock và màn hình Admin; chưa xác minh dữ liệu thật |

Đã đồng bộ thật 40 mã môn từ truy vấn “lập trình” và 5 thông tin chương trình K66 vào SQLite trong lần triển khai này. Không coi số kết quả đó là toàn bộ danh mục học phần NEU. Các bản ghi tìm kiếm chỉ mô tả tên/mã và các khóa xuất hiện; không đủ chứng minh môn thuộc nhóm tự chọn hay có cùng đề cương ở mọi khóa.

Trang tham khảo [NEU AI Learning](https://ai.neu.edu.vn/learning) đã mở được. Giao diện quan sát được có thanh điều hướng, vùng tìm kiếm và tùy chọn hiển thị chương trình/môn/bài học. Thiết kế ứng dụng dùng logo tự tạo và bố cục lộ trình từ ảnh người dùng cung cấp.

Đối chiếu [chương trình Công nghệ thông tin K68](https://courses.neu.edu.vn/curriculum/cong-nghe-thong-tin-K677480201?year=K68+-+2026) với [Kỹ thuật phần mềm EP17 K68](https://courses.neu.edu.vn/curriculum/ky-thuat-phan-mem-k67ep17?year=K68+-+2026) cho thấy cấu trúc nhóm tự chọn khác nhau. Đây là lý do hệ thống không tự áp dụng cùng quy tắc cho mọi chương trình. Quan sát này chưa được chuyển thành cấu hình nhóm môn đã xác minh trong ứng dụng.

Website danh mục dẫn đến trang đề cương có dạng `/syllabus/{khóa}/{ngôn ngữ}/{mã môn}`. Một đường dẫn đề cương được quan sát và thử mở đã hiển thị thông báo tài liệu chưa được cập nhật hoặc có lỗi; không thu được ID dùng cho API đề cương. Không thể suy ra rằng tất cả đề cương đều không truy cập được. Chi tiết ở `api_samples/syllabus_inspection.json`.

Các bước xác minh còn lại:

1. Lấy ID đề cương thực tế cùng ánh xạ mã môn–ID từ NEU hoặc nguồn được cấp quyền.
2. Chạy `python scripts/inspect_neu_api.py --syllabus-id <ID_THAT>` và xem phản hồi của cả hai endpoint.
3. Đồng bộ đề cương từng môn trong Admin, đối chiếu tín chỉ, môn tiên quyết, nội dung và phiên bản khóa.
4. Nhập membership nhóm tự chọn có tài liệu nguồn. Xác minh số môn phải chọn theo từng chương trình/khóa; chương trình khác 10/15 cần thuật toán cấu hình riêng thay vì ép cho đủ.
5. Kiểm duyệt liên kết kỹ năng từ bằng chứng đề cương. Chỉ khi đủ dữ liệu mới bật xác minh chương trình và tạo gợi ý chính thức.

Chế độ demo độc lập và được đánh dấu rõ. Không thay dữ liệu thật bằng dữ liệu demo khi đồng bộ lỗi. Thất bại đồng bộ giữ nguyên SQLite và ghi một `sync_job` có `cache_preserved=true`.
