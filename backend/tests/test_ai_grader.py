import pytest

from app.modules.content.service import InvalidContent, validate_content
from app.modules.grading.ai import FakeGrader, get_grader


def test_fake_grader_deterministic_and_bounded():
    g = FakeGrader()
    text = "The weather today is sunny and warm with a gentle breeze from the north"
    a = g.grade_writing("Describe the weather", "IELTS band", text)
    b = g.grade_writing("Describe the weather", "IELTS band", text)
    assert a.score == b.score  # tất định
    assert 0.0 <= a.score <= 1.0
    assert 0.0 <= a.confidence <= 1.0
    assert a.feedback


def test_fake_grader_empty_is_zero():
    g = FakeGrader()
    r = g.grade_writing("prompt", "", "")
    assert r.score == 0.0


def test_fake_grader_longer_scores_higher():
    g = FakeGrader()
    short = g.grade_writing("p", "", "good essay here")
    long = g.grade_writing(
        "p",
        "",
        "This is a much longer and more varied essay discussing several distinct ideas "
        "with rich vocabulary spanning many different unique words and concepts overall",
    )
    assert long.score > short.score


def test_get_grader_defaults_to_fake_without_key(monkeypatch):
    from app.config import settings

    # không cấu hình endpoint/key nào -> Fake
    monkeypatch.setattr(settings, "ai_base_url", "")
    monkeypatch.setattr(settings, "ai_api_key", "")
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    assert isinstance(get_grader(), FakeGrader)


def test_validate_writing_ok_and_bad():
    validate_content("writing", {"prompt": "Write about your city", "rubric": "IELTS"}, {})
    validate_content("writing", {"prompt": "No rubric ok"}, {})
    with pytest.raises(InvalidContent):
        validate_content("writing", {"prompt": "  "}, {})
    with pytest.raises(InvalidContent):
        validate_content("writing", {"prompt": "ok", "rubric": 123}, {})


def test_openai_compat_grader_parses_json(monkeypatch):
    """OpenAICompatGrader gọi endpoint OpenAI-compatible và parse JSON (kể cả có ```fence)."""
    import httpx

    from app.config import settings
    from app.modules.grading.ai import OpenAICompatGrader, get_grader

    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["model"] = json["model"]
        body = {
            "choices": [
                {
                    "message": {
                        "content": '```json\n{"score": 0.72, "feedback": "Ổn, cần mở bài rõ.", '
                        '"confidence": 0.8}\n```'
                    }
                }
            ]
        }
        return httpx.Response(200, json=body, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setattr(settings, "ai_base_url", "https://route-ai.example/v1")
    monkeypatch.setattr(settings, "ai_api_key", "sk-test")
    monkeypatch.setattr(settings, "ai_grader_model", "kiro/claude-sonnet-4.5")

    assert isinstance(get_grader(), OpenAICompatGrader)  # ưu tiên openai-compat
    g = OpenAICompatGrader().grade_writing("Đề", "Rubric", "Bài làm")
    assert g.score == 0.72
    assert "mở bài" in g.feedback
    assert captured["url"].endswith("/chat/completions")
    assert captured["model"] == "kiro/claude-sonnet-4.5"


@pytest.mark.asyncio
async def test_ai_generate_creates_drafts(monkeypatch, session_factory):
    """AI sinh câu → tạo draft vào kho đúng thư mục; câu lỗi schema bị bỏ qua."""
    import json as _json
    import uuid as _uuid

    import httpx
    from sqlalchemy import text as _text

    from app.config import settings
    from app.db import set_tenant
    from app.modules.content import ai_service
    from app.modules.content import service as content_svc

    tid = str(_uuid.uuid4())
    payload = [
        {
            "type": "mcq_single",
            "prompt": "Chọn từ đúng?",
            "options": ["cat", "cut", "cot"],
            "correct_index": 0,
            "explanation": "cat = con mèo",
        },
        {"type": "mcq_single", "prompt": "Thiếu options nên bị bỏ"},
    ]

    def fake_post(url, headers=None, json=None, timeout=None):
        body = {"choices": [{"message": {"content": _json.dumps(payload)}}]}
        return httpx.Response(200, json=body, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setattr(settings, "ai_base_url", "https://route-ai.example/v1")
    monkeypatch.setattr(settings, "ai_api_key", "sk-test")

    async with session_factory() as s, s.begin():
        await set_tenant(s, tid)
        await s.execute(
            _text("INSERT INTO tenants (id, slug, name) VALUES (:id, :sl, 'AG')"),
            {"id": tid, "sl": f"ag-{tid[:8]}"},
        )
        fid = await content_svc.create_folder(s, tid, "AI sinh", None)
        ids = await ai_service.generate_questions(
            s,
            tid,
            str(_uuid.uuid4()),
            topic="Từ vựng động vật",
            skill="reading",
            qtype="mcq_single",
            count=2,
            folder_id=fid,
        )
        assert len(ids) == 1  # câu lỗi schema bị bỏ
        rows = await content_svc.list_questions(s, {"folder_id": fid})
        assert rows[0]["id"] == ids[0]
        assert rows[0]["status"] == "draft"
