"""Tests for validating PageAnalysis against NormalizedPrimitivePage."""

from __future__ import annotations

import unittest

from capture_model import DrawingCommand
from geometry_model import PageGeometry
from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    LayoutRegion,
    PageAnalysis,
    PageAnalysisProvenance,
)
from page_analysis_validate import validate_page_analysis_against_primitive_page
from primitive_model import (
    DrawingPrimitive,
    ImageOccurrencePrimitive,
    NormalizedPrimitivePage,
    TextPrimitive,
)


class PageAnalysisValidateTests(unittest.TestCase):
    def _geometry(self) -> PageGeometry:
        return PageGeometry(
            width=100.0,
            height=200.0,
            unit="pt",
            coordinate_system="top_left_y_down",
        )

    def _text_primitive(self, primitive_id: str = "text-1") -> TextPrimitive:
        return TextPrimitive(
            primitive_id=primitive_id,
            bbox=(10.0, 10.0, 20.0, 20.0),
            text="Text",
            source_observation_id=f"obs-{primitive_id}",
        )

    def _image_primitive(self, primitive_id: str = "image-1") -> ImageOccurrencePrimitive:
        return ImageOccurrencePrimitive(
            primitive_id=primitive_id,
            bbox=(30.0, 10.0, 40.0, 20.0),
            source_observation_id=f"obs-{primitive_id}",
        )

    def _drawing_primitive(self, primitive_id: str = "drawing-1") -> DrawingPrimitive:
        return DrawingPrimitive(
            primitive_id=primitive_id,
            bbox=(50.0, 10.0, 60.0, 20.0),
            source_observation_id=f"obs-{primitive_id}",
            commands=(
                DrawingCommand(
                    kind="line",
                    points=((50.0, 10.0), (60.0, 20.0)),
                    bbox=(50.0, 10.0, 60.0, 20.0),
                ),
            ),
        )

    def _primitive_page(
        self,
        *,
        page_id: str = "page-1",
        text_primitives: tuple[TextPrimitive, ...] = (),
        image_primitives: tuple[ImageOccurrencePrimitive, ...] = (),
        drawing_primitives: tuple[DrawingPrimitive, ...] = (),
    ) -> NormalizedPrimitivePage:
        return NormalizedPrimitivePage(
            schema_version="1.0",
            source_capture_id="capture-1",
            source_id="source-1",
            page_id=page_id,
            page_index=0,
            page_geometry=self._geometry(),
            capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
            text_primitives=text_primitives,
            image_primitives=image_primitives,
            drawing_primitives=drawing_primitives,
        )

    def _region(
        self,
        *,
        region_id: str = "region-1",
        page_id: str = "page-1",
        bbox: tuple[float, float, float, float] = (0.0, 0.0, 50.0, 50.0),
        primitive_ids: tuple[str, ...] = (),
    ) -> LayoutRegion:
        return LayoutRegion(
            region_id=region_id,
            page_id=page_id,
            bbox=bbox,
            structural_kind="layout.generic",
            primitive_ids=primitive_ids,
        )

    def _provenance(
        self,
        *,
        source_id: str = "source-1",
        source_capture_id: str = "capture-1",
        source_page_id: str = "page-1",
        source_primitive_schema_version: str = "1.0",
    ) -> PageAnalysisProvenance:
        return PageAnalysisProvenance(
            source_id=source_id,
            source_capture_id=source_capture_id,
            source_page_id=source_page_id,
            source_primitive_schema_version=source_primitive_schema_version,
            producer_name="region-graph",
            producer_version="0.1",
            configuration_id="config-default-v1",
        )

    def _analysis(
        self,
        *,
        page_id: str = "page-1",
        provenance: PageAnalysisProvenance | None = None,
        regions: tuple[LayoutRegion, ...] = (),
    ) -> PageAnalysis:
        return PageAnalysis(
            schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
            generation_id="generation-1",
            page_id=page_id,
            provenance=self._provenance() if provenance is None else provenance,
            regions=regions,
        )

    def test_wrong_analysis_type_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "analysis"):
            validate_page_analysis_against_primitive_page(
                object(),  # type: ignore[arg-type]
                self._primitive_page(),
            )

    def test_wrong_primitive_page_type_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "primitive_page"):
            validate_page_analysis_against_primitive_page(
                self._analysis(),
                object(),  # type: ignore[arg-type]
            )

    def test_matching_page_id_is_valid(self) -> None:
        result = validate_page_analysis_against_primitive_page(
            self._analysis(),
            self._primitive_page(),
        )

        self.assertIsNone(result)

    def test_different_page_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "page_id"):
            validate_page_analysis_against_primitive_page(
                self._analysis(page_id="page-1"),
                self._primitive_page(page_id="page-2"),
            )

    def test_coherent_provenance_is_valid(self) -> None:
        validate_page_analysis_against_primitive_page(self._analysis(), self._primitive_page())

    def test_different_provenance_source_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "source_id"):
            validate_page_analysis_against_primitive_page(
                self._analysis(provenance=self._provenance(source_id="other-source")),
                self._primitive_page(),
            )

    def test_different_provenance_source_capture_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "source_capture_id"):
            validate_page_analysis_against_primitive_page(
                self._analysis(provenance=self._provenance(source_capture_id="other-capture")),
                self._primitive_page(),
            )

    def test_different_provenance_source_page_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "source_page_id"):
            validate_page_analysis_against_primitive_page(
                self._analysis(provenance=self._provenance(source_page_id="other-page")),
                self._primitive_page(),
            )

    def test_different_provenance_source_primitive_schema_version_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "source_primitive_schema_version"):
            validate_page_analysis_against_primitive_page(
                self._analysis(
                    provenance=self._provenance(
                        source_primitive_schema_version="primitive-schema-2"
                    )
                ),
                self._primitive_page(),
            )

    def test_region_referencing_text_primitive_is_valid(self) -> None:
        validate_page_analysis_against_primitive_page(
            self._analysis(regions=(self._region(primitive_ids=("text-1",)),)),
            self._primitive_page(text_primitives=(self._text_primitive(),)),
        )

    def test_region_referencing_image_primitive_is_valid(self) -> None:
        validate_page_analysis_against_primitive_page(
            self._analysis(regions=(self._region(primitive_ids=("image-1",)),)),
            self._primitive_page(image_primitives=(self._image_primitive(),)),
        )

    def test_region_referencing_drawing_primitive_is_valid(self) -> None:
        validate_page_analysis_against_primitive_page(
            self._analysis(regions=(self._region(primitive_ids=("drawing-1",)),)),
            self._primitive_page(drawing_primitives=(self._drawing_primitive(),)),
        )

    def test_region_referencing_primitives_from_multiple_channels_is_valid(self) -> None:
        validate_page_analysis_against_primitive_page(
            self._analysis(
                regions=(self._region(primitive_ids=("text-1", "image-1", "drawing-1")),)
            ),
            self._primitive_page(
                text_primitives=(self._text_primitive(),),
                image_primitives=(self._image_primitive(),),
                drawing_primitives=(self._drawing_primitive(),),
            ),
        )

    def test_missing_primitive_id_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_page_analysis_against_primitive_page(
                self._analysis(regions=(self._region(primitive_ids=("missing-1",)),)),
                self._primitive_page(text_primitives=(self._text_primitive(),)),
            )

    def test_missing_primitive_error_identifies_region_and_primitive(self) -> None:
        with self.assertRaisesRegex(ValueError, "region-1.*missing-1"):
            validate_page_analysis_against_primitive_page(
                self._analysis(regions=(self._region(primitive_ids=("missing-1",)),)),
                self._primitive_page(text_primitives=(self._text_primitive(),)),
            )

    def test_region_without_primitives_is_valid(self) -> None:
        validate_page_analysis_against_primitive_page(
            self._analysis(regions=(self._region(primitive_ids=()),)),
            self._primitive_page(text_primitives=(self._text_primitive(),)),
        )

    def test_page_without_regions_is_valid(self) -> None:
        validate_page_analysis_against_primitive_page(
            self._analysis(regions=()),
            self._primitive_page(text_primitives=(self._text_primitive(),)),
        )

    def test_page_without_primitives_and_region_without_primitives_is_valid(self) -> None:
        validate_page_analysis_against_primitive_page(
            self._analysis(regions=(self._region(primitive_ids=()),)),
            self._primitive_page(),
        )

    def test_page_without_primitives_and_region_with_reference_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_page_analysis_against_primitive_page(
                self._analysis(regions=(self._region(primitive_ids=("text-1",)),)),
                self._primitive_page(),
            )

    def test_same_primitive_referenced_by_two_regions_is_valid(self) -> None:
        first = self._region(region_id="region-1", primitive_ids=("text-1",))
        second = self._region(region_id="region-2", primitive_ids=("text-1",))

        validate_page_analysis_against_primitive_page(
            self._analysis(regions=(first, second)),
            self._primitive_page(text_primitives=(self._text_primitive(),)),
        )

    def test_unreferenced_primitives_are_valid(self) -> None:
        validate_page_analysis_against_primitive_page(
            self._analysis(regions=(self._region(primitive_ids=("text-1",)),)),
            self._primitive_page(
                text_primitives=(self._text_primitive(), self._text_primitive("text-2")),
                image_primitives=(self._image_primitive(),),
                drawing_primitives=(self._drawing_primitive(),),
            ),
        )

    def test_bbox_completely_inside_page_is_valid(self) -> None:
        validate_page_analysis_against_primitive_page(
            self._analysis(regions=(self._region(bbox=(1.0, 2.0, 99.0, 199.0)),)),
            self._primitive_page(),
        )

    def test_bbox_matching_entire_page_is_valid(self) -> None:
        validate_page_analysis_against_primitive_page(
            self._analysis(regions=(self._region(bbox=(0.0, 0.0, 100.0, 200.0)),)),
            self._primitive_page(),
        )

    def test_bbox_with_negative_x0_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_page_analysis_against_primitive_page(
                self._analysis(regions=(self._region(bbox=(-0.1, 0.0, 50.0, 50.0)),)),
                self._primitive_page(),
            )

    def test_bbox_with_negative_y0_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_page_analysis_against_primitive_page(
                self._analysis(regions=(self._region(bbox=(0.0, -0.1, 50.0, 50.0)),)),
                self._primitive_page(),
            )

    def test_bbox_with_x1_beyond_width_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_page_analysis_against_primitive_page(
                self._analysis(regions=(self._region(bbox=(0.0, 0.0, 100.1, 50.0)),)),
                self._primitive_page(),
            )

    def test_bbox_with_y1_beyond_height_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_page_analysis_against_primitive_page(
                self._analysis(regions=(self._region(bbox=(0.0, 0.0, 50.0, 200.1)),)),
                self._primitive_page(),
            )

    def test_bbox_error_identifies_region(self) -> None:
        with self.assertRaisesRegex(ValueError, "region-1"):
            validate_page_analysis_against_primitive_page(
                self._analysis(regions=(self._region(bbox=(0.0, 0.0, 100.1, 50.0)),)),
                self._primitive_page(),
            )

    def test_validation_does_not_modify_inputs(self) -> None:
        text = self._text_primitive()
        region = self._region(primitive_ids=("text-1",))
        analysis = self._analysis(regions=(region,))
        primitive_page = self._primitive_page(text_primitives=(text,))
        expected_analysis = self._analysis(regions=(self._region(primitive_ids=("text-1",)),))
        expected_primitive_page = self._primitive_page(text_primitives=(self._text_primitive(),))

        validate_page_analysis_against_primitive_page(analysis, primitive_page)

        self.assertEqual(analysis, expected_analysis)
        self.assertEqual(analysis.provenance, self._provenance())
        self.assertEqual(primitive_page, expected_primitive_page)


if __name__ == "__main__":
    unittest.main()
