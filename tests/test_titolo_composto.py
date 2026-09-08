"""Il meccanismo A di `Criterio_TitoloComposto_v1.md`: la sovrastampa."""

from __future__ import annotations

import unittest

from document_heading_measurements import sized_lines
from geometry_model import PageGeometry
from primitive_model import NormalizedPrimitivePage, TextPrimitive

GEOMETRIA = PageGeometry(
    width=595.0, height=842.0, unit="pt", coordinate_system="top_left_y_down"
)
IDENTITA = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def _pagina(*righe: tuple[str, tuple[float, float, float, float], float, int]):
    """Una pagina in cui ogni pezzo dichiara testo, bbox, dimensione e riga."""

    return NormalizedPrimitivePage(
        schema_version="1", source_capture_id="c", source_id="s", page_id="page:0001",
        page_index=0, page_geometry=GEOMETRIA, capture_to_canonical_transform=IDENTITA,
        text_primitives=tuple(
            TextPrimitive(
                primitive_id=f"primitive:text:{n}",
                bbox=bbox,
                text=testo,
                source_observation_id=f"text:b0000:l{riga:04d}:s{n:04d}",
                font_size=dimensione,
            )
            for n, (testo, bbox, dimensione, riga) in enumerate(righe)
        ),
    )


ANGELI = (34.9625, 42.9375, 192.1955, 152.3325)


class SovrastampaTest(unittest.TestCase):
    def test_la_seconda_impressione_non_ripete_il_testo(self) -> None:
        # Su Kul idx 162 la sorgente scrive la stessa parola due volte alla
        # stessa coordinata, e da li' veniva `'ANGELI ANGELI CADUTI CADUTI'`.
        pagina = _pagina(
            ("ANGELI", ANGELI, 85.0, 0),
            ("ANGELI", ANGELI, 85.0, 1),
        )
        righe = [r for r in sized_lines(pagina) if r.text]
        self.assertEqual([r.text for r in righe], ["ANGELI"])

    def test_lo_spazio_in_coda_non_salva_il_duplicato(self) -> None:
        # E' il caso vero: la seconda riga e' la stessa primitiva PIU' uno
        # spazio, quindi le bbox di RIGA non coincidono e quelle di PRIMITIVA
        # si'. E' la ragione per cui il confronto sta fra primitive.
        pagina = _pagina(
            ("ANGELI", ANGELI, 85.0, 0),
            ("ANGELI", ANGELI, 85.0, 1),
            (" ", (192.2939, 69.2895, 203.8939, 143.9355), 85.0, 1),
        )
        righe = [r for r in sized_lines(pagina) if r.text]
        self.assertEqual([r.text for r in righe], ["ANGELI"])

    def test_la_primitiva_duplicata_resta_nella_pagina(self) -> None:
        # Non si scarta, smette solo di contribuire al testo: `AGENTS.MD`
        # §Coverage vuole ogni primitiva coperta da un nodo.
        pagina = _pagina(
            ("ANGELI", ANGELI, 85.0, 0),
            ("ANGELI", ANGELI, 85.0, 1),
        )
        self.assertEqual(len(pagina.text_primitives), 2)

    def test_due_parole_uguali_in_posti_DIVERSI_restano_due(self) -> None:
        # La sovrastampa e' la stessa scatola. Due occorrenze legittime dello
        # stesso testo altrove nella pagina non si toccano.
        altrove = (34.9625, 300.0, 192.1955, 409.4)
        pagina = _pagina(
            ("ANGELI", ANGELI, 85.0, 0),
            ("ANGELI", altrove, 85.0, 1),
        )
        righe = [r for r in sized_lines(pagina) if r.text]
        self.assertEqual([r.text for r in righe], ["ANGELI", "ANGELI"])

    def test_stesso_testo_e_posto_ma_dimensione_diversa_resta(self) -> None:
        pagina = _pagina(
            ("ANGELI", ANGELI, 85.0, 0),
            ("ANGELI", ANGELI, 70.0, 1),
        )
        righe = [r for r in sized_lines(pagina) if r.text]
        self.assertEqual(len(righe), 2)


if __name__ == "__main__":
    unittest.main()
