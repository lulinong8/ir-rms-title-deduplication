# A dictionary-free language-adaptive text similarity algorithm for academic literature deduplication in institutional repositories

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24576834.svg)](https://doi.org/10.5281/zenodo.24576834)

Companion source code and data for:

> Lu L, Yang B, Wang X. *A dictionary-free language-adaptive text similarity algorithm for academic literature deduplication in institutional repositories.* PLOS ONE (under review; PONE-D-26-35837).

**Release:** v1.0.1 (2026-11-27)  
**Version DOI:** [10.5281/zenodo.24576834](https://doi.org/10.5281/zenodo.24576834)  
**Concept DOI:** [10.5281/zenodo.24557249](https://doi.org/10.5281/zenodo.24557249)

The implementation is Python 3. It uses language-adaptive segmentation and surface-unit Jaccard similarity; it does not require a dictionary, a word-segmentation model, embeddings, or an external service.

## Repository structure

| Path | Purpose |
|---|---|
| `src/` | Python package: CLI, configuration, workbook reader, candidate recall, similarity scoring, pipeline, result writer and Excel-safe text cleanup |
| `doc/User_Guide_EN.md` | Input/output formats, command-line options, classification rules and tuning notes |
| `data/s1 dataset.xlsx` | Input workbook: 24,612 IR records and 18,157 RMS records |
| `output/deduplication_results.xlsx` | Five-sheet result workbook produced from the included input |
| `tests/` | Unit tests for scoring primitives and classification rules |
| `requirements.txt` | Pinned runtime and test dependencies |
| `CITATION.cff` | Citation metadata for this release |
| `LICENSE` | MIT License for the source code |
| `DATA_LICENSE.md` | CC0 1.0 dedication for the data files |

## Installation

Requirements: Python 3.11 or later.

```bash
python -m pip install -r requirements.txt
```

Dependencies are pinned to the versions used for the reported run: pandas 3.1.1, openpyxl 3.1.5, xlrd 2.0.2 and pytest 9.2.0. The run was tested with Python 3.13.18 on Windows 11. `xlrd` is needed only for legacy `.xls` input; `.xlsx` input is read through `openpyxl`.

## Usage

Run from the repository root:

```bash
python -m src.cli -i "data/s1 dataset.xlsx" -o output/deduplication_results.xlsx
```

Run the unit tests:

```bash
python -m pytest -q
```

Expected: `22 passed`. The tests cover the scoring primitives and classification rules; the full 24,612 × 18,157 run is reproduced by the command above.

## Output

The result workbook contains five worksheets:

| Worksheet | Rows | Content |
|---|---:|---|
| `Records from IR` | 24,612 | Original IR records |
| `Records from RMS` | 18,157 | Original RMS records |
| `Overlapping Publications` | 18,144 | Each RMS record and its most similar IR record |
| `Definite Duplicates` | 17,599 | Pairs satisfying the definite-duplicate rules |
| `Suspected-Du & Key-Attention` | 545 | Combined review worksheet |

The 545-row worksheet contains 69 key-attention records, 58 suspected duplicates and 418 lower-similarity fallback records. It does not contain a separate category column. The full run takes about 117 s wall-clock on the test machine; runtime depends on CPU and disk speed.

## Input data

`data/s1 dataset.xlsx` contains two worksheets: `Records from IR` with 24,612 rows and five metadata columns, and `Records from RMS` with 18,157 rows and six metadata columns. The data are bibliographic metadata only; no full text or PDFs are included.

## Citation

Use the version DOI for this release, or the concept DOI for all versions:

```text
Lu L, Yang B, Wang X. A dictionary-free language-adaptive text similarity
algorithm for academic literature deduplication in institutional repositories.
PLOS ONE (under review; PONE-D-26-35837). Version 1.0.1. Zenodo.
https://doi.org/10.5281/zenodo.24576834
```

`CITATION.cff` contains the same metadata for GitHub's citation button.

## License

Source code is released under the MIT License (see `LICENSE`). The input and result workbooks are released under CC0 1.0 (see `DATA_LICENSE.md`).

## Contact

Corresponding author: Linong Lu, `luln@llas.ac.cn`.
