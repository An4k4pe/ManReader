"""Tests per i titoli desunti dalla dimensione del carattere.

`Criterio_Titoli_v2.md` §1. Ogni caso viene da un manuale vero, e i casi in cui la
regola **non** promuove contano quanto gli altri: la v1 di questo criterio
scambiava per titoli 67 righe di prosa su Kul.
"""

from __future__ import annotations

import unittest

from document_heading_measurements import FontSizeMeasurements, SizedLine
from document_heading_policy import heading_levels, heading_lines, prose_sizes


def _measure(**per_size: tuple[int, float]) -> FontSizeMeasurements:
    """`{dimensione: (righe, lunghezza mediana)}`, scritto come si legge."""

    return FontSizeMeasurements(
        line_count={float(s): n for s, (n, _m) in per_size.items()},
        median_length={float(s): m for s, (_n, m) in per_size.items()},
    )


class ProseSizesTest(unittest.TestCase):
    def test_the_biggest_gap_separates_prose_from_headings(self) -> None:
        # DB: le mediane sono 10, 14, 45, 55 e il salto sta fra 14 e 45.
        measured = FontSizeMeasurements(
            line_count={10.0: 612, 9.0: 86, 11.5: 43, 34.0: 8},
            median_length={10.0: 55.0, 9.0: 45.0, 11.5: 10.0, 34.0: 14.0},
        )
        self.assertEqual(prose_sizes(measured), frozenset({9.0, 10.0}))

    def test_two_prose_streams_are_both_prose(self) -> None:
        # Kul: 8,0 e 10,0 sono entrambe prosa. Guardando solo la piu' frequente,
        # le 67 righe a 10,0 risultavano titoli.
        measured = FontSizeMeasurements(
            line_count={8.0: 552, 10.0: 67, 27.9: 6},
            median_length={8.0: 52.0, 10.0: 44.0, 27.9: 13.0},
        )
        self.assertEqual(prose_sizes(measured), frozenset({8.0, 10.0}))

    def test_a_size_with_too_few_lines_says_nothing_about_its_median(self) -> None:
        measured = FontSizeMeasurements(
            line_count={10.0: 500, 30.0: 2}, median_length={10.0: 50.0, 30.0: 90.0}
        )
        self.assertEqual(prose_sizes(measured), frozenset({10.0}))

    def test_with_a_single_size_everything_seen_is_prose(self) -> None:
        # Preferire il silenzio all'invenzione: senza un salto non c'e' niente
        # da separare, e non si promuove nulla.
        measured = FontSizeMeasurements(line_count={10.0: 500}, median_length={10.0: 50.0})
        self.assertEqual(prose_sizes(measured), frozenset({10.0}))


class HeadingLevelsTest(unittest.TestCase):
    def test_the_level_is_a_rank_not_a_threshold(self) -> None:
        measured = FontSizeMeasurements(
            line_count={10.0: 500, 34.0: 8, 20.0: 9, 12.0: 7},
            median_length={10.0: 50.0, 34.0: 12.0, 20.0: 11.0, 12.0: 9.0},
        )
        levels = heading_levels(measured, frozenset({10.0}))
        self.assertEqual(levels, {34.0: 1, 20.0: 2, 12.0: 3})

    def test_it_collapses_at_six_because_that_is_what_markdown_has(self) -> None:
        sizes = {float(20 + i): 5 for i in range(8)}
        measured = FontSizeMeasurements(
            line_count={10.0: 500, **sizes},
            median_length={10.0: 50.0, **{s: 9.0 for s in sizes}},
        )
        levels = heading_levels(measured, frozenset({10.0}))
        self.assertEqual(max(levels.values()), 6)


class HeadingLinesTest(unittest.TestCase):
    def _line(self, block: str, text: str, size: float) -> SizedLine:
        return SizedLine(block=block, text=text, size=size)

    def test_a_lone_big_line_is_a_heading(self) -> None:
        lines = [self._line("b0005", "SCUOLE DI MAGIA", 34.0)]
        self.assertEqual(
            heading_lines(lines, frozenset({10.0}), {34.0: 1}), {0: 1}
        )

    def test_a_block_that_carries_prose_is_not_a_heading_block(self) -> None:
        lines = [
            self._line("b0005", "TITOLO", 34.0),
            self._line("b0005", "e poi del testo di prosa lungo abbastanza", 10.0),
        ]
        self.assertEqual(heading_lines(lines, frozenset({10.0}), {34.0: 1}), {})

    def test_a_smaller_running_head_beside_the_title_does_not_block_it(self) -> None:
        # Apo: il blocco del titolo contiene anche la testatina, che sta SOTTO
        # la prosa. Chiedere che tutte le righe stiano sopra perdeva Apo e Vil.
        lines = [
            self._line("b0001", "S E C O N D O AT TO", 7.5),
            self._line("b0001", "Introduzione", 46.4),
        ]
        self.assertEqual(
            heading_lines(lines, frozenset({11.6}), {46.4: 1}), {1: 1}
        )

    def test_a_long_block_is_not_a_heading(self) -> None:
        lines = [self._line("b0002", f"riga {i}", 20.0) for i in range(3)]
        self.assertEqual(heading_lines(lines, frozenset({10.0}), {20.0: 1}), {})

    def test_a_single_character_is_a_drop_cap_and_not_a_heading(self) -> None:
        # Fab: `3`, `n`, `W` a corpo 30 sono la prima lettera ingrandita.
        lines = [self._line("b0000", "W", 30.2)]
        self.assertEqual(heading_lines(lines, frozenset({10.0}), {30.2: 1}), {})

    def test_furniture_is_not_promoted(self) -> None:
        # In molti manuali il numero di pagina e' piu' grande della prosa.
        lines = [self._line("b0000", "152", 14.0)]
        self.assertEqual(
            heading_lines(lines, frozenset({9.5}), {14.0: 1}, frozenset({"152"})), {}
        )


if __name__ == "__main__":
    unittest.main()
