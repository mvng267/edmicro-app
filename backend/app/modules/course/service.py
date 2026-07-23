"""Khóa học → bài học (nhúng practice/exam) + tiến độ. Xem SRS COURSE §5, FR-COURSE.
M9: cấu trúc Course → Lesson (bỏ Section); 6 loại lesson; hoàn thành lesson → % + điểm GAME.
"""

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.game import service as game

LESSON_KINDS = {"text", "video", "file", "flashcard", "practice", "exam"}


class InvalidLesson(Exception):
    pass


async def create_course(s: AsyncSession, tenant_id: str, creator: str, data: dict[str, Any]) -> str:
    cid = str(uuid.uuid4())
    await s.execute(
        text(
            "INSERT INTO courses (id, tenant_id, name, language, status, created_by) "
            "VALUES (:id, :t, :n, :lang, 'published', :by)"
        ),
        {
            "id": cid,
            "t": tenant_id,
            "n": data["name"],
            "lang": data.get("language", "en"),
            "by": creator,
        },
    )
    return cid


async def add_lesson(s: AsyncSession, tenant_id: str, course_id: str, data: dict[str, Any]) -> str:
    kind = data.get("kind", "text")
    if kind not in LESSON_KINDS:
        raise InvalidLesson(f"invalid_kind:{kind}")
    if kind in ("practice", "exam") and not data.get("content_ref"):
        raise InvalidLesson("embed_needs_content_ref")
    order = (
        await s.execute(
            text("SELECT COALESCE(max(sort_order), -1) + 1 FROM lessons WHERE course_id = :c"),
            {"c": course_id},
        )
    ).scalar_one()
    lid = str(uuid.uuid4())
    await s.execute(
        text(
            "INSERT INTO lessons (id, tenant_id, course_id, sort_order, title, kind, body, "
            "content_ref) VALUES (:id, :t, :c, :o, :ti, :k, :b, :cr)"
        ),
        {
            "id": lid,
            "t": tenant_id,
            "c": course_id,
            "o": order,
            "ti": data["title"],
            "k": kind,
            "b": data.get("body", ""),
            "cr": data.get("content_ref"),
        },
    )
    return lid


async def assign_to_class(s: AsyncSession, tenant_id: str, course_id: str, class_id: str) -> None:
    await s.execute(
        text(
            "INSERT INTO course_classes (tenant_id, course_id, class_id) VALUES (:t, :c, :cl) "
            "ON CONFLICT (course_id, class_id) DO NOTHING"
        ),
        {"t": tenant_id, "c": course_id, "cl": class_id},
    )


async def list_courses(s: AsyncSession) -> list[dict]:
    rows = (
        (
            await s.execute(
                text(
                    "SELECT c.id, c.name, c.language, c.status, "
                    "(SELECT count(*) FROM lessons l WHERE l.course_id = c.id) AS n_lessons "
                    "FROM courses c ORDER BY c.created_at DESC"
                )
            )
        )
        .mappings()
        .all()
    )
    return [{**r, "id": str(r["id"])} for r in rows]


async def _lessons(s: AsyncSession, course_id: str, student_id: str | None = None) -> list[dict]:
    rows = (
        (
            await s.execute(
                text(
                    "SELECT l.id, l.sort_order, l.title, l.kind, l.body, l.content_ref, "
                    "(lp.id IS NOT NULL) AS done "
                    "FROM lessons l "
                    "LEFT JOIN lesson_progress lp "
                    "ON lp.lesson_id = l.id AND lp.student_id = :sid "
                    "WHERE l.course_id = :c ORDER BY l.sort_order"
                ),
                {"c": course_id, "sid": student_id},
            )
        )
        .mappings()
        .all()
    )
    return [
        {
            "id": str(r["id"]),
            "sort_order": r["sort_order"],
            "title": r["title"],
            "kind": r["kind"],
            "body": r["body"],
            "content_ref": str(r["content_ref"]) if r["content_ref"] else None,
            "done": r["done"],
        }
        for r in rows
    ]


async def get_course(s: AsyncSession, course_id: str, student_id: str | None = None) -> dict | None:
    c = (
        (
            await s.execute(
                text("SELECT id, name, language, status FROM courses WHERE id = :id"),
                {"id": course_id},
            )
        )
        .mappings()
        .first()
    )
    if c is None:
        return None
    return {**c, "id": str(c["id"]), "lessons": await _lessons(s, course_id, student_id)}


async def list_student_courses(s: AsyncSession, student_id: str) -> list[dict]:
    """Khóa học của các lớp HS đang học + % tiến độ."""
    rows = (
        (
            await s.execute(
                text(
                    "SELECT DISTINCT c.id, c.name, c.language, "
                    "(SELECT count(*) FROM lessons l WHERE l.course_id = c.id) AS total, "
                    "(SELECT count(*) FROM lessons l "
                    " JOIN lesson_progress lp ON lp.lesson_id = l.id AND lp.student_id = :sid "
                    " WHERE l.course_id = c.id) AS done "
                    "FROM courses c "
                    "JOIN course_classes cc ON cc.course_id = c.id "
                    "JOIN class_students cs ON cs.class_id = cc.class_id AND cs.left_at IS NULL "
                    "WHERE cs.user_id = :sid ORDER BY c.name"
                ),
                {"sid": student_id},
            )
        )
        .mappings()
        .all()
    )
    out = []
    for r in rows:
        total = r["total"]
        done = r["done"]
        out.append(
            {
                "id": str(r["id"]),
                "name": r["name"],
                "language": r["language"],
                "total": total,
                "done": done,
                "progress": round(done * 100.0 / total, 1) if total else 0.0,
            }
        )
    return out


async def _student_in_course_class(s: AsyncSession, student_id: str, lesson_id: str) -> bool:
    return (
        await s.execute(
            text(
                "SELECT 1 FROM lessons l "
                "JOIN course_classes cc ON cc.course_id = l.course_id "
                "JOIN class_students cs ON cs.class_id = cc.class_id AND cs.left_at IS NULL "
                "WHERE l.id = :lid AND cs.user_id = :sid LIMIT 1"
            ),
            {"lid": lesson_id, "sid": student_id},
        )
    ).first() is not None


async def complete_lesson(s: AsyncSession, tenant_id: str, student_id: str, lesson_id: str) -> dict:
    """HS đánh dấu hoàn thành bài (phải thuộc lớp được giao khóa). Cộng điểm. Trả % khóa."""
    if not await _student_in_course_class(s, student_id, lesson_id):
        raise PermissionError("not_your_course")
    await s.execute(
        text(
            "INSERT INTO lesson_progress (tenant_id, student_id, lesson_id) VALUES (:t, :u, :l) "
            "ON CONFLICT (student_id, lesson_id) DO NOTHING"
        ),
        {"t": tenant_id, "u": student_id, "l": lesson_id},
    )
    await game.award_for_lesson(s, tenant_id, student_id, lesson_id)
    prog = (
        (
            await s.execute(
                text(
                    "SELECT "
                    "(SELECT count(*) FROM lessons l2 WHERE l2.course_id = l.course_id) AS total, "
                    "(SELECT count(*) FROM lessons l2 "
                    " JOIN lesson_progress lp ON lp.lesson_id = l2.id AND lp.student_id = :sid "
                    " WHERE l2.course_id = l.course_id) AS done "
                    "FROM lessons l WHERE l.id = :lid"
                ),
                {"lid": lesson_id, "sid": student_id},
            )
        )
        .mappings()
        .one()
    )
    total, done = prog["total"], prog["done"]
    return {
        "done": done,
        "total": total,
        "progress": round(done * 100.0 / total, 1) if total else 0,
    }
