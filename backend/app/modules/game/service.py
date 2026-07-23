"""Gamification: điểm + streak + BXH + huy hiệu. Xem SRS GAME §5, FR-GAME.
M9: điểm cộng tự động (idempotent), streak ngày liên tiếp, BXH lớp, badge cơ bản.
Bảng quy tắc điểm ở mức platform (tenant không sửa) — hằng số dưới đây.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Quy tắc điểm (SRS GAME §5): nộp bài +10, điểm ≥80% +5, hoàn thành lesson +5.
PTS_SUBMIT = 10
PTS_HIGH_SCORE = 5
PTS_LESSON = 5
HIGH_SCORE_THRESHOLD = 80.0

# Catalog huy hiệu (rút gọn M9) — code: (tên, mô tả).
BADGES: dict[str, dict[str, str]] = {
    "first_submission": {"name": "Khởi động", "desc": "Nộp bài đầu tiên"},
    "points_100": {"name": "Trăm điểm", "desc": "Đạt 100 điểm tích lũy"},
    "streak_7": {"name": "Chuỗi 7 ngày", "desc": "Học 7 ngày liên tiếp"},
}


async def award(
    s: AsyncSession,
    tenant_id: str,
    student_id: str,
    points: int,
    reason: str,
    ref_type: str | None,
    ref_id: str | None,
) -> bool:
    """Cộng điểm 1 lần (idempotent theo (student, reason, ref)). True nếu thực sự cộng."""
    r = await s.execute(
        text(
            "INSERT INTO points_ledger (tenant_id, student_id, points, reason, ref_type, ref_id) "
            "VALUES (:t, :u, :p, :rs, :rt, :ri) "
            "ON CONFLICT (student_id, reason, ref_id) DO NOTHING"
        ),
        {"t": tenant_id, "u": student_id, "p": points, "rs": reason, "rt": ref_type, "ri": ref_id},
    )
    return r.rowcount > 0


async def total_points(s: AsyncSession, student_id: str) -> int:
    return (
        await s.execute(
            text("SELECT COALESCE(sum(points), 0) FROM points_ledger WHERE student_id = :u"),
            {"u": student_id},
        )
    ).scalar_one()


async def current_streak(s: AsyncSession, student_id: str) -> int:
    """Số ngày liên tiếp có hoạt động tính điểm, kết thúc hôm nay hoặc hôm qua."""
    from datetime import timedelta

    rows = (
        (
            await s.execute(
                text(
                    "SELECT DISTINCT created_at::date AS d FROM points_ledger "
                    "WHERE student_id = :u ORDER BY d DESC"
                ),
                {"u": student_id},
            )
        )
        .scalars()
        .all()
    )
    if not rows:
        return 0
    today = (await s.execute(text("SELECT now()::date"))).scalar_one()
    # streak phải chạm hôm nay hoặc hôm qua mới còn "sống"
    if rows[0] < today - timedelta(days=1):
        return 0
    streak = 1
    for prev, cur in zip(rows, rows[1:], strict=False):
        if (prev - cur).days == 1:
            streak += 1
        else:
            break
    return streak


async def award_badges(s: AsyncSession, tenant_id: str, student_id: str) -> list[str]:
    """Kiểm tra rule → cấp huy hiệu chưa có. Trả danh sách code vừa cấp."""
    earned: list[str] = []
    total = await total_points(s, student_id)
    streak = await current_streak(s, student_id)
    has_submit = (
        await s.execute(
            text("SELECT 1 FROM points_ledger WHERE student_id = :u AND reason = 'submit' LIMIT 1"),
            {"u": student_id},
        )
    ).first() is not None

    to_grant = []
    if has_submit:
        to_grant.append("first_submission")
    if total >= 100:
        to_grant.append("points_100")
    if streak >= 7:
        to_grant.append("streak_7")
    for code in to_grant:
        r = await s.execute(
            text(
                "INSERT INTO student_badges (tenant_id, student_id, badge_code) "
                "VALUES (:t, :u, :c) ON CONFLICT (student_id, badge_code) DO NOTHING"
            ),
            {"t": tenant_id, "u": student_id, "c": code},
        )
        if r.rowcount > 0:
            earned.append(code)
    return earned


async def list_badges(s: AsyncSession, student_id: str) -> list[dict]:
    codes = (
        (
            await s.execute(
                text(
                    "SELECT badge_code FROM student_badges WHERE student_id = :u ORDER BY earned_at"
                ),
                {"u": student_id},
            )
        )
        .scalars()
        .all()
    )
    return [{"code": c, **BADGES.get(c, {"name": c, "desc": ""})} for c in codes]


async def points_summary(s: AsyncSession, tenant_id: str, student_id: str) -> dict:
    await award_badges(s, tenant_id, student_id)
    return {
        "total": await total_points(s, student_id),
        "streak": await current_streak(s, student_id),
        "badges": await list_badges(s, student_id),
    }


async def class_leaderboard(s: AsyncSession, class_id: str) -> list[dict]:
    rows = (
        (
            await s.execute(
                text(
                    "SELECT cs.user_id AS student_id, "
                    "COALESCE(NULLIF(u.full_name, ''), u.username) AS full_name, "
                    "COALESCE(sum(pl.points), 0) AS points "
                    "FROM class_students cs "
                    "JOIN users u ON u.id = cs.user_id "
                    "LEFT JOIN points_ledger pl ON pl.student_id = cs.user_id "
                    "WHERE cs.class_id = :c AND cs.left_at IS NULL "
                    "GROUP BY cs.user_id, u.full_name, u.username "
                    "ORDER BY points DESC, full_name"
                ),
                {"c": class_id},
            )
        )
        .mappings()
        .all()
    )
    return [
        {
            "rank": i + 1,
            "student_id": str(r["student_id"]),
            "full_name": r["full_name"],
            "points": r["points"],
        }
        for i, r in enumerate(rows)
    ]


async def award_for_submission(
    s: AsyncSession, tenant_id: str, attempt_id: str, score: float
) -> None:
    """Nộp bài → +10 (lần đầu theo assignee); điểm ≥80% → +5. Cấp badge."""
    info = (
        (
            await s.execute(
                text(
                    "SELECT aa.id AS assignee_id, aa.student_id FROM attempts at "
                    "JOIN assignment_assignees aa ON aa.id = at.assignee_id WHERE at.id = :att"
                ),
                {"att": attempt_id},
            )
        )
        .mappings()
        .first()
    )
    if info is None:
        return
    assignee = str(info["assignee_id"])
    student = str(info["student_id"])
    await award(s, tenant_id, student, PTS_SUBMIT, "submit", "assignee", assignee)
    if score >= HIGH_SCORE_THRESHOLD:
        await award(s, tenant_id, student, PTS_HIGH_SCORE, "high_score", "assignee", assignee)
    await award_badges(s, tenant_id, student)


async def award_for_lesson(
    s: AsyncSession, tenant_id: str, student_id: str, lesson_id: str
) -> None:
    """Hoàn thành lesson → +5 (lần đầu). Cấp badge."""
    await award(s, tenant_id, student_id, PTS_LESSON, "lesson", "lesson", lesson_id)
    await award_badges(s, tenant_id, student_id)
