"""Comparison pipeline: recall -> similarity scoring -> classification -> result sets."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import pandas as pd

from .config import RESULT_COLUMNS, RunConfig, Thresholds
from .dataset import SourceData
from .retrieval import BestMatch, TitleIndex
from .similarity import author_related, get_result

CATEGORY_DUPLICATE = "Definite Duplicate"
CATEGORY_SUSPECT = "Suspected Duplicate"
CATEGORY_ATTENTION = "Key Attention"
CATEGORY_UNMATCHED = "Unmatched"


@dataclass
class MatchRow:
    research_index: int
    library_index: int
    title_similarity: float
    journal_similarity: float
    author_related: bool
    category: str


@dataclass
class PipelineResult:
    intersection: pd.DataFrame
    duplicate: pd.DataFrame
    suspect_and_key_attention: pd.DataFrame
    elapsed_seconds: float = 0.0
    stats: dict[str, int] = field(default_factory=dict)


def classify(title_similarity: float, journal_similarity: float, author_ok: bool, thresholds: Thresholds) -> str:
    """Classify a candidate pair into one of Definite/Suspect/Attention.

    Every record that enters Overlapping Publications receives a category, so that
    Overlap count always equals Definite + Suspect + Key-Attention.
    """
    if title_similarity >= thresholds.duplicate_title and journal_similarity >= thresholds.duplicate_journal:
        return CATEGORY_DUPLICATE
    if (
        title_similarity >= thresholds.key_title
        and journal_similarity > thresholds.key_journal
        and author_ok
    ):
        return CATEGORY_DUPLICATE
    if title_similarity >= thresholds.duplicate_title:
        return CATEGORY_ATTENTION
    if title_similarity >= thresholds.suspect_title_mid:
        return CATEGORY_SUSPECT
    if title_similarity >= thresholds.suspect_title and journal_similarity > thresholds.suspect_journal:
        return CATEGORY_SUSPECT
    return CATEGORY_ATTENTION


def _choose_candidate(match: BestMatch, research_row: pd.Series, library: pd.DataFrame) -> tuple[int, float, bool]:
    docs = match.library_indices
    if len(docs) == 1 or match.title_similarity <= 0:
        index = docs[0]
        journal_similarity = get_result(research_row["Source"], library.at[index, "Source"])
        author_ok = author_related(research_row["Author"], library.at[index, "Author"])
        return index, journal_similarity, author_ok

    best: tuple[float, bool, int] | None = None
    best_index = docs[0]
    best_journal = 0.0
    best_author = False
    for index in docs:
        journal_similarity = get_result(research_row["Source"], library.at[index, "Source"])
        author_ok = author_related(research_row["Author"], library.at[index, "Author"])
        key = (journal_similarity, author_ok, -index)
        if best is None or key > best:
            best = key
            best_index = index
            best_journal = journal_similarity
            best_author = author_ok
    return best_index, best_journal, best_author


def _result_frame(rows: list[MatchRow], source: SourceData) -> pd.DataFrame:
    library = source.library
    research = source.research
    records = []
    for row in rows:
        research_row = research.iloc[row.research_index]
        library_row = library.iloc[row.library_index]
        records.append(
            {
                "Document Type": research_row["Document Type"] or library_row["Document Type"],
                "Title From RSM": research_row["Title"],
                "Title From IR": library_row["Title"],
                "Title's Similarity Score": row.title_similarity,
                "Source From SRM": research_row["Source"],
                "Source From IR": library_row["Source"],
                "Source's Similarity Score": row.journal_similarity,
                "Author From SRM": research_row["Author"],
                "Author From IR": library_row["Author"],
                "Publish Date From SRM": research_row["Publish Date"],
                "Publish Date From IR": library_row["Publish Date"],
            }
        )
    return pd.DataFrame(records, columns=RESULT_COLUMNS)


def run_pipeline(source: SourceData, config: RunConfig | None = None, progress: bool = True) -> PipelineResult:
    config = config or RunConfig()
    started = time.time()

    library = source.library
    research = source.research
    index = TitleIndex(library["Title"].tolist(), config.retrieval)

    matched: list[MatchRow] = []
    total = len(research)
    for position, (_, research_row) in enumerate(research.iterrows()):
        match = index.search(research_row["Title"])
        if match is None or match.title_similarity < config.retrieval.min_intersection_similarity:
            continue

        library_index, journal_similarity, author_ok = _choose_candidate(match, research_row, library)
        category = classify(match.title_similarity, journal_similarity, author_ok, config.thresholds)
        matched.append(
            MatchRow(
                research_index=position,
                library_index=library_index,
                title_similarity=match.title_similarity,
                journal_similarity=journal_similarity,
                author_related=author_ok,
                category=category,
            )
        )

        if progress and (position + 1) % 5000 == 0:
            print(f"  Processed {position + 1}/{total} RMS records")

    duplicate = [row for row in matched if row.category == CATEGORY_DUPLICATE]
    suspect_and_key_attention = [
        row for row in matched if row.category in (CATEGORY_SUSPECT, CATEGORY_ATTENTION)
    ]

    return PipelineResult(
        intersection=_result_frame(matched, source),
        duplicate=_result_frame(duplicate, source),
        suspect_and_key_attention=_result_frame(suspect_and_key_attention, source),
        elapsed_seconds=time.time() - started,
        stats={
            "Records from IR": len(library),
            "Records from RMS": len(research),
            "Overlapping Publications": len(matched),
            "Definite Duplicates": len(duplicate),
            "Suspected-Du & Key-Attention": len(suspect_and_key_attention),
        },
    )
