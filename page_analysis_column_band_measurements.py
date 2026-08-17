"""Misure satellite pure per i candidati `layout.column_band`.

La misura satellite prevista dal contratto di Milestone 33, e mai scritta fino
al 17 agosto 2026. Stesso pattern di Milestone 7
(`page_analysis_candidate_page_context_measurements`): osserva, non classifica,
non crea artefatti e non persiste nulla.

**Perche' serve, e non e' un accessorio.** Milestone 33 ha scelto
«`RegionCandidate` minimale per banda **piu'** una misura satellite», e ha
registrato come **scartata** l'opzione «piu' `RegionCandidate` senza misura
satellite», con la ragione esplicita che non c'e' modo pulito di portare
`column_count` e i gap senza toccare `structural_kind` o estendere
`RegionCandidate`. Un candidato minimale porta bbox e primitive: un consumer che
debba ordinare per colonne non ha da dove prendere **dove passano i gutter**, e
senza quelli deve ricostruirsi il meccanismo -- cioe' una seconda
implementazione, che su questo progetto e' gia' divergita una volta.

Fino a oggi quel buco era tappato esponendo l'albero interno del producer. Era
un ponte dichiarato, e questo modulo lo sostituisce: da qui in avanti un consumer
ha bisogno di candidati e misure, non delle strutture interne di chi li produce.

**Cosa NON fa**, ed e' la parte che la rende una misura e non una decisione: non
dice quale banda vinca su un'altra, non ordina, non risolve sovrapposizioni. La
gerarchia viene riportata come **fatto osservato** (`parent_candidate_id`,
`depth`), non come istruzione: metterla in relazione e' mestiere di Resolution o
del consumer, mai di chi misura.
"""

from __future__ import annotations

from dataclasses import dataclass

from geometry_model import _validate_non_empty_string
from page_analysis_model import RegionCandidate

_STRUCTURAL_KIND = "layout.column_band"


@dataclass(frozen=True, slots=True)
class ColumnBandMeasurements:
    """Cosa descrive una banda, oltre al suo rettangolo.

    `gutter_x_intervals` sono gli intervalli x dei corridoi **dentro** questa
    banda, ordinati da sinistra: sono la grandezza che un consumer usa per
    dividere la banda in colonne, e l'unica che il candidato minimale non puo'
    portare.

    `column_count` e' `len(gutter_x_intervals) + 1` e viene riportato perche' e'
    la grandezza che Milestone 33 nomina, non perche' aggiunga informazione.
    """

    candidate_id: str
    page_id: str
    column_count: int
    gutter_x_intervals: tuple[tuple[float, float], ...]
    depth: int
    parent_candidate_id: str | None

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.candidate_id, "candidate_id")
        _validate_non_empty_string(self.page_id, "page_id")
        if self.column_count < 1:
            raise ValueError("column_count must be at least 1")
        if self.column_count != len(self.gutter_x_intervals) + 1:
            raise ValueError("column_count must be len(gutter_x_intervals) + 1")
        if self.depth < 0:
            raise ValueError("depth must not be negative")
        previous_end: float | None = None
        for x0, x1 in self.gutter_x_intervals:
            if x1 <= x0:
                raise ValueError("gutter interval must have x1 > x0")
            if previous_end is not None and x0 < previous_end:
                raise ValueError("gutter intervals must be sorted and disjoint")
            previous_end = x1
        if self.parent_candidate_id is not None:
            _validate_non_empty_string(self.parent_candidate_id, "parent_candidate_id")
        if self.depth == 0 and self.parent_candidate_id is not None:
            raise ValueError("a depth-0 band has no parent")
        if self.depth > 0 and self.parent_candidate_id is None:
            raise ValueError("a nested band must name its parent")


def measure_column_bands(
    candidates: tuple[RegionCandidate, ...],
    tree: list[dict[str, object]],
) -> tuple[ColumnBandMeasurements, ...]:
    """Le misure dei candidati `layout.column_band`, una per candidato.

    Prende l'albero da cui i candidati sono stati emessi perche' e' li' che
    vivono i gutter: la misura non li ricalcola e non torna sulle primitive.
    Chi la chiama e' il producer, che ha entrambi.

    I candidati di altro `structural_kind` vengono ignorati in silenzio: e'
    l'unico caso di scarto non etichettato di questo modulo, ed e' un filtro di
    pertinenza, non un'esclusione di contenuto.
    """

    rows_by_band_id = {int(_as_int(row["band_id"])): row for row in tree}
    candidate_id_by_band_id: dict[int, str] = {}
    for candidate in candidates:
        band_id = _band_id_of(candidate)
        if band_id is not None:
            candidate_id_by_band_id[band_id] = candidate.candidate_id

    measurements: list[ColumnBandMeasurements] = []
    for candidate in candidates:
        if candidate.proposed_structural_kind != _STRUCTURAL_KIND:
            continue
        band_id = _band_id_of(candidate)
        row = rows_by_band_id.get(band_id) if band_id is not None else None
        if row is None:
            continue

        gutters = _parse_gutters(str(row.get("gutter_x_intervals") or ""))
        parent = row.get("parent_id")
        parent_candidate_id: str | None = None
        depth = int(_as_int(row["depth"]))
        if parent not in ("", None):
            parent_candidate_id = candidate_id_by_band_id.get(int(_as_int(parent)))
            if parent_candidate_id is None:
                # Il padre esiste nell'albero ma non e' stato emesso come
                # candidato (per esempio perche' non conteneva primitive):
                # la banda diventa osservabilmente di primo livello, e non si
                # inventa un riferimento a qualcosa che nessuno puo' risolvere.
                depth = 0
        measurements.append(
            ColumnBandMeasurements(
                candidate_id=candidate.candidate_id,
                page_id=candidate.page_id,
                column_count=len(gutters) + 1,
                gutter_x_intervals=gutters,
                depth=depth,
                parent_candidate_id=parent_candidate_id if depth > 0 else None,
            )
        )
    return tuple(measurements)


def _band_id_of(candidate: RegionCandidate) -> int | None:
    tail = candidate.candidate_id.rsplit(":", 1)[-1]
    return int(tail) if tail.isdigit() else None


def _as_int(value: object) -> int:
    return int(value)  # type: ignore[arg-type]


def _parse_gutters(raw: str) -> tuple[tuple[float, float], ...]:
    out: list[tuple[float, float]] = []
    for chunk in raw.split():
        start, _, end = chunk.partition("-")
        try:
            out.append((float(start), float(end)))
        except ValueError:
            continue
    return tuple(sorted(out))
