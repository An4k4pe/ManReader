"""Il meccanismo C di `Criterio_Capolettera_v1.md`. Il B e' stato ritirato."""

from __future__ import annotations

import unittest

from document_heading_measurements import sized_lines
from document_heading_policy import LEADER_RUN, has_leader
from geometry_model import PageGeometry
from primitive_model import NormalizedPrimitivePage, TextPrimitive

GEOMETRIA = PageGeometry(
    width=595.0, height=842.0, unit="pt", coordinate_system="top_left_y_down"
)
IDENTITA = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def _riga(*pezzi: tuple[str, float]) -> NormalizedPrimitivePage:
    """Una pagina con una riga sola, fatta dei pezzi dati."""

    return NormalizedPrimitivePage(
        schema_version="1", source_capture_id="c", source_id="s", page_id="page:0001",
        page_index=0, page_geometry=GEOMETRIA, capture_to_canonical_transform=IDENTITA,
        text_primitives=tuple(
            TextPrimitive(
                primitive_id=f"primitive:text:{n}",
                bbox=(float(n) * 10, 0.0, float(n) * 10 + 9, 12.0),
                text=testo,
                source_observation_id=f"text:b0000:l0000:s{n:04d}",
                font_size=dimensione,
            )
            for n, (testo, dimensione) in enumerate(pezzi)
        ),
    )


class DimensioneDellaRigaTest(unittest.TestCase):
    """Il meccanismo B -- la riga alla dimensione che la porta -- e' **ritirato**.

    Curava FWK, dove un capolettera a 58 pt si prendeva la riga del paragrafo e
    diventava il tetto della prosa; ma spostava anche il tetto di Fab (14,0 ->
    10,3, e 88 titoli diventavano 626) e di Wil (10,3 -> 12,9), e per farlo
    toccava `ir2_builder`, che sta sulla strada dell'ordine di lettura.

    Il tetto dalla massa lo rende inutile: un capolettera porta lo 0,00% della
    massa e non e' prosa comunque.
    """

    def test_la_riga_va_ancora_alla_dimensione_massima(self) -> None:
        pagina = _riga(("S", 58.0), ("egue il paragrafo, che e' lungo davvero", 12.0))
        self.assertEqual(sized_lines(pagina)[0].size, 58.0)


class FilettoDiGuidaTest(unittest.TestCase):
    """§3: una voce di sommario non e' un titolo."""

    def test_riconosce_il_filetto(self) -> None:
        for testo in (
            "la struttura del gioco...............................11",
            "stress e trauma.................. 14 corruzione e flagelli",
            "il tempo scorre................ 254 azioni campagna",
        ):
            self.assertTrue(has_leader(testo), testo[:30])

    def test_i_puntini_di_sospensione_NON_sono_un_filetto(self) -> None:
        # Tre e non quattro: e' la ragione per cui la soglia sta a quattro.
        self.assertEqual(LEADER_RUN, 4)
        self.assertFalse(has_leader("Eccetera... e poi si vedra'"))
        self.assertFalse(has_leader("..."))

    def test_un_titolo_vero_non_e_un_filetto(self) -> None:
        for testo in ("PANORAMICA", "◈ villaggio di lala", "CAPITOLO UNO:",
                      "Vali Quanto la Tua Parola: puoi spendere Rep"):
            self.assertFalse(has_leader(testo), testo)

    def test_vale_per_qualunque_carattere_ripetuto(self) -> None:
        self.assertFalse(has_leader("A---B"))
        self.assertTrue(has_leader("A----B"))
        self.assertTrue(has_leader("voce____________12"))

    def test_lo_spazio_e_le_lettere_spezzano_la_corsa(self) -> None:
        self.assertFalse(has_leader(". . . . . ."))
        self.assertFalse(has_leader("a.b.c.d.e."))


if __name__ == "__main__":
    unittest.main()
