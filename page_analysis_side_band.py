"""Produce conservative structural side-band candidates.

The singleton producer considers only canonical singleton text hypotheses. The
local-fragment producer uses conservative locally contiguous hypotheses. Each
accepted hypothesis becomes one unresolved ``layout.side_band`` candidate.
"""

from __future__ import annotations

from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    PageAnalysis,
    PageAnalysisProvenance,
)
from page_analysis_side_band_candidate import (
    build_side_band_candidate_from_text_hypothesis,
)
from page_analysis_text_hypotheses import (
    GeometricTextHypothesis,
    build_geometric_text_hypotheses,
)
from page_analysis_text_hypothesis_measurements import (
    TextHypothesisMeasurements,
    measure_geometric_text_hypothesis,
)
from page_analysis_validate import validate_page_analysis_against_primitive_page
from primitive_model import NormalizedPrimitivePage

_PRODUCER_NAME = "page_analysis.singleton_side_band"
_PRODUCER_VERSION = "0.1"
_CONFIGURATION_ID = "singleton-side-band-v1"
_LOCAL_FRAGMENT_PRODUCER_NAME = "page_analysis.local_fragment_side_band"
_LOCAL_FRAGMENT_PRODUCER_VERSION = "0.1"
_LOCAL_FRAGMENT_CONFIGURATION_ID = "local-fragment-side-band-v1"
_SIDE_BAND_OUTER_BAND_RATIO = 0.25
_SIDE_BAND_MAX_WIDTH_RATIO = 0.22
_SIDE_BAND_VERTICAL_MARGIN_RATIO = 0.12
_LOCAL_FRAGMENT_VERTICAL_OVERLAP_RATIO = 0.60
_LOCAL_FRAGMENT_CENTER_Y_TOLERANCE_RATIO = 0.50
_LOCAL_FRAGMENT_MAX_GAP_HEIGHT_RATIO = 0.75
_LOCAL_FRAGMENT_MAX_TOTAL_GAP_HEIGHT_RATIO = 1.50


def build_singleton_side_band_page_analysis(
    primitive_page: NormalizedPrimitivePage,
    *,
    generation_id: str,
) -> PageAnalysis:
    """Build page-level side-band candidates from canonical singleton hypotheses."""

    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")
    if not isinstance(generation_id, str) or not generation_id:
        raise ValueError("generation_id must be a non-empty string")

    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height
    candidates = []

    for hypothesis in build_geometric_text_hypotheses(primitive_page):
        primitive_ids = hypothesis.primitive_ids
        measurements = measure_geometric_text_hypothesis(
            primitive_page,
            primitive_ids=primitive_ids,
        )
        if not _is_conservative_side_band_singleton(
            measurements,
            page_width=page_width,
            page_height=page_height,
        ):
            continue

        primitive_id = primitive_ids[0]
        candidates.append(
            build_side_band_candidate_from_text_hypothesis(
                primitive_page,
                candidate_id=f"candidate:side-band:{primitive_id}",
                primitive_ids=primitive_ids,
            )
        )

    analysis = PageAnalysis(
        schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        generation_id=generation_id,
        page_id=primitive_page.page_id,
        provenance=PageAnalysisProvenance(
            source_id=primitive_page.source_id,
            source_capture_id=primitive_page.source_capture_id,
            source_page_id=primitive_page.page_id,
            source_primitive_schema_version=primitive_page.schema_version,
            producer_name=_PRODUCER_NAME,
            producer_version=_PRODUCER_VERSION,
            configuration_id=_CONFIGURATION_ID,
        ),
        regions=(),
        relations=(),
        candidates=tuple(candidates),
    )
    validate_page_analysis_against_primitive_page(analysis, primitive_page)
    return analysis


def build_local_fragment_side_band_page_analysis(
    primitive_page: NormalizedPrimitivePage,
    *,
    generation_id: str,
) -> PageAnalysis:
    """Build side-band candidates from locally contiguous text fragments."""

    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")
    if not isinstance(generation_id, str) or not generation_id:
        raise ValueError("generation_id must be a non-empty string")

    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height
    candidates = []

    for hypothesis in _build_local_horizontal_fragment_hypotheses(primitive_page):
        primitive_ids = hypothesis.primitive_ids
        measurements = measure_geometric_text_hypothesis(
            primitive_page,
            primitive_ids=primitive_ids,
        )
        if not _is_conservative_side_band_singleton(
            measurements,
            page_width=page_width,
            page_height=page_height,
        ):
            continue

        candidates.append(
            build_side_band_candidate_from_text_hypothesis(
                primitive_page,
                candidate_id=(
                    "candidate:side-band:local-fragment:" + "+".join(primitive_ids)
                ),
                primitive_ids=primitive_ids,
            )
        )

    analysis = PageAnalysis(
        schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        generation_id=generation_id,
        page_id=primitive_page.page_id,
        provenance=PageAnalysisProvenance(
            source_id=primitive_page.source_id,
            source_capture_id=primitive_page.source_capture_id,
            source_page_id=primitive_page.page_id,
            source_primitive_schema_version=primitive_page.schema_version,
            producer_name=_LOCAL_FRAGMENT_PRODUCER_NAME,
            producer_version=_LOCAL_FRAGMENT_PRODUCER_VERSION,
            configuration_id=_LOCAL_FRAGMENT_CONFIGURATION_ID,
        ),
        regions=(),
        relations=(),
        candidates=tuple(candidates),
    )
    validate_page_analysis_against_primitive_page(analysis, primitive_page)
    return analysis


def _build_local_horizontal_fragment_hypotheses(
    primitive_page: NormalizedPrimitivePage,
) -> tuple[GeometricTextHypothesis, ...]:
    """Coalesce only unambiguous locally contiguous horizontal text fragments."""

    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")

    records = tuple(
        (
            hypothesis.primitive_ids[0],
            measure_geometric_text_hypothesis(
                primitive_page,
                primitive_ids=hypothesis.primitive_ids,
            ).bbox,
        )
        for hypothesis in build_geometric_text_hypotheses(primitive_page)
    )
    if not records:
        return ()

    by_id = {primitive_id: bbox for primitive_id, bbox in records}
    outgoing: dict[str, list[str]] = {primitive_id: [] for primitive_id, _ in records}
    incoming: dict[str, list[str]] = {primitive_id: [] for primitive_id, _ in records}

    for left_id, left_bbox in records:
        for right_id, right_bbox in records:
            if left_id == right_id or not _are_local_horizontal_neighbors(left_bbox, right_bbox):
                continue
            if _skips_intermediate_fragment(
                left_id,
                left_bbox,
                right_id,
                right_bbox,
                records,
            ):
                continue
            outgoing[left_id].append(right_id)
            incoming[right_id].append(left_id)

    successors = {
        primitive_id: neighbor_ids[0]
        for primitive_id, neighbor_ids in outgoing.items()
        if len(neighbor_ids) == 1 and len(incoming[neighbor_ids[0]]) == 1
    }
    predecessors = {right_id: left_id for left_id, right_id in successors.items()}

    hypotheses: list[GeometricTextHypothesis] = []
    visited: set[str] = set()
    for primitive_id, _ in records:
        if primitive_id in predecessors or primitive_id in visited:
            continue
        chain = _successor_chain(primitive_id, successors)
        visited.update(chain)
        member_bboxes = tuple(by_id[member_id] for member_id in chain)
        if (
            len(chain) > 1
            and _has_common_local_corridor(member_bboxes)
            and _has_gap_budget(member_bboxes)
        ):
            hypotheses.append(GeometricTextHypothesis(primitive_ids=chain))
        else:
            hypotheses.extend(
                GeometricTextHypothesis(primitive_ids=(member_id,)) for member_id in chain
            )

    return tuple(
        sorted(hypotheses, key=lambda hypothesis: _hypothesis_order_key(hypothesis, by_id))
    )


def _are_local_horizontal_neighbors(
    left_bbox: tuple[float, float, float, float],
    right_bbox: tuple[float, float, float, float],
) -> bool:
    if right_bbox[0] < left_bbox[2]:
        return False
    left_height = left_bbox[3] - left_bbox[1]
    right_height = right_bbox[3] - right_bbox[1]
    minimum_height = min(left_height, right_height)
    vertical_overlap = min(left_bbox[3], right_bbox[3]) - max(left_bbox[1], right_bbox[1])
    if vertical_overlap < minimum_height * _LOCAL_FRAGMENT_VERTICAL_OVERLAP_RATIO:
        return False
    left_center_y = (left_bbox[1] + left_bbox[3]) / 2.0
    right_center_y = (right_bbox[1] + right_bbox[3]) / 2.0
    if abs(left_center_y - right_center_y) > (
        minimum_height * _LOCAL_FRAGMENT_CENTER_Y_TOLERANCE_RATIO
    ):
        return False
    return right_bbox[0] - left_bbox[2] <= minimum_height * _LOCAL_FRAGMENT_MAX_GAP_HEIGHT_RATIO


def _skips_intermediate_fragment(
    left_id: str,
    left_bbox: tuple[float, float, float, float],
    right_id: str,
    right_bbox: tuple[float, float, float, float],
    records: tuple[tuple[str, tuple[float, float, float, float]], ...],
) -> bool:
    return any(
        primitive_id not in {left_id, right_id}
        and left_bbox[2] <= bbox[0] < right_bbox[0]
        and _are_local_horizontal_neighbors(left_bbox, bbox)
        and _are_local_horizontal_neighbors(bbox, right_bbox)
        for primitive_id, bbox in records
    )


def _successor_chain(start_id: str, successors: dict[str, str]) -> tuple[str, ...]:
    chain = [start_id]
    while chain[-1] in successors:
        chain.append(successors[chain[-1]])
    return tuple(chain)


def _has_common_local_corridor(bboxes: tuple[tuple[float, float, float, float], ...]) -> bool:
    minimum_height = min(bbox[3] - bbox[1] for bbox in bboxes)
    common_y0 = max(bbox[1] for bbox in bboxes)
    common_y1 = min(bbox[3] for bbox in bboxes)
    if common_y1 - common_y0 < minimum_height * _LOCAL_FRAGMENT_VERTICAL_OVERLAP_RATIO:
        return False
    centers = tuple((bbox[1] + bbox[3]) / 2.0 for bbox in bboxes)
    return max(centers) - min(centers) <= (
        minimum_height * _LOCAL_FRAGMENT_CENTER_Y_TOLERANCE_RATIO
    )


def _has_gap_budget(bboxes: tuple[tuple[float, float, float, float], ...]) -> bool:
    minimum_height = min(bbox[3] - bbox[1] for bbox in bboxes)
    total_positive_gap = sum(
        max(0.0, right_bbox[0] - left_bbox[2])
        for left_bbox, right_bbox in zip(bboxes, bboxes[1:], strict=False)
    )
    return total_positive_gap <= minimum_height * _LOCAL_FRAGMENT_MAX_TOTAL_GAP_HEIGHT_RATIO


def _hypothesis_order_key(
    hypothesis: GeometricTextHypothesis,
    by_id: dict[str, tuple[float, float, float, float]],
) -> tuple[float, float, float, float, tuple[str, ...]]:
    bboxes = tuple(by_id[primitive_id] for primitive_id in hypothesis.primitive_ids)
    return (
        min(bbox[1] for bbox in bboxes),
        min(bbox[0] for bbox in bboxes),
        max(bbox[3] for bbox in bboxes),
        max(bbox[2] for bbox in bboxes),
        hypothesis.primitive_ids,
    )


def _is_conservative_side_band_singleton(
    measurements: TextHypothesisMeasurements,
    *,
    page_width: float,
    page_height: float,
) -> bool:
    x0, y0, x1, y1 = measurements.bbox
    in_vertical_corridor = (
        y0 >= page_height * _SIDE_BAND_VERTICAL_MARGIN_RATIO
        and y1 <= page_height * (1.0 - _SIDE_BAND_VERTICAL_MARGIN_RATIO)
    )
    if not in_vertical_corridor or measurements.width_ratio > _SIDE_BAND_MAX_WIDTH_RATIO:
        return False

    is_left = x0 >= 0.0 and x1 <= page_width * _SIDE_BAND_OUTER_BAND_RATIO
    is_right = x0 >= page_width * (1.0 - _SIDE_BAND_OUTER_BAND_RATIO) and x1 <= page_width
    return is_left or is_right
