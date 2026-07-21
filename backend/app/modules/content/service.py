"""Ngân hàng câu hỏi: validate nội dung theo loại, tạo/sửa (versioning), publish, tìm kiếm.
Xem SRS CONTENT + phụ lục loại câu hỏi. M2: mcq_single, fill_blank.
"""

import json
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

SUPPORTED_TYPES = {"mcq_single", "fill_blank", "writing"}
# Loại câu mở (không có đáp án cố định) — chấm AI sơ bộ → GV chốt (M6).
OPEN_TYPES = {"writing"}


class InvalidContent(Exception):
    pass


def validate_content(qtype: str, content: dict[str, Any], answer_key: dict[str, Any]) -> None:
    if qtype not in SUPPORTED_TYPES:
        raise InvalidContent(f"unsupported_type:{qtype}")

    if qtype == "mcq_single":
        prompt = content.get("prompt")
        options = content.get("options")
        if not isinstance(prompt, str) or not prompt.strip():
            raise InvalidContent("missing_prompt")
        if not isinstance(options, list) or len(options) < 2:
            raise InvalidContent("need_at_least_2_options")
        idx = answer_key.get("correct_index")
        if not isinstance(idx, int) or not (0 <= idx < len(options)):
            raise InvalidContent("correct_index_out_of_range")

    elif qtype == "writing":
        prompt = content.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise InvalidContent("missing_prompt")
        rubric = content.get("rubric")
        if rubric is not None and not isinstance(rubric, str):
            raise InvalidContent("rubric_must_be_text")
        # câu mở: không có answer_key cố định

    elif qtype == "fill_blank":
        prompt = content.get("prompt")
        if not isinstance(prompt, str) or "___" not in prompt:
            raise InvalidContent("prompt_needs_blank_marker")
        n_blanks = prompt.count("___")
        blanks = answer_key.get("blanks")
        if not isinstance(blanks, list) or len(blanks) != n_blanks:
            raise InvalidContent("blanks_count_mismatch")
        for accepted in blanks:
            if not isinstance(accepted, list) or not accepted:
                raise InvalidContent("blank_needs_accepted_answers")


async def create_question(
    s: AsyncSession, tenant_id: str, creator: str, data: dict[str, Any]
) -> str:
    validate_content(data["type"], data["content"], data["answer_key"])
    qid = str(uuid.uuid4())
    vid = str(uuid.uuid4())
    await s.execute(
        text(
            "INSERT INTO questions (id, tenant_id, type, language, skill, level, exam_tag, topic, "
            "difficulty, status, current_version_id, created_by) "
            "VALUES (:id, :t, :ty, :lang, :sk, :lv, :ex, :tp, :df, 'draft', :vid, :by)"
        ),
        {
            "id": qid,
            "t": tenant_id,
            "ty": data["type"],
            "lang": data["language"],
            "sk": data.get("skill"),
            "lv": data.get("level"),
            "ex": data.get("exam_tag"),
            "tp": data.get("topic"),
            "df": data.get("difficulty"),
            "vid": vid,
            "by": creator,
        },
    )
    await _insert_version(s, tenant_id, qid, vid, 1, data, creator)
    return qid


async def _insert_version(
    s: AsyncSession,
    tenant_id: str,
    qid: str,
    vid: str,
    version_no: int,
    data: dict[str, Any],
    creator: str,
) -> None:
    await s.execute(
        text(
            "INSERT INTO question_versions (id, tenant_id, question_id, version_no, content, "
            "answer_key, explanation, created_by) "
            "VALUES (:id, :t, :q, :vn, CAST(:c AS jsonb), CAST(:a AS jsonb), :e, :by)"
        ),
        {
            "id": vid,
            "t": tenant_id,
            "q": qid,
            "vn": version_no,
            "c": json.dumps(data["content"], ensure_ascii=False),
            "a": json.dumps(data["answer_key"], ensure_ascii=False),
            "e": data.get("explanation"),
            "by": creator,
        },
    )


async def get_question_type(s: AsyncSession, qid: str) -> str | None:
    return (
        await s.execute(text("SELECT type FROM questions WHERE id = :id"), {"id": qid})
    ).scalar_one_or_none()


async def update_question(
    s: AsyncSession, tenant_id: str, qid: str, creator: str, data: dict[str, Any]
) -> int:
    qtype = await get_question_type(s, qid)
    if qtype is None:
        raise KeyError("not_found")
    validate_content(qtype, data["content"], data["answer_key"])
    next_no = (
        await s.execute(
            text(
                "SELECT COALESCE(MAX(version_no), 0) + 1 "
                "FROM question_versions WHERE question_id = :q"
            ),
            {"q": qid},
        )
    ).scalar_one()
    vid = str(uuid.uuid4())
    await _insert_version(s, tenant_id, qid, vid, next_no, {**data, "type": qtype}, creator)
    # nếu đã published thì trỏ current sang version mới
    await s.execute(
        text("UPDATE questions SET current_version_id = :vid, updated_at = now() WHERE id = :id"),
        {"vid": vid, "id": qid},
    )
    return next_no


async def publish_question(s: AsyncSession, qid: str) -> None:
    r = (
        await s.execute(text("SELECT 1 FROM questions WHERE id = :id"), {"id": qid})
    ).scalar_one_or_none()
    if r is None:
        raise KeyError("not_found")
    await s.execute(
        text("UPDATE questions SET status = 'published', updated_at = now() WHERE id = :id"),
        {"id": qid},
    )


async def list_questions(s: AsyncSession, filters: dict[str, Any]) -> list[dict]:
    sql = (
        "SELECT q.id, q.type, q.language, q.skill, q.level, q.exam_tag, q.topic, q.status, "
        "v.content->>'prompt' AS prompt "
        "FROM questions q LEFT JOIN question_versions v ON v.id = q.current_version_id "
        "WHERE 1=1"
    )
    p: dict[str, Any] = {}
    for col in ("language", "skill", "level", "status", "exam_tag"):
        if filters.get(col):
            sql += f" AND q.{col} = :{col}"
            p[col] = filters[col]
    sql += " ORDER BY q.created_at DESC LIMIT 200"
    rows = (await s.execute(text(sql), p)).mappings().all()
    return [{**r, "id": str(r["id"])} for r in rows]


async def get_question(s: AsyncSession, qid: str) -> dict | None:
    row = (
        (
            await s.execute(
                text(
                    "SELECT q.id, q.type, q.language, q.skill, q.level, q.exam_tag, q.topic, "
                    "q.status, v.version_no, v.content, v.answer_key, v.explanation "
                    "FROM questions q JOIN question_versions v ON v.id = q.current_version_id "
                    "WHERE q.id = :id"
                ),
                {"id": qid},
            )
        )
        .mappings()
        .first()
    )
    return {**row, "id": str(row["id"])} if row else None
