# Milestone 4 — GRADE tự động Implementation Plan

**Trạng thái thực thi:** 🟢 Đã chốt (tự chốt 2026-07-17) — đang thực thi.

> Kế thừa quy ước M0–M3: module `backend/app/modules/grading/`; TDD testcontainers; RLS + grant; log_activity; ruff+import-linter; HeroUI v3; Playwright workers=1; commit nhỏ. **Bài học M3**: unit test có >1 bản ghi để bắt lỗi cardinality; subquery correlate đúng khóa.

**Goal:** Khi học sinh **nộp bài**, hệ thống **chấm tự động câu đóng** (mcq_single so đáp án đúng; fill_blank so đáp án chấp nhận, bỏ hoa/thường) → tạo **submission** (số câu đúng / tổng / % điểm) và đánh dấu đúng/sai từng câu. Học sinh **xem kết quả** + **xem lại từng câu** (đáp án của mình, đáp án đúng, giải thích). → Chạm mốc "xương sống demo được đầu-cuối".

**Nguồn:** [SRS GRADE](../../08-cham-bai/srs-cham-bai.md) §5.1 + FR-GRADE-01, [SRS PRACTICE](../../05-practice/srs-practice.md) (xem lại bài).

**Phạm vi cắt (M6 sau):** AI chấm speaking/writing; rubric; hàng đợi review GV; sửa điểm sau chốt. M4 chỉ chấm câu đóng, điểm là final ngay (không có tầng GV vì câu đóng).

---

## Task 1: Migration 0006 — submissions + answers.is_correct

- `submissions`: id, tenant_id, attempt_id uuid UNIQUE, correct_count int, total_count int, score numeric(5,2), graded_at timestamptz default now(). RLS FORCE + policy + grant.
- `ALTER TABLE answers ADD COLUMN is_correct boolean` (null = chưa chấm).
Verify: `alembic upgrade head` sạch; conftest tự chạy migration.

## Task 2: Grade service (TDD)

`app/modules/grading/service.py`:
- `grade_answer(qtype, payload, answer_key) -> bool | None`:
  - `mcq_single`: `payload["selected"] == answer_key["correct_index"]`.
  - `fill_blank`: `payload["blanks"]` (list str) so từng chỗ với `answer_key["blanks"]` (list các list accepted); so sánh **strip + lower** (case-insensitive); đúng khi mọi chỗ khớp ≥1 accepted.
  - loại khác → None (chưa chấm tự động).
- `grade_attempt(s, tenant, attempt_id) -> dict`: đọc mọi answer của attempt + type/answer_key qua question_version; set answers.is_correct; đếm correct/total (total = số câu trong practice, câu không trả lời tính sai); upsert submission (ON CONFLICT attempt_id). Trả {correct_count, total_count, score}.

Test (`tests/test_grading.py`): grade_answer 4 case (mcq đúng/sai, fill_blank đúng/hoa-thường); grade_attempt trên attempt có 2 câu (1 đúng 1 sai + 1 câu bỏ trống) → correct/total/score đúng; chấm lại (idempotent) không tạo submission trùng.

## Task 3: Nối chấm vào submit + endpoint kết quả (TDD)

- Sửa `attempt_service.submit_attempt`: sau khi mark submitted → gọi `grading.grade_attempt`. (import service chéo module — hợp lệ.)
- Endpoint `GET /api/v1/attempts/{id}/result` (student chủ attempt): trả submission summary + **review** từng câu: prompt, đáp án của mình, đáp án đúng, giải thích, is_correct. Chỉ khi attempt submitted (409 nếu chưa nộp).
- log_activity action='auto_grade' module='GRADE'.

Test integration: student làm 2 câu (1 đúng 1 sai) → submit → result trả score đúng, review có đáp án đúng; attempt chưa nộp gọi result → 409; student khác → 403.

## Task 4: Frontend — trang kết quả

- Student: sau nộp (`/hoc/lam-bai` submit) → chuyển `/hoc/ket-qua/[attemptId]`.
- `/hoc/ket-qua/[attemptId]`: điểm lớn (correct/total + %), danh sách review từng câu (đúng ✓ xanh / sai ✗ đỏ, hiện đáp án đúng + giải thích).
- Trang `/hoc`: assignment submitted → nút "Xem kết quả" (cần attempt_id — bổ sung vào list_student_assignments: trả attempt_id nếu đã có attempt submitted).
- `lib/api.ts`: getResult(attemptId).

## Task 5: E2E + hoàn tất

- Mở rộng `practice.spec.ts` (hoặc thêm): sau nộp, student thấy trang kết quả với điểm (VD "1/1" hoặc số câu đúng), và review hiện đáp án đúng.
- ruff + import-linter + full pytest xanh; biome; commit; merge main; push.

## Definition of Done (M4)

- [ ] Migration 0006 áp sạch; RLS submissions.
- [ ] grade_answer đúng cho mcq + fill_blank (case-insensitive) — test.
- [ ] Nộp bài tự động chấm → submission có correct/total/score; câu bỏ trống tính sai — test.
- [ ] Kết quả: student xem điểm + review đáp án đúng; chưa nộp → 409; người khác → 403 — test.
- [ ] E2E: nộp → thấy điểm + review PASS.
- [ ] CI xanh; merged main; push.

## Lịch sử thay đổi

| Ngày | Thay đổi | Người |
|---|---|---|
| 2026-07-17 | Tạo + tự chốt plan M4 | Claude |
