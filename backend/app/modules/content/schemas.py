from typing import Any

from pydantic import BaseModel


class QuestionCreate(BaseModel):
    type: str  # mcq_single | fill_blank
    language: str = "en"
    skill: str | None = None
    level: str | None = None
    exam_tag: str | None = None
    topic: str | None = None
    difficulty: int | None = None
    content: dict[str, Any]
    answer_key: dict[str, Any]
    explanation: str | None = None


class QuestionUpdate(BaseModel):
    content: dict[str, Any]
    answer_key: dict[str, Any]
    explanation: str | None = None


class QuestionRow(BaseModel):
    id: str
    type: str
    language: str
    skill: str | None
    level: str | None
    exam_tag: str | None
    topic: str | None
    status: str
    prompt: str | None = None


class QuestionDetail(QuestionRow):
    version_no: int
    content: dict[str, Any]
    answer_key: dict[str, Any] | None
    explanation: str | None
