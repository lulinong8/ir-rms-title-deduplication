"""Command line entry point.

Usage:
    python -m src.cli --input "data/s1 dataset.xlsx" --output output/deduplication_results.xlsx
"""

from __future__ import annotations

import argparse
import os

from .config import RetrievalConfig, RunConfig, Thresholds
from .dataset import load_source
from .pipeline import run_pipeline
from .writer import write_workbook


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="IR vs. Research management system (RMS) publication deduplication")
    parser.add_argument("--input", "-i", default=os.path.join("data", "s1 dataset.xlsx"), help="Input workbook (.xls/.xlsx)")
    parser.add_argument(
        "--output",
        "-o",
        default=os.path.join("output", "deduplication_results.xlsx"),
        help="Output workbook (.xlsx)",
    )
    parser.add_argument("--anchors", type=int, default=8, help="Number of inverted-index anchors used for recall")
    parser.add_argument("--max-candidates", type=int, default=200, help="Maximum candidates scored per RMS record")
    parser.add_argument(
        "--min-intersection-similarity",
        type=float,
        default=0.0,
        help="Minimum title similarity required for Overlapping Publications",
    )

    parser.add_argument("--duplicate-title", type=float, default=80.0, help="Title threshold for Definite Duplicate")
    parser.add_argument("--duplicate-journal", type=float, default=70.0, help="Source threshold for Definite Duplicate")
    parser.add_argument("--key-title", type=float, default=70.0, help="Title threshold for author-matched Definite Duplicate")
    parser.add_argument("--key-journal", type=float, default=90.0, help="Source threshold for author-matched Definite Duplicate")
    parser.add_argument("--suspect-title", type=float, default=30.0, help="Minimum title similarity for Suspected Duplicate")
    parser.add_argument("--suspect-title-mid", type=float, default=50.0, help="Title similarity that directly yields Suspected Duplicate")
    parser.add_argument("--suspect-journal", type=float, default=70.0, help="Source threshold for low title similarity")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    thresholds = Thresholds(
        duplicate_title=args.duplicate_title,
        duplicate_journal=args.duplicate_journal,
        key_title=args.key_title,
        key_journal=args.key_journal,
        suspect_title=args.suspect_title,
        suspect_title_mid=args.suspect_title_mid,
        suspect_journal=args.suspect_journal,
    )
    retrieval = RetrievalConfig(
        anchors=args.anchors,
        max_candidates=args.max_candidates,
        min_intersection_similarity=args.min_intersection_similarity,
    )

    print(f"Reading: {args.input}")
    source = load_source(args.input)
    print(f"  IR records: {len(source.library)}, RMS records: {len(source.research)}")
    print("Running deduplication...")

    result = run_pipeline(source, RunConfig(thresholds=thresholds, retrieval=retrieval))
    for name, value in result.stats.items():
        print(f"  {name}: {value}")
    print(f"Elapsed: {result.elapsed_seconds:.1f}s")

    output_dir = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(output_dir, exist_ok=True)
    write_workbook(args.output, source, result)
    print(f"Results written to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
