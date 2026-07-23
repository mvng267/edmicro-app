# Milestone 10 — SUPPORT + LOG UI + Usage (hoàn thiện) Implementation Plan

**Trạng thái thực thi:** 🟡 Slice cơ bản (tự chốt 2026-07-21). Milestone chốt cuối M0–M10.

> Kế thừa quy ước M0–M9. Tận dụng activity_logs/audit_logs đã có từ M0.

**Goal:** (1) **LOG UI** — admin/owner xem nhật ký hoạt động theo module/actor/entity (yêu cầu gốc: "mọi phần log phiên bản ai sửa gì"). (2) **SUPPORT** — ticket trong tenant + **impersonation có audit** (đăng nhập thay có ghi vết). (3) **Usage** — dashboard mức dùng + quota AI writing.

**Nguồn:** [SRS SUPPORT](../../15-ho-tro/srs-ho-tro.md), [SRS LOG](../../18-quan-tri-log/srs-quan-tri-log.md), [SRS PLAN](../../14-goi-dich-vu/srs-goi-dich-vu.md).

**Phạm vi cắt (sau):** support cross-tenant (platform), SLA/ưu tiên ticket, log usage-stats biểu đồ + export, quản trị gói/quota đầy đủ, đóng gói on-premise (thuộc ops/docker, không code milestone).

---

## Task 1: Migration 0011
- `tickets` (subject, body, status open/closed, created_by, assigned_to, created_at, updated_at). RLS+grant.
- `ticket_comments` (ticket_id, author_id, body, created_at). RLS+grant.

## Task 2: LOG query + Usage (TDD)
`log/service.py`: `list_activity(filters: module/actor/entity_type, limit)` đọc activity_logs (đã có SELECT). Router `GET /admin/logs` roles owner/it_admin/admin.
`usage/service.py`: `tenant_usage()` — đếm students/classes/submissions + quota writing (tenant_ai_quota kỳ hiện tại). Router `GET /usage` roles owner/manager/it_admin. Test: thao tác sinh activity → /admin/logs thấy; usage trả counts + quota; RBAC.

## Task 3: SUPPORT tickets + impersonation (TDD)
`support/service.py`: create_ticket, list_tickets (của tôi / mọi ticket nếu staff), add_comment, close_ticket, get_ticket(+comments). Router `POST /support/tickets`, `GET /support/tickets`, `GET /support/tickets/{id}`, `POST /support/tickets/{id}/comments`, `POST /support/tickets/{id}/close`.
Impersonation: `POST /support/impersonate/{user_id}` (support_agent/owner/admin) → phát access token cho user đích cùng tenant + **ghi audit_log(action='impersonate', target=user)**. Test: tạo ticket + comment + close; impersonate ghi audit + token dùng được; RBAC (student không impersonate).

## Task 4: Frontend
- `/quan-tri/log`: bảng nhật ký (lọc module) — admin/owner.
- `/ho-tro`: tạo ticket + danh sách + mở ticket + comment + đóng.
- `/quan-tri/usage`: thẻ mức dùng + quota.
- nav theo vai trò (hiện hết, API chặn).

## Task 5: E2E + lint + merge + push
E2E: user tạo ticket → thấy trong danh sách → thêm comment → đóng; owner mở /quan-tri/log thấy hoạt động. Lint sạch; merge `m10-support-log`→main; push; roadmap đánh dấu M10 + **hoàn tất M0–M10**.

## Definition of Done
- LOG UI liệt kê hoạt động theo module — test + E2E.
- Ticket tạo/comment/đóng — test + E2E. Impersonation ghi audit + RBAC — test.
- Usage trả counts + quota — test. Lint sạch, merge+push, roadmap đóng dự án.
