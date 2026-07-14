"""Read-only diagnostics for local-fragment side-band candidates."""

from __future__ import annotations

import unicodedata

from geometry_model import BBox
from page_analysis_side_band import build_local_fragment_side_band_page_analysis
from primitive_model import NormalizedPrimitivePage, TextPrimitive

_SAME_BASELINE_MIN_VERTICAL_OVERLAP_RATIO = 0.60
_BULLET_OR_MARKER_TEXTS = frozenset(
    {
        "•",
        "◦",
        "▪",
        "‣",
        "⬣",
        "◆",
        "◇",
        "■",
        "□",
        "●",
        "○",
        "▶",
        "▸",
        "►",
        "-",
        "–",
        "—",
        "*",
        "+",
        "·",
    }
)


def dump_side_band_local_fragment_diagnostics(
    primitive_page: NormalizedPrimitivePage,
    *,
    generation_id: str,
) -> dict[str, object]:
    """Describe local-fragment side-band candidates without changing them."""

    analysis = build_local_fragment_side_band_page_analysis(
        primitive_page,
        generation_id=generation_id,
    )
    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height
    text_by_id = {
        primitive.primitive_id: primitive for primitive in primitive_page.text_primitives
    }

    return {
        "generation_id": generation_id,
        "page_id": primitive_page.page_id,
        "candidates": [
            _candidate_diagnostics(
                candidate_id=candidate.candidate_id,
                bbox=candidate.bbox,
                primitive_ids=candidate.primitive_ids,
                text_by_id=text_by_id,
                text_primitives=primitive_page.text_primitives,
                page_width=page_width,
                page_height=page_height,
            )
            for candidate in analysis.candidates
        ],
    }


def _candidate_diagnostics(
    *,
    candidate_id: str,
    bbox: BBox,
    primitive_ids: tuple[str, ...],
    text_by_id: dict[str, TextPrimitive],
    text_primitives: tuple[TextPrimitive, ...],
    page_width: float,
    page_height: float,
) -> dict[str, object]:
    text = " ".join(text_by_id[primitive_id].text for primitive_id in primitive_ids)
    normalized_text = text.strip()
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    same_baseline = _same_baseline_diagnostics(
        candidate_bbox=bbox,
        candidate_primitive_ids=primitive_ids,
        text_primitives=text_primitives,
        page_width=page_width,
        page_height=page_height,
    )
    return {
        "candidate_id": candidate_id,
        "bbox": list(bbox),
        "primitive_ids": list(primitive_ids),
        "text": text,
        "primitive_count": len(primitive_ids),
        "page_width_ratio": width / page_width,
        "page_height_ratio": height / page_height,
        "page_area_ratio": (width * height) / (page_width * page_height),
        "distance_left": bbox[0],
        "distance_right": page_width - bbox[2],
        "distance_top": bbox[1],
        "distance_bottom": page_height - bbox[3],
        "distance_left_ratio": bbox[0] / page_width,
        "distance_right_ratio": (page_width - bbox[2]) / page_width,
        "distance_top_ratio": bbox[1] / page_height,
        "distance_bottom_ratio": (page_height - bbox[3]) / page_height,
        "is_numeric_only": bool(normalized_text) and normalized_text.isdecimal(),
        "is_punctuation_only": _is_punctuation_only(normalized_text),
        "is_single_character": len(normalized_text) == 1,
        "is_bullet_or_marker_like": normalized_text in _BULLET_OR_MARKER_TEXTS,
        "has_cased_characters_and_all_are_uppercase": normalized_text.isupper(),
        "is_short_uppercase": (
            normalized_text.isalpha()
            and normalized_text.isupper()
            and len(normalized_text) <= 5
        ),
        **same_baseline,
    }


def _is_punctuation_only(text: str) -> bool:
    return bool(text) and all(unicodedata.category(character).startswith("P") for character in text)


def _same_baseline_diagnostics(
    *,
    candidate_bbox: BBox,
    candidate_primitive_ids: tuple[str, ...],
    text_primitives: tuple[TextPrimitive, ...],
    page_width: float,
    page_height: float,
) -> dict[str, object]:
    candidate_ids = set(candidate_primitive_ids)
    records: list[tuple[float, float, str]] = []
    for primitive in text_primitives:
        if primitive.primitive_id in candidate_ids:
            continue
        visible_bbox = _visible_bbox(
            primitive.bbox,
            page_width=page_width,
            page_height=page_height,
        )
        if visible_bbox is None:
            continue
        vertical_overlap_ratio = _vertical_overlap_ratio(candidate_bbox, visible_bbox)
        if vertical_overlap_ratio < _SAME_BASELINE_MIN_VERTICAL_OVERLAP_RATIO:
            continue
        records.append(
            (
                _horizontal_gap(candidate_bbox, visible_bbox),
                vertical_overlap_ratio,
                primitive.primitive_id,
            )
        )

    if not records:
        return {
            "same_baseline_neighbor_count": 0,
            "nearest_same_baseline_text_primitive_id": None,
            "nearest_same_baseline_gap": None,
            "nearest_same_baseline_vertical_overlap_ratio": None,
            "has_same_baseline_neighbor": False,
        }

    nearest_gap, nearest_overlap_ratio, nearest_id = min(
        records,
        key=lambda record: (record[0], -record[1], record[2]),
    )
    return {
        "same_baseline_neighbor_count": len(records),
        "nearest_same_baseline_text_primitive_id": nearest_id,
        "nearest_same_baseline_gap": nearest_gap,
        "nearest_same_baseline_vertical_overlap_ratio": nearest_overlap_ratio,
        "has_same_baseline_neighbor": True,
    }


def _visible_bbox(
    bbox: BBox,
    *,
    page_width: float,
    page_height: float,
) -> BBox | None:
    x0 = max(0.0, bbox[0])
    y0 = max(0.0, bbox[1])
    x1 = min(page_width, bbox[2])
    y1 = min(page_height, bbox[3])
    if x0 >= x1 or y0 >= y1:
        return None
    return (x0, y0, x1, y1)


def _horizontal_gap(first_bbox: BBox, second_bbox: BBox) -> float:
    return max(0.0, first_bbox[0] - second_bbox[2], second_bbox[0] - first_bbox[2])


def _vertical_overlap_ratio(first_bbox: BBox, second_bbox: BBox) -> float:
    overlap = max(0.0, min(first_bbox[3], second_bbox[3]) - max(first_bbox[1], second_bbox[1]))
    first_height = first_bbox[3] - first_bbox[1]
    second_height = second_bbox[3] - second_bbox[1]
    return overlap / min(first_height, second_height)
