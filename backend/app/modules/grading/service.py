"""Chấm bài 3 tầng. Xem SRS GRADE §5, FR-GRADE-01/04.
M4: câu đóng (mcq_single, fill_blank) chấm tức thì.
M6: câu mở (writing) → hàng đợi chấm AI sơ bộ (quota tenant, degrade khi lỗi) → GV chốt.
Điểm mỗi câu tính 1 điểm; câu mở đóng góp final_score (0..1). Submission provisional khi
còn câu mở chưa chốt.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.grading.ai import get_grader

# Loại câu mở: không chấm tự động, đẩy hàng đợi AI → GV chốt.
OPEN_TYPES = {"writing"}


def _period() -> str:
    return datetime.now(UTC).strftime("%Y-%m")


def _band_for(scale: list[dict[str, Any]] | None, pct: float) -> str | None:
    """Quy đổi % → band: mốc có min lớn nhất mà ≤ pct (đồng bộ exam.service.band_for)."""
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


async def _total_questions(s: AsyncSession, attempt_id: str) -> int:
    return (
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


async def _recompute_submission(s: AsyncSession, tenant_id: str, attempt_id: str) -> dict:
    """Tính lại điểm từ trạng thái answers hiện tại; upsert submission.

    Điểm = (số câu đóng đúng + tổng final_score câu mở đã chốt) / tổng số câu * 100.
    status = provisional nếu còn câu mở chưa chốt (pending/ai_graded/needs_manual), else final.
    """
    total = await _total_questions(s, attempt_id)
    agg = (
        (
            await s.execute(
                text(
                    "SELECT "
                    "count(*) FILTER (WHERE is_correct IS TRUE) AS closed_correct, "
                    "COALESCE(sum(final_score) FILTER (WHERE grade_status = 'finalized'), 0) "
                    "AS open_points, "
                    "count(*) FILTER (WHERE grade_status IN "
                    "('pending', 'ai_graded', 'needs_manual')) AS pending_open "
                    "FROM answers WHERE attempt_id = :att"
                ),
                {"att": attempt_id},
            )
        )
        .mappings()
        .one()
    )
    closed_correct = agg["closed_correct"]
    points = float(closed_correct) + float(agg["open_points"])
    pending_open = agg["pending_open"]
    score = round(points * 100.0 / total, 2) if total else 0.0
    status = "provisional" if pending_open > 0 else "final"
    await s.execute(
        text(
            "INSERT INTO submissions "
            "(tenant_id, attempt_id, correct_count, total_count, score, status) "
            "VALUES (:t, :att, :c, :tot, :sc, :st) "
            "ON CONFLICT (attempt_id) DO UPDATE SET "
            "correct_count = EXCLUDED.correct_count, total_count = EXCLUDED.total_count, "
            "score = EXCLUDED.score, status = EXCLUDED.status, graded_at = now()"
        ),
        {
            "t": tenant_id,
            "att": attempt_id,
            "c": closed_correct,
            "tot": total,
            "sc": score,
            "st": status,
        },
    )
    return {
        "correct_count": closed_correct,
        "total_count": total,
        "score": score,
        "status": status,
        "pending_open": pending_open,
    }


async def grade_attempt(s: AsyncSession, tenant_id: str, attempt_id: str) -> dict:
    """Chấm câu đóng ngay; câu mở đẩy hàng đợi AI (job pending). Upsert submission."""
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
    for r in rows:
        if r["type"] in OPEN_TYPES:
            # câu mở: đưa vào hàng đợi chấm AI, đánh dấu pending
            await s.execute(
                text(
                    "INSERT INTO grading_jobs (tenant_id, attempt_id, answer_id) "
                    "VALUES (:t, :att, :ans) ON CONFLICT (answer_id) DO NOTHING"
                ),
                {"t": tenant_id, "att": attempt_id, "ans": r["answer_id"]},
            )
            await s.execute(
                text("UPDATE answers SET grade_status = 'pending' WHERE id = :id"),
                {"id": r["answer_id"]},
            )
            continue
        ok = grade_answer(r["type"], r["payload"], r["answer_key"])
        await s.execute(
            text("UPDATE answers SET is_correct = :c WHERE id = :id"),
            {"c": ok, "id": r["answer_id"]},
        )
    return await _recompute_submission(s, tenant_id, attempt_id)


async def _ensure_quota_row(s: AsyncSession, tenant_id: str, period: str) -> None:
    await s.execute(
        text(
            "INSERT INTO tenant_ai_quota (tenant_id, period, writing_limit) "
            "VALUES (:t, :p, :lim) ON CONFLICT (tenant_id, period) DO NOTHING"
        ),
        {"t": tenant_id, "p": period, "lim": settings.ai_writing_quota_default},
    )


async def _consume_quota(s: AsyncSession, tenant_id: str, period: str) -> bool:
    """Trừ 1 lượt writing nếu còn hạn mức. True = còn quota, False = vượt (soft-block)."""
    r = (
        await s.execute(
            text(
                "UPDATE tenant_ai_quota SET writing_used = writing_used + 1 "
                "WHERE tenant_id = :t AND period = :p AND writing_used < writing_limit "
                "RETURNING id"
            ),
            {"t": tenant_id, "p": period},
        )
    ).first()
    return r is not None


async def _refund_quota(s: AsyncSession, tenant_id: str, period: str) -> None:
    await s.execute(
        text(
            "UPDATE tenant_ai_quota SET writing_used = GREATEST(writing_used - 1, 0) "
            "WHERE tenant_id = :t AND period = :p"
        ),
        {"t": tenant_id, "p": period},
    )


async def process_attempt_ai(s: AsyncSession, tenant_id: str, attempt_id: str) -> dict:
    """Rút hàng đợi câu mở của attempt: chấm AI nếu còn quota, degrade sang chấm tay
    khi vượt quota hoặc AI lỗi. Không đổi điểm submission (chờ GV chốt)."""
    period = _period()
    await _ensure_quota_row(s, tenant_id, period)
    grader = get_grader()
    jobs = (
        (
            await s.execute(
                text(
                    "SELECT gj.id AS job_id, gj.answer_id, ans.payload, v.content "
                    "FROM grading_jobs gj "
                    "JOIN answers ans ON ans.id = gj.answer_id "
                    "JOIN question_versions v ON v.id = ans.question_version_id "
                    "WHERE gj.attempt_id = :att AND gj.status = 'pending'"
                ),
                {"att": attempt_id},
            )
        )
        .mappings()
        .all()
    )
    ai_graded = 0
    needs_manual = 0
    for j in jobs:
        answer_text = (j["payload"] or {}).get("text", "")
        content = j["content"] or {}
        if not await _consume_quota(s, tenant_id, period):
            await _degrade(s, j["job_id"], j["answer_id"])  # vượt quota
            needs_manual += 1
            continue
        try:
            g = grader.grade_writing(
                content.get("prompt", ""), content.get("rubric", ""), answer_text
            )
        except Exception:  # noqa: BLE001 — AI lỗi thì degrade, không làm hỏng luồng nộp
            await _refund_quota(s, tenant_id, period)
            await _degrade(s, j["job_id"], j["answer_id"])
            needs_manual += 1
            continue
        await s.execute(
            text(
                "UPDATE answers SET ai_score = :sc, ai_feedback = :fb, ai_confidence = :cf, "
                "grade_status = 'ai_graded' WHERE id = :id"
            ),
            {"sc": g.score, "fb": g.feedback, "cf": g.confidence, "id": j["answer_id"]},
        )
        await s.execute(
            text(
                "UPDATE grading_jobs SET status = 'ai_graded', "
                "priority = CASE WHEN :cf < 0.6 THEN 1 ELSE 0 END, updated_at = now() "
                "WHERE id = :id"
            ),
            {"cf": g.confidence, "id": j["job_id"]},
        )
        ai_graded += 1
    return {"ai_graded": ai_graded, "needs_manual": needs_manual}


async def _degrade(s: AsyncSession, job_id: str, answer_id: str) -> None:
    """AI không chấm được (vượt quota / lỗi) → chuyển câu sang chấm tay, ưu tiên cao."""
    await s.execute(
        text(
            "UPDATE grading_jobs SET status = 'needs_manual', priority = 2, updated_at = now() "
            "WHERE id = :id"
        ),
        {"id": job_id},
    )
    await s.execute(
        text("UPDATE answers SET grade_status = 'needs_manual' WHERE id = :id"),
        {"id": answer_id},
    )


async def finalize_open_answer(
    s: AsyncSession, tenant_id: str, answer_id: str, final_score: float, feedback: str | None
) -> dict:
    """GV chốt 1 câu mở: đặt final_score + (nhận xét) → finalized; tính lại submission."""
    row = (
        await s.execute(
            text("SELECT attempt_id, grade_status FROM answers WHERE id = :id"),
            {"id": answer_id},
        )
    ).first()
    if row is None:
        raise KeyError("answer_not_found")
    attempt_id, grade_status = str(row[0]), row[1]
    if grade_status not in ("ai_graded", "needs_manual", "finalized"):
        raise ValueError("not_reviewable")
    score = max(0.0, min(1.0, float(final_score)))
    if feedback is not None:
        await s.execute(
            text(
                "UPDATE answers SET final_score = :fs, ai_feedback = :fb, "
                "grade_status = 'finalized' WHERE id = :id"
            ),
            {"fs": score, "fb": feedback, "id": answer_id},
        )
    else:
        await s.execute(
            text("UPDATE answers SET final_score = :fs, grade_status = 'finalized' WHERE id = :id"),
            {"fs": score, "id": answer_id},
        )
    await s.execute(
        text(
            "UPDATE grading_jobs SET status = 'finalized', updated_at = now() WHERE answer_id = :id"
        ),
        {"id": answer_id},
    )
    return await _recompute_submission(s, tenant_id, attempt_id)


async def get_result(s: AsyncSession, attempt_id: str) -> dict | None:
    sub = (
        (
            await s.execute(
                text(
                    "SELECT correct_count, total_count, score, status "
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
    # review từng câu (đáp án đúng lộ sau khi nộp; câu mở kèm trạng thái chấm AI/GV)
    review = (
        (
            await s.execute(
                text(
                    "SELECT pq.sort_order, q.type, v.content, v.answer_key, v.explanation, "
                    "ans.payload, ans.is_correct, ans.grade_status, ans.ai_score, "
                    "ans.ai_feedback, ans.final_score "
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

    def _num(v):
        return float(v) if v is not None else None

    # đề thi: quy đổi điểm % → band theo bảng của exam_meta
    exam = (
        (
            await s.execute(
                text(
                    "SELECT em.band_scale, em.duration_minutes FROM attempts at "
                    "JOIN assignment_assignees aa ON aa.id = at.assignee_id "
                    "JOIN assignments a ON a.id = aa.assignment_id "
                    "JOIN exam_meta em ON em.content_id = a.content_id "
                    "WHERE at.id = :att"
                ),
                {"att": attempt_id},
            )
        )
        .mappings()
        .first()
    )
    is_exam = exam is not None
    band = _band_for(exam["band_scale"], float(sub["score"])) if is_exam else None

    return {
        "correct_count": sub["correct_count"],
        "total_count": sub["total_count"],
        "score": float(sub["score"]),
        "status": sub["status"],
        "is_exam": is_exam,
        "band": band,
        "duration_minutes": exam["duration_minutes"] if is_exam else None,
        "review": [
            {
                "sort_order": r["sort_order"],
                "type": r["type"],
                "content": r["content"],
                "answer_key": r["answer_key"],
                "explanation": r["explanation"],
                "your_answer": r["payload"],
                "is_correct": r["is_correct"],
                "grade_status": r["grade_status"],
                # điểm AI chỉ lộ khi đã có điểm chốt; trước đó chỉ hiện "chờ GV duyệt"
                "ai_feedback": r["ai_feedback"] if r["grade_status"] == "finalized" else None,
                "final_score": _num(r["final_score"]),
            }
            for r in review
        ],
    }
