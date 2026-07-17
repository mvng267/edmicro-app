# Milestone 1 — ORG tối thiểu Implementation Plan

**Trạng thái thực thi:** ✅ HOÀN TẤT 2026-07-17 — 19 backend test + 3 E2E PASS. Khác plan: conftest chạy Alembic thật (bỏ DDL tay); frontend HeroUI v3 (Input dùng aria-label thay label prop, bỏ color prop dùng default variant); server defaults cột vận hành; port Next dev 3005. Cắt sang M2: rooms, class_delegations, anonymize job.

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. Quy ước kế thừa M0 (không lặp lại): module layout `backend/app/modules/<m>/{router,service,repository,schemas}.py`, TDD với testcontainers (fixture `session_factory` trong `tests/conftest.py`), RLS + grant cho `app_user` trong mọi migration, `log_activity` cho mọi thao tác ghi, ruff/import-linter sạch trước khi commit, commit nhỏ.

**Goal:** Owner dựng được bộ máy trung tâm: chi nhánh → lớp → tài khoản đủ 8 vai trò tenant + gán phạm vi chi nhánh; it_admin import học sinh từ Excel (validate → preview → commit → phát tài khoản); học sinh vừa tạo **đăng nhập được**. Mọi thao tác ghi có activity log; RBAC + scope cưỡng chế ở API với test chứng minh.

**Nguồn yêu cầu:** [SRS ORG](../../03-to-chuc-nguoi-dung/srs-to-chuc-nguoi-dung.md) (FR-ORG-04→15, 22, 23), [SRS AUTH](../../02-phan-quyen/srs-phan-quyen.md) (ma trận §6, FR-AUTH-12/14/17).

**Phạm vi cắt (để M2+):** consent UI đầy đủ (M1 chỉ đánh trạng thái `pending` khi tạo HS <16 tuổi), rooms, class_delegations (ủy quyền TA), soft-delete→anonymize job (M1 có soft-delete, job anonymize để M2), 2FA, đổi cấu hình tenant (logo/theme).

---

## Task 1: Migration 0003 — bảng tổ chức + RLS

Bảng mới (tất cả RLS trừ ghi chú): `branches`, `classes`, `class_staff`, `class_students`, `user_scopes`, `parent_students`, `consents`, `import_jobs`, `import_rows`.

- Mọi bảng: `tenant_id uuid NOT NULL` + `ENABLE/FORCE ROW LEVEL SECURITY` + policy `tenant_isolation` (USING + WITH CHECK như bảng users) + GRANT SELECT/INSERT/UPDATE/DELETE cho app_user.
- `classes`: branch_id FK, name, language, level, capacity NULL, start_date/end_date NULL, status default 'active'.
- `class_staff`: class_id, user_id, role ('homeroom'|'teacher'|'assistant'), UNIQUE (class_id, user_id).
- `class_students`: class_id, user_id, joined_at default now(), left_at NULL — lịch sử chuyển lớp.
- `user_scopes`: user_id, branch_id NULL (=toàn trung tâm), language NULL (cho academic_head).
- `parent_students`: parent_user_id, student_user_id, linked_by, UNIQUE cặp.
- `consents`: user_id, status ('pending'|'granted'|'declined'), updated_by, note NULL.
- `import_jobs`: status ('validated'|'committed'|'expired'), filename, summary jsonb; `import_rows`: job_id, row_no, data jsonb, error text NULL, action ('create'|'skip'|'error').
- `users`: thêm cột `dob date NULL`, `parent_phone text NULL`.

Verify: `alembic upgrade head` sạch trên DB dev; cập nhật `_SCHEMA_DDL` trong conftest tương ứng (chỉ bảng test cần: branches, classes, class_staff, class_students, user_scopes, consents, parent_students).

## Task 2: Auth dependencies — current user + RBAC + scope

File `backend/app/core/authn.py`:

- `CurrentUser` (dataclass): user_id, tenant_id, role.
- `get_current_user(authorization: Header)` → decode JWT (type=access), trả CurrentUser; 401 nếu thiếu/sai.
- `get_tenant_session(current=Depends(get_current_user), session=Depends(get_session))` → `set_tenant(session, current.tenant_id)` rồi yield session — **mọi endpoint sau đăng nhập dùng dependency này** (RLS theo token, không theo header slug).
- `require_roles(*roles)` → dependency factory 403 nếu role không thuộc danh sách (owner luôn qua với các quyền manager: caller liệt kê tường minh `"owner", "manager"` — không magic).
- `scope_branch_ids(session, current) -> list[str] | None`: owner → None (toàn tenant); manager/it_admin → đọc user_scopes (rỗng → coi như toàn tenant nếu không có bản ghi nào — mặc định gán toàn trung tâm khi tạo); vai trò khác → None (không dùng ở M1).

Test (`tests/test_authn.py`): token hết hạn/thiếu → 401; role sai → 403; đúng role → 200 (dùng endpoint giả trong test app).

## Task 3: Branches API (TDD)

`/api/v1/org/branches` — GET (mọi vai trò quản lý + teacher đọc), POST/PATCH/DELETE (owner only — FR-AUTH-17). DELETE chặn khi còn lớp `status='active'` (409). log_activity mọi thao tác ghi.

Test: owner tạo/sửa/xóa OK; manager POST → 403; xóa chi nhánh còn lớp active → 409; RLS: tenant khác không thấy.

## Task 4: Classes + staff + students API (TDD)

`/api/v1/org/classes` — POST/PATCH (owner, manager, it_admin — trong scope chi nhánh), GET danh sách lọc theo scope; `POST /{id}/staff` gán GV/TA (validate user role teacher/assistant, UNIQUE); `POST /{id}/students` thêm HS; `DELETE /{id}/students/{uid}` rời lớp (set left_at); `POST /{id}/students/{uid}/transfer` chuyển lớp (đóng enrollment cũ + mở mới, giữ lịch sử).

Test: manager scope branch A tạo lớp branch B → 403; thêm user role student OK, role teacher vào students → 422; transfer giữ bản ghi cũ có left_at.

## Task 5: Users API (TDD)

`/api/v1/org/users`:
- POST tạo tay: owner tạo mọi vai trò tenant; manager/it_admin chỉ teacher/assistant/student/parent (403 nếu tạo owner/manager/academic_head/it_admin — FR-AUTH-12); sinh username nếu bỏ trống (slug họ tên + số), password ngẫu nhiên trả về 1 lần, must_change_password=true; HS có dob <16 tuổi → tạo consents(status='pending').
- GET danh sách + tìm kiếm (q, role, class_id, status) trong scope.
- POST `/{id}/lock` · `/{id}/unlock` (không khóa được vai trò quản lý trừ khi caller là owner), POST `/{id}/reset-password` (trả mật khẩu mới 1 lần), PATCH `/{id}/role` (owner only, audit log).
- POST `/api/v1/org/parents` tạo parent + liên kết con (parent_students); POST `/{id}/children` thêm liên kết.
- PUT `/api/v1/org/users/{id}/scopes` (owner) — gán branch scope cho manager/it_admin.

Test: ma trận tạo vai trò đúng như trên; reset password đổi hash + must_change_password; student <16 có consent pending; parent link UNIQUE.

## Task 6: Import Excel (TDD)

Dep mới: `openpyxl`. `/api/v1/org/users/import`:
- POST (multipart .xlsx) → parse cột: họ tên*, ngày sinh*, giới tính, email, SĐT phụ huynh, mã lớp, ghi chú → validate từng dòng (lớp tồn tại trong scope, ngày sinh hợp lệ, trùng trong file, trùng tenant theo tên+ngày sinh → warning) → lưu import_jobs + import_rows, trả preview {job_id, rows: [{row_no, data, error?}], summary}.
- POST `/import/{job_id}/commit` (body: skip_errors=true, confirm_duplicates=[row_no]) → tạo users + class_students + consents(<16) trong 1 transaction; trả credentials [{username, password}] **một lần**; job → committed. Job đã committed → 409.
- Giới hạn 2.000 dòng (413 nếu vượt).

Test: file 5 dòng (3 hợp lệ, 1 sai lớp, 1 sai ngày sinh) → preview đúng lỗi từng dòng; commit skip_errors tạo đúng 3 user + enrollment; student mới login được bằng credentials trả về (test qua endpoint login thật).

## Task 7: Frontend — shell + 4 trang ORG (HeroUI v3)

- `components/AppShell.tsx`: navbar + sidebar theo vai trò (owner/manager/it_admin thấy menu Tổ chức; teacher/student menu tối thiểu — placeholder).
- Trang `/org/branches`: bảng + form tạo/sửa (owner).
- Trang `/org/classes`: bảng lọc chi nhánh + drawer chi tiết (gán GV/TA, danh sách HS, nút thêm/chuyển).
- Trang `/org/users`: bảng tìm kiếm + tạo tài khoản (hiện mật khẩu 1 lần trong modal) + khóa/reset + gán phạm vi.
- Trang `/org/import`: wizard 3 bước theo mockup `it-admin/import-hoc-sinh.html` (upload → preview lỗi/sửa không cần inline, chỉ skip → kết quả + tải credentials CSV client-side).
- `lib/api.ts` mở rộng: fetch wrapper gắn Bearer + X-Tenant-Slug, hàm cho các endpoint trên.

## Task 8: E2E + hoàn tất

- E2E Playwright: owner login → tạo chi nhánh → tạo lớp → tạo teacher + student (lấy mật khẩu từ modal) → logout → student login thành công thấy dashboard.
- ruff + import-linter + full pytest xanh; cập nhật CI không đổi; commit, merge main, push.

## Definition of Done (M1)

- [ ] Migration 0003 áp sạch; RLS mọi bảng mới (test tự động cho branches/classes).
- [ ] RBAC + scope: 3 test 403 chứng minh (manager tạo branch, it_admin tạo manager, manager ngoài scope chi nhánh).
- [ ] Import Excel end-to-end qua API test; student import xong login được.
- [ ] E2E owner-dựng-bộ-máy → student login PASS.
- [ ] Mọi thao tác ghi ORG có activity log (spot-check test 1 endpoint).
- [ ] CI xanh; merged main; push GitHub.

## Lịch sử thay đổi

| Ngày | Thay đổi | Người |
|---|---|---|
| 2026-07-17 | Tạo + tự chốt plan M1 | Claude |
