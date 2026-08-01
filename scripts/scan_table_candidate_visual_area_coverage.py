"""Exploratory scan: table x visual overlap, denominated on the table's own area.

Companion to scripts/scan_table_candidate_interior_visual_overlap_ratio.py.
That script's overlap_ratio field is overlap_area / min(table_area, box_area)
(page_analysis_co_reference_candidate_overlap_ratio_measurements.py) -- the
right denominator for interior_visual_frame/embedded_visual deduplication
(E1, symmetric by design, cc89248/9368a5c), but not for the question this
script asks: "how much of this table candidate's own area does a visual
cover", which needs table_area fixed as the denominator regardless of which
side happens to be smaller. A tiny box fully inside a huge table candidate
gives overlap_ratio near 1.0 in the companion script's field even though it
covers a negligible fraction of the table -- confirmed on DB/Fab/Lan real
output (e.g. Fab.pdf page 133, dozens of ~1-2pt-tall raster candidates with
overlap_ratio>=0.9 that cover under 1% of the table's own area).

This script does not re-open the source PDF and does not re-run any producer:
it reads the pair-level output already produced by
scan_table_candidate_interior_visual_overlap_ratio.py (table_bbox/box_bbox
are already exact, per pair, per page) and recomputes
intersection_area / table_area for each pair. Like its companion, it does not
choose or apply any threshold -- raw numbers per table candidate, plus the
raster/vector origin of the best-matching box, so the real distribution can
be inspected before any Resolution rule is proposed on top of it.

Not a producer, not wired anywhere, no persistence, no PDF/pdfplumber/fitz
dependency -- pure post-processing of one or more scan output JSON files.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _area(bbox: list[float]) -> float:
    return max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])


def _intersection_area(first: list[float], second: list[float]) -> float:
    x0 = max(first[0], second[0])
    y0 = max(first[1], second[1])
    x1 = min(first[2], second[2])
    y1 = min(first[3], second[3])
    return _area([x0, y0, x1, y1])


def _box_kind(box_candidate_id: str) -> str:
    if "raster" in box_candidate_id:
        return "raster"
    if "vector" in box_candidate_id:
        return "vector"
    return "unknown"


def _best_per_table(pairs: list[dict[str, Any]]) -> dict[tuple[int, str], dict[str, Any]]:
    """For each (page_number, table_candidate_id), keep the pair whose box
    covers the largest fraction of the table candidate's own area."""

    best: dict[tuple[int, str], dict[str, Any]] = {}
    for pair in pairs:
        table_bbox = pair["table_bbox"]
        table_area = _area(table_bbox)
        if table_area <= 0.0:
            continue
        coverage_ratio = _intersection_area(table_bbox, pair["box_bbox"]) / table_area
        key = (pair["page_number"], pair["table_candidate_id"])
        if key not in best or coverage_ratio > best[key]["table_area_coverage_ratio"]:
            best[key] = {
                "page_number": pair["page_number"],
                "table_candidate_id": pair["table_candidate_id"],
                "table_bbox": table_bbox,
                "box_candidate_id": pair["box_candidate_id"],
                "box_bbox": pair["box_bbox"],
                "box_kind": _box_kind(pair["box_candidate_id"]),
                "table_area_coverage_ratio": coverage_ratio,
            }
    return best


def scan_area_coverage(scan_output: dict[str, Any]) -> dict[str, Any]:
    """Recompute table-area-denominated coverage from one scan output's pairs."""

    report: dict[str, Any] = {
        "input": scan_output.get("input"),
        "totals": scan_output.get("totals"),
    }
    for pairs_key, box_kind_key in (
        ("table_x_embedded_visual_pairs", "embedded_visual"),
        ("table_x_interior_visual_frame_pairs", "interior_visual_frame"),
    ):
        pairs = scan_output.get(pairs_key, [])
        best = _best_per_table(pairs)
        entries = sorted(
            best.values(),
            key=lambda entry: -entry["table_area_coverage_ratio"],
        )
        report[f"table_area_coverage_vs_{box_kind_key}"] = {
            "distinct_table_candidates_with_a_pair": len(entries),
            "table_area_coverage_ratios_sorted_desc": [
                entry["table_area_coverage_ratio"] for entry in entries
            ],
            "best_pair_per_table_candidate": entries,
        }
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "scan_output_json",
        type=Path,
        nargs="+",
        help="one or more scan_table_candidate_interior_visual_overlap_ratio.py JSON outputs",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    reports = {}
    for path in args.scan_output_json:
        with path.open(encoding="utf-8") as handle:
            scan_output = json.load(handle)
        reports[str(path)] = scan_area_coverage(scan_output)
    print(json.dumps(reports, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
