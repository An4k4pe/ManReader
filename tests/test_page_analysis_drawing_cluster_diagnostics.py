from __future__ import annotations

import unittest
from typing import Any, cast

from geometry_model import PageGeometry
from page_analysis_drawing_cluster_diagnostics import dump_drawing_cluster_diagnostics
from primitive_model import DrawingPrimitive, NormalizedPrimitivePage


def _drawing(
    primitive_id: str,
    bbox: tuple[float, float, float, float],
) -> DrawingPrimitive:
    return DrawingPrimitive(
        primitive_id=primitive_id,
        bbox=bbox,
        source_observation_id=f"obs:{primitive_id}",
    )


def _page(*, drawings: tuple[DrawingPrimitive, ...] = ()) -> NormalizedPrimitivePage:
    return NormalizedPrimitivePage(
        schema_version="1",
        source_capture_id="capture-1",
        source_id="source-1",
        page_id="page-1",
        page_index=0,
        page_geometry=PageGeometry(
            width=100.0,
            height=200.0,
            unit="pt",
            coordinate_system="top_left_y_down",
        ),
        capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
        text_primitives=(),
        image_primitives=(),
        drawing_primitives=drawings,
    )


def _cluster_with(result: dict[str, object], primitive_id: str) -> dict[str, object]:
    return next(
        cast(dict[str, object], cluster)
        for cluster in cast(list[object], result["clusters"])
        if primitive_id in cast(list[str], cast(dict[str, object], cluster)["drawing_primitive_ids"])
    )


class DumpDrawingClusterDiagnosticsTest(unittest.TestCase):
    def test_rejects_wrong_page_type_and_empty_generation_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "primitive_page"):
            dump_drawing_cluster_diagnostics(cast(Any, object()), generation_id="gen-1")
        with self.assertRaisesRegex(ValueError, "generation_id"):
            dump_drawing_cluster_diagnostics(_page(), generation_id="")

    def test_merges_drawings_within_default_margin(self) -> None:
        page = _page(
            drawings=(
                _drawing("a", (10.0, 10.0, 20.0, 20.0)),
                _drawing("b", (24.0, 10.0, 34.0, 20.0)),
            )
        )

        result = dump_drawing_cluster_diagnostics(page, generation_id="gen-1")

        cluster = _cluster_with(result, "a")
        self.assertEqual(cluster["drawing_primitive_ids"], ["a", "b"])
        self.assertEqual(cluster["primitive_count"], 2)
        self.assertIsNone(cluster["excluded_reason"])
        self.assertAlmostEqual(cast(float, cluster["dispersion_ratio"]), 200.0 / 240.0)

    def test_keeps_distant_drawings_in_separate_clusters(self) -> None:
        page = _page(
            drawings=(
                _drawing("a", (10.0, 10.0, 20.0, 20.0)),
                _drawing("c", (80.0, 10.0, 90.0, 20.0)),
            )
        )

        result = dump_drawing_cluster_diagnostics(page, generation_id="gen-1")

        self.assertEqual(len(cast(list[object], result["clusters"])), 2)
        self.assertEqual(_cluster_with(result, "a")["drawing_primitive_ids"], ["a"])
        self.assertEqual(_cluster_with(result, "c")["drawing_primitive_ids"], ["c"])

    def test_excludes_tiny_drawing_without_merging(self) -> None:
        page = _page(
            drawings=(
                _drawing("tiny", (10.0, 10.0, 11.0, 11.0)),
                _drawing("d", (12.0, 10.0, 22.0, 20.0)),
            )
        )

        result = dump_drawing_cluster_diagnostics(page, generation_id="gen-1")

        tiny_cluster = _cluster_with(result, "tiny")
        self.assertEqual(tiny_cluster["excluded_reason"], "tiny")
        self.assertEqual(tiny_cluster["drawing_primitive_ids"], ["tiny"])

    def test_excludes_border_like_drawing(self) -> None:
        page = _page(drawings=(_drawing("border", (5.0, 50.0, 95.0, 55.0)),))

        result = dump_drawing_cluster_diagnostics(page, generation_id="gen-1")

        cluster = _cluster_with(result, "border")
        self.assertEqual(cluster["excluded_reason"], "border_like")

    def test_completely_invisible_drawing_has_null_geometry(self) -> None:
        page = _page(drawings=(_drawing("outside", (110.0, 0.0, 120.0, 20.0)),))

        result = dump_drawing_cluster_diagnostics(page, generation_id="gen-1")

        cluster = _cluster_with(result, "outside")
        self.assertIsNone(cluster["bbox"])
        self.assertIsNone(cluster["dispersion_ratio"])
        self.assertFalse(cluster["is_residual_interior_visual"])

    def test_is_deterministic(self) -> None:
        page = _page(
            drawings=(
                _drawing("a", (10.0, 10.0, 20.0, 20.0)),
                _drawing("b", (24.0, 10.0, 34.0, 20.0)),
            )
        )

        first = dump_drawing_cluster_diagnostics(page, generation_id="gen-1")
        second = dump_drawing_cluster_diagnostics(page, generation_id="gen-1")

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
