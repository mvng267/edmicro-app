# Milestone 6 — AI chấm writing + quota Implementation Plan

**Trạng thái thực thi:** 🟡 Writing xong (tự chốt 2026-07-20). Speaking hoãn slice sau.

> Kế thừa quy ước M0–M5: module `backend/app/modules/grading/`; TDD testcontainers; RLS + scope; ruff+import-linter; HeroUI v3; Playwright workers=1; commit nhỏ.

**Goal:** Câu **writing** (câu mở) chạy đủ mô hình hybrid: HS nộp → **AI chấm sơ bộ** (điểm 0..1 + nhận xét, adapter provider) đưa vào **hàng đợi review** → **GV chốt điểm** → điểm bài thành final. Có **quota AI theo tenant/kỳ** và **degrade** (vượt quota / AI lỗi → chuyển chấm tay, luồng nộp không vỡ, HS luôn an toàn).

**Nguồn:** [SRS GRADE](../../08-cham-bai/srs-cham-bai.md) §5.2–5.3 + FR-GRADE-02/04/06/07/08/09; [SRS PLAN](../../14-goi-dich-vu/srs-goi-dich-vu.md) §quota+soft-block.

**Phạm vi cắt (slice sau):** speaking (audio upload + STT Whisper + phát âm Azure) — dùng lại queue/review; rubric bank chuẩn thi + rubric riêng tenant; hiệu chuẩn AI-vs-GV; trang usage/quota cho owner/admin; circuit breaker AI theo thời gian; trợ giảng chấm nháp → GV xác nhận hàng loạt.

---

## Task 1: Migration 0007
`grading_jobs` (1 job/câu mở: status pending/ai_graded/needs_manual/finalized, priority), `tenant_ai_quota` (tenant+period, writing_limit/used), `answers` +ai_score/ai_feedback/ai_confidence/final_score/grade_status, `submissions` +status (final/provisional). RLS+grant mọi bảng mới.

## Task 2: AI grader adapter + loại writing (TDD)
`grading/ai.py`: `AIGrader` Protocol + `FakeGrader` (tất định theo độ dài/đa dạng — dev/test/degrade) + `ClaudeGrader` (LLM thật, temperature 0, JSON, gated `anthropic_api_key`); `get_grader()` chọn theo key. Content: thêm type `writing` (prompt + rubric tùy chọn, không answer_key). Test: Fake tất định/bounded/empty=0/dài hơn điểm cao hơn; validate writing.

## Task 3: Hàng đợi + process + quota/degrade (TDD)
`grade_attempt`: câu đóng chấm ngay; câu mở → job pending + grade_status pending; submission **provisional**. `process_attempt_ai` (gọi ngay sau submit): rút job pending → còn quota thì chấm AI (ai_graded, trừ quota) → vượt quota/AI lỗi thì **needs_manual** (degrade, hoàn quota nếu lỗi). `finalize_open_answer`: đặt final_score 0..1 → recompute (final khi hết câu chờ). Test: submit→ai_graded; quota=0→needs_manual; finalize→final score đúng ((đóng+mở)/tổng).

## Task 4: Endpoint review GV (RBAC/scope, TDD)
`grading/router.py`: `GET /grading/queue` (gộp theo lượt, ưu tiên needs_manual/confidence thấp), `GET /grading/attempts/{id}` (chi tiết bài + điểm AI), `POST /grading/answers/{id}/finalize` (chốt + log). Scope: teacher/assistant chỉ lớp mình (class_staff); owner/manager/academic_head toàn tenant. Test: queue thấy bài, finalize→final; student/GV-ngoài-lớp 403.

## Task 5: Frontend
Content: form writing (prompt+rubric). Làm bài: câu writing = textarea autosave {text}. Kết quả: banner "điểm tạm tính", câu writing "Chờ GV duyệt" / điểm chốt + nhận xét. `/cham-bai` hàng đợi + `/cham-bai/[attemptId]` xem bài + điểm AI đề xuất → chốt điểm; nav "Chấm bài".

## Task 6: E2E + lint + merge + push
E2E: owner giao bài writing → HS viết+nộp → kết quả "chờ GV duyệt" → owner mở /cham-bai → chốt điểm. Lint sạch; merge `m6-ai-grade`→main; push; roadmap.

## Definition of Done
- writing: nộp → AI sơ bộ → GV chốt → final; câu bỏ trống an toàn — test.
- quota vượt / AI lỗi → needs_manual, luồng nộp không vỡ — test.
- review RBAC/scope đúng — test. FE demo đủ luồng — E2E. Lint sạch, merge+push.
