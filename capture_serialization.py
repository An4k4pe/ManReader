"""Conversione JSON per `BackendPageCapture`, nei due versi.

**Il verso che mancava e' la lettura.** `job_capture_page_runner` scrive gia'
`asdict(capture)` in `raw/page-NNNN.json`, ma **nessuno sa rileggerlo**: a ogni
cache miss `job_page_analysis_runner` **ricattura la pagina dallo snapshot**, e
l'artefatto su disco serve solo da testimone che quella pagina e' stata fatta.
Lo stesso buco vale per le primitive, che infatti la fetta verticale ricattura.

Segue `page_analysis_serialization` e `ir2_serialization`: dizionari
deterministici, tuple ricostruite come tuple, e **nessun valore inventato in
lettura** -- una chiave che manca resta il default del contratto, una chiave che
non appartiene al contratto fa fallire.

**Le tuple tornano tuple, non liste.** JSON non distingue, i contratti si': ogni
dataclass di `capture_model` e' `frozen` con campi `tuple`, e ricostruirli come
liste passerebbe la validazione di `__post_init__` in alcuni punti e la
romperebbe in altri, in modo dipendente dal campo. Qui la conversione e'
esplicita per ogni campo, e il round-trip lo verifica.

**Perche' non `dataclasses.asdict` e `Cls(**d)`.** `asdict` funziona in
scrittura ma degrada le tuple a liste; e la ricostruzione ingenua non ricorre
nei figli, quindi `page_geometry` tornerebbe un dizionario invece di un
`PageGeometry`. Il modo esplicito costa righe e non ha quei due difetti.
"""

from __future__ import annotations

from typing import Any, cast

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
from geometry_model import BBox, PageGeometry, Point, RGBAColor

CAPTURE_SERIALIZATION_SCHEMA = "capture-serialization-1"


def _tupla(valore: object) -> tuple[float, ...] | None:
    """Una sequenza di numeri torna tupla; `None` resta `None`."""

    if valore is None:
        return None
    if not isinstance(valore, (list, tuple)):
        raise ValueError("expected a sequence of numbers")
    return tuple(float(componente) for componente in cast("list[Any]", valore))


def _bbox(valore: object) -> BBox | None:
    tupla = _tupla(valore)
    if tupla is None:
        return None
    if len(tupla) != 4:
        raise ValueError("a bbox needs four numbers")
    return cast(BBox, tupla)


def _colore(valore: object) -> RGBAColor | None:
    tupla = _tupla(valore)
    if tupla is None:
        return None
    if len(tupla) != 4:
        raise ValueError("a colour needs four components")
    return cast(RGBAColor, tupla)


def _punto(valore: object) -> Point | None:
    tupla = _tupla(valore)
    if tupla is None:
        return None
    if len(tupla) != 2:
        raise ValueError("a point needs two numbers")
    return cast(Point, tupla)


def _chiavi_ammesse(dato: dict[str, object], ammesse: frozenset[str], dove: str) -> None:
    """Una chiave sconosciuta e' un errore, non qualcosa da ignorare.

    Un artefatto scritto da una versione futura non si legge a meta': lo si
    rifiuta, e chi legge se ne accorge invece di ottenere una cattura monca.
    """

    inattese = set(dato) - ammesse
    if inattese:
        raise ValueError(f"{dove}: unexpected keys {sorted(inattese)}")


_GEOMETRIA = frozenset({"width", "height", "unit", "coordinate_system"})
_ERRORE = frozenset({"code", "message", "observation_id", "recoverable"})
_TESTO = frozenset({
    "observation_id", "bbox", "text", "font_name", "font_size", "font_flags",
    "color", "direction",
})
_IMMAGINE = frozenset({
    "observation_id", "bbox", "resource_ref", "content_digest", "pixel_width",
    "pixel_height", "placement_transform", "has_alpha", "has_stored_resource",
})
_COMANDO = frozenset({"kind", "points", "bbox", "orientation"})
_DISEGNO = frozenset({
    "observation_id", "bbox", "commands", "stroke_width", "stroke_color",
    "fill_color", "stroke_opacity", "fill_opacity", "is_closed",
})
_COLLEGAMENTO = frozenset({
    "observation_id", "bbox", "target_kind", "uri", "target_page_index",
    "named_destination",
})
_ANNOTAZIONE = frozenset({"observation_id", "bbox", "annotation_kind", "content"})
_CATTURA = frozenset({
    "serialization_schema", "schema_version", "capture_id", "backend_name",
    "backend_version", "source_id", "page_id", "page_index", "page_geometry",
    "source_rotation_degrees", "crop_box", "media_box", "text_observations",
    "image_observations", "drawing_observations", "link_observations",
    "annotation_observations", "backend_order_kind", "backend_order", "errors",
})


def backend_page_capture_to_dict(capture: BackendPageCapture) -> dict[str, object]:
    """Una cattura in dizionario JSON-safe e deterministico."""

    if not isinstance(capture, BackendPageCapture):
        raise ValueError("capture must be a BackendPageCapture")

    return {
        "serialization_schema": CAPTURE_SERIALIZATION_SCHEMA,
        "schema_version": capture.schema_version,
        "capture_id": capture.capture_id,
        "backend_name": capture.backend_name,
        "backend_version": capture.backend_version,
        "source_id": capture.source_id,
        "page_id": capture.page_id,
        "page_index": capture.page_index,
        "page_geometry": {
            "width": capture.page_geometry.width,
            "height": capture.page_geometry.height,
            "unit": capture.page_geometry.unit,
            "coordinate_system": capture.page_geometry.coordinate_system,
        },
        "source_rotation_degrees": capture.source_rotation_degrees,
        "crop_box": list(capture.crop_box) if capture.crop_box else None,
        "media_box": list(capture.media_box) if capture.media_box else None,
        "text_observations": [
            {
                "observation_id": o.observation_id,
                "bbox": list(o.bbox),
                "text": o.text,
                "font_name": o.font_name,
                "font_size": o.font_size,
                "font_flags": o.font_flags,
                "color": list(o.color) if o.color else None,
                "direction": list(o.direction) if o.direction else None,
            }
            for o in capture.text_observations
        ],
        "image_observations": [
            {
                "observation_id": o.observation_id,
                "bbox": list(o.bbox),
                "resource_ref": o.resource_ref,
                "content_digest": o.content_digest,
                "pixel_width": o.pixel_width,
                "pixel_height": o.pixel_height,
                "placement_transform": (
                    list(o.placement_transform) if o.placement_transform else None
                ),
                "has_alpha": o.has_alpha,
                "has_stored_resource": o.has_stored_resource,
            }
            for o in capture.image_observations
        ],
        "drawing_observations": [
            {
                "observation_id": o.observation_id,
                "bbox": list(o.bbox),
                "commands": [
                    {
                        "kind": c.kind,
                        "points": [list(p) for p in c.points],
                        "bbox": list(c.bbox) if c.bbox else None,
                        "orientation": c.orientation,
                    }
                    for c in o.commands
                ],
                "stroke_width": o.stroke_width,
                "stroke_color": list(o.stroke_color) if o.stroke_color else None,
                "fill_color": list(o.fill_color) if o.fill_color else None,
                "stroke_opacity": o.stroke_opacity,
                "fill_opacity": o.fill_opacity,
                "is_closed": o.is_closed,
            }
            for o in capture.drawing_observations
        ],
        "link_observations": [
            {
                "observation_id": o.observation_id,
                "bbox": list(o.bbox),
                "target_kind": o.target_kind,
                "uri": o.uri,
                "target_page_index": o.target_page_index,
                "named_destination": o.named_destination,
            }
            for o in capture.link_observations
        ],
        "annotation_observations": [
            {
                "observation_id": o.observation_id,
                "bbox": list(o.bbox),
                "annotation_kind": o.annotation_kind,
                "content": o.content,
            }
            for o in capture.annotation_observations
        ],
        "backend_order_kind": capture.backend_order_kind,
        "backend_order": list(capture.backend_order),
        "errors": [
            {
                "code": e.code,
                "message": e.message,
                "observation_id": e.observation_id,
                "recoverable": e.recoverable,
            }
            for e in capture.errors
        ],
    }


def _oggetti(dato: dict[str, object], chiave: str) -> list[dict[str, object]]:
    valore = dato.get(chiave, [])
    if not isinstance(valore, list):
        raise ValueError(f"{chiave} must be a list")
    for voce in cast("list[Any]", valore):
        if not isinstance(voce, dict):
            raise ValueError(f"{chiave} must contain objects")
    return cast("list[dict[str, object]]", valore)


def backend_page_capture_from_dict(dato: dict[str, object]) -> BackendPageCapture:
    """Ricostruisce una cattura. Il round-trip e' senza perdita."""

    if not isinstance(dato, dict):
        raise ValueError("data must be a dict")
    _chiavi_ammesse(dato, _CATTURA, "capture")
    schema = dato.get("serialization_schema")
    if schema is not None and schema != CAPTURE_SERIALIZATION_SCHEMA:
        raise ValueError(f"unsupported serialization schema: {schema!r}")

    geometria = dato.get("page_geometry")
    if not isinstance(geometria, dict):
        raise ValueError("page_geometry must be an object")
    _chiavi_ammesse(cast("dict[str, object]", geometria), _GEOMETRIA, "page_geometry")

    for voce in _oggetti(dato, "text_observations"):
        _chiavi_ammesse(voce, _TESTO, "text_observations")
    for voce in _oggetti(dato, "image_observations"):
        _chiavi_ammesse(voce, _IMMAGINE, "image_observations")
    for voce in _oggetti(dato, "drawing_observations"):
        _chiavi_ammesse(voce, _DISEGNO, "drawing_observations")
        for comando in _oggetti(voce, "commands"):
            _chiavi_ammesse(comando, _COMANDO, "commands")
    for voce in _oggetti(dato, "link_observations"):
        _chiavi_ammesse(voce, _COLLEGAMENTO, "link_observations")
    for voce in _oggetti(dato, "annotation_observations"):
        _chiavi_ammesse(voce, _ANNOTAZIONE, "annotation_observations")
    for voce in _oggetti(dato, "errors"):
        _chiavi_ammesse(voce, _ERRORE, "errors")

    return BackendPageCapture(
        schema_version=cast(str, dato["schema_version"]),
        capture_id=cast(str, dato["capture_id"]),
        backend_name=cast(str, dato["backend_name"]),
        backend_version=cast(str, dato["backend_version"]),
        source_id=cast(str, dato["source_id"]),
        page_id=cast(str, dato["page_id"]),
        page_index=cast(int, dato["page_index"]),
        page_geometry=PageGeometry(
            width=float(cast(float, geometria["width"])),
            height=float(cast(float, geometria["height"])),
            unit=cast(Any, geometria["unit"]),
            coordinate_system=cast(Any, geometria["coordinate_system"]),
        ),
        source_rotation_degrees=cast(Any, dato.get("source_rotation_degrees", 0)),
        crop_box=_bbox(dato.get("crop_box")),
        media_box=_bbox(dato.get("media_box")),
        text_observations=tuple(
            BackendTextObservation(
                observation_id=cast(str, o["observation_id"]),
                bbox=cast(BBox, _bbox(o["bbox"])),
                text=cast(str, o["text"]),
                font_name=cast("str | None", o.get("font_name")),
                font_size=cast("float | None", o.get("font_size")),
                font_flags=cast("int | None", o.get("font_flags")),
                color=_colore(o.get("color")),
                direction=_punto(o.get("direction")),
            )
            for o in _oggetti(dato, "text_observations")
        ),
        image_observations=tuple(
            BackendImageObservation(
                observation_id=cast(str, o["observation_id"]),
                bbox=cast(BBox, _bbox(o["bbox"])),
                resource_ref=cast("str | None", o.get("resource_ref")),
                content_digest=cast("str | None", o.get("content_digest")),
                pixel_width=cast("int | None", o.get("pixel_width")),
                pixel_height=cast("int | None", o.get("pixel_height")),
                placement_transform=cast(
                    Any, _tupla(o.get("placement_transform"))
                ),
                has_alpha=cast("bool | None", o.get("has_alpha")),
                has_stored_resource=cast("bool | None", o.get("has_stored_resource")),
            )
            for o in _oggetti(dato, "image_observations")
        ),
        drawing_observations=tuple(
            BackendDrawingObservation(
                observation_id=cast(str, o["observation_id"]),
                bbox=cast(BBox, _bbox(o["bbox"])),
                commands=tuple(
                    DrawingCommand(
                        kind=cast(str, c["kind"]),
                        points=tuple(
                            cast(Point, _punto(p))
                            for p in cast("list[Any]", c.get("points", []))
                        ),
                        bbox=_bbox(c.get("bbox")),
                        orientation=cast("int | None", c.get("orientation")),
                    )
                    for c in _oggetti(o, "commands")
                ),
                stroke_width=cast("float | None", o.get("stroke_width")),
                stroke_color=_colore(o.get("stroke_color")),
                fill_color=_colore(o.get("fill_color")),
                stroke_opacity=cast("float | None", o.get("stroke_opacity")),
                fill_opacity=cast("float | None", o.get("fill_opacity")),
                is_closed=cast("bool | None", o.get("is_closed")),
            )
            for o in _oggetti(dato, "drawing_observations")
        ),
        link_observations=tuple(
            BackendLinkObservation(
                observation_id=cast(str, o["observation_id"]),
                bbox=cast(BBox, _bbox(o["bbox"])),
                target_kind=cast(Any, o["target_kind"]),
                uri=cast("str | None", o.get("uri")),
                target_page_index=cast("int | None", o.get("target_page_index")),
                named_destination=cast("str | None", o.get("named_destination")),
            )
            for o in _oggetti(dato, "link_observations")
        ),
        annotation_observations=tuple(
            BackendAnnotationObservation(
                observation_id=cast(str, o["observation_id"]),
                bbox=cast(BBox, _bbox(o["bbox"])),
                annotation_kind=cast(str, o["annotation_kind"]),
                content=cast("str | None", o.get("content")),
            )
            for o in _oggetti(dato, "annotation_observations")
        ),
        backend_order_kind=cast(Any, dato.get("backend_order_kind")),
        backend_order=tuple(
            cast(str, voce) for voce in cast("list[Any]", dato.get("backend_order", []))
        ),
        errors=tuple(
            CaptureError(
                code=cast(str, e["code"]),
                message=cast(str, e["message"]),
                observation_id=cast("str | None", e.get("observation_id")),
                recoverable=cast(bool, e.get("recoverable", True)),
            )
            for e in _oggetti(dato, "errors")
        ),
    )
