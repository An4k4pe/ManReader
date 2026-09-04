"""Massa, pagine e parole per dimensione. `Criterio_TitoliPerFascia_v1.md` §1."""

from __future__ import annotations

import unittest

from document_heading_band_measurements import (
    SAMPLE_TEXTS_PER_SIZE,
    is_word,
    measure_size_mass,
)
from geometry_model import PageGeometry
from primitive_model import NormalizedPrimitivePage, TextPrimitive

GEOMETRIA = PageGeometry(
    width=595.0, height=842.0, unit="pt", coordinate_system="top_left_y_down"
)
IDENTITA = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def _pagina(indice: int, *testi: tuple[str, float | None]) -> NormalizedPrimitivePage:
    return NormalizedPrimitivePage(
        schema_version="1",
        source_capture_id=f"capture:{indice}",
        source_id="source:1",
        page_id=f"page:{indice:04d}",
        page_index=indice,
        page_geometry=GEOMETRIA,
        capture_to_canonical_transform=IDENTITA,
        text_primitives=tuple(
            TextPrimitive(
                primitive_id=f"primitive:text:{indice}:{posizione}",
                bbox=(0.0, float(posizione), 10.0, float(posizione) + 10.0),
                text=testo,
                source_observation_id=f"text:{posizione}",
                font_size=dimensione,
            )
            for posizione, (testo, dimensione) in enumerate(testi)
        ),
    )


class ParolaTest(unittest.TestCase):
    def test_cosa_separa_una_parola_da_un_ornamento(self) -> None:
        for testo in ("Ciao", "AB", "E'"):
            self.assertTrue(is_word(testo), testo)
        # Misurati sul corpus: `'y'` a 172 pt su Fab, `'••'` a 24 pt su Dag,
        # `'2'`/`'3'`/`'4'` a 292 pt su BiD.
        for testo in ("y", "••", "2", "12", "", "  "):
            self.assertFalse(is_word(testo), testo)


class MassaTest(unittest.TestCase):
    def test_conta_i_caratteri_non_le_righe(self) -> None:
        # E' la differenza con `FontSizeMeasurements`, che conta righe: due
        # popolazioni diverse, e i numeri del criterio vengono da questa.
        misura = measure_size_mass([_pagina(0, ("dodici car.", 9.0), ("ab", 9.0))])
        self.assertEqual(misura.characters[9.0], len("dodici car.") + 2)
        self.assertEqual(misura.text_count[9.0], 2)
        self.assertEqual(misura.total_characters, len("dodici car.") + 2)

    def test_le_pagine_si_contano_una_volta_sola(self) -> None:
        misura = measure_size_mass([
            _pagina(0, ("alfa", 9.0), ("beta", 9.0)),
            _pagina(1, ("gamma", 9.0)),
        ])
        self.assertEqual(misura.page_indices[9.0], frozenset({0, 1}))

    def test_la_dimensione_si_arrotonda_al_decimo(self) -> None:
        # Lo stesso `round(..., 1)` di `sized_lines`: e' la precisione con cui il
        # backend riporta il corpo del font, non una soglia.
        misura = measure_size_mass([_pagina(0, ("alfa", 8.97), ("beta", 9.04))])
        self.assertEqual(sorted(misura.characters), [9.0])
        self.assertEqual(misura.characters[9.0], 8)

    def test_lo_spazio_si_normalizza(self) -> None:
        misura = measure_size_mass([_pagina(0, ("  due   parole  ", 9.0))])
        self.assertEqual(misura.characters[9.0], len("due parole"))

    def test_senza_dimensione_o_senza_testo_non_si_conta(self) -> None:
        # Lo zero non si prova perche' `TextPrimitive` lo rifiuta gia' in
        # `__post_init__`: la guardia nella misura copre il solo `None`.
        misura = measure_size_mass([
            _pagina(0, ("niente dimensione", None), ("   ", 9.0))
        ])
        self.assertEqual(misura.characters, {})
        self.assertEqual(misura.total_characters, 0)

    def test_le_parole_si_contano_a_parte_dai_testi(self) -> None:
        misura = measure_size_mass([_pagina(0, ("alfa", 30.0), ("12", 30.0))])
        self.assertEqual(misura.text_count[30.0], 2)
        self.assertEqual(misura.word_count[30.0], 1)


class ChiNonPuoEssereTitoloNonVotaTest(unittest.TestCase):
    """Il parametro del voto. Il meccanismo A di `Criterio_Capolettera_v1.md` e'
    **caduto**, ma il parametro resta ed e' il punto da cui riprenderlo."""

    def test_un_carattere_solo_VOTA_ancora(self) -> None:
        # Il meccanismo A voleva togliergli il voto ed e' caduto: da solo porta
        # la fascia dei nomi di insediamento di Wil dal 33% al 52%, sotto la
        # soglia del 60% che serviva a sbloccarla, e intanto su Fab alza sopra
        # soglia le fasce di prosa da display -- 88 titoli diventano 631, con
        # dentro un paragrafo di 314 caratteri.
        misura = measure_size_mass([
            _pagina(0, ("alfa", 30.0), ("beta", 30.0), ("C", 30.0), ("S", 30.0))
        ])
        self.assertEqual(misura.text_count[30.0], 4)
        self.assertEqual(misura.word_count[30.0], 2)

    def test_l_arredo_non_vota(self) -> None:
        # I folii: su Wil 213 numeri di pagina alla stessa dimensione dei nomi.
        pagina = _pagina(0, ("alfa", 30.0), ("beta", 30.0), ("117", 30.0))
        folio = pagina.text_primitives[2].primitive_id
        misura = measure_size_mass([pagina], excluded_primitive_ids=[frozenset({folio})])
        self.assertEqual(misura.text_count[30.0], 2)
        self.assertEqual(misura.word_count[30.0], 2)

    def test_la_massa_in_caratteri_vede_tutto_lo_stesso(self) -> None:
        # Le esclusioni valgono per il voto, non per la massa: `characters` serve
        # a trovare il corpo e deve continuare a vedere tutto il testo.
        pagina = _pagina(0, ("alfa", 30.0), ("C", 30.0), ("117", 30.0))
        folio = pagina.text_primitives[2].primitive_id
        misura = measure_size_mass([pagina], excluded_primitive_ids=[frozenset({folio})])
        self.assertEqual(misura.characters[30.0], len("alfa") + 1 + 3)
        self.assertEqual(misura.page_indices[30.0], frozenset({0}))

    def test_l_esclusione_e_per_pagina_e_non_globale(self) -> None:
        # Gli id di primitiva non sono unici fra pagine: una lista per pagina.
        uno = _pagina(0, ("alfa", 30.0), ("beta", 30.0))
        due = _pagina(1, ("gamma", 30.0), ("delta", 30.0))
        primo = uno.text_primitives[0].primitive_id
        misura = measure_size_mass(
            [uno, due], excluded_primitive_ids=[frozenset({primo}), frozenset()]
        )
        self.assertEqual(misura.text_count[30.0], 3)

    def test_senza_esclusioni_si_comporta_come_prima(self) -> None:
        pagina = _pagina(0, ("alfa", 30.0), ("beta", 30.0))
        self.assertEqual(
            measure_size_mass([pagina]), measure_size_mass([pagina], excluded_primitive_ids=None)
        )

    def test_gli_esempi_sono_parole_e_hanno_un_tetto(self) -> None:
        pagina = _pagina(0, *[(f"parola{n}", 30.0) for n in range(20)], ("y", 30.0))
        misura = measure_size_mass([pagina])
        self.assertEqual(len(misura.sample_texts[30.0]), SAMPLE_TEXTS_PER_SIZE)
        self.assertNotIn("y", misura.sample_texts[30.0])

    def test_nessuna_pagina_nessuna_misura(self) -> None:
        misura = measure_size_mass([])
        self.assertEqual(misura.characters, {})
        self.assertEqual(misura.total_characters, 0)


if __name__ == "__main__":
    unittest.main()
