"""Aggregates the per-cluster/per-subcluster CSVs from
scan_embedded_visual_interior_visual_frame_twin_diagnostics.py into the numbers the closing
criteria in Proposta_Milestone35_ClusteringColorDiagnostics_v4.md (Criteri di chiusura) actually
need. Pure aggregation over already-produced CSVs -- reopens no PDF, calls no producer, chooses
no new threshold: uses only the two filters interior_visual_frame already applies in production
(_DEFAULT_MIN_AREA_RATIO/_DEFAULT_MAX_AREA_RATIO = 0.006/0.28, contained_text_primitive_count>0).

Target population for criteria 1/2/3, all three: rows in <prefix>_clusters.csv with
branch=="vector" AND area_filter_result=="above_max" AND member_count>=2. Within this population
has_ivf_twin is always False by construction: interior_visual_frame applies the same area filter
when constructing its own candidates, so an above_max cluster can never have a primitive_ids-
identical IVF candidate. Not filtered separately -- asserted as a sanity check, and the run stops
loudly (AssertionError) if the assumption is violated on real data rather than silently reporting
a number built on top of a false premise.

Criterion 3 (v4, B3 -- restricted to this exact stratum, not the full missing-twin population):
within the target population, how many rows have text_filter_result=="has_text" (area is the only
failing filter -- compatible with "color re-partition might rescue this cluster") vs "no_text"
(fails both filters independently of area, color re-partition cannot rescue it since text-
containment does not depend on how members are grouped by color).

Criteria 1/2, (iii) as redefined in v4 (B2, not a raw sub-cluster count): for each target-
population cluster_id, per partition axis (subcluster_fill, subcluster_stroke -- kept separate,
they are two independent re-partitions of the same members over two different color fields, not
one joint partition), count how many of its subclusters in <prefix>_subclusters.csv satisfy BOTH
recalculated IVF filters (area_filter_result=="in_range" AND text_filter_result=="has_text"). A
cluster with >=1 such subcluster on either axis is reported as "supported": color re-partition
produced at least one sub-region that would independently qualify as interior_visual_frame.

Not a producer, not wired anywhere, no persistence beyond stdout, no PDF/pdfplumber/fitz
dependency.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def summarize(clusters_path: Path, subclusters_path: Path) -> dict[str, Any]:
    clusters = _read_csv(clusters_path)
    subclusters = _read_csv(subclusters_path)

    target = [
        row
        for row in clusters
        if row["branch"] == "vector"
        and row["area_filter_result"] == "above_max"
        and int(row["member_count"]) >= 2
    ]

    twin_violations = [row for row in target if row["has_ivf_twin"] != "False"]
    if twin_violations:
        raise AssertionError(
            f"{len(twin_violations)} above_max vector cluster(s) with member_count>=2 report "
            "has_ivf_twin != False in "
            f"{clusters_path} -- the 'above_max implies no twin' assumption this script relies "
            "on is violated on this manual's real data, inspect those rows before trusting "
            "anything else in this report"
        )

    has_text = sum(1 for row in target if row["text_filter_result"] == "has_text")
    no_text = sum(1 for row in target if row["text_filter_result"] == "no_text")
    other_text = len(target) - has_text - no_text  # n/a, should be 0 in this stratum

    # Chiave (page_index, cluster_id, role): cluster_id da solo NON e' univoco nel manuale --
    # primitive_id (quindi cluster_id, il primo primitive_id del cluster) riparte da p0001 a ogni
    # pagina (primitive_normalizer.py:141, _primitive_id per-pagina). Senza page_index nella
    # chiave, cluster con lo stesso cluster_id su pagine diverse si fondono nello stesso bucket
    # -- bug trovato per ispezione diretta dall'utente (Dag pag. 24/113/361, stesso
    # "primitive:drawing:drawing:p0003"), non dallo script.
    sub_by_parent_axis: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in subclusters:
        sub_by_parent_axis[(row["page_index"], row["cluster_id"], row["role"])].append(row)

    supported_fill = 0
    supported_stroke = 0
    supported_either = 0
    passing_subcluster_examples: list[dict[str, str]] = []
    for row in target:
        pidx = row["page_index"]
        cid = row["cluster_id"]
        fill_subs = sub_by_parent_axis.get((pidx, cid, "subcluster_fill"), [])
        stroke_subs = sub_by_parent_axis.get((pidx, cid, "subcluster_stroke"), [])

        def _passes(sub: dict[str, str]) -> bool:
            return (
                sub["area_filter_result"] == "in_range" and sub["text_filter_result"] == "has_text"
            )

        fill_passing = [s for s in fill_subs if _passes(s)]
        stroke_passing = [s for s in stroke_subs if _passes(s)]
        if fill_passing:
            supported_fill += 1
            passing_subcluster_examples.append(fill_passing[0])
        if stroke_passing:
            supported_stroke += 1
            passing_subcluster_examples.append(stroke_passing[0])
        if fill_passing or stroke_passing:
            supported_either += 1

    return {
        "target_population_count": len(target),
        "criterion_3_has_text": has_text,
        "criterion_3_no_text": no_text,
        "criterion_3_other_should_be_zero": other_text,
        "criteria_1_2_supported_by_fill_partition": supported_fill,
        "criteria_1_2_supported_by_stroke_partition": supported_stroke,
        "criteria_1_2_supported_by_either_partition": supported_either,
        "example_passing_subcluster_bboxes": [
            {
                "page_index": ex["page_index"],
                "role": ex["role"],
                "bbox": [ex["bbox_x0"], ex["bbox_y0"], ex["bbox_x1"], ex["bbox_y1"]],
            }
            for ex in passing_subcluster_examples[:5]
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "prefix",
        type=Path,
        nargs="+",
        help="one or more <prefix> such that <prefix>_clusters.csv and <prefix>_subclusters.csv "
        "both exist (same prefix given to scan_embedded_visual_interior_visual_frame_twin_diagnostics.py)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report: dict[str, Any] = {}
    for prefix in args.prefix:
        clusters_path = prefix.with_name(prefix.name + "_clusters.csv")
        subclusters_path = prefix.with_name(prefix.name + "_subclusters.csv")
        report[prefix.name] = summarize(clusters_path, subclusters_path)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
