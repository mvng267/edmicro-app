# Milestone 9 — COURSE + GAME + Cổng phụ huynh Implementation Plan

**Trạng thái thực thi:** 🟡 Slice cơ bản (tự chốt 2026-07-21).

> Kế thừa quy ước M0–M8. Ba module thin slice, tái dùng ASSIGN/GRADE/REPORT.

**Goal:** (1) **COURSE** — GV tạo khóa học gồm bài học (text/video/file/flashcard + **nhúng practice/exam**), giao lớp; HS học theo lộ trình, đánh dấu hoàn thành → **% tiến độ**. (2) **GAME** — cộng **điểm** tự động (nộp bài/điểm cao/hoàn thành lesson), **streak** ngày học, **bảng xếp hạng lớp**, **huy hiệu** cơ bản. (3) **Cổng phụ huynh** — tài khoản `parent` xem **báo cáo + điểm của con**.

**Nguồn:** [SRS COURSE](../../04-khoa-hoc/srs-khoa-hoc.md), [SRS GAME](../../13-gamification/srs-gamification.md), [SRS REPORT §5.4](../../09-bao-cao/srs-bao-cao.md).

**Phạm vi cắt (slice sau):** COURSE — Section (chương), video %-đã-xem, flashcard SRS Leitner, preview file, học tuần tự khóa bài, versioning, kho global, chứng chỉ. GAME — thưởng tay, chống spike, BXH tuần/tháng reset + ẩn danh + đóng băng streak, tắt/bật per lớp. PARENT — báo cáo PDF song ngữ, gửi Zalo, nhiều con drill sâu.

---

## Task 1: Migration 0010
- `courses` (name, language, status), `lessons` (course_id, sort_order, title, kind, body, content_ref), `course_classes` (course_id, class_id), `lesson_progress` (student_id, lesson_id, completed_at, UNIQUE).
- `points_ledger` (student_id, points, reason, ref_type, ref_id, created_at, UNIQUE(student_id,reason,ref_id) — chống cộng trùng).
- `badges` (code, name, description) seed vài badge; `student_badges` (student_id, badge_code, earned_at, UNIQUE).
- RLS+grant hết (badges là catalog dùng chung: seed + đọc mọi tenant — để tenant_id nullable, policy cho đọc).

## Task 2: COURSE service + router (TDD)
`course/service.py`: create_course, add_lesson (kind∈text/video/file/flashcard/practice/exam; practice/exam kèm content_ref), assign_to_class, list_courses, get_course (+lessons), list_student_courses (+% tiến độ), complete_lesson (upsert progress → trả % + gọi GAME award). Router: POST /courses, POST /courses/{id}/lessons, POST /courses/{id}/assign, GET /courses, GET /courses/{id}, GET /me/courses, POST /lessons/{id}/complete. RBAC author roles; HS xem khóa lớp mình. Test: tạo khóa+bài+giao → HS thấy; hoàn thành bài → tiến độ tăng.

## Task 3: GAME service + emit + router (TDD)
`game/service.py`: `award(student, points, reason, ref)` (idempotent qua UNIQUE), `total_points`, `current_streak` (ngày liên tiếp có điểm tính đến hôm nay/qua), `class_leaderboard`, `award_badges` (rule: first_submission, streak_7, points_100). Emit: submit practice/exam → +10 (đúng hạn) +5 (điểm≥80); complete lesson → +5. Router: GET /me/points (total+streak+badges), GET /classes/{id}/leaderboard. Test: nộp bài cộng điểm 1 lần (nộp lại không cộng), leaderboard xếp hạng, streak.

## Task 4: Cổng phụ huynh (TDD)
- Link parent–HS: `POST /org/parents/{parent_id}/children/{student_id}` (owner/manager) ghi parent_students.
- `GET /me/children` (parent) → danh sách con.
- Mở rộng scope `GET /reports/students/{id}`: parent xem được con mình (parent_students).
- `GET /me/children/{student_id}/points` cho parent (điểm con). Test: parent xem báo cáo + điểm con; parent khác → 403.

## Task 5: Frontend
- `/khoa-hoc` (GV tạo khóa + thêm bài + giao lớp); `/hoc/khoa-hoc` (HS: khóa của mình + % tiến độ → mở bài → hoàn thành; bài practice/exam link sang làm).
- Điểm/BXH: dashboard HS hiện điểm + streak + badge; `/bang-xep-hang` theo lớp.
- `/phu-huynh` (parent chọn con → báo cáo + điểm). nav theo.

## Task 6: E2E + lint + merge + push
E2E: GV tạo khóa + bài + giao → HS hoàn thành bài → tiến độ + điểm tăng; (nộp bài → điểm; BXH). Lint sạch; merge `m9-course-game-parent`→main; push; roadmap.

## Definition of Done
- Khóa học: tạo/giao/hoàn thành bài → % tiến độ — test + E2E.
- Điểm cộng tự động idempotent + streak + BXH lớp + badge — test.
- Parent xem báo cáo + điểm con, chặn con người khác — test. Lint sạch, merge+push.
