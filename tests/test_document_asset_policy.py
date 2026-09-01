import unittest

from document_asset_policy import (
    BELOW_TEXT_SCALE,
    CONTENT,
    NO_STORED_RESOURCE,
    RECURRING,
    decide_document_assets,
    decisions_by_digest,
    digests_with_body_note,
)
from document_asset_recurrence_measurements import (
    AssetRecurrence,
    DocumentAssetRecurrenceMeasurements,
)


def _measured(
    *assets: tuple[str, int, int, float],
    page_count: int = 100,
    has_stored_resource: bool | None = True,
) -> DocumentAssetRecurrenceMeasurements:
    return DocumentAssetRecurrenceMeasurements(
        page_count=page_count,
        assets=tuple(
            AssetRecurrence(
                digest=digest,
                page_count=pages,
                page_indices=tuple(range(pages)),
                occurrence_count=max(occurrences, pages),
                smallest_placed_extent=extent,
                largest_placed_extent=extent,
                has_stored_resource=has_stored_resource,
            )
            for digest, pages, occurrences, extent in assets
        ),
    )


class DestinationTest(unittest.TestCase):
    def test_an_illustration_on_one_page_is_content_and_gets_a_note(self) -> None:
        # Dag idx 199: 614x285 pt, 1 pagina su 379. E' l'immagine che mancava.
        decisions = decide_document_assets(
            _measured(("md5:art", 1, 1, 285.3)), text_scale=7.8
        )
        self.assertEqual(decisions[0].destination, CONTENT)
        self.assertEqual(decisions[0].folder, "images")
        self.assertTrue(decisions[0].renders_body_note)

    def test_a_background_on_many_pages_is_recurring_and_stays_silent(self) -> None:
        # Dag idx 199: il fondo carta, 156 pagine su 379.
        decisions = decide_document_assets(
            _measured(("md5:bg", 156, 156, 627.7), page_count=379), text_scale=7.8
        )
        self.assertEqual(decisions[0].destination, RECURRING)
        self.assertEqual(decisions[0].folder, "assets")
        self.assertFalse(decisions[0].renders_body_note)

    def test_a_footer_bar_narrow_but_everywhere_is_recurring(self) -> None:
        # La regola legacy dello sfondo -- bbox oltre il 60% della pagina --
        # manca questo caso: 569x57 pt e' il 4% della pagina, e sta su 342
        # pagine su 379. La ricorrenza lo prende.
        decisions = decide_document_assets(
            _measured(("md5:bar", 342, 342, 56.7), page_count=379), text_scale=7.8
        )
        self.assertEqual(decisions[0].destination, RECURRING)

    def test_a_table_rule_thinner_than_the_text_gets_no_file_and_no_note(self) -> None:
        # Fab idx 126: filetto di riga, 185x1 pt, contro una prosa a 8,0.
        decisions = decide_document_assets(
            _measured(("md5:rule", 1, 1, 1.0), page_count=362), text_scale=8.0
        )
        self.assertEqual(decisions[0].destination, BELOW_TEXT_SCALE)
        self.assertIsNone(decisions[0].folder)
        self.assertFalse(decisions[0].renders_body_note)

    def test_the_text_scale_branch_runs_before_recurrence(self) -> None:
        # Un filetto ripetuto resta un filetto: non va nella cartella degli
        # sfondi, che l'utente ha chiesto di tenere pulita.
        decisions = decide_document_assets(
            _measured(("md5:rule", 58, 58, 2.0), page_count=362), text_scale=8.0
        )
        self.assertEqual(decisions[0].destination, BELOW_TEXT_SCALE)

    def test_exactly_at_the_text_scale_survives(self) -> None:
        # Il confine e' stretto: «piu' sottile della lettera piu' piccola», non
        # «alto quanto». Un'icona alla dimensione del corpo resta contenuto.
        decisions = decide_document_assets(
            _measured(("md5:icon", 1, 1, 8.0)), text_scale=8.0
        )
        self.assertEqual(decisions[0].destination, CONTENT)

    def test_two_pages_already_count_as_repeated(self) -> None:
        # BiD idx 287: lo sfondo a piena pagina sta su 2 pagine. `page_count > 1`
        # e' la lettura letterale di «ripetuto», non una soglia tarata.
        decisions = decide_document_assets(
            _measured(("md5:spread", 2, 2, 807.6)), text_scale=8.0
        )
        self.assertEqual(decisions[0].destination, RECURRING)

    def test_one_content_placed_twice_on_one_page_is_still_content(self) -> None:
        # Due bande ai lati della stessa pagina: due collocazioni, una pagina.
        # E' la ricorrenza fra PAGINE che segna l'arredo, non la ripetizione.
        decisions = decide_document_assets(
            _measured(("md5:twice", 1, 2, 40.0)), text_scale=8.0
        )
        self.assertEqual(decisions[0].destination, CONTENT)


class NoStoredResourceTest(unittest.TestCase):
    """Il ramo che etichetta invece di cancellare."""

    def test_a_gradient_fill_has_no_file_and_no_note(self) -> None:
        # Fab idx 126: i riempimenti a gradiente escono da `get_image_info` come
        # immagini a xref 0. Non c'e' niente da estrarre: il file sarebbe una
        # fotografia della regione di pagina, col testo dentro.
        decisions = decide_document_assets(
            _measured(("md5:grad", 1, 1, 129.0), has_stored_resource=False),
            text_scale=8.0,
        )
        self.assertEqual(decisions[0].destination, NO_STORED_RESOURCE)
        self.assertIsNone(decisions[0].folder)
        self.assertFalse(decisions[0].renders_body_note)

    def test_the_fact_survives_onto_the_decision(self) -> None:
        # «Non si cancellano le cose, ma si taggano per usi futuri»: il fatto
        # deve restare leggibile a valle, non solo cambiare la destinazione.
        decisions = decide_document_assets(
            _measured(("md5:grad", 1, 1, 129.0), has_stored_resource=False),
            text_scale=8.0,
        )
        self.assertIs(decisions[0].has_stored_resource, False)

    def test_it_runs_before_every_other_branch(self) -> None:
        # Un gradiente ricorrente non e' arredo da inventariare, e un gradiente
        # sottile non e' un filetto: prima si constata che non c'e' la risorsa.
        for pages, extent in ((58, 1.0), (58, 129.0), (1, 1.0)):
            with self.subTest(pages=pages, extent=extent):
                decisions = decide_document_assets(
                    _measured(
                        ("md5:grad", pages, pages, extent),
                        page_count=362,
                        has_stored_resource=False,
                    ),
                    text_scale=8.0,
                )
                self.assertEqual(decisions[0].destination, NO_STORED_RESOURCE)

    def test_an_undeclared_fact_does_not_trigger_the_branch(self) -> None:
        # `None` e' «il backend non lo dichiara», non «non c'e' la risorsa».
        decisions = decide_document_assets(
            _measured(("md5:art", 1, 1, 285.0), has_stored_resource=None),
            text_scale=8.0,
        )
        self.assertEqual(decisions[0].destination, CONTENT)

    def test_a_stored_image_is_untouched_by_the_branch(self) -> None:
        decisions = decide_document_assets(
            _measured(("md5:art", 1, 1, 285.0), has_stored_resource=True),
            text_scale=8.0,
        )
        self.assertEqual(decisions[0].destination, CONTENT)


class SilentScaleTest(unittest.TestCase):
    def test_without_a_text_scale_the_thin_branch_says_nothing(self) -> None:
        # Stesso verso di `document_furniture_policy`: dove il documento non
        # dichiara, non si rimuove. Scartare per una scala inventata sarebbe
        # perdita di contenuto travestita da politica.
        decisions = decide_document_assets(
            _measured(("md5:rule", 1, 1, 1.0)), text_scale=None
        )
        self.assertEqual(decisions[0].destination, CONTENT)

    def test_recurrence_still_works_without_a_text_scale(self) -> None:
        decisions = decide_document_assets(
            _measured(("md5:bg", 40, 40, 1.0)), text_scale=None
        )
        self.assertEqual(decisions[0].destination, RECURRING)

    def test_a_non_positive_scale_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            decide_document_assets(_measured(("md5:a", 1, 1, 5.0)), text_scale=0.0)


class ConsumerShapeTest(unittest.TestCase):
    def test_only_content_digests_carry_a_body_note(self) -> None:
        decisions = decide_document_assets(
            _measured(
                ("md5:art", 1, 1, 285.0),
                ("md5:bg", 156, 156, 627.0),
                ("md5:rule", 1, 1, 1.0),
                page_count=379,
            ),
            text_scale=8.0,
        )
        self.assertEqual(digests_with_body_note(decisions), frozenset({"md5:art"}))

    def test_decisions_are_reachable_by_digest(self) -> None:
        decisions = decide_document_assets(
            _measured(("md5:art", 1, 1, 285.0), ("md5:bg", 9, 9, 627.0)),
            text_scale=8.0,
        )
        index = decisions_by_digest(decisions)
        self.assertEqual(index["md5:bg"].destination, RECURRING)
        self.assertEqual(index["md5:art"].destination, CONTENT)

    def test_one_decision_per_distinct_content(self) -> None:
        decisions = decide_document_assets(
            _measured(("md5:a", 1, 3, 50.0), ("md5:b", 2, 8, 50.0)), text_scale=8.0
        )
        self.assertEqual(len(decisions), 2)

    def test_measurements_of_the_wrong_type_are_refused(self) -> None:
        with self.assertRaises(ValueError):
            decide_document_assets(object(), text_scale=8.0)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
