# Milestone 3 — ASSIGN + PRACTICE Implementation Plan

**Trạng thái thực thi:** ✅ HOÀN TẤT 2026-07-17 — 26 backend test + 5 E2E PASS. Bug đã sửa: submit_attempt subquery trả nhiều dòng (lọt unit test vì test tenant 1 assignment; E2E DB nhiều assignment lộ ra) → correlate qua aa.assignment_id. Thêm chọn lớp khi tạo HS + khi giao bài (dev DB nhiều lớp). Cắt sang M4: chấm điểm/kết quả.

> Kế thừa quy ước M0–M2: module `backend/app/modules/{practice,assignment}/`; TDD testcontainers (`session_factory`); RLS + grant `app_user` mọi migration; `log_activity` mọi thao tác ghi; ruff+import-linter sạch; HeroUI v3; Playwright workers=1; commit nhỏ.

**Goal:** Teacher lắp **practice** từ câu hỏi đã publish → **giao cho lớp** kèm deadline → học sinh trong lớp thấy trong "việc cần làm", **làm bài (autosave từng câu)** và **nộp**. Học sinh chỉ truy cập bài của mình; vào lớp muộn vẫn nhận assignment còn hạn.

**Nguồn:** [SRS PRACTICE](../../05-practice/srs-practice.md), [SRS ASSIGN](../../07-giao-bai/srs-giao-bai.md).

**Phạm vi cắt (M4+ sau):** chấm điểm (M4 = GRADE — M3 chỉ lưu câu trả lời + nộp, chưa tính điểm/kết quả); speaking/writing (ghi âm/AI); attempt limit nhiều lần (M3 = 1 attempt/assignee); recurring assignment; nhắc deadline qua NOTIF (M8); question_groups/passage.

---

## Task 1: Migration 0005 — practice + assignment + attempt/answer + RLS

Bảng (RLS FORCE + policy + grant app_user, đều có tenant_id):
- `practices`: id, tenant_id, name, skill, language, level, settings jsonb default '{}', status text default 'published', created_by, created_at/updated_at.
- `practice_questions`: id, tenant_id, practice_id FK, question_version_id uuid (ghim version), sort_order int. UNIQUE (practice_id, sort_order).
- `assignments`: id, tenant_id, content_kind text default 'practice', content_id uuid, class_id uuid, available_from timestamptz null, due_at timestamptz null, late_policy text default 'allow_late', status text default 'active', created_by, created_at.
- `assignment_assignees`: id, tenant_id, assignment_id FK, student_id uuid, derived_status text default 'not_opened' ('not_opened'|'in_progress'|'submitted'|'overdue'), submitted_at, is_late boolean default false. UNIQUE (assignment_id, student_id).
- `attempts`: id, tenant_id, assignee_id FK, kind text default 'practice', status text default 'in_progress' ('in_progress'|'submitted'), started_at default now(), submitted_at.
- `answers`: id, tenant_id, attempt_id FK, question_version_id uuid, payload jsonb, saved_at default now(). UNIQUE (attempt_id, question_version_id).

Verify: `alembic upgrade head` sạch dev; conftest tự chạy migration.

## Task 2: Practice service + router (TDD)

`app/modules/practice/`:
- `create_practice(s, tenant, creator, {name, skill, language, question_ids: [str]})`: với mỗi question_id lấy `current_version_id` (chỉ câu status='published' của tenant); tạo practice + practice_questions theo thứ tự. Câu chưa publish/không tồn tại → `InvalidQuestion`.
- `list_practices(s)`; `get_practice_for_edit(s, id)` (kèm câu hỏi + đáp án); `get_practice_for_attempt(s, id)` (câu hỏi **ẩn answer_key** — student view).
- Router `/api/v1/practices`: POST (author roles owner/manager/academic_head/teacher — 403 khác), GET list, GET /{id}.

Test: tạo practice từ 2 câu published OK; thêm câu chưa publish → 422; get_for_attempt không có answer_key; RLS.

## Task 3: Assignment service + router (TDD)

`app/modules/assignment/`:
- `create_assignment(s, tenant, creator, {content_id practice, class_id, due_at})`: tạo assignment + **fan-out** assignment_assignees cho mọi học sinh đang trong lớp (class_students left_at IS NULL); log.
- `list_student_assignments(s, student_id)`: các assignment active của lớp học sinh + trạng thái + due_at + tên practice; **tính overdue** nếu quá hạn chưa nộp.
- `enroll_backfill(s, class_id, student_id)`: khi thêm HS vào lớp (gọi từ ORG add_student sau này — M3 chỉ hàm + test), gán các assignment active còn hạn. **M3: chỉ test hàm, chưa nối vào ORG** (ghi chú).
- Router `/api/v1/assignments`: POST (author roles), GET `/api/v1/me/assignments` (student — bài của mình).

Test: giao practice cho lớp 2 HS → 2 assignee; student list thấy 1 assignment; quá hạn → derived_status overdue.

## Task 4: Attempt + answer service + router (TDD)

`app/modules/practice/attempt_service.py`:
- `start_attempt(s, tenant, assignee_id, student_id)`: kiểm tra assignee thuộc student; tạo attempt (hoặc trả attempt in_progress hiện có — 1 attempt/assignee); set assignee derived_status='in_progress'.
- `save_answer(s, attempt_id, question_version_id, payload)`: **upsert** (ON CONFLICT update payload + saved_at). Chỉ khi attempt in_progress.
- `submit_attempt(s, attempt_id)`: set status='submitted' + submitted_at; assignee derived_status='submitted', is_late nếu quá due_at.
- Router: POST `/api/v1/assignments/{aid}/start` (student, trả attempt_id + câu hỏi ẩn đáp án), PUT `/api/v1/attempts/{id}/answers` (student chủ attempt, autosave), POST `/api/v1/attempts/{id}/submit`. Chặn student thao tác attempt không phải của mình (403).

Test: student start → attempt; save 2 answers (upsert lần 2 không tạo trùng); submit đổi trạng thái; student khác truy cập attempt → 403.

## Task 5: Frontend

- Teacher: trang `/practices` — tạo practice (chọn câu đã publish qua checkbox từ danh sách + đặt tên) + nút "Giao cho lớp" (chọn lớp + deadline).
- Student: trang `/hoc/todo` — danh sách việc cần làm (assignment) + nút "Làm bài" → trang làm bài `/hoc/lam-bai/[assignmentId]`: hiện từng câu, chọn/điền đáp án, **autosave** (PUT sau mỗi thay đổi, hiện "Đã lưu"), nút Nộp bài.
- Menu theo vai trò: teacher thấy Practices; student thấy "Việc cần làm" (shell tối giản cho student).
- `lib/api.ts`: practices + assignments + attempt endpoints.

## Task 6: E2E + hoàn tất

- E2E: owner login → tạo chi nhánh/lớp → tạo học sinh trong lớp (lấy mật khẩu) → tạo câu hỏi publish → tạo practice (chọn câu) → giao practice cho lớp (deadline tương lai) → logout → student login → thấy việc cần làm → làm bài (chọn đáp án, thấy "Đã lưu") → nộp → trạng thái "đã nộp".
- ruff + import-linter + full pytest xanh; biome; commit; merge main; push.

## Definition of Done (M3)

- [ ] Migration 0005 áp sạch; RLS 6 bảng.
- [ ] Practice ghim question_version; get_for_attempt ẩn đáp án (test).
- [ ] Giao bài fan-out đúng số học sinh; student chỉ thấy bài của mình (test + RLS).
- [ ] Autosave upsert (không tạo answer trùng) + submit đổi trạng thái (test).
- [ ] Student không truy cập được attempt của người khác (403 test).
- [ ] E2E đầy đủ luồng giao→làm→nộp PASS.
- [ ] CI xanh; merged main; push.

## Lịch sử thay đổi

| Ngày | Thay đổi | Người |
|---|---|---|
| 2026-07-17 | Tạo + tự chốt plan M3 | Claude |
