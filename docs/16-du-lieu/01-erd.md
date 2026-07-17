# ERD — Mô hình dữ liệu tổng

**Trạng thái:** 🟢 Đã chốt

> ERD mức thiết kế (chưa phải schema SQL cuối). Quy ước: mọi bảng nghiệp vụ có `tenant_id` (RLS) + `id UUID` + `created_at/updated_at` — không vẽ lại trong sơ đồ. Bảng platform (không RLS): `tenants`, `plans`, `tenant_plans`, `platform_users`, `question_types`, `point_rules`, `badges`, `exam_templates` chuẩn, `faq_articles`. Thuộc tính chi tiết ở [Từ điển dữ liệu](02-tu-dien-du-lieu.md); danh sách đầy đủ ~70 bảng ở [Danh mục bảng](03-danh-muc-bang.md).

## 1. Toàn cảnh quan hệ giữa các nhóm

```mermaid
flowchart LR
  ORG[ORG - to chuc va nguoi dung] --> ASSIGN[ASSIGN - giao bai]
  CONTENT[CONTENT - ngan hang cau hoi] --> PRACTICE[PRACTICE va EXAM - bai tap va de thi]
  CONTENT --> COURSE[COURSE - khoa hoc]
  COURSE --> ASSIGN
  PRACTICE --> ASSIGN
  ASSIGN --> ATT[Attempt - Submission - Answer]
  ATT --> GRADE[GRADE - cham bai]
  GRADE --> REPORT[REPORT - bao cao]
  ORG --> SCHED[SCHED - lich va diem danh] --> REPORT
  GRADE --> GAME[GAME - gamification]
  PLAN[PLAN - goi va quota] --> ORG
  NOTIF[NOTIF - thong bao] -.nghe su kien tu moi module.- ASSIGN
  SUPPORT[SUPPORT - ho tro] -.doc ngu canh.- ORG
```

## 2. Tổ chức & người dùng (ORG)

```mermaid
erDiagram
  TENANTS ||--o{ BRANCHES : co
  TENANTS ||--o{ USERS : co
  BRANCHES ||--o{ ROOMS : co
  BRANCHES ||--o{ CLASSES : co
  CLASSES ||--o{ CLASS_STAFF : "GV - TA"
  CLASSES ||--o{ CLASS_STUDENTS : "enrollment"
  USERS ||--o{ CLASS_STAFF : ""
  USERS ||--o{ CLASS_STUDENTS : ""
  USERS ||--o| CONSENTS : "HS duoi 16"
  USERS ||--o{ USER_SCOPES : "pham vi manager-it_admin-academic_head"
  BRANCHES ||--o{ USER_SCOPES : ""
  USERS ||--o{ PARENT_STUDENTS : "phu huynh"
  PARENT_STUDENTS }o--|| USERS : "hoc sinh"
  CLASSES ||--o{ CLASS_DELEGATIONS : "uy quyen TA"
  TENANTS ||--o{ IMPORT_JOBS : ""
  IMPORT_JOBS ||--o{ IMPORT_ROWS : ""

  USERS {
    uuid id PK
    uuid tenant_id FK
    string username UK
    string role "owner|manager|academic_head|it_admin|teacher|assistant|student|parent"
    string status "pending|active|locked|soft_deleted|anonymized"
    string full_name
    date dob
    string parent_phone "ma hoa ung dung"
    string email "nullable"
  }
  CLASSES {
    uuid id PK
    uuid branch_id FK
    string name
    string language "en|zh|ja|ko"
    string level
    string status "upcoming|active|finished"
  }
```

`platform_users` tách riêng cho vai trò platform (admin, content_editor, support_agent) — không thuộc tenant.

## 3. Nội dung (CONTENT)

```mermaid
erDiagram
  QUESTION_TYPES ||--o{ QUESTIONS : "phan loai"
  QUESTIONS ||--o{ QUESTION_VERSIONS : "versioning"
  QUESTION_GROUPS ||--o{ QUESTIONS : "passage-audio chung"
  QUESTION_VERSIONS }o--o{ MEDIA_ASSETS : "audio - anh"
  CONTENT_PACKS ||--o{ CONTENT_PACK_ITEMS : ""
  CONTENT_PACK_ITEMS }o--|| QUESTIONS : ""
  PLANS ||--o{ PLAN_CONTENT_PACKS : "phan phoi theo goi"
  PLAN_CONTENT_PACKS }o--|| CONTENT_PACKS : ""

  QUESTIONS {
    uuid id PK
    uuid tenant_id FK "NULL neu global"
    bool is_global
    string type FK
    string language
    string skill "listening|speaking|reading|writing"
    string level
    string exam_tag "IELTS|TOEIC|HSK|..."
    string topic
    int difficulty "1-5"
    string status "draft|in_review|published|archived"
    uuid current_version_id FK
  }
  QUESTION_VERSIONS {
    uuid id PK
    uuid question_id FK
    jsonb content "theo JSON Schema cua type"
    jsonb answer_key
    text explanation
    int version_no
  }
```

## 4. Khóa học (COURSE)

```mermaid
erDiagram
  COURSES ||--o{ COURSE_VERSIONS : ""
  COURSE_VERSIONS ||--o{ COURSE_SECTIONS : chuong
  COURSE_SECTIONS ||--o{ LESSONS : ""
  LESSONS ||--o{ CONTENT_BLOCKS : ""
  CONTENT_BLOCKS ||--o{ FLASHCARDS : "khi type=flashcard_set"
  CONTENT_BLOCKS }o--o| FILES : "video - tai lieu"
  CONTENT_BLOCKS }o--o| PRACTICES : "khi type=practice_ref"
  CONTENT_BLOCKS }o--o| EXAMS : "khi type=exam_ref"
  FLASHCARDS ||--o{ FLASHCARD_REVIEW_STATES : "Leitner per HS"
  CONTENT_BLOCKS ||--o{ BLOCK_PROGRESS : "per HS"
  LESSONS ||--o{ LESSON_PROGRESS : ""
  COURSES ||--o{ COURSE_PROGRESS : ""

  CONTENT_BLOCKS {
    uuid id PK
    uuid lesson_id FK
    string type "video|rich_text|flashcard_set|document|practice_ref|exam_ref"
    jsonb payload
    int sort_order
  }
```

## 5. Practice & Exam

```mermaid
erDiagram
  PRACTICES ||--o{ PRACTICE_QUESTIONS : "lap rap tu ngan hang"
  PRACTICE_QUESTIONS }o--|| QUESTION_VERSIONS : "ghim version"
  EXAM_TEMPLATES ||--o{ EXAM_SECTION_TEMPLATES : ""
  EXAM_TEMPLATES ||--o{ SCORE_CONVERSIONS : "quy doi thang diem"
  EXAMS }o--|| EXAM_TEMPLATES : "tao tu template"
  EXAMS ||--o{ EXAM_SECTIONS : ""
  EXAM_SECTIONS ||--o{ EXAM_SECTION_QUESTIONS : ""
  EXAM_SECTION_QUESTIONS }o--|| QUESTION_VERSIONS : "ghim version"
  EXAMS ||--o{ EXAM_SESSIONS : "lich thi tap trung"

  PRACTICES {
    uuid id PK
    uuid tenant_id FK "NULL neu global"
    string skill
    string language
    string level
    jsonb settings "dap an - thoi gian - so lan"
    string status
  }
  EXAM_TEMPLATES {
    uuid id PK
    string exam_code "IELTS_A|TOEIC_LR|HSK4|JLPT_N3|TOPIK_II|VSTEP|CUSTOM"
    uuid tenant_id FK "NULL neu chuan platform"
    jsonb scale_config "thang diem - diem liet"
  }
```

## 6. Giao bài → làm bài → chấm (ASSIGN · GRADE)

```mermaid
erDiagram
  ASSIGNMENTS ||--o{ ASSIGNMENT_ASSIGNEES : "fan-out per HS"
  ASSIGNMENTS }o--o| ASSIGNMENT_RECURRENCES : "giao lap lai"
  ASSIGNMENT_ASSIGNEES ||--o{ ATTEMPTS : "luot lam"
  ATTEMPTS ||--|| SUBMISSIONS : "khi nop"
  ATTEMPTS ||--o{ ANSWERS : "per cau hoi - autosave"
  SUBMISSIONS ||--o{ AI_GRADINGS : "ket qua AI + raw"
  SUBMISSIONS ||--o{ SCORES : "per tieu chi rubric"
  RUBRICS ||--o{ RUBRIC_CRITERIA : ""
  SCORES }o--|| RUBRIC_CRITERIA : ""
  SUBMISSIONS ||--o{ AI_USAGE_LEDGER : "tru quota"

  ASSIGNMENTS {
    uuid id PK
    uuid tenant_id FK
    string content_kind "course|practice|exam"
    uuid content_id
    timestamptz available_from
    timestamptz due_at
    string late_policy "allow_late|lock"
    int attempt_limit
    string scoring_policy "highest|latest|average"
    string grading_mode "auto|hybrid|manual"
  }
  ATTEMPTS {
    uuid id PK
    uuid assignee_id FK
    string kind "practice|exam"
    string status "in_progress|submitted|grading|graded"
    timestamptz started_at
    jsonb timer_state "dong ho server-side"
  }
  SCORES {
    uuid id PK
    uuid submission_id FK
    uuid criterion_id FK "NULL voi diem tong"
    numeric ai_score "de xuat"
    numeric final_score "GV chot"
    string status "ai_draft|ta_draft|final"
    uuid graded_by FK
  }
```

## 7. Vận hành (SCHED · NOTIF · GAME · PLAN · SUPPORT)

```mermaid
erDiagram
  TIMETABLE_RULES ||--o{ SESSIONS : "sinh buoi hoc"
  SESSIONS ||--o{ ATTENDANCE_RECORDS : "per HS"
  HOLIDAYS ||..o{ SESSIONS : "danh dau huy"

  NOTIFICATION_EVENTS ||--o{ NOTIFICATIONS : "in-app per nguoi nhan"
  NOTIFICATION_EVENTS ||--o{ NOTIFICATION_DELIVERIES : "per kenh"
  NOTIFICATION_TEMPLATES ||..o{ NOTIFICATION_DELIVERIES : render
  ZNS_TEMPLATE_MAPS ||..o{ NOTIFICATION_DELIVERIES : "kenh zalo"

  POINT_RULES ||..o{ POINT_TRANSACTIONS : ""
  POINT_TRANSACTIONS }o--|| STUDENT_GAME_PROFILES : "cong don"
  BADGES ||--o{ STUDENT_BADGES : trao
  LEADERBOARD_SNAPSHOTS ||..|| STUDENT_GAME_PROFILES : "chot chu ky"

  PLANS ||--o{ TENANT_PLANS : "hop dong"
  TENANT_PLANS ||--o{ TENANT_PLAN_OVERRIDES : ""
  TENANT_PLANS ||..o{ USAGE_COUNTERS : "doi chieu"
  USAGE_COUNTERS ||--o{ USAGE_DAILY_SNAPSHOTS : ""
  USAGE_COUNTERS ||--o{ QUOTA_ALERTS : ""

  TICKETS ||--o{ TICKET_COMMENTS : ""
  TICKETS ||--o{ TICKET_ATTACHMENTS : ""
  TICKETS ||--o{ IMPERSONATION_SESSIONS : "dieu kien bat buoc"
```

## 8. Bảng dùng chung

| Bảng | Vai trò | Ghi chú |
|---|---|---|
| `files` | Nguồn chân lý mọi file trên object storage | key, original_name, checksum, module, entity_id — [Lưu trữ file](../01-kien-truc/04-luu-tru-file.md) |
| `audit_logs` | Nhật ký bất biến (hành động nhạy cảm) | append-only — [Bảo mật §6](../01-kien-truc/03-bao-mat.md) |
| `activity_logs` | Nhật ký hoạt động MỌI thao tác ghi (ai sửa gì, diff before/after) | append-only, partition theo tháng — [SRS Quản trị log](../18-quan-tri-log/srs-quan-tri-log.md) |
| `activity_daily_stats` | Pre-aggregate usage theo vai trò/module/ngày | rebuild được từ activity_logs |
| `jobs` (queue metadata) | Trạng thái job nền tra cứu được | chấm AI, gửi thông báo, import, export |

## 9. Nguyên tắc thiết kế dữ liệu

1. **Ghim version**: attempt/answer tham chiếu `question_version_id` (không phải question) — sửa câu hỏi không đổi điểm hồi tố. Tương tự course_version.
2. **Điểm 2 tầng**: `ai_score` (đề xuất) và `final_score` (GV chốt) tách cột — báo cáo chỉ dùng final; hiệu chuẩn dùng cả hai.
3. **Append-only cho dữ liệu tiền/điểm/audit**: `point_transactions`, `ai_usage_ledger`, `audit_logs` không update/delete.
4. **Pre-aggregate tách bảng riêng** (nhóm `*_stat`) — rebuild được từ dữ liệu gốc bất kỳ lúc nào.
5. **JSONB có schema**: `question_versions.content`, `content_blocks.payload`, `exam_templates.scale_config` validate bằng JSON Schema ở tầng ứng dụng.
6. **Soft-delete + ẩn danh**: user và file có `deleted_at`; ẩn danh hóa giữ khóa ngoại (điểm/attempt không gãy) nhưng xóa danh tính.

## Lịch sử thay đổi

| Ngày | Thay đổi | Người |
|---|---|---|
| 2026-07-16 | Tạo bản nháp đầu tiên | Claude |
| 2026-07-16 | Chốt — chuyển trạng thái Đã chốt | Chủ sản phẩm |
| 2026-07-16 | Thêm role enum 8 giá trị tenant, bảng user_scopes (phạm vi chi nhánh/tổ) và parent_students | Chủ sản phẩm |
| 2026-07-17 | Thêm activity_logs + activity_daily_stats | Chủ sản phẩm + Claude |
