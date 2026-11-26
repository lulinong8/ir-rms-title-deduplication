"""Text similarity scoring.

Chinese text is compared character by character and English text word by word
using Jaccard similarity, with a length-ratio bonus when one text contains the
other. The implementation explicitly handles the following details so that the
same input pair always produces the same score:

* Whitespace trimming only strips ASCII whitespace (<= 0x20), preserving the
  ideographic space U+3000.
* An empty string yields one empty placeholder element when split into
  characters, keeping set operations stable.
* Unicode punctuation categories and the explicit symbols + ~ $ ` ^ = | < > are
  removed.
* Scores are rounded to two decimals using banker's rounding (HALF_EVEN).
* Mixed Chinese-English text counts Chinese characters and the English
  remainder separately.

Scores range from 0.00 to 100.00.
"""

from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, ROUND_HALF_EVEN

__all__ = ["get_result", "get_clean_str", "is_chinese", "author_related"]

_CJK_PATTERN = re.compile(r"[\u4e00-\u9fa5]")
_ENGLISH_WORD_PATTERN = re.compile(r"[A-Za-z]+")

# Explicit symbols to remove (Unicode punctuation is detected by unicodedata)
_EXTRA_SYMBOLS = frozenset("+~$`^=|<>" + "\uFF5E\uFF40\uFF04\uFF3E\uFF0B\uFF1D\uFF5C\uFF1C\uFF1E\uFFE5\u00D7")


def _is_punct_or_extra(ch: str) -> bool:
    return ch in _EXTRA_SYMBOLS or unicodedata.category(ch).startswith("P")


def _trim_ascii_space(text: str) -> str:
    """Strip leading and trailing ASCII whitespace (<= 0x20); keep U+3000."""
    start, end = 0, len(text)
    while start < end and ord(text[start]) <= 0x20:
        start += 1
    while end > start and ord(text[end - 1]) <= 0x20:
        end -= 1
    return text[start:end]


def _format2(value: float) -> float:
    """Round to two decimals using banker's rounding (HALF_EVEN)."""
    return float(Decimal(repr(float(value))).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN))


def is_chinese(text: str) -> bool:
    """Return True when the text contains at least one Chinese character."""
    return _CJK_PATTERN.search(text) is not None


def get_clean_str(text: str) -> str:
    """Remove punctuation and configured symbols, keeping letters, digits and whitespace."""
    return "".join(ch for ch in text if not _is_punct_or_extra(ch))


def _split_chars(text: str) -> list[str]:
    """Split text into characters; an empty string yields one empty placeholder."""
    return list(text) if text else [""]


def _get_chinese_words(text: str) -> str:
    text = text.replace(" ", "")
    return re.sub(r"[^\u4e00-\u9fa5]", "", text)


def _get_english_words(text: str) -> str:
    text = text.replace(" ", "")
    return re.sub(r"[^a-zA-Z]", "", text)


def _intersect(left: list[str], right: list[str]) -> list[str]:
    """Return the intersection of two lists, de-duplicated in first-seen order."""
    left_unique: list[str] = []
    for item in left:
        if item not in left_unique:
            left_unique.append(item)
    right_unique: list[str] = []
    for item in right:
        if item not in right_unique:
            right_unique.append(item)
    return [item for item in right_unique if item in left_unique]


def _union(left: list[str], right: list[str]) -> list[str]:
    return list(set(left) | set(right))


def _delete_null(items: list[str]) -> list[str]:
    return [item for item in items if item not in (None, "")]


def _get_temp(text1: str, text2: str) -> float:
    if len(text1) <= len(text2):
        return _format2(len(text1) * 100.0 / len(text2))
    return _format2(len(text2) * 100.0 / len(text1))


def _compare_result(text1: str, text2: str) -> float:
    lower1, lower2 = text1.lower(), text2.lower()
    split1 = _split_chars(lower1) if is_chinese(text1) else lower1.split(" ")
    split2 = _split_chars(lower2) if is_chinese(text2) else lower2.split(" ")

    intersect_words = _delete_null(_intersect(split1, split2))
    union_words = _delete_null(_union(split1, split2))
    if not union_words:
        return 0.0
    result = _format2(100.00 * len(intersect_words) / len(union_words))

    if result != 100.00:
        if not is_chinese(text1) and not is_chinese(text2):
            if lower2 in lower1 or lower1 in lower2:
                return _format2(min(result + _get_temp(text1, text2), 99.97))
        else:
            if text2 in text1 or text1 in text2:
                return _format2(min(result + _get_temp(text1, text2), 99.97))
    return result


def _chinese_result(text1: str, text2: str) -> float:
    text1 = text1.replace(" ", "")
    text2 = text2.replace(" ", "")
    clean1, clean2 = get_clean_str(text1), get_clean_str(text2)
    if clean1 == clean2:
        return 99.98
    return _compare_result(clean1, clean2)


def _english_result(text1: str, text2: str) -> float:
    if text1.lower() == text2.lower():
        return 99.99
    clean1, clean2 = get_clean_str(text1), get_clean_str(text2)
    if clean1 == clean2 or clean1.lower() == clean2.lower():
        return 99.98
    return _compare_result(clean1, clean2)


def _chinese_and_english_result(text1: str, text2: str) -> float:
    chinese1, chinese2 = _get_chinese_words(text1), _get_chinese_words(text2)
    english1, english2 = _get_english_words(text1), _get_english_words(text2)

    chinese_intersect = len(_intersect(_split_chars(chinese1), _split_chars(chinese2)))
    english_intersect = len(_intersect(english1.split(" "), english2.split(" ")))
    chinese_union = len(_union(_split_chars(chinese1), _split_chars(chinese2)))
    english_union = len(_union(english1.split(" "), english2.split(" ")))

    total_union = chinese_union + english_union
    if total_union == 0:
        return 0.0
    result = _format2(100.00 * (chinese_intersect + english_intersect) / total_union)

    if result != 100.00 and (text2 in text1 or text1 in text2):
        return _format2(min(result + _get_temp(text1, text2), 99.97))
    return result


def get_result(text1: str | None, text2: str | None) -> float:
    """Compute the similarity of two texts in the range 0.00 to 100.00."""
    if text1 is None or text2 is None:
        return 0.0
    text1, text2 = _trim_ascii_space(str(text1)), _trim_ascii_space(str(text2))
    if text1 == "" or text2 == "":
        return 0.0
    if text1 == text2:
        return 100.00

    chinese1, chinese2 = is_chinese(text1), is_chinese(text2)
    if chinese1 and chinese2:
        return _chinese_result(text1, text2)
    if not chinese1 and not chinese2:
        return _english_result(text1, text2)
    return _chinese_and_english_result(text1, text2)


def _author_tokens(value: str) -> list[str]:
    value = str(value).replace("\uFF1B", ";")
    return [token.strip() for token in value.split(";") if token.strip()]


def author_related(author1: str, author2: str) -> bool:
    """Return True when two semicolon-separated author lists share a contained name."""
    tokens1, tokens2 = _author_tokens(author1), _author_tokens(author2)
    return any(a == b or a in b or b in a for a in tokens1 for b in tokens2)
