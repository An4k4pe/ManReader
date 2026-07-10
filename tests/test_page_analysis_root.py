from __future__ import annotations

import unittest
from dataclasses import replace
from typing import cast

from geometry_model import PageGeometry
from page_analysis_model import PAGE_ANALYSIS_SCHEMA_VERSION, PageAnalysis
from page_analysis_root import (
    ROOT_PAGE_ANALYSIS_CONFIGURATION_ID,
    ROOT_PAGE_ANALYSIS_PRODUCER_NAME,
    ROOT_PAGE_ANALYSIS_PRODUCER_VERSION,
    ROOT_REGION_ID,
    ROOT_STRUCTURAL_KIND,
    build_root_page_analysis,
)
from primitive_model import (
    DrawingPrimitive,
    ImageOccurrencePrimitive,
    NormalizedPrimitivePage,
    TextPrimitive,
)


class PageAnalysisRootTest(unittest.TestCase):
    def test_build_root_page_analysis_returns_page_analysis(self) -> None:
        primitive_page = _primitive_page()

        analysis = build_root_page_analysis(
            primitive_page,
            generation_id="generation-1",
        )

        self.assertIsInstance(analysis, PageAnalysis)

    def test_schema_generation_id_and_page_id_are_preserved(self) -> None:
        primitive_page = _primitive_page(page_id="page-custom")

        analysis = build_root_page_analysis(
            primitive_page,
            generation_id="generation-custom",
        )

        self.assertEqual(analysis.schema_version, PAGE_ANALYSIS_SCHEMA_VERSION)
        self.assertEqual(analysis.generation_id, "generation-custom")
        self.assertEqual(analysis.page_id, "page-custom")

    def test_provenance_matches_primitive_page_and_root_producer(self) -> None:
        primitive_page = _primitive_page()

        analysis = build_root_page_analysis(
            primitive_page,
            generation_id="generation-1",
        )

        self.assertEqual(analysis.provenance.source_id, primitive_page.source_id)
        self.assertEqual(
            analysis.provenance.source_capture_id,
            primitive_page.source_capture_id,
        )
        self.assertEqual(analysis.provenance.source_page_id, primitive_page.page_id)
        self.assertEqual(
            analysis.provenance.source_primitive_schema_version,
            primitive_page.schema_version,
        )
        self.assertEqual(
            analysis.provenance.producer_name,
            ROOT_PAGE_ANALYSIS_PRODUCER_NAME,
        )
        self.assertEqual(
            analysis.provenance.producer_version,
            ROOT_PAGE_ANALYSIS_PRODUCER_VERSION,
        )
        self.assertEqual(
            analysis.provenance.configuration_id,
            ROOT_PAGE_ANALYSIS_CONFIGURATION_ID,
        )

    def test_builds_exactly_one_page_root_region(self) -> None:
        primitive_page = _primitive_page(width=123.0, height=456.0)

        analysis = build_root_page_analysis(
            primitive_page,
            generation_id="generation-1",
        )

        self.assertEqual(len(analysis.regions), 1)
        root = analysis.regions[0]
        self.assertEqual(root.region_id, ROOT_REGION_ID)
        self.assertEqual(root.page_id, primitive_page.page_id)
        self.assertEqual(root.structural_kind, ROOT_STRUCTURAL_KIND)
        self.assertEqual(root.bbox, (0.0, 0.0, 123.0, 456.0))
        self.assertEqual(analysis.relations, ())
        self.assertEqual(analysis.candidates, ())

    def test_primitive_ids_are_concatenated_in_channel_order(self) -> None:
        primitive_page = _primitive_page()

        analysis = build_root_page_analysis(
            primitive_page,
            generation_id="generation-1",
        )

        self.assertEqual(
            analysis.regions[0].primitive_ids,
            (
                "text-1",
                "text-2",
                "image-1",
                "drawing-1",
                "drawing-2",
            ),
        )

    def test_all_primitive_ids_are_present_and_no_ids_are_invented(self) -> None:
        primitive_page = _primitive_page()
        expected_ids = (
            tuple(primitive.primitive_id for primitive in primitive_page.text_primitives)
            + tuple(primitive.primitive_id for primitive in primitive_page.image_primitives)
            + tuple(primitive.primitive_id for primitive in primitive_page.drawing_primitives)
        )

        analysis = build_root_page_analysis(
            primitive_page,
            generation_id="generation-1",
        )

        self.assertEqual(analysis.regions[0].primitive_ids, expected_ids)
        self.assertEqual(len(analysis.regions[0].primitive_ids), len(expected_ids))

    def test_page_without_primitives_is_valid(self) -> None:
        primitive_page = _primitive_page(
            text_primitives=(),
            image_primitives=(),
            drawing_primitives=(),
        )

        analysis = build_root_page_analysis(
            primitive_page,
            generation_id="generation-1",
        )

        self.assertEqual(len(analysis.regions), 1)
        self.assertEqual(analysis.regions[0].primitive_ids, ())
        self.assertEqual(analysis.relations, ())
        self.assertEqual(analysis.candidates, ())

    def test_input_primitive_page_is_not_modified(self) -> None:
        primitive_page = _primitive_page()
        equivalent = _primitive_page()

        build_root_page_analysis(primitive_page, generation_id="generation-1")

        self.assertEqual(primitive_page, equivalent)

    def test_result_is_deterministic(self) -> None:
        primitive_page = _primitive_page()

        first = build_root_page_analysis(primitive_page, generation_id="generation-1")
        second = build_root_page_analysis(primitive_page, generation_id="generation-1")

        self.assertEqual(first, second)

    def test_different_generation_ids_change_only_generation_id(self) -> None:
        primitive_page = _primitive_page()

        first = build_root_page_analysis(primitive_page, generation_id="generation-1")
        second = build_root_page_analysis(primitive_page, generation_id="generation-2")

        self.assertNotEqual(first, second)
        self.assertEqual(replace(first, generation_id="generation-2"), second)

    def test_invalid_primitive_page_type_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "primitive_page"):
            build_root_page_analysis(
                cast(NormalizedPrimitivePage, object()),
                generation_id="generation-1",
            )

    def test_non_string_generation_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "generation_id"):
            build_root_page_analysis(
                _primitive_page(),
                generation_id=cast(str, 123),
            )

    def test_empty_generation_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "generation_id"):
            build_root_page_analysis(_primitive_page(), generation_id="")


def _primitive_page(
    *,
    page_id: str = "page-1",
    width: float = 100.0,
    height: float = 200.0,
    text_primitives: tuple[TextPrimitive, ...] | None = None,
    image_primitives: tuple[ImageOccurrencePrimitive, ...] | None = None,
    drawing_primitives: tuple[DrawingPrimitive, ...] | None = None,
) -> NormalizedPrimitivePage:
    return NormalizedPrimitivePage(
        schema_version="1",
        source_capture_id="capture-1",
        source_id="source-1",
        page_id=page_id,
        page_index=0,
        page_geometry=PageGeometry(
            width=width,
            height=height,
            unit="pt",
            coordinate_system="top_left_y_down",
        ),
        capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
        text_primitives=(
            TextPrimitive(
                primitive_id="text-1",
                bbox=(1.0, 1.0, 10.0, 10.0),
                text="Text 1",
                source_observation_id="text-observation-1",
            ),
            TextPrimitive(
                primitive_id="text-2",
                bbox=(11.0, 1.0, 20.0, 10.0),
                text="Text 2",
                source_observation_id="text-observation-2",
            ),
        )
        if text_primitives is None
        else text_primitives,
        image_primitives=(
            ImageOccurrencePrimitive(
                primitive_id="image-1",
                bbox=(1.0, 20.0, 10.0, 30.0),
                source_observation_id="image-observation-1",
            ),
        )
        if image_primitives is None
        else image_primitives,
        drawing_primitives=(
            DrawingPrimitive(
                primitive_id="drawing-1",
                bbox=(1.0, 40.0, 10.0, 50.0),
                source_observation_id="drawing-observation-1",
            ),
            DrawingPrimitive(
                primitive_id="drawing-2",
                bbox=(11.0, 40.0, 20.0, 50.0),
                source_observation_id="drawing-observation-2",
            ),
        )
        if drawing_primitives is None
        else drawing_primitives,
    )


if __name__ == "__main__":
    unittest.main()
