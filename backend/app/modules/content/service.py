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

    # audio đính kèm (câu nghe): key trả về từ POST /media, đi kèm content sang màn làm bài
    audio_key = content.get("audio_key")
    if audio_key is not None and not isinstance(audio_key, str):
        raise InvalidContent("audio_key_must_be_string")

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
            "difficulty, status, current_version_id, created_by, folder_id) "
            "VALUES (:id, :t, :ty, :lang, :sk, :lv, :ex, :tp, :df, 'draft', :vid, :by, :fold)"
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
            "fold": data.get("folder_id"),
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


async def list_questions(
    s: AsyncSession, filters: dict[str, Any], limit: int = 50, offset: int = 0
) -> list[dict]:
    sql = (
        "SELECT q.id, q.type, q.language, q.skill, q.level, q.exam_tag, q.topic, q.status, "
        "q.folder_id, v.content->>'prompt' AS prompt "
        "FROM questions q LEFT JOIN question_versions v ON v.id = q.current_version_id "
        "WHERE 1=1"
    )
    p: dict[str, Any] = {"lim": max(1, min(limit, 200)), "off": max(0, offset)}
    for col in ("language", "skill", "level", "status", "exam_tag", "topic"):
        if filters.get(col):
            sql += f" AND q.{col} = :{col}"
            p[col] = filters[col]
    # lọc theo thư mục: 'none' = chưa phân loại; giá trị khác = đúng thư mục đó
    if filters.get("folder_id") == "none":
        sql += " AND q.folder_id IS NULL"
    elif filters.get("folder_id"):
        sql += " AND q.folder_id = :folder_id"
        p["folder_id"] = filters["folder_id"]
    if not filters.get("status"):
        # mặc định ẩn câu đã lưu trữ (chỉ hiện khi lọc status=archived tường minh)
        sql += " AND q.status != 'archived'"
    sql += " ORDER BY q.created_at DESC LIMIT :lim OFFSET :off"
    rows = (await s.execute(text(sql), p)).mappings().all()
    return [
        {**r, "id": str(r["id"]), "folder_id": str(r["folder_id"]) if r["folder_id"] else None}
        for r in rows
    ]


async def archive_question(s: AsyncSession, qid: str) -> None:
    """Lưu trữ (ẩn khỏi kho + không giao mới); bài đã giao vẫn giữ version cũ."""
    r = (
        await s.execute(
            text("UPDATE questions SET status = 'archived', updated_at = now() WHERE id = :id"),
            {"id": qid},
        )
    ).rowcount
    if r == 0:
        raise KeyError("not_found")


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


# ── Cây thư mục kho câu hỏi (SRS CONTENT — tổ chức kho) ────────────────


class FolderNotEmpty(Exception):
    pass


async def create_folder(s: AsyncSession, tenant_id: str, name: str, parent_id: str | None) -> str:
    import uuid as _uuid

    fid = str(_uuid.uuid4())
    await s.execute(
        text(
            "INSERT INTO question_folders (id, tenant_id, parent_id, name) VALUES (:id, :t, :p, :n)"
        ),
        {"id": fid, "t": tenant_id, "p": parent_id, "n": name},
    )
    return fid


async def rename_folder(s: AsyncSession, folder_id: str, name: str) -> None:
    r = (
        await s.execute(
            text("UPDATE question_folders SET name = :n WHERE id = :id"),
            {"n": name, "id": folder_id},
        )
    ).rowcount
    if r == 0:
        raise KeyError("not_found")


async def delete_folder(s: AsyncSession, folder_id: str) -> None:
    """Chỉ xóa thư mục RỖNG (không câu hỏi, không thư mục con) — tránh mất dữ liệu."""
    n_children = (
        await s.execute(
            text("SELECT count(*) FROM question_folders WHERE parent_id = :id"),
            {"id": folder_id},
        )
    ).scalar_one()
    n_questions = (
        await s.execute(
            text("SELECT count(*) FROM questions WHERE folder_id = :id"), {"id": folder_id}
        )
    ).scalar_one()
    if n_children or n_questions:
        raise FolderNotEmpty(f"folder_not_empty:{n_questions}q,{n_children}f")
    r = (
        await s.execute(text("DELETE FROM question_folders WHERE id = :id"), {"id": folder_id})
    ).rowcount
    if r == 0:
        raise KeyError("not_found")


async def list_folders(s: AsyncSession) -> list[dict]:
    """Danh sách phẳng kèm số câu — FE tự dựng cây theo parent_id."""
    rows = (
        (
            await s.execute(
                text(
                    "SELECT f.id, f.parent_id, f.name, f.sort_order, "
                    "(SELECT count(*) FROM questions q "
                    " WHERE q.folder_id = f.id AND q.status != 'archived') AS n_questions "
                    "FROM question_folders f ORDER BY f.sort_order, f.name"
                )
            )
        )
        .mappings()
        .all()
    )
    return [
        {
            "id": str(r["id"]),
            "parent_id": str(r["parent_id"]) if r["parent_id"] else None,
            "name": r["name"],
            "n_questions": r["n_questions"],
        }
        for r in rows
    ]


async def move_question(s: AsyncSession, qid: str, folder_id: str | None) -> None:
    """Chuyển câu hỏi sang thư mục (None = về Chưa phân loại)."""
    r = (
        await s.execute(
            text("UPDATE questions SET folder_id = :f, updated_at = now() WHERE id = :id"),
            {"f": folder_id, "id": qid},
        )
    ).rowcount
    if r == 0:
        raise KeyError("not_found")
