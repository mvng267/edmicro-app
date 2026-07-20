# Milestone 2 — CONTENT tối thiểu Implementation Plan

**Trạng thái thực thi:** ✅ HOÀN TẤT 2026-07-17 — 24 backend test + 4 E2E PASS. Playwright ép workers=1 (E2E chung DB dev). Cắt sang M3: question_groups (passage chung).

> Kế thừa quy ước M0/M1: module `backend/app/modules/content/{router,service,repository,schemas}.py`; TDD testcontainers (fixture `session_factory`); RLS + grant `app_user` mọi migration; `log_activity` mọi thao tác ghi; ruff+import-linter sạch; HeroUI v3 (`Input` aria-label, không `color` prop, `CardContent`); commit nhỏ.

**Goal:** Teacher (và owner/manager/academic_head) soạn **câu hỏi** loại `mcq_single` + `fill_blank` trong kho tenant, có **versioning** (sửa câu đã publish → version mới), tìm theo **tag** (ngôn ngữ/kỹ năng/level/chủ đề). Câu hỏi là nguyên liệu cho M3 (practice) — M2 chỉ quản lý kho.

**Nguồn:** [SRS CONTENT](../../10-noi-dung/srs-noi-dung.md) FR-CONTENT-01..14, [loại câu hỏi](../../99-phu-luc/01-loai-cau-hoi.md).

**Phạm vi cắt (M2+ sau):** kho global + content_editor + phân phối gói (M6+), quy trình duyệt/review_logs (mặc định teacher tự publish), question_groups (passage chung — M3 khi cần), import câu hỏi từ Word, loại câu hỏi ngoài mcq_single/fill_blank.

---

## Task 1: Migration 0004 — questions + question_versions + RLS

- `questions`: id, tenant_id, is_global bool default false, type text, language text, skill text, level text, exam_tag text, topic text, difficulty int, status text default 'draft' ('draft'|'published'|'archived'), current_version_id uuid null, created_by uuid, created_at/updated_at. RLS FORCE + policy + grant.
- `question_versions`: id, tenant_id, question_id uuid FK, version_no int, content jsonb, answer_key jsonb, explanation text, created_by uuid, created_at. RLS + grant. UNIQUE (question_id, version_no).
- Index GIN/btree phục vụ lọc: `(tenant_id, language, skill, level, status)`.
- Verify: `alembic upgrade head` sạch trên dev; conftest tự chạy migration (không sửa).

## Task 2: Content service + validation (TDD)

`backend/app/modules/content/service.py`:
- `validate_content(type, content, answer_key)`:
  - `mcq_single`: content={prompt:str, options:[str>=2]}, answer_key={correct_index:int in range}. Sai → `InvalidContent`.
  - `fill_blank`: content={prompt:str có ít nhất 1 chỗ trống ký hiệu `___`}, answer_key={blanks:[[accepted:str,...]]} khớp số chỗ trống, case_insensitive bool default true.
- `create_question(s, tenant, creator, data)`: tạo question (draft) + version_no=1; validate content; log.
- `publish_question(s, id)`: set status='published', current_version_id = version mới nhất.
- `update_question(s, id, data)`: tạo **version mới** (version_no+1) với content mới; nếu đang published thì current_version_id trỏ version mới; version cũ giữ nguyên (bất biến).
- `list_questions(s, filters)`: lọc theo language/skill/level/status/exam_tag/q(prompt ILIKE) + phân trang.
- `get_question(s, id)`: câu hỏi + version hiện hành (content + answer_key + explanation).

Test (`tests/test_content.py`): tạo mcq hợp lệ; mcq correct_index ngoài range → 422; fill_blank số blanks lệch → 422; update tạo version 2 giữ version 1; publish set current_version; list lọc theo skill.

## Task 3: Content router (TDD)

`/api/v1/content/questions` — POST tạo, GET list (filters query), GET /{id} chi tiết, PATCH /{id} (tạo version mới), POST /{id}/publish. Quyền: `{owner, manager, academic_head, teacher}` (403 role khác). log_activity + RLS.

Test integration (như M1 pattern override get_tenant_session + get_current_user): teacher tạo mcq → 201; student POST → 403; list trả câu vừa tạo; RLS tenant khác không thấy.

## Task 4: Frontend — trang ngân hàng câu hỏi

- Thêm mục sidebar AppShell "Ngân hàng câu hỏi" → `/content`.
- `/content`: filter (Select ngôn ngữ/kỹ năng/level + Input tìm) + bảng câu hỏi (prompt rút gọn, type chip, tag chip, status chip). Nút "Tạo câu hỏi".
- Form tạo: chọn type (mcq_single | fill_blank); mcq → prompt + danh sách option động + chọn đáp án đúng; fill_blank → prompt (hướng dẫn dùng `___`) + đáp án từng chỗ trống; nút Lưu (draft) + Xuất bản.
- `lib/api.ts`: hàm listQuestions/createQuestion/publishQuestion.

## Task 5: E2E + hoàn tất

- E2E: owner login → /content → tạo 1 câu mcq_single (prompt + 3 option + đáp án) → xuất bản → thấy trong danh sách với status "published" → lọc theo kỹ năng thấy câu đó.
- ruff + import-linter + full pytest xanh; biome frontend; commit; merge main; push.

## Definition of Done (M2)

- [ ] Migration 0004 áp sạch; RLS questions + question_versions.
- [ ] Validation 2 loại câu hỏi + versioning (test tạo version 2 giữ version 1).
- [ ] RBAC: student POST → 403 (test).
- [ ] E2E tạo + xuất bản + lọc câu hỏi PASS.
- [ ] activity log cho create/publish (spot-check).
- [ ] CI xanh; merged main; push.

## Lịch sử thay đổi

| Ngày | Thay đổi | Người |
|---|---|---|
| 2026-07-17 | Tạo + tự chốt plan M2 | Claude |
