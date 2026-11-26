"""Column definitions, sheet names, thresholds and run parameters."""

from __future__ import annotations

from dataclasses import dataclass, field

# IR export columns
IR_COLUMNS = ["Document Type", "Title", "Source", "Author", "Publish Date"]

# RMS export columns, kept in the order used by the input workbook
RMS_COLUMNS = ["Title", "Publish Date", "left", "Document Type", "Source", "Author"]

# Result columns shared by all comparison sheets
RESULT_COLUMNS = [
    "Document Type",
    "Title From RSM",
    "Title From IR",
    "Title's Similarity Score",
    "Source From SRM",
    "Source From IR",
    "Source's Similarity Score",
    "Author From SRM",
    "Author From IR",
    "Publish Date From SRM",
    "Publish Date From IR",
]

SHEET_RECORDS_IR = "Records from IR"
SHEET_RECORDS_RMS = "Records from RMS"
SHEET_OVERLAP = "Overlapping Publications"
SHEET_DEFINITE = "Definite Duplicates"
SHEET_SUSPECT_KEY = "Suspected-Du & Key-Attention"

RESULT_SHEETS = [SHEET_RECORDS_IR, SHEET_RECORDS_RMS, SHEET_OVERLAP, SHEET_DEFINITE, SHEET_SUSPECT_KEY]


@dataclass(frozen=True)
class Thresholds:
    """Similarity thresholds (percentage scale).

    Title >= 80 and Source >= 70 is a definite duplicate;
    Title >= 70, Source > 90 with related authors is also a definite duplicate.
    """

    duplicate_title: float = 80.0
    duplicate_journal: float = 70.0
    key_title: float = 70.0
    key_journal: float = 90.0
    suspect_title: float = 30.0
    suspect_title_mid: float = 50.0
    suspect_journal: float = 70.0


@dataclass(frozen=True)
class RetrievalConfig:
    """Candidate retrieval parameters.

    Candidates are recalled with a Chinese character bigram and English word
    inverted index, then scored by the exact similarity algorithm.
    """

    # Number of lowest-document-frequency features used as recall anchors
    anchors: int = 8
    # Maximum number of candidates scored per RMS record
    max_candidates: int = 200
    # High-frequency features above this document frequency are ignored
    max_feature_frequency: int = 20000
    # Minimum title similarity required to appear in Overlapping Publications
    min_intersection_similarity: float = 0.0


@dataclass(frozen=True)
class RunConfig:
    thresholds: Thresholds = field(default_factory=Thresholds)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
