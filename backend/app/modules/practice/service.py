"""Lắp ráp practice từ câu hỏi đã publish; view làm bài ẩn đáp án.
Xem SRS PRACTICE. M3: câu đóng (mcq_single, fill_blank).
"""

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class InvalidQuestion(Exception):
    pass


async def create_practice(
    s: AsyncSession, tenant_id: str, creator: str, data: dict[str, Any]
) -> str:
    question_ids: list[str] = data["question_ids"]
    if not question_ids:
        raise InvalidQuestion("empty_practice")

    # Lấy current_version_id của các câu đã publish, đúng thứ tự yêu cầu
    version_by_q: dict[str, str] = {}
    rows = (
        (
            await s.execute(
                text(
                    "SELECT id, current_version_id FROM questions "
                    "WHERE id = ANY(:ids) AND status = 'published' "
                    "AND current_version_id IS NOT NULL"
                ),
                {"ids": question_ids},
            )
        )
        .mappings()
        .all()
    )
    for r in rows:
        version_by_q[str(r["id"])] = str(r["current_version_id"])
    missing = [q for q in question_ids if q not in version_by_q]
    if missing:
        raise InvalidQuestion(f"not_published_or_missing:{missing[0]}")

    pid = str(uuid.uuid4())
    await s.execute(
        text(
            "INSERT INTO practices (id, tenant_id, name, skill, language, created_by) "
            "VALUES (:id, :t, :n, :sk, :lang, :by)"
        ),
        {
            "id": pid,
            "t": tenant_id,
            "n": data["name"],
            "sk": data.get("skill"),
            "lang": data.get("language", "en"),
            "by": creator,
        },
    )
    for order, qid in enumerate(question_ids):
        await s.execute(
            text(
                "INSERT INTO practice_questions "
                "(tenant_id, practice_id, question_version_id, sort_order) "
                "VALUES (:t, :p, :v, :o)"
            ),
            {"t": tenant_id, "p": pid, "v": version_by_q[qid], "o": order},
        )
    return pid


async def list_practices(s: AsyncSession) -> list[dict]:
    rows = (
        (
            await s.execute(
                text(
                    "SELECT p.id, p.name, p.skill, p.language, p.status, "
                    "(SELECT count(*) FROM practice_questions pq "
                    "WHERE pq.practice_id = p.id) AS n_q "
                    "FROM practices p ORDER BY p.created_at DESC LIMIT 200"
                )
            )
        )
        .mappings()
        .all()
    )
    return [{**r, "id": str(r["id"]), "n_q": int(r["n_q"])} for r in rows]


async def _questions(s: AsyncSession, practice_id: str, *, hide_answer: bool) -> list[dict]:
    rows = (
        (
            await s.execute(
                text(
                    "SELECT pq.sort_order, pq.question_version_id, q.type, "
                    "v.content, v.answer_key "
                    "FROM practice_questions pq "
                    "JOIN question_versions v ON v.id = pq.question_version_id "
                    "JOIN questions q ON q.id = v.question_id "
                    "WHERE pq.practice_id = :p ORDER BY pq.sort_order"
                ),
                {"p": practice_id},
            )
        )
        .mappings()
        .all()
    )
    out = []
    for r in rows:
        item = {
            "question_version_id": str(r["question_version_id"]),
            "type": r["type"],
            "content": r["content"],
            "sort_order": r["sort_order"],
        }
        if not hide_answer:
            item["answer_key"] = r["answer_key"]
        out.append(item)
    return out


async def get_practice(s: AsyncSession, practice_id: str, *, for_attempt: bool) -> dict | None:
    p = (
        (
            await s.execute(
                text("SELECT id, name, skill, language, status FROM practices WHERE id = :id"),
                {"id": practice_id},
            )
        )
        .mappings()
        .first()
    )
    if p is None:
        return None
    return {
        **p,
        "id": str(p["id"]),
        "questions": await _questions(s, practice_id, hide_answer=for_attempt),
    }
