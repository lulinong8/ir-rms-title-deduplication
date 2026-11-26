"""Unit tests for the similarity primitives."""

import pytest

from src.similarity import author_related, get_result, is_chinese


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ("abc", "abc", 100.00),
        ("abc", "ABC", 99.99),
        ("a-b", "ab", 99.98),
        ("This is a test.", "This is a test!", 99.98),
        ("这是测试", "这是测验", 60.00),
        ("this is a test", "this is a test extra", 99.97),
        ("", "abc", 0.00),
        (None, "abc", 0.00),
    ],
)
def test_get_result(left, right, expected):
    assert get_result(left, right) == pytest.approx(expected)


def test_is_chinese():
    assert is_chinese("这是中文")
    assert not is_chinese("This is English")
    assert is_chinese("Mixed 中文 title")


def test_author_related():
    assert author_related("Zhang San; Li Si", "Zhang San")
    assert author_related("Wang Wu", "Wang Wu; Zhao Liu")
    assert not author_related("Zhang San", "San Zhang")
    assert not author_related("", "")
