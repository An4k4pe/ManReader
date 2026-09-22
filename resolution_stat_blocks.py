"""Le schede risolte: il confine dal riquadro disegnato, l'identità dalla policy.

`Criterio_RiquadriNelConsumer_v1.md`. Parallelo a `resolve_page_candidates`, sul
precedente di `resolution_column_boundaries.py` (Milestone 43): quello decide un
esito per candidato e non produce regioni nuove; questo produce regioni.

**La regola.** I riquadri disegnati della pagina si spezzano nei loro massimali
con `split_frame`. Un pezzo **delimita una scheda** se contiene **per intero**
almeno una proposta di scheda che il consumer ha accettato; allora l'area della
scheda è il pezzo, con tutte le righe che ci cadono dentro. Fra due pezzi che
delimitano e stanno uno dentro l'altro vince il più grande. Le proposte accettate
che nessun pezzo contiene per intero restano schede da sole.

**Il riquadro dà il confine, non l'identità.** Un riquadro senza una scheda
accettata dentro resta quello che è: lo stesso fondo fa anche da box di regole,
ed è così che AZIONI e ATTRIBUTI DEI PNG passavano per schede (giudizio
dell'utente, 12 settembre: «può essere un elemento, ma non lo userei come unico
discriminante»).

**Il riquadro non si allunga nell'altra colonna** (v2,
`Criterio_RiquadriNelConsumer_v2.md`). Un pezzo non delimita una scheda se,
all'altezza della scheda, scavalca un corridoio fra colonne che la scheda stessa
non scavalca. Su DB idx 92 un pannello `(54,117)-(550,382)` attraversa le due
colonne, contiene la scheda del grifone a sinistra, e la v1 ci aveva inghiottito
la tabella degli attacchi a destra. La forma semplice — «non attraversa un
corridoio» — non va: `column_band` ammette corridoi larghi un punto dentro le
schede di Daggerheart, dove si allineano i rientri, e le scarterebbe.

**Per intero, e per questo.** Su Dragonbane la pergamena della scheda è raster —
esclusa, perché un'immagine è un'illustrazione e non un riquadro — e l'unico
riquadro disegnato vicino è il filetto sotto `Ferocia: 1 Taglia: Enorme`, che
contiene una riga sola delle due. Senza la condizione il gigante di DB idx 90 si
restringerebbe a quella riga. Un riquadro può allargare una scheda, mai
restringerla.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from geometry_model import BBox
from page_analysis_co_reference_binding import BoundCoReferencedPageAnalyses
from page_analysis_column_band import column_band_gutter_rows
from page_analysis_model import RegionCandidate
from page_analysis_stat_block import source_lines_of_page
from primitive_model import TextPrimitive
from resolution_model import ResolvedPageCandidates
from stat_block_regions import FrameInput, centre_inside, contains_box, line_bbox, split_frame

_STAT_BLOCK_PRODUCER_NAME = "page_analysis.stat_block"
_FRAME_PRODUCER_NAMES = frozenset(
    {"page_analysis.interior_visual_frame", "page_analysis.embedded_visual"}
)


@dataclass(frozen=True, slots=True)
class ResolvedStatBlock:
    """Una scheda della pagina, com'è dopo la Resolution.

    ``primitive_ids`` sono le primitive di testo della scheda. ``frame_bbox`` è
    il pezzo di riquadro che la delimita, ``None`` se nessun riquadro la contiene
    per intero e l'area è la sola proposta."""

    bbox: BBox
    primitive_ids: tuple[str, ...]
    field_candidate_ids: tuple[str, ...]
    frame_bbox: BBox | None


def _drawn_frames(bound: BoundCoReferencedPageAnalyses) -> list[FrameInput]:
    """I candidati di riquadro fatti **solo** di primitive vettoriali."""

    drawing_ids = {p.primitive_id for p in bound.primitive_page.drawing_primitives}
    return [
        FrameInput(
            candidate_id=candidate.candidate_id,
            bbox=candidate.bbox,
            primitive_ids=candidate.primitive_ids,
        )
        for analysis in bound.co_referenced_page_analyses.analyses
        if analysis.provenance.producer_name in _FRAME_PRODUCER_NAMES
        for candidate in analysis.candidates
        if candidate.primitive_ids
        and all(pid in drawing_ids for pid in candidate.primitive_ids)
    ]


def _accepted_stat_blocks(
    bound: BoundCoReferencedPageAnalyses, resolved: ResolvedPageCandidates
) -> list[RegionCandidate]:
    accettati = {
        outcome.candidate_reference.candidate_id
        for outcome in resolved.outcomes
        if outcome.outcome == "accepted"
        and outcome.candidate_reference.producer_name == _STAT_BLOCK_PRODUCER_NAME
    }
    return [
        candidate
        for analysis in bound.co_referenced_page_analyses.analyses
        if analysis.provenance.producer_name == _STAT_BLOCK_PRODUCER_NAME
        for candidate in analysis.candidates
        if candidate.candidate_id in accettati
    ]


def _lines_of(candidate: RegionCandidate, lines: Sequence[Sequence[TextPrimitive]]) -> set[int]:
    suoi = set(candidate.primitive_ids)
    return {i for i, riga in enumerate(lines) if any(p.primitive_id in suoi for p in riga)}


def _reaches_the_other_column(
    scheda: BBox,
    righe_del_pezzo: Sequence[BBox],
    corridoi: Sequence[tuple[float, float, float, float]],
) -> bool:
    """All'altezza della scheda, il pezzo ha TESTO dall'altra parte di un
    corridoio che la scheda non scavalca: si allunga nell'altra colonna.

    **Conta il contenuto, non il bordo** (v3,
    `Criterio_RiquadriNelConsumer_v3.md`). La v2 guardava dove passava il bordo
    del riquadro, e su Dag idx 214 scartava tre schede vere: il corridoio
    ammesso a x 322-324 e' lo spazio fra il bordo sinistro dei riquadri e il
    testo dentro, quindi il bordo lo scavalca ma dall'altra parte non c'e'
    niente. Il pannello del grifone di DB idx 92 dall'altra parte ha invece la
    tabella degli attacchi."""

    for x0, y0, x1, y1 in corridoi:
        if not (scheda[1] < y1 and scheda[3] > y0):
            continue
        if scheda[0] < x0 and scheda[2] > x1:
            continue  # la scheda stessa lo scavalca: non separa niente
        if scheda[2] <= x0:
            altra_parte = [r for r in righe_del_pezzo if (r[0] + r[2]) / 2 >= x1]
        elif scheda[0] >= x1:
            altra_parte = [r for r in righe_del_pezzo if (r[0] + r[2]) / 2 <= x0]
        else:
            continue  # la scheda sta dentro il corridoio: non c'e' un'altra parte
        if altra_parte:
            return True
    return False


def resolve_stat_blocks(
    bound: BoundCoReferencedPageAnalyses, resolved: ResolvedPageCandidates
) -> tuple[ResolvedStatBlock, ...]:
    """Le schede della pagina, dal riquadro quando c'è, dalla proposta altrimenti."""

    if not isinstance(bound, BoundCoReferencedPageAnalyses):
        raise ValueError("bound must be a BoundCoReferencedPageAnalyses")

    accettate = _accepted_stat_blocks(bound, resolved)
    if not accettate:
        return ()

    righe = source_lines_of_page(bound.primitive_page)
    corridoi = [
        (float(g["x0"]), float(g["y0"]), float(g["x1"]), float(g["y1"]))  # type: ignore[arg-type]
        for g in column_band_gutter_rows(bound.primitive_page)
        if g["reject_reason"] is None
    ]
    bbox_di = {c.candidate_id: c.bbox for c in accettate}
    riquadri_righe = [line_bbox(riga) for riga in righe]
    righe_di = {c.candidate_id: _lines_of(c, righe) for c in accettate}
    visual_boxes = {
        p.primitive_id: p.bbox
        for p in (*bound.primitive_page.drawing_primitives, *bound.primitive_page.image_primitives)
    }

    def dentro(pezzo: BBox) -> set[int]:
        return {
            i
            for i, riquadro in enumerate(riquadri_righe)
            if riquadro is not None and centre_inside(pezzo, riquadro)
        }

    # 1. i pezzi dei riquadri disegnati, senza doppioni
    pezzi: list[BBox] = []
    for frame in _drawn_frames(bound):
        for pezzo in split_frame(frame, visual_boxes, riquadri_righe):
            if pezzo not in pezzi:
                pezzi.append(pezzo)

    # 2. quelli che contengono PER INTERO una scheda accettata
    delimitano: list[tuple[BBox, set[int], tuple[str, ...]]] = []
    for pezzo in pezzi:
        sue = dentro(pezzo)
        righe_del_pezzo = [
            riquadro
            for i in sorted(sue)
            if (riquadro := riquadri_righe[i]) is not None
        ]
        contenute = tuple(
            c.candidate_id
            for c in accettate
            if righe_di[c.candidate_id]
            and righe_di[c.candidate_id] <= sue
            and not _reaches_the_other_column(
                bbox_di[c.candidate_id], righe_del_pezzo, corridoi
            )
        )
        if contenute:
            delimitano.append((pezzo, sue, contenute))

    # 3. i massimali: un pezzo che delimita dentro un altro che delimita cede
    tenuti = [
        voce
        for voce in delimitano
        if not any(
            altra[0] != voce[0] and contains_box(altra[0], voce[0]) for altra in delimitano
        )
    ]

    schede: list[ResolvedStatBlock] = []
    coperte: set[str] = set()
    for pezzo, sue, contenute in tenuti:
        coperte.update(contenute)
        schede.append(
            ResolvedStatBlock(
                bbox=pezzo,
                primitive_ids=tuple(p.primitive_id for i in sorted(sue) for p in righe[i]),
                field_candidate_ids=contenute,
                frame_bbox=pezzo,
            )
        )
    # 4. le proposte che nessun riquadro contiene per intero restano da sole
    for candidate in accettate:
        if candidate.candidate_id in coperte:
            continue
        schede.append(
            ResolvedStatBlock(
                bbox=candidate.bbox,
                primitive_ids=candidate.primitive_ids,
                field_candidate_ids=(candidate.candidate_id,),
                frame_bbox=None,
            )
        )
    return tuple(sorted(schede, key=lambda s: (s.bbox[1], s.bbox[0])))
