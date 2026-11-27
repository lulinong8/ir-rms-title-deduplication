# User Guide: Dictionary-free language-adaptive title deduplication

**Release:** v1.0.1 (2026-11-27)  
**Version DOI:** [10.5281/zenodo.24576834](https://doi.org/10.5281/zenodo.24576834)  
**Companion manuscript:** Lu L, Yang B, Wang X. *A dictionary-free language-adaptive text similarity algorithm for academic literature deduplication in institutional repositories.* PLOS ONE (under review; PONE-D-26-35837).

## 1. Overview

This tool compares publication records from an institutional repository (IR) and a research management system (RMS). It recalls candidate IR records for each RMS record, scores title, source (venue) and author fields, and writes a five-sheet result workbook.

The implementation is dictionary-free. Chinese titles are segmented into characters; English titles are segmented into lowercased words. No word-segmentation model, embeddings or external service is required.

## 2. Requirements

- Python 3.11 or later.
- Install the pinned dependencies from the repository root:

```bash
python -m pip install -r requirements.txt
```

The pinned versions are pandas 3.1.1, openpyxl 3.1.5, xlrd 2.0.2 and pytest 9.2.0. The reported run used Python 3.13.18 on Windows 11. `xlrd` is needed only for legacy `.xls` input; `.xlsx` input is read through `openpyxl`.

## 3. Directory layout

All paths are relative to the repository root:

```text
./
├─ src/                      # Python source code
│  ├─ cli.py                 # Command-line entry point
│  ├─ config.py              # Columns, thresholds and recall settings
│  ├─ dataset.py             # Input workbook reader
│  ├─ retrieval.py           # Inverted-index candidate recall
│  ├─ similarity.py          # Language identification, cleaning and scoring
│  ├─ pipeline.py            # Recall, scoring, classification and result sets
│  ├─ writer.py              # Five-sheet result writer
│  └─ excel_utils.py         # Excel-safe text cleanup
├─ doc/                      # Documentation
├─ data/s1 dataset.xlsx      # Input data
├─ output/                   # Output workbooks
├─ tests/                    # Unit tests
├─ requirements.txt          # Pinned dependencies
└─ CITATION.cff              # Citation metadata
```

## 4. Input requirements

Input files may be `.xls` or `.xlsx` and must contain the `Records from IR` and `Records from RMS` worksheets. Header names must match the expected names; leading and trailing whitespace is stripped before matching. The header row is searched within the first 20 rows, so a title row above the header is allowed; data start on the following row.

### 4.1 Records from IR

| Header | Description |
|---|---|
| Document Type | Document type, for example `Article` |
| Title | Publication title |
| Source | Source (journal) name |
| Author | Authors separated by semicolons |
| Publish Date | Publication date |

### 4.2 Records from RMS

| Header | Description |
|---|---|
| Title | Publication title |
| Publish Date | Publication date |
| left | Input helper column, preserved as provided |
| Document Type | Document type, for example `Article` |
| Source | Source (journal) name |
| Author | Authors separated by semicolons |

Worksheet detection first tries an exact name match and then a prefix match. If a workbook contains a title row above the header, it is skipped.

## 5. Quick start

Run from the repository root:

```bash
python -m src.cli -i "data/s1 dataset.xlsx" -o output/deduplication_results.xlsx
```

The console prints the record counts for each result set and the elapsed time. Results are written to the specified workbook. Input files are never modified.

Run the tests:

```bash
python -m pytest -q
```

Expected: `22 passed`.

## 6. Command-line options

| Option | Default | Description |
|---|---|---|
| `--input`, `-i` | `data/s1 dataset.xlsx` | Input data file |
| `--output`, `-o` | `output/deduplication_results.xlsx` | Output workbook |
| `--anchors` | `8` | Number of inverted-index features used for recall |
| `--max-candidates` | `200` | Maximum candidates scored per RMS record |
| `--min-intersection-similarity` | `0` | Minimum title similarity retained in Overlapping Publications |
| `--duplicate-title` | `80` | Title threshold for Definite Duplicate |
| `--duplicate-journal` | `70` | Source threshold for Definite Duplicate |
| `--key-title` | `70` | Title threshold for the author-matched Definite Duplicate rule |
| `--key-journal` | `90` | Source threshold for the author-matched Definite Duplicate rule |
| `--suspect-title` | `30` | Minimum title similarity for Suspected Duplicate |
| `--suspect-title-mid` | `50` | Title similarity that directly yields Suspected Duplicate |
| `--suspect-journal` | `70` | Source threshold for low title similarity |

Example: broaden candidate recall.

```bash
python -m src.cli -i "data/s1 dataset.xlsx" -o output/deduplication_results.xlsx --anchors 12 --max-candidates 300
```

## 7. Processing flow

1. Read `Records from IR` and `Records from RMS` and normalize field names.
2. Build an inverted index of IR titles using Chinese character bigrams and English words.
3. Select low-frequency features of each RMS title as anchors and recall candidate IR records.
4. Score candidates, retain the most similar IR record, then compute source similarity and author containment.
5. Assign Definite Duplicate, Suspected Duplicate or Key Attention.
6. Write the five-sheet result workbook.

## 8. Similarity and classification

### 8.1 Similarity

- Chinese text is compared character by character; English text is compared word by word, ignoring case.
- Punctuation, Unicode symbols and ASCII whitespace are removed before comparison. Digits and CJK characters are retained.
- Similarity is Jaccard similarity over the segmented units.
- When one text contains the other, a length-ratio term is added, capped at 99.97.
- Identical raw text returns 100.00; an English case variant returns 99.99; a punctuation or ASCII-whitespace variant returns 99.98.
- Scores are rounded to two decimal places.

The current scorer retains the ideographic space U+3000, while recall keys remove it. Titles that differ only by U+3000 versus an ASCII space are therefore not guaranteed to be treated as whitespace variants.

### 8.2 Classification rules

| Category | Condition |
|---|---|
| Definite Duplicate | Title similarity ≥ 80 and source similarity ≥ 70 |
| Definite Duplicate | Title similarity ≥ 70, source similarity > 90, and authors are related |
| Key Attention | Title similarity ≥ 80 and source similarity < 70 |
| Suspected Duplicate | 50 ≤ title similarity < 80 |
| Suspected Duplicate | 30 ≤ title similarity < 50 and source similarity > 70 |
| Key Attention | Any other recalled record retained in Overlapping Publications |

"Authors are related" means that, after splitting both author lists on semicolons, at least one author name on one side is a substring of an author name on the other side.

The last row is a fallback rule: every recalled record enters either Definite Duplicate or the combined Suspected-Du & Key-Attention worksheet. Therefore:

```text
Overlapping Publications = Definite Duplicates + Suspected-Du & Key-Attention
```

`Definite Duplicate` is a rule-generated label, not an adjudicated ground-truth label. No manual precision/recall estimate is included in this release.

## 9. Output worksheets

| Worksheet | Content |
|---|---|
| Records from IR | Original IR input records |
| Records from RMS | Original RMS input records |
| Overlapping Publications | Each RMS record and its most similar IR record |
| Definite Duplicates | Pairs satisfying the Definite Duplicate rules |
| Suspected-Du & Key-Attention | Combined review worksheet |

The combined worksheet contains 69 key-attention records, 58 suspected duplicates and 418 lower-similarity fallback records in the included run. It does not contain a separate category column.

All comparison sheets use these columns:

```text
Document Type, Title From RSM, Title From IR, Title's Similarity Score,
Source From SRM, Source From IR, Source's Similarity Score,
Author From SRM, Author From IR, Publish Date From SRM, Publish Date From IR
```

Similarity columns keep two decimal places and can be sorted or filtered directly in Excel.

## 10. Performance and tuning

With 24,612 IR records and 18,157 RMS records, the reported run took about 117 s wall-clock: about 15.4 s reading, 2.7 s indexing, 84 s recall/scoring/classification and 15.0 s writing. Memory use is dominated by the inverted index and result sets. Runtime depends on CPU and disk speed.

Tuning options:

- `--anchors`: increase to improve recall at the cost of runtime.
- `--max-candidates`: increase to avoid candidate truncation at the cost of scoring time.
- `--min-intersection-similarity`: set to 30 to retain only candidates that can reach classification in Overlapping Publications.

## 11. FAQ

**Q: How do the row counts relate?**

`Overlapping Publications` retains every recalled record, and every such record is assigned to either `Definite Duplicates` or `Suspected-Du & Key-Attention`. The identity above always holds.

**Q: Why is the similarity 99.98 or 99.97 instead of 100.00?**

99.98 means the texts are identical after punctuation removal. 99.97 means one text contains the other and receives a length-ratio term capped below 100. Only exactly identical raw texts return 100.00.

**Q: Why do two titles with different space characters score differently?**

The current scorer normalizes ASCII whitespace only and retains U+3000. This is a known boundary condition of v1.0.1, not a guarantee that all whitespace variants collapse to the same score.

**Q: Do control characters in the input affect the output?**

Excel-incompatible control characters are removed when writing the result workbook so that the file remains valid. Input files are never modified.
