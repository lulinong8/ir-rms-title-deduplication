"""Read the input workbook (.xls/.xlsx) and locate the IR and RMS sheets."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import IR_COLUMNS, RMS_COLUMNS, SHEET_RECORDS_IR, SHEET_RECORDS_RMS


@dataclass
class SourceData:
    library: pd.DataFrame
    research: pd.DataFrame


def _header_row(raw: pd.DataFrame, required: list[str]) -> int | None:
    for row_index in range(min(len(raw), 20)):
        values = [str(value).strip() for value in raw.iloc[row_index].tolist()]
        if all(token in values for token in required):
            return row_index
    return None


def _read_sheet(path: str, sheet_name: str, columns: list[str], required: list[str]) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name=sheet_name, header=None, dtype=str, keep_default_na=False)
    header_index = _header_row(raw, required)
    if header_index is None:
        raise ValueError(f"Sheet {sheet_name!r} does not contain the required headers {required}")

    header = [str(value).strip() for value in raw.iloc[header_index].tolist()]
    data = raw.iloc[header_index + 1 :].copy()
    data.columns = header
    data = data.reset_index(drop=True)

    for column in columns:
        if column not in data.columns:
            data[column] = ""
    data = data[columns].fillna("")
    non_empty = (data != "").any(axis=1)
    return data[non_empty].reset_index(drop=True)


def _locate_sheet(names: list[str], expected: str) -> str:
    lowered = {name.lower(): name for name in names}
    if expected.lower() in lowered:
        return lowered[expected.lower()]
    for name in names:
        if name.lower().startswith(expected.lower()):
            return name
    raise ValueError(f"Sheet {expected!r} was not found; available sheets: {names}")


def load_source(path: str) -> SourceData:
    xls = pd.ExcelFile(path)
    names = list(xls.sheet_names)

    library_sheet = _locate_sheet(names, SHEET_RECORDS_IR)
    research_sheet = _locate_sheet(names, SHEET_RECORDS_RMS)

    library = _read_sheet(path, library_sheet, IR_COLUMNS, ["Title"])
    research = _read_sheet(path, research_sheet, RMS_COLUMNS, ["Title", "Source", "Author"])
    return SourceData(library=library, research=research)
