import json
import unittest

from ir2_builder import (
    StatBlockAreaInput,
    TableRegionInput,
    _repaired_region,
    build_page_ir2,
    build_table,
    column_bounds,
    group_source_lines,
)
from ir2_markdown import render_page_markdown, render_table
from ir2_model import CellIR2, DocumentIR2, IR2Provenance, NodeIR2, PageIR2, TableIR2
from ir2_serialization import document_ir2_from_dict, document_ir2_to_dict
from ir2_validate import validate_page_ir2_against_primitive_page
from primitive_model import NormalizedPrimitivePage, PageGeometry, TextPrimitive

PAGE = "page:0001"


def _span(block: int, line: int, text: str, x0: float, y: float, width: float = 40.0):
    observation = f"text:b{block:04d}:l{line:04d}:s0000"
    return TextPrimitive(
        primitive_id=f"primitive:text:{observation}",
        bbox=(x0, y, x0 + width, y + 10.0),
        text=text,
        source_observation_id=observation,
    )


def _region(gutters=((100.0, 110.0),), bbox=(0.0, 0.0, 200.0, 100.0)) -> TableRegionInput:
    return TableRegionInput(bbox=bbox, gutter_x_intervals=gutters, candidate_ids=("c1",))


class ColumnBoundsTest(unittest.TestCase):
    def test_one_gutter_gives_two_columns(self) -> None:
        self.assertEqual(column_bounds(_region()), [(0.0, 100.0), (110.0, 200.0)])

    def test_two_gutters_give_three_columns(self) -> None:
        region = _region(gutters=((60.0, 70.0), (130.0, 140.0)))
        self.assertEqual(len(column_bounds(region)), 3)

    def test_a_gutter_outside_the_region_is_ignored(self) -> None:
        region = _region(gutters=((300.0, 310.0),))
        self.assertEqual(column_bounds(region), [(0.0, 200.0)])

    def test_no_gutter_gives_a_single_column(self) -> None:
        self.assertEqual(column_bounds(_region(gutters=())), [(0.0, 200.0)])


class BuildTableTest(unittest.TestCase):
    def _lines(self):
        return group_source_lines([
            _span(1, 0, "D6", 10.0, 0.0),
            _span(2, 0, "ATTACCO", 120.0, 0.0),
            _span(3, 0, "1", 10.0, 20.0),
            _span(4, 0, "Colpo", 120.0, 20.0),
        ])

    def test_builds_a_two_by_two_grid(self) -> None:
        table, residuals = build_table(_region(), self._lines())
        assert table is not None
        self.assertEqual(len(table.rows), 2)
        self.assertEqual([c.text for c in table.rows[0]], ["D6", "ATTACCO"])
        self.assertEqual([c.text for c in table.rows[1]], ["1", "Colpo"])
        self.assertEqual(residuals, [])

    def test_a_line_straddling_a_gutter_becomes_a_residual(self) -> None:
        lines = group_source_lines([_span(1, 0, "titolo largo", 10.0, 0.0, width=180.0)])
        table, residuals = build_table(_region(), lines)
        self.assertIsNone(table)
        self.assertEqual(len(residuals), 1)

    def test_a_region_without_gutters_is_not_a_table(self) -> None:
        table, residuals = build_table(_region(gutters=()), self._lines())
        self.assertIsNone(table)
        self.assertEqual(len(residuals), 4)

    def test_an_empty_cell_is_allowed(self) -> None:
        lines = group_source_lines([_span(1, 0, "solo sinistra", 10.0, 0.0)])
        table, _ = build_table(_region(), lines)
        assert table is not None
        self.assertEqual(table.rows[0][1].text, "")
        self.assertEqual(table.rows[0][1].primitive_ids, ())


class BuildPageWithTableTest(unittest.TestCase):
    def _page(self) -> PageIR2:
        prose_before = _span(0, 0, "Prima della tabella.", 10.0, -30.0, width=180.0)
        cells = [
            _span(1, 0, "D6", 10.0, 0.0),
            _span(2, 0, "ATTACCO", 120.0, 0.0),
            _span(3, 0, "1", 10.0, 20.0),
            _span(4, 0, "Colpo", 120.0, 20.0),
        ]
        prose_after = _span(9, 0, "Dopo la tabella.", 10.0, 200.0, width=180.0)
        return build_page_ir2(
            page_id=PAGE,
            ordered_text_primitives=[prose_before, *cells, prose_after],
            table_regions=[_region()],
        )

    def test_the_table_node_sits_between_the_two_paragraphs(self) -> None:
        kinds = [node.kind for node in self._page().nodes]
        self.assertEqual(kinds, ["text.paragraph", "layout.table", "text.paragraph"])

    def test_the_cells_leave_the_paragraph_flow(self) -> None:
        texts = [n.text for n in self._page().nodes if n.text]
        self.assertEqual(texts, ["Prima della tabella.", "Dopo la tabella."])

    def test_the_node_owns_exactly_the_cell_primitives(self) -> None:
        node = next(n for n in self._page().nodes if n.structure is not None)
        from_cells = {
            pid for row in node.structure.rows for cell in row for pid in cell.primitive_ids
        }
        self.assertEqual(set(node.primitive_ids), from_cells)

    def test_every_primitive_is_still_covered_once(self) -> None:
        page = self._page()
        covered = [pid for node in page.nodes for pid in node.primitive_ids]
        self.assertEqual(len(covered), len(set(covered)))
        self.assertEqual(len(covered), 6)


class ValidatorTest(unittest.TestCase):
    """Il modello non puo' vedere la coerenza celle/nodo: la vede il validatore."""

    def _primitive_page(self, *ids: str) -> NormalizedPrimitivePage:
        primitives = tuple(
            TextPrimitive(
                primitive_id=pid,
                bbox=(0.0, float(i), 10.0, float(i) + 5.0),
                text="x",
                source_observation_id=f"text:b{i:04d}:l0000:s0000",
            )
            for i, pid in enumerate(ids)
        )
        return NormalizedPrimitivePage(
            schema_version="1.0",
            source_capture_id="capture:1",
            source_id="source:1",
            page_id=PAGE,
            page_index=0,
            page_geometry=PageGeometry(
                width=100.0, height=200.0, unit="pt", coordinate_system="top_left_y_down"
            ),
            capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
            text_primitives=primitives,
        )

    def _page_with(self, node_ids: tuple[str, ...], cell_ids: tuple[str, ...]) -> PageIR2:
        table = TableIR2(rows=((
            CellIR2(row=0, column=0, text="a", primitive_ids=cell_ids),
        ),))
        return PageIR2(page_id=PAGE, nodes=(NodeIR2(
            node_id="n", order=0, kind="layout.table",
            primitive_ids=node_ids, page_ids=(PAGE,), structure=table,
        ),))

    def test_accepts_when_the_cells_match_the_node(self) -> None:
        validate_page_ir2_against_primitive_page(
            self._page_with(("p1",), ("p1",)), self._primitive_page("p1")
        )

    def test_rejects_when_the_node_owns_more_than_its_cells(self) -> None:
        with self.assertRaises(ValueError):
            validate_page_ir2_against_primitive_page(
                self._page_with(("p1", "p2"), ("p1",)), self._primitive_page("p1", "p2")
            )

    def test_rejects_when_a_cell_owns_something_the_node_does_not(self) -> None:
        with self.assertRaises(ValueError):
            validate_page_ir2_against_primitive_page(
                self._page_with(("p1",), ("p1", "p2")), self._primitive_page("p1", "p2")
            )


class SerializationTest(unittest.TestCase):
    def test_round_trip_preserves_a_table(self) -> None:
        table = TableIR2(rows=(
            (CellIR2(row=0, column=0, text="D6", primitive_ids=("p1",)),
             CellIR2(row=0, column=1, text="ATTACCO", primitive_ids=("p2",))),
        ))
        document = DocumentIR2(
            provenance=IR2Provenance(source_id="s", generation_id="g"),
            pages=(PageIR2(page_id=PAGE, nodes=(NodeIR2(
                node_id="n", order=0, kind="layout.table",
                primitive_ids=("p1", "p2"), page_ids=(PAGE,), structure=table,
            ),)),),
        )
        payload = json.loads(json.dumps(document_ir2_to_dict(document)))
        self.assertEqual(document_ir2_from_dict(payload), document)

    def test_rejects_an_unknown_structure_kind(self) -> None:
        table = TableIR2(rows=((CellIR2(row=0, column=0, text="a", primitive_ids=("p1",)),),))
        document = DocumentIR2(
            provenance=IR2Provenance(source_id="s", generation_id="g"),
            pages=(PageIR2(page_id=PAGE, nodes=(NodeIR2(
                node_id="n", order=0, kind="layout.table",
                primitive_ids=("p1",), page_ids=(PAGE,), structure=table,
            ),)),),
        )
        payload = document_ir2_to_dict(document)
        payload["pages"][0]["nodes"][0]["structure"]["kind"] = "grafico"
        with self.assertRaises(ValueError):
            document_ir2_from_dict(payload)


class RenderTest(unittest.TestCase):
    def test_renders_a_markdown_table_with_a_header_rule(self) -> None:
        table = TableIR2(rows=(
            (CellIR2(row=0, column=0, text="D6", primitive_ids=("p1",)),
             CellIR2(row=0, column=1, text="ATTACCO", primitive_ids=("p2",))),
            (CellIR2(row=1, column=0, text="1", primitive_ids=("p3",)),
             CellIR2(row=1, column=1, text="Colpo", primitive_ids=("p4",))),
        ))
        self.assertEqual(
            render_table(table),
            "| D6 | ATTACCO |\n| --- | --- |\n| 1 | Colpo |",
        )

    def test_escapes_a_pipe_instead_of_dropping_it(self) -> None:
        table = TableIR2(rows=((CellIR2(row=0, column=0, text="a|b", primitive_ids=("p",)),),))
        self.assertIn("a\\|b", render_table(table))

    def test_an_empty_cell_keeps_the_column(self) -> None:
        table = TableIR2(rows=(
            (CellIR2(row=0, column=0, text="a", primitive_ids=("p",)),
             CellIR2(row=0, column=1, text="")),
        ))
        self.assertEqual(render_table(table).splitlines()[0].count("|"), 3)

    def test_the_table_is_rendered_in_the_page(self) -> None:
        table = TableIR2(rows=((CellIR2(row=0, column=0, text="a", primitive_ids=("p",)),),))
        page = PageIR2(page_id=PAGE, nodes=(NodeIR2(
            node_id="n", order=0, kind="layout.table",
            primitive_ids=("p",), page_ids=(PAGE,), structure=table,
        ),))
        self.assertIn("| a |", render_page_markdown(page))


class AdmittedBoundaryTest(unittest.TestCase):
    """`Criterio_ConfiniFase2InIR2_v1.md`: a boundary enters only if no line leaves."""

    def _region(self, admitted, gutters=((100.0, 110.0),)) -> TableRegionInput:
        return TableRegionInput(
            bbox=(0.0, 0.0, 200.0, 100.0),
            gutter_x_intervals=gutters,
            candidate_ids=("c1",),
            admitted_boundaries=admitted,
        )

    def test_a_boundary_no_line_crosses_splits_a_column(self) -> None:
        lines = group_source_lines([
            _span(1, 0, "01", 5.0, 0.0, width=20.0),
            _span(2, 0, "Sacco", 40.0, 0.0, width=50.0),
            _span(3, 0, "Stress", 120.0, 0.0),
        ])
        table, residuals = build_table(self._region(((28.0, 36.0),)), lines)
        assert table is not None
        self.assertEqual([c.text for c in table.rows[0]], ["01", "Sacco", "Stress"])
        self.assertEqual(residuals, [])

    def test_a_boundary_a_line_crosses_is_refused(self) -> None:
        lines = group_source_lines([
            _span(1, 0, "01", 5.0, 0.0, width=20.0),
            _span(2, 0, "Sacco", 40.0, 0.0, width=50.0),
            _span(3, 0, "prosa che lo attraversa", 5.0, 20.0, width=90.0),
        ])
        table, residuals = build_table(self._region(((28.0, 36.0),)), lines)
        assert table is not None
        self.assertEqual([c.text for c in table.rows[0]], ["01 Sacco", ""])
        self.assertEqual([c.text for c in table.rows[1]], ["prosa che lo attraversa", ""])
        self.assertEqual(residuals, [])

    def test_a_single_column_region_becomes_a_table(self) -> None:
        lines = group_source_lines([
            _span(1, 0, "1", 5.0, 0.0, width=10.0),
            _span(2, 0, "Colpo", 40.0, 0.0),
        ])
        table, residuals = build_table(self._region(((20.0, 35.0),), gutters=()), lines)
        assert table is not None
        self.assertEqual([c.text for c in table.rows[0]], ["1", "Colpo"])
        self.assertEqual(residuals, [])

    def test_a_single_column_region_crossed_by_a_line_stays_no_table(self) -> None:
        lines = group_source_lines([
            _span(1, 0, "1", 5.0, 0.0, width=10.0),
            _span(2, 0, "Colpo", 40.0, 0.0),
            _span(3, 0, "prosa che lo attraversa", 5.0, 20.0, width=90.0),
        ])
        table, residuals = build_table(self._region(((20.0, 35.0),), gutters=()), lines)
        self.assertIsNone(table)
        self.assertEqual(len(residuals), 3)


class RegionRepairTest(unittest.TestCase):
    """`Criterio_RiparazioneRegioneIR2_v1.md`: the prototype's two repairs in IR 2.

    **La riparazione non e' collegata**: il suo veto e' caduto due volte
    (`Esito_RiparazioneRegioneIR2_v1.md` e `_v2.md`), e `build_page_ir2` usa la
    regione grezza. Il codice resta in albero con il suo verbale, e questi test
    provano la funzione applicandola qui invece che nella pipeline."""

    def _table(self, spans, bbox=(0.0, 0.0, 200.0, 30.0)):
        riparata = _repaired_region(_region(bbox=bbox), group_source_lines(spans), set())
        page = build_page_ir2(
            page_id=PAGE,
            ordered_text_primitives=spans,
            table_regions=[riparata],
        )
        tables = [n for n in page.nodes if n.structure is not None]
        paragraphs = [n.text for n in page.nodes if n.text]
        return tables, paragraphs

    def _rows(self):
        return [
            _span(1, 0, "1", 10.0, 0.0),
            _span(2, 0, "Colpo", 120.0, 0.0),
            _span(3, 0, "2", 10.0, 20.0),
            _span(4, 0, "Taglio", 120.0, 20.0),
        ]

    def test_the_last_row_below_the_region_joins_the_table(self) -> None:
        spans = [*self._rows(), _span(5, 0, "3", 10.0, 40.0), _span(6, 0, "Fendente", 120.0, 40.0)]
        tables, paragraphs = self._table(spans)
        self.assertEqual([c.text for c in tables[0].structure.rows[-1]], ["3", "Fendente"])
        self.assertEqual(paragraphs, [])

    def test_a_header_above_the_region_joins_the_table(self) -> None:
        spans = [_span(7, 0, "D6", 10.0, -20.0), _span(8, 0, "ATTACCO", 120.0, -20.0), *self._rows()]
        tables, _ = self._table(spans)
        self.assertEqual([c.text for c in tables[0].structure.rows[0]], ["D6", "ATTACCO"])

    def test_prose_that_crosses_the_columns_stays_out(self) -> None:
        prose = _span(0, 0, "Una frase di prosa che attraversa", 10.0, -20.0, width=180.0)
        tables, paragraphs = self._table([prose, *self._rows()])
        self.assertEqual(len(tables[0].structure.rows), 2)
        self.assertEqual(paragraphs, ["Una frase di prosa che attraversa"])

    def test_a_line_sticking_out_of_the_region_is_held_whole(self) -> None:
        spans = [
            _span(1, 0, "1", 10.0, 0.0),
            _span(2, 0, "Colpo molto lungo", 120.0, 0.0, width=120.0),
            _span(3, 0, "2", 10.0, 20.0),
            _span(4, 0, "Taglio", 120.0, 20.0),
        ]
        tables, paragraphs = self._table(spans)
        self.assertEqual([c.text for c in tables[0].structure.rows[0]], ["1", "Colpo molto lungo"])
        self.assertEqual(paragraphs, [])

    def test_a_long_last_row_joins_once_the_region_is_widened(self) -> None:
        spans = [
            _span(1, 0, "1", 10.0, 0.0),
            _span(2, 0, "Colpo molto lungo", 120.0, 0.0, width=120.0),
            _span(3, 0, "2", 10.0, 20.0),
            _span(4, 0, "Taglio", 120.0, 20.0),
            _span(5, 0, "3", 10.0, 40.0),
            _span(6, 0, "Fendente anche lui lungo", 120.0, 40.0, width=120.0),
        ]
        tables, paragraphs = self._table(spans)
        self.assertEqual(
            [c.text for c in tables[0].structure.rows[-1]], ["3", "Fendente anche lui lungo"]
        )
        self.assertEqual(paragraphs, [])


class StatBlockAreaTest(unittest.TestCase):
    """`Criterio_SchedaControLaTabella_v1.md`: le righe di una scheda sono sue."""

    def _rows(self):
        return [
            _span(1, 0, "1", 10.0, 0.0),
            _span(2, 0, "Colpo", 120.0, 0.0),
            _span(3, 0, "2", 10.0, 20.0),
            _span(4, 0, "Taglio", 120.0, 20.0),
        ]

    def _page(self, spans, areas, bbox=(0.0, 0.0, 200.0, 30.0)):
        page = build_page_ir2(
            page_id=PAGE,
            ordered_text_primitives=spans,
            table_regions=[_region(bbox=bbox)],
            stat_block_areas=areas,
        )
        tables = [n for n in page.nodes if n.structure is not None]
        return tables, [n.text for n in page.nodes if n.text]

    def test_a_table_crossing_a_stat_block_does_not_take_its_lines(self) -> None:
        spans = self._rows()
        area = StatBlockAreaInput(
            bbox=(0.0, 15.0, 200.0, 40.0),
            primitive_ids=(spans[2].primitive_id, spans[3].primitive_id),
        )
        tables, paragraphs = self._page(spans, [area])
        self.assertEqual([[c.text for c in r] for r in tables[0].structure.rows], [["1", "Colpo"]])
        self.assertEqual(paragraphs, ["2", "Taglio"])

    def test_a_table_inside_a_stat_block_keeps_them(self) -> None:
        spans = self._rows()
        area = StatBlockAreaInput(
            bbox=(-10.0, -10.0, 210.0, 40.0),
            primitive_ids=tuple(span.primitive_id for span in spans),
        )
        tables, paragraphs = self._page(spans, [area])
        self.assertEqual(len(tables[0].structure.rows), 2)
        self.assertEqual(paragraphs, [])

    def test_the_repair_stops_at_a_stat_block(self) -> None:
        spans = [*self._rows(), _span(5, 0, "3", 10.0, 40.0), _span(6, 0, "Fendente", 120.0, 40.0)]
        area = StatBlockAreaInput(
            bbox=(0.0, 35.0, 200.0, 60.0),
            primitive_ids=(spans[4].primitive_id, spans[5].primitive_id),
        )
        tables, paragraphs = self._page(spans, [area])
        self.assertEqual(len(tables[0].structure.rows), 2)
        self.assertEqual(paragraphs, ["3", "Fendente"])

    def _due_righe_di_scheda(self):
        """Due righe nello **stesso blocco**: senza segnale il builder le salda,
        ed e' cio' che succede alle righe di una scheda."""
        return [
            _span(7, 0, "Ferocia: 3", 10.0, 0.0, width=80.0),
            _span(7, 1, "Movimento: 18", 10.0, 20.0, width=80.0),
        ]

    def _senza_tabella(self, spans, area):
        return build_page_ir2(
            page_id=PAGE,
            ordered_text_primitives=spans,
            table_regions=[],
            stat_block_areas=[area],
        )

    def test_without_record_starts_the_lines_stay_joined(self) -> None:
        spans = self._due_righe_di_scheda()
        area = StatBlockAreaInput(
            bbox=(-10.0, -10.0, 210.0, 40.0),
            primitive_ids=tuple(span.primitive_id for span in spans),
        )
        page = self._senza_tabella(spans, area)
        self.assertEqual(
            [n.text for n in page.nodes if n.text], ["Ferocia: 3 Movimento: 18"]
        )

    def test_a_record_start_opens_its_own_paragraph(self) -> None:
        """`Criterio_RigheDellaSchedaACapo_v1.md` §2: dentro una scheda una riga
        che apre un record apre un paragrafo, anche nello stesso blocco."""
        spans = self._due_righe_di_scheda()
        area = StatBlockAreaInput(
            bbox=(-10.0, -10.0, 210.0, 40.0),
            primitive_ids=tuple(span.primitive_id for span in spans),
            record_start_ids=(spans[1].primitive_id,),
        )
        page = self._senza_tabella(spans, area)
        self.assertEqual(
            [n.text for n in page.nodes if n.text], ["Ferocia: 3", "Movimento: 18"]
        )

    def test_without_stat_blocks_nothing_changes(self) -> None:
        tables, paragraphs = self._page(self._rows(), [])
        self.assertEqual(len(tables[0].structure.rows), 2)
        self.assertEqual(paragraphs, [])


if __name__ == "__main__":
    unittest.main()
