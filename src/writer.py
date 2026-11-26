"""Write pipeline results to an Excel workbook with the expected sheet layout."""

from __future__ import annotations

import pandas as pd

from .config import (
    IR_COLUMNS,
    RMS_COLUMNS,
    SHEET_DEFINITE,
    SHEET_OVERLAP,
    SHEET_RECORDS_IR,
    SHEET_RECORDS_RMS,
    SHEET_SUSPECT_KEY,
)
from .dataset import SourceData
from .excel_utils import sanitize_frame
from .pipeline import PipelineResult

_SIMILARITY_COLUMNS = {"Title's Similarity Score", "Source's Similarity Score"}
_WIDE_COLUMNS = {
    "Title",
    "Title From RSM",
    "Title From IR",
    "Author",
    "Author From SRM",
    "Author From IR",
}


def _write_sheet(writer: pd.ExcelWriter, sheet_name: str, frame: pd.DataFrame) -> None:
    frame = sanitize_frame(frame)
    frame.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    worksheet = writer.sheets[sheet_name[:31]]

    for column_index, column_name in enumerate(frame.columns, start=1):
        letter = worksheet.cell(row=1, column=column_index).column_letter
        if column_name in _SIMILARITY_COLUMNS:
            for row_index in range(2, len(frame) + 2):
                worksheet[f"{letter}{row_index}"].number_format = "0.00"
            width = 16
        elif column_name in _WIDE_COLUMNS:
            width = 40
        else:
            width = 18
        worksheet.column_dimensions[letter].width = width


def write_workbook(path: str, source: SourceData, result: PipelineResult) -> None:
    library = source.library[IR_COLUMNS]
    research = source.research[RMS_COLUMNS]

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        _write_sheet(writer, SHEET_RECORDS_IR, library)
        _write_sheet(writer, SHEET_RECORDS_RMS, research)
        _write_sheet(writer, SHEET_OVERLAP, result.intersection)
        _write_sheet(writer, SHEET_DEFINITE, result.duplicate)
        _write_sheet(writer, SHEET_SUSPECT_KEY, result.suspect_and_key_attention)
