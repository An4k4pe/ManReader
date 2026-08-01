from __future__ import annotations

import unittest

from geometry_model import PageGeometry
from page_analysis_co_reference import build_co_referenced_page_analyses
from page_analysis_co_reference_binding import bind_co_referenced_page_analyses
from page_analysis_embedded_visual import build_embedded_visual_page_analysis
from page_analysis_interior_visual_frame import build_interior_visual_frame_page_analysis
from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionCandidate,
)
from primitive_model import (
    DrawingPrimitive,
    ImageOccurrencePrimitive,
    NormalizedPrimitivePage,
    TextPrimitive,
)
from resolution_page_candidates import resolve_page_candidates


def _image(
    primitive_id: str,
    bbox: tuple[float, float, float, float],
) -> ImageOccurrencePrimitive:
    return ImageOccurrencePrimitive(
        primitive_id=primitive_id,
        bbox=bbox,
        source_observation_id=f"obs:{primitive_id}",
    )


def _drawing(
    primitive_id: str,
    bbox: tuple[float, float, float, float],
) -> DrawingPrimitive:
    return DrawingPrimitive(
        primitive_id=primitive_id,
        bbox=bbox,
        source_observation_id=f"obs:{primitive_id}",
    )


def _text(
    primitive_id: str,
    bbox: tuple[float, float, float, float],
) -> TextPrimitive:
    return TextPrimitive(
        primitive_id=primitive_id,
        bbox=bbox,
        text=primitive_id,
        source_observation_id=f"obs:{primitive_id}",
    )


def _page(
    *,
    text: tuple[TextPrimitive, ...] = (),
    images: tuple[ImageOccurrencePrimitive, ...] = (),
    drawings: tuple[DrawingPrimitive, ...] = (),
) -> NormalizedPrimitivePage:
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
        text_primitives=text,
        image_primitives=images,
        drawing_primitives=drawings,
    )


def _custom_analysis(
    page: NormalizedPrimitivePage,
    *,
    producer_name: str,
    candidate_id: str,
    primitive_ids: tuple[str, ...],
    bbox: tuple[float, float, float, float],
) -> PageAnalysis:
    """A synthetic analysis stream for a producer with no Resolution rule."""

    return PageAnalysis(
        schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        generation_id="gen-1",
        page_id=page.page_id,
        provenance=PageAnalysisProvenance(
            source_id=page.source_id,
            source_capture_id=page.source_capture_id,
            source_page_id=page.page_id,
            source_primitive_schema_version=page.schema_version,
            producer_name=producer_name,
            producer_version="1.0",
            configuration_id="custom-v1",
        ),
        candidates=(
            RegionCandidate(
                candidate_id=candidate_id,
                page_id=page.page_id,
                bbox=bbox,
                proposed_structural_kind="layout.custom_test_kind",
                primitive_ids=primitive_ids,
            ),
        ),
    )


def _resolve(
    page: NormalizedPrimitivePage,
    analyses: tuple[PageAnalysis, ...],
):
    co_referenced = build_co_referenced_page_analyses(analyses)
    bound = bind_co_referenced_page_analyses(page, co_referenced_page_analyses=co_referenced)
    return resolve_page_candidates(bound)


class ResolvePageCandidatesTest(unittest.TestCase):
    def test_raster_case_accepts_frame_and_rejects_embedded_visual(self) -> None:
        page = _page(
            text=(_text("inside", (30.0, 30.0, 50.0, 40.0)),),
            images=(_image("framed", (20.0, 20.0, 80.0, 100.0)),),
        )
        embedded_analysis = build_embedded_visual_page_analysis(page, generation_id="gen-1")
        frame_analysis = build_interior_visual_frame_page_analysis(page, generation_id="gen-1")

        resolved = _resolve(page, (embedded_analysis, frame_analysis))

        self.assertEqual(len(resolved.outcomes), 2)
        by_producer = {
            outcome.candidate_reference.producer_name: outcome
            for outcome in resolved.outcomes
        }
        frame_outcome = by_producer["page_analysis.interior_visual_frame"]
        embedded_outcome = by_producer["page_analysis.embedded_visual"]

        self.assertEqual(frame_outcome.outcome, "accepted")
        self.assertIsNone(frame_outcome.reason_token)
        self.assertEqual(embedded_outcome.outcome, "rejected")
        self.assertEqual(embedded_outcome.reason_token, "superseded_by_more_specific")

    def test_resolution_is_independent_of_stream_construction_order(self) -> None:
        page = _page(
            text=(_text("inside", (30.0, 30.0, 50.0, 40.0)),),
            images=(_image("framed", (20.0, 20.0, 80.0, 100.0)),),
        )
        embedded_analysis = build_embedded_visual_page_analysis(page, generation_id="gen-1")
        frame_analysis = build_interior_visual_frame_page_analysis(page, generation_id="gen-1")

        # build_co_referenced_page_analyses canonicalizes the stream order
        # regardless of the order passed in: verifying that explicitly here is
        # a zero-cost regression check, since embedded_visual sorts before
        # interior_visual_frame alphabetically either way.
        co_referenced_embedded_first = build_co_referenced_page_analyses(
            (embedded_analysis, frame_analysis)
        )
        co_referenced_frame_first = build_co_referenced_page_analyses(
            (frame_analysis, embedded_analysis)
        )
        expected_producer_order = (
            "page_analysis.embedded_visual",
            "page_analysis.interior_visual_frame",
        )
        self.assertEqual(
            tuple(
                analysis.provenance.producer_name
                for analysis in co_referenced_embedded_first.analyses
            ),
            expected_producer_order,
        )
        self.assertEqual(
            tuple(
                analysis.provenance.producer_name
                for analysis in co_referenced_frame_first.analyses
            ),
            expected_producer_order,
        )

        resolved_embedded_first = _resolve(page, (embedded_analysis, frame_analysis))
        resolved_frame_first = _resolve(page, (frame_analysis, embedded_analysis))

        self.assertEqual(set(resolved_embedded_first.outcomes), set(resolved_frame_first.outcomes))

    def test_no_rule_applies_regardless_of_producer_name_or_construction_order(self) -> None:
        page = _page(drawings=(_drawing("shared", (10.0, 10.0, 20.0, 20.0)),))
        zzz_analysis = _custom_analysis(
            page,
            producer_name="custom.zzz_producer",
            candidate_id="candidate:zzz:1",
            primitive_ids=("shared",),
            bbox=(10.0, 10.0, 20.0, 20.0),
        )
        aaa_analysis = _custom_analysis(
            page,
            producer_name="custom.aaa_producer",
            candidate_id="candidate:aaa:1",
            primitive_ids=("shared",),
            bbox=(10.0, 10.0, 20.0, 20.0),
        )

        resolved_zzz_first = _resolve(page, (zzz_analysis, aaa_analysis))
        resolved_aaa_first = _resolve(page, (aaa_analysis, zzz_analysis))

        for resolved in (resolved_zzz_first, resolved_aaa_first):
            self.assertEqual(len(resolved.outcomes), 2)
            for outcome in resolved.outcomes:
                self.assertEqual(outcome.outcome, "unresolved")
                self.assertEqual(outcome.reason_token, "no_applicable_rule")

        self.assertEqual(set(resolved_zzz_first.outcomes), set(resolved_aaa_first.outcomes))

    def test_page_with_no_candidates_has_no_outcomes(self) -> None:
        page = _page(drawings=(_drawing("solo", (10.0, 10.0, 20.0, 20.0)),))
        analysis = PageAnalysis(
            schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
            generation_id="gen-1",
            page_id=page.page_id,
            provenance=PageAnalysisProvenance(
                source_id=page.source_id,
                source_capture_id=page.source_capture_id,
                source_page_id=page.page_id,
                source_primitive_schema_version=page.schema_version,
                producer_name="custom.no_candidates_producer",
                producer_version="1.0",
                configuration_id="custom-v1",
            ),
        )

        resolved = _resolve(page, (analysis,))

        self.assertEqual(resolved.outcomes, ())


if __name__ == "__main__":
    unittest.main()
