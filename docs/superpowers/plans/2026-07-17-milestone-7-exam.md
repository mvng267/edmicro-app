# Milestone 7 — EXAM (thi thử có đồng hồ server) Implementation Plan

**Trạng thái thực thi:** 🟡 Slice cơ bản (tự chốt 2026-07-20).

> Kế thừa quy ước M0–M6. **Thiết kế chốt: exam = practice + `exam_meta`** — tái dùng toàn bộ assignment/attempt/answer/grading (câu đóng M4 + writing hybrid M6). Chỉ thêm phần đặc trưng thi: **đồng hồ server** (deadline trên attempt) + **tự nộp khi hết giờ** + **quy đổi band**.

**Goal:** GV tạo **đề thi** (chọn câu từ ngân hàng + thời lượng + bảng quy đổi band) → giao lớp → HS thi với **đồng hồ đếm ngược theo server**, hết giờ **tự nộp**; chấm (đóng ngay, writing vào hàng đợi GV) → phiếu kết quả có **điểm quy đổi band**.

**Nguồn:** [SRS EXAM](../../06-exam/srs-exam.md) FR-EXAM-04/05/07/08/09; [chuẩn thi](../../99-phu-luc/02-chuan-thi-quoc-te.md).

**Phạm vi cắt (slice sau):** đa-section timer riêng từng phần (M7 dùng 1 đồng hồ cho cả đề); template chuẩn dựng sẵn (M7 nhập band_scale tự do); phòng thi tập trung/lịch/phòng chờ/dashboard realtime; chống gian lận (rời tab, chặn 2 phiên, copy/paste, xáo trộn, rút pool); cấp bù thời gian; kiểm tra thiết bị.

---

## Task 1: Migration 0008
- `exam_meta`: content_id uuid PK (= practices.id), tenant_id, duration_minutes int, band_scale jsonb (list {min: pct, band: label}), review_allowed bool default true. RLS+grant.
- `attempts` ADD `deadline_at timestamptz` (null với practice; đặt lúc start với exam).

## Task 2: exam service + đồng hồ + band (TDD)
`app/modules/exam/service.py`: `create_exam` (gọi practice.create_practice + insert exam_meta), `get_exam_meta`, `band_for(scale, pct)` (band có min lớn nhất ≤ pct). Hook attempt:
- `start_attempt`: nếu content có exam_meta → `attempts.kind='exam'`, `deadline_at = now + duration`; trả deadline.
- `save_answer`: attempt exam quá deadline → NotEditable (409 time_expired) — đồng hồ không dừng.
- `grading.get_result`: nếu content là exam → thêm `band` (quy đổi từ score), `is_exam`, `duration_minutes`.
Test: band_for biên; start đặt deadline; save sau deadline → 409; submit chấm; result có band đúng.

## Task 3: exam router + RBAC (TDD)
`app/modules/exam/router.py`: `POST /exams` (tạo đề — roles owner/manager/academic_head/teacher/content_editor), `GET /exams` (list). Start endpoint (assignment router) trả thêm `deadline_at` + `duration_minutes` khi exam. Test: tạo đề + giao + start trả deadline; student tạo đề → 403.

## Task 4: Frontend
- `/exams`: chọn câu (như practices) + thời lượng + nhập band_scale (mặc định gợi ý) → tạo + giao lớp.
- `/hoc/lam-bai/[assigneeId]`: nếu start trả deadline → hiện **đồng hồ đếm ngược** (theo deadline server); hết giờ → tự gọi submit.
- Kết quả: nếu exam → hiện **band** cạnh điểm.
- nav "Đề thi".

## Task 5: E2E + lint + merge + push
E2E: GV tạo đề (thời lượng ngắn) + giao → HS thi thấy đồng hồ → nộp → kết quả có band. Lint sạch; merge `m7-exam`→main; push; roadmap.

## Definition of Done
- Exam có đồng hồ server (deadline), save sau giờ bị chặn, hết giờ tự nộp — test + E2E.
- Quy đổi band từ score theo band_scale — test.
- Tái dùng chấm (đóng + writing hybrid); phiếu kết quả có band. Lint sạch, merge+push.
