"""Driver for check_callout_text_pattern.py over the 9 rows of milestone35_oracle_cases.csv.

Joins each oracle row (manual, page_index, cluster_id) against the real bbox_x0..bbox_y1
already computed for that cluster in <manual>_clusters.csv (the CSV produced by
scan_embedded_visual_interior_visual_frame_twin_diagnostics.py, targeted run with --pages,
per the earlier oracle build). This script does NOT recompute or guess bbox coordinates --
they are read from the existing CSVs on this machine, not from anything I (Chat A) recorded
in a prior message. If a (page_index, cluster_id) pair from the oracle is not found in the
corresponding clusters CSV, the row is reported as unresolved and skipped, not guessed.

Requires check_callout_text_pattern.py in the same directory (imports check_region/scan_one
from it directly, not a subprocess, to avoid re-deriving the bbox lookup logic twice).

Usage:
    python run_callout_text_pattern_check.py \\
        --oracle milestone35_oracle_cases.csv \\
        --clusters-dir /path/to/dir/with/<prefix>_clusters.csv/files \\
        --pdf-dir /path/to/dir/with/<prefix>.pdf/files \\
        --out callout_text_pattern_results.csv

<prefix> is the manual code (Dag, Kul, Lan, DB, ...) matching the oracle's "manual" column,
and is expected as the exact filename stem before "_clusters.csv" / ".pdf" respectively
(per the user's own convention: "le sigle sono la radice del nome prima di .pdf").
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_callout_text_pattern import scan_one  # noqa: E402


def _load_clusters_bbox(
    clusters_csv: Path,
) -> dict[tuple[str, str], tuple[float, float, float, float]]:
    bbox_by_key: dict[tuple[str, str], tuple[float, float, float, float]] = {}
    with clusters_csv.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = (row["page_index"], row["cluster_id"])
            try:
                bbox = (
                    float(row["bbox_x0"]),
                    float(row["bbox_y0"]),
                    float(row["bbox_x1"]),
                    float(row["bbox_y1"]),
                )
            except KeyError, ValueError:
                continue
            # A (page_index, cluster_id) pair can repeat across roles/branches (original +
            # subclusters) with different bboxes; keep the first "role=original" match if
            # present, else the first row seen -- declared, not silent.
            if key not in bbox_by_key or row.get("role") == "original":
                bbox_by_key[key] = bbox
    return bbox_by_key


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--clusters-dir", type=Path, required=True)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    with args.oracle.open("r", newline="", encoding="utf-8") as handle:
        oracle_rows = list(csv.DictReader(handle))

    bbox_cache: dict[str, dict[tuple[str, str], tuple[float, float, float, float]]] = {}
    out_rows: list[dict[str, object]] = []

    for oracle_row in oracle_rows:
        manual = oracle_row["manual"]
        page_index = oracle_row["page_index"]
        cluster_id = oracle_row["cluster_id"]
        label = oracle_row["label"]

        if manual not in bbox_cache:
            clusters_csv = args.clusters_dir / f"{manual}_clusters.csv"
            if not clusters_csv.exists():
                bbox_cache[manual] = {}
            else:
                bbox_cache[manual] = _load_clusters_bbox(clusters_csv)

        bbox = bbox_cache[manual].get((page_index, cluster_id))
        if bbox is None:
            out_rows.append(
                {
                    "manual": manual,
                    "page_index": page_index,
                    "cluster_id": cluster_id,
                    "label": label,
                    "status": "bbox_not_found",
                    "text_primitive_count_in_region": "",
                    "title_like_lines": "",
                    "body_like_lines_individual": "",
                    "combined_text_is_body_like": "",
                    "has_title_and_body_pattern": "",
                }
            )
            continue

        pdf_path = args.pdf_dir / f"{manual}.pdf"
        if not pdf_path.exists():
            out_rows.append(
                {
                    "manual": manual,
                    "page_index": page_index,
                    "cluster_id": cluster_id,
                    "label": label,
                    "status": f"pdf_not_found:{pdf_path}",
                    "text_primitive_count_in_region": "",
                    "title_like_lines": "",
                    "body_like_lines_individual": "",
                    "combined_text_is_body_like": "",
                    "has_title_and_body_pattern": "",
                }
            )
            continue

        result = scan_one(pdf_path, page_index=int(page_index), bbox=bbox)
        out_rows.append(
            {
                "manual": manual,
                "page_index": page_index,
                "cluster_id": cluster_id,
                "label": label,
                "status": "ok",
                "text_primitive_count_in_region": result["text_primitive_count_in_region"],
                "title_like_lines": " | ".join(result["title_like_lines"]),
                "body_like_lines_individual": " | ".join(result["body_like_lines_individual"]),
                "combined_text_is_body_like": result["combined_text_is_body_like"],
                "has_title_and_body_pattern": result["has_title_and_body_pattern"],
            }
        )

    fieldnames = [
        "manual",
        "page_index",
        "cluster_id",
        "label",
        "status",
        "text_primitive_count_in_region",
        "title_like_lines",
        "body_like_lines_individual",
        "combined_text_is_body_like",
        "has_title_and_body_pattern",
    ]
    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Scritte {len(out_rows)} righe in {args.out}")
    for row in out_rows:
        print(
            f"  {row['manual']} p.{row['page_index']} {row['label']}: "
            f"status={row['status']} has_title_and_body_pattern={row['has_title_and_body_pattern']}"
        )


if __name__ == "__main__":
    main()
