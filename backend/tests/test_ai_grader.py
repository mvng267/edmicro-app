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


def test_get_grader_defaults_to_fake_without_key():
    # môi trường test không set anthropic_api_key -> Fake
    assert isinstance(get_grader(), FakeGrader)


def test_validate_writing_ok_and_bad():
    validate_content("writing", {"prompt": "Write about your city", "rubric": "IELTS"}, {})
    validate_content("writing", {"prompt": "No rubric ok"}, {})
    with pytest.raises(InvalidContent):
        validate_content("writing", {"prompt": "  "}, {})
    with pytest.raises(InvalidContent):
        validate_content("writing", {"prompt": "ok", "rubric": 123}, {})
