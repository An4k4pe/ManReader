import unittest

from primitive_model import TextPrimitive
from stat_block_field_lines import (
    field_line_groups,
    field_line_indices,
    opens_a_record,
    recurring_field_combinations,
)
from stat_block_regions import line_facts


def _line(*pezzi, y=0.0):
    """Una riga: coppie (testo, stile) dove lo stile alterna per fare etichetta/valore."""
    primitives = []
    x = 10.0
    for indice, (testo, grassetto) in enumerate(pezzi):
        primitives.append(
            TextPrimitive(
                primitive_id=f"primitive:text:text:b0000:l{int(y):04d}:s{indice:04d}",
                bbox=(x, y, x + 10.0 * len(testo), y + 10.0),
                text=testo,
                source_observation_id=f"text:b0000:l{int(y):04d}:s{indice:04d}",
                font_name="Bold" if grassetto else "Regular",
                font_size=9.0,
            )
        )
        x += 10.0 * len(testo) + 4.0
    return line_facts(primitives)


class ApreUnRecordTest(unittest.TestCase):
    """`Criterio_RigheDellaSchedaACapo_v1.md` §5: dentro una scheda una riga che
    apre un record apre un paragrafo."""

    def test_una_riga_che_comincia_con_un_campo_apre_un_record(self) -> None:
        self.assertTrue(
            opens_a_record(_line(("Ferocia:", True), ("3", False)))
        )

    def test_una_riga_di_continuazione_non_apre_niente(self) -> None:
        """Il testo prima di una parola in grassetto diventa «etichetta» per
        `field_labels`, ma non si dichiara: niente due punti, niente record."""
        self.assertFalse(
            opens_a_record(
                _line(("l’ha evocata, usando i", False), ("PV", True), ("del suo creatore.", False))
            )
        )

    def test_l_etichetta_spezzata_dal_font_apre_lo_stesso(self) -> None:
        """`Canto Incantatore - Azione:` esce dal PDF in tre span, e i due punti
        stanno nel terzo."""
        self.assertTrue(
            opens_a_record(
                _line(("Canto", True), ("Incantato", False), ("re - Azione:", True), ("Spendete", False))
            )
        )

    def test_un_campo_che_non_comincia_la_riga_non_apre_un_record(self) -> None:
        self.assertFalse(
            opens_a_record(_line(("la sirena ha", False), ("Ferocia:", True), ("3", False)))
        )


class CombinazioniTest(unittest.TestCase):
    """`stat_block_field_lines`: la scheda e' una riga con piu' campi insieme."""

    def _scheda(self, y):
        return _line(("Ferocia:", True), ("3", False), ("Taglia:", True), ("Enorme", False), y=y)

    def test_una_combinazione_ripetuta_tre_volte_conta(self) -> None:
        pagine = {i: [self._scheda(0.0)] for i in range(3)}
        self.assertEqual(
            recurring_field_combinations(pagine),
            frozenset({frozenset({"ferocia", "taglia"})}),
        )

    def _scheda_larga(self, y):
        """La stessa combinazione con un valore piu' lungo: `Taglia:` slitta a destra."""
        return _line(
            ("Ferocia:", True), ("300000", False), ("Taglia:", True), ("Enorme", False), y=y
        )

    def test_le_etichette_sparse_non_fanno_combinazione(self) -> None:
        """`Criterio_PosizioneRelativaDeiCampi_v1.md` §2: nessun profilo maggioritario.

        Cinque occorrenze, cinque posti diversi: sono i numeri delle opzioni di un
        D6 dentro le celle della tabella dei tesori di DB, non una scheda."""
        pagine = {
            i: [
                _line(
                    ("Ferocia:", True),
                    ("3" * (i + 1), False),
                    ("Taglia:", True),
                    ("Enorme", False),
                    y=0.0,
                )
            ]
            for i in range(5)
        }
        self.assertEqual(recurring_field_combinations(pagine), frozenset())

    def test_una_minoranza_spostata_non_toglie_la_combinazione(self) -> None:
        """Il filtro sta sulla combinazione, non sulla riga: le creature evocate di
        DB hanno `PF` piu' a sinistra e restano schede."""
        pagine = {i: [self._scheda(0.0)] for i in range(4)}
        pagine[4] = [self._scheda_larga(0.0)]
        self.assertEqual(
            recurring_field_combinations(pagine),
            frozenset({frozenset({"ferocia", "taglia"})}),
        )

    def test_meta_esatta_non_e_maggioranza(self) -> None:
        pagine = {i: [self._scheda(0.0)] for i in range(2)}
        pagine.update({i: [self._scheda_larga(0.0)] for i in (2, 3)})
        self.assertEqual(recurring_field_combinations(pagine), frozenset())

    def test_due_volte_non_bastano(self) -> None:
        pagine = {i: [self._scheda(0.0)] for i in range(2)}
        self.assertEqual(recurring_field_combinations(pagine), frozenset())

    def test_una_etichetta_sola_non_fa_combinazione(self) -> None:
        riga = _line(("Movimento:", True), ("24", False))
        pagine = {i: [riga] for i in range(5)}
        self.assertEqual(recurring_field_combinations(pagine), frozenset())

    def test_la_riga_con_la_combinazione_piu_un_campo_resta_di_campi(self) -> None:
        combinazioni = frozenset({frozenset({"ferocia", "taglia"})})
        riga = _line(("Ferocia:", True), ("3", False), ("Taglia:", True), ("Enorme", False),
                     ("Armatura:", True), ("6", False))
        self.assertEqual(field_line_indices([riga], combinazioni), (0,))

    def test_un_pezzo_solo_della_combinazione_non_basta(self) -> None:
        combinazioni = frozenset({frozenset({"ferocia", "taglia"})})
        riga = _line(("Ferocia:", True), ("3", False))
        self.assertEqual(field_line_indices([riga], combinazioni), ())

    def test_righe_vicine_sono_la_stessa_scheda_lontane_no(self) -> None:
        self.assertEqual(field_line_groups([], (0, 1, 2, 20, 21)), [(0, 1, 2), (20, 21)])
        self.assertEqual(field_line_groups([], (0, 2, 5)), [(0, 2), (5,)])
