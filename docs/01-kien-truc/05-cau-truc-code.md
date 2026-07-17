# Cấu trúc code & quy ước module

**Trạng thái:** 🟢 Đã chốt

> Yêu cầu từ chủ sản phẩm: code **chia theo từng module, dễ làm dễ sửa**, cấu trúc gọn gàng, docs theo module — và dùng **phương án hiện đại, tối ưu nhất**.
>
> **Triết lý:** kiến trúc là **modular monolith** (1 backend, 1 frontend, module ranh giới cứng) — không microservices ở v1; "hiện đại" nằm ở **toolchain thế hệ mới** (uv, ruff, Biome, Turborepo, testcontainers) và **ranh giới module được máy kiểm tra** chứ không chỉ là quy ước miệng.

## 0. Toolchain (chốt phương án hiện đại)

| Việc | Công cụ chốt | Thay cho | Lý do |
|---|---|---|---|
| Quản lý gói Python | **uv** (`pyproject.toml` + `uv.lock`) | pip + requirements.txt | Nhanh hơn 10–100×, lockfile tái lập được, chuẩn hiện hành |
| Lint + format Python | **ruff** (lint **và** format) | flake8 + black + isort | 1 công cụ, 1 config, chạy < 1s toàn repo |
| Type-check Python | **pyright** (strict với `service.py`/`schemas.py`) | mypy | Nhanh, chính xác, chạy được trong editor + CI |
| ORM / DB | **SQLAlchemy 2.0** (`Mapped[]`, async + asyncpg) + **Alembic** | — | Chuẩn typed ORM hiện tại |
| Kiểm tra ranh giới module BE | **import-linter** (contracts trong `pyproject.toml`) | quy ước miệng | Luật phụ thuộc §2 được CI cưỡng chế |
| Test backend | **pytest + testcontainers** (Postgres thật) | SQLite giả lập | **Bắt buộc** vì RLS/multi-tenant chỉ test được trên Postgres thật |
| Quản lý gói JS | **pnpm workspaces** | npm | Nhanh, tiết kiệm disk, chuẩn monorepo |
| Task runner / cache monorepo | **Turborepo** (`turbo.json`) | script rời | Cache build/test, chỉ chạy phần thay đổi |
| Lint + format TS | **Biome** | eslint + prettier | 1 công cụ Rust, nhanh ~30×, đủ rule cho Next.js |
| Kiểm tra ranh giới module FE | **dependency-cruiser** | quy ước miệng | Cưỡng chế luật §3 trong CI |
| API client | **@hey-api/openapi-ts** sinh client + **TanStack Query v5** hooks | viết tay fetch | Type-safe end-to-end từ OpenAPI của FastAPI |
| Validate ENV frontend | **zod** schema cho `process.env` (kiểu t3-env) | đọc env trần | Fail sớm khi thiếu config |
| Test frontend | **Vitest** (unit) + **Playwright** (E2E luồng chính) | jest | Nhanh, chuẩn hiện hành |
| Dev environment | **docker compose watch** + **justfile** + `.devcontainer/` | script tự chế | Lên môi trường 1 lệnh: `just dev` |
| CI | **GitHub Actions** + cache uv/pnpm/turbo | — | Lint → typecheck → test → build ≤ ~5 phút |
| Observability | **OpenTelemetry** SDK (trace xuyên API→queue→worker) + structured logging JSON | chỉ log | Gắn với [NFR-MAINT](06-yeu-cau-phi-chuc-nang.md) từ ngày đầu |

## 1. Cấu trúc repo (monorepo)

```
edmicro-app/
├── docs/                    # Bộ tài liệu này (SRS, kiến trúc, mockups)
├── backend/                 # FastAPI (uv + pyproject.toml)
├── frontend/                # Next.js + HeroUI (pnpm)
├── packages/
│   └── api-client/          # TS client sinh từ OpenAPI (không sửa tay)
├── infra/                   # docker-compose, systemd, script deploy SaaS/on-premise
├── scripts/                 # tiện ích dev (seed, gen-types, backup...)
├── .devcontainer/           # môi trường dev chuẩn hóa
├── .github/workflows/       # CI
├── turbo.json               # pipeline + cache monorepo
├── pnpm-workspace.yaml
├── justfile                 # just dev / just test / just gen-api ...
└── README.md
```

## 2. Backend — module theo nghiệp vụ

Mỗi module nghiệp vụ = 1 folder **tự chứa** dưới `backend/app/modules/`, tên trùng mã module trong docs:

```
backend/
├── pyproject.toml               # uv + ruff + pyright + import-linter contracts
├── uv.lock
├── app/
│   ├── main.py                  # wiring: mount routers, middleware (~30 dòng)
│   ├── config.py                # settings từ ENV (pydantic-settings)
│   ├── db.py                    # engine, session, tenant context (SET app.tenant_id)
│   ├── core/                    # dùng chung, KHÔNG chứa nghiệp vụ
│   │   ├── auth/                # JWT, password, 2FA, dependencies quyền + scope (chi nhánh/tổ)
│   │   ├── storage/             # storage adapter (base + minio/s3/r2)
│   │   ├── ai/                  # AI provider adapter (LLM, speech, STT)
│   │   ├── queue/               # arq setup, base job (idempotent, retry)
│   │   ├── notify/              # driver kênh: email, zalo, sms (module notif gọi vào)
│   │   ├── telemetry.py         # OpenTelemetry + structured logging
│   │   ├── audit.py             # ghi audit log (hành động nhạy cảm)
│   │   └── activity_log.py      # interceptor activity log 2 tầng (mọi thao tác ghi, async)
│   └── modules/
│       ├── org/                 # ORG — tenant, chi nhánh, lớp, user, scope, parent link
│       │   ├── router.py        #   endpoints /api/v1/org/...
│       │   ├── service.py       #   nghiệp vụ (interface công khai của module)
│       │   ├── repository.py    #   truy vấn DB (chỉ service của chính module gọi)
│       │   ├── schemas.py       #   Pydantic v2 request/response
│       │   ├── models.py        #   SQLAlchemy 2.0 models (Mapped[])
│       │   ├── jobs.py          #   background jobs (nếu có)
│       │   └── tests/           #   pytest + testcontainers (test cả RLS)
│       ├── authz/               # AUTH — vai trò, ma trận quyền, user_scopes
│       ├── course/              # COURSE
│       ├── practice/            # PRACTICE
│       ├── exam/                # EXAM
│       ├── assignment/          # ASSIGN
│       ├── grading/             # GRADE
│       ├── report/              # REPORT (kể cả cổng phụ huynh)
│       ├── content/             # CONTENT — ngân hàng câu hỏi
│       ├── notification/        # NOTIF
│       ├── schedule/            # SCHED — lịch học, điểm danh
│       ├── gamification/        # GAME
│       ├── plan/                # PLAN — gói, quota
│       ├── support/             # SUPPORT — ticket, impersonation
│       └── log/                 # LOG — quản trị nhật ký hoạt động + usage stats
├── alembic/                     # migrations (naming convention thống nhất)
└── Dockerfile                   # multi-stage, chạy bằng uv
```

**Luật phụ thuộc (CI cưỡng chế bằng import-linter):**

1. Module chỉ được import `core/*` và `service.py` của module khác — **cấm** import `repository.py`/`models.py` chéo module.
2. `core/` không import `modules/` (tránh vòng).
3. Router mỏng: validate + gọi service; nghiệp vụ nằm trong service; SQL nằm trong repository.
4. File > ~400 dòng → tách (`service_grading.py`, `service_review.py`…).
5. Test module nào nằm trong module đó; test RLS/quyền là **bắt buộc** với mọi endpoint mới (template test có sẵn).

## 3. Frontend — Next.js App Router, chia theo module

```
frontend/
├── app/                              # routes (App Router, React Server Components)
│   ├── (tenant)/                     # nhóm route trong tenant, sau đăng nhập
│   │   ├── layout.tsx                #   shell: Navbar/Sidebar HeroUI theo vai trò
│   │   ├── dashboard/
│   │   ├── courses/[courseId]/
│   │   ├── practice/[practiceId]/
│   │   ├── exams/[examId]/
│   │   ├── assignments/
│   │   ├── grading/                  #   hàng đợi chấm của GV/trợ giảng
│   │   ├── reports/
│   │   ├── schedule/
│   │   ├── leaderboard/
│   │   ├── parent/                   #   cổng phụ huynh (xem kết quả của con)
│   │   └── settings/                 #   cài đặt: tab theo vai trò (owner thấy phần trung tâm)
│   ├── (platform)/ops/               # cổng quản trị platform (admin/content/support)
│   └── (auth)/login/
├── modules/                          # code nghiệp vụ theo module (đối xứng backend)
│   └── <module>/
│       ├── components/               #   component riêng module (100% HeroUI)
│       ├── hooks.ts                  #   TanStack Query v5 hooks (bọc api-client)
│       └── types.ts                  #   type nghiệp vụ FE (type API lấy từ packages/api-client)
├── components/                       # dùng chung: shell, form controls bọc HeroUI
├── lib/                              # auth, tenant, i18n (next-intl), sse, env (zod)
├── e2e/                              # Playwright: luồng chính per vai trò
├── middleware.ts                     # resolve tenant từ subdomain
├── biome.json
└── tailwind.config.ts                # theme HeroUI (design tokens)
```

**Luật frontend (CI cưỡng chế bằng dependency-cruiser):**

1. **100% HeroUI**: mọi UI control dùng component HeroUI; không tự viết control trùng chức năng, không trộn thư viện UI khác. Thiếu component → bọc/ghép từ HeroUI primitives trong `components/`.
2. `app/` chỉ là route + layout; logic và UI nghiệp vụ nằm trong `modules/<module>/`; module không import chéo `modules/<khác>/components` (chỉ qua `components/` chung).
3. Types API **chỉ** từ `packages/api-client` (sinh bằng `just gen-api` từ OpenAPI) — cấm viết tay types trùng.
4. **Server Components mặc định** (báo cáo, danh sách — fetch trên server, ít JS xuống client); `"use client"` chỉ cho tương tác thật (làm bài, ghi âm, đồng hồ thi); mutation qua TanStack Query (giữ REST thuần — không dùng Server Actions cho API nghiệp vụ, tránh 2 đường vào backend).
5. Route guard theo vai trò ở `middleware.ts` + kiểm tra lại ở component (nguồn chân lý vẫn là API).

## 4. Vòng phát triển (dev loop)

```
just dev        # docker compose watch: postgres + redis + minio + api + worker + web (hot reload)
just gen-api    # FastAPI OpenAPI → packages/api-client (hey-api) — chạy khi đổi schema
just test       # turbo: pytest (testcontainers) + vitest + biome + ruff + pyright + import-linter
just seed       # dữ liệu mẫu: 1 tenant + đủ 8 vai trò tenant + lớp + nội dung demo
```

- Quy trình khi thêm 1 tính năng: sửa SRS nếu lệch → viết test (TDD) → implement module → `just gen-api` → UI → E2E nếu là luồng chính.
- CI (GitHub Actions): `lint → typecheck → test → build`, cache uv/pnpm/turbo; PR phải xanh + review.

## 5. Quy ước chung

| Chủ đề | Quy ước |
|---|---|
| Đặt tên | Bảng DB: `snake_case` số nhiều (`submissions`); API path: `kebab-case`; component: `PascalCase` |
| API | REST `/api/v1/<module>/...`; lỗi trả `{code, message, details}` thống nhất |
| Commit | Conventional Commits (`feat(exam): ...`, `fix(grading): ...`) |
| i18n | UI text qua next-intl, mặc định `vi`, sẵn sàng thêm locale |
| Migration | Alembic; reversible hoặc có script rollback; zero-downtime với thay đổi thường |
| Test coverage | Service layer ≥ 80%; E2E các luồng: làm bài, giao bài, chấm, báo cáo, cổng phụ huynh |

## 6. Skills hỗ trợ khi implement (note lại theo yêu cầu)

| Việc | Skill (Claude Code) |
|---|---|
| Component React/HeroUI, hooks, typing | `react-dev`, `composition-patterns` |
| Hiệu năng Next.js / RSC | `react-best-practices` (Vercel) |
| useEffect/data fetching đúng cách | `react-useeffect` |
| Thiết kế schema & migration | `database-schema-designer` |
| Viết test trước khi code | `test-driven-development` |
| Sơ đồ trong docs | `mermaid-diagrams`, `c4-architecture` |
| Commit sạch | `commit-work` |
| Kiểm tra sau mỗi thay đổi | `verify`, `code-review` |

## 7. Những gì cố ý KHÔNG dùng (v1) — và vì sao

| Không dùng | Lý do |
|---|---|
| Microservices | Đội nhỏ, domain chưa ổn định — modular monolith với ranh giới máy-kiểm-tra cho tốc độ + kỷ luật; tách service sau này theo đúng ranh giới module nếu cần |
| GraphQL | Đã chốt ADR #3 — REST + OpenAPI codegen đủ type-safe, đơn giản hơn |
| Server Actions cho API nghiệp vụ | Tránh 2 đường vào backend (Next server + FastAPI); FastAPI là API duy nhất |
| ORM code-first sinh schema tự động (kiểu Prisma cho BE Python) | Alembic migration tường minh, kiểm soát RLS/index thủ công |
| Kubernetes v1 | Đã chốt ở [Vận hành](07-van-hanh-trien-khai.md) — compose single-node trước |

## Lịch sử thay đổi

| Ngày | Thay đổi | Người |
|---|---|---|
| 2026-07-16 | Tạo bản nháp đầu tiên | Claude |
| 2026-07-16 | Chốt — chuyển trạng thái Đã chốt | Chủ sản phẩm |
| 2026-07-16 | Nâng cấp toolchain hiện đại: uv, ruff, pyright, import-linter, testcontainers, pnpm+Turborepo, Biome, hey-api, dependency-cruiser, OTel, justfile/devcontainer; thêm packages/api-client, route cổng phụ huynh; mục "cố ý không dùng" | Chủ sản phẩm + Claude |
| 2026-07-17 | Thêm core/activity_log.py + module log/ | Chủ sản phẩm + Claude |
