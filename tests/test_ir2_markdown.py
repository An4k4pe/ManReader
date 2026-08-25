import unittest

from ir2_markdown import (
    is_rendered_in_body,
    render_asset_note,
    render_document_markdown,
    render_node,
    render_page_markdown,
)
from ir2_model import (
    KIND_TEXT_PARAGRAPH,
    AssetRefIR2,
    DocumentIR2,
    IR2Provenance,
    NodeIR2,
    PageIR2,
    TextRunIR2,
)

PAGE = "page:0099"


def _paragraph(order: int, text: str, node_id: str | None = None) -> NodeIR2:
    return NodeIR2(
        node_id=node_id or f"{PAGE}:b{order:04d}:l0000",
        order=order,
        kind="text.paragraph",
        primitive_ids=(f"primitive:text:p{order}",),
        page_ids=(PAGE,),
        text=text,
    )


def _asset_node(
    order: int, kind: str | None, count: int = 1, resolution: str = "unresolved"
) -> NodeIR2:
    return NodeIR2(
        node_id=f"{PAGE}:i{order:04d}",
        order=order,
        kind="asset.note",
        primitive_ids=(f"primitive:image:i{order}",),
        page_ids=(PAGE,),
        asset=AssetRefIR2(
            digest="md5:abc",
            file_name="md5_abc.jpx",
            bbox=(0.0, 0.0, 621.8, 807.8),
            occurrence_count=count,
            proposed_structural_kind=kind,
        ),
        resolution=resolution,
    )


class RenderAssetNoteTest(unittest.TestCase):
    def test_says_what_it_replaced_and_how_big(self) -> None:
        note = render_asset_note(_asset_node(0, "layout.page_covering_visual").asset)
        self.assertIn("sfondo di pagina", note)
        self.assertIn("622×808 pt", note)
        self.assertIn("md5_abc.jpx", note)

    def test_translates_each_known_kind(self) -> None:
        expected = {
            "layout.page_covering_visual": "sfondo di pagina",
            "layout.page_edge_visual": "elemento di bordo",
            "layout.embedded_visual": "immagine inserita",
            "layout.interior_visual_frame": "riquadro",
        }
        for kind, phrase in expected.items():
            self.assertIn(phrase, render_asset_note(_asset_node(0, kind).asset))

    def test_an_unknown_kind_is_not_guessed_at(self) -> None:
        self.assertIn(
            "immagine non classificata",
            render_asset_note(_asset_node(0, "layout.qualcosa_di_nuovo").asset),
        )

    def test_no_candidate_is_not_guessed_at(self) -> None:
        self.assertIn("immagine non classificata", render_asset_note(_asset_node(0, None).asset))

    def test_reports_repetition_only_when_there_is_some(self) -> None:
        self.assertNotIn("occorrenze", render_asset_note(_asset_node(0, None, count=1).asset))
        self.assertIn("3 occorrenze", render_asset_note(_asset_node(0, None, count=3).asset))


class RenderNodeTest(unittest.TestCase):
    def test_renders_a_paragraph_as_its_text(self) -> None:
        self.assertEqual(render_node(_paragraph(0, "testo")), "testo")

    def test_refuses_a_kind_it_cannot_render(self) -> None:
        node = NodeIR2(
            node_id="n",
            order=0,
            kind="text.heading",
            primitive_ids=("p",),
            page_ids=(PAGE,),
            text="SCHELETRO",
        )
        with self.assertRaises(ValueError):
            render_node(node)


class RenderPageTest(unittest.TestCase):
    def test_emits_nodes_in_order_not_in_tuple_position(self) -> None:
        page = PageIR2(
            page_id=PAGE,
            nodes=(_paragraph(1, "seconda"), _paragraph(0, "prima")),
        )
        self.assertEqual(render_page_markdown(page), "prima\n\nseconda\n")

    def test_separates_blocks_with_a_blank_line(self) -> None:
        page = PageIR2(page_id=PAGE, nodes=(_paragraph(0, "a"), _paragraph(1, "b")))
        self.assertEqual(render_page_markdown(page), "a\n\nb\n")

    def test_an_empty_page_renders_empty(self) -> None:
        self.assertEqual(render_page_markdown(PageIR2(page_id=PAGE)), "")

    def test_interleaves_an_asset_note(self) -> None:
        page = PageIR2(
            page_id=PAGE,
            nodes=(
                _paragraph(0, "prima"),
                _asset_node(1, "layout.embedded_visual", resolution="accepted"),
                _paragraph(2, "dopo"),
            ),
        )
        rendered = render_page_markdown(page)
        self.assertLess(rendered.index("prima"), rendered.index("immagine inserita"))
        self.assertLess(rendered.index("immagine inserita"), rendered.index("dopo"))


class EmissionGateTest(unittest.TestCase):
    """La porta di resa: nel corpo solo cio' che Resolution ha accettato."""

    def _node(self, order: int, resolution: str | None) -> NodeIR2:
        node = _asset_node(order, "layout.embedded_visual")
        return NodeIR2(
            node_id=node.node_id,
            order=node.order,
            kind=node.kind,
            primitive_ids=node.primitive_ids,
            page_ids=node.page_ids,
            asset=node.asset,
            resolution=resolution,
        )

    def test_an_accepted_note_is_rendered(self) -> None:
        self.assertTrue(is_rendered_in_body(self._node(0, "accepted"), render_unresolved=False))

    def test_an_unresolved_note_is_not_rendered(self) -> None:
        self.assertFalse(is_rendered_in_body(self._node(0, "unresolved"), render_unresolved=False))

    def test_a_rejected_note_is_not_rendered(self) -> None:
        self.assertFalse(is_rendered_in_body(self._node(0, "rejected"), render_unresolved=False))

    def test_a_note_without_a_candidate_is_not_rendered(self) -> None:
        self.assertFalse(is_rendered_in_body(self._node(0, None), render_unresolved=False))

    def test_a_paragraph_is_always_rendered(self) -> None:
        self.assertTrue(is_rendered_in_body(_paragraph(0, "testo"), render_unresolved=False))

    def test_the_page_drops_the_unresolved_note_but_keeps_the_text(self) -> None:
        page = PageIR2(
            page_id=PAGE,
            nodes=(_paragraph(0, "prima"), self._node(1, "unresolved"), _paragraph(2, "dopo")),
        )
        rendered = render_page_markdown(page)
        self.assertEqual(rendered, "prima\n\ndopo\n")

    def test_the_flag_puts_them_back(self) -> None:
        page = PageIR2(page_id=PAGE, nodes=(self._node(0, "unresolved"),))
        self.assertEqual(render_page_markdown(page), "")
        self.assertIn(
            "immagine inserita", render_page_markdown(page, render_unresolved_assets=True)
        )

    def test_the_node_survives_even_when_not_rendered(self) -> None:
        # La copertura resta per costruzione: il nodo c'e', non viene reso.
        page = PageIR2(page_id=PAGE, nodes=(self._node(0, "unresolved"),))
        self.assertEqual(len(page.nodes), 1)


class RenderDocumentTest(unittest.TestCase):
    def test_marks_each_page(self) -> None:
        document = DocumentIR2(
            provenance=IR2Provenance(source_id="s", generation_id="g"),
            pages=(PageIR2(page_id=PAGE, nodes=(_paragraph(0, "testo"),)),),
        )
        rendered = render_document_markdown(document)
        self.assertIn("<!-- page: page:0099 -->", rendered)
        self.assertIn("testo", rendered)

    def test_an_empty_document_renders_empty(self) -> None:
        document = DocumentIR2(provenance=IR2Provenance(source_id="s", generation_id="g"))
        self.assertEqual(render_document_markdown(document), "")


if __name__ == "__main__":
    unittest.main()


class RenderRunsTest(unittest.TestCase):
    """`Criterio_UscitaLeggibile_v1.md` A: lo stile inline arriva in uscita."""

    def _node(self, runs):
        return NodeIR2(
            node_id="n",
            order=0,
            kind=KIND_TEXT_PARAGRAPH,
            primitive_ids=("p",),
            page_ids=("page:0001",),
            text="".join(run.text for run in runs),
            runs=tuple(runs),
        )

    def test_without_runs_the_output_is_exactly_the_text(self) -> None:
        node = NodeIR2(
            node_id="n",
            order=0,
            kind=KIND_TEXT_PARAGRAPH,
            primitive_ids=("p",),
            page_ids=("page:0001",),
            text="testo semplice",
        )
        self.assertEqual(render_node(node), "testo semplice")

    def test_bold_and_italic_inside_a_paragraph(self) -> None:
        node = self._node(
            [
                TextRunIR2("Usa il Master. Le regole di ", ("serifed",)),
                TextRunIR2("DIE", ("italic", "serifed")),
                TextRunIR2(" contano.", ("serifed",)),
            ]
        )
        self.assertEqual(render_node(node), "Usa il Master. Le regole di *DIE* contano.")

    def test_bold_and_italic_together(self) -> None:
        node = self._node([TextRunIR2("nota", ("bold", "italic"))])
        self.assertEqual(render_node(node), "***nota***")

    def test_traits_without_a_markdown_form_are_ignored(self) -> None:
        # `serifed`, `monospaced` e `superscript` restano sul nodo e non si
        # rendono: inventargli una resa sarebbe far mentire l'adattatore.
        node = self._node([TextRunIR2("x", ("serifed", "monospaced", "superscript"))])
        self.assertEqual(render_node(node), "x")

    def test_the_junction_space_stays_outside_the_markup(self) -> None:
        node = self._node([TextRunIR2("forte ", ("bold",)), TextRunIR2("piano", ())])
        self.assertEqual(render_node(node), "**forte** piano")
