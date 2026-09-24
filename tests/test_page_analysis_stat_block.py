"""Il producer delle schede: che cosa una pagina, da sola, puo' proporre.

Meta' di questi test sono **controlli negativi**: mostrano che la guardia
fallisce quando deve. Le due cose che il producer NON puo' sapere — se il
documento ripete quella combinazione, e se c'e' un riquadro disegnato intorno —
non si provano qui perche' non stanno qui.
"""

from __future__ import annotations

import unittest

from page_analysis_stat_block import (
    build_stat_block_page_analysis,
    declared_field_pairs,
)
from primitive_model import NormalizedPrimitivePage, PageGeometry, TextPrimitive

PAGE = "page:0001"


def _riga(indice: int, *pezzi: tuple[str, bool], y: float | None = None):
    """Una riga di sorgente: coppie (testo, grassetto), stile alternato."""
    y = float(indice * 20) if y is None else y
    x = 10.0
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


def _pagina(*righe):
    return NormalizedPrimitivePage(
        schema_version="1.0",
        source_capture_id="capture:1",
        source_id="source:1",
        page_id=PAGE,
        page_index=0,
        page_geometry=PageGeometry(
            width=600.0, height=800.0, unit="pt", coordinate_system="top_left_y_down"
        ),
        capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
        text_primitives=tuple(p for riga in righe for p in riga),
    )


def _campi(indice):
    return _riga(
        indice, ("Ferocia:", True), ("3", False), ("Taglia:", True), ("Enorme", False)
    )


def _statistiche(indice):
    return _riga(
        indice,
        ("Movimento:", True), ("24", False),
        ("Armatura:", True), ("6", False),
        ("PF:", True), ("84", False),
    )


class CoppieDichiarateTest(unittest.TestCase):
    def test_due_campi_con_i_due_punti_contano(self) -> None:
        self.assertEqual(declared_field_pairs(_campi(0)), 2)

    def test_una_parola_in_grassetto_dentro_la_prosa_non_conta(self) -> None:
        """`label_spans` la chiama etichetta, ma non si dichiara."""
        riga = _riga(
            0, ("l’ha evocata, usando i", False), ("PV", True), ("del suo creatore.", False)
        )
        self.assertEqual(declared_field_pairs(riga), 0)


class ProducerTest(unittest.TestCase):
    def _candidati(self, *righe):
        analysis = build_stat_block_page_analysis(_pagina(*righe), generation_id="g")
        return analysis.candidates

    def test_due_righe_di_campi_fanno_una_scheda(self) -> None:
        candidati = self._candidati(_campi(0), _statistiche(1))
        self.assertEqual(len(candidati), 1)
        self.assertEqual(candidati[0].proposed_structural_kind, "layout.stat_block")

    def test_una_riga_sola_basta(self) -> None:
        """`Criterio_SchedaDaUnaRigaSola_v1.md`: i colossi di Daggerheart
        dichiarano `Soglie: … | Stress: …` su una riga che sta da sola."""
        self.assertEqual(len(self._candidati(_campi(0))), 1)

    def test_una_riga_con_una_coppia_sola_non_basta(self) -> None:
        """Controllo negativo: cambia quante RIGHE servono, non quante coppie.
        «Una coppia per riga» resta rifiutata."""
        riga = _riga(0, ("Movimento:", True), ("24", False))
        self.assertEqual(self._candidati(riga), ())

    def test_una_parola_in_grassetto_senza_due_punti_non_basta(self) -> None:
        """I `TRATTI` delle carte AREA di Wilder — `Meteo Costiero.` — finiscono
        con il punto, non con i due punti, e non sono campi. Visto misurando
        `Criterio_UnaCoppiaPerRiga_v1.md`."""
        riga = _riga(0, ("Meteo Costiero.", True), ("Ogni volta che il branco", False))
        self.assertEqual(self._candidati(riga), ())

    def test_tre_righe_da_un_campo_fanno_una_scheda(self) -> None:
        """Le carte AREA di Wilder: `Sentieri:`, `Mostri:`, `Umani:`, una per
        riga. `Criterio_UnaCoppiaPerRiga_v2.md`."""
        righe = [
            _riga(0, ("Sentieri:", True), ("Baia di Aso, Isola Culla", False)),
            _riga(1, ("Mostri:", True), ("lotangwa, shulu xie", False)),
            _riga(2, ("Umani:", True), ("CSA Sud, Villaggio di Da-o", False)),
        ]
        self.assertEqual(len(self._candidati(*righe)), 1)

    def test_una_cella_con_un_campo_solo_non_e_una_struttura(self) -> None:
        """La colonna CARATTERISTICA delle tabelle delle armi di Daggerheart:
        `Versatile: Quest'arma…` e' un blocco di una etichetta sola."""
        riga = _riga(0, ("Versatile:", True), ("Quest’arma puo' essere usata", False))
        self.assertEqual(self._candidati(riga), ())

    def test_la_prosa_non_propone_niente(self) -> None:
        prosa = _riga(0, ("Una frase intera senza nessun campo dentro.", False))
        altra = _riga(1, ("E una seconda frase, sempre senza campi.", False))
        self.assertEqual(self._candidati(prosa, altra), ())

    def test_il_nome_del_tratto_in_mezzo_resta_dentro(self) -> None:
        """Fra `Ferocia` e `Movimento` la scheda mette il nome di un tratto: se
        uscisse, la scheda si spezzerebbe in due."""
        tratto = _riga(1, ("Immunità", True))
        candidati = self._candidati(_campi(0), tratto, _statistiche(2))
        self.assertEqual(len(candidati), 1)
        self.assertEqual(
            len(candidati[0].primitive_ids),
            len(_campi(0)) + len(tratto) + len(_statistiche(2)),
        )

    def test_due_schede_lontane_sono_due_candidati(self) -> None:
        """Il salto si conta sulle righe presenti, non sui loro numeri: fra le
        due schede ci sono quattro righe di prosa."""
        mezzo = [_riga(i, (f"Riga di prosa numero {i}.", False)) for i in range(2, 6)]
        candidati = self._candidati(
            _campi(0), _statistiche(1), *mezzo, _campi(6), _statistiche(7)
        )
        self.assertEqual(len(candidati), 2)

    def test_poche_righe_in_mezzo_non_separano_due_schede(self) -> None:
        """Controllo negativo del precedente: con una riga sola in mezzo resta
        un candidato solo, ed e' il prezzo dichiarato del raggruppamento."""
        mezzo = _riga(2, ("Una riga sola.", False))
        candidati = self._candidati(
            _campi(0), _statistiche(1), mezzo, _campi(3), _statistiche(4)
        )
        self.assertEqual(len(candidati), 1)

    def test_il_candidato_porta_le_primitive_delle_sue_righe(self) -> None:
        candidati = self._candidati(_campi(0), _statistiche(1))
        attese = {p.primitive_id for p in (*_campi(0), *_statistiche(1))}
        self.assertEqual(set(candidati[0].primitive_ids), attese)

    def test_una_pagina_vuota_non_propone_niente(self) -> None:
        self.assertEqual(build_stat_block_page_analysis(_pagina(), generation_id="g").candidates, ())
