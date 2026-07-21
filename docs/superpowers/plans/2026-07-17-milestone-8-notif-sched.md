# Milestone 8 — NOTIF + SCHED Implementation Plan

**Trạng thái thực thi:** 🟡 Slice cơ bản (tự chốt 2026-07-21).

> Kế thừa quy ước M0–M7. Hai module thin slice, gắn với luồng đã có.

**Goal:** (1) **NOTIF** — thông báo **in-app** (badge chưa đọc) phát theo **catalog sự kiện**, có **adapter kênh** (in-app thật; email/ZNS stub log — nối provider sau); emit ở `assignment_created`, `grade_finalized`, `attendance_absent`, `deadline_reminder`. (2) **SCHED** — buổi học của lớp + **điểm danh** ("cả lớp có mặt rồi chỉnh lệch"); HS xem lịch mình; vắng → phát `attendance_absent`.

**Nguồn:** [SRS NOTIF](../../11-thong-bao/srs-thong-bao.md) §catalog + FR-NOTIF; [SRS SCHED](../../12-lich-hoc-diem-danh/srs-lich-hoc-diem-danh.md) FR-SCHED.

**Phạm vi cắt (slice sau):** email/ZNS/SMS provider thật (M8 chỉ adapter stub + in-app); SSE realtime (M8 poll); preference bật/tắt kênh per tenant; lịch lặp hằng tuần auto-sinh buổi + ngày nghỉ lễ + cảnh báo trùng (M8 tạo buổi lẻ tay); phòng học/online link danh mục; digest; cron nhắc (M8 hàm remind_due gọi tay/test).

---

## Task 1: Migration 0009
- `notifications`: id, tenant_id, user_id, event_code, title, body, entity_type, entity_id, channel default 'in_app', read_at, created_at. Index (tenant,user,read_at). RLS+grant.
- `class_sessions`: id, tenant_id, class_id, starts_at, ends_at, topic, online_link. RLS+grant.
- `attendance`: id, tenant_id, session_id, student_id, status, note, UNIQUE(session_id,student_id). RLS+grant.

## Task 2: NOTIF service + emit + API (TDD)
`notify/channels.py`: adapter in-app (INSERT notifications) + email/zns stub (log). `notify/service.py`: `notify(s, tenant, recipients, event_code, title, body, entity, channels)` (in-app luôn ghi), `list_for_user`, `unread_count`, `mark_read`, `mark_all_read`, `remind_due_assignments(s, tenant, within_hours)` (HS chưa nộp, assignment sắp tới hạn → in-app). Emit hooks: assignment.create_assignment → `assignment_created` cho HS được giao; grading.finalize → `grade_finalized` cho HS. Router `GET /me/notifications`, `GET /me/notifications/unread-count`, `POST /notifications/{id}/read`, `POST /notifications/read-all`. Test: assignment giao → HS có notif chưa đọc; mark read; remind_due tạo notif; đọc của người khác không thấy (RLS).

## Task 3: SCHED service + API (TDD)
`sched/service.py`: `create_session`, `list_class_sessions`, `list_student_sessions`, `mark_attendance(session, [{student_id,status,note}])` (bulk upsert; vắng → emit attendance_absent), `session_attendance`, `student_attendance`. Router: `POST /sessions` (staff scope lớp), `GET /sessions?class_id=`, `GET /me/sessions` (student), `POST /sessions/{id}/attendance`, `GET /sessions/{id}/attendance`. RBAC: teacher/assistant lớp mình (class_staff), owner/manager toàn tenant. Test: tạo buổi + điểm danh (1 vắng → HS đó có notif attendance_absent); HS xem lịch mình; RBAC.

## Task 4: Frontend
- AppShell: chuông + badge chưa đọc (poll unread-count); `/thong-bao` list + đánh dấu đã đọc.
- `/lich-hoc`: staff chọn lớp → tạo buổi + danh sách buổi → điểm danh (mặc định tất cả có mặt, chỉnh lệch) ; student `/hoc/lich` xem buổi sắp tới.
- nav "Thông báo", "Lịch học".

## Task 5: E2E + lint + merge + push
E2E: owner giao bài → HS thấy chuông có badge + /thong-bao có "Bài mới"; owner tạo buổi + điểm danh vắng 1 HS → HS đó có thông báo vắng. Lint sạch; merge `m8-notif-sched`→main; push; roadmap.

## Definition of Done
- Notif in-app phát ở assignment_created + grade_finalized + attendance_absent + deadline_reminder — test.
- Điểm danh bulk (mặc định có mặt, chỉnh lệch); vắng → thông báo — test + E2E.
- Badge chưa đọc + đánh dấu đã đọc — E2E. RBAC/RLS đúng. Lint sạch, merge+push.
