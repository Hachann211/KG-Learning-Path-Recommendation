# API nội bộ

Phản hồi thành công có dạng `{"data": ...}`; thất bại có dạng `{"error": "Thông báo tiếng Việt"}`. Mã 400 cho dữ liệu sai, 401 cho chưa đăng nhập, 403 cho không có quyền, 404 cho tài nguyên không tồn tại, 409 cho email trùng, 422 cho ràng buộc nghiệp vụ chưa đáp ứng và 502 khi đồng bộ nguồn ngoài thất bại.

Mọi thao tác POST/PATCH/PUT/DELETE cần cookie phiên và header `X-CSRFToken`. Lấy CSRF token từ thẻ `meta[name="csrf-token"]` của trang HTML. Không truyền URL nguồn từ trình duyệt; nguồn được đọc từ `.env`.

| Endpoint | Quyền | Ý nghĩa |
| --- | --- | --- |
| GET `/api/majors` | Công khai | 5 cấu hình ngành/chương trình |
| GET `/api/curricula?major_id=...&cohort=...&source=...` | Công khai | Lọc chương trình, tách nguồn |
| GET `/api/courses?source=...&curriculum_id=...&q=...` | Công khai | Tối đa 250 môn |
| GET `/api/courses/{id}` | Công khai | Chi tiết và nguồn học phần |
| GET `/api/careers`, `/api/careers/{id}`, `/api/skills` | Công khai | Nghề và kỹ năng |
| POST `/api/recommendations` | Công khai | Tạo gợi ý, ghi lại kết quả |
| GET `/api/recommendations/{id}` | Khách tạo hoặc chủ sở hữu | Xem lần tính |
| GET `/api/recommendations/{id}/pdf` | Như trên | PDF tiếng Việt |
| GET `/api/graph?career_id=...&curriculum_id=...` | Công khai | Đồ thị giới hạn theo nghề và chương trình |
| GET `/api/graph/path?career_id=...&course_id=...` | Công khai | Các quan hệ giải thích |
| POST `/api/auth/register` | Công khai | `name`, `email`, `password` |
| POST `/api/auth/login` | Công khai | `email`, `password` |
| POST `/api/auth/logout` | Đăng nhập | Kết thúc phiên |
| GET/PATCH `/api/profile` | Đăng nhập | Hồ sơ; đổi mật khẩu cần `old_password` |
| GET/POST `/api/roadmaps` | Đăng nhập | Danh sách của tôi / lưu `run_id`, `name` |
| GET/PATCH/DELETE `/api/roadmaps/{id}` | Chủ sở hữu | Xem, đổi tên, xóa |
| GET `/api/progress` | Đăng nhập | Tiến độ cá nhân |
| PATCH `/api/progress/{course_id}` | Đăng nhập | `status`: `not_started`, `in_progress`, `completed` |
| GET `/api/admin/stats` | Admin | Thống kê và chu trình |
| POST `/api/admin/sync` | Admin | Đồng bộ `kind=courses` với `q`, hoặc `kind=curricula` với `cohort` |
| GET `/api/admin/sync/status` | Admin | 20 lần đồng bộ gần nhất |
| GET/POST `/api/admin/{kind}` | Admin | Quản lý careers, skills, curricula, majors, nodes, edges |
| PATCH/DELETE `/api/admin/{kind}/{id}` | Admin | Chỉnh sửa / xóa bản ghi theo ràng buộc |
| GET `/api/admin/courses`, `/api/admin/users` | Admin | Danh sách môn/người dùng |
| PATCH `/api/admin/courses/{id}`, `/api/admin/users/{id}` | Admin | Sửa các trường cho phép |
| GET/PUT `/api/admin/curricula/{id}/courses` | Admin | Membership nhóm môn có `items`, `provenance` |
| POST `/api/admin/syllabus/{course_id}` | Admin | Đồng bộ từ `syllabus_id` đã xác minh |
| PATCH `/api/admin/weights` | Admin | 5 trọng số có tổng bằng 1 |

Ví dụ tạo lộ trình:

```json
{
  "curriculum_id": "DEMO-7480201-K66",
  "career_id": "backend",
  "current_semester": 3,
  "completed": ["DEMO-PY"],
  "interests": ["sql"],
  "existing_skills": ["python"]
}
```

Kết quả chứa `run_id`, `candidate_count: 15`, `selected_count: 10`, `items` (cả 15 môn, có `selected`), `ordering`, `coverage`, `credits`, `objective`, `combinations_evaluated: 3003`. Mỗi môn có `score`, `components`, `paths`, `missing_prerequisites`, `proposed_semester` và lý do lựa chọn/không lựa chọn. Điểm là mức liên quan của học phần, không phải xác suất có việc làm hay tỷ lệ hoàn thành.

Ví dụ membership:

```json
{
  "items": [
    {"course_id": "NEU:CNTT1188", "group": "elective"},
    {"course_id": "NEU:TIKT1130", "group": "required"}
  ],
  "provenance": "URL tài liệu chính thức + mục + khóa tuyển sinh"
}
```

Sửa membership đặt lại `verified=false`. Sau khi đối chiếu, quản trị viên mới cập nhật quy tắc của chương trình và xác minh. Không gắn `verified=true` để bỏ qua bước kiểm chứng dữ liệu.
