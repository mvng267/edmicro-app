"""Chấm tự động câu đóng khi nộp bài. Xem SRS GRADE FR-GRADE-01.
M4: mcq_single, fill_blank. Điểm là final ngay (không tầng GV cho câu đóng).
"""

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def grade_answer(
    qtype: str, payload: dict[str, Any] | None, answer_key: dict[str, Any]
) -> bool | None:
    """True/False nếu chấm được; None nếu loại chưa hỗ trợ chấm tự động."""
    if payload is None:
        return False
    if qtype == "mcq_single":
        return payload.get("selected") == answer_key.get("correct_index")
    if qtype == "fill_blank":
        filled = payload.get("blanks") or []
        accepted_all = answer_key.get("blanks") or []
        if len(filled) != len(accepted_all):
            return False
        for got, accepted in zip(filled, accepted_all, strict=False):
            got_norm = str(got).strip().lower()
            if got_norm not in [str(a).strip().lower() for a in accepted]:
                return False
        return True
    return None


async def grade_attempt(s: AsyncSession, tenant_id: str, attempt_id: str) -> dict:
    """Chấm mọi câu của attempt; câu không trả lời tính sai. Upsert submission."""
    # tổng số câu của practice tương ứng attempt
    total = (
        await s.execute(
            text(
                "SELECT count(*) FROM practice_questions pq "
                "JOIN assignments a ON a.content_id = pq.practice_id "
                "JOIN assignment_assignees aa ON aa.assignment_id = a.id "
                "JOIN attempts at ON at.assignee_id = aa.id "
                "WHERE at.id = :att"
            ),
            {"att": attempt_id},
        )
    ).scalar_one()

    # các câu đã trả lời + type/answer_key
    rows = (
        (
            await s.execute(
                text(
                    "SELECT ans.id AS answer_id, ans.payload, q.type, v.answer_key "
                    "FROM answers ans "
                    "JOIN question_versions v ON v.id = ans.question_version_id "
                    "JOIN questions q ON q.id = v.question_id "
                    "WHERE ans.attempt_id = :att"
                ),
                {"att": attempt_id},
            )
        )
        .mappings()
        .all()
    )

    correct = 0
    for r in rows:
        ok = grade_answer(r["type"], r["payload"], r["answer_key"])
        await s.execute(
            text("UPDATE answers SET is_correct = :c WHERE id = :id"),
            {"c": ok, "id": r["answer_id"]},
        )
        if ok:
            correct += 1

    score = round(correct * 100.0 / total, 2) if total else 0.0
    await s.execute(
        text(
            "INSERT INTO submissions (tenant_id, attempt_id, correct_count, total_count, score) "
            "VALUES (:t, :att, :c, :tot, :sc) "
            "ON CONFLICT (attempt_id) DO UPDATE SET "
            "correct_count = EXCLUDED.correct_count, total_count = EXCLUDED.total_count, "
            "score = EXCLUDED.score, graded_at = now()"
        ),
        {"t": tenant_id, "att": attempt_id, "c": correct, "tot": total, "sc": score},
    )
    return {"correct_count": correct, "total_count": total, "score": score}


async def get_result(s: AsyncSession, attempt_id: str) -> dict | None:
    sub = (
        (
            await s.execute(
                text(
                    "SELECT correct_count, total_count, score "
                    "FROM submissions WHERE attempt_id = :att"
                ),
                {"att": attempt_id},
            )
        )
        .mappings()
        .first()
    )
    if sub is None:
        return None
    # review từng câu (đáp án đúng lộ sau khi nộp)
    review = (
        (
            await s.execute(
                text(
                    "SELECT pq.sort_order, q.type, v.content, v.answer_key, v.explanation, "
                    "ans.payload, ans.is_correct "
                    "FROM practice_questions pq "
                    "JOIN question_versions v ON v.id = pq.question_version_id "
                    "JOIN questions q ON q.id = v.question_id "
                    "JOIN assignments a ON a.content_id = pq.practice_id "
                    "JOIN assignment_assignees aa ON aa.assignment_id = a.id "
                    "JOIN attempts at ON at.assignee_id = aa.id "
                    "LEFT JOIN answers ans "
                    "ON ans.attempt_id = at.id "
                    "AND ans.question_version_id = pq.question_version_id "
                    "WHERE at.id = :att ORDER BY pq.sort_order"
                ),
                {"att": attempt_id},
            )
        )
        .mappings()
        .all()
    )
    return {
        "correct_count": sub["correct_count"],
        "total_count": sub["total_count"],
        "score": float(sub["score"]),
        "review": [
            {
                "sort_order": r["sort_order"],
                "type": r["type"],
                "content": r["content"],
                "answer_key": r["answer_key"],
                "explanation": r["explanation"],
                "your_answer": r["payload"],
                "is_correct": r["is_correct"],
            }
            for r in review
        ],
    }
