"""La seconda regola del consumer: chi decide se una scheda proposta e' vera.

`page_analysis.stat_block` vede una pagina sola e propone in eccesso. Qui si
prova che la policy del documento accetta le schede e respinge le proposte che
il documento non ripete — e che **senza** policy la regola tace, cioe' il
comportamento di prima non cambia.
"""

from __future__ import annotations

import unittest

from document_stat_block_policy import StatBlockFields
from page_analysis_co_reference import build_co_referenced_page_analyses
from page_analysis_co_reference_binding import bind_co_referenced_page_analyses
from page_analysis_stat_block import build_stat_block_page_analysis
from primitive_model import NormalizedPrimitivePage, PageGeometry, TextPrimitive
from resolution_page_candidates import resolve_page_candidates

FEROCIA = frozenset({"ferocia", "taglia"})


def _riga(indice: int, *pezzi: tuple[str, bool]):
    x = 10.0
    out = []
    for numero, (testo, grassetto) in enumerate(pezzi):
        larghezza = 7.0 * max(len(testo), 1)
        out.append(
            TextPrimitive(
                primitive_id=f"primitive:text:text:b0000:l{indice:04d}:s{numero:04d}",
                bbox=(x, float(indice * 20), x + larghezza, float(indice * 20) + 10.0),
                text=testo,
                source_observation_id=f"text:b0000:l{indice:04d}:s{numero:04d}",
                font_name="Bold" if grassetto else "Regular",
                font_size=9.0,
            )
        )
        x += larghezza + 4.0
    return out


def _pagina(*righe) -> NormalizedPrimitivePage:
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
    )


def _scheda_dragonbane():
    return (
        _riga(0, ("Ferocia:", True), ("3", False), ("Taglia:", True), ("Enorme", False)),
        _riga(1, ("Movimento:", True), ("24", False), ("Armatura:", True), ("6", False)),
    )


def _righe_del_d6():
    """Le righe della tabella dei tesori di DB, nella forma che il producer ha
    visto davvero su idx 123: i due punti stanno dentro lo span dell'etichetta,
    e il valore e' la corsa nell'altro stile."""
    return (
        _riga(
            0,
            ("Tira un D6. 1:", False), ("vetro,", True),
            ("2:", False), ("cristallo,", True),
            ("3:", False), ("smeraldo", True),
        ),
        _riga(
            1,
            ("Tira un D6. 1:", False), ("corda,", True),
            ("2:", False), ("olio,", True),
            ("3:", False), ("torcia", True),
        ),
    )


def _esiti(pagina, fields):
    analisi = build_stat_block_page_analysis(pagina, generation_id="gen-1")
    bound = bind_co_referenced_page_analyses(
        pagina, co_referenced_page_analyses=build_co_referenced_page_analyses((analisi,))
    )
    risolti = resolve_page_candidates(bound, stat_block_fields=fields)
    return [(o.outcome, o.reason_token) for o in risolti.outcomes]


class ConsumerSchedeTest(unittest.TestCase):
    def test_la_scheda_e_accettata(self) -> None:
        pagina = _pagina(*_scheda_dragonbane())
        self.assertEqual(
            _esiti(pagina, StatBlockFields(frozenset({FEROCIA}))), [("accepted", None)]
        )

    def test_la_proposta_che_il_documento_non_ripete_e_respinta(self) -> None:
        pagina = _pagina(*_righe_del_d6())
        self.assertEqual(
            _esiti(pagina, StatBlockFields(frozenset({FEROCIA}))),
            [("rejected", "field_combination_not_recurring")],
        )

    def test_senza_policy_la_regola_tace(self) -> None:
        """Il comportamento di prima: il candidato resta irrisolto."""
        pagina = _pagina(*_scheda_dragonbane())
        self.assertEqual(_esiti(pagina, None), [("unresolved", "no_applicable_rule")])

    def test_una_policy_vuota_respinge_tutto(self) -> None:
        pagina = _pagina(*_scheda_dragonbane())
        self.assertEqual(
            _esiti(pagina, StatBlockFields(frozenset())),
            [("rejected", "field_combination_not_recurring")],
        )

    def test_la_combinazione_piu_un_campo_resta_ammessa(self) -> None:
        """Contenimento e non uguaglianza: la riga porta anche `PF`."""
        riga = _riga(
            0,
            ("Ferocia:", True), ("3", False),
            ("Taglia:", True), ("Enorme", False),
            ("PF:", True), ("84", False),
        )
        pagina = _pagina(riga, _riga(1, ("Movimento:", True), ("24", False), ("Armatura:", True), ("6", False)))
        self.assertEqual(
            _esiti(pagina, StatBlockFields(frozenset({FEROCIA}))), [("accepted", None)]
        )
