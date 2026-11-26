# IR–RMS title deduplication

Companion source code and data for the manuscript:

> Lu L, Yang B, Wang X. *A lightweight character-level text similarity algorithm for academic literature deduplication in institutional repositories.* PLOS ONE (under review; PONE-D-26-35837).

This repository is the public code and data record for the manuscript. It contains the Python 3 implementation, the S1 input workbook, the five-sheet result workbook, the user guide, and a lightweight unit-test suite.

## Repository contents

| Path | Bytes | Purpose |
|---|---:|---|
| `src/__init__.py` | 81 | Package marker |
| `src/cli.py` | 3,469 | Command-line entry point |
| `src/config.py` | 2,367 | Sheet names, columns, thresholds and recall parameters |
| `src/dataset.py` | 2,256 | Input workbook reader |
| `src/excel_utils.py` | 627 | Removes control characters that `openpyxl` rejects |
| `src/pipeline.py` | 6,207 | Recall, scoring, classification and result sets |
| `src/retrieval.py` | 4,561 | Inverted-index candidate recall |
| `src/similarity.py` | 7,058 | Language identification, cleaning, segmentation and scoring |
| `src/writer.py` | 1,929 | Writes the five-sheet result workbook |
| `doc/User_Guide_EN.md` | 9,218 | Detailed installation, input, output and tuning guide |
| `data/s1 dataset.xlsx` | 3,856,620 | S1 input: IR and RMS record exports |
| `output/deduplication_results.xlsx` | 8,590,991 | Five-sheet result workbook generated from the included input |
| `tests/test_similarity.py` | 1,018 | Unit tests for scoring primitives |
| `tests/test_pipeline.py` | 1,042 | Unit tests for the classification rules |
| `requirements.txt` | 48 | Runtime and test dependencies |
| `pytest.ini` | 42 | Pytest import path and test directory |
| `LICENSE` | — | MIT License for the source code |
| `DATA_LICENSE.md` | — | CC0-1.0 dedication for the data files |
| `CITATION.cff` | — | Citation metadata |
| `.gitignore` | 80 | Excludes caches and temporary files |

The repository deliberately excludes `__pycache__/`, `.pytest_cache/`, temporary verification workbooks, old result workbooks, and any local absolute paths. All paths in the code and documentation are relative to the repository root.

## Requirements

- Python 3.10 or later
- Install dependencies:

```bash
python -m pip install -r requirements.txt
```

The reported run was tested with Python 3.13.18, pandas 3.1.1, openpyxl 3.1.5, xlrd 2.0.2 and pytest 9.2.0 on Windows 11. The code uses only `pandas`, `openpyxl` and `xlrd`; `xlrd` is needed only when reading legacy `.xls` input.

## Reproduce the results

Run from the repository root:

```bash
python -m src.cli -i "data/s1 dataset.xlsx" -o output/reproduced_results.xlsx
```

To regenerate the included workbook in place, use the default output path:

```bash
python -m src.cli -i "data/s1 dataset.xlsx" -o output/deduplication_results.xlsx
```

The console prints the record counts for each result set and the elapsed time. On the test machine the pipeline took about 58 s of computation and about 90 s wall-clock time, including Python startup and workbook writing. Runtime depends on CPU and disk speed.

## Expected output

The included workbook and a fresh run on `data/s1 dataset.xlsx` contain:

| Worksheet | Rows | Content |
|---|---:|---|
| `Records from IR` | 24,612 | IR records, five metadata columns |
| `Records from RMS` | 18,157 | RMS records, six metadata columns |
| `Overlapping Publications` | 18,144 | Each RMS record and its most similar IR record |
| `Definite Duplicates` | 17,599 | Pairs classified as definite duplicates |
| `Suspected-Du & Key-Attention` | 545 | Pairs classified as suspected duplicates or key attention |

The last worksheet combines two categories, following `src/writer.py`; it does not contain a separate category column. Reapplying `src.config.Thresholds` to the 545 rows gives 487 Key Attention (69 with title similarity ≥ 80 and source similarity < 70, plus 418 fallback records) and 58 Suspected Duplicate (41 with title similarity 50–80, plus 17 with title similarity 30–50 and source similarity > 70).

The title-similarity range in `Overlapping Publications` is 8.57–100.00; the source-similarity range is 0.00–100.00. These are the values produced by the current code on the included input, not a claim that every manuscript table has the same rounding or aggregation.

## Input data

`data/s1 dataset.xlsx` contains two worksheets:

- `Records from IR`: 24,612 rows — 23,513 Article and 1,099 Conference Paper; publication years 1987–2020; columns `Document Type`, `Title`, `Source`, `Author`, `Publish Date`.
- `Records from RMS`: 18,157 rows — 17,978 Article and 179 Conference Paper; publication years 1984–2020; columns `Title`, `Publish Date`, `left`, `Document Type`, `Source`, `Author`. The `left` column is a helper column preserved from the RMS export.

The data are bibliographic metadata (titles, venues, author names and dates). No full text, PDFs or proprietary content are included. SHA-256 of the input workbook:

```text
B59435547F0B78418E10A4EC76BE4C0625A96472F4AB8CF858D953AA8AB97668
```

SHA-256 of the included result workbook:

```text
6C383DF6DDA3BA1C09B7725CD43D90DC9B24536B935E2C04F1BBD7B05FB41222
```

## Method in brief

1. Identify whether each title contains Chinese characters.
2. Remove Unicode punctuation and the configured symbol set.
3. Segment Chinese text character by character and English text word by word.
4. Compute Jaccard similarity over the segmented sets.
5. Apply the front-end fixed scores: identical raw text 100.00, English case variant 99.99, punctuation/spacing variant 99.98.
6. When one text contains the other, add a length-ratio term capped at 99.97.
7. Recall candidates with a Chinese-bigram and English-word inverted index, score the best candidate for each RMS record, and classify it with the thresholds in `src/config.py`.

The method uses surface units only; it does not use word order or semantic representations.

## Tests

```bash
python -m pytest -q
```

Expected: `22 passed`. The tests cover the scoring primitives (identical, case-variant, punctuation-variant, inclusion cap, Chinese character Jaccard, empty input, author matching) and the classification rules. They do not run the full 24,612 × 18,157 pipeline; the full run is reproduced by the command above.

## License

- **Source code** (`src/`, `tests/`, and the build/configuration files): MIT License. See `LICENSE`. PLOS ONE explicitly lists MIT as a suitable open-source license for software, and it permits reuse, modification and redistribution with attribution.
- **Data** (`data/s1 dataset.xlsx` and `output/deduplication_results.xlsx`): CC0 1.0 Universal public-domain dedication. See `DATA_LICENSE.md`. PLOS requires data-repository policies to be no more restrictive than CC BY 4.0; CC0 is more permissive and is appropriate for bibliographic metadata that the authors have declared free of restrictions.

The two licenses are deliberately separate: MIT is a software license, while CC0 is a data dedication. Neither license imposes a non-commercial or share-alike condition.

## Data and code availability

Suitable statement for the manuscript:

> The source code, user guide, test dataset and five-sheet S1 result workbook are publicly available at https://github.com/lulinong8/ir-rms-title-deduplication under the MIT License (code) and CC0 1.0 (data). The archived release is available at [Zenodo DOI].

Replace `[Zenodo DOI]` after archiving the GitHub release with Zenodo. PLOS recommends a repository that issues persistent identifiers; GitHub provides the public, login-free code archive, and Zenodo provides the DOI for the release.

## Archiving

For a citeable release:

1. Create a GitHub release tagged `v1.0.0`.
2. Connect the repository to Zenodo (or upload the release archive manually) and mint a DOI.
3. Insert the DOI into the manuscript's Data availability and Code availability statements, replacing `[X12]` and `[X13]`.

## Contact

Corresponding author: Linong Lu, `luln@llas.ac.cn`.
