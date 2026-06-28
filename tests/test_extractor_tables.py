import unittest

from extractor import (
    TableBlock,
    _bbox_contains,
    _bbox_overlaps_any,
    _find_table_regions,
    _is_meaningful_table,
    _rebuild_numbered_table_from_words,
    _rebuild_tables_from_vector_regions,
    _rebuild_temporal_units_table_from_words,
    _table_fragments_non_empty_in_region,
)


class FakeTable:
    def __init__(self, bbox, rows=None):
        self.bbox = bbox
        self._rows = rows or [["cell"]]

    def extract(self):
        return self._rows


class FakePage:
    def __init__(self, tables, text_line_tables=None, width=200.0, height=200.0):
        self._tables = tables
        self._text_line_tables = text_line_tables or []
        self.width = width
        self.height = height

    def find_tables(self, table_settings=None):
        if table_settings == {"vertical_strategy": "text", "horizontal_strategy": "lines"}:
            return self._text_line_tables
        return self._tables


class ExtractorTablesTest(unittest.TestCase):
    def test_find_table_regions_includes_single_row_candidate_bbox(self):
        page = FakePage([FakeTable((10, 20, 100, 40))])

        regions = _find_table_regions(page)

        self.assertEqual(regions, [(10.0, 20.0, 100.0, 40.0)])

    def test_find_table_regions_accepts_valid_text_lines_region(self):
        default = FakeTable((10, 40, 100, 60))
        text_lines = FakeTable(
            (10, 40, 100, 140),
            rows=[
                ["D6", "Luogo", "Ritrovamento"],
                ["1", "Casa", "Dettaglio"],
                ["2", "Mulino", "Dettaglio"],
            ],
        )
        page = FakePage([default], [text_lines], width=120.0, height=200.0)

        regions = _find_table_regions(page)

        self.assertEqual(regions, [(8.0, 38.0, 102.0, 142.0)])

    def test_find_table_regions_rejects_too_tall_text_lines_region(self):
        default = FakeTable((10, 40, 100, 60))
        text_lines = FakeTable(
            (10, 10, 100, 190),
            rows=[
                ["D6", "Luogo", "Ritrovamento"],
                ["1", "Casa", "Dettaglio"],
                ["2", "Mulino", "Dettaglio"],
            ],
        )
        page = FakePage([default], [text_lines], width=120.0, height=200.0)

        regions = _find_table_regions(page)

        self.assertEqual(regions, [(10.0, 40.0, 100.0, 60.0)])

    def test_find_table_regions_deduplicates_contained_regions_in_favor_of_larger_one(self):
        default = FakeTable((20, 60, 80, 80))
        text_lines = FakeTable(
            (10, 40, 100, 140),
            rows=[
                ["D6", "Luogo", "Ritrovamento"],
                ["1", "Casa", "Dettaglio"],
                ["2", "Mulino", "Dettaglio"],
            ],
        )
        page = FakePage([default], [text_lines], width=120.0, height=200.0)

        regions = _find_table_regions(page)

        self.assertEqual(regions, [(8.0, 38.0, 102.0, 142.0)])

    def test_vector_bbox_strongly_overlapping_table_region_is_excluded(self):
        vector_bbox = (10.0, 20.0, 100.0, 40.0)
        table_regions = [(12.0, 20.0, 98.0, 40.0)]

        overlaps = _bbox_overlaps_any(vector_bbox, table_regions, threshold=0.8)

        self.assertTrue(overlaps)

    def test_vector_bbox_not_overlapping_table_region_is_kept(self):
        vector_bbox = (10.0, 20.0, 100.0, 40.0)
        table_regions = [(120.0, 20.0, 200.0, 40.0)]

        overlaps = _bbox_overlaps_any(vector_bbox, table_regions, threshold=0.8)

        self.assertFalse(overlaps)

    def test_meaningful_table_rejects_sparse_large_false_positive(self):
        rows = [["" for _ in range(15)] for _ in range(14)]
        for index in range(6):
            rows[index][index] = f"cell{index}"

        self.assertFalse(_is_meaningful_table(rows))

    def test_meaningful_table_rejects_empty_table(self):
        rows = [["", ""], ["", ""]]

        self.assertFalse(_is_meaningful_table(rows))

    def test_meaningful_table_accepts_real_two_column_table(self):
        rows = [["Tiro", "Stirpe"], ["1", "Umano"], ["2", "Anatra"], ["3", "Elfo"]]

        self.assertTrue(_is_meaningful_table(rows))

    def test_meaningful_table_accepts_d6_table_like_page_8(self):
        rows = [["D6", "Luogo", "Ritrovamento", "Dettagli e atmosfera"]]
        for row_num in range(1, 7):
            rows.append(
                [
                    str(row_num),
                    f"Luogo {row_num}",
                    f"Ritrovamento {row_num}",
                    f"Dettagli {row_num}",
                ]
            )

        self.assertTrue(_is_meaningful_table(rows))

    def test_meaningful_table_rejects_two_by_one_label(self):
        rows = [["REGOLE OPZIONALI"], [""]]

        self.assertFalse(_is_meaningful_table(rows))

    def test_rebuild_tables_from_vector_regions_handles_d12_stirpe(self):
        words = [
            (144.6, 595.2, 158.8, 604.8, "D12"),
            (171.5, 595.2, 202.0, 604.8, "STIRPE"),
            (144.7, 611.5, 158.6, 622.8, "1–4"),
            (171.5, 611.5, 201.5, 622.8, "Umano"),
            (314.7, 614.2, 382.0, 628.8, "LINGUAGGI"),
            (143.2, 629.1, 160.1, 640.4, "5–7"),
            (171.5, 629.1, 204.0, 640.4, "Halfling"),
            (143.2, 646.7, 160.1, 658.1, "8–9"),
            (171.5, 646.7, 193.4, 658.1, "Nano"),
            (147.4, 664.4, 155.9, 675.7, "10"),
            (171.5, 664.4, 187.5, 675.7, "Elfo"),
            (148.8, 682.0, 154.5, 693.4, "11"),
            (171.5, 682.0, 208.1, 693.4, "Mallardo"),
            (147.4, 699.7, 155.9, 711.0, "12"),
            (171.5, 699.7, 207.6, 711.0, "Lupinide"),
        ]

        rebuilt = _rebuild_tables_from_vector_regions(words, [(140.0, 606.0, 215.0, 696.0)])

        self.assertEqual(len(rebuilt), 1)
        rows, bbox = rebuilt[0]
        self.assertEqual(
            rows,
            [
                ["D12", "STIRPE"],
                ["1–4", "Umano"],
                ["5–7", "Halfling"],
                ["8–9", "Nano"],
                ["10", "Elfo"],
                ["11", "Mallardo"],
                ["12", "Lupinide"],
            ],
        )
        self.assertEqual(bbox, (143.2, 595.2, 208.1, 711.0))

    def test_rebuild_tables_from_vector_regions_handles_side_by_side_tables(self):
        words = [
            (10, 10, 22, 20, "D6"),
            (40, 10, 70, 20, "NOME"),
            (10, 30, 15, 40, "1"),
            (40, 30, 70, 40, "Alda"),
            (10, 50, 15, 60, "2"),
            (40, 50, 70, 60, "Boro"),
            (10, 70, 15, 80, "3"),
            (40, 70, 70, 80, "Cora"),
            (120, 10, 132, 20, "D6"),
            (150, 10, 180, 20, "NOME"),
            (120, 30, 125, 40, "1"),
            (150, 30, 180, 40, "Dario"),
            (120, 50, 125, 60, "2"),
            (150, 50, 180, 60, "Erin"),
            (120, 70, 125, 80, "3"),
            (150, 70, 180, 80, "Fara"),
        ]

        rebuilt = _rebuild_tables_from_vector_regions(
            words,
            [(8.0, 24.0, 80.0, 74.0), (118.0, 24.0, 190.0, 74.0)],
        )

        self.assertEqual(
            [rows for rows, _ in rebuilt],
            [
                [["D6", "NOME"], ["1", "Alda"], ["2", "Boro"], ["3", "Cora"]],
                [["D6", "NOME"], ["1", "Dario"], ["2", "Erin"], ["3", "Fara"]],
            ],
        )

    def test_rebuild_tables_from_vector_regions_merges_multiline_logical_rows(self):
        words = [
            (10, 10, 22, 20, "D6"),
            (40, 10, 115, 20, "ATTREZZATURA"),
            (10, 30, 25, 40, "1–2"),
            (40, 30, 78, 40, "Martello"),
            (80, 30, 120, 40, "d’arme,"),
            (40, 42, 82, 52, "armatura"),
            (84, 42, 94, 52, "di"),
            (96, 42, 125, 52, "cuoio,"),
            (40, 54, 68, 64, "torcia"),
            (10, 76, 25, 86, "3–4"),
            (40, 76, 78, 86, "Accetta,"),
            (40, 88, 82, 98, "armatura"),
            (84, 88, 94, 98, "di"),
            (96, 88, 125, 98, "cuoio"),
            (10, 110, 25, 120, "5–6"),
            (40, 110, 80, 120, "Coltello,"),
            (40, 122, 82, 132, "armatura"),
            (84, 122, 94, 132, "di"),
            (96, 122, 125, 132, "cuoio"),
        ]

        rebuilt = _rebuild_tables_from_vector_regions(words, [(8.0, 24.0, 135.0, 126.0)])

        self.assertEqual(len(rebuilt), 1)
        self.assertEqual(
            rebuilt[0][0],
            [
                ["D6", "ATTREZZATURA"],
                ["1–2", "Martello d’arme, armatura di cuoio, torcia"],
                ["3–4", "Accetta, armatura di cuoio"],
                ["5–6", "Coltello, armatura di cuoio"],
            ],
        )

    def test_rebuild_tables_from_vector_regions_stops_before_next_table_after_gap(self):
        words = [
            (10, 10, 70, 20, "ATTREZZATURA"),
            (90, 10, 140, 20, "VALORE"),
            (10, 30, 16, 40, "1"),
            (90, 30, 120, 40, "Corda"),
            (10, 50, 16, 60, "2"),
            (90, 50, 120, 60, "Torcia"),
            (10, 100, 80, 110, "SOPRANNOME"),
            (90, 100, 140, 110, "ORIGINE"),
            (10, 120, 16, 130, "1"),
            (90, 120, 120, 130, "Rosso"),
            (10, 140, 16, 150, "2"),
            (90, 140, 120, 150, "Lesto"),
        ]

        rebuilt = _rebuild_tables_from_vector_regions(words, [(8.0, 24.0, 150.0, 145.0)])

        self.assertEqual(len(rebuilt), 2)
        self.assertEqual(
            rebuilt[0][0], [["ATTREZZATURA", "VALORE"], ["1", "Corda"], ["2", "Torcia"]]
        )
        self.assertEqual(rebuilt[1][0], [["SOPRANNOME", "ORIGINE"], ["1", "Rosso"], ["2", "Lesto"]])

    def test_rebuild_tables_from_vector_regions_rejects_paragraph_box(self):
        words = [
            (10, 10, 40, 20, "Questo"),
            (42, 10, 70, 20, "box"),
            (72, 10, 110, 20, "contiene"),
            (10, 30, 45, 40, "solo"),
            (47, 30, 90, 40, "testo"),
            (92, 30, 135, 40, "normale"),
            (10, 50, 50, 60, "senza"),
            (52, 50, 95, 60, "colonne"),
            (97, 50, 130, 60, "vere"),
        ]

        rebuilt = _rebuild_tables_from_vector_regions(words, [(8.0, 8.0, 140.0, 62.0)])

        self.assertEqual(rebuilt, [])

    def test_rebuild_temporal_units_table_from_aligned_words(self):
        words = [
            (68.1, 512.8, 94.4, 522.5, "UNITÀ"),
            (68.1, 521.8, 116.2, 531.5, "TEMPORALI"),
            (127.6, 521.8, 162.0, 531.5, "DURATA"),
            (182.6, 521.8, 212.0, 531.5, "TEMPO"),
            (214.6, 521.8, 268.8, 531.5, "NECESSARIO"),
            (271.4, 521.8, 287.8, 531.5, "PER"),
            (68.0, 538.1, 94.9, 549.5, "Round"),
            (127.6, 538.1, 136.1, 549.5, "10"),
            (138.1, 538.1, 170.4, 549.5, "secondi"),
            (182.5, 538.1, 219.3, 549.5, "Eseguire"),
            (221.3, 538.1, 261.0, 549.5, "un’azione"),
            (263.0, 538.1, 270.7, 549.5, "in"),
            (182.5, 550.1, 249.2, 561.5, "combattimento,"),
            (251.2, 550.1, 287.6, 561.5, "eseguire"),
            (182.5, 562.1, 193.1, 573.5, "un"),
            (195.1, 562.1, 219.7, 573.5, "round"),
            (221.7, 562.1, 229.4, 573.5, "di"),
            (231.4, 562.1, 257.8, 573.5, "riposo"),
            (182.5, 574.1, 203.3, 585.5, "(pag."),
            (205.3, 574.1, 221.9, 585.5, "52)."),
            (68.0, 591.7, 108.6, 603.1, "Intervallo"),
            (127.6, 591.7, 136.1, 603.1, "15"),
            (138.1, 591.7, 165.1, 603.1, "minuti"),
            (182.5, 591.7, 220.5, 603.1, "Esplorare"),
            (222.0, 591.7, 237.0, 603.1, "una"),
            (238.4, 591.7, 267.1, 603.1, "stanza,"),
            (182.5, 603.7, 217.1, 615.1, "eseguire"),
            (218.5, 603.7, 228.8, 615.1, "un"),
            (230.2, 603.7, 268.0, 615.1, "intervallo"),
            (269.4, 603.7, 276.8, 615.1, "di"),
            (182.5, 615.7, 207.6, 627.1, "riposo"),
            (209.0, 615.7, 228.7, 627.1, "(pag."),
            (230.1, 615.7, 245.9, 627.1, "52)."),
            (68.0, 633.4, 100.6, 644.7, "Periodo"),
            (127.6, 633.4, 133.2, 644.7, "6"),
            (135.2, 633.4, 149.1, 644.7, "ore"),
            (182.5, 633.4, 229.1, 644.7, "Camminare"),
            (230.7, 633.4, 244.3, 644.7, "per"),
            (245.9, 633.4, 254.3, 644.7, "15"),
            (255.9, 633.4, 270.7, 644.7, "km,"),
            (182.5, 645.4, 217.7, 656.7, "eseguire"),
            (219.3, 645.4, 229.7, 656.7, "un"),
            (231.3, 645.4, 262.1, 656.7, "periodo"),
            (263.8, 645.4, 271.3, 656.7, "di"),
            (182.5, 657.4, 208.0, 668.7, "riposo"),
            (209.7, 657.4, 229.7, 668.7, "(pag."),
            (231.3, 657.4, 247.3, 668.7, "52)."),
        ]

        rebuilt = _rebuild_temporal_units_table_from_words(words)

        self.assertIsNotNone(rebuilt)
        rows, _ = rebuilt
        self.assertEqual(
            rows,
            [
                ["UNITÀ TEMPORALI", "DURATA", "TEMPO NECESSARIO PER"],
                [
                    "Round",
                    "10 secondi",
                    "Eseguire un’azione in combattimento, eseguire un round di riposo (pag. 52).",
                ],
                [
                    "Intervallo",
                    "15 minuti",
                    "Esplorare una stanza, eseguire un intervallo di riposo (pag. 52).",
                ],
                [
                    "Periodo",
                    "6 ore",
                    "Camminare per 15 km, eseguire un periodo di riposo (pag. 52).",
                ],
            ],
        )

    def test_rebuild_numbered_table_from_words_splits_fused_d6_row_by_coordinates(self):
        words = [
            (10, 10, 20, 20, "D6"),
            (30, 10, 50, 20, "Luogo"),
            (90, 10, 140, 20, "Ritrovamento"),
            (180, 10, 220, 20, "Dettagli"),
            (222, 10, 228, 20, "e"),
            (230, 10, 270, 20, "atmosfera"),
        ]
        for row_num, y in enumerate([40, 70, 100], start=1):
            words.extend(
                [
                    (10, y, 15, y + 10, str(row_num)),
                    (30, y, 38, y + 10, "Il"),
                    (40, y, 65, y + 10, f"luogo{row_num}"),
                    (90, y, 105, y + 10, "Il"),
                    (107, y, 145, y + 10, f"ritrovamento{row_num}"),
                    (180, y, 220, y + 10, f"dettaglio{row_num}"),
                ]
            )

        rows = _rebuild_numbered_table_from_words(words, (0.0, 0.0, 300.0, 130.0))

        self.assertIsNotNone(rows)
        self.assertEqual(rows[0], ["D6", "Luogo", "Ritrovamento", "Dettagli e atmosfera"])
        self.assertEqual(rows[2], ["2", "Il luogo2", "Il ritrovamento2", "dettaglio2"])

    def test_rebuild_numbered_table_from_words_rejects_missing_essential_cells(self):
        words = [
            (10, 10, 20, 20, "D6"),
            (30, 10, 50, 20, "Luogo"),
            (90, 10, 140, 20, "Ritrovamento"),
            (180, 10, 220, 20, "Dettagli"),
            (10, 40, 15, 50, "1"),
            (30, 40, 60, 50, "Casa"),
            (180, 40, 220, 50, "dettaglio"),
            (10, 70, 15, 80, "2"),
            (30, 70, 60, 80, "Mulino"),
            (90, 70, 130, 80, "registro"),
            (180, 70, 220, 80, "dettaglio"),
            (10, 100, 15, 110, "3"),
            (30, 100, 60, 110, "Pozzo"),
            (90, 100, 130, 110, "secchio"),
            (180, 100, 220, 110, "dettaglio"),
        ]

        rows = _rebuild_numbered_table_from_words(words, (0.0, 0.0, 300.0, 130.0))

        self.assertIsNone(rows)

    def test_fallback_region_can_identify_contained_pdfplumber_fragments(self):
        fallback_region = (8.0, 8.0, 220.0, 120.0)
        fragment = TableBlock(
            rows=[["1", "Casa"], ["2", "Mulino"]],
            bbox=(10.0, 20.0, 100.0, 60.0),
            page_num=0,
            index=0,
        )

        self.assertTrue(_bbox_contains(fallback_region, fragment.bbox))
        self.assertEqual(_table_fragments_non_empty_in_region([fragment], fallback_region), 4)


if __name__ == "__main__":
    unittest.main()
