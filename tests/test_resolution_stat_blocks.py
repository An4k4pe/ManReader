"""Le schede risolte: il riquadro disegnato ne dà il confine, mai l'identità.

Metà controlli negativi, e sono quelli che contano: un riquadro che contiene
solo metà scheda non la restringe (il filetto sotto `Ferocia` su DB idx 90), un
riquadro raster non è un riquadro, un riquadro senza scheda accettata dentro non
diventa una scheda (i box di regole).
"""

from __future__ import annotations

import unittest

from document_stat_block_policy import StatBlockFields
from page_analysis_co_reference import build_co_referenced_page_analyses
from page_analysis_co_reference_binding import bind_co_referenced_page_analyses
from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionCandidate,
)
from page_analysis_stat_block import build_stat_block_page_analysis
from primitive_model import (
    DrawingPrimitive,
    ImageOccurrencePrimitive,
    NormalizedPrimitivePage,
    PageGeometry,
    TextPrimitive,
)
from resolution_page_candidates import resolve_page_candidates
from resolution_stat_blocks import resolve_stat_blocks

FEROCIA = frozenset({"ferocia", "taglia"})
CON_FEROCIA = StatBlockFields(frozenset({FEROCIA}))


def _riga(indice: int, *pezzi: tuple[str, bool]):
    y = 100.0 + indice * 20
    x = 110.0
    out = []
    for numero, (testo, grassetto) in enumerate(pezzi):
        larghezza = 7.0 * max(len(testo), 1)
        out.append(
            TextPrimitive(
                primitive_id=f"primitive:text:text:b0000:l{indice:04d}:s{numero:04d}",
                bbox=(x, y, x + larghezza, y + 10.0),
                text=testo,
                source_observation_id=f"text:b0000:l{indice:04d}:s{numero:04d}",
                font_name="Bold" if grassetto else "Regular",
                font_size=9.0,
            )
        )
        x += larghezza + 4.0
    return out


def _nome():
    return _riga(0, ("GIGANTE", True))


def _campi():
    return _riga(1, ("Ferocia:", True), ("3", False), ("Taglia:", True), ("Enorme", False))


def _tratto():
    return _riga(2, ("Armi: i giganti portano grandi armi.", False))


def _disegno(pid: str, bbox):
    return DrawingPrimitive(primitive_id=pid, bbox=bbox, source_observation_id=f"obs:{pid}")


def _immagine(pid: str, bbox):
    return ImageOccurrencePrimitive(primitive_id=pid, bbox=bbox, source_observation_id=f"obs:{pid}")


def _pagina(righe, disegni=(), immagini=()):
    return NormalizedPrimitivePage(
        schema_version="1.0",
        source_capture_id="capture:1",
        source_id="source:1",
        page_id="page:0001",
        page_index=0,
        page_geometry=PageGeometry(
            width=600.0, height=800.0, unit="pt", coordinate_system="top_left_y_down"
        ),
        capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
        text_primitives=tuple(p for riga in righe for p in riga),
        drawing_primitives=tuple(disegni),
        image_primitives=tuple(immagini),
    )


def _riquadri(pagina, *riquadri):
    """Un'analisi di `interior_visual_frame` con un candidato per riquadro."""
    return PageAnalysis(
        schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        generation_id="gen-1",
        page_id=pagina.page_id,
        provenance=PageAnalysisProvenance(
            source_id=pagina.source_id,
            source_capture_id=pagina.source_capture_id,
            source_page_id=pagina.page_id,
            source_primitive_schema_version=pagina.schema_version,
            producer_name="page_analysis.interior_visual_frame",
            producer_version="0.1",
            configuration_id="test",
        ),
        candidates=tuple(
            RegionCandidate(
                candidate_id=f"candidate:frame:{numero:04d}",
                page_id=pagina.page_id,
                bbox=bbox,
                proposed_structural_kind="layout.interior_visual_frame",
                primitive_ids=(pid,),
            )
            for numero, (pid, bbox) in enumerate(riquadri)
        ),
    )


def _schede(pagina, *riquadri, fields=CON_FEROCIA):
    analisi = [build_stat_block_page_analysis(pagina, generation_id="gen-1")]
    if riquadri:
        analisi.append(_riquadri(pagina, *riquadri))
    bound = bind_co_referenced_page_analyses(
        pagina, co_referenced_page_analyses=build_co_referenced_page_analyses(tuple(analisi))
    )
    return resolve_stat_blocks(bound, resolve_page_candidates(bound, stat_block_fields=fields))


SCHEDA_INTERA = (100.0, 95.0, 500.0, 160.0)  # nome, campi e tratto
SOLO_I_CAMPI = (100.0, 115.0, 500.0, 135.0)  # la riga dei campi e basta
META_SCHEDA = (100.0, 95.0, 500.0, 115.0)  # solo il nome: i campi restano fuori


class RiquadriTest(unittest.TestCase):
    def test_il_riquadro_che_contiene_la_scheda_ne_e_il_confine(self) -> None:
        pagina = _pagina((_nome(), _campi(), _tratto()), disegni=(_disegno("d1", SCHEDA_INTERA),))
        schede = _schede(pagina, ("d1", SCHEDA_INTERA))
        self.assertEqual(len(schede), 1)
        self.assertEqual(schede[0].frame_bbox, SCHEDA_INTERA)
        attese = {p.primitive_id for p in (*_nome(), *_campi(), *_tratto())}
        self.assertEqual(set(schede[0].primitive_ids), attese)

    def test_senza_riquadro_la_scheda_e_la_proposta(self) -> None:
        pagina = _pagina((_nome(), _campi(), _tratto()))
        schede = _schede(pagina)
        self.assertEqual(len(schede), 1)
        self.assertIsNone(schede[0].frame_bbox)
        self.assertEqual(set(schede[0].primitive_ids), {p.primitive_id for p in _campi()})

    def test_un_riquadro_che_non_contiene_tutta_la_scheda_non_la_restringe(self) -> None:
        """Il filetto sotto `Ferocia` su DB idx 90: contiene meta' della scheda."""
        pagina = _pagina((_nome(), _campi(), _tratto()), disegni=(_disegno("d1", META_SCHEDA),))
        schede = _schede(pagina, ("d1", META_SCHEDA))
        self.assertEqual(len(schede), 1)
        self.assertIsNone(schede[0].frame_bbox)
        self.assertEqual(set(schede[0].primitive_ids), {p.primitive_id for p in _campi()})

    def test_un_riquadro_raster_non_e_un_riquadro(self) -> None:
        """La pergamena di Dragonbane e' un'immagine: un'illustrazione, non un confine."""
        pagina = _pagina((_nome(), _campi(), _tratto()), immagini=(_immagine("i1", SCHEDA_INTERA),))
        schede = _schede(pagina, ("i1", SCHEDA_INTERA))
        self.assertEqual(len(schede), 1)
        self.assertIsNone(schede[0].frame_bbox)

    def test_un_riquadro_senza_scheda_accettata_non_diventa_scheda(self) -> None:
        """Il box di regole: il riquadro da' il confine, non l'identita'."""
        pagina = _pagina((_nome(), _campi(), _tratto()), disegni=(_disegno("d1", SCHEDA_INTERA),))
        self.assertEqual(_schede(pagina, ("d1", SCHEDA_INTERA), fields=StatBlockFields(frozenset())), ())

    def test_fra_due_riquadri_annidati_vince_il_piu_grande(self) -> None:
        pagina = _pagina(
            (_nome(), _campi(), _tratto()),
            disegni=(_disegno("d1", SCHEDA_INTERA), _disegno("d2", SOLO_I_CAMPI)),
        )
        schede = _schede(pagina, ("d1", SCHEDA_INTERA), ("d2", SOLO_I_CAMPI))
        self.assertEqual(len(schede), 1)
        self.assertEqual(schede[0].frame_bbox, SCHEDA_INTERA)
