# Từ điển dữ liệu (Data Dictionary)

**Trạng thái:** 🟢 Đã chốt

> Thuộc tính chi tiết các entity **cốt lõi** (các bảng phụ/join đã mô tả đủ trong [ERD](01-erd.md) và SRS module). Quy ước chung cho mọi bảng nghiệp vụ: `id UUID PK`, `tenant_id UUID NOT NULL` (trừ bảng platform/global), `created_at`, `updated_at`. Kiểu thời gian: `timestamptz` (UTC, hiển thị theo múi giờ tenant).

## tenants (platform)

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| slug | text | UNIQUE, immutable | Subdomain `<slug>.edmicro.app` |
| name | text | NOT NULL | Tên trung tâm |
| status | text | `active\|suspended\|archived` | Tạm ngưng chặn đăng nhập toàn tenant |
| settings | jsonb | | logo_file_id, primary_color, timezone (mặc định Asia/Ho_Chi_Minh), school_year, cờ: hiển_thị_điểm_AI, cho_phép_impersonation, bật_gamification |
| single_tenant | bool | default false | true với deploy on-premise |

## users (tenant) & platform_users

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| username | text | UNIQUE per tenant | Đăng nhập; sinh tự động khi import |
| password_hash | text | NOT NULL | Argon2id |
| role | text | users: `owner\|manager\|academic_head\|it_admin\|teacher\|assistant\|student\|parent`; platform_users: `admin\|content_editor\|support_agent` | 1 vai trò/tài khoản |
| status | text | `pending\|active\|locked\|soft_deleted\|anonymized` | Vòng đời [SRS ORG §5.3](../03-to-chuc-nguoi-dung/srs-to-chuc-nguoi-dung.md) |
| full_name / dob / email / phone | text/date | email nullable (HS nhỏ) | Danh tính — xóa khi anonymize |
| parent_phone | text | mã hóa ứng dụng (AES-256-GCM) | Nhận Zalo ZNS/SMS; chỉ manager/teacher sửa |
| must_change_password | bool | default true khi cấp phát | Buộc đổi lần đầu |
| totp_secret | text | nullable, mã hóa | 2FA (bắt buộc platform_users) |
| deleted_at | timestamptz | nullable | Mốc soft-delete (30 ngày → anonymize) |

## classes

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| branch_id | uuid | FK branches | |
| name | text | NOT NULL | |
| language / level | text | | Ngôn ngữ dạy (en/zh/ja/ko) + trình độ |
| capacity | int | nullable | Sĩ số tối đa |
| start_date / end_date | date | | Khoảng chạy lớp — sinh session theo timetable |
| status | text | `upcoming\|active\|finished` | |

`class_staff(class_id, user_id, role: homeroom|teacher|assistant)` · `class_students(class_id, user_id, joined_at, left_at)` — giữ lịch sử chuyển lớp.

`user_scopes(user_id, branch_id NULL=toàn trung tâm, language NULL)` — phạm vi của manager/it_admin (theo chi nhánh) và academic_head (theo ngôn ngữ + chi nhánh tùy chọn). `parent_students(parent_user_id, student_user_id, linked_by, linked_at)` — liên kết phụ huynh ↔ con, UNIQUE cặp.

## questions / question_versions

| Cột (questions) | Kiểu | Mô tả |
|---|---|---|
| tenant_id | uuid NULL | NULL = kho global (`is_global=true`) |
| type | text FK question_types | Mã loại theo [catalog](../99-phu-luc/01-loai-cau-hoi.md) |
| language / skill / level / exam_tag / topic / difficulty | text, int | Bộ tag lọc — index GIN tổng hợp |
| status | text | `draft\|in_review\|published\|archived` |
| group_id | uuid NULL | Question group (passage/audio chung) |
| current_version_id | uuid | Version đang hiệu lực |

| Cột (question_versions) | Kiểu | Mô tả |
|---|---|---|
| content | jsonb | Đề bài theo JSON Schema per type (prompt, options, media, ruby…) |
| answer_key | jsonb NULL | NULL với loại AI/GV chấm |
| explanation | text | Giải thích hiển thị sau làm bài |
| version_no | int | Bất biến sau khi có attempt tham chiếu |

## practices / exams / exam_templates

| Cột (practices) | Kiểu | Mô tả |
|---|---|---|
| skill / language / level | text | 1 kỹ năng chính |
| settings | jsonb | show_answer (`per_question\|after_submit`), time_limit, shuffle, audio_max_plays, retry_wrong_only |
| status | text | `draft\|published\|archived` |

| Cột (exam_templates) | Kiểu | Mô tả |
|---|---|---|
| exam_code | text | `IELTS_A\|IELTS_G\|TOEIC_LR\|TOEIC_SW\|VSTEP\|KET\|PET\|FCE\|HSK1..6\|HSKK_*\|JLPT_N5..N1\|TOPIK_I\|TOPIK_II\|CUSTOM` |
| tenant_id | uuid NULL | NULL = template chuẩn platform |
| scale_config | jsonb | Kiểu quy đổi (`table\|formula\|threshold`), bảng quy đổi, điểm liệt per phần, cấp đạt |
| section_templates | (bảng con) | tên, skill, duration_sec, question_count, allow_back (bool), sort_order |

`exams`: template_id + danh sách `exam_section_questions` ghim `question_version_id`. `exam_sessions`: lịch thi tập trung (class_id, open_at, close_at, join_code, status).

## assignments / assignment_assignees

| Cột (assignments) | Kiểu | Mô tả |
|---|---|---|
| content_kind / content_id | text, uuid | `course\|practice\|exam` |
| class_ids / student_ids | (bảng con assignment_targets) | Lớp / nhóm / cá nhân |
| available_from / due_at | timestamptz | |
| late_policy | text | `allow_late\|lock` |
| attempt_limit | int | NULL = không giới hạn |
| scoring_policy | text | `highest\|latest\|average` |
| show_answers | text | `never\|after_submit\|after_due` |
| grading_mode | text | `auto\|hybrid\|manual` |
| reminder_hours_before | int | default 24; NULL = tắt |
| status | text | `active\|cancelled` |

`assignment_assignees`: (assignment_id, student_id, derived_status `not_opened|in_progress|submitted|graded|overdue`, submitted_at, is_late).

## attempts / answers / submissions

| Cột (attempts) | Kiểu | Mô tả |
|---|---|---|
| assignee_id | uuid FK | NULL nếu tự luyện (practice tự do) |
| kind | text | `practice\|exam` |
| status | text | `in_progress\|submitted\|grading\|graded` |
| started_at / submitted_at | timestamptz | |
| timer_state | jsonb | Đồng hồ server-side per section (exam) |
| behavior_log | jsonb | Rời tab, mất kết nối, thời gian per câu (exam) |

`answers`: (attempt_id, question_version_id, payload jsonb — lựa chọn/text/file_id audio, auto_score numeric NULL, saved_at) — autosave upsert.
`submissions`: chốt 1 attempt; tổng hợp điểm; trạng thái chấm per phần.

## ai_gradings / scores / rubrics

| Cột (ai_gradings) | Kiểu | Mô tả |
|---|---|---|
| submission_id / answer_id | uuid | Chấm mức câu (speaking/writing) |
| provider / model | text | Azure PA, LLM model… |
| result | jsonb | Điểm chỉ số, transcript, nhận xét, raw response |
| confidence | numeric | Ưu tiên hàng đợi review |
| status | text | `queued\|running\|done\|failed\|held_quota` |

`rubrics`: bộ tiêu chí (chuẩn thi hoặc tenant tự tạo); `rubric_criteria`: tên (TA/CC/LR/GRA…), thang, mô tả band.
`scores`: (submission_id, criterion_id NULL với điểm tổng, ai_score, ta_draft_score, final_score, status `ai_draft|ta_draft|final`, graded_by, finalized_at, change_reason).

## Vận hành (tóm tắt cột chính)

| Bảng | Cột chính |
|---|---|
| `sessions` | class_id, date, start/end, room_id, teacher_id, assistant_id, online_link, topic, status `scheduled\|modified\|cancelled\|completed`, origin_session_id (buổi bù) |
| `attendance_records` | session_id, student_id, status `present\|absent\|late\|excused`, note, recorded_by, recorded_at (sửa trong 48h) |
| `notification_events` | type (event catalog), payload, source_module; deliveries per (recipient, channel) với status `queued\|sent\|failed\|delivered`, retry_count, fallback_from |
| `point_transactions` | student_id, rule_code hoặc manual, points, ref (submission/lesson…), period — append-only |
| `student_game_profiles` | total_points, week_points, month_points, streak, longest_streak, freeze_left, nickname, is_anonymous |
| `tenant_plans` | plan_id, valid_from/to, status `active\|grace\|read_only\|archived\|purged` |
| `usage_counters` | tenant_id, month, metric `active_students\|storage_gb\|ai_speaking\|ai_writing\|zns\|sms`, used, limit_snapshot |
| `tickets` | type, priority, status `new\|in_progress\|waiting_user\|resolved\|closed`, context jsonb, assignee_id, sla_due_at, escalated |
| `impersonation_sessions` | agent_id, target_user_id, ticket_id NOT NULL, started_at, expires_at (≤30'), ended_reason |
| `files` | key, original_name, content_type, size, checksum, module, entity_id, uploaded_by, deleted_at |
| `audit_logs` | actor_id, actor_role, tenant_id, action, target_type/id, before/after jsonb, ip, user_agent, at — append-only |
| `activity_logs` | tenant_id (NULL với platform), actor_id, actor_role, on_behalf_of, action, module, entity_type/id/label, diff jsonb (che trường nhạy cảm), ip, user_agent, request_id, at — append-only, partition tháng |

## Chỉ mục & ràng buộc đáng chú ý (mức thiết kế)

- `answers`: UNIQUE (attempt_id, question_version_id) — autosave upsert.
- `attempts`: partial index theo (assignee_id, status='in_progress') — khôi phục phiên nhanh.
- `questions`: GIN theo bộ tag (language, skill, level, exam_tag, topic) — lọc ngân hàng.
- `notification_deliveries`, `point_transactions`, `audit_logs`: partition theo tháng khi dữ liệu lớn (ghi chú cho implement, không bắt buộc v1).
- RLS mọi bảng có `tenant_id`; FORCE ROW LEVEL SECURITY ([Multi-tenant §3](../01-kien-truc/02-multi-tenant.md)).

## Lịch sử thay đổi

| Ngày | Thay đổi | Người |
|---|---|---|
| 2026-07-16 | Tạo bản nháp đầu tiên | Claude |
| 2026-07-16 | Chốt — chuyển trạng thái Đã chốt | Chủ sản phẩm |
| 2026-07-16 | Role enum 11 vai trò; thêm user_scopes + parent_students | Chủ sản phẩm |
| 2026-07-17 | Thêm activity_logs | Chủ sản phẩm + Claude |
