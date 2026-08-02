"""Three cheap readouts on the CSVs already produced by
scan_embedded_visual_interior_visual_frame_twin_diagnostics.py, requested by Chat B round 4 (§D)
before any manual visual labeling of the 78 remaining target-population clusters:

D1 (B2): is the fill-axis and stroke-axis color re-partition actually producing independent
evidence, or the same subclusters twice? For each target cluster, compares the set of PASSING
(area in_range AND has_text) subcluster bboxes on the fill axis against the stroke axis. If they
are identical and non-empty, "supported_by_either" is not combining two checks -- it is one check
counted once, dressed as two.

D2 (B4): page_index concentration. Counts how many of the target-population clusters share the
same page_index per manual, and how many DISTINCT pages they span. A population concentrated on
few distinct pages is not the same number of independent observations as one spread across many
-- a repeated template (e.g. one character-sheet layout printed for N classes) inflates the raw
cluster count without adding N independent data points.

D3 (B3): lists every target-population row that has NO passing subcluster on either axis --
the only rows where the (iv) test says "no". On the data already summarized once
(Kul: 1 of 2), this is at most a handful of rows across all 7 manuals; printed in full with page
index and bbox for direct visual inspection, no sampling.

Reads <prefix>_clusters.csv and <prefix>_subclusters.csv, produced by
scan_embedded_visual_interior_visual_frame_twin_diagnostics.py. Does not reopen any PDF, does not
call any producer, chooses no new threshold -- pure aggregation, same standard as
summarize_milestone35_measures.py which it is a companion to (not a replacement).
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bbox_key(row: dict[str, str]) -> tuple[float, float, float, float]:
    return (
        round(float(row["bbox_x0"]), 3),
        round(float(row["bbox_y0"]), 3),
        round(float(row["bbox_x1"]), 3),
        round(float(row["bbox_y1"]), 3),
    )


def _passes(row: dict[str, str]) -> bool:
    return row["area_filter_result"] == "in_range" and row["text_filter_result"] == "has_text"


def inspect(clusters_path: Path, subclusters_path: Path) -> dict[str, Any]:
    clusters = _read_csv(clusters_path)
    subclusters = _read_csv(subclusters_path)

    target = [
        row
        for row in clusters
        if row["branch"] == "vector"
        and row["area_filter_result"] == "above_max"
        and int(row["member_count"]) >= 2
    ]

    sub_by_parent_axis: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in subclusters:
        sub_by_parent_axis[(row["cluster_id"], row["role"])].append(row)

    # D1: axis redundancy
    identical_nonempty = 0
    fill_only = 0
    stroke_only = 0
    both_different = 0
    neither = 0
    negatives: list[dict[str, Any]] = []

    for row in target:
        cid = row["cluster_id"]
        fill_subs = sub_by_parent_axis.get((cid, "subcluster_fill"), [])
        stroke_subs = sub_by_parent_axis.get((cid, "subcluster_stroke"), [])
        fill_pass_bboxes = frozenset(_bbox_key(s) for s in fill_subs if _passes(s))
        stroke_pass_bboxes = frozenset(_bbox_key(s) for s in stroke_subs if _passes(s))

        if fill_pass_bboxes and stroke_pass_bboxes:
            if fill_pass_bboxes == stroke_pass_bboxes:
                identical_nonempty += 1
            else:
                both_different += 1
        elif fill_pass_bboxes:
            fill_only += 1
        elif stroke_pass_bboxes:
            stroke_only += 1
        else:
            neither += 1
            negatives.append(
                {
                    "page_index": row["page_index"],
                    "cluster_id": cid,
                    "bbox": [row["bbox_x0"], row["bbox_y0"], row["bbox_x1"], row["bbox_y1"]],
                    "member_count": row["member_count"],
                    "page_area_ratio": row["page_area_ratio"],
                }
            )

    # D2: page_index concentration
    page_counter = Counter(row["page_index"] for row in target)

    return {
        "target_population_count": len(target),
        "d1_axis_redundancy": {
            "identical_passing_set_both_axes": identical_nonempty,
            "fill_only_passes": fill_only,
            "stroke_only_passes": stroke_only,
            "both_pass_different_subclusters": both_different,
            "neither_axis_passes": neither,
        },
        "d2_page_concentration": {
            "distinct_pages_with_a_target_cluster": len(page_counter),
            "clusters_per_page_index": dict(sorted(page_counter.items(), key=lambda kv: -kv[1])),
        },
        "d3_negative_rows_no_passing_subcluster_on_either_axis": negatives,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "prefix",
        type=Path,
        nargs="+",
        help="same <prefix> given to scan_embedded_visual_interior_visual_frame_twin_diagnostics.py",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report: dict[str, Any] = {}
    for prefix in args.prefix:
        clusters_path = prefix.with_name(prefix.name + "_clusters.csv")
        subclusters_path = prefix.with_name(prefix.name + "_subclusters.csv")
        report[prefix.name] = inspect(clusters_path, subclusters_path)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
