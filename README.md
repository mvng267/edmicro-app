# Edmicro App

LMS B2B đa ngôn ngữ cho trung tâm ngoại ngữ tại Việt Nam — multi-tenant, 11 vai trò, chấm bài hybrid AI + giáo viên.

## Tài liệu

- **Nguồn chân lý:** [docs/README.md](docs/README.md) — 35 tài liệu SRS + kiến trúc + dữ liệu + mockup, tất cả đã chốt (🟢).
- **Kế hoạch triển khai:** [docs/superpowers/plans/2026-07-17-roadmap.md](docs/superpowers/plans/2026-07-17-roadmap.md) — roadmap 11 milestone theo thứ tự "xương sống".
- **Milestone 0 (nền tảng):** [docs/superpowers/plans/2026-07-17-milestone-0-foundation.md](docs/superpowers/plans/2026-07-17-milestone-0-foundation.md).

## Tech stack

Python FastAPI · Next.js (App Router) + HeroUI · PostgreSQL (RLS multi-tenant) · Redis + arq · MinIO → S3/R2 · uv · pnpm + Turborepo. Chi tiết: [docs/01-kien-truc/05-cau-truc-code.md](docs/01-kien-truc/05-cau-truc-code.md).

## Chạy dev (sau khi implement M0)

```bash
cp .env.example .env
just dev      # dựng postgres/redis/minio + backend
just test     # chạy test
```

## Trạng thái

Giai đoạn: **hoàn tất tài liệu, bắt đầu triển khai từ Milestone 0**.
