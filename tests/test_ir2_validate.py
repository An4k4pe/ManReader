import unittest

from geometry_model import AffineMatrix
from ir2_model import NodeIR2, PageIR2
from ir2_validate import validate_page_ir2_against_primitive_page
from primitive_model import NormalizedPrimitivePage, PageGeometry, TextPrimitive

PAGE = "page:0099"
IDENTITY: AffineMatrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def _primitive(index: int, text: str = "testo") -> TextPrimitive:
    observation = f"text:b{index:04d}:l0000:s0000"
    return TextPrimitive(
        primitive_id=f"primitive:text:{observation}",
        bbox=(0.0, float(index), 10.0, float(index) + 5.0),
        text=text,
        source_observation_id=observation,
    )


def _primitive_page(*primitives: TextPrimitive) -> NormalizedPrimitivePage:
    return NormalizedPrimitivePage(
        schema_version="1.0",
        source_capture_id="capture:1",
        source_id="source:1",
        page_id=PAGE,
        page_index=0,
        page_geometry=PageGeometry(
            width=100.0,
            height=200.0,
            unit="pt",
            coordinate_system="top_left_y_down",
        ),
        capture_to_canonical_transform=IDENTITY,
        text_primitives=primitives,
    )


def _node(order: int, *primitive_ids: str) -> NodeIR2:
    return NodeIR2(
        node_id=f"{PAGE}:n{order}",
        order=order,
        kind="text.paragraph",
        primitive_ids=primitive_ids,
        page_ids=(PAGE,),
        text="testo",
    )


class ValidatePageIR2Test(unittest.TestCase):
    def test_accepts_full_coverage(self) -> None:
        a, b = _primitive(0), _primitive(1)
        page = PageIR2(page_id=PAGE, nodes=(_node(0, a.primitive_id, b.primitive_id),))
        validate_page_ir2_against_primitive_page(page, _primitive_page(a, b))

    def test_rejects_an_uncovered_text_primitive(self) -> None:
        a, b = _primitive(0), _primitive(1)
        page = PageIR2(page_id=PAGE, nodes=(_node(0, a.primitive_id),))
        with self.assertRaises(ValueError):
            validate_page_ir2_against_primitive_page(page, _primitive_page(a, b))

    def test_rejects_an_uncovered_empty_span(self) -> None:
        # Una primitiva senza testo e' comunque una primitiva: lasciarla fuori
        # sarebbe un'esclusione silenziosa.
        a, empty = _primitive(0), _primitive(1, text="")
        page = PageIR2(page_id=PAGE, nodes=(_node(0, a.primitive_id),))
        with self.assertRaises(ValueError):
            validate_page_ir2_against_primitive_page(page, _primitive_page(a, empty))

    def test_rejects_the_same_primitive_in_two_nodes(self) -> None:
        a = _primitive(0)
        page = PageIR2(
            page_id=PAGE,
            nodes=(_node(0, a.primitive_id), _node(1, a.primitive_id)),
        )
        with self.assertRaises(ValueError):
            validate_page_ir2_against_primitive_page(page, _primitive_page(a))

    def test_rejects_a_reference_to_an_unknown_primitive(self) -> None:
        a = _primitive(0)
        page = PageIR2(page_id=PAGE, nodes=(_node(0, a.primitive_id, "primitive:text:ghost"),))
        with self.assertRaises(ValueError):
            validate_page_ir2_against_primitive_page(page, _primitive_page(a))

    def test_rejects_a_page_id_mismatch(self) -> None:
        a = _primitive(0)
        page = PageIR2(page_id="page:0001", nodes=())
        with self.assertRaises(ValueError):
            validate_page_ir2_against_primitive_page(page, _primitive_page(a))

    def test_rejects_wrong_types(self) -> None:
        with self.assertRaises(ValueError):
            validate_page_ir2_against_primitive_page(None, _primitive_page(_primitive(0)))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
