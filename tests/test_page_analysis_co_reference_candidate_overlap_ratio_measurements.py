"""Tests for the contextual overlap-ratio measurement of co-referenced candidates."""

from __future__ import annotations

import unittest

from geometry_model import PageGeometry
from page_analysis_co_reference import build_co_referenced_page_analyses
from page_analysis_co_reference_binding import (
    BoundCoReferencedPageAnalyses,
    bind_co_referenced_page_analyses,
)
from page_analysis_co_reference_candidate_overlap_ratio_measurements import (
    measure_co_referenced_page_candidate_overlap_ratio,
)
from page_analysis_co_reference_candidate_reference import (
    CoReferencedPageCandidateReference,
    build_co_referenced_page_candidate_reference,
)
from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionCandidate,
)
from primitive_model import NormalizedPrimitivePage


def _page() -> NormalizedPrimitivePage:
    return NormalizedPrimitivePage(
        schema_version="1.0",
        source_capture_id="capture-1",
        source_id="source-1",
        page_id="page-1",
        page_index=0,
        page_geometry=PageGeometry(
            width=100.0,
            height=100.0,
            unit="pt",
            coordinate_system="top_left_y_down",
        ),
        capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
    )


def _candidate(
    candidate_id: str,
    bbox: tuple[float, float, float, float],
) -> RegionCandidate:
    return RegionCandidate(
        candidate_id=candidate_id,
        page_id="page-1",
        bbox=bbox,
        proposed_structural_kind="layout.side_band",
    )


def _analysis(
    *,
    producer_name: str,
    candidates: tuple[RegionCandidate, ...],
) -> PageAnalysis:
    return PageAnalysis(
        schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        generation_id="generation-1",
        page_id="page-1",
        provenance=PageAnalysisProvenance(
            source_id="source-1",
            source_capture_id="capture-1",
            source_page_id="page-1",
            source_primitive_schema_version="1.0",
            producer_name=producer_name,
            producer_version="0.1",
            configuration_id="config-v1",
        ),
        candidates=candidates,
    )


def _bound(*analyses: PageAnalysis) -> BoundCoReferencedPageAnalyses:
    return bind_co_referenced_page_analyses(
        _page(),
        co_referenced_page_analyses=build_co_referenced_page_analyses(analyses),
    )


def _reference(
    bound: BoundCoReferencedPageAnalyses,
    analysis: PageAnalysis,
    candidate: RegionCandidate,
) -> CoReferencedPageCandidateReference:
    return build_co_referenced_page_candidate_reference(
        bound,
        analysis=analysis,
        candidate=candidate,
    )


class MeasureCoReferencedPageCandidateOverlapRatioTests(unittest.TestCase):
    def test_partial_overlap_matches_hand_computed_values(self) -> None:
        # first: (0,0)-(10,10) area 100; second: (5,5)-(15,15) area 100.
        # intersection: (5,5)-(10,10), area 25. Smaller area is 100 (tied).
        first_candidate = _candidate("first", (0.0, 0.0, 10.0, 10.0))
        second_candidate = _candidate("second", (5.0, 5.0, 15.0, 15.0))
        first = _analysis(producer_name="alpha", candidates=(first_candidate,))
        second = _analysis(producer_name="beta", candidates=(second_candidate,))
        bound = _bound(first, second)

        result = measure_co_referenced_page_candidate_overlap_ratio(
            bound,
            first_candidate_reference=_reference(bound, first, first_candidate),
            second_candidate_reference=_reference(bound, second, second_candidate),
        )

        self.assertEqual(result.first_candidate_area, 100.0)
        self.assertEqual(result.second_candidate_area, 100.0)
        self.assertEqual(result.overlap_area, 25.0)
        self.assertEqual(result.overlap_ratio, 0.25)

    def test_overlap_ratio_is_symmetric_when_arguments_are_genuinely_swapped(self) -> None:
        first_candidate = _candidate("first", (0.0, 0.0, 10.0, 20.0))
        second_candidate = _candidate("second", (5.0, 5.0, 15.0, 15.0))
        first = _analysis(producer_name="alpha", candidates=(first_candidate,))
        second = _analysis(producer_name="beta", candidates=(second_candidate,))
        bound = _bound(first, second)
        first_reference = _reference(bound, first, first_candidate)
        second_reference = _reference(bound, second, second_candidate)

        forward = measure_co_referenced_page_candidate_overlap_ratio(
            bound,
            first_candidate_reference=first_reference,
            second_candidate_reference=second_reference,
        )
        reverse = measure_co_referenced_page_candidate_overlap_ratio(
            bound,
            first_candidate_reference=second_reference,
            second_candidate_reference=first_reference,
        )

        self.assertEqual(forward.overlap_ratio, reverse.overlap_ratio)
        self.assertEqual(forward.overlap_area, reverse.overlap_area)

    def test_disjoint_candidates_have_zero_overlap_area_and_ratio(self) -> None:
        first_candidate = _candidate("first", (0.0, 0.0, 10.0, 10.0))
        second_candidate = _candidate("second", (20.0, 20.0, 30.0, 30.0))
        first = _analysis(producer_name="alpha", candidates=(first_candidate,))
        second = _analysis(producer_name="beta", candidates=(second_candidate,))
        bound = _bound(first, second)

        result = measure_co_referenced_page_candidate_overlap_ratio(
            bound,
            first_candidate_reference=_reference(bound, first, first_candidate),
            second_candidate_reference=_reference(bound, second, second_candidate),
        )

        self.assertEqual(result.overlap_area, 0.0)
        self.assertEqual(result.overlap_ratio, 0.0)

    def test_full_containment_has_overlap_ratio_of_one(self) -> None:
        # first (container): (0,0)-(20,20) area 400.
        # second (contained): (5,5)-(10,10) area 25, entirely inside first.
        first_candidate = _candidate("first", (0.0, 0.0, 20.0, 20.0))
        second_candidate = _candidate("second", (5.0, 5.0, 10.0, 10.0))
        first = _analysis(producer_name="alpha", candidates=(first_candidate,))
        second = _analysis(producer_name="beta", candidates=(second_candidate,))
        bound = _bound(first, second)

        result = measure_co_referenced_page_candidate_overlap_ratio(
            bound,
            first_candidate_reference=_reference(bound, first, first_candidate),
            second_candidate_reference=_reference(bound, second, second_candidate),
        )

        self.assertEqual(result.overlap_area, 25.0)
        self.assertEqual(result.overlap_ratio, 1.0)


if __name__ == "__main__":
    unittest.main()
