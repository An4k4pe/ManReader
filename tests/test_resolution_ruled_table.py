"""La terza regola del consumer: una regione di tabella senza filetti e' un fantasma.

`Criterio_TabellaAFiletti_v1.md`. `table_candidate` trova le colonne dove il testo
si allinea, e su due colonne di prosa con un filetto vede una tabella; qui si
prova che la regione e' accettata solo se contiene una griglia a filetti, e che
senza l'analisi a filetti la regola tace.
"""

from __future__ import annotations

import unittest

from page_analysis_co_reference import build_co_referenced_page_analyses
from page_analysis_co_reference_binding import bind_co_referenced_page_analyses
from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionCandidate,
)
from page_analysis_ruled_table import filled_share
from primitive_model import NormalizedPrimitivePage, PageGeometry, TextPrimitive
from resolution_page_candidates import resolve_page_candidates

REGIONE = (50.0, 100.0, 550.0, 500.0)


def _pagina() -> NormalizedPrimitivePage:
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
        text_primitives=(
            TextPrimitive(
                primitive_id="primitive:text:t1",
                bbox=(60.0, 110.0, 120.0, 120.0),
                text="x",
                source_observation_id="text:b0000:l0000:s0000",
            ),
        ),
    )


def _analisi(pagina, produttore: str, *bbox_list) -> PageAnalysis:
    return PageAnalysis(
        schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        generation_id="gen-1",
        page_id=pagina.page_id,
        provenance=PageAnalysisProvenance(
            source_id=pagina.source_id,
            source_capture_id=pagina.source_capture_id,
            source_page_id=pagina.page_id,
            source_primitive_schema_version=pagina.schema_version,
            producer_name=produttore,
            producer_version="0.1",
            configuration_id="test",
        ),
        candidates=tuple(
            RegionCandidate(
                candidate_id=f"candidate:{produttore}:{numero:04d}",
                page_id=pagina.page_id,
                bbox=bbox,
                proposed_structural_kind="layout.table",
                primitive_ids=(),
            )
            for numero, bbox in enumerate(bbox_list)
        ),
    )


def _esito_della_tabella(*griglie, con_filetti=True):
    pagina = _pagina()
    analisi = [_analisi(pagina, "table_candidate", REGIONE)]
    if con_filetti:
        analisi.append(_analisi(pagina, "page_analysis.ruled_table", *griglie))
    bound = bind_co_referenced_page_analyses(
        pagina, co_referenced_page_analyses=build_co_referenced_page_analyses(tuple(analisi))
    )
    esiti = resolve_page_candidates(bound).outcomes
    return next(
        (o.outcome, o.reason_token)
        for o in esiti
        if o.candidate_reference.producer_name == "table_candidate"
    )


class TabellaAFilettiTest(unittest.TestCase):
    def test_una_griglia_a_filetti_dentro_fa_la_tabella(self) -> None:
        self.assertEqual(_esito_della_tabella((60.0, 120.0, 540.0, 200.0)), ("accepted", None))

    def test_senza_griglia_dentro_la_regione_e_un_fantasma(self) -> None:
        """Dag idx 108: due colonne di prosa, e i filetti non trovano niente."""
        self.assertEqual(_esito_della_tabella(), ("rejected", "not_resolved_by_rules"))

    def test_una_griglia_fuori_dalla_regione_non_conta(self) -> None:
        self.assertEqual(
            _esito_della_tabella((60.0, 600.0, 540.0, 700.0)),
            ("rejected", "not_resolved_by_rules"),
        )

    def test_senza_analisi_a_filetti_la_regola_tace(self) -> None:
        """Il comportamento di prima, per chi non costruisce l'analisi a filetti."""
        self.assertEqual(
            _esito_della_tabella(con_filetti=False), ("unresolved", "no_applicable_rule")
        )


class _Tabella:
    def __init__(self, righe):
        self._righe = righe

    def extract(self):
        return self._righe


class QuotaPieneTest(unittest.TestCase):
    def test_tutte_piene(self) -> None:
        self.assertEqual(filled_share(_Tabella([["a", "b"], ["c", "d"]])), (4, 1.0))

    def test_vuote_e_none_non_contano(self) -> None:
        self.assertEqual(filled_share(_Tabella([["a", ""], [None, " "]])), (4, 0.25))
