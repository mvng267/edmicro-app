"""Đề thi = practice + exam_meta (thời lượng + quy đổi band). Xem SRS EXAM §5, FR-EXAM-04/08.
Tái dùng toàn bộ assignment/attempt/grading; chỉ thêm đồng hồ server + quy đổi thang điểm.
"""

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.practice import service as practice_svc


def band_for(scale: list[dict[str, Any]] | None, pct: float) -> str | None:
    """Quy đổi % → band: chọn mốc có min lớn nhất mà ≤ pct. None nếu không có bảng/không khớp."""
    if not scale:
        return None
    best: dict[str, Any] | None = None
    for row in scale:
        try:
            m = float(row.get("min"))
        except (TypeError, ValueError):
            continue
        if m <= pct and (best is None or m > float(best["min"])):
            best = row
    return str(best["band"]) if best else None


async def create_exam(s: AsyncSession, tenant_id: str, creator: str, data: dict[str, Any]) -> str:
    """Tạo đề: dựng practice từ câu đã publish rồi gắn exam_meta (thời lượng + band_scale)."""
    duration = int(data["duration_minutes"])
    if duration <= 0:
        raise ValueError("duration_must_be_positive")
    content_id = await practice_svc.create_practice(s, tenant_id, creator, data)
    import json

    await s.execute(
        text(
            "INSERT INTO exam_meta (content_id, tenant_id, duration_minutes, band_scale, "
            "review_allowed) VALUES (:c, :t, :d, CAST(:bs AS jsonb), :ra)"
        ),
        {
            "c": content_id,
            "t": tenant_id,
            "d": duration,
            "bs": json.dumps(data.get("band_scale") or [], ensure_ascii=False),
            "ra": data.get("review_allowed", True),
        },
    )
    return content_id


async def get_exam_meta(s: AsyncSession, content_id: str) -> dict | None:
    row = (
        (
            await s.execute(
                text(
                    "SELECT duration_minutes, band_scale, review_allowed "
                    "FROM exam_meta WHERE content_id = :c"
                ),
                {"c": content_id},
            )
        )
        .mappings()
        .first()
    )
    return dict(row) if row else None


async def list_exams(s: AsyncSession) -> list[dict]:
    rows = (
        (
            await s.execute(
                text(
                    "SELECT p.id, p.name, p.language, p.status, em.duration_minutes, "
                    "(SELECT count(*) FROM practice_questions pq "
                    "WHERE pq.practice_id = p.id) AS n_q "
                    "FROM exam_meta em JOIN practices p ON p.id = em.content_id "
                    "ORDER BY em.created_at DESC"
                ),
            )
        )
        .mappings()
        .all()
    )
    return [{**r, "id": str(r["id"])} for r in rows]
