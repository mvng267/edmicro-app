"""AI sinh câu hỏi vào kho (draft — GV duyệt/sửa/xuất bản tay).
Dùng chung endpoint OpenAI-compatible với chấm writing (grading.ai.chat_json).
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.content import service as content_svc
from app.modules.grading.ai import ai_available, chat_json


class AIUnavailable(Exception):
    pass


class AIGenerateFailed(Exception):
    pass


_SYSTEM = (
    "Bạn là chuyên gia soạn đề cho trung tâm ngoại ngữ. Sinh câu hỏi CHUẨN, đa dạng, "
    "đúng trình độ. Trả về DUY NHẤT một mảng JSON, mỗi phần tử theo đúng schema:\n"
    '- mcq_single: {"type":"mcq_single","prompt":"...","options":["A","B","C","D"],'
    '"correct_index":0,"explanation":"giải thích ngắn"}\n'
    '- fill_blank: {"type":"fill_blank","prompt":"câu có ___ tại chỗ trống",'
    '"blanks":[["đáp án","biến thể chấp nhận"]],"explanation":"..."}\n'
    "Số phần tử ĐÚNG BẰNG số câu được yêu cầu. prompt/option viết bằng ngôn ngữ đang học; "
    "explanation bằng tiếng Việt."
)


async def generate_questions(
    s: AsyncSession,
    tenant_id: str,
    creator: str,
    *,
    topic: str,
    skill: str,
    qtype: str,
    count: int,
    language: str = "en",
    folder_id: str | None = None,
) -> list[str]:
    """Sinh `count` câu (draft) vào kho/thư mục. Trả danh sách question_id."""
    if not ai_available():
        raise AIUnavailable("ai_not_configured")
    if qtype not in ("mcq_single", "fill_blank"):
        raise AIGenerateFailed(f"unsupported_type:{qtype}")
    count = max(1, min(int(count), 10))

    user = (
        f"Sinh {count} câu loại {qtype}, kỹ năng {skill}, ngôn ngữ đang học: {language}. "
        f"Chủ đề: {topic}."
    )
    try:
        data = chat_json(_SYSTEM, user, max_tokens=3000)
    except Exception as e:  # noqa: BLE001 — mạng/parse lỗi → báo FE, không 500 thô
        raise AIGenerateFailed(f"ai_error:{type(e).__name__}") from e
    if not isinstance(data, list):
        raise AIGenerateFailed("ai_bad_format")

    created: list[str] = []
    for item in data[:count]:
        try:
            if item.get("type", qtype) == "fill_blank" or qtype == "fill_blank":
                content: dict[str, Any] = {"prompt": item["prompt"]}
                answer_key: dict[str, Any] = {"blanks": item["blanks"]}
                q_type = "fill_blank"
            else:
                content = {"prompt": item["prompt"], "options": item["options"]}
                answer_key = {"correct_index": int(item["correct_index"])}
                q_type = "mcq_single"
            qid = await content_svc.create_question(
                s,
                tenant_id,
                creator,
                {
                    "type": q_type,
                    "language": language,
                    "skill": skill,
                    "topic": topic[:80] or None,
                    "content": content,
                    "answer_key": answer_key,
                    "explanation": item.get("explanation"),
                    "folder_id": folder_id,
                },
            )
            created.append(qid)
        except (content_svc.InvalidContent, KeyError, TypeError, ValueError):
            continue  # câu lỗi schema thì bỏ, giữ các câu hợp lệ
    if not created:
        raise AIGenerateFailed("no_valid_questions")
    return created
