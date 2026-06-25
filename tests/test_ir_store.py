import tempfile
import unittest
from pathlib import Path

from ir_model import BlockIR, DocumentIR, PageIR
from ir_store import load_document_ir, save_document_ir


class IRStoreTest(unittest.TestCase):
    def test_preserves_block_role_and_metadata_on_roundtrip(self):
        document = DocumentIR(
            schema_version="1",
            source_path="manual.pdf",
            page_count=1,
            pages=[
                PageIR(
                    id="page-1",
                    page_num=1,
                    blocks=[
                        BlockIR(
                            id="block-1",
                            type="text",
                            page_num=1,
                            order=0,
                            text="Domande",
                            role="question_list",
                            metadata={"marker": "❖"},
                        )
                    ],
                )
            ],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "document_ir.json"

            save_document_ir(document, path)
            loaded = load_document_ir(path)

        block = loaded.pages[0].blocks[0]
        self.assertEqual(block.role, "question_list")
        self.assertEqual(block.metadata, {"marker": "❖"})


if __name__ == "__main__":
    unittest.main()
