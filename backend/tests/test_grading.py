from app.modules.grading import service as g


def test_grade_answer_mcq():
    assert g.grade_answer("mcq_single", {"selected": 1}, {"correct_index": 1}) is True
    assert g.grade_answer("mcq_single", {"selected": 0}, {"correct_index": 1}) is False
    assert g.grade_answer("mcq_single", None, {"correct_index": 1}) is False


def test_grade_answer_fill_blank_case_insensitive():
    assert (
        g.grade_answer(
            "fill_blank", {"blanks": ["Hanoi", "a"]}, {"blanks": [["hanoi"], ["a", "an"]]}
        )
        is True
    )
    assert (
        g.grade_answer("fill_blank", {"blanks": ["wrong", "a"]}, {"blanks": [["hanoi"], ["a"]]})
        is False
    )


def test_grade_answer_unsupported():
    assert g.grade_answer("essay", {"text": "x"}, {}) is None
