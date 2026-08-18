import json
import unittest

from ir2_model import (
    AssetRefIR2,
    DocumentIR2,
    IR2Provenance,
    NodeIR2,
    PageIR2,
)
from ir2_serialization import document_ir2_from_dict, document_ir2_to_dict


def _document() -> DocumentIR2:
    text_node = NodeIR2(
        node_id="page:0001:b0000",
        order=0,
        kind="text.paragraph",
        primitive_ids=("primitive:text:text:b0000:l0000:s0000",),
        page_ids=("page:0001",),
        text="Gli scheletri sono resti di umanoidi.",
        candidate_ids=(),
        resolution=None,
    )
    asset_node = NodeIR2(
        node_id="page:0001:i0001",
        order=1,
        kind="asset.note",
        primitive_ids=("primitive:image:image:i0001",),
        page_ids=("page:0001",),
        asset=AssetRefIR2(
            digest="md5:abc",
            file_name="md5_abc.jpx",
            bbox=(1.0, 2.0, 3.0, 4.0),
            occurrence_count=2,
            proposed_structural_kind="layout.embedded_visual",
        ),
        candidate_ids=("candidate:embedded-visual-raster:primitive:image:image:i0001",),
        resolution="unresolved",
    )
    return DocumentIR2(
        provenance=IR2Provenance(
            source_id="source:db",
            generation_id="generation:test",
            producer_names=("embedded_visual",),
        ),
        pages=(PageIR2(page_id="page:0001", nodes=(text_node, asset_node)),),
    )


class RoundTripTest(unittest.TestCase):
    def test_round_trip_preserves_the_document(self) -> None:
        document = _document()
        self.assertEqual(document_ir2_from_dict(document_ir2_to_dict(document)), document)

    def test_round_trip_survives_json(self) -> None:
        document = _document()
        payload = json.loads(json.dumps(document_ir2_to_dict(document)))
        self.assertEqual(document_ir2_from_dict(payload), document)

    def test_round_trip_preserves_an_empty_document(self) -> None:
        document = DocumentIR2(
            provenance=IR2Provenance(source_id="s", generation_id="g"),
        )
        self.assertEqual(document_ir2_from_dict(document_ir2_to_dict(document)), document)


class ValidationOnTheWayInTest(unittest.TestCase):
    def _payload(self) -> dict[str, object]:
        return document_ir2_to_dict(_document())

    def test_rejects_a_missing_key(self) -> None:
        payload = self._payload()
        del payload["schema_version"]
        with self.assertRaises(ValueError):
            document_ir2_from_dict(payload)

    def test_rejects_an_unknown_key(self) -> None:
        payload = self._payload()
        payload["extra"] = 1
        with self.assertRaises(ValueError):
            document_ir2_from_dict(payload)

    def test_rejects_an_unknown_node_key(self) -> None:
        payload = self._payload()
        pages = payload["pages"]
        assert isinstance(pages, list)
        page = pages[0]
        assert isinstance(page, dict)
        nodes = page["nodes"]
        assert isinstance(nodes, list)
        node = nodes[0]
        assert isinstance(node, dict)
        node["role"] = "callout"
        with self.assertRaises(ValueError):
            document_ir2_from_dict(payload)

    def test_rejects_a_non_int_order(self) -> None:
        payload = self._payload()
        pages = payload["pages"]
        assert isinstance(pages, list)
        page = pages[0]
        assert isinstance(page, dict)
        nodes = page["nodes"]
        assert isinstance(nodes, list)
        node = nodes[0]
        assert isinstance(node, dict)
        node["order"] = "0"
        with self.assertRaises(ValueError):
            document_ir2_from_dict(payload)

    def test_rejects_a_bbox_with_three_numbers(self) -> None:
        payload = self._payload()
        pages = payload["pages"]
        assert isinstance(pages, list)
        page = pages[0]
        assert isinstance(page, dict)
        nodes = page["nodes"]
        assert isinstance(nodes, list)
        node = nodes[1]
        assert isinstance(node, dict)
        asset = node["asset"]
        assert isinstance(asset, dict)
        asset["bbox"] = [1.0, 2.0, 3.0]
        with self.assertRaises(ValueError):
            document_ir2_from_dict(payload)

    def test_rejects_a_root_that_is_not_a_dict(self) -> None:
        with self.assertRaises(ValueError):
            document_ir2_from_dict([])

    def test_model_validation_still_applies_after_parsing(self) -> None:
        payload = self._payload()
        pages = payload["pages"]
        assert isinstance(pages, list)
        page = pages[0]
        assert isinstance(page, dict)
        nodes = page["nodes"]
        assert isinstance(nodes, list)
        node = nodes[0]
        assert isinstance(node, dict)
        node["resolution"] = "no_candidate"
        with self.assertRaises(ValueError):
            document_ir2_from_dict(payload)


if __name__ == "__main__":
    unittest.main()
