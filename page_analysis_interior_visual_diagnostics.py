"""Read-only diagnostics for visual primitives outside page_covering_visual and
page_edge_visual thresholds.

Milestone 6 (State_Archive.md:133, ripetuta a riga 894) ha deciso di non introdurre
un producer per "visuali interne" finche' non osservate con la diagnostica. Questo
modulo e' quell'osservazione: non costruisce mai un RegionCandidate, PageAnalysis o
proposed_structural_kind. Non e' superata ne' ignorata: e' soddisfatta.

Soglie di page_covering_visual/page_edge_visual duplicate localmente (stessa scelta
gia' presa per _visible_bbox in entrambi i moduli esistenti) invece di importate:
nessun helper condiviso senza una decisione dedicata (State_Archive.md:143).

I campi contained_text_* sono ispirati da extractor.py (_asset_is_box_like_text_region,
pipeline legacy) solo nel segnale (testo contenuto in una visuale), non
nell'implementazione ne' nelle soglie: calcolati componendo solo
measure_primitive_pair, gia' ratificata in Milestone 6. Nessun codice legacy
importato o duplicato.
"""

from __future__ import annotations

from geometry_model import BBox
from page_analysis_primitive_pair_measurements import (
    PrimitiveNotVisibleOnPageError,
    measure_primitive_pair,
)
from primitive_model import DrawingPrimitive, ImageOccurrencePrimitive, NormalizedPrimitivePage

_MIN_COVERING_WIDTH_RATIO = 0.95
_MIN_COVERING_HEIGHT_RATIO = 0.95
_MIN_EDGE_LONG_RATIO = 0.80
_MAX_EDGE_THIN_RATIO = 0.15
_MAX_EDGE_AREA_RATIO = 0.20
_MAX_EDGE_DISTANCE_RATIO = 0.05

type _VisualPrimitive = ImageOccurrencePrimitive | DrawingPrimitive


def dump_interior_visual_diagnostics(
    primitive_page: NormalizedPrimitivePage,
    *,
    generation_id: str,
) -> dict[str, object]:
    """Describe every visual primitive against existing thresholds; create nothing."""

    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")
    if not isinstance(generation_id, str) or not generation_id:
        raise ValueError("generation_id must be a non-empty string")

    visual_primitives: tuple[_VisualPrimitive, ...] = (
        *primitive_page.image_primitives,
        *primitive_page.drawing_primitives,
    )
    return {
        "generation_id": generation_id,
        "page_id": primitive_page.page_id,
        "visuals": [
            _visual_diagnostics(primitive, primitive_page)
            for primitive in sorted(visual_primitives, key=lambda item: item.primitive_id)
        ],
    }


def _visual_diagnostics(
    primitive: _VisualPrimitive,
    primitive_page: NormalizedPrimitivePage,
) -> dict[str, object]:
    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height
    primitive_kind = "image" if isinstance(primitive, ImageOccurrencePrimitive) else "drawing"
    content_digest = getattr(primitive, "content_digest", None)

    visible_bbox = _visible_bbox(primitive.bbox, page_width=page_width, page_height=page_height)
    if visible_bbox is None:
        return {
            "primitive_id": primitive.primitive_id,
            "primitive_kind": primitive_kind,
            "content_digest": content_digest,
            "visible_bbox": None,
            "page_width_ratio": None,
            "page_height_ratio": None,
            "page_area_ratio": None,
            "distance_left_ratio": None,
            "distance_right_ratio": None,
            "distance_top_ratio": None,
            "distance_bottom_ratio": None,
            "is_page_covering_visual": False,
            "is_page_edge_visual": False,
            "is_residual_interior_visual": False,
            "contained_text_primitive_count": 0,
            "contained_text_area_ratio": None,
        }

    width_ratio = (visible_bbox[2] - visible_bbox[0]) / page_width
    height_ratio = (visible_bbox[3] - visible_bbox[1]) / page_height
    area_ratio = width_ratio * height_ratio
    is_covering = (
        width_ratio >= _MIN_COVERING_WIDTH_RATIO and height_ratio >= _MIN_COVERING_HEIGHT_RATIO
    )
    is_edge = _is_page_edge_visual(
        visible_bbox, page_width=page_width, page_height=page_height
    )

    contained_count, contained_area_ratio = _contained_text_diagnostics(
        primitive, visible_bbox, primitive_page
    )

    return {
        "primitive_id": primitive.primitive_id,
        "primitive_kind": primitive_kind,
        "content_digest": content_digest,
        "visible_bbox": list(visible_bbox),
        "page_width_ratio": width_ratio,
        "page_height_ratio": height_ratio,
        "page_area_ratio": area_ratio,
        "distance_left_ratio": visible_bbox[0] / page_width,
        "distance_right_ratio": (page_width - visible_bbox[2]) / page_width,
        "distance_top_ratio": visible_bbox[1] / page_height,
        "distance_bottom_ratio": (page_height - visible_bbox[3]) / page_height,
        "is_page_covering_visual": is_covering,
        "is_page_edge_visual": is_edge,
        "is_residual_interior_visual": not is_covering and not is_edge,
        "contained_text_primitive_count": contained_count,
        "contained_text_area_ratio": contained_area_ratio,
    }


def _contained_text_diagnostics(
    primitive: _VisualPrimitive,
    visible_bbox: BBox,
    primitive_page: NormalizedPrimitivePage,
) -> tuple[int, float | None]:
    contained_count = 0
    contained_area = 0.0
    for text_primitive in primitive_page.text_primitives:
        try:
            measurement = measure_primitive_pair(
                primitive_page,
                first_primitive_id=primitive.primitive_id,
                second_primitive_id=text_primitive.primitive_id,
            )
        except PrimitiveNotVisibleOnPageError:
            continue
        if not measurement.first_contains_second:
            continue
        contained_count += 1
        text_bbox = measurement.second_visible_bbox
        contained_area += (text_bbox[2] - text_bbox[0]) * (text_bbox[3] - text_bbox[1])

    if contained_count == 0:
        return 0, None
    visible_area = (visible_bbox[2] - visible_bbox[0]) * (visible_bbox[3] - visible_bbox[1])
    return contained_count, contained_area / visible_area


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


def _is_page_edge_visual(
    visible_bbox: BBox,
    *,
    page_width: float,
    page_height: float,
) -> bool:
    visible_width_ratio = (visible_bbox[2] - visible_bbox[0]) / page_width
    visible_height_ratio = (visible_bbox[3] - visible_bbox[1]) / page_height
    visible_area_ratio = visible_width_ratio * visible_height_ratio
    top_distance_ratio = visible_bbox[1] / page_height
    bottom_distance_ratio = (page_height - visible_bbox[3]) / page_height
    left_distance_ratio = visible_bbox[0] / page_width
    right_distance_ratio = (page_width - visible_bbox[2]) / page_width

    is_horizontal_edge_visual = (
        visible_width_ratio >= _MIN_EDGE_LONG_RATIO
        and visible_height_ratio <= _MAX_EDGE_THIN_RATIO
        and visible_area_ratio <= _MAX_EDGE_AREA_RATIO
        and (
            top_distance_ratio <= _MAX_EDGE_DISTANCE_RATIO
            or bottom_distance_ratio <= _MAX_EDGE_DISTANCE_RATIO
        )
    )
    is_vertical_edge_visual = (
        visible_height_ratio >= _MIN_EDGE_LONG_RATIO
        and visible_width_ratio <= _MAX_EDGE_THIN_RATIO
        and visible_area_ratio <= _MAX_EDGE_AREA_RATIO
        and (
            left_distance_ratio <= _MAX_EDGE_DISTANCE_RATIO
            or right_distance_ratio <= _MAX_EDGE_DISTANCE_RATIO
        )
    )
    return is_horizontal_edge_visual or is_vertical_edge_visual
