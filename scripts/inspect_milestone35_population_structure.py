"""Cheap readouts on the CSVs already produced by
scan_embedded_visual_interior_visual_frame_twin_diagnostics.py, requested by Chat B round 4 (§D)
and round 5 (§D) before any manual visual labeling of the target-population clusters:

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

D4 (round 5, B1): (iii) as scoped in the proposal (Proposta_Milestone35_ClusteringColorDiagnostics_v6.md,
Scope) is a COUNT of passing subclusters per original cluster, not the boolean
"at least one passes" that summarize_milestone35_measures.py's 79/80 headline reads. The two
readings are not equivalent: the "stacked panels" hypothesis predicts >=2 passing subclusters per
cluster (N independently valid panels merged into one candidate); a single panel split into
body+border, or a form/UI fragment that happens to pass numerically (the inspected Dag p.24
counter-example), predicts exactly 1. This computes, per target cluster and per axis
(fill/stroke, kept separate -- they are independent partitions, not summed), the count of
subclusters passing BOTH recalculated IVF filters, and reports the distribution across the target
population per manual (0 / 1 / 2 / 3+), using max(fill_count, stroke_count) per cluster as the
headline bucket (the more favorable of the two axes to the hypothesis).

D5 (round 5, B2): the four pages that originated this milestone (Lan p.37/114/119/131, 1-based;
page_index 36/113/118/130, 0-based) never had their own numbers reported once the milestone moved
to the whole-manual measures. In particular p.119 (page_index 118) is the "zebra" pattern
Proposta_Milestone35_ClusteringColorDiagnostics_v6.md §Scope assigns to (iv) explicitly ("quanti
sotto-cluster color-partizionati rientrerebbero in tutti i filtri IVF, cioe' quanti candidati spuri
produrrebbe un futuro criterio di clustering per colore") -- never actually computed. This prints,
for any page_index passed via --highlight-pages, the full target-cluster row plus its D4 passing
counts, regardless of which manual's prefix is being processed (a page_index only matches within
its own manual's data, so passing 36,113,118,130 against non-Lan prefixes silently returns
nothing for pages that don't exist in that manual's target population).

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


def _count_bucket(count: int) -> str:
    if count >= 3:
        return "3+"
    return str(count)


def inspect(
    clusters_path: Path,
    subclusters_path: Path,
    *,
    highlight_pages: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    clusters = _read_csv(clusters_path)
    subclusters = _read_csv(subclusters_path)

    target = [
        row
        for row in clusters
        if row["branch"] == "vector"
        and row["area_filter_result"] == "above_max"
        and int(row["member_count"]) >= 2
    ]

    # Chiave (page_index, cluster_id, role): cluster_id da solo NON e' univoco nel manuale --
    # primitive_id (quindi cluster_id, il primo primitive_id del cluster) riparte da p0001 a ogni
    # pagina (primitive_normalizer.py:141, _primitive_id per-pagina). Senza page_index nella
    # chiave, cluster con lo stesso cluster_id su pagine diverse si fondono nello stesso bucket
    # -- bug trovato per ispezione diretta dall'utente (Dag pag. 24/113/361, stesso
    # "primitive:drawing:drawing:p0003"), non dallo script. Stessa correzione applicata a
    # summarize_milestone35_measures.py.
    sub_by_parent_axis: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in subclusters:
        sub_by_parent_axis[(row["page_index"], row["cluster_id"], row["role"])].append(row)

    # D1: axis redundancy. D4: passing-subcluster COUNT per axis (not just boolean "any pass").
    identical_nonempty = 0
    fill_only = 0
    stroke_only = 0
    both_different = 0
    neither = 0
    negatives: list[dict[str, Any]] = []
    fill_count_histogram: Counter[str] = Counter()
    stroke_count_histogram: Counter[str] = Counter()
    combined_max_histogram: Counter[str] = Counter()
    highlighted: list[dict[str, Any]] = []

    for row in target:
        pidx = row["page_index"]
        cid = row["cluster_id"]
        fill_subs = sub_by_parent_axis.get((pidx, cid, "subcluster_fill"), [])
        stroke_subs = sub_by_parent_axis.get((pidx, cid, "subcluster_stroke"), [])
        fill_passing = [s for s in fill_subs if _passes(s)]
        stroke_passing = [s for s in stroke_subs if _passes(s)]
        fill_pass_bboxes = frozenset(_bbox_key(s) for s in fill_passing)
        stroke_pass_bboxes = frozenset(_bbox_key(s) for s in stroke_passing)

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

        fill_count = len(fill_passing)
        stroke_count = len(stroke_passing)
        combined_max = max(fill_count, stroke_count)
        fill_count_histogram[_count_bucket(fill_count)] += 1
        stroke_count_histogram[_count_bucket(stroke_count)] += 1
        combined_max_histogram[_count_bucket(combined_max)] += 1

        if pidx in highlight_pages:
            highlighted.append(
                {
                    "page_index": pidx,
                    "cluster_id": cid,
                    "member_count": row["member_count"],
                    "page_area_ratio": row["page_area_ratio"],
                    "contained_text_count": row["contained_text_count"],
                    "fill_passing_subcluster_count": fill_count,
                    "stroke_passing_subcluster_count": stroke_count,
                    "bbox": [row["bbox_x0"], row["bbox_y0"], row["bbox_x1"], row["bbox_y1"]],
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
        "d4_passing_subcluster_count_distribution": {
            "fill_axis": dict(sorted(fill_count_histogram.items())),
            "stroke_axis": dict(sorted(stroke_count_histogram.items())),
            "max_of_both_axes_headline": dict(sorted(combined_max_histogram.items())),
        },
        "d5_highlighted_pages": highlighted,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "prefix",
        type=Path,
        nargs="+",
        help="same <prefix> given to scan_embedded_visual_interior_visual_frame_twin_diagnostics.py",
    )
    parser.add_argument(
        "--highlight-pages",
        type=str,
        default="",
        help="comma-separated page_index values (0-based) to report in full regardless of "
        "prefix -- e.g. the 4 Lan origin pages: 36,113,118,130 (1-based 37,114,119,131). "
        "Silently empty for prefixes that do not have a target cluster on those pages.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    highlight_pages = frozenset(p.strip() for p in args.highlight_pages.split(",") if p.strip())
    report: dict[str, Any] = {}
    for prefix in args.prefix:
        clusters_path = prefix.with_name(prefix.name + "_clusters.csv")
        subclusters_path = prefix.with_name(prefix.name + "_subclusters.csv")
        report[prefix.name] = inspect(
            clusters_path, subclusters_path, highlight_pages=highlight_pages
        )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
