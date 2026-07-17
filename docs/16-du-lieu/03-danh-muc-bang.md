# Danh mục bảng đầy đủ theo module

**Trạng thái:** 🟢 Đã chốt

> Danh mục **toàn bộ bảng** của hệ thống, gom theo module sở hữu — tổng hợp từ mục "Entity liên quan" của 15 SRS. Bổ sung cho [ERD](01-erd.md) (quan hệ) và [Từ điển dữ liệu](02-tu-dien-du-lieu.md) (cột chi tiết các bảng cốt lõi). Đây là mức **thiết kế** — schema SQL thật (kiểu dữ liệu, index, RLS policy đầy đủ) viết bằng Alembic migration khi implement, lấy file này làm checklist.
>
> Quy ước: mọi bảng có `id UUID PK, created_at, updated_at`; cột **RLS** = có `tenant_id` + row-level security. "Global" = bảng platform, không RLS.

## Bảng platform (không RLS)

| Bảng | Mục đích | Ghi chú |
|---|---|---|
| `tenants` | Trung tâm (khách hàng B2B) | slug subdomain unique; settings jsonb |
| `platform_users` | Tài khoản admin / content_editor / support_agent | 2FA bắt buộc |
| `plans` | Định nghĩa gói dịch vụ + hạn mức + feature flags | |
| `plan_content_packs` | Gói ↔ bộ nội dung global được truy cập | |
| `question_types` | Catalog ~24 loại câu hỏi + JSON Schema validate | [Phụ lục](../99-phu-luc/01-loai-cau-hoi.md) |
| `exam_templates` (chuẩn) | Template kỳ thi chuẩn platform (tenant_id NULL) | tenant tạo template riêng → có tenant_id |
| `point_rules` | Quy tắc cộng điểm gamification (cấp platform) | |
| `badges` | Catalog huy hiệu | |
| `faq_articles` | Bài hướng dẫn/FAQ | admin quản lý (đã chốt SUPPORT #3) |

## ORG — Tổ chức & người dùng (RLS)

| Bảng | Mục đích | Ghi chú |
|---|---|---|
| `users` | Tài khoản tenant — 8 vai trò | role enum; parent_phone mã hóa; trạng thái vòng đời |
| `branches` / `rooms` | Chi nhánh / phòng học | rooms dùng cho SCHED |
| `classes` | Lớp học | thuộc 1 branch; language + level |
| `class_staff` | Gán GV/TA vào lớp | role trong lớp: homeroom/teacher/assistant |
| `class_students` | Enrollment học sinh ↔ lớp | joined_at/left_at — giữ lịch sử chuyển lớp |
| `class_delegations` | Ủy quyền trợ giảng per lớp (4 nhóm quyền) | AUTH FR-05 |
| `user_scopes` | Phạm vi manager/it_admin (chi nhánh) + academic_head (ngôn ngữ) | branch_id NULL = toàn trung tâm |
| `parent_students` | Liên kết phụ huynh ↔ con | UNIQUE cặp; linked_by |
| `consents` | Consent phụ huynh cho HS <16 tuổi | trạng thái + scan đính kèm |
| `import_jobs` / `import_rows` | Phiên import Excel + kết quả từng dòng | tự hủy sau 24h nếu chưa commit |

## CONTENT — Ngân hàng câu hỏi (RLS; global khi tenant_id NULL)

| Bảng | Mục đích | Ghi chú |
|---|---|---|
| `questions` | Câu hỏi + bộ tag (ngôn ngữ/kỹ năng/level/kỳ thi/chủ đề/độ khó) | is_global; GIN index tag |
| `question_versions` | Nội dung JSONB + đáp án per version | bất biến khi có attempt tham chiếu |
| `question_groups` | Nhóm câu chung passage/audio | |
| `content_packs` / `content_pack_items` | Bộ nội dung global để phân phối theo gói | |
| `review_logs` | Lịch sử duyệt nội dung (4 mắt) | |
| `tenant_content_settings` | Cờ "cần duyệt" per tenant | owner bật/tắt |

## COURSE — Khóa học (RLS)

| Bảng | Mục đích | Ghi chú |
|---|---|---|
| `courses` / `course_versions` | Khóa học + versioning đơn giản | HS đang học giữ version cũ |
| `course_sections` / `lessons` | Chương / bài học | |
| `content_blocks` | Khối nội dung 6 loại trong bài học | payload jsonb theo loại |
| `flashcards` / `flashcard_review_states` | Thẻ ghi nhớ + trạng thái Leitner per HS | chu kỳ 1/2/4 ngày (đã chốt) |
| `block_progress` / `lesson_progress` / `course_progress` | Tiến độ 3 cấp per HS | course/lesson là giá trị tổng hợp lưu sẵn |

## PRACTICE & EXAM (RLS)

| Bảng | Mục đích | Ghi chú |
|---|---|---|
| `practices` / `practice_questions` | Bài luyện + câu hỏi lắp ráp (ghim version) | |
| `exams` / `exam_sections` / `exam_section_questions` | Đề thi cụ thể theo template | ghim question_version |
| `exam_section_templates` | Phần thi của template (thời gian, số câu, allow_back) | |
| `score_conversions` | Bảng quy đổi raw → thang chuẩn | 3 kiểu: table/formula/threshold |
| `exam_sessions` | Lịch thi tập trung (phòng chờ, mã vào) | |

## ASSIGN — Giao bài (RLS)

| Bảng | Mục đích | Ghi chú |
|---|---|---|
| `assignments` | Lượt giao bài + cấu hình (deadline, attempt, chấm) | khóa cấu hình điểm sau khi có bài nộp (đã chốt) |
| `assignment_targets` | Đối tượng giao: lớp / nhóm / cá nhân | |
| `assignment_assignees` | Fan-out per học sinh + trạng thái dẫn xuất | |
| `assignment_recurrences` | Mẫu giao lặp hằng tuần | sinh trước 24h dạng nháp (đã chốt) |

## GRADE — Chấm bài (RLS)

| Bảng | Mục đích | Ghi chú |
|---|---|---|
| `attempts` | Lượt làm bài (practice/exam) + timer server + behavior log | |
| `answers` | Câu trả lời per câu hỏi — autosave upsert | UNIQUE (attempt, question_version) |
| `submissions` | Bài nộp chốt của attempt | |
| `ai_gradings` | Kết quả AI (điểm, transcript, raw JSON, confidence) | giữ theo retention audit |
| `scores` | Điểm per tiêu chí: ai_score / ta_draft / final | change_reason khi sửa sau chốt |
| `rubrics` / `rubric_criteria` | Thang chấm chuẩn thi + tenant tự tạo | |
| `ai_usage_ledger` | Sổ trừ quota chấm AI — append-only | |

## REPORT — Báo cáo (RLS)

| Bảng | Mục đích | Ghi chú |
|---|---|---|
| `student_skill_stats` / `student_tag_stats` | Pre-aggregate per HS × kỹ năng / tag | rebuild được |
| `class_assignment_stats` / `tenant_daily_stats` / `teacher_activity_stats` | Pre-aggregate lớp / tenant / giáo viên | |
| `report_exports` | Job xuất PDF/Excel | |
| `parent_report_schedules` / `parent_report_logs` | Lịch gửi + log gửi báo cáo phụ huynh | |
| `report_settings` | Ngưỡng rule cần-chú-ý / nguy-cơ-bỏ-học per tenant | |

## NOTIF — Thông báo (RLS)

| Bảng | Mục đích | Ghi chú |
|---|---|---|
| `notification_events` | Sự kiện phát (catalog ~28 sự kiện × 11 vai trò) | |
| `notifications` | Bản ghi in-app per người nhận | retention 90 ngày (đã chốt) |
| `notification_deliveries` | Trạng thái gửi per kênh + retry + fallback | partition tháng khi lớn |
| `notification_templates` / `zns_template_maps` | Template nội dung / map template Zalo đã duyệt | |
| `notification_preferences` | Preference user theo nhóm sự kiện × kênh | |
| `tenant_channel_configs` | SMTP, token Zalo OA (mã hóa), SMS provider per tenant | owner quản lý |
| `notification_usage` | Bộ đếm ZNS/SMS theo tenant/tháng | đối chiếu PLAN |

## SCHED — Lịch học & điểm danh (RLS)

| Bảng | Mục đích | Ghi chú |
|---|---|---|
| `timetable_rules` | Lịch lặp hằng tuần của lớp | |
| `sessions` | Buổi học cụ thể (kể cả buổi bù) | link online dán tay |
| `holidays` | Ngày nghỉ lễ per tenant | |
| `attendance_records` | Điểm danh per buổi × HS | sửa trong 48h; manager sửa sau đó có audit (đã chốt) |

## GAME — Gamification (RLS)

| Bảng | Mục đích | Ghi chú |
|---|---|---|
| `point_transactions` | Giao dịch điểm — append-only | partition tháng khi lớn |
| `student_game_profiles` | Points, streak, freeze, nickname per HS | |
| `student_badges` | Badge đã trao | |
| `leaderboard_snapshots` | Chốt BXH cuối chu kỳ | |
| `gamification_settings` | Bật/tắt per tenant (owner) / per lớp | |
| `point_anomaly_flags` | Cảnh báo spike điểm | |

## PLAN — Gói dịch vụ (platform + RLS hỗn hợp)

| Bảng | Mục đích | Ghi chú |
|---|---|---|
| `tenant_plans` | Hợp đồng: gói, thời hạn, vòng đời active→grace→read_only→purged | platform |
| `tenant_plan_overrides` | Override hạn mức riêng + grant nới tạm | platform |
| `usage_counters` / `usage_daily_snapshots` | Bộ đếm usage theo tenant/tháng + snapshot ngày | realtime ở Redis, chốt về Postgres |
| `quota_alerts` | Ngưỡng đã cảnh báo (chống lặp) | |
| `ai_grading_holds` | Hàng chờ bài chấm AI giữ vì hết quota (FIFO) | |

## SUPPORT — Hỗ trợ (platform + tenant)

| Bảng | Mục đích | Ghi chú |
|---|---|---|
| `tickets` / `ticket_comments` / `ticket_attachments` | Ticket + trao đổi + đính kèm | context jsonb tự động |
| `impersonation_sessions` | Phiên đăng nhập thay (≤30', gắn ticket) | |
| `tenant_support_settings` | Cờ cho phép impersonation per tenant | owner quản lý |

## LOG — Nhật ký (RLS; platform khi tenant_id NULL)

| Bảng | Mục đích | Ghi chú |
|---|---|---|
| `activity_logs` | Mọi thao tác ghi: actor, action, entity, diff before/after | append-only, **partition tháng từ v1** |
| `activity_daily_stats` | Pre-aggregate usage theo vai trò/module/ngày | |
| `audit_logs` | Hành động nhạy cảm — tập con nghiêm ngặt | append-only, ≥24 tháng |

## Dùng chung

| Bảng | Mục đích | Ghi chú |
|---|---|---|
| `files` | Nguồn chân lý mọi file object storage | key theo prefix tenant; soft-delete |
| `jobs` | Metadata job nền tra cứu được (chấm AI, import, export, gửi tin) | support tra cứu |

## Tổng hợp & quy tắc kiểm tra khi implement

- **~70 bảng**, trong đó 9 bảng platform thuần, còn lại RLS theo tenant.
- Checklist mỗi migration: (1) có `tenant_id` + RLS + FORCE nếu là bảng nghiệp vụ; (2) bảng append-only không có UPDATE/DELETE grant; (3) bảng ghi nhiều (`activity_logs`, `notification_deliveries`, `point_transactions`, `answers`) cân nhắc partition; (4) khớp tên với danh mục này — lệch thì cập nhật doc trước.

## Lịch sử thay đổi

| Ngày | Thay đổi | Người |
|---|---|---|
| 2026-07-17 | Tổng hợp danh mục bảng từ 15 SRS theo yêu cầu hoàn thiện tài liệu database | Claude |
| 2026-07-17 | Chốt — chuyển trạng thái Đã chốt | Chủ sản phẩm |
