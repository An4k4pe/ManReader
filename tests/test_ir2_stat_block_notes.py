"""La nota dello sfondo della scheda: `Criterio_NotaSfondoScheda_v1.md`.

Il campo `AssetRefIR2.stat_block_name` dal modello alla resa: si valida, si
serializza con chiave esatta, arriva dal costruttore e si rende come «sfondo
della scheda NOME». Senza nome la nota resta quella del kind proposto.
"""

from __future__ import annotations

import json
import unittest

from ir2_builder import AssetNoteInput, build_page_ir2
from ir2_markdown import render_asset_note
from ir2_model import (
    KIND_ASSET_NOTE,
    AssetRefIR2,
    DocumentIR2,
    IR2Provenance,
    NodeIR2,
    PageIR2,
)
from ir2_serialization import document_ir2_from_dict, document_ir2_to_dict
from primitive_model import TextPrimitive

PAGE = "page:0030"
# Il riquadro della pergamena del Ragno Gigante, Dragonbane idx 29: 254×94 pt.
BBOX = (79.0, 296.0, 333.0, 390.0)


def _asset(name: str | None = None) -> AssetRefIR2:
    return AssetRefIR2(
        digest="md5:pergamena",
        file_name="md5_pergamena.png",
        bbox=BBOX,
        occurrence_count=1,
        proposed_structural_kind="layout.interior_visual_frame",
        stat_block_name=name,
    )


def _document(asset: AssetRefIR2) -> DocumentIR2:
    node = NodeIR2(
        node_id=f"{PAGE}:primitive:image:a",
        order=0,
        kind=KIND_ASSET_NOTE,
        primitive_ids=("primitive:image:a",),
        page_ids=(PAGE,),
        asset=asset,
        resolution="accepted",
    )
    return DocumentIR2(
        provenance=IR2Provenance(source_id="s", generation_id="g", producer_names=("p",)),
        pages=(PageIR2(page_id=PAGE, nodes=(node,)),),
    )


class StatBlockNameModelTest(unittest.TestCase):
    def test_no_name_is_the_default(self) -> None:
        asset = AssetRefIR2(digest="d", file_name="f", bbox=BBOX, occurrence_count=1)
        self.assertIsNone(asset.stat_block_name)

    def test_an_empty_name_is_refused(self) -> None:
        # Un nome vuoto e' indistinguibile da uno pieno per ogni controllo: si
        # rifiuta qui, come il testo vuoto di un nodo.
        with self.assertRaises(ValueError):
            _asset("")


class StatBlockNameSerializationTest(unittest.TestCase):
    def test_the_name_survives_the_round_trip(self) -> None:
        for name in ("RAGNO GIGANTE", None):
            document = _document(_asset(name))
            payload = json.loads(json.dumps(document_ir2_to_dict(document)))
            self.assertEqual(document_ir2_from_dict(payload), document)

    def test_the_key_is_required(self) -> None:
        # Chiavi esatte, come per `runs`, `heading_level` e `marker`: un file
        # scritto prima del campo non passa per letto a meta'.
        payload = document_ir2_to_dict(_document(_asset("RAGNO GIGANTE")))
        pages = payload["pages"]
        assert isinstance(pages, list)
        asset = pages[0]["nodes"][0]["asset"]
        del asset["stat_block_name"]
        with self.assertRaises(ValueError):
            document_ir2_from_dict(payload)


class StatBlockNameRenderingTest(unittest.TestCase):
    def test_the_note_says_what_it_replaced(self) -> None:
        self.assertEqual(
            render_asset_note(_asset("RAGNO GIGANTE")),
            "> **[sfondo della scheda RAGNO GIGANTE]** 254×94 pt — `md5_pergamena.png`",
        )

    def test_without_a_name_the_note_keeps_the_proposed_kind(self) -> None:
        self.assertEqual(
            render_asset_note(_asset()),
            "> **[riquadro]** 254×94 pt — `md5_pergamena.png`",
        )


class StatBlockNameBuilderTest(unittest.TestCase):
    def test_the_builder_carries_the_name_to_the_asset(self) -> None:
        text = TextPrimitive(
            primitive_id="primitive:text:text:b0001:l0000:s0000",
            bbox=(90.0, 360.0, 200.0, 370.0),
            text="Ferocia: 2",
            source_observation_id="text:b0001:l0000:s0000",
        )
        note = AssetNoteInput(
            primitive_id="primitive:image:a",
            digest="md5:pergamena",
            file_name="md5_pergamena.png",
            bbox=BBOX,
            occurrence_count=1,
            anchor_index=0,
            proposed_structural_kind="layout.interior_visual_frame",
            resolution="accepted",
            stat_block_name="RAGNO GIGANTE",
        )
        page = build_page_ir2(page_id=PAGE, ordered_text_primitives=[text], asset_notes=[note])
        assets = [node.asset for node in page.nodes if node.asset is not None]
        self.assertEqual([asset.stat_block_name for asset in assets], ["RAGNO GIGANTE"])


if __name__ == "__main__":
    unittest.main()
