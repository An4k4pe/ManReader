"""Read-only geometric clustering diagnostics for DrawingPrimitive.

Milestone 26. "Clustering" e' una categoria esplicitamente non autorizzata in piu'
punti di State_Archive.md (righe 117, 135, 160, 228, 894, 921-926, 962), sempre
"salvo una futura decisione architetturale dedicata" (894, 962). Questa milestone e'
quella decisione, con perimetro stretto: solo DrawingPrimitive, solo diagnostica
read-only (dict[str, object], nessun nuovo tipo pubblico Cluster/Block/Group/Span),
nessun RegionCandidate, PageAnalysis, structural_kind, nessun uso come meccanismo di
producer o candidate. Non si estende a TextPrimitive/side_band ne' a
ImageOccurrencePrimitive (gia' identificata via content_digest).

Algoritmo ispirato a extractor.py:3822-3970 (_extract_vectors, pipeline legacy) solo
nella forma -- union-find su bbox espanse di un margine fisso -- non nei valori
numerici, esposti qui come parametri espliciti con default legacy come solo punto di
partenza, non come soglia validata sul nuovo modello dati.

Il pre-filtro (min_member_area, max_member_page_width/height_ratio) esclude un
primitivo dal confronto a coppie interamente, cosi' non puo' fare da ponte fra
cluster altrimenti distanti. Non e' un'esclusione silenziosa: ogni primitivo escluso
compare comunque in output come cluster di un solo membro con excluded_reason
valorizzato.

Soglie di page_covering_visual/page_edge_visual duplicate localmente (stessa scelta
di page_analysis_interior_visual_diagnostics.py, Milestone 25) applicate al bbox
unito del cluster. dispersion_ratio (somma aree membri / area unione) rende visibile
quanto il bbox-unione sia rappresentativo dell'inchiostro reale, per distinguere un
cluster compatto da uno disperso prima di trarre conclusioni dalle soglie applicate.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import cast

from geometry_model import BBox
from primitive_model import DrawingPrimitive, NormalizedPrimitivePage

_DEFAULT_CLUSTER_MARGIN = 5.0
_DEFAULT_MIN_MEMBER_AREA = 4.0
_DEFAULT_MAX_MEMBER_PAGE_WIDTH_RATIO = 0.70
_DEFAULT_MAX_MEMBER_PAGE_HEIGHT_RATIO = 0.70

_MIN_COVERING_WIDTH_RATIO = 0.95
_MIN_COVERING_HEIGHT_RATIO = 0.95
_MIN_EDGE_LONG_RATIO = 0.80
_MAX_EDGE_THIN_RATIO = 0.15
_MAX_EDGE_AREA_RATIO = 0.20
_MAX_EDGE_DISTANCE_RATIO = 0.05


@dataclass(frozen=True, slots=True)
class _Eligibility:
    primitive: DrawingPrimitive
    excluded_reason: str | None


def dump_drawing_cluster_diagnostics(
    primitive_page: NormalizedPrimitivePage,
    *,
    generation_id: str,
    cluster_margin: float = _DEFAULT_CLUSTER_MARGIN,
    min_member_area: float = _DEFAULT_MIN_MEMBER_AREA,
    max_member_page_width_ratio: float = _DEFAULT_MAX_MEMBER_PAGE_WIDTH_RATIO,
    max_member_page_height_ratio: float = _DEFAULT_MAX_MEMBER_PAGE_HEIGHT_RATIO,
) -> dict[str, object]:
    """Describe geometric clusters of DrawingPrimitive; create nothing."""

    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")
    if not isinstance(generation_id, str) or not generation_id:
        raise ValueError("generation_id must be a non-empty string")

    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height

    eligibilities = sorted(
        (
            _classify_eligibility(
                primitive,
                page_width=page_width,
                page_height=page_height,
                min_member_area=min_member_area,
                max_member_page_width_ratio=max_member_page_width_ratio,
                max_member_page_height_ratio=max_member_page_height_ratio,
            )
            for primitive in primitive_page.drawing_primitives
        ),
        key=lambda item: item.primitive.primitive_id,
    )

    eligible = [item for item in eligibilities if item.excluded_reason is None]
    excluded = [item for item in eligibilities if item.excluded_reason is not None]

    groups = _cluster_eligible(eligible, cluster_margin=cluster_margin)

    clusters = [
        _cluster_diagnostics(
            [item.primitive for item in group],
            excluded_reason=None,
            page_width=page_width,
            page_height=page_height,
        )
        for group in groups
    ] + [
        _cluster_diagnostics(
            [item.primitive],
            excluded_reason=item.excluded_reason,
            page_width=page_width,
            page_height=page_height,
        )
        for item in excluded
    ]
    clusters.sort(key=lambda cluster: cast(list[str], cluster["drawing_primitive_ids"])[0])

    return {
        "generation_id": generation_id,
        "page_id": primitive_page.page_id,
        "cluster_margin": cluster_margin,
        "min_member_area": min_member_area,
        "max_member_page_width_ratio": max_member_page_width_ratio,
        "max_member_page_height_ratio": max_member_page_height_ratio,
        "clusters": clusters,
    }


def _classify_eligibility(
    primitive: DrawingPrimitive,
    *,
    page_width: float,
    page_height: float,
    min_member_area: float,
    max_member_page_width_ratio: float,
    max_member_page_height_ratio: float,
) -> _Eligibility:
    width = primitive.bbox[2] - primitive.bbox[0]
    height = primitive.bbox[3] - primitive.bbox[1]
    area = width * height
    if area < min_member_area:
        return _Eligibility(primitive, "tiny")
    if page_width > 0 and width / page_width > max_member_page_width_ratio:
        return _Eligibility(primitive, "border_like")
    if page_height > 0 and height / page_height > max_member_page_height_ratio:
        return _Eligibility(primitive, "border_like")
    return _Eligibility(primitive, None)


def _cluster_eligible(
    eligible: list[_Eligibility],
    *,
    cluster_margin: float,
) -> list[list[_Eligibility]]:
    parent: dict[str, str] = {
        item.primitive.primitive_id: item.primitive.primitive_id for item in eligible
    }

    def find(primitive_id: str) -> str:
        while parent[primitive_id] != primitive_id:
            parent[primitive_id] = parent[parent[primitive_id]]
            primitive_id = parent[primitive_id]
        return primitive_id

    def union(first_id: str, second_id: str) -> None:
        first_root, second_root = find(first_id), find(second_id)
        if first_root != second_root:
            parent[first_root] = second_root

    for first_index in range(len(eligible)):
        for second_index in range(first_index + 1, len(eligible)):
            first_item = eligible[first_index]
            second_item = eligible[second_index]
            if _expanded_bboxes_intersect(
                first_item.primitive.bbox,
                second_item.primitive.bbox,
                margin=cluster_margin,
            ):
                union(first_item.primitive.primitive_id, second_item.primitive.primitive_id)

    groups: dict[str, list[_Eligibility]] = defaultdict(list)
    for item in eligible:
        groups[find(item.primitive.primitive_id)].append(item)
    return list(groups.values())


def _expanded_bboxes_intersect(first: BBox, second: BBox, *, margin: float) -> bool:
    expanded_first = (
        first[0] - margin,
        first[1] - margin,
        first[2] + margin,
        first[3] + margin,
    )
    expanded_second = (
        second[0] - margin,
        second[1] - margin,
        second[2] + margin,
        second[3] + margin,
    )
    return (
        expanded_first[0] <= expanded_second[2]
        and expanded_second[0] <= expanded_first[2]
        and expanded_first[1] <= expanded_second[3]
        and expanded_second[1] <= expanded_first[3]
    )


def _cluster_diagnostics(
    members: list[DrawingPrimitive],
    *,
    excluded_reason: str | None,
    page_width: float,
    page_height: float,
) -> dict[str, object]:
    drawing_primitive_ids = sorted(member.primitive_id for member in members)
    visible_member_bboxes = [
        visible_bbox
        for member in members
        if (
            visible_bbox := _visible_bbox(
                member.bbox, page_width=page_width, page_height=page_height
            )
        )
        is not None
    ]

    if not visible_member_bboxes:
        return {
            "drawing_primitive_ids": drawing_primitive_ids,
            "primitive_count": len(members),
            "excluded_reason": excluded_reason,
            "bbox": None,
            "page_width_ratio": None,
            "page_height_ratio": None,
            "page_area_ratio": None,
            "is_page_covering_visual": False,
            "is_page_edge_visual": False,
            "is_residual_interior_visual": False,
            "member_area_sum": None,
            "dispersion_ratio": None,
        }

    union_bbox = _union_bbox(visible_member_bboxes)
    member_area_sum = sum(
        (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) for bbox in visible_member_bboxes
    )
    union_area = (union_bbox[2] - union_bbox[0]) * (union_bbox[3] - union_bbox[1])

    width_ratio = (union_bbox[2] - union_bbox[0]) / page_width
    height_ratio = (union_bbox[3] - union_bbox[1]) / page_height
    area_ratio = width_ratio * height_ratio
    is_covering = (
        width_ratio >= _MIN_COVERING_WIDTH_RATIO and height_ratio >= _MIN_COVERING_HEIGHT_RATIO
    )
    is_edge = _is_page_edge_visual(union_bbox, page_width=page_width, page_height=page_height)

    return {
        "drawing_primitive_ids": drawing_primitive_ids,
        "primitive_count": len(members),
        "excluded_reason": excluded_reason,
        "bbox": list(union_bbox),
        "page_width_ratio": width_ratio,
        "page_height_ratio": height_ratio,
        "page_area_ratio": area_ratio,
        "is_page_covering_visual": is_covering,
        "is_page_edge_visual": is_edge,
        "is_residual_interior_visual": not is_covering and not is_edge,
        "member_area_sum": member_area_sum,
        "dispersion_ratio": (member_area_sum / union_area) if union_area > 0 else None,
    }


def _union_bbox(bboxes: list[BBox]) -> BBox:
    return (
        min(bbox[0] for bbox in bboxes),
        min(bbox[1] for bbox in bboxes),
        max(bbox[2] for bbox in bboxes),
        max(bbox[3] for bbox in bboxes),
    )


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
