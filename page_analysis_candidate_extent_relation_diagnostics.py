"""Read-only candidate-to-extent relation diagnostics for local side-band candidates."""

from __future__ import annotations

from page_analysis_candidate_extent_relation_measurements import (
    CandidateExtentRelationMeasurements,
    CandidateNonCandidateExtentRelationMeasurements,
    measure_candidate_non_candidate_extent_relations,
)
from page_analysis_candidate_page_context_measurements import (
    measure_candidate_page_context,
)
from page_analysis_side_band import build_local_fragment_side_band_page_analysis
from primitive_model import NormalizedPrimitivePage


def dump_local_fragment_side_band_candidate_extent_relations(
    primitive_page: NormalizedPrimitivePage,
    *,
    generation_id: str,
) -> dict[str, object]:
    """Describe candidate-to-non-candidate-family extent relations as plain JSON data."""

    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")
    if not isinstance(generation_id, str) or not generation_id:
        raise ValueError("generation_id must be a non-empty string")

    analysis = build_local_fragment_side_band_page_analysis(
        primitive_page,
        generation_id=generation_id,
    )
    candidates: list[dict[str, object]] = []
    for candidate in analysis.candidates:
        context_measurements = measure_candidate_page_context(
            primitive_page,
            candidate=candidate,
        )
        relation_measurements = measure_candidate_non_candidate_extent_relations(
            context_measurements
        )
        candidates.append(_measurements_to_dict(relation_measurements))

    return {
        "generation_id": generation_id,
        "page_id": primitive_page.page_id,
        "candidates": candidates,
    }


def _measurements_to_dict(
    measurements: CandidateNonCandidateExtentRelationMeasurements,
) -> dict[str, object]:
    return {
        "candidate_id": measurements.candidate_id,
        "page_id": measurements.page_id,
        "candidate_bbox": list(measurements.candidate_bbox),
        "candidate_primitive_ids": list(measurements.candidate_primitive_ids),
        "non_candidate_visible_text_extent_bbox": _json_bbox(
            measurements.non_candidate_visible_text_extent_bbox
        ),
        "non_candidate_visible_text_extent_relation": _relation_to_dict(
            measurements.non_candidate_visible_text_extent_relation
        ),
        "non_candidate_visible_image_extent_bbox": _json_bbox(
            measurements.non_candidate_visible_image_extent_bbox
        ),
        "non_candidate_visible_image_extent_relation": _relation_to_dict(
            measurements.non_candidate_visible_image_extent_relation
        ),
        "non_candidate_visible_drawing_extent_bbox": _json_bbox(
            measurements.non_candidate_visible_drawing_extent_bbox
        ),
        "non_candidate_visible_drawing_extent_relation": _relation_to_dict(
            measurements.non_candidate_visible_drawing_extent_relation
        ),
    }


def _json_bbox(bbox: tuple[float, float, float, float] | None) -> list[float] | None:
    return None if bbox is None else list(bbox)


def _relation_to_dict(
    relation: CandidateExtentRelationMeasurements | None,
) -> dict[str, object] | None:
    if relation is None:
        return None
    return {
        "horizontal_gap": relation.horizontal_gap,
        "vertical_gap": relation.vertical_gap,
        "horizontal_overlap": relation.horizontal_overlap,
        "vertical_overlap": relation.vertical_overlap,
        "candidate_contains_extent": relation.candidate_contains_extent,
        "extent_contains_candidate": relation.extent_contains_candidate,
    }
