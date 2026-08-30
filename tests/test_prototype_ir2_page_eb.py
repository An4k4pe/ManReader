"""Il confronto E-B: cosa resta dell'emesso e cosa la resa ha perso.

`Criterio_ConfrontoEB_v4.md`. Le due regole si testano qui e non nel modulo
della resa perche' vivono nello script diagnostico che porta E-B.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for path in (PROJECT_ROOT, PROJECT_ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from prototype_ir2_page import _emitted_content, _lost_in_rendering  # noqa: E402

from ir2_model import NodeIR2, PageIR2, TextRunIR2  # noqa: E402

PAGE = "page:0001"


def _node(order: int, kind: str, text: str, **extra) -> NodeIR2:
    return NodeIR2(
        node_id=f"{PAGE}:n{order}",
        order=order,
        kind=kind,
        primitive_ids=(f"primitive:text:n{order}",),
        page_ids=(PAGE,),
        text=text,
        **extra,
    )


class LostInRenderingTest(unittest.TestCase):
    def test_a_faithful_rendering_loses_nothing(self) -> None:
        self.assertEqual(_lost_in_rendering("**Utilizzo.** Richiede", "Utilizzo. Richiede"), "")

    def test_it_names_the_character_the_rendering_ate(self) -> None:
        # Il difetto di Fab: `- livia` per `Olivia`. Prima nessuno lo guardava,
        # perche' E-B cancellava i marcatori da entrambi i lati.
        self.assertEqual(_lost_in_rendering("livia", "Olivia"), "O")

    def test_whitespace_is_not_content(self) -> None:
        # La resa unisce le righe: gli spazi non si contano da nessuna parte.
        self.assertEqual(_lost_in_rendering("- Una voce", "Una  voce"), "")


class EmittedContentTest(unittest.TestCase):
    """La sintassi che l'emettitore aggiunge non deve arrivare al confronto."""

    def test_it_drops_the_heading_hashes(self) -> None:
        page = PageIR2(
            page_id=PAGE,
            nodes=(_node(0, "text.heading", "Arcanista", heading_level=2),),
        )
        emitted, losses = _emitted_content(page)
        self.assertEqual(emitted, "Arcanista")
        self.assertEqual(losses, [])

    def test_it_drops_the_emphasis_delimiters(self) -> None:
        node = NodeIR2(
            node_id=f"{PAGE}:n0",
            order=0,
            kind="text.paragraph",
            primitive_ids=("primitive:text:n0",),
            page_ids=(PAGE,),
            text="Gli Arcanisti cadono",
            runs=(
                TextRunIR2(text="Gli "),
                TextRunIR2(text="Arcanisti", traits=("bold",)),
                TextRunIR2(text=" cadono"),
            ),
        )
        emitted, _losses = _emitted_content(PageIR2(page_id=PAGE, nodes=(node,)))
        self.assertEqual(emitted, "Gli Arcanisti cadono")

    def test_it_puts_the_declared_marker_back(self) -> None:
        # La base porta il marcatore della sorgente; la resa ci mette `- `.
        page = PageIR2(
            page_id=PAGE,
            nodes=(_node(0, "text.list_item", "* Una voce", marker="* "),),
        )
        emitted, losses = _emitted_content(page)
        self.assertEqual(emitted, "* Una voce")
        self.assertEqual(losses, [])

    def test_an_item_without_a_declared_marker_keeps_its_text_whole(self) -> None:
        page = PageIR2(page_id=PAGE, nodes=(_node(0, "text.list_item", "Olivia"),))
        emitted, losses = _emitted_content(page)
        self.assertEqual(emitted, "Olivia")
        self.assertEqual(losses, [])

    def test_the_furniture_stays_in_the_comparison(self) -> None:
        # `Criterio_ConfrontoEB_v4.md`: togliere l'arredo e' una decisione di
        # RESA, come i `#` e gli `*`, e la base non lo toglie. Confrontarci una
        # resa gia' potata misurerebbe la politica d'arredo invece dell'ordine.
        page = PageIR2(
            page_id=PAGE,
            nodes=(
                _node(0, "text.paragraph", "Capitolo 6"),
                _node(1, "text.paragraph", "Il corpo"),
            ),
        )
        emitted, _losses = _emitted_content(page)
        self.assertEqual(emitted, "Capitolo 6\nIl corpo")


if __name__ == "__main__":
    unittest.main()
