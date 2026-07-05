from __future__ import annotations

import ast
import json
import math
import unittest
from dataclasses import FrozenInstanceError, asdict, fields
from pathlib import Path

from capture_model import (
    BackendAnnotationObservation,
    BackendDrawingObservation,
    BackendImageObservation,
    BackendLinkObservation,
    BackendPageCapture,
    BackendTextObservation,
    CaptureError,
    DrawingCommand,
)
from geometry_model import PageGeometry
from primitive_model import (
    DrawingPrimitive,
    ImageOccurrencePrimitive,
    NormalizedPrimitivePage,
    TextPrimitive,
)

IDENTITY = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
CANONICAL_GEOMETRY = PageGeometry(
    width=600.0,
    height=800.0,
    unit="pt",
    coordinate_system="top_left_y_down",
)


def _text_observation(
    observation_id: str = "text:1",
    text: str = "Raw text",
) -> BackendTextObservation:
    return BackendTextObservation(
        observation_id=observation_id,
        bbox=(10.0, 20.0, 100.0, 40.0),
        text=text,
        font_name="Example",
        font_size=10.0,
        font_flags=0,
        color=(0.0, 0.0, 0.0, 1.0),
        direction=(1.0, 0.0),
    )


def _image_observation(
    observation_id: str = "image:1",
    resource_ref: str = "xref:7",
) -> BackendImageObservation:
    return BackendImageObservation(
        observation_id=observation_id,
        bbox=(20.0, 50.0, 120.0, 150.0),
        resource_ref=resource_ref,
        content_digest="sha256:example",
        pixel_width=100,
        pixel_height=100,
        placement_transform=IDENTITY,
        has_alpha=True,
    )


def _drawing_observation(
    observation_id: str = "drawing:1",
) -> BackendDrawingObservation:
    command = DrawingCommand(
        kind="line",
        points=((0.0, 0.0), (10.0, 10.0)),
    )
    return BackendDrawingObservation(
        observation_id=observation_id,
        bbox=(0.0, 0.0, 10.0, 10.0),
        commands=(command,),
        stroke_width=1.0,
        stroke_color=(0.0, 0.0, 0.0, 1.0),
        stroke_opacity=1.0,
        is_closed=False,
    )


def _text_primitive(
    primitive_id: str = "primitive:text:1",
    source_observation_id: str = "text:1",
) -> TextPrimitive:
    return TextPrimitive(
        primitive_id=primitive_id,
        bbox=(10.0, 20.0, 100.0, 40.0),
        text="Raw text",
        source_observation_id=source_observation_id,
        font_name="Example",
        font_size=10.0,
        font_traits=("bold",),
        color=(0.0, 0.0, 0.0, 1.0),
        direction=(1.0, 0.0),
    )


def _image_primitive(
    primitive_id: str = "primitive:image:1",
    source_observation_id: str = "image:1",
) -> ImageOccurrencePrimitive:
    return ImageOccurrencePrimitive(
        primitive_id=primitive_id,
        bbox=(20.0, 50.0, 120.0, 150.0),
        source_observation_id=source_observation_id,
        content_digest="sha256:example",
        intrinsic_width=100,
        intrinsic_height=100,
        placement_transform=IDENTITY,
        has_alpha=True,
    )


class GeometryModelTest(unittest.TestCase):
    def test_valid_page_geometry(self) -> None:
        self.assertEqual(CANONICAL_GEOMETRY.width, 600.0)

    def test_non_positive_page_dimensions_are_rejected(self) -> None:
        for width, height in ((0.0, 1.0), (-1.0, 1.0), (1.0, 0.0), (1.0, -1.0)):
            with self.subTest(width=width, height=height), self.assertRaises(ValueError):
                    PageGeometry(
                        width=width,
                        height=height,
                        unit="pt",
                        coordinate_system="top_left_y_down",
                    )

    def test_non_finite_page_dimensions_are_rejected(self) -> None:
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                    PageGeometry(
                        width=value,
                        height=800.0,
                        unit="pt",
                        coordinate_system="top_left_y_down",
                    )

    def test_inverted_bbox_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            BackendTextObservation("text:1", (2.0, 0.0, 1.0, 1.0), "x")

    def test_degenerate_and_external_bboxes_are_accepted(self) -> None:
        degenerate = BackendDrawingObservation("drawing:1", (1.0, 1.0, 1.0, 1.0))
        external = BackendTextObservation("text:1", (-10.0, -5.0, 700.0, 900.0), "x")
        self.assertEqual(degenerate.bbox[0], degenerate.bbox[2])
        self.assertLess(external.bbox[0], 0.0)

    def test_affine_matrix_validation(self) -> None:
        valid = BackendImageObservation(
            observation_id="image:1",
            bbox=(0.0, 0.0, 1.0, 1.0),
            placement_transform=IDENTITY,
        )
        self.assertEqual(valid.placement_transform, IDENTITY)
        with self.assertRaises(ValueError):
            BackendImageObservation(
                observation_id="image:1",
                bbox=(0.0, 0.0, 1.0, 1.0),
                placement_transform=(1.0, 0.0, 0.0, 1.0, math.inf, 0.0),
            )

    def test_color_validation(self) -> None:
        valid = BackendTextObservation(
            "text:1",
            (0.0, 0.0, 1.0, 1.0),
            "x",
            color=(0.0, 0.5, 1.0, 1.0),
        )
        self.assertEqual(valid.color, (0.0, 0.5, 1.0, 1.0))
        with self.assertRaises(ValueError):
            BackendTextObservation(
                "text:1",
                (0.0, 0.0, 1.0, 1.0),
                "x",
                color=(0.0, 0.0, 0.0, 1.1),
            )


class CaptureModelTest(unittest.TestCase):
    def test_empty_capture_is_valid(self) -> None:
        capture = BackendPageCapture(
            schema_version="1",
            capture_id="capture:1",
            backend_name="example",
            backend_version="1",
            source_id="source:1",
            page_id="page:1",
            page_index=0,
            page_geometry=CANONICAL_GEOMETRY,
        )
        self.assertEqual(capture.text_observations, ())

    def test_complete_capture_is_valid_and_serializable(self) -> None:
        text = _text_observation()
        image = _image_observation()
        drawing = _drawing_observation()
        link = BackendLinkObservation(
            "link:1",
            (0.0, 0.0, 10.0, 10.0),
            "uri",
            uri="https://example.invalid",
        )
        annotation = BackendAnnotationObservation(
            "annotation:1",
            (2.0, 2.0, 8.0, 8.0),
            "text",
            content="  preserved  ",
        )
        capture = BackendPageCapture(
            schema_version="1",
            capture_id="capture:1",
            backend_name="example",
            backend_version="1",
            source_id="source:1",
            page_id="page:1",
            page_index=0,
            page_geometry=CANONICAL_GEOMETRY,
            text_observations=(text,),
            image_observations=(image,),
            drawing_observations=(drawing,),
            link_observations=(link,),
            annotation_observations=(annotation,),
            backend_order_kind="technical",
            backend_order=("text:1", "drawing:1"),
            errors=(CaptureError("partial", "Recoverable", "text:1", True),),
        )
        json.dumps(asdict(capture))
        self.assertEqual(capture.annotation_observations[0].content, "  preserved  ")

    def test_text_is_preserved_exactly(self) -> None:
        for text in ("", "   ", "\n raw \t"):
            with self.subTest(text=text):
                self.assertEqual(_text_observation(text=text).text, text)

    def test_capture_is_frozen_and_collections_are_tuples(self) -> None:
        capture = BackendPageCapture(
            schema_version="1",
            capture_id="capture:1",
            backend_name="example",
            backend_version="1",
            source_id="source:1",
            page_id="page:1",
            page_index=0,
            page_geometry=CANONICAL_GEOMETRY,
        )
        with self.assertRaises(FrozenInstanceError):
            capture.page_index = 1  # type: ignore[misc]
        self.assertIsInstance(capture.text_observations, tuple)

    def test_duplicate_observation_ids_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            BackendPageCapture(
                schema_version="1",
                capture_id="capture:1",
                backend_name="example",
                backend_version="1",
                source_id="source:1",
                page_id="page:1",
                page_index=0,
                page_geometry=CANONICAL_GEOMETRY,
                text_observations=(_text_observation("same"), _text_observation("same")),
            )
        with self.assertRaises(ValueError):
            BackendPageCapture(
                schema_version="1",
                capture_id="capture:1",
                backend_name="example",
                backend_version="1",
                source_id="source:1",
                page_id="page:1",
                page_index=0,
                page_geometry=CANONICAL_GEOMETRY,
                text_observations=(_text_observation("same"),),
                image_observations=(_image_observation("same"),),
            )

    def test_backend_order_rules(self) -> None:
        BackendPageCapture(
            schema_version="1",
            capture_id="capture:1",
            backend_name="example",
            backend_version="1",
            source_id="source:1",
            page_id="page:1",
            page_index=0,
            page_geometry=CANONICAL_GEOMETRY,
            text_observations=(_text_observation(),),
            image_observations=(_image_observation(),),
        )
        partial = BackendPageCapture(
            schema_version="1",
            capture_id="capture:1",
            backend_name="example",
            backend_version="1",
            source_id="source:1",
            page_id="page:1",
            page_index=0,
            page_geometry=CANONICAL_GEOMETRY,
            text_observations=(_text_observation(),),
            image_observations=(_image_observation(),),
            backend_order_kind="extraction",
            backend_order=("text:1",),
        )
        self.assertEqual(partial.backend_order, ("text:1",))

        with self.assertRaises(ValueError):
            BackendPageCapture(
                schema_version="1",
                capture_id="capture:1",
                backend_name="example",
                backend_version="1",
                source_id="source:1",
                page_id="page:1",
                page_index=0,
                page_geometry=CANONICAL_GEOMETRY,
                text_observations=(_text_observation(),),
                image_observations=(_image_observation(),),
                backend_order=("text:1",),
            )

        with self.assertRaises(ValueError):
            BackendPageCapture(
                schema_version="1",
                capture_id="capture:1",
                backend_name="example",
                backend_version="1",
                source_id="source:1",
                page_id="page:1",
                page_index=0,
                page_geometry=CANONICAL_GEOMETRY,
                text_observations=(_text_observation(),),
                image_observations=(_image_observation(),),
                backend_order_kind="technical",
                backend_order=("missing",),
            )

        with self.assertRaises(ValueError):
            BackendPageCapture(
                schema_version="1",
                capture_id="capture:1",
                backend_name="example",
                backend_version="1",
                source_id="source:1",
                page_id="page:1",
                page_index=0,
                page_geometry=CANONICAL_GEOMETRY,
                text_observations=(_text_observation(),),
                image_observations=(_image_observation(),),
                backend_order_kind="technical",
                backend_order=("text:1", "text:1"),
            )

    def test_invalid_rotation_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            BackendPageCapture(
                schema_version="1",
                capture_id="capture:1",
                backend_name="example",
                backend_version="1",
                source_id="source:1",
                page_id="page:1",
                page_index=0,
                page_geometry=CANONICAL_GEOMETRY,
                source_rotation_degrees=45,  # type: ignore[arg-type]
            )

    def test_same_resource_ref_can_have_multiple_occurrences(self) -> None:
        capture = BackendPageCapture(
            schema_version="1",
            capture_id="capture:1",
            backend_name="example",
            backend_version="1",
            source_id="source:1",
            page_id="page:1",
            page_index=0,
            page_geometry=CANONICAL_GEOMETRY,
            image_observations=(
                _image_observation("image:1", "xref:7"),
                _image_observation("image:2", "xref:7"),
            ),
        )
        self.assertEqual(len(capture.image_observations), 2)

    def test_capture_error_reference_rules(self) -> None:
        BackendPageCapture(
            schema_version="1",
            capture_id="capture:1",
            backend_name="example",
            backend_version="1",
            source_id="source:1",
            page_id="page:1",
            page_index=0,
            page_geometry=CANONICAL_GEOMETRY,
            errors=(CaptureError("page", "Page-level error"),),
        )
        BackendPageCapture(
            schema_version="1",
            capture_id="capture:1",
            backend_name="example",
            backend_version="1",
            source_id="source:1",
            page_id="page:1",
            page_index=0,
            page_geometry=CANONICAL_GEOMETRY,
            text_observations=(_text_observation(),),
            errors=(CaptureError("text", "Text warning", "text:1"),),
        )
        with self.assertRaises(ValueError):
            BackendPageCapture(
                schema_version="1",
                capture_id="capture:1",
                backend_name="example",
                backend_version="1",
                source_id="source:1",
                page_id="page:1",
                page_index=0,
                page_geometry=CANONICAL_GEOMETRY,
                errors=(CaptureError("bad", "Unknown observation", "missing"),),
            )

    def test_link_targets_and_annotation(self) -> None:
        BackendLinkObservation(
            "link:uri",
            (0.0, 0.0, 1.0, 1.0),
            "uri",
            uri="https://example.invalid",
        )
        BackendLinkObservation(
            "link:page",
            (0.0, 0.0, 1.0, 1.0),
            "page",
            target_page_index=2,
        )
        BackendLinkObservation(
            "link:named",
            (0.0, 0.0, 1.0, 1.0),
            "named_destination",
            named_destination="chapter-1",
        )
        BackendAnnotationObservation(
            "annotation:1",
            (0.0, 0.0, 1.0, 1.0),
            "text",
        )
        invalid_cases = (
            dict(target_kind="uri"),
            dict(target_kind="uri", uri="x", target_page_index=1),
            dict(target_kind="page", uri="x"),
            dict(target_kind="named_destination", target_page_index=1),
            dict(target_kind="unknown", uri="x", target_page_index=1),
        )
        for kwargs in invalid_cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                    BackendLinkObservation(
                        "link:bad",
                        (0.0, 0.0, 1.0, 1.0),
                        **kwargs,  # type: ignore[arg-type]
                    )


class PrimitiveModelTest(unittest.TestCase):
    def test_canonical_page_is_valid_and_serializable(self) -> None:
        text = _text_primitive()
        image = _image_primitive()
        drawing = DrawingPrimitive(
            primitive_id="primitive:drawing:1",
            bbox=(0.0, 0.0, 10.0, 10.0),
            source_observation_id="drawing:1",
            commands=(
                DrawingCommand(
                    kind="line",
                    points=((0.0, 0.0), (10.0, 10.0)),
                ),
            ),
        )
        page = NormalizedPrimitivePage(
            schema_version="1",
            source_capture_id="capture:1",
            source_id="source:1",
            page_id="page:1",
            page_index=0,
            page_geometry=CANONICAL_GEOMETRY,
            capture_to_canonical_transform=IDENTITY,
            text_primitives=(text,),
            image_primitives=(image,),
            drawing_primitives=(drawing,),
        )
        json.dumps(asdict(page))
        self.assertEqual(page.capture_to_canonical_transform, IDENTITY)

    def test_normalized_page_requires_canonical_geometry(self) -> None:
        pixel_geometry = PageGeometry(
            600.0,
            800.0,
            "px",
            "top_left_y_down",
        )
        bottom_left_geometry = PageGeometry(
            600.0,
            800.0,
            "pt",
            "bottom_left_y_up",
        )
        for geometry in (pixel_geometry, bottom_left_geometry):
            with self.subTest(geometry=geometry), self.assertRaises(ValueError):
                    NormalizedPrimitivePage(
                        schema_version="1",
                        source_capture_id="capture:1",
                        source_id="source:1",
                        page_id="page:1",
                        page_index=0,
                        page_geometry=geometry,
                        capture_to_canonical_transform=IDENTITY,
                    )

    def test_invalid_canonical_transform_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            NormalizedPrimitivePage(
                schema_version="1",
                source_capture_id="capture:1",
                source_id="source:1",
                page_id="page:1",
                page_index=0,
                page_geometry=CANONICAL_GEOMETRY,
                capture_to_canonical_transform=(
                    1.0,
                    0.0,
                    0.0,
                    1.0,
                    math.nan,
                    0.0,
                ),
            )

    def test_primitive_is_frozen_and_collections_are_tuples(self) -> None:
        primitive = _text_primitive()
        with self.assertRaises(FrozenInstanceError):
            primitive.text = "changed"  # type: ignore[misc]
        self.assertIsInstance(primitive.font_traits, tuple)

    def test_duplicate_primitive_ids_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            NormalizedPrimitivePage(
                schema_version="1",
                source_capture_id="capture:1",
                source_id="source:1",
                page_id="page:1",
                page_index=0,
                page_geometry=CANONICAL_GEOMETRY,
                capture_to_canonical_transform=IDENTITY,
                text_primitives=(
                    _text_primitive("same"),
                    _text_primitive("same", "text:2"),
                ),
            )
        with self.assertRaises(ValueError):
            NormalizedPrimitivePage(
                schema_version="1",
                source_capture_id="capture:1",
                source_id="source:1",
                page_id="page:1",
                page_index=0,
                page_geometry=CANONICAL_GEOMETRY,
                capture_to_canonical_transform=IDENTITY,
                text_primitives=(_text_primitive("same"),),
                image_primitives=(_image_primitive("same"),),
            )

    def test_source_reference_and_duplicate_content_rules(self) -> None:
        with self.assertRaises(ValueError):
            _text_primitive(source_observation_id="")
        page = NormalizedPrimitivePage(
            schema_version="1",
            source_capture_id="capture:1",
            source_id="source:1",
            page_id="page:1",
            page_index=0,
            page_geometry=CANONICAL_GEOMETRY,
            capture_to_canonical_transform=IDENTITY,
            text_primitives=(
                _text_primitive("primitive:text:1", "text:1"),
                _text_primitive("primitive:text:2", "text:1"),
            ),
            image_primitives=(
                _image_primitive("primitive:image:1", "image:1"),
                _image_primitive("primitive:image:2", "image:2"),
            ),
        )
        self.assertEqual(len(page.text_primitives), 2)
        self.assertEqual(
            page.image_primitives[0].content_digest,
            page.image_primitives[1].content_digest,
        )

    def test_image_and_drawing_bbox_rules(self) -> None:
        with self.assertRaises(ValueError):
            ImageOccurrencePrimitive(
                primitive_id="primitive:image:1",
                bbox=(1.0, 1.0, 1.0, 2.0),
                source_observation_id="image:1",
            )
        drawing = DrawingPrimitive(
            primitive_id="primitive:drawing:1",
            bbox=(1.0, 1.0, 1.0, 1.0),
            source_observation_id="drawing:1",
        )
        self.assertEqual(drawing.bbox[0], drawing.bbox[2])

    def test_text_direction_and_font_trait_rules(self) -> None:
        with self.assertRaises(ValueError):
            TextPrimitive(
                primitive_id="primitive:text:1",
                bbox=(0.0, 0.0, 1.0, 1.0),
                text="x",
                source_observation_id="text:1",
                direction=(2.0, 0.0),
            )
        with self.assertRaises(ValueError):
            TextPrimitive(
                primitive_id="primitive:text:1",
                bbox=(0.0, 0.0, 1.0, 1.0),
                text="x",
                source_observation_id="text:1",
                font_traits=("bold", "bold"),
            )

    def test_primitives_do_not_expose_forbidden_fields(self) -> None:
        forbidden = {
            "role",
            "classification",
            "semantic_role",
            "structural_kind",
            "is_background",
            "is_duplicate",
            "reading_order",
            "resource_ref",
            "source_order",
            "backend_order",
            "errors",
        }
        for model in (
            TextPrimitive,
            ImageOccurrencePrimitive,
            DrawingPrimitive,
            NormalizedPrimitivePage,
        ):
            with self.subTest(model=model.__name__):
                names = {field.name for field in fields(model)}
                self.assertTrue(names.isdisjoint(forbidden))


class ImportBoundaryTest(unittest.TestCase):
    def test_new_models_do_not_import_legacy_or_pdf_backends(self) -> None:
        root = Path(__file__).resolve().parents[1]
        forbidden = {"extractor", "ir_model", "fitz", "pdfplumber"}

        for filename in (
            "geometry_model.py",
            "capture_model.py",
            "primitive_model.py",
        ):
            with self.subTest(filename=filename):
                tree = ast.parse((root / filename).read_text(encoding="utf-8"))
                imported_roots: set[str] = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imported_roots.add(node.module.split(".", 1)[0])
                self.assertTrue(imported_roots.isdisjoint(forbidden))


if __name__ == "__main__":
    unittest.main()
