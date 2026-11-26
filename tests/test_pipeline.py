"""Unit tests for the four-tier classification rules."""

import pytest

from src.config import Thresholds
from src.pipeline import (
    CATEGORY_ATTENTION,
    CATEGORY_DUPLICATE,
    CATEGORY_SUSPECT,
    classify,
)

THRESHOLDS = Thresholds()


@pytest.mark.parametrize(
    ("title", "source", "author_ok", "expected"),
    [
        (80.0, 70.0, False, CATEGORY_DUPLICATE),
        (75.0, 95.0, True, CATEGORY_DUPLICATE),
        (75.0, 95.0, False, CATEGORY_SUSPECT),
        (85.0, 60.0, False, CATEGORY_ATTENTION),
        (40.0, 80.0, False, CATEGORY_SUSPECT),
        (20.0, 80.0, False, CATEGORY_ATTENTION),
        (75.0, 60.0, False, CATEGORY_SUSPECT),
        (30.0, 70.0, False, CATEGORY_ATTENTION),
        (30.0, 71.0, False, CATEGORY_SUSPECT),
        (70.0, 91.0, True, CATEGORY_DUPLICATE),
        (70.0, 91.0, False, CATEGORY_SUSPECT),
        (80.0, 69.99, False, CATEGORY_ATTENTION),
    ],
)
def test_classify(title, source, author_ok, expected):
    assert classify(title, source, author_ok, THRESHOLDS) == expected
