# Milestone 5 — REPORT cơ bản Implementation Plan

**Trạng thái thực thi:** 🟢 Đã chốt (tự chốt 2026-07-20) — đang thực thi.

> Kế thừa quy ước M0–M4: module `backend/app/modules/report/`; TDD testcontainers; RLS theo tenant + scope theo vai trò; log không cần (chỉ đọc); ruff+import-linter; HeroUI v3; Playwright workers=1; commit nhỏ. **Bài học M3/M4**: unit test có >1 bản ghi; subquery correlate đúng khóa; response_model phải khai báo field mới.

**Goal:** Sau khi có điểm chốt (M4), dựng **báo cáo cấp 1–2**: (1) **học sinh** xem tiến bộ của mình (số bài đã nộp, điểm trung bình, danh sách bài + điểm, drill xuống từng bài); (2) **giáo viên/quản lý** xem **báo cáo lớp** (mỗi HS: đã nộp/được giao, điểm TB; điểm TB lớp, tỉ lệ hoàn thành) với **drill-down lớp → học sinh → bài làm**. → Chạm mốc **"xương sống hoàn tất"**: giao → làm → chấm → **báo cáo**, pilot được.

**Nguồn:** [SRS REPORT](../../09-bao-cao/srs-bao-cao.md) §5.1 (drill-down) + US-REPORT-01..06 cấp 1–2.

**Phạm vi cắt (v2/M8+ sau):** pre-aggregation nightly (M5 đọc trực tiếp bảng nguồn — pilot nhỏ, realtime); báo cáo cấp trung tâm (dashboard chi nhánh, hoạt động GV, nguy cơ bỏ học); xuất PDF/Excel song ngữ; lịch gửi phụ huynh Zalo; phân tích điểm mạnh/yếu theo tag kỹ năng.

---

## Task 1: Report service (TDD)

`app/modules/report/service.py` — đọc trực tiếp từ `assignment_assignees` + `submissions` + `attempts` (RLS lọc tenant):

- `student_report(s, student_id) -> dict`:
  - `summary`: assigned (đếm assignee của HS), submitted (derived_status='submitted'), avg_score (avg submissions.score qua attempt submitted của HS), làm tròn 2.
  - `items`: mỗi bài đã nộp → practice_name, score, correct_count, total_count, submitted_at, attempt_id (drill sang trang kết quả). Sắp theo submitted_at desc.
- `class_report(s, class_id) -> dict`:
  - `students`: mỗi HS đang học (class_students left_at IS NULL) → student_id, full_name, assigned, submitted, avg_score.
  - `summary`: class_avg (avg điểm các submission trong lớp), completion_rate (submitted/assigned toàn lớp), student_count.

Test (`tests/test_report.py`) trên seed ≥2 HS, ≥2 bài (1 HS nộp đúng, 1 HS chưa nộp): student_report đúng summary + items; class_report có đủ HS, HS chưa nộp submitted=0/avg=None, class_avg/ completion_rate đúng. (Nhiều HS để bắt lỗi gộp nhóm.)

## Task 2: Report router + RBAC/scope (TDD)

`app/modules/report/router.py` (prefix `/api/v1`):
- `GET /me/report` — role `student`: `student_report(current.user_id)`.
- `GET /reports/classes/{class_id}` — roles owner/manager/academic_head/teacher/assistant. Scope: teacher/assistant phải có trong `class_staff` của lớp (else 403); owner/manager/academic_head → mọi lớp tenant.
- `GET /reports/students/{student_id}` — cùng roles. Scope: teacher/assistant → HS phải cùng lớp mình dạy (class_staff ∩ class_students); owner/manager/academic_head → mọi HS.
- Helper `_can_access_class`, `_can_access_student`. Đăng ký router vào `app.main`.

Test integration: teacher xem lớp mình dạy OK; teacher lớp khác → 403; student gọi /reports → 403; student /me/report OK; owner xem mọi lớp OK.

## Task 3: Frontend — trang báo cáo

`lib/api.ts`: `myReport()`, `classReport(classId)`, `studentReport(studentId)` + types.
- HS: `/hoc/bao-cao` — thẻ điểm TB + số bài nộp; bảng bài đã làm (điểm, ngày) → mỗi dòng link `/hoc/ket-qua/[attemptId]`. Link "Báo cáo của tôi" ở AppShell/nav cho student.
- GV/quản lý: `/bao-cao` — chọn lớp (dropdown); thẻ điểm TB lớp + tỉ lệ hoàn thành; bảng HS (đã nộp/được giao, điểm TB) → mỗi HS link `/bao-cao/hoc-sinh/[studentId]`.
- `/bao-cao/hoc-sinh/[studentId]` — báo cáo 1 HS (dùng studentReport); mỗi bài link sang… (GV không mở trang kết quả của HS ở M5 — chỉ hiện điểm; drill sang result là v2). Hiển thị bảng bài + điểm.
- Thêm mục nav "Báo cáo" cho vai trò GV/quản lý; "Báo cáo của tôi" cho student.

## Task 4: E2E + lint + merge + push

E2E mở rộng `report.spec.ts` (hoặc nối practice.spec): owner dựng lớp+HS+câu hỏi → giao → HS nộp (đúng) → **owner mở `/bao-cao` chọn lớp → thấy HS + điểm 100 + tỉ lệ hoàn thành** → drill `/bao-cao/hoc-sinh/[id]` thấy bài + điểm. HS mở `/hoc/bao-cao` thấy điểm TB + bài.
- `uv run ruff check . && uv run lint-imports && uv run pytest -q`; frontend `tsc --noEmit` + biome trên file mới; `npx playwright test`.
- Commit nhỏ theo task; merge `m5-report` → main (no-ff); push; cập nhật roadmap đánh dấu M5 + mốc "xương sống hoàn tất".

## Definition of Done

- Student /me/report: summary (assigned/submitted/avg) + items đúng — test.
- Class report: mỗi HS đã/ chưa nộp + điểm TB; class_avg + completion_rate — test.
- RBAC/scope: student↔/me/report; teacher chỉ lớp mình; owner mọi lớp; sai vai trò/scope → 403 — test.
- Frontend: HS xem báo cáo mình; GV xem báo cáo lớp + drill xuống HS — E2E.
- Toàn bộ backend + E2E pass, lint sạch; merge + push; roadmap cập nhật.
