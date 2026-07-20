import uuid

import pytest
from sqlalchemy import text

from app.db import set_tenant
from app.modules.content import service as svc

TID = str(uuid.uuid4())
CREATOR = str(uuid.uuid4())


def _mcq() -> dict:
    return {
        "type": "mcq_single",
        "language": "en",
        "skill": "reading",
        "content": {"prompt": "2+2=?", "options": ["3", "4", "5"]},
        "answer_key": {"correct_index": 1},
    }


@pytest.mark.asyncio
async def test_validate_mcq_and_fill_blank():
    svc.validate_content("mcq_single", {"prompt": "p", "options": ["a", "b"]}, {"correct_index": 0})
    with pytest.raises(svc.InvalidContent):
        svc.validate_content(
            "mcq_single", {"prompt": "p", "options": ["a", "b"]}, {"correct_index": 5}
        )
    svc.validate_content(
        "fill_blank", {"prompt": "I ___ a cat and ___ dog."}, {"blanks": [["have"], ["a"]]}
    )
    with pytest.raises(svc.InvalidContent):
        svc.validate_content("fill_blank", {"prompt": "no blank"}, {"blanks": [["x"]]})


@pytest.mark.asyncio
async def test_create_update_versioning(session_factory):
    async with session_factory() as s:
        async with s.begin():
            await set_tenant(s, TID)
            qid = await svc.create_question(s, TID, CREATOR, _mcq())
        # sửa -> version 2, version 1 vẫn còn
        async with s.begin():
            await set_tenant(s, TID)
            v2 = await svc.update_question(
                s,
                TID,
                qid,
                CREATOR,
                {
                    "content": {"prompt": "2+2=?", "options": ["3", "4", "5", "6"]},
                    "answer_key": {"correct_index": 1},
                },
            )
            assert v2 == 2
        async with s.begin():
            await set_tenant(s, TID)
            n = (
                await s.execute(
                    text("SELECT count(*) FROM question_versions WHERE question_id = :q"),
                    {"q": qid},
                )
            ).scalar_one()
            assert n == 2
            # current trỏ version 2
            detail = await svc.get_question(s, qid)
            assert detail["version_no"] == 2
            assert len(detail["content"]["options"]) == 4


@pytest.mark.asyncio
async def test_publish_and_list_filter(session_factory):
    async with session_factory() as s:
        async with s.begin():
            await set_tenant(s, TID)
            qid = await svc.create_question(s, TID, CREATOR, {**_mcq(), "skill": "listening"})
            await svc.publish_question(s, qid)
        async with s.begin():
            await set_tenant(s, TID)
            listening = await svc.list_questions(s, {"skill": "listening", "status": "published"})
            assert any(q["id"] == qid for q in listening)
            reading_only = await svc.list_questions(s, {"skill": "reading", "status": "published"})
            assert all(q["id"] != qid for q in reading_only)
