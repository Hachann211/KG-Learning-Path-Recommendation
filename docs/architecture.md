# Kiến trúc và mô hình dữ liệu

Ứng dụng chạy cục bộ, không cần Docker, Neo4j hoặc dịch vụ AI trả phí. Flask phục vụ Jinja2, REST API và toàn bộ tài nguyên tĩnh. SQLite lưu dữ liệu và NetworkX nạp lại đồ thị từ các bảng `knowledge_nodes`, `knowledge_edges` mỗi khi cần tính toán. Không dùng danh sách môn viết cứng theo nghề nghiệp để thay thế thuật toán.

```mermaid
flowchart LR
    UI[Giao diện tiếng Việt<br>Jinja2 · CSS · JavaScript] --> API[Flask REST API<br>CSRF · Student / Admin]
    API --> DB[(SQLite / SQLAlchemy)]
    API --> REC[Bộ gợi ý 10/15]
    REC --> GRAPH[NetworkX MultiDiGraph]
    GRAPH --> DB
    API --> PDF[ReportLab<br>Font tiếng Việt cục bộ]
    API --> SYNC[NEUApiClient / adapters]
    SYNC --> NEU[API NEU đã cấu hình]
    SYNC --> DB
```

Mô hình được thu gọn thành 15 bảng, thay vì sao chép cùng một quan hệ vào nhiều bảng chuyên biệt. Nghề–kỹ năng, môn–kỹ năng, môn–chủ đề, tiên quyết, bài học và chuẩn đầu ra biểu diễn bằng các loại nút và cạnh. Đề cương và nội dung nguyên bản nằm trong JSON `courses.detail`; đây là chủ đích của phiên bản triển khai này, khác mô hình 26 bảng trong bản yêu cầu ban đầu.

```mermaid
erDiagram
    USERS ||--o{ LEARNING_PATHS : saves
    USERS ||--o{ RECOMMENDATION_RUNS : creates
    USERS ||--o{ STUDENT_COURSE_PROGRESS : tracks
    USERS ||--o{ ADMIN_AUDIT_LOGS : audits
    MAJORS ||--o{ CURRICULA : offers
    CURRICULA ||--o{ CURRICULUM_COURSES : contains
    COURSES ||--o{ CURRICULUM_COURSES : belongs
    COURSES ||--o{ STUDENT_COURSE_PROGRESS : progresses
    RECOMMENDATION_RUNS ||--o{ LEARNING_PATHS : saved_as
    KNOWLEDGE_NODES ||--o{ KNOWLEDGE_EDGES : source
    KNOWLEDGE_NODES ||--o{ KNOWLEDGE_EDGES : target
    USERS { int id PK string email UK string password_hash string role json profile }
    CURRICULA { string id PK string major_id FK string cohort string source boolean verified int elective_count int choose_count }
    COURSES { string id PK string code string source int credits string syllabus_id json detail }
    KNOWLEDGE_NODES { string id PK string kind string label json properties }
    KNOWLEDGE_EDGES { int id PK string source_id FK string target_id FK string relation float weight string provenance float confidence boolean approved }
    RECOMMENDATION_RUNS { string id PK int user_id FK json inputs json result }
    LEARNING_PATHS { int id PK int user_id FK string run_id FK string name }
```

`skills`, `careers` quản lý tên, mô tả và từ đồng nghĩa. `sync_jobs` lưu trạng thái đồng bộ và chi tiết từng nguồn. `settings` lưu phiên bản bộ dữ liệu và cấu hình trọng số. Khóa ngoại SQLite được bật tại thời điểm kết nối. Membership chương trình dùng khóa chính kép; cạnh dùng ràng buộc duy nhất `(source_id, target_id, relation)`.

Nút có 8 loại: Major, Curriculum, Course, Topic, Skill, Career, Lesson, LearningOutcome. Cạnh có 9 quan hệ theo bản yêu cầu. Cạnh có `provenance`, `confidence`, `approved`. Chỉ cạnh đã duyệt được sử dụng cho gợi ý.

```mermaid
flowchart TD
    A[Ngành / khóa / nghề / môn đã học] --> B{Xác minh chương trình<br>và đúng nhóm 15 môn?}
    B -- Không --> X[Trả lỗi có lý do<br>Không tự thêm môn]
    B -- Có --> C[Nạp đồ thị từ SQLite]
    C --> D{Tiên quyết có chu trình?}
    D -- Có --> X
    D -- Không --> E[Tính 5 thành phần điểm môn học]
    E --> F[Xét đủ 3.003 tổ hợp 10/15]
    F --> G[Lọc ràng buộc môn đã học<br>và đóng tiên quyết trong nhóm]
    G --> H[Tối đa 0.65 coverage<br>+ 0.25 relevance + 0.10 coherence]
    H --> I[Topological sort<br>Học kỳ dự kiến]
    I --> J[10 môn / 5 môn còn lại<br>đường đi giải thích / PDF]
```

Điểm học phần dùng 45% kỹ năng, 25% chủ đề, 15% đường liên hệ trong đồ thị, 10% kiến thức nền và 5% sở thích. Các trọng số chỉnh được trong Admin. Mức bao phủ kỹ năng của tổ hợp lấy mức hỗ trợ cao nhất trên mỗi kỹ năng, không cộng trùng nhiều môn. Cùng dữ liệu và trọng số cho cùng kết quả; phá hòa bằng thứ tự mã môn.

Các môn tiên quyết bắt buộc ngoài nhóm không tính vào 10 học phần. Trạng thái chưa hoàn thành tiên quyết vẫn hiển thị rõ; lịch chỉ là dự kiến, không cam kết lớp thực tế được mở. Không giả định mọi chương trình chính thức đều áp dụng quy tắc 10/15.
