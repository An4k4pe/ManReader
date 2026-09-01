import unittest

from document_asset_recurrence_measurements import (
    AssetRecurrence,
    DigestlessOccurrence,
    DocumentAssetRecurrenceMeasurements,
    measure_document_asset_recurrence,
)
from geometry_model import PageGeometry
from primitive_model import ImageOccurrencePrimitive, NormalizedPrimitivePage

GEOMETRY = PageGeometry(
    width=100.0,
    height=100.0,
    unit="pt",
    coordinate_system="top_left_y_down",
)


def _page(
    index: int,
    *images_at: tuple[str | None, float, float, float, float],
    has_stored_resource: bool | None = None,
) -> NormalizedPrimitivePage:
    primitives = tuple(
        ImageOccurrencePrimitive(
            primitive_id=f"primitive:image:p{index}:i{order}",
            bbox=(x0, y0, x1, y1),
            source_observation_id=f"image:i{order:04d}",
            content_digest=digest,
            has_stored_resource=has_stored_resource,
        )
        for order, (digest, x0, y0, x1, y1) in enumerate(images_at)
    )
    return NormalizedPrimitivePage(
        schema_version="1",
        source_capture_id="c",
        source_id="s",
        page_id=f"page:{index:04d}",
        page_index=index,
        page_geometry=GEOMETRY,
        capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
        image_primitives=primitives,
    )


class MeasureAssetRecurrenceTest(unittest.TestCase):
    def test_a_background_on_every_page_is_one_asset(self) -> None:
        pages = [_page(i, ("md5:bg", 0.0, 0.0, 100.0, 100.0)) for i in range(6)]
        measured = measure_document_asset_recurrence(pages)
        self.assertEqual(len(measured.assets), 1)
        self.assertEqual(measured.assets[0].page_count, 6)
        self.assertEqual(measured.assets[0].occurrence_count, 6)

    def test_an_illustration_on_one_page_stays_at_one(self) -> None:
        pages = [_page(i) for i in range(5)]
        pages[2] = _page(2, ("md5:art", 10.0, 10.0, 90.0, 60.0))
        measured = measure_document_asset_recurrence(pages)
        self.assertEqual(measured.assets[0].page_count, 1)
        self.assertEqual(measured.assets[0].page_indices, (2,))

    def test_two_bands_on_the_same_page_are_one_content_placed_twice(self) -> None:
        # Il caso che la deduplica deve prendere: stesso digest, due
        # collocazioni, una pagina sola. Un file, non due.
        pages = [
            _page(
                0,
                ("md5:band", 0.0, 0.0, 5.0, 100.0),
                ("md5:band", 95.0, 0.0, 100.0, 100.0),
            )
        ]
        measured = measure_document_asset_recurrence(pages)
        self.assertEqual(len(measured.assets), 1)
        self.assertEqual(measured.assets[0].page_count, 1)
        self.assertEqual(measured.assets[0].occurrence_count, 2)

    def test_the_smallest_placed_extent_is_the_minor_side(self) -> None:
        # Una striscia larga e alta un punto: l'estensione che conta e' 1.
        pages = [_page(0, ("md5:rule", 10.0, 50.0, 95.0, 51.0))]
        measured = measure_document_asset_recurrence(pages)
        self.assertAlmostEqual(measured.assets[0].smallest_placed_extent, 1.0)
        self.assertAlmostEqual(measured.assets[0].largest_placed_extent, 1.0)

    def test_the_same_content_placed_at_two_sizes_reports_both(self) -> None:
        pages = [
            _page(0, ("md5:icon", 0.0, 0.0, 10.0, 10.0)),
            _page(1, ("md5:icon", 0.0, 0.0, 40.0, 40.0)),
        ]
        measured = measure_document_asset_recurrence(pages)
        self.assertAlmostEqual(measured.assets[0].smallest_placed_extent, 10.0)
        self.assertAlmostEqual(measured.assets[0].largest_placed_extent, 40.0)

    def test_an_occurrence_without_a_digest_is_registered_not_dropped(self) -> None:
        # AGENTS.MD §Coverage: nessuna esclusione puo' essere silenziosa.
        pages = [_page(0, (None, 10.0, 10.0, 20.0, 20.0))]
        measured = measure_document_asset_recurrence(pages)
        self.assertEqual(measured.assets, ())
        self.assertEqual(len(measured.digestless), 1)
        self.assertEqual(measured.digestless[0].page_index, 0)

    def test_assets_come_out_sorted_by_digest(self) -> None:
        pages = [
            _page(
                0,
                ("md5:zzz", 0.0, 0.0, 10.0, 10.0),
                ("md5:aaa", 20.0, 20.0, 30.0, 30.0),
            )
        ]
        measured = measure_document_asset_recurrence(pages)
        self.assertEqual(
            [asset.digest for asset in measured.assets], ["md5:aaa", "md5:zzz"]
        )

    def test_a_page_without_images_still_counts_towards_the_document(self) -> None:
        pages = [_page(0, ("md5:bg", 0.0, 0.0, 100.0, 100.0)), _page(1)]
        measured = measure_document_asset_recurrence(pages)
        self.assertEqual(measured.page_count, 2)
        self.assertEqual(measured.assets[0].page_count, 1)

    def test_empty_pages_are_refused(self) -> None:
        with self.assertRaises(ValueError):
            measure_document_asset_recurrence([])

    def test_a_repeated_page_index_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            measure_document_asset_recurrence([_page(0), _page(0)])


class StoredResourceTest(unittest.TestCase):
    def test_the_fact_reaches_the_measurement(self) -> None:
        pages = [
            _page(0, ("md5:grad", 0.0, 0.0, 50.0, 1.0), has_stored_resource=False)
        ]
        measured = measure_document_asset_recurrence(pages)
        self.assertIs(measured.assets[0].has_stored_resource, False)

    def test_one_stored_placement_makes_the_content_extractable(self) -> None:
        # Il verso conta: se lo stesso contenuto compare una volta memorizzato e
        # una volta sintetizzato, esiste e va preso da dove c'e'. Il contrario
        # perderebbe un asset vero per via della sua seconda collocazione.
        pages = [
            _page(0, ("md5:x", 0.0, 0.0, 50.0, 50.0), has_stored_resource=False),
            _page(1, ("md5:x", 0.0, 0.0, 50.0, 50.0), has_stored_resource=True),
        ]
        measured = measure_document_asset_recurrence(pages)
        self.assertIs(measured.assets[0].has_stored_resource, True)

    def test_all_synthesized_stays_false(self) -> None:
        pages = [
            _page(i, ("md5:x", 0.0, 0.0, 50.0, 50.0), has_stored_resource=False)
            for i in range(3)
        ]
        measured = measure_document_asset_recurrence(pages)
        self.assertIs(measured.assets[0].has_stored_resource, False)

    def test_an_undeclared_fact_stays_undeclared(self) -> None:
        pages = [_page(0, ("md5:x", 0.0, 0.0, 50.0, 50.0), has_stored_resource=None)]
        measured = measure_document_asset_recurrence(pages)
        self.assertIsNone(measured.assets[0].has_stored_resource)


class ConvenienceReadersTest(unittest.TestCase):
    def _measured(self) -> DocumentAssetRecurrenceMeasurements:
        pages = [_page(i, ("md5:bg", 0.0, 0.0, 100.0, 100.0)) for i in range(10)]
        pages[3] = _page(
            3,
            ("md5:bg", 0.0, 0.0, 100.0, 100.0),
            ("md5:art", 10.0, 10.0, 90.0, 60.0),
        )
        return measure_document_asset_recurrence(pages)

    def test_more_than_one_page_separates_furniture_from_content(self) -> None:
        repeated = self._measured().placed_on_more_than_one_page()
        self.assertEqual([asset.digest for asset in repeated], ["md5:bg"])

    def test_placed_on_at_least_takes_the_share_from_the_caller(self) -> None:
        measured = self._measured()
        self.assertEqual(len(measured.placed_on_at_least(0.5)), 1)
        self.assertEqual(len(measured.placed_on_at_least(1.0)), 1)

    def test_a_share_outside_the_unit_interval_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            self._measured().placed_on_at_least(0.0)

    def test_by_digest_finds_and_misses_cleanly(self) -> None:
        measured = self._measured()
        self.assertIsNotNone(measured.by_digest("md5:art"))
        self.assertIsNone(measured.by_digest("md5:nowhere"))


class ContractTest(unittest.TestCase):
    def test_page_indices_must_match_page_count(self) -> None:
        with self.assertRaises(ValueError):
            AssetRecurrence(
                digest="md5:a",
                page_count=2,
                page_indices=(0,),
                occurrence_count=2,
                smallest_placed_extent=1.0,
                largest_placed_extent=1.0,
            )

    def test_occurrences_cannot_be_fewer_than_pages(self) -> None:
        with self.assertRaises(ValueError):
            AssetRecurrence(
                digest="md5:a",
                page_count=2,
                page_indices=(0, 1),
                occurrence_count=1,
                smallest_placed_extent=1.0,
                largest_placed_extent=1.0,
            )

    def test_a_duplicate_digest_is_refused(self) -> None:
        asset = AssetRecurrence(
            digest="md5:a",
            page_count=1,
            page_indices=(0,),
            occurrence_count=1,
            smallest_placed_extent=1.0,
            largest_placed_extent=1.0,
        )
        with self.assertRaises(ValueError):
            DocumentAssetRecurrenceMeasurements(page_count=1, assets=(asset, asset))

    def test_an_asset_cannot_span_more_pages_than_the_document(self) -> None:
        asset = AssetRecurrence(
            digest="md5:a",
            page_count=3,
            page_indices=(0, 1, 2),
            occurrence_count=3,
            smallest_placed_extent=1.0,
            largest_placed_extent=1.0,
        )
        with self.assertRaises(ValueError):
            DocumentAssetRecurrenceMeasurements(page_count=2, assets=(asset,))

    def test_a_digestless_occurrence_needs_a_primitive_id(self) -> None:
        with self.assertRaises(ValueError):
            DigestlessOccurrence(page_index=0, primitive_id="")


if __name__ == "__main__":
    unittest.main()
