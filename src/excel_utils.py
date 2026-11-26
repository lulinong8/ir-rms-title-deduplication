"""Excel output helpers: remove control characters that openpyxl rejects."""

from __future__ import annotations

import re

import pandas as pd

_ILLEGAL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def sanitize_value(value):
    if isinstance(value, str) and _ILLEGAL_CHARACTERS.search(value):
        return _ILLEGAL_CHARACTERS.sub("", value)
    return value


def sanitize_frame(frame: pd.DataFrame) -> pd.DataFrame:
    cleaned = frame.copy()
    for column in cleaned.columns:
        if cleaned[column].dtype == object:
            cleaned[column] = cleaned[column].map(sanitize_value)
    return cleaned
