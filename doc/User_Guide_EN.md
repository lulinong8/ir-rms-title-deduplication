# User Guide: IR vs. Research management system Publication Deduplication

## 1. Overview

This tool compares publication data from IR and the Research management system (RMS) to identify duplicate and suspected duplicate records.

Key features:

- Computes similarity for Chinese, English, and mixed-language titles and sources;
- Automatically recalls the most similar IR record for each RMS record;
- Classifies candidate pairs into Definite Duplicate, Suspected Duplicate, and Key Attention using percentage thresholds;
- Produces 5 worksheets covering overlapping publications and classification results.

## 2. Requirements

- Python 3.10 or later
- Required packages:

```powershell
python -m pip install pandas openpyxl xlrd
```

`xlrd` is used to read `.xls` files and `openpyxl` is used to write `.xlsx` files.

## 3. Directory Layout

All paths below are relative to the current directory:

```text
./
├─ src/                      # Python source code
│  ├─ cli.py                 # Command-line entry point
│  ├─ config.py              # Columns, thresholds, retrieval settings
│  ├─ dataset.py             # Input reader
│  ├─ retrieval.py           # Candidate recall
│  ├─ similarity.py          # Similarity scoring
│  ├─ pipeline.py            # Deduplication pipeline
│  ├─ writer.py              # Result writer
│  └─ excel_utils.py         # Excel output helpers
├─ doc/                      # Documentation
├─ data/s1 dataset.xlsx      # Input data
└─ output/                   # Output files (deduplication_results.xlsx)
```

## 4. Input Requirements

Input files may be `.xls` or `.xlsx` and must contain the `Records from IR` and `Records from RMS` worksheets.

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

Worksheet detection:

1. Names matching `Records from IR` and `Records from RMS` are used;
2. If a name differs, a prefix match is used.

The header row should be the first row and data should start from the second row. A title row above the header is allowed.

## 5. Quick Start

Run the following in the current directory:

```powershell
python -m src.cli -i "data/s1 dataset.xlsx" -o output/deduplication_results.xlsx
```

When the run finishes, the console shows the record counts for each result set and the elapsed time. Results are written to the specified file.

## 6. Command-Line Options

| Option | Default | Description |
|---|---|---|
| `--input`, `-i` | `data/s1 dataset.xlsx` | Input data file |
| `--output`, `-o` | `output/deduplication_results.xlsx` | Output file |
| `--anchors` | `8` | Number of inverted-index features used for recall |
| `--max-candidates` | `200` | Maximum candidates scored per RMS record |
| `--min-intersection-similarity` | `0` | Minimum title similarity for Overlapping Publications |
| `--duplicate-title` | `80` | Title similarity threshold for Definite Duplicate |
| `--duplicate-journal` | `70` | Source similarity threshold for Definite Duplicate |
| `--key-title` | `70` | Title threshold for author-matched Definite Duplicate |
| `--key-journal` | `90` | Source threshold for author-matched Definite Duplicate |
| `--suspect-title` | `30` | Minimum title similarity for Suspected Duplicate |
| `--suspect-title-mid` | `50` | Title similarity that directly yields Suspected Duplicate |
| `--suspect-journal` | `70` | Source threshold for low title similarity |

Example: broaden candidate recall.

```powershell
python -m src.cli -i "data/s1 dataset.xlsx" -o output/deduplication_results.xlsx --anchors 12 --max-candidates 300
```

## 7. Processing Flow

1. **Read data**: load `Records from IR` and `Records from RMS` and normalize field names;
2. **Build the index**: create an inverted index of IR titles using Chinese character bigrams and English words;
3. **Recall candidates**: select low-frequency features of each RMS title as anchors and recall candidate IR records;
4. **Score candidates**: compute exact title similarity, keep the most similar record, then compute source similarity and author containment;
5. **Classify**: assign Definite Duplicate, Suspected Duplicate, or Key Attention by threshold;
6. **Write results**: produce 5 worksheets.

### 7.1 Similarity Algorithm

- Chinese text is compared character by character using Jaccard similarity after removing punctuation, symbols, and spaces;
- English text is compared word by word using Jaccard similarity, ignoring case;
- When one text contains the other, a length-ratio bonus is added, capped at 99.97;
- Chinese texts that are identical after punctuation removal score 99.98; English texts that match case-insensitively score 99.99;
- Results are rounded to two decimal places.

## 8. Classification Rules

| Category | Condition |
|---|---|
| Definite Duplicate | Title similarity ≥ 80 and source similarity ≥ 70 |
| Definite Duplicate | Title similarity ≥ 70, source similarity > 90, and authors are related |
| Key Attention | Title similarity ≥ 80 and source similarity < 70 |
| Suspected Duplicate | 50 ≤ title similarity < 80 |
| Suspected Duplicate | 30 ≤ title similarity < 50 and source similarity > 70 |
| Key Attention | Any other recalled record that enters Overlapping Publications (fallback) |

"Authors are related" means that, after splitting both author lists by semicolons, at least one author name on one side is a substring of an author name on the other side.

The last row is a fallback rule: every recalled record that enters Overlapping Publications is assigned either Definite Duplicate or Suspected-Du & Key-Attention, which guarantees `Overlap = Definite + Suspected & Key Attention`.

## 9. Output Worksheets

The output workbook contains 5 worksheets:

| Worksheet | Content |
|---|---|
| Records from IR | Original IR input records |
| Records from RMS | Original RMS input records |
| Overlapping Publications | Each RMS record and its most similar IR record |
| Definite Duplicates | Pairs classified as Definite Duplicate |
| Suspected-Du & Key-Attention | Pairs classified as Suspected Duplicate or Key Attention |

`Suspected-Du & Key-Attention` holds every record in Overlapping Publications that is not classified as Definite Duplicate, so the following identity always holds:

```text
Overlapping Publications = Definite Duplicates + Suspected-Du & Key-Attention
```

Records whose title similarity is ≥ 80 and source similarity < 70 are Key Attention; the rest are suspected duplicates or low-similarity fallback records.

All comparison sheets use these columns:

```text
Document Type, Title From RSM, Title From IR, Title's Similarity Score,
Source From SRM, Source From IR, Source's Similarity Score,
Author From SRM, Author From IR, Publish Date From SRM, Publish Date From IR
```

Similarity columns keep two decimal places and can be sorted or filtered directly in Excel.

## 10. Performance and Tuning

With the current sample of 24,612 IR records and 18,157 RMS records, a full run takes about 25 seconds. Memory usage is dominated by the inverted index and the result sets.

Tuning options:

- `--anchors`: increase to improve recall at the cost of runtime;
- `--max-candidates`: increase to avoid candidate truncation at the cost of scoring time;
- `--min-intersection-similarity`: set to 30 to keep only candidates that can reach classification in Overlapping Publications.

## 11. FAQ

**Q: How do the row counts of Overlapping Publications, Definite Duplicates, and Suspected-Du & Key-Attention relate?**

Overlapping Publications keeps every recalled record, and every such record is assigned to either Definite Duplicates or Suspected-Du & Key-Attention, so the counts are always equal:

```text
Overlapping Publications = Definite Duplicates + Suspected-Du & Key-Attention
```

**Q: Why is the similarity 99.98 or 99.97 instead of 100?**

99.98 means the texts are identical after punctuation removal. 99.97 means one text contains the other and receives a length-ratio bonus capped below 100. Only exactly identical raw texts return 100.00.

**Q: Why do the counts differ from historical cleaning results?**

Historical results may be based on a different data snapshot or a different recall range. This tool recalculates from the current input file using the same classification rules.

**Q: Do special control characters in the input affect the output?**

Excel-incompatible control characters are removed before writing so the workbook stays valid. Input files are never modified.
