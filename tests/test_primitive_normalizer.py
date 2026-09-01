from __future__ import annotations

import unittest
from dataclasses import fields

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
from primitive_normalizer import (
    NORMALIZED_PRIMITIVE_SCHEMA_VERSION,
    font_traits_from_flags,
    normalize_backend_page_capture,
)

IDENTITY = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
CANONICAL_GEOMETRY = PageGeometry(
    width=600.0,
    height=800.0,
    unit="pt",
    coordinate_system="top_left_y_down",
)


def _capture(
    *,
    text_observations: tuple[BackendTextObservation, ...] = (),
    image_observations: tuple[BackendImageObservation, ...] = (),
    drawing_observations: tuple[BackendDrawingObservation, ...] = (),
    link_observations: tuple[BackendLinkObservation, ...] = (),
    annotation_observations: tuple[BackendAnnotationObservation, ...] = (),
    errors: tuple[CaptureError, ...] = (),
    geometry: PageGeometry = CANONICAL_GEOMETRY,
) -> BackendPageCapture:
    return BackendPageCapture(
        schema_version="1",
        capture_id="capture:page:7",
        backend_name="example",
        backend_version="1",
        source_id="source:book",
        page_id="page:7",
        page_index=6,
        page_geometry=geometry,
        text_observations=text_observations,
        image_observations=image_observations,
        drawing_observations=drawing_observations,
        link_observations=link_observations,
        annotation_observations=annotation_observations,
        errors=errors,
    )


class PrimitiveNormalizerTest(unittest.TestCase):
    def test_empty_capture_produces_empty_canonical_page(self) -> None:
        page = normalize_backend_page_capture(_capture())

        self.assertEqual(page.schema_version, NORMALIZED_PRIMITIVE_SCHEMA_VERSION)
        self.assertEqual(page.source_capture_id, "capture:page:7")
        self.assertEqual(page.source_id, "source:book")
        self.assertEqual(page.page_id, "page:7")
        self.assertEqual(page.page_index, 6)
        self.assertEqual(page.page_geometry, CANONICAL_GEOMETRY)
        self.assertEqual(page.capture_to_canonical_transform, IDENTITY)
        self.assertEqual(page.text_primitives, ())
        self.assertEqual(page.image_primitives, ())
        self.assertEqual(page.drawing_primitives, ())

    def test_supported_observations_are_converted_one_to_one(self) -> None:
        texts = (
            BackendTextObservation(
                observation_id="text:1",
                bbox=(10.0, 20.0, 100.0, 40.0),
                text=" raw ",
                font_name="Example",
                font_size=10.0,
                font_flags=17,
                color=(0.1, 0.2, 0.3, 1.0),
                direction=(2.0, 0.0),
            ),
            BackendTextObservation(
                observation_id="text:2",
                bbox=(10.0, 50.0, 80.0, 65.0),
                text="second",
            ),
        )
        images = (
            BackendImageObservation(
                observation_id="image:1",
                bbox=(20.0, 100.0, 120.0, 200.0),
                resource_ref="xref:7",
                content_digest="md5:abc",
                pixel_width=100,
                pixel_height=100,
                placement_transform=IDENTITY,
                has_alpha=True,
            ),
            BackendImageObservation(
                observation_id="image:2",
                bbox=(220.0, 100.0, 320.0, 200.0),
                resource_ref="xref:7",
                content_digest="md5:abc",
                pixel_width=100,
                pixel_height=100,
                placement_transform=IDENTITY,
                has_alpha=True,
            ),
        )
        command = DrawingCommand(
            kind="line",
            points=((0.0, 0.0), (10.0, 10.0)),
        )
        drawings = (
            BackendDrawingObservation(
                observation_id="drawing:1",
                bbox=(0.0, 0.0, 10.0, 10.0),
                commands=(command,),
                stroke_width=1.0,
                stroke_color=(0.0, 0.0, 0.0, 1.0),
                fill_color=(1.0, 1.0, 1.0, 1.0),
                stroke_opacity=0.75,
                fill_opacity=0.5,
                is_closed=False,
            ),
        )

        page = normalize_backend_page_capture(
            _capture(
                text_observations=texts,
                image_observations=images,
                drawing_observations=drawings,
            )
        )

        self.assertEqual(len(page.text_primitives), len(texts))
        self.assertEqual(len(page.image_primitives), len(images))
        self.assertEqual(len(page.drawing_primitives), len(drawings))

        text = page.text_primitives[0]
        self.assertEqual(text.bbox, texts[0].bbox)
        self.assertEqual(text.text, " raw ")
        self.assertEqual(text.source_observation_id, "text:1")
        self.assertEqual(text.font_name, "Example")
        self.assertEqual(text.font_size, 10.0)
        # La fixture porta `font_flags=17`, cioe' bold (16) piu' superscript (1).
        # Questa riga asseriva la tupla VUOTA, che era il difetto: il campo
        # esisteva, era validato, e il normalizzatore ci scriveva `()` buttando
        # via l'informazione catturata.
        self.assertEqual(text.font_traits, ("bold", "superscript"))
        self.assertEqual(text.color, (0.1, 0.2, 0.3, 1.0))
        self.assertEqual(text.direction, (1.0, 0.0))

        image = page.image_primitives[0]
        self.assertEqual(image.bbox, images[0].bbox)
        self.assertEqual(image.source_observation_id, "image:1")
        self.assertEqual(image.content_digest, "md5:abc")
        self.assertEqual(image.intrinsic_width, 100)
        self.assertEqual(image.intrinsic_height, 100)
        self.assertEqual(image.placement_transform, IDENTITY)
        self.assertTrue(image.has_alpha)

        drawing = page.drawing_primitives[0]
        self.assertEqual(drawing.bbox, drawings[0].bbox)
        self.assertEqual(drawing.source_observation_id, "drawing:1")
        self.assertEqual(drawing.commands, (command,))
        self.assertEqual(drawing.stroke_width, 1.0)
        self.assertEqual(drawing.stroke_opacity, 0.75)
        self.assertEqual(drawing.fill_opacity, 0.5)
        self.assertFalse(drawing.is_closed)

    def test_ids_are_deterministic_and_distinct_per_observation(self) -> None:
        capture = _capture(
            text_observations=(
                BackendTextObservation("shared", (0.0, 0.0, 1.0, 1.0), "x"),
            ),
            image_observations=(
                BackendImageObservation("image:1", (0.0, 0.0, 1.0, 1.0)),
                BackendImageObservation("image:2", (1.0, 0.0, 2.0, 1.0)),
            ),
        )

        first = normalize_backend_page_capture(capture)
        second = normalize_backend_page_capture(capture)

        self.assertEqual(first, second)
        primitive_ids = {
            primitive.primitive_id
            for primitive in (
                *first.text_primitives,
                *first.image_primitives,
                *first.drawing_primitives,
            )
        }
        self.assertEqual(len(primitive_ids), 3)
        self.assertEqual(
            tuple(image.source_observation_id for image in first.image_primitives),
            ("image:1", "image:2"),
        )

    def test_capture_errors_do_not_hide_successful_observations(self) -> None:
        page = normalize_backend_page_capture(
            _capture(
                text_observations=(
                    BackendTextObservation("text:1", (0.0, 0.0, 1.0, 1.0), "x"),
                ),
                errors=(CaptureError("partial", "recoverable"),),
            )
        )
        self.assertEqual(len(page.text_primitives), 1)

    def test_noncanonical_geometry_is_rejected(self) -> None:
        geometries = (
            PageGeometry(600.0, 800.0, "px", "top_left_y_down"),
            PageGeometry(600.0, 800.0, "pt", "bottom_left_y_up"),
        )
        for geometry in geometries:
            with self.subTest(geometry=geometry), self.assertRaisesRegex(
                ValueError,
                "not directly convertible",
            ):
                normalize_backend_page_capture(_capture(geometry=geometry))

    def test_unsupported_observation_channels_are_not_silently_discarded(self) -> None:
        link = BackendLinkObservation(
            "link:1",
            (0.0, 0.0, 1.0, 1.0),
            "uri",
            uri="https://example.invalid",
        )
        annotation = BackendAnnotationObservation(
            "annotation:1",
            (0.0, 0.0, 1.0, 1.0),
            "text",
        )
        with self.assertRaisesRegex(ValueError, "link observations"):
            normalize_backend_page_capture(_capture(link_observations=(link,)))
        with self.assertRaisesRegex(ValueError, "annotation observations"):
            normalize_backend_page_capture(
                _capture(annotation_observations=(annotation,))
            )

    def test_degenerate_image_bbox_is_rejected_with_source_identity(self) -> None:
        image = BackendImageObservation(
            "image:thin",
            (10.0, 10.0, 10.0, 20.0),
        )
        with self.assertRaisesRegex(ValueError, "image:thin"):
            normalize_backend_page_capture(_capture(image_observations=(image,)))

    def test_the_stored_resource_fact_crosses_but_the_identifier_does_not(
        self,
    ) -> None:
        """Il confine che questa correzione sposta, e quello che NON sposta.

        `resource_ref` e' `"xref:7"`, cioe' backend-locale, e resta di la'
        (`capture_model` §Identifiers). Il fatto che codifica -- se una risorsa
        raster memorizzata ci sia -- deve invece attraversare, perche' senza di
        esso a valle non si distingue un'immagine da un raster che il renderer
        ha sintetizzato per contenuto che immagine non e'.
        """

        for declared in (True, False, None):
            with self.subTest(has_stored_resource=declared):
                image = BackendImageObservation(
                    "image:i0000",
                    (10.0, 10.0, 20.0, 20.0),
                    resource_ref="xref:7",
                    has_stored_resource=declared,
                )
                page = normalize_backend_page_capture(
                    _capture(image_observations=(image,))
                )
                primitive = page.image_primitives[0]
                self.assertIs(primitive.has_stored_resource, declared)
                self.assertFalse(hasattr(primitive, "resource_ref"))

    def test_normalizer_does_not_add_semantic_or_order_fields(self) -> None:
        forbidden = {
            "role",
            "classification",
            "semantic_role",
            "structural_kind",
            "reading_order",
            "backend_order",
            "resource_ref",
        }
        for model in (
            TextPrimitive,
            ImageOccurrencePrimitive,
            DrawingPrimitive,
            NormalizedPrimitivePage,
        ):
            with self.subTest(model=model.__name__):
                self.assertTrue(
                    {field.name for field in fields(model)}.isdisjoint(forbidden)
                )


if __name__ == "__main__":
    unittest.main()


class FontTraitsFromFlagsTest(unittest.TestCase):
    """Il campo che esisteva, era validato, e questo modulo svuotava."""

    def test_no_flags_gives_no_traits(self) -> None:
        self.assertEqual(font_traits_from_flags(None), ())
        self.assertEqual(font_traits_from_flags(0), ())

    def test_bold_and_serif_of_a_real_title(self) -> None:
        # Wil idx 103, titolo `I Wilder`: GaramondPremrPro-Bd, flags=20.
        self.assertEqual(font_traits_from_flags(20), ("bold", "serifed"))

    def test_bold_italic_and_serif_of_a_real_side_note(self) -> None:
        # DIE p.380, note a margine: MinionPro-SemiboldIt, flags=22.
        self.assertEqual(font_traits_from_flags(22), ("bold", "italic", "serifed"))

    def test_the_order_is_fixed_and_not_the_bit_order(self) -> None:
        # `font_traits` e' una tupla e il modello ne vieta i duplicati: l'uscita
        # dev'essere deterministica, non dipendere dall'ordine dei bit.
        self.assertEqual(
            font_traits_from_flags(1 | 2 | 4 | 8 | 16),
            ("bold", "italic", "superscript", "monospaced", "serifed"),
        )
