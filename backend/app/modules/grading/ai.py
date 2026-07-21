"""Chấm AI câu writing (sơ bộ, luôn chờ GV chốt). Xem SRS GRADE §5.2, FR-GRADE-04.

Adapter theo provider: FakeGrader (dev/test/degrade, tất định) và ClaudeGrader (LLM thật,
bật khi có anthropic_api_key). Trả điểm 0..1 + nhận xét + độ tự tin. Không raise ra ngoài
nếu provider lỗi ở tầng gọi — tầng service sẽ degrade sang chấm tay.
"""

from dataclasses import dataclass
from typing import Protocol

from app.config import settings


@dataclass
class AIGrade:
    score: float  # 0..1
    feedback: str
    confidence: float  # 0..1


class AIGrader(Protocol):
    def grade_writing(self, prompt: str, rubric: str, answer_text: str) -> AIGrade: ...


class FakeGrader:
    """Chấm tất định theo độ dài + đa dạng từ — đủ để demo/E2E, không gọi mạng.

    Điểm tăng theo số từ (bão hòa ~60 từ) và tỉ lệ từ khác nhau; luôn cùng kết quả
    cho cùng input (E2E ổn định). Confidence trung bình để GV vẫn cần chốt.
    """

    def grade_writing(self, prompt: str, rubric: str, answer_text: str) -> AIGrade:
        words = [w for w in answer_text.split() if w.strip()]
        n = len(words)
        if n == 0:
            return AIGrade(
                score=0.0, feedback="Bài trống — chưa có nội dung để chấm.", confidence=0.9
            )
        length_score = min(n, 60) / 60.0
        variety = len({w.lower() for w in words}) / n
        score = round(0.4 * variety + 0.6 * length_score, 3)
        score = max(0.0, min(1.0, score))
        feedback = (
            f"Bài dài {n} từ, độ đa dạng từ vựng {variety:.0%}. "
            "Điểm AI sơ bộ theo độ dài và đa dạng — giáo viên vui lòng chốt lại theo rubric."
        )
        return AIGrade(score=score, feedback=feedback, confidence=0.5)


class ClaudeGrader:
    """Chấm bằng LLM Claude theo rubric (analytic, temperature 0, yêu cầu JSON).

    Chỉ khởi tạo khi có anthropic_api_key. Lỗi mạng/parse để tầng gọi bắt và degrade.
    """

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    def grade_writing(self, prompt: str, rubric: str, answer_text: str) -> AIGrade:
        import json

        from anthropic import Anthropic

        client = Anthropic(api_key=self._api_key)
        sys = (
            "Bạn là giám khảo chấm writing theo rubric chuẩn thi. Chấm analytic, khắt khe, "
            "không thiên vị bài dài. Trả về DUY NHẤT JSON: "
            '{"score": <0..1>, "feedback": "<nhận xét + gợi ý sửa, tiếng Việt>", '
            '"confidence": <0..1>}.'
        )
        rubric_txt = rubric or "(không có — chấm theo chuẩn chung)"
        user = (
            f"ĐỀ BÀI:\n{prompt}\n\nRUBRIC:\n{rubric_txt}\n\nBÀI LÀM:\n{answer_text}"
        )
        msg = client.messages.create(
            model=self._model,
            max_tokens=1024,
            temperature=0,
            system=sys,
            messages=[{"role": "user", "content": user}],
        )
        raw = "".join(b.text for b in msg.content if b.type == "text")
        data = json.loads(raw[raw.index("{") : raw.rindex("}") + 1])
        return AIGrade(
            score=max(0.0, min(1.0, float(data["score"]))),
            feedback=str(data.get("feedback", "")),
            confidence=max(0.0, min(1.0, float(data.get("confidence", 0.5)))),
        )


def get_grader() -> AIGrader:
    """Provider thật nếu có key, ngược lại Fake (dev/test/degrade)."""
    if settings.anthropic_api_key:
        return ClaudeGrader(settings.anthropic_api_key, settings.ai_grader_model)
    return FakeGrader()
