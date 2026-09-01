import unittest

from document_asset_catalogue import (
    AssetCatalogue,
    AssetCatalogueEntry,
    UncataloguedOccurrence,
    build_asset_catalogue,
    file_stem_for,
)
from document_asset_policy import (
    BELOW_TEXT_SCALE,
    CONTENT,
    NO_STORED_RESOURCE,
    RECURRING,
    AssetDecision,
)


def _decision(
    digest: str,
    destination: str = CONTENT,
    *,
    pages: int = 1,
    occurrences: int = 1,
    extent: float = 100.0,
    stored: bool | None = True,
) -> AssetDecision:
    return AssetDecision(
        digest=digest,
        destination=destination,  # type: ignore[arg-type]
        page_count=pages,
        occurrence_count=occurrences,
        smallest_placed_extent=extent,
        text_scale=8.0,
        has_stored_resource=stored,
    )


class Recorder:
    """Un estrattore e un magazzino finti: il catalogo non deve sapere di piu'."""

    def __init__(self, raster: tuple[bytes, str, str] | None = (b"PNG", "png", "stored")):
        self.raster = raster
        self.extracted: list[str] = []
        self.stored: list[tuple[str, str, bytes]] = []

    def extract(self, digest: str):
        self.extracted.append(digest)
        return self.raster

    def store(self, folder: str, name: str, payload: bytes) -> None:
        self.stored.append((folder, name, payload))


class BuildCatalogueTest(unittest.TestCase):
    def test_a_content_asset_is_extracted_stored_and_noted(self) -> None:
        recorder = Recorder()
        catalogue = build_asset_catalogue(
            decisions=[_decision("md5:art")],
            first_page_index_of={"md5:art": 12},
            extract=recorder.extract,
            store=recorder.store,
        )
        entry = catalogue.entries[0]
        self.assertEqual(entry.folder, "images")
        self.assertEqual(entry.file_name, "md5_art.png")
        self.assertEqual(entry.extraction_method, "stored")
        self.assertEqual(entry.first_page_index, 12)
        self.assertTrue(entry.renders_body_note)
        self.assertEqual(recorder.stored, [("images", "md5_art.png", b"PNG")])

    def test_a_recurring_asset_gets_a_file_but_no_note(self) -> None:
        recorder = Recorder()
        catalogue = build_asset_catalogue(
            decisions=[_decision("md5:bg", RECURRING, pages=40, occurrences=40)],
            first_page_index_of={"md5:bg": 0},
            extract=recorder.extract,
            store=recorder.store,
        )
        entry = catalogue.entries[0]
        self.assertEqual(entry.folder, "assets")
        self.assertIsNotNone(entry.file_name)
        self.assertFalse(entry.renders_body_note)

    def test_a_destination_without_a_folder_is_never_extracted(self) -> None:
        # E' il punto della correzione: un gradiente non ha byte da tirare fuori,
        # e chiederli produrrebbe la fotografia della pagina col testo dentro.
        recorder = Recorder()
        catalogue = build_asset_catalogue(
            decisions=[
                _decision("md5:grad", NO_STORED_RESOURCE, stored=False),
                _decision("md5:rule", BELOW_TEXT_SCALE, extent=1.0),
            ],
            first_page_index_of={"md5:grad": 3, "md5:rule": 4},
            extract=recorder.extract,
            store=recorder.store,
        )
        self.assertEqual(recorder.extracted, [])
        self.assertEqual(recorder.stored, [])
        for entry in catalogue.entries:
            self.assertIsNone(entry.folder)
            self.assertIsNone(entry.file_name)
            self.assertFalse(entry.renders_body_note)

    def test_everything_stays_catalogued_even_without_a_file(self) -> None:
        # AGENTS.MD §Coverage: nessuna esclusione puo' essere silenziosa.
        catalogue = build_asset_catalogue(
            decisions=[
                _decision("md5:art"),
                _decision("md5:grad", NO_STORED_RESOURCE, stored=False),
            ],
            first_page_index_of={"md5:art": 1, "md5:grad": 2},
            extract=Recorder().extract,
            store=Recorder().store,
        )
        self.assertEqual(len(catalogue.entries), 2)
        self.assertIsNotNone(catalogue.by_digest("md5:grad"))

    def test_one_extraction_per_content_not_per_occurrence(self) -> None:
        recorder = Recorder()
        build_asset_catalogue(
            decisions=[_decision("md5:x", pages=1, occurrences=9)],
            first_page_index_of={"md5:x": 0},
            extract=recorder.extract,
            store=recorder.store,
        )
        self.assertEqual(recorder.extracted, ["md5:x"])

    def test_nothing_to_extract_leaves_a_row_without_a_file(self) -> None:
        # Occorrenza interamente fuori pagina: il catalogo dice quello che c'e'.
        recorder = Recorder(raster=None)
        catalogue = build_asset_catalogue(
            decisions=[_decision("md5:offpage")],
            first_page_index_of={"md5:offpage": 0},
            extract=recorder.extract,
            store=recorder.store,
        )
        entry = catalogue.entries[0]
        self.assertIsNone(entry.file_name)
        self.assertIsNone(entry.folder)
        self.assertFalse(entry.renders_body_note)
        self.assertEqual(recorder.stored, [])

    def test_uncatalogued_occurrences_survive(self) -> None:
        catalogue = build_asset_catalogue(
            decisions=[],
            first_page_index_of={},
            extract=Recorder().extract,
            store=Recorder().store,
            uncatalogued=[
                UncataloguedOccurrence(
                    page_index=7, primitive_id="p:i0003", reason="nessun digest"
                )
            ],
        )
        self.assertEqual(len(catalogue.uncatalogued), 1)
        self.assertEqual(catalogue.uncatalogued[0].page_index, 7)


class ConsumerShapeTest(unittest.TestCase):
    def _catalogue(self) -> AssetCatalogue:
        return build_asset_catalogue(
            decisions=[
                _decision("md5:art"),
                _decision("md5:bg", RECURRING, pages=9, occurrences=9),
                _decision("md5:grad", NO_STORED_RESOURCE, stored=False),
            ],
            first_page_index_of={"md5:art": 0, "md5:bg": 0, "md5:grad": 0},
            extract=Recorder().extract,
            store=Recorder().store,
        )

    def test_only_content_carries_a_body_note(self) -> None:
        self.assertEqual(
            self._catalogue().digests_with_body_note(), frozenset({"md5:art"})
        )

    def test_stored_files_lists_only_what_was_written(self) -> None:
        files = self._catalogue().stored_files()
        self.assertEqual(len(files), 2)
        self.assertIn(("images", "md5_art.png"), files)


class NamingTest(unittest.TestCase):
    def test_the_name_comes_from_the_content_not_the_page(self) -> None:
        # Il legacy nomina `p92_img11.jpeg`: la stessa immagine su due pagine ha
        # due nomi. Qui un contenuto ha un nome solo.
        self.assertEqual(file_stem_for("md5:abc123"), "md5_abc123")

    def test_unsafe_characters_are_replaced(self) -> None:
        self.assertEqual(file_stem_for("a/b\\c d"), "a_b_c_d")

    def test_an_empty_digest_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            file_stem_for("")


class ContractTest(unittest.TestCase):
    def _entry(self, **overrides) -> AssetCatalogueEntry:
        fields = dict(
            digest="md5:a",
            destination=CONTENT,
            folder="images",
            file_name="md5_a.png",
            extraction_method="stored",
            page_count=1,
            occurrence_count=1,
            first_page_index=0,
            smallest_placed_extent=10.0,
            has_stored_resource=True,
            renders_body_note=True,
        )
        fields.update(overrides)
        return AssetCatalogueEntry(**fields)  # type: ignore[arg-type]

    def test_a_note_without_a_file_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            self._entry(file_name=None, folder=None, extraction_method=None)

    def test_a_file_without_a_folder_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            self._entry(folder=None, renders_body_note=False)

    def test_a_method_without_a_file_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            self._entry(file_name=None, renders_body_note=False)

    def test_two_entries_must_not_claim_the_same_file(self) -> None:
        with self.assertRaises(ValueError):
            AssetCatalogue(entries=(self._entry(), self._entry(digest="md5:b")))

    def test_a_repeated_digest_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            AssetCatalogue(
                entries=(self._entry(), self._entry(file_name="md5_b.png"))
            )


if __name__ == "__main__":
    unittest.main()
