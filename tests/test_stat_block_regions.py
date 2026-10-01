"""Le schede statistiche nel consumer: `Criterio_SchedaInIR2_v1.md`.

Casi sintetici per le tre regole e per il nome. I numeri veri stanno nei verbali
di `esperimenti_statblock/`; qui si fissa il contratto.
"""

from __future__ import annotations

import unittest

from primitive_model import TextPrimitive
from stat_block_regions import (
    FrameInput,
    StatBlockRegion,
    crosses_a_stat_block,
    label_pairs,
    split_frame,
    stat_block_regions,
)

BOLD = "Hideout-Bold"
BODY = "Hideout-Regular"
NAME = "Hideout-Display"
CHAR = 8.0


def _line(line: int, y: float, *parts: tuple[str, str]) -> list[TextPrimitive]:
    """Una riga di sorgente fatta di span consecutivi, ognuno col suo font."""

    spans: list[TextPrimitive] = []
    cursor = 10.0
    for index, (text, font) in enumerate(parts):
        observation = f"text:b0001:l{line:04d}:s{index:04d}"
        width = CHAR * max(len(text), 1)
        spans.append(
            TextPrimitive(
                primitive_id=f"primitive:text:{observation}",
                bbox=(cursor, y, cursor + width, y + 10.0),
                text=text,
                source_observation_id=observation,
                font_name=font,
                font_size=9.0,
            )
        )
        cursor += width
    return spans


def _name(line: int, y: float, text: str = "RAGNO GIGANTE") -> list[TextPrimitive]:
    return _line(line, y, (text, NAME))


def _fields(line: int, y: float) -> list[TextPrimitive]:
    """Una riga di scheda: due coppie etichetta/valore."""

    return _line(line, y, ("Ferocia:", BOLD), (" 2  ", BODY), ("Taglia:", BOLD), (" Normale", BODY))


def _frame(candidate_id: str, bbox: tuple[float, float, float, float], *ids: str) -> FrameInput:
    return FrameInput(candidate_id=candidate_id, bbox=bbox, primitive_ids=ids)


BOX_1 = (0.0, 0.0, 300.0, 60.0)
BOX_2 = (0.0, 68.0, 300.0, 128.0)


class LabelPairsTest(unittest.TestCase):
    def test_two_pairs_on_one_line(self) -> None:
        self.assertEqual(label_pairs(_fields(0, 0.0)), 2)

    def test_a_line_in_one_style_has_none(self) -> None:
        self.assertEqual(label_pairs(_name(0, 0.0)), 0)

    def test_prose_opening_in_bold_has_one(self) -> None:
        line = _line(0, 0.0, ("Mandibole!", BOLD), (" Le mandibole seghettate", BODY))
        self.assertEqual(label_pairs(line), 1)

    def test_a_space_in_another_font_is_not_a_value(self) -> None:
        # Senza scartare le spaziature, `Movimento` avrebbe per valore uno spazio.
        line = _line(0, 0.0, ("Movimento", BOLD), (" ", BODY), ("24", BOLD))
        self.assertEqual(label_pairs(line), 0)

    def test_a_colon_alone_is_not_a_label(self) -> None:
        self.assertEqual(label_pairs(_line(0, 0.0, (":", BOLD), (" 2", BODY))), 0)


class SplitFrameTest(unittest.TestCase):
    def test_a_merged_frame_splits_into_its_boxes(self) -> None:
        # Il caso di Daggerheart: due riquadri a 8 pt fusi dal raggruppamento.
        frame = _frame("c", (0.0, 0.0, 300.0, 128.0), "d:1", "d:2")
        lines = [(10.0, 20.0, 200.0, 30.0), (10.0, 90.0, 200.0, 100.0)]
        pieces = split_frame(frame, {"d:1": BOX_1, "d:2": BOX_2}, lines)
        self.assertEqual(pieces, [BOX_1, BOX_2])

    def test_a_box_with_its_outline_and_inner_panel_stays_whole(self) -> None:
        # Fondo, contorno e fondino dei campi: un solo massimale, nessuna
        # separazione, e il bbox resta quello del candidato.
        frame = _frame("c", BOX_1, "d:fondo", "d:contorno", "d:campi")
        boxes = {
            "d:fondo": BOX_1,
            "d:contorno": (0.2, 0.2, 299.8, 59.8),
            "d:campi": (5.0, 25.0, 295.0, 55.0),
        }
        pieces = split_frame(frame, boxes, [(10.0, 30.0, 200.0, 40.0)])
        self.assertEqual(pieces, [BOX_1])

    def test_maximal_boxes_sharing_a_line_are_one_box(self) -> None:
        frame = _frame("c", (0.0, 0.0, 300.0, 100.0), "d:a", "d:b")
        boxes = {"d:a": (0.0, 0.0, 200.0, 100.0), "d:b": (100.0, 0.0, 300.0, 100.0)}
        pieces = split_frame(frame, boxes, [(100.0, 40.0, 200.0, 50.0)])
        self.assertEqual(pieces, [(0.0, 0.0, 300.0, 100.0)])

    def test_a_box_without_lines_does_not_split(self) -> None:
        frame = _frame("c", (0.0, 0.0, 300.0, 128.0), "d:1", "d:2")
        pieces = split_frame(frame, {"d:1": BOX_1, "d:2": BOX_2}, [(10.0, 20.0, 200.0, 30.0)])
        self.assertEqual(pieces, [(0.0, 0.0, 300.0, 128.0)])


class StatBlockRegionsTest(unittest.TestCase):
    def test_a_frame_with_two_field_lines_is_a_stat_block_named_by_its_first_line(self) -> None:
        lines = [_name(0, 10.0), _fields(1, 30.0), _fields(2, 45.0)]
        regions = stat_block_regions([_frame("c", BOX_1, "d")], {"d": BOX_1}, lines)
        self.assertEqual(len(regions), 1)
        self.assertEqual(regions[0].line_indices, (0, 1, 2))
        self.assertEqual(regions[0].name_line_indices, (0,))
        self.assertEqual(regions[0].candidate_id, "c")

    def test_one_field_line_is_not_enough(self) -> None:
        prose = _line(2, 45.0, ("Il ragno attacca con le zampe.", BODY))
        lines = [_name(0, 10.0), _fields(1, 30.0), prose]
        self.assertEqual(stat_block_regions([_frame("c", BOX_1, "d")], {"d": BOX_1}, lines), ())

    def test_a_merged_frame_gives_one_stat_block_per_box(self) -> None:
        lines = [
            _name(0, 10.0, "GIANT RAT"),
            _fields(1, 30.0),
            _fields(2, 45.0),
            _name(3, 78.0, "GIANT SCORPION"),
            _fields(4, 98.0),
            _fields(5, 113.0),
        ]
        frame = _frame("fuso", (0.0, 0.0, 300.0, 128.0), "d:1", "d:2")
        regions = stat_block_regions([frame], {"d:1": BOX_1, "d:2": BOX_2}, lines)
        self.assertEqual([r.name_line_indices for r in regions], [(0,), (3,)])
        self.assertEqual([r.bbox for r in regions], [BOX_1, BOX_2])
        self.assertEqual({r.candidate_id for r in regions}, {"fuso"})

    def test_the_frame_with_more_lines_wins_and_each_line_is_taken_once(self) -> None:
        # Il riquadro dei soli campi sta dentro la scheda: vince la scheda intera.
        inner = (0.0, 25.0, 300.0, 60.0)
        lines = [_name(0, 10.0), _fields(1, 30.0), _fields(2, 45.0)]
        frames = [_frame("campi", inner, "d:campi"), _frame("scheda", BOX_1, "d:scheda")]
        regions = stat_block_regions(frames, {"d:campi": inner, "d:scheda": BOX_1}, lines)
        self.assertEqual([r.candidate_id for r in regions], ["scheda"])

    def test_an_illustration_over_the_stat_block_does_not_win_it(self) -> None:
        # Dragonbane idx 31: l'illustrazione del pipistrello copre la pergamena
        # e anche il testo accanto. Entrambe cominciano dal nome; vince la piu'
        # stretta.
        lines = [
            _name(0, 10.0, "PIPISTRELLI VAMPIRO"),
            _fields(1, 30.0),
            _fields(2, 45.0),
            _line(3, 80.0, ("5. CRIPTA DELLA SERVITU'", BODY)),
            _line(4, 95.0, ("Una camera buia e umida.", BODY)),
        ]
        illustration = (0.0, 0.0, 400.0, 110.0)
        frames = [_frame("illustrazione", illustration, "i:1"), _frame("pergamena", BOX_1, "i:2")]
        regions = stat_block_regions(frames, {"i:1": illustration, "i:2": BOX_1}, lines)
        self.assertEqual([r.candidate_id for r in regions], ["pergamena"])
        self.assertEqual(regions[0].name_line_indices, (0,))

    def test_a_wrapped_name_is_one_name(self) -> None:
        tier = _line(2, 30.0, ("Tier", BOLD), (" 4 Solo", BODY))
        lines = [
            _name(0, 5.0, "FALLEN WARLORD:"),
            _name(1, 16.0, "UNDEFEATED CHAMPION"),
            tier,
            _fields(3, 40.0),
            _fields(4, 50.0),
        ]
        regions = stat_block_regions([_frame("c", BOX_1, "d")], {"d": BOX_1}, lines)
        self.assertEqual(regions[0].name_line_indices, (0, 1))

    def test_a_stat_block_opening_with_fields_has_no_name(self) -> None:
        lines = [_fields(0, 10.0), _fields(1, 30.0)]
        regions = stat_block_regions([_frame("c", BOX_1, "d")], {"d": BOX_1}, lines)
        self.assertEqual(regions[0].name_line_indices, ())

    def test_a_line_of_spaces_belongs_to_no_frame(self) -> None:
        lines = [_line(0, 10.0, ("   ", BODY)), _name(1, 12.0), _fields(2, 30.0), _fields(3, 45.0)]
        regions = stat_block_regions([_frame("c", BOX_1, "d")], {"d": BOX_1}, lines)
        self.assertEqual(regions[0].line_indices, (1, 2, 3))
        self.assertEqual(regions[0].name_line_indices, (1,))


    def test_a_style_that_recurs_in_the_stat_block_is_not_a_name(self) -> None:
        # DB p.98: un'illustrazione con sopra anche prosa passa da scheda, e la
        # sua prima riga e' prosa, nello stesso stile di altre righe della
        # scheda. Meglio nessun titolo che un titolo falso.
        prose = _line(0, 10.0, ("occhi penetranti che brillano", BODY))
        lines = [prose, _fields(1, 30.0), _fields(2, 45.0), _line(3, 52.0, ("di un giallo", BODY))]
        regions = stat_block_regions([_frame("c", BOX_1, "d")], {"d": BOX_1}, lines)
        self.assertEqual(regions[0].name_line_indices, ())

    def test_a_style_seen_only_as_a_value_is_still_another_line(self) -> None:
        # Lo stile del nome conta anche dentro una riga di campi: se il valore
        # di un campo e' nello stile del nome, il nome non e' unico.
        lines = [
            _name(0, 10.0),
            _line(1, 30.0, ("Ferocia:", BOLD), (" 2 ", NAME), ("Taglia:", BOLD), (" N", BODY)),
            _fields(2, 45.0),
        ]
        regions = stat_block_regions([_frame("c", BOX_1, "d")], {"d": BOX_1}, lines)
        self.assertEqual(regions[0].name_line_indices, ())

    def test_a_name_does_not_jump_over_lines_outside_the_frame(self) -> None:
        # DB p.98: la riga 1 sta fuori dal riquadro (un'altra colonna). Senza la
        # contiguita' la riga 2, nello stesso stile, entrava nel nome; con la
        # contiguita' resta fuori dal nome, lo stile non e' piu' unico nella
        # scheda, e il nome non c'e'. Nessun titolo invece di un titolo sbagliato.
        lines = [
            _name(0, 10.0),
            _line(1, 400.0, ("fuori dal riquadro", NAME)),
            _name(2, 22.0, "CONTINUAZIONE"),
            _fields(3, 34.0),
            _fields(4, 46.0),
        ]
        regions = stat_block_regions([_frame("c", BOX_1, "d")], {"d": BOX_1}, lines)
        self.assertEqual(regions[0].line_indices, (0, 2, 3, 4))
        self.assertEqual(regions[0].name_line_indices, ())


class CrossesAStatBlockTest(unittest.TestCase):
    REGION = StatBlockRegion(
        bbox=(0.0, 0.0, 300.0, 200.0), candidate_id="c", line_indices=(0,), name_line_indices=()
    )

    def test_a_table_inside_the_stat_block_stays(self) -> None:
        self.assertFalse(crosses_a_stat_block((10.0, 10.0, 290.0, 190.0), [self.REGION]))

    def test_a_table_across_its_border_does_not(self) -> None:
        self.assertTrue(crosses_a_stat_block((0.0, 150.0, 300.0, 400.0), [self.REGION]))

    def test_a_table_elsewhere_is_not_its_business(self) -> None:
        self.assertFalse(crosses_a_stat_block((400.0, 0.0, 500.0, 100.0), [self.REGION]))


class RepeatedStructureTest(unittest.TestCase):
    """La regola dalla struttura ripetuta, senza riquadri: etichette che si contano
    insieme sulle pagine (`esperimenti_statblock/strutture_contate.py`)."""

    NAME = ("Newzald-Bold", 12.0, None)
    BODY = ("Berlingske", 7.5, None)

    def _row(self, text, labels=(), x=50.0, y=0.0, style=None):
        from stat_block_regions import LineFacts

        return LineFacts(
            style=style or self.BODY,
            text=text,
            labels=tuple(labels),
            label_starts=tuple((x + 20.0 * i, 5.0) for i, _l in enumerate(labels)),
            bbox=(x, y, x + 200.0, y + 9.0),
        )

    def _monster(self, name, y):
        return [
            self._row(name, style=self.NAME, y=y),
            self._row("Immunity: —", ["immunity"], y=y + 10),
            self._row("Movement: —  Weakness: —", ["movement", "weakness"], y=y + 20),
            self._row("Effect: a thing", ["effect"], y=y + 30),
            self._row("Effect: another", ["effect"], y=y + 40),
            self._row("They can still roll.", y=y + 50),
        ]

    def _pages(self):
        return {
            index: [row for k in range(count) for row in self._monster(f"M{index}{k}", 60.0 * k)]
            for index, count in ((1, 2), (2, 1), (3, 3))
        }

    def test_labels_counted_together_form_the_structure(self) -> None:
        from stat_block_regions import repeated_structures

        structures = repeated_structures(self._pages())
        self.assertEqual(len(structures), 1)
        # Effect compare due volte per mostro: non conta insieme alle altre.
        self.assertEqual(structures[0].labels, frozenset({"immunity", "movement", "weakness"}))
        self.assertEqual(structures[0].head_style, self.NAME)

    def test_each_instance_is_a_stat_block_named_by_the_head_style(self) -> None:
        from stat_block_regions import repeated_structures, stat_blocks_from_structures

        pages = self._pages()
        blocks = stat_blocks_from_structures(pages[3], repeated_structures(pages))
        self.assertEqual([pages[3][b.name_line_indices[0]].text for b in blocks], ["M30", "M31", "M32"])
        # La scheda arriva fino al nome della successiva, coda compresa.
        self.assertEqual(blocks[0].line_indices, tuple(range(0, 6)))

    def test_ordered_rows_in_one_column_are_a_table(self) -> None:
        from stat_block_regions import repeated_structures

        def weapons(index):
            return [
                self._row("Longsword", y=10.0),
                self._row("Heavy: -1 to Evasion", ["heavy"], x=300.0, y=10.0),
                self._row("Warhammer", y=20.0),
                self._row("Massive: roll an extra die", ["massive"], x=300.0, y=20.0),
            ]

        self.assertEqual(repeated_structures({i: weapons(i) for i in (1, 2, 3)}), ())

    def test_the_last_block_ends_at_a_heading_size_line(self) -> None:
        # La parte libera continua dopo le etichette e si ferma alla prima riga a
        # dimensione di titolo: li' comincia la prosa della sezione dopo.
        from stat_block_regions import repeated_structures, stat_blocks_from_structures

        pages = self._pages()
        page = pages[2] + [
            self._row("More ability text.", y=60.0),
            self._row("ANGULOTLS", style=("Newzald-Bold", 24.0, None), y=80.0),
            self._row("Prose about angulotls.", y=100.0),
        ]
        blocks = stat_blocks_from_structures(page, repeated_structures(pages), heading_sizes=frozenset({24.0}))
        self.assertEqual(blocks[-1].line_indices, tuple(range(0, 7)))

    def test_the_last_block_ends_at_the_border_of_its_frame(self) -> None:
        from stat_block_regions import repeated_structures, stat_blocks_from_structures

        pages = self._pages()
        page = pages[2] + [self._row("Prose outside the box.", y=200.0)]
        frame = (0.0, -5.0, 400.0, 60.0)
        blocks = stat_blocks_from_structures(page, repeated_structures(pages), frames=[frame])
        self.assertEqual(blocks[-1].line_indices, tuple(range(0, 6)))

    def test_a_foreign_box_in_the_middle_is_skipped(self) -> None:
        # DrM idx 43: nell'ordine di lettura il box laterale sta in mezzo alla scheda.
        from stat_block_regions import repeated_structures, stat_blocks_from_structures

        pages = self._pages()
        page = pages[2] + [
            self._row("Angulotl Tactics", x=450.0, y=300.0),
            self._row("Prose in the box.", x=450.0, y=310.0),
            self._row("Noxious Bubble", y=70.0),
        ]
        sidebar = (440.0, 290.0, 700.0, 330.0)
        blocks = stat_blocks_from_structures(page, repeated_structures(pages), frames=[sidebar])
        self.assertEqual(blocks[-1].line_indices, (0, 1, 2, 3, 4, 5, 8))

    def test_a_heading_inside_a_foreign_box_does_not_end_the_block(self) -> None:
        # Prima i riquadri, poi i titoli: il titolo del box laterale si salta col box.
        from stat_block_regions import repeated_structures, stat_blocks_from_structures

        pages = self._pages()
        page = pages[2] + [
            self._row("ANGULOTL TACTICS", x=450.0, y=300.0, style=("Newzald-Bold", 24.0, None)),
            self._row("Prose in the box.", x=450.0, y=320.0),
            self._row("Noxious Bubble", y=70.0),
        ]
        sidebar = (440.0, 290.0, 700.0, 340.0)
        blocks = stat_blocks_from_structures(
            page, repeated_structures(pages), heading_sizes=frozenset({24.0}), frames=[sidebar]
        )
        self.assertEqual(blocks[-1].line_indices, (0, 1, 2, 3, 4, 5, 8))

    def test_a_single_label_is_not_an_instance(self) -> None:
        from stat_block_regions import repeated_structures, stat_blocks_from_structures

        pages = self._pages()
        rules = [self._row("Rules text"), self._row("Immunity: see below", ["immunity"])]
        self.assertEqual(stat_blocks_from_structures(rules, repeated_structures(pages)), ())


if __name__ == "__main__":
    unittest.main()
