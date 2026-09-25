"""La policy di documento delle schede: quali combinazioni contano.

Meta' controlli negativi: la guardia deve vedersi fallire. Le due condizioni
sono la ripetizione e la posizione, e ognuna si prova da sola.
"""

from __future__ import annotations

import unittest

from document_stat_block_measurements import (
    declared_labels,
    measure_declared_label_counts,
    measure_field_combinations,
)
from document_stat_block_policy import (
    StatBlockFields,
    is_a_scale,
    stat_block_fields,
    stat_block_nuclei,
)
from primitive_model import NormalizedPrimitivePage, PageGeometry, TextPrimitive


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


def _pagina(numero: int, *righe):
    return NormalizedPrimitivePage(
        schema_version="1.0",
        source_capture_id="capture:1",
        source_id="source:1",
        page_id=f"page:{numero:04d}",
        page_index=numero - 1,
        page_geometry=PageGeometry(
            width=600.0, height=800.0, unit="pt", coordinate_system="top_left_y_down"
        ),
        capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
        text_primitives=tuple(p for riga in righe for p in riga),
    )


def _scheda(valore: str = "3"):
    return _riga(0, ("Ferocia:", True), (valore, False), ("Taglia:", True), ("Enorme", False))


def _ammesse(*pagine):
    return stat_block_fields(measure_field_combinations(pagine)).combinations


class EtichetteDichiarateTest(unittest.TestCase):
    def test_i_due_punti_fanno_l_etichetta(self) -> None:
        self.assertEqual(declared_labels(_scheda()), ("ferocia", "taglia"))

    def test_senza_due_punti_non_e_un_campo(self) -> None:
        riga = _riga(0, ("usando i", False), ("PV", True), ("del creatore", False))
        self.assertEqual(declared_labels(riga), ())


class PolicyTest(unittest.TestCase):
    def test_tre_ripetizioni_nello_stesso_posto_ammettono(self) -> None:
        pagine = [_pagina(i + 1, _scheda()) for i in range(3)]
        self.assertEqual(_ammesse(*pagine), frozenset({frozenset({"ferocia", "taglia"})}))

    def test_due_ripetizioni_non_bastano(self) -> None:
        pagine = [_pagina(i + 1, _scheda()) for i in range(2)]
        self.assertEqual(_ammesse(*pagine), frozenset())

    def test_le_etichette_sparse_non_ammettono(self) -> None:
        """Cinque occorrenze, cinque posti: sono i numeri di un D6 dentro le
        celle di una tabella, non una scheda."""
        pagine = [_pagina(i + 1, _scheda("3" * (i + 1))) for i in range(5)]
        self.assertEqual(_ammesse(*pagine), frozenset())

    def test_una_minoranza_spostata_non_toglie_la_combinazione(self) -> None:
        pagine = [_pagina(i + 1, _scheda()) for i in range(4)]
        pagine.append(_pagina(5, _scheda("300000")))
        self.assertEqual(_ammesse(*pagine), frozenset({frozenset({"ferocia", "taglia"})}))

    def test_una_etichetta_sola_non_fa_combinazione(self) -> None:
        riga = _riga(0, ("Movimento:", True), ("24", False))
        self.assertEqual(_ammesse(*[_pagina(i + 1, riga) for i in range(5)]), frozenset())

    def test_un_documento_senza_schede_non_ammette_niente(self) -> None:
        prosa = _riga(0, ("Una frase di prosa, senza campi dentro.", False))
        self.assertEqual(_ammesse(*[_pagina(i + 1, prosa) for i in range(5)]), frozenset())



class NucleiTest(unittest.TestCase):
    """`Criterio_NucleoCheSiContaInsieme_v1.md`: la scheda e' un nucleo di
    etichette dichiarate che il documento conta insieme."""

    def _nuclei(self, *pagine):
        return stat_block_nuclei(measure_declared_label_counts(pagine)).nuclei

    def _carta(self, numero):
        return _pagina(
            numero,
            _riga(0, ("Sentieri:", True), ("Baia di Aso", False)),
            _riga(1, ("Mostri:", True), ("lotangwa", False)),
            _riga(2, ("Umani:", True), ("CSA Sud", False)),
        )

    def test_etichette_contate_insieme_fanno_un_nucleo(self) -> None:
        nuclei = self._nuclei(*[self._carta(i + 1) for i in range(3)])
        self.assertEqual(nuclei, (frozenset({"sentieri", "mostri", "umani"}),))

    def test_un_etichetta_sola_non_fa_un_nucleo(self) -> None:
        """Controllo negativo: la cella `Versatile:` si ripete, ma da sola."""
        cella = _riga(0, ("Versatile:", True), ("Quest’arma", False))
        self.assertEqual(self._nuclei(*[_pagina(i + 1, cella) for i in range(9)]), ())

    def test_il_nome_d_arma_che_cambia_non_rompe_la_scheda(self) -> None:
        """La sirena: il blocco porta `mascella disarticolata`, che cambia a ogni
        creatura, ma porta due etichette del nucleo."""
        fields = StatBlockFields(frozenset(), (frozenset({"difficolta", "soglie", "pf", "att"}),))
        blocco = frozenset({"difficolta", "soglie", "att", "mascelladisarticolata"})
        self.assertTrue(fields.carried_by(blocco))

    def test_un_etichetta_sola_del_nucleo_non_basta(self) -> None:
        """Controllo negativo: una cella con un tratto del nucleo delle armi."""
        fields = StatBlockFields(frozenset(), (frozenset({"versatile", "potente", "pesante"}),))
        self.assertFalse(fields.carried_by(frozenset({"versatile"})))

    def test_senza_nuclei_la_policy_tace(self) -> None:
        self.assertFalse(StatBlockFields(frozenset()).speaks)



class ScalaTest(unittest.TestCase):
    """`Criterio_NucleoCheSiContaInsieme_v2.md`: una scala non e' una struttura."""

    def test_i_ranghi_sono_una_scala(self) -> None:
        """La colonna DANNO delle armi di Dag idx 324: `Rango 1:` … `Rango 4:`."""
        self.assertTrue(is_a_scale(frozenset({"rango1", "rango2", "rango3", "rango4"})))

    def test_i_marcatori_numerati_sono_una_scala(self) -> None:
        """Wilder: `#1:`, `#2:`, `#3:`."""
        self.assertTrue(is_a_scale(frozenset({"#1", "#2", "#3"})))

    def test_i_campi_di_una_scheda_non_sono_una_scala(self) -> None:
        """Controllo negativo: nomi diversi."""
        self.assertFalse(is_a_scale(frozenset({"ferocia", "taglia", "movimento"})))

    def test_gli_esiti_con_nome_non_sono_una_scala(self) -> None:
        """Controllo negativo: BiD — `Fallimento (1-3):`, `Successo Parziale (4/5):`
        hanno un numero, ma radici diverse."""
        self.assertFalse(is_a_scale(frozenset(
            {"fallimento(1-3)", "successoparziale(4/5)", "successopieno(6)"}
        )))
