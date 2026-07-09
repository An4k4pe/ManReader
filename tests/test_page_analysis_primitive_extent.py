from __future__ import annotations

import unittest
from dataclasses import replace
from typing import cast

from geometry_model import PageGeometry
from page_analysis_model import PAGE_ANALYSIS_SCHEMA_VERSION, PageAnalysis
from page_analysis_primitive_extent import (
    PRIMITIVE_EXTENT_CONFIGURATION_ID,
    PRIMITIVE_EXTENT_PRODUCER_NAME,
    PRIMITIVE_EXTENT_PRODUCER_VERSION,
    PRIMITIVE_EXTENT_REGION_ID,
    PRIMITIVE_EXTENT_STRUCTURAL_KIND,
    ROOT_CONTAINS_EXTENT_RELATION_ID,
    build_primitive_extent_page_analysis,
)
from page_analysis_root import ROOT_REGION_ID, ROOT_STRUCTURAL_KIND
from primitive_model import (
    DrawingPrimitive,
    ImageOccurrencePrimitive,
    NormalizedPrimitivePage,
    TextPrimitive,
)


class PageAnalysisPrimitiveExtentTest(unittest.TestCase):
    def test_build_primitive_extent_page_analysis_returns_page_analysis(self) -> None:
        analysis = build_primitive_extent_page_analysis(
            _primitive_page(),
            generation_id="generation-1",
        )

        self.assertIsInstance(analysis, PageAnalysis)

    def test_schema_generation_id_and_provenance_are_preserved(self) -> None:
        primitive_page = _primitive_page(page_id="page-custom")

        analysis = build_primitive_extent_page_analysis(
            primitive_page,
            generation_id="generation-custom",
        )

        self.assertEqual(analysis.schema_version, PAGE_ANALYSIS_SCHEMA_VERSION)
        self.assertEqual(analysis.generation_id, "generation-custom")
        self.assertEqual(analysis.page_id, "page-custom")
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

    def test_uses_primitive_extent_producer_identity(self) -> None:
        analysis = build_primitive_extent_page_analysis(
            _primitive_page(),
            generation_id="generation-1",
        )

        self.assertEqual(analysis.provenance.producer_name, PRIMITIVE_EXTENT_PRODUCER_NAME)
        self.assertEqual(
            analysis.provenance.producer_version,
            PRIMITIVE_EXTENT_PRODUCER_VERSION,
        )
        self.assertEqual(
            analysis.provenance.configuration_id,
            PRIMITIVE_EXTENT_CONFIGURATION_ID,
        )

    def test_root_and_extent_region_order_and_identity(self) -> None:
        primitive_page = _primitive_page(width=123.0, height=456.0)

        analysis = build_primitive_extent_page_analysis(
            primitive_page,
            generation_id="generation-1",
        )

        self.assertEqual(len(analysis.regions), 2)
        root = analysis.regions[0]
        extent = analysis.regions[1]
        self.assertEqual(root.region_id, ROOT_REGION_ID)
        self.assertEqual(root.structural_kind, ROOT_STRUCTURAL_KIND)
        self.assertEqual(root.bbox, (0.0, 0.0, 123.0, 456.0))
        self.assertEqual(extent.region_id, PRIMITIVE_EXTENT_REGION_ID)
        self.assertEqual(extent.structural_kind, PRIMITIVE_EXTENT_STRUCTURAL_KIND)

    def test_extent_bbox_is_exact_union_of_primitives(self) -> None:
        analysis = build_primitive_extent_page_analysis(
            _primitive_page(),
            generation_id="generation-1",
        )

        self.assertEqual(analysis.regions[1].bbox, (1.5, 1.25, 90.125, 95.875))

    def test_extent_primitive_ids_are_in_channel_order(self) -> None:
        analysis = build_primitive_extent_page_analysis(
            _primitive_page(),
            generation_id="generation-1",
        )

        self.assertEqual(
            analysis.regions[1].primitive_ids,
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

        analysis = build_primitive_extent_page_analysis(
            primitive_page,
            generation_id="generation-1",
        )

        self.assertEqual(analysis.regions[1].primitive_ids, expected_ids)
        self.assertEqual(len(analysis.regions[1].primitive_ids), len(expected_ids))

    def test_creates_exactly_one_contains_relation_from_root_to_extent(self) -> None:
        analysis = build_primitive_extent_page_analysis(
            _primitive_page(),
            generation_id="generation-1",
        )

        self.assertEqual(len(analysis.relations), 1)
        relation = analysis.relations[0]
        self.assertEqual(relation.relation_id, ROOT_CONTAINS_EXTENT_RELATION_ID)
        self.assertEqual(relation.relation_kind, "layout.contains")
        self.assertEqual(relation.source_region_id, ROOT_REGION_ID)
        self.assertEqual(relation.target_region_id, PRIMITIVE_EXTENT_REGION_ID)

    def test_page_without_primitives_produces_only_root_and_no_relations(self) -> None:
        analysis = build_primitive_extent_page_analysis(
            _primitive_page(text_primitives=(), image_primitives=(), drawing_primitives=()),
            generation_id="generation-1",
        )

        self.assertEqual(len(analysis.regions), 1)
        self.assertEqual(analysis.regions[0].region_id, ROOT_REGION_ID)
        self.assertEqual(analysis.relations, ())
        self.assertEqual(analysis.provenance.producer_name, PRIMITIVE_EXTENT_PRODUCER_NAME)

    def test_single_primitive_produces_identical_extent_bbox(self) -> None:
        primitive = TextPrimitive(
            primitive_id="single-text",
            bbox=(10.25, 20.5, 30.75, 40.125),
            text="Single",
            source_observation_id="text-observation-single",
        )

        analysis = build_primitive_extent_page_analysis(
            _primitive_page(
                text_primitives=(primitive,), image_primitives=(), drawing_primitives=()
            ),
            generation_id="generation-1",
        )

        self.assertEqual(analysis.regions[1].bbox, primitive.bbox)
        self.assertEqual(analysis.regions[1].primitive_ids, ("single-text",))

    def test_float_coordinates_are_preserved_without_rounding(self) -> None:
        primitive = DrawingPrimitive(
            primitive_id="precise-drawing",
            bbox=(0.123456789, 1.987654321, 99.111111111, 150.999999999),
            source_observation_id="drawing-observation-precise",
        )

        analysis = build_primitive_extent_page_analysis(
            _primitive_page(
                text_primitives=(), image_primitives=(), drawing_primitives=(primitive,)
            ),
            generation_id="generation-1",
        )

        self.assertEqual(analysis.regions[1].bbox, primitive.bbox)

    def test_partially_out_of_bounds_primitives_are_clipped_to_page(self) -> None:
        primitives = (
            _text_primitive("inside", (10.0, 20.0, 30.0, 40.0)),
            _text_primitive("partial-left", (-5.0, 30.0, 5.0, 50.0)),
            _text_primitive("partial-top", (15.0, -5.0, 35.0, 5.0)),
            _text_primitive("partial-right", (95.0, 60.0, 105.0, 80.0)),
            _text_primitive("partial-bottom", (45.0, 195.0, 55.0, 205.0)),
        )

        analysis = build_primitive_extent_page_analysis(
            _primitive_page(text_primitives=primitives, image_primitives=(), drawing_primitives=()),
            generation_id="generation-1",
        )

        extent = analysis.regions[1]
        self.assertEqual(extent.bbox, (0.0, 0.0, 100.0, 200.0))
        self.assertEqual(
            extent.primitive_ids,
            ("inside", "partial-left", "partial-top", "partial-right", "partial-bottom"),
        )

    def test_completely_out_of_bounds_primitives_are_excluded_from_extent(self) -> None:
        primitives = (
            _text_primitive("inside", (10.0, 20.0, 30.0, 40.0)),
            _text_primitive("outside-left", (-20.0, 10.0, -5.0, 20.0)),
            _text_primitive("outside-right", (105.0, 10.0, 120.0, 20.0)),
            _text_primitive("outside-top", (10.0, -20.0, 20.0, -5.0)),
            _text_primitive("outside-bottom", (10.0, 205.0, 20.0, 220.0)),
        )

        analysis = build_primitive_extent_page_analysis(
            _primitive_page(text_primitives=primitives, image_primitives=(), drawing_primitives=()),
            generation_id="generation-1",
        )

        root = analysis.regions[0]
        extent = analysis.regions[1]
        self.assertEqual(
            root.primitive_ids,
            (
                "inside",
                "outside-left",
                "outside-right",
                "outside-top",
                "outside-bottom",
            ),
        )
        self.assertEqual(extent.bbox, (10.0, 20.0, 30.0, 40.0))
        self.assertEqual(extent.primitive_ids, ("inside",))

    def test_mixed_visible_and_invisible_primitives_preserve_visible_id_order(self) -> None:
        text_primitives = (
            _text_primitive("text-visible", (10.0, 10.0, 20.0, 20.0)),
            _text_primitive("text-invisible", (-30.0, 10.0, -20.0, 20.0)),
            _text_primitive("text-partial", (90.0, 15.0, 110.0, 25.0)),
        )
        image_primitives = (
            ImageOccurrencePrimitive(
                primitive_id="image-partial",
                bbox=(5.5, -2.5, 15.25, 8.75),
                source_observation_id="image-observation-partial",
            ),
        )
        drawing_primitives = (
            DrawingPrimitive(
                primitive_id="drawing-visible",
                bbox=(50.25, 150.5, 60.75, 160.875),
                source_observation_id="drawing-observation-visible",
            ),
            DrawingPrimitive(
                primitive_id="drawing-invisible",
                bbox=(0.0, 200.0, 10.0, 210.0),
                source_observation_id="drawing-observation-invisible",
            ),
        )

        analysis = build_primitive_extent_page_analysis(
            _primitive_page(
                text_primitives=text_primitives,
                image_primitives=image_primitives,
                drawing_primitives=drawing_primitives,
            ),
            generation_id="generation-1",
        )

        root = analysis.regions[0]
        extent = analysis.regions[1]
        self.assertEqual(
            root.primitive_ids,
            (
                "text-visible",
                "text-invisible",
                "text-partial",
                "image-partial",
                "drawing-visible",
                "drawing-invisible",
            ),
        )
        self.assertEqual(
            extent.primitive_ids,
            ("text-visible", "text-partial", "image-partial", "drawing-visible"),
        )
        self.assertEqual(extent.bbox, (5.5, 0.0, 100.0, 160.875))

    def test_only_completely_invisible_primitives_produce_only_root(self) -> None:
        primitives = (
            _text_primitive("outside-left", (-20.0, 10.0, -5.0, 20.0)),
            _text_primitive("outside-right", (100.0, 10.0, 120.0, 20.0)),
            _text_primitive("outside-top", (10.0, -20.0, 20.0, 0.0)),
            _text_primitive("outside-bottom", (10.0, 200.0, 20.0, 220.0)),
        )

        analysis = build_primitive_extent_page_analysis(
            _primitive_page(text_primitives=primitives, image_primitives=(), drawing_primitives=()),
            generation_id="generation-1",
        )

        self.assertEqual(len(analysis.regions), 1)
        self.assertEqual(
            analysis.regions[0].primitive_ids,
            tuple(primitive.primitive_id for primitive in primitives),
        )
        self.assertEqual(analysis.relations, ())

    def test_bbox_touching_page_border_without_area_is_excluded(self) -> None:
        primitives = (
            _text_primitive("touches-right-border", (100.0, 10.0, 120.0, 20.0)),
            _text_primitive("visible", (25.0, 25.0, 35.0, 35.0)),
        )

        analysis = build_primitive_extent_page_analysis(
            _primitive_page(text_primitives=primitives, image_primitives=(), drawing_primitives=()),
            generation_id="generation-1",
        )

        self.assertEqual(analysis.regions[1].bbox, (25.0, 25.0, 35.0, 35.0))
        self.assertEqual(analysis.regions[1].primitive_ids, ("visible",))

    def test_input_primitive_page_is_not_modified(self) -> None:
        primitive_page = _primitive_page()
        equivalent = _primitive_page()

        build_primitive_extent_page_analysis(primitive_page, generation_id="generation-1")

        self.assertEqual(primitive_page, equivalent)

    def test_result_is_deterministic(self) -> None:
        primitive_page = _primitive_page()

        first = build_primitive_extent_page_analysis(primitive_page, generation_id="generation-1")
        second = build_primitive_extent_page_analysis(primitive_page, generation_id="generation-1")

        self.assertEqual(first, second)

    def test_different_generation_ids_change_only_generation_id(self) -> None:
        primitive_page = _primitive_page()

        first = build_primitive_extent_page_analysis(primitive_page, generation_id="generation-1")
        second = build_primitive_extent_page_analysis(primitive_page, generation_id="generation-2")

        self.assertNotEqual(first, second)
        self.assertEqual(replace(first, generation_id="generation-2"), second)

    def test_invalid_primitive_page_type_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "primitive_page"):
            build_primitive_extent_page_analysis(
                cast(NormalizedPrimitivePage, object()),
                generation_id="generation-1",
            )

    def test_non_string_generation_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "generation_id"):
            build_primitive_extent_page_analysis(
                _primitive_page(),
                generation_id=cast(str, 123),
            )

    def test_empty_generation_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "generation_id"):
            build_primitive_extent_page_analysis(_primitive_page(), generation_id="")


def _text_primitive(primitive_id: str, bbox: tuple[float, float, float, float]) -> TextPrimitive:
    return TextPrimitive(
        primitive_id=primitive_id,
        bbox=bbox,
        text=primitive_id,
        source_observation_id=f"observation-{primitive_id}",
    )


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
                bbox=(10.5, 20.25, 30.75, 40.5),
                text="Text 1",
                source_observation_id="text-observation-1",
            ),
            TextPrimitive(
                primitive_id="text-2",
                bbox=(1.5, 60.25, 12.25, 70.5),
                text="Text 2",
                source_observation_id="text-observation-2",
            ),
        )
        if text_primitives is None
        else text_primitives,
        image_primitives=(
            ImageOccurrencePrimitive(
                primitive_id="image-1",
                bbox=(50.5, 1.25, 90.125, 35.75),
                source_observation_id="image-observation-1",
            ),
        )
        if image_primitives is None
        else image_primitives,
        drawing_primitives=(
            DrawingPrimitive(
                primitive_id="drawing-1",
                bbox=(5.5, 80.25, 15.75, 90.5),
                source_observation_id="drawing-observation-1",
            ),
            DrawingPrimitive(
                primitive_id="drawing-2",
                bbox=(20.25, 85.5, 45.75, 95.875),
                source_observation_id="drawing-observation-2",
            ),
        )
        if drawing_primitives is None
        else drawing_primitives,
    )


if __name__ == "__main__":
    unittest.main()
