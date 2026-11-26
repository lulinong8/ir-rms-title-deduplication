"""Candidate recall with an inverted index.

Builds an inverted index from Chinese character bigrams and English words,
recalls candidate IR records for each RMS title, then scores them with
:mod:`src.similarity`.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass

from .config import RetrievalConfig
from .similarity import get_clean_str, get_result

_WORD_PATTERN = re.compile(r"[A-Za-z]+")
_CJK_MIN, _CJK_MAX = "\u4e00", "\u9fa5"


@dataclass(frozen=True)
class TitleFeatures:
    chars: frozenset[str]
    bigrams: frozenset[str]
    words: frozenset[str]


def extract_features(text: str) -> TitleFeatures:
    clean = get_clean_str(str(text))
    nospace = clean.replace(" ", "").replace("\u3000", "")
    chars = frozenset(ch for ch in nospace if _CJK_MIN <= ch <= _CJK_MAX)
    ordered = [ch for ch in nospace if _CJK_MIN <= ch <= _CJK_MAX]
    bigrams = frozenset(a + b for a, b in zip(ordered, ordered[1:]))
    words = frozenset(word.lower() for word in _WORD_PATTERN.findall(clean))
    return TitleFeatures(chars=chars, bigrams=bigrams, words=words)


@dataclass(frozen=True)
class BestMatch:
    title_similarity: float
    library_indices: tuple[int, ...]


class TitleIndex:
    def __init__(self, titles: list[str], config: RetrievalConfig | None = None):
        self.titles = titles
        self.config = config or RetrievalConfig()
        self._bigram_index: dict[str, list[int]] = defaultdict(list)
        self._word_index: dict[str, list[int]] = defaultdict(list)
        self._char_index: dict[str, list[int]] = defaultdict(list)
        for index, title in enumerate(titles):
            features = extract_features(title)
            for bigram in features.bigrams:
                self._bigram_index[bigram].append(index)
            for word in features.words:
                self._word_index[word].append(index)
            for char in features.chars:
                self._char_index[char].append(index)

    def _postings(self, kind: str, token: str) -> list[int]:
        table = {"b": self._bigram_index, "w": self._word_index, "c": self._char_index}[kind]
        return table.get(token, [])

    def search(self, title: str) -> BestMatch | None:
        features = extract_features(title)
        short_title = len(features.bigrams) < 2
        if features.bigrams:
            atoms = [("b", token) for token in features.bigrams]
        else:
            atoms = [("c", token) for token in features.chars]
        if short_title:
            atoms.extend(("c", token) for token in features.chars)
        atoms.extend(("w", token) for token in features.words)

        max_frequency = self.config.max_feature_frequency
        atoms = [(kind, token) for kind, token in atoms if 0 < len(self._postings(kind, token)) <= max_frequency]
        if not atoms:
            return None

        atoms.sort(key=lambda item: (len(self._postings(*item)), item[0], item[1]))
        anchors = atoms[: self.config.anchors]

        bigram_hits: Counter[int] = Counter()
        word_hits: Counter[int] = Counter()
        char_hits: Counter[int] = Counter()
        for kind, token in anchors:
            target = bigram_hits if kind == "b" else word_hits if kind == "w" else char_hits
            for doc in self._postings(kind, token):
                target[doc] += 1

        required_words = min(2, len(features.words))
        candidates: list[int] = []
        for doc in set(bigram_hits) | set(word_hits) | set(char_hits):
            accepted = bigram_hits[doc] >= 2 or (required_words and word_hits[doc] >= required_words)
            if short_title and char_hits[doc] >= 1:
                accepted = True
            if accepted:
                candidates.append(doc)
        if not candidates:
            return None

        candidates.sort(key=lambda doc: (-(bigram_hits[doc] + word_hits[doc] + char_hits[doc]), doc))
        candidates = candidates[: self.config.max_candidates]

        best_similarity = -1.0
        best_docs: list[int] = []
        for doc in candidates:
            similarity = get_result(title, self.titles[doc])
            if similarity > best_similarity + 1e-12:
                best_similarity = similarity
                best_docs = [doc]
            elif abs(similarity - best_similarity) <= 1e-12 and len(best_docs) < 20:
                best_docs.append(doc)
        if not best_docs:
            return None
        return BestMatch(title_similarity=best_similarity, library_indices=tuple(best_docs))
