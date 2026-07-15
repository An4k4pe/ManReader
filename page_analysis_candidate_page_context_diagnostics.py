"""Read-only page-context diagnostics for local-fragment side-band candidates."""

from __future__ import annotations

from page_analysis_candidate_page_context_measurements import (
    CandidatePageContextMeasurements,
    measure_candidate_page_context,
)
from page_analysis_side_band import build_local_fragment_side_band_page_analysis
from primitive_model import NormalizedPrimitivePage


def dump_local_fragment_side_band_candidate_page_context(
    primitive_page: NormalizedPrimitivePage,
    *,
    generation_id: str,
) -> dict[str, object]:
    """Describe page context for existing local-fragment side-band candidates."""

    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")
    if not isinstance(generation_id, str) or not generation_id:
        raise ValueError("generation_id must be a non-empty string")

    analysis = build_local_fragment_side_band_page_analysis(
        primitive_page,
        generation_id=generation_id,
    )
    return {
        "generation_id": generation_id,
        "page_id": primitive_page.page_id,
        "candidates": [
            _measurements_to_dict(
                measure_candidate_page_context(primitive_page, candidate=candidate)
            )
            for candidate in analysis.candidates
        ],
    }


def _measurements_to_dict(
    measurements: CandidatePageContextMeasurements,
) -> dict[str, object]:
    return {
        "candidate_id": measurements.candidate_id,
        "page_id": measurements.page_id,
        "candidate_bbox": list(measurements.candidate_bbox),
        "candidate_primitive_ids": list(measurements.candidate_primitive_ids),
        "non_candidate_visible_text_primitive_count": (
            measurements.non_candidate_visible_text_primitive_count
        ),
        "non_candidate_visible_text_extent_bbox": _json_bbox(
            measurements.non_candidate_visible_text_extent_bbox
        ),
        "non_candidate_visible_image_primitive_count": (
            measurements.non_candidate_visible_image_primitive_count
        ),
        "non_candidate_visible_image_extent_bbox": _json_bbox(
            measurements.non_candidate_visible_image_extent_bbox
        ),
        "non_candidate_visible_drawing_primitive_count": (
            measurements.non_candidate_visible_drawing_primitive_count
        ),
        "non_candidate_visible_drawing_extent_bbox": _json_bbox(
            measurements.non_candidate_visible_drawing_extent_bbox
        ),
    }


def _json_bbox(bbox: tuple[float, float, float, float] | None) -> list[float] | None:
    return None if bbox is None else list(bbox)
