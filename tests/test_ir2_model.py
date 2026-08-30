import unittest

from ir2_model import (
    IR2_SCHEMA_VERSION,
    AssetRefIR2,
    DocumentIR2,
    IR2Provenance,
    NodeIR2,
    PageIR2,
)


def _text_node(node_id: str = "n1", order: int = 0, page_id: str = "page:0001") -> NodeIR2:
    return NodeIR2(
        node_id=node_id,
        order=order,
        kind="text.paragraph",
        primitive_ids=(f"primitive:text:{node_id}",),
        page_ids=(page_id,),
        text="testo",
    )


def _asset() -> AssetRefIR2:
    return AssetRefIR2(
        digest="md5:abc",
        file_name="md5_abc.png",
        bbox=(0.0, 0.0, 10.0, 10.0),
        occurrence_count=1,
        proposed_structural_kind="layout.embedded_visual",
    )


def _item(text: str, marker: str | None) -> NodeIR2:
    return NodeIR2(
        node_id="page:0001:b0001:l0000",
        order=0,
        kind="text.list_item",
        primitive_ids=("primitive:text:i1",),
        page_ids=("page:0001",),
        text=text,
        marker=marker,
    )


class NodeMarkerTest(unittest.TestCase):
    """`Criterio_MarcatorePerPrimitiva_v1.md`: il nodo dice quale testa togliere."""

    def test_accepts_a_marker_that_is_a_prefix_of_the_text(self) -> None:
        self.assertEqual(_item("h Utilizzo.", "h ").marker, "h ")

    def test_rejects_a_marker_that_is_not_a_prefix(self) -> None:
        # Se non e' un prefisso, toglierlo taglierebbe altrove: uno stato che
        # non significa niente non deve essere rappresentabile.
        with self.assertRaises(ValueError):
            _item("h Utilizzo.", "x ")

    def test_rejects_a_marker_on_a_paragraph(self) -> None:
        with self.assertRaises(ValueError):
            NodeIR2(
                node_id="page:0001:b0001:l0000",
                order=0,
                kind="text.paragraph",
                primitive_ids=("primitive:text:p1",),
                page_ids=("page:0001",),
                text="h Prosa",
                marker="h ",
            )

    def test_a_list_item_without_a_marker_is_legal(self) -> None:
        # E' il caso di Fab: la testa c'e' ma non si puo' togliere, e la voce
        # esce col suo carattere invece che mutilata.
        self.assertIsNone(_item("Olivia", None).marker)


class AssetRefIR2Test(unittest.TestCase):
    def test_accepts_a_minimal_asset(self) -> None:
        self.assertEqual(_asset().occurrence_count, 1)

    def test_rejects_a_zero_occurrence_count(self) -> None:
        with self.assertRaises(ValueError):
            AssetRefIR2(digest="d", file_name="f", bbox=(0.0, 0.0, 1.0, 1.0), occurrence_count=0)

    def test_rejects_a_non_namespaced_structural_kind(self) -> None:
        with self.assertRaises(ValueError):
            AssetRefIR2(
                digest="d",
                file_name="f",
                bbox=(0.0, 0.0, 1.0, 1.0),
                occurrence_count=1,
                proposed_structural_kind="embedded_visual",
            )


class NodeIR2Test(unittest.TestCase):
    def test_accepts_a_text_node(self) -> None:
        self.assertEqual(_text_node().kind, "text.paragraph")

    def test_accepts_an_asset_node(self) -> None:
        node = NodeIR2(
            node_id="n1",
            order=0,
            kind="asset.note",
            primitive_ids=("primitive:image:i0",),
            page_ids=("page:0001",),
            asset=_asset(),
        )
        self.assertIsNotNone(node.asset)

    def test_rejects_a_node_carrying_both_text_and_asset(self) -> None:
        with self.assertRaises(ValueError):
            NodeIR2(
                node_id="n1",
                order=0,
                kind="text.paragraph",
                primitive_ids=("p",),
                page_ids=("page:0001",),
                text="testo",
                asset=_asset(),
            )

    def test_rejects_a_node_carrying_neither(self) -> None:
        with self.assertRaises(ValueError):
            NodeIR2(
                node_id="n1",
                order=0,
                kind="text.paragraph",
                primitive_ids=("p",),
                page_ids=("page:0001",),
            )

    def test_rejects_empty_primitive_ids(self) -> None:
        with self.assertRaises(ValueError):
            NodeIR2(
                node_id="n1",
                order=0,
                kind="text.paragraph",
                primitive_ids=(),
                page_ids=("page:0001",),
                text="testo",
            )

    def test_rejects_duplicate_primitive_ids(self) -> None:
        with self.assertRaises(ValueError):
            NodeIR2(
                node_id="n1",
                order=0,
                kind="text.paragraph",
                primitive_ids=("p", "p"),
                page_ids=("page:0001",),
                text="testo",
            )

    def test_accepts_the_three_resolution_values_and_none(self) -> None:
        for value in ("accepted", "rejected", "unresolved", None):
            node = NodeIR2(
                node_id="n1",
                order=0,
                kind="text.paragraph",
                primitive_ids=("p",),
                page_ids=("page:0001",),
                text="t",
                resolution=value,
            )
            self.assertEqual(node.resolution, value)

    def test_rejects_an_invented_resolution_value(self) -> None:
        with self.assertRaises(ValueError):
            NodeIR2(
                node_id="n1",
                order=0,
                kind="text.paragraph",
                primitive_ids=("p",),
                page_ids=("page:0001",),
                text="t",
                resolution="no_candidate",
            )

    def test_accepts_multi_page_provenance(self) -> None:
        node = NodeIR2(
            node_id="n1",
            order=0,
            kind="text.paragraph",
            primitive_ids=("p",),
            page_ids=("page:0001", "page:0002"),
            text="t",
        )
        self.assertEqual(len(node.page_ids), 2)


class PageIR2Test(unittest.TestCase):
    def test_accepts_an_ordered_page(self) -> None:
        page = PageIR2(page_id="page:0001", nodes=(_text_node("a", 0), _text_node("b", 1)))
        self.assertEqual(len(page.nodes), 2)

    def test_rejects_duplicate_node_ids(self) -> None:
        with self.assertRaises(ValueError):
            PageIR2(page_id="page:0001", nodes=(_text_node("a", 0), _text_node("a", 1)))

    def test_rejects_a_node_that_does_not_declare_its_page(self) -> None:
        with self.assertRaises(ValueError):
            PageIR2(page_id="page:0002", nodes=(_text_node("a", 0, page_id="page:0001"),))

    def test_rejects_duplicate_order_values(self) -> None:
        with self.assertRaises(ValueError):
            PageIR2(page_id="page:0001", nodes=(_text_node("a", 0), _text_node("b", 0)))

    def test_rejects_a_gap_in_the_order(self) -> None:
        with self.assertRaises(ValueError):
            PageIR2(page_id="page:0001", nodes=(_text_node("a", 0), _text_node("b", 2)))

    def test_accepts_an_empty_page(self) -> None:
        self.assertEqual(PageIR2(page_id="page:0001").nodes, ())


class DocumentIR2Test(unittest.TestCase):
    def test_defaults_to_the_declared_schema_version(self) -> None:
        document = DocumentIR2(provenance=IR2Provenance(source_id="s", generation_id="g"))
        self.assertEqual(document.schema_version, IR2_SCHEMA_VERSION)

    def test_rejects_duplicate_page_ids(self) -> None:
        with self.assertRaises(ValueError):
            DocumentIR2(
                provenance=IR2Provenance(source_id="s", generation_id="g"),
                pages=(PageIR2(page_id="page:0001"), PageIR2(page_id="page:0001")),
            )


if __name__ == "__main__":
    unittest.main()
