"""
extractor.py — Estrazione strutturata da PDF.

Gestisce tre tipi di contenuto grafico:
  - Immagini raster (JPEG, PNG, JP2...): estratte direttamente dai metadati
    del PDF come file binari, salvate nel formato originale.
  - Illustrazioni vettoriali: rilevate tramite clustering dei path vettoriali
    (get_drawings), esportate come SVG ritagliando la regione su una pagina
    temporanea con show_pdf_page().
  - Tabelle: rilevate da pdfplumber, salvate come CSV.

Tutto il testo viene estratto con posizione spaziale per ricostruire l'ordine
di lettura corretto (singola o doppia colonna).

Il filtro `filter_repeated_blocks` rimuove intestazioni, piè di pagina e
filigrane identificandoli statisticamente per posizione Y e testo normalizzato.

Struttura cartelle output:
  {output_dir}/{book_name}_extracted/
      images/    ← raster (PNG, JPEG, ...)
      vectors/   ← illustrazioni vettoriali (SVG)
      tables/    ← tabelle (CSV)
"""

from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import re as _re
import statistics
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
import pdfplumber
from PIL import Image

from config import LayoutConfig

_NONSTANDARD_CHAR_RE = _re.compile(r"^[^\w\s]+$")
_DIE_HEADER_RE = _re.compile(r"^D(?P<sides>\d{1,3})$", _re.IGNORECASE)
_DIE_BODY_VALUE_RE = _re.compile(r"^(?P<start>\d{1,3})(?:\s*[-–—]\s*(?P<end>\d{1,3}))?$")
_TABLE_TEXT_LINES_SETTINGS = {"vertical_strategy": "text", "horizontal_strategy": "lines"}
# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

BBox = tuple[float, float, float, float]
WordItem = tuple[float, float, float, float, str]


@dataclass(frozen=True)
class _CompactDieTableInfo:
    header: tuple[str, str]
    sides: int
    values: frozenset[int]


@dataclass
class TextSpan:
    text: str
    font: str
    size: float
    bold: bool
    italic: bool
    bbox: tuple[float, float, float, float]


@dataclass
class TextBlock:
    spans: list[TextSpan]
    bbox: tuple[float, float, float, float]

    @property
    def text(self) -> str:
        return _join_text_spans(self.spans)

    @property
    def avg_font_size(self) -> float:
        sizes = [s.size for s in self.spans if s.text.strip()]
        return statistics.mean(sizes) if sizes else 0.0

    @property
    def is_bold(self) -> bool:
        return any(s.bold for s in self.spans if s.text.strip())

    @property
    def is_italic(self) -> bool:
        return all(s.italic for s in self.spans if s.text.strip())


def _join_text_spans(spans: list[TextSpan]) -> str:
    clean_spans = [span for span in spans if span.text.strip()]
    if not clean_spans:
        return ""

    text = clean_spans[0].text.strip()
    previous = clean_spans[0]

    for span in clean_spans[1:]:
        current = span.text.strip()
        if _should_join_span_without_space(previous, span):
            text += current
        else:
            text += f" {current}"
        previous = span

    return text


def _line_text_from_words(
    words: list[tuple[float, float, float, float, str, int, int, int]],
) -> str:
    clean_words = sorted((word for word in words if word[4].strip()), key=lambda word: word[0])
    if not clean_words:
        return ""

    text = clean_words[0][4].strip()
    for word in clean_words[1:]:
        current = word[4].strip()
        if current[0] in ",.;:!?)]»":
            text += current
        else:
            text += f" {current}"

    return text


def _normalize_words(raw_words: Sequence[object]) -> list[WordItem]:
    normalized: list[WordItem] = []
    for raw_word in raw_words:
        if not isinstance(raw_word, (list, tuple)) or len(raw_word) < 5:
            continue
        text = str(raw_word[4]).strip()
        if not text:
            continue
        normalized.append(
            (
                float(raw_word[0]),
                float(raw_word[1]),
                float(raw_word[2]),
                float(raw_word[3]),
                text,
            )
        )
    return normalized


def _text_from_block(block: tuple[float, float, float, float, str, int, int]) -> str:
    return " ".join(block[4].strip().split())


def _find_table_regions(plumb_page) -> list[tuple[float, float, float, float]]:
    default_regions = _table_bboxes(_safe_find_tables(plumb_page))
    text_line_regions = []

    text_line_tables = _safe_find_tables(
        plumb_page,
        _TABLE_TEXT_LINES_SETTINGS,
    )
    for table in text_line_tables:
        bbox = _table_bbox(table)
        if bbox is None:
            continue
        if _is_valid_text_line_table_region(table, bbox, default_regions, plumb_page):
            text_line_regions.append(_pad_bbox_to_page(bbox, plumb_page, padding=2.0))

    return _dedupe_table_regions([*default_regions, *text_line_regions])


def _safe_find_tables(
    plumb_page: Any,
    table_settings: dict[str, str] | None = None,
) -> list[Any]:
    try:
        if table_settings is None:
            return list(plumb_page.find_tables())
        return list(plumb_page.find_tables(table_settings=table_settings))
    except Exception:
        return []


def _table_bboxes(tables: Sequence[Any]) -> list[BBox]:
    regions = []
    for table in tables:
        bbox = _table_bbox(table)
        if bbox is not None:
            regions.append(bbox)
    return regions


def _table_bbox(table: Any) -> BBox | None:
    bbox = getattr(table, "bbox", None)
    if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
        return (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
    return None


def _is_valid_text_line_table_region(
    table: Any,
    bbox: BBox,
    default_regions: list[BBox],
    plumb_page: Any,
) -> bool:
    rows = table.extract() or []
    row_count = len(rows)
    column_count = max((len(row) for row in rows), default=0)
    non_empty = sum(1 for row in rows for cell in row if (cell or "").strip())
    page_height = float(getattr(plumb_page, "height", bbox[3]) or bbox[3])

    return (
        row_count >= 3
        and column_count >= 3
        and non_empty >= 8
        and (bbox[3] - bbox[1]) <= page_height * 0.75
        and any(
            _horizontal_overlap_ratio(bbox, default_region) >= 0.5
            for default_region in default_regions
        )
    )


def _horizontal_overlap_ratio(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> float:
    width = max(min(first[2] - first[0], second[2] - second[0]), 1.0)
    overlap = max(0.0, min(first[2], second[2]) - max(first[0], second[0]))
    return overlap / width


def _pad_bbox_to_page(
    bbox: tuple[float, float, float, float],
    plumb_page,
    padding: float,
) -> tuple[float, float, float, float]:
    width = float(getattr(plumb_page, "width", bbox[2]) or bbox[2])
    height = float(getattr(plumb_page, "height", bbox[3]) or bbox[3])
    return (
        max(0.0, bbox[0] - padding),
        max(0.0, bbox[1] - padding),
        min(width, bbox[2] + padding),
        min(height, bbox[3] + padding),
    )


def _dedupe_table_regions(
    regions: list[tuple[float, float, float, float]],
) -> list[tuple[float, float, float, float]]:
    deduped = []
    for region in sorted(regions, key=_bbox_area, reverse=True):
        if any(
            _bbox_contains(existing, region) or _bbox_overlap_ratio(region, existing) >= 0.95
            for existing in deduped
        ):
            continue
        deduped.append(region)
    return sorted(deduped, key=lambda bbox: (bbox[1], bbox[0]))


def _table_like_regions(plumb_page: Any) -> list[BBox]:
    regions: list[BBox] = []
    for table in _safe_find_tables(plumb_page, _TABLE_TEXT_LINES_SETTINGS):
        bbox = _table_bbox(table)
        if bbox is None:
            continue
        rows = table.extract() or []
        if _table_like_header_from_rows(rows) is not None:
            regions.append(_pad_bbox_to_page(bbox, plumb_page, padding=2.0))
    return regions


def _table_like_header_from_rows(rows: list[list[str | None]]) -> tuple[str, int] | None:
    for row in rows:
        cells = [(cell or "").strip() for cell in row]
        if not cells:
            continue
        first = cells[0].split()[0] if cells[0].split() else ""
        match = _DIE_HEADER_RE.match(first)
        if match is not None:
            return first.upper(), int(match.group("sides"))
    return None


def _words_in_bbox(
    words: Sequence[WordItem],
    bbox: BBox,
    padding: float = 16.0,
) -> list[WordItem]:
    x0, y0, x1, y1 = bbox
    region = (x0 - padding, y0 - padding, x1 + padding, y1 + padding)
    selected: list[WordItem] = []

    for word in words:
        wx0, wy0, wx1, wy1, raw_text = word
        text = str(raw_text).strip()
        if not text:
            continue

        word_bbox = (float(wx0), float(wy0), float(wx1), float(wy1))
        center_x = (word_bbox[0] + word_bbox[2]) / 2
        center_y = (word_bbox[1] + word_bbox[3]) / 2
        if region[0] <= center_x <= region[2] and region[1] <= center_y <= region[3]:
            selected.append((word_bbox[0], word_bbox[1], word_bbox[2], word_bbox[3], text))

    return sorted(selected, key=lambda item: (item[1], item[0]))


def _rebuild_numbered_table_from_words(
    words: Sequence[WordItem],
    region: BBox,
) -> list[list[str]] | None:
    region_words = _words_in_bbox(words, region, padding=16.0)
    header = _numbered_table_header(region_words)
    if header is None:
        return None

    header_row, die_sides, starts, header_bottom = header
    row_starts = _numbered_table_row_starts(
        region_words,
        die_sides,
        header_bottom,
        starts[0],
    )
    if len(row_starts) < 3:
        return None

    bands = _table_row_bands(row_starts)
    rows_by_number = {num: ["" for _ in starts] for num, _, _ in row_starts}
    cell_words: dict[tuple[int, int], list[WordItem]] = defaultdict(list)

    for word in region_words:
        center_y = (word[1] + word[3]) / 2
        if center_y <= header_bottom:
            continue
        row_num = _table_row_for_y(center_y, bands)
        if row_num is None:
            continue
        col = _table_column_for_x(word[0], starts)
        cell_words[(row_num, col)].append(word)

    for (row_num, col), grouped_words in cell_words.items():
        rows_by_number[row_num][col] = _join_table_words(grouped_words)

    ordered_rows = [rows_by_number[num] for num, _, _ in row_starts]
    if any(not cell.strip() for row in ordered_rows for cell in row):
        return None
    return [header_row, *ordered_rows]


def _numbered_table_header(
    words: Sequence[WordItem],
) -> tuple[list[str], int, list[float], float] | None:
    for word in words:
        match = _DIE_HEADER_RE.match(word[4])
        if match is None:
            continue
        center_y = (word[1] + word[3]) / 2
        line_words = [
            candidate
            for candidate in words
            if abs(((candidate[1] + candidate[3]) / 2) - center_y) <= 3.0
        ]
        line_words.sort(key=lambda item: item[0])
        if len(line_words) < 3:
            continue
        starts = [item[0] for item in line_words[:4]]
        if len(starts) < 3:
            continue
        header_row = [item[4] for item in line_words[: len(starts) - 1]]
        header_row.append(_join_table_words(line_words[len(starts) - 1 :]))
        return (
            header_row,
            int(match.group("sides")),
            starts,
            max(item[3] for item in line_words),
        )
    return None


def _numbered_table_row_starts(
    words: Sequence[WordItem],
    die_sides: int,
    header_bottom: float,
    first_column_x: float,
) -> list[tuple[int, float, float]]:
    starts = []
    for word in words:
        text = word[4]
        if not text.isdigit():
            continue

        number = int(text)
        if not (1 <= number <= die_sides):
            continue

        if abs(word[0] - first_column_x) > 12.0:
            continue

        center_y = (word[1] + word[3]) / 2
        if center_y <= header_bottom:
            continue

        starts.append((number, word[1], word[3]))

    starts.sort(key=lambda item: item[1])
    return starts


def _table_row_bands(row_starts: list[tuple[int, float, float]]) -> dict[int, tuple[float, float]]:
    bands = {}
    for index, (num, y0, y1) in enumerate(row_starts):
        top = (row_starts[index - 1][1] + y0) / 2 if index > 0 else y0 - 20.0
        bottom = (y1 + row_starts[index + 1][1]) / 2 if index + 1 < len(row_starts) else y1 + 40.0
        bands[num] = (top, bottom)
    return bands


def _table_row_for_y(center_y: float, bands: dict[int, tuple[float, float]]) -> int | None:
    for num, (top, bottom) in bands.items():
        if top <= center_y <= bottom:
            return num
    return None


def _rebuild_tables_from_vector_regions(
    words: Sequence[WordItem],
    vector_regions: Sequence[BBox],
) -> list[tuple[list[list[str]], BBox]]:
    rebuilt: list[tuple[list[list[str]], BBox]] = []
    for region in sorted(vector_regions, key=lambda bbox: (bbox[1], bbox[0])):
        expanded = _expand_bbox(region, x_padding=4.0, y_padding=18.0)
        region_words = _words_in_bbox(words, expanded, padding=0.0)
        for segment in _table_line_segments(region_words):
            table = _rebuild_table_from_word_lines(segment)
            if table is None:
                continue
            rows, bbox = table
            if not _is_meaningful_table(rows):
                continue
            if any(_bbox_overlap_ratio(bbox, existing_bbox) >= 0.8 for _, existing_bbox in rebuilt):
                continue
            rebuilt.append((rows, bbox))

    rebuilt = _merge_compact_die_table_candidates(rebuilt)
    return _merge_compact_die_tables_with_loose_fragments(rebuilt, words)


def _merge_compact_die_table_candidates(
    tables: Sequence[tuple[list[list[str]], BBox]],
) -> list[tuple[list[list[str]], BBox]]:
    merged: list[tuple[list[list[str]], BBox]] = []
    consumed: set[int] = set()

    for index, (rows, bbox) in enumerate(tables):
        if index in consumed:
            continue

        current_rows = rows
        current_bbox = bbox
        current_info = _compact_die_table_info(current_rows)

        if current_info is not None:
            for other_index in range(index + 1, len(tables)):
                if other_index in consumed:
                    continue

                other_rows, other_bbox = tables[other_index]
                other_info = _compact_die_table_info(other_rows)
                if other_info is None:
                    continue
                if not _compact_die_tables_can_merge(
                    current_info,
                    current_bbox,
                    other_info,
                    other_bbox,
                ):
                    continue

                current_rows = _merge_compact_die_rows(
                    current_rows,
                    other_rows,
                    current_info.sides,
                )
                current_bbox = _union_bboxes([current_bbox, other_bbox])
                consumed.add(other_index)
                current_info = _compact_die_table_info(current_rows)

                if current_info is None:
                    break

        merged.append((current_rows, current_bbox))

    return sorted(merged, key=lambda item: (item[1][1], item[1][0]))


def _merge_compact_die_tables_with_loose_fragments(
    tables: Sequence[tuple[list[list[str]], BBox]],
    words: Sequence[WordItem],
) -> list[tuple[list[list[str]], BBox]]:
    merged: list[tuple[list[list[str]], BBox]] = []

    for rows, bbox in tables:
        fragment = _find_loose_compact_die_table_fragment(rows, bbox, words)
        if fragment is None:
            merged.append((rows, bbox))
            continue

        fragment_rows, fragment_bbox = fragment
        info = _compact_die_table_info(rows)
        if info is None:
            merged.append((rows, bbox))
            continue

        merged_rows = _merge_compact_die_rows(rows, fragment_rows, info.sides)
        merged_bbox = _union_bboxes([bbox, fragment_bbox])
        merged.append((merged_rows, merged_bbox))

    return sorted(merged, key=lambda item: (item[1][1], item[1][0]))


def _compact_die_tables_can_merge(
    left_info: _CompactDieTableInfo,
    left_bbox: BBox,
    right_info: _CompactDieTableInfo,
    right_bbox: BBox,
) -> bool:
    if left_info.header != right_info.header or left_info.sides != right_info.sides:
        return False
    if not _die_value_sets_are_complementary(left_info.values, right_info.values):
        return False
    if not _bboxes_are_side_by_side(left_bbox, right_bbox):
        return False
    return _vertical_overlap_ratio(left_bbox, right_bbox) >= 0.65


def _compact_die_table_info(rows: Sequence[Sequence[str]]) -> _CompactDieTableInfo | None:
    if len(rows) < 3:
        return None

    header = [cell.strip() for cell in rows[0]]
    if len(header) != 2:
        return None

    match = _DIE_HEADER_RE.match(header[0])
    if match is None or not header[1]:
        return None

    sides = int(match.group("sides"))
    values: set[int] = set()

    for row in rows[1:]:
        if len(row) < 2 or not row[1].strip():
            return None

        row_values = _die_body_values(row[0], sides)
        if row_values is None or values.intersection(row_values):
            return None
        values.update(row_values)

    if len(values) < 2:
        return None

    return _CompactDieTableInfo(
        header=(header[0].upper(), _normalize_table_header_cell(header[1])),
        sides=sides,
        values=frozenset(values),
    )


def _normalize_table_header_cell(text: str) -> str:
    return " ".join(text.strip().upper().split())


def _die_body_values(text: str, die_sides: int) -> frozenset[int] | None:
    match = _DIE_BODY_VALUE_RE.match(text.strip())
    if match is None:
        return None

    start = int(match.group("start"))
    end = int(match.group("end") or start)
    if start > end or start < 1 or end > die_sides:
        return None

    return frozenset(range(start, end + 1))


def _die_value_sets_are_complementary(
    first: frozenset[int],
    second: frozenset[int],
) -> bool:
    if not first or not second or not first.isdisjoint(second):
        return False
    return len(first | second) > max(len(first), len(second))


def _die_value_sets_complete_die(
    first: frozenset[int],
    second: frozenset[int],
    die_sides: int,
) -> bool:
    if not _die_value_sets_are_complementary(first, second):
        return False
    return first | second == frozenset(range(1, die_sides + 1))


def _bboxes_are_side_by_side(first: BBox, second: BBox) -> bool:
    first_width = max(first[2] - first[0], 1.0)
    second_width = max(second[2] - second[0], 1.0)
    max_reasonable_gap = max(first_width, second_width) * 2.5

    if first[2] <= second[0]:
        return second[0] - first[2] <= max_reasonable_gap
    if second[2] <= first[0]:
        return first[0] - second[2] <= max_reasonable_gap
    return False


def _vertical_overlap_ratio(first: BBox, second: BBox) -> float:
    height = max(min(first[3] - first[1], second[3] - second[1]), 1.0)
    overlap = max(0.0, min(first[3], second[3]) - max(first[1], second[1]))
    return overlap / height


def _merge_compact_die_rows(
    first: Sequence[Sequence[str]],
    second: Sequence[Sequence[str]],
    die_sides: int,
) -> list[list[str]]:
    header = [cell.strip() for cell in first[0]]
    body = [[cell.strip() for cell in row[:2]] for row in [*first[1:], *second[1:]]]

    def row_key(row: Sequence[str]) -> int:
        values = _die_body_values(row[0], die_sides)
        return min(values) if values else die_sides + 1

    return [header, *sorted(body, key=row_key)]


def _find_loose_compact_die_table_fragment(
    rows: Sequence[Sequence[str]],
    bbox: BBox,
    words: Sequence[WordItem],
) -> tuple[list[list[str]], BBox] | None:
    info = _compact_die_table_info(rows)
    if info is None:
        return None

    candidates = [
        fragment
        for direction in (1, -1)
        if (
            fragment := _loose_compact_die_fragment_for_direction(
                rows, bbox, words, info, direction
            )
        )
        is not None
    ]
    if not candidates:
        return None

    return max(candidates, key=lambda item: len(item[0]))


def _compact_die_row_anchors(
    rows: Sequence[Sequence[str]],
    bbox: BBox,
    words: Sequence[WordItem],
    die_sides: int,
) -> list[tuple[float, float, float]]:
    expected = [
        _die_body_values(row[0], die_sides)
        for row in rows[1:]
        if row and _die_body_values(row[0], die_sides) is not None
    ]
    expected_values = {value for values in expected if values is not None for value in values}

    anchors: list[tuple[float, float, float]] = []
    for word in _words_in_bbox(words, bbox, padding=2.0):
        values = _die_body_values(word[4], die_sides)
        if values is None or not values.issubset(expected_values):
            continue
        if word[0] > bbox[0] + 24.0:
            continue
        center_y = (word[1] + word[3]) / 2
        anchors.append((center_y, word[1], word[3]))

    anchors.sort(key=lambda item: item[0])
    return anchors


def _loose_compact_die_fragment_for_direction(
    rows: Sequence[Sequence[str]],
    bbox: BBox,
    words: Sequence[WordItem],
    info: _CompactDieTableInfo,
    direction: int,
) -> tuple[list[list[str]], BBox] | None:
    table_width = max(bbox[2] - bbox[0], 1.0)
    search_distance = max(140.0, table_width * 2.5)

    if direction > 0:
        min_x = bbox[2] + 6.0
        max_x = bbox[2] + search_distance
    else:
        min_x = bbox[0] - search_distance
        max_x = bbox[0] - 6.0

    expected_values = frozenset(range(1, info.sides + 1))
    missing_values = expected_values - info.values
    if not missing_values:
        return None

    candidate_numbers: list[WordItem] = []
    for word in words:
        if not (min_x <= word[0] <= max_x):
            continue

        values = _die_body_values(word[4], info.sides)
        if values is None:
            continue

        if not values.issubset(missing_values):
            continue

        candidate_numbers.append(word)

    for cluster in _cluster_words_by_x(candidate_numbers, tolerance=12.0):
        fragment = _build_loose_compact_die_fragment_from_number_cluster(
            rows,
            bbox,
            words,
            info,
            cluster,
        )
        if fragment is not None:
            return fragment

    return None


def _die_values_from_number_words(
    words: Sequence[WordItem],
    die_sides: int,
) -> frozenset[int]:
    values: set[int] = set()
    for word in words:
        word_values = _die_body_values(word[4], die_sides)
        if word_values is None or values.intersection(word_values):
            return frozenset()
        values.update(word_values)
    return frozenset(values)


def _cluster_words_by_x(words: Sequence[WordItem], tolerance: float) -> list[list[WordItem]]:
    clusters: list[list[WordItem]] = []
    for word in sorted(words, key=lambda item: item[0]):
        for cluster in clusters:
            center = sum(item[0] for item in cluster) / len(cluster)
            if abs(word[0] - center) <= tolerance:
                cluster.append(word)
                break
        else:
            clusters.append([word])
    return clusters


def _build_loose_compact_die_fragment_from_number_cluster(
    rows: Sequence[Sequence[str]],
    bbox: BBox,
    words: Sequence[WordItem],
    info: _CompactDieTableInfo,
    number_words: Sequence[WordItem],
) -> tuple[list[list[str]], BBox] | None:
    if len(number_words) < 2:
        return None

    ordered_numbers = sorted(number_words, key=lambda word: (word[1], word[0]))
    values: set[int] = set()
    body_rows: list[list[str]] = []
    used_words: list[WordItem] = []
    fragment_width = max(110.0, min(240.0, (bbox[2] - bbox[0]) * 1.8))

    if not _loose_fragment_header_matches_or_absent(
        rows,
        bbox,
        words,
        info,
        ordered_numbers[0][0],
        fragment_width,
    ):
        return None

    for number_word in ordered_numbers:
        row_values = _die_body_values(number_word[4], info.sides)
        if row_values is None or values.intersection(row_values):
            return None
        values.update(row_values)

        center_y = (number_word[1] + number_word[3]) / 2
        row_words = [
            word
            for word in words
            if abs(((word[1] + word[3]) / 2) - center_y) <= 4.0
            and number_word[0] - 2.0 <= word[0] <= number_word[0] + fragment_width
        ]
        row_words.sort(key=lambda word: word[0])
        if not row_words or row_words[0] != number_word:
            return None

        body_cell_words = row_words[1:]
        if not body_cell_words:
            return None

        body_rows.append([number_word[4], _join_table_words(body_cell_words)])
        used_words.extend(row_words)

    if not _die_value_sets_complete_die(info.values, frozenset(values), info.sides):
        return None

    header = [cell.strip() for cell in rows[0][:2]]
    fragment_rows = [header, *body_rows]
    if not _is_meaningful_table(fragment_rows):
        return None

    word_bboxes = [(word[0], word[1], word[2], word[3]) for word in used_words]
    fragment_bbox = _union_bboxes(
        [
            *word_bboxes,
            (
                min(word[0] for word in used_words),
                bbox[1],
                max(word[2] for word in used_words),
                bbox[3],
            ),
        ]
    )
    return fragment_rows, fragment_bbox


def _loose_fragment_header_matches_or_absent(
    rows: Sequence[Sequence[str]],
    bbox: BBox,
    words: Sequence[WordItem],
    info: _CompactDieTableInfo,
    fragment_x0: float,
    fragment_width: float,
) -> bool:
    first_row_top = min(
        (word[1] for word in words if word[0] >= fragment_x0 - 2.0), default=bbox[3]
    )
    header_words = [
        word
        for word in words
        if bbox[1] - 4.0 <= word[1] <= first_row_top
        and fragment_x0 - 2.0 <= word[0] <= fragment_x0 + fragment_width
        and _is_die_header(word[4])
    ]
    if not header_words:
        return True

    expected_header = (rows[0][0].strip().upper(), _normalize_table_header_cell(rows[0][1]))
    for die_word in header_words:
        center_y = (die_word[1] + die_word[3]) / 2
        line_words = [
            word
            for word in words
            if abs(((word[1] + word[3]) / 2) - center_y) <= 4.0
            and fragment_x0 - 2.0 <= word[0] <= fragment_x0 + fragment_width
        ]
        line_words.sort(key=lambda word: word[0])
        if len(line_words) < 2:
            continue
        candidate_header = (
            line_words[0][4].strip().upper(),
            _normalize_table_header_cell(_join_table_words(line_words[1:])),
        )
        if candidate_header == expected_header and candidate_header == info.header:
            return True

    return False


def _expand_bbox(bbox: BBox, x_padding: float, y_padding: float) -> BBox:
    return (
        bbox[0] - x_padding,
        bbox[1] - y_padding,
        bbox[2] + x_padding,
        bbox[3] + y_padding,
    )


def _table_line_segments(words: Sequence[WordItem]) -> list[list[list[WordItem]]]:
    lines = _cluster_words_by_line(words)
    if len(lines) < 3:
        return []

    gaps = [lines[index][0][1] - lines[index - 1][0][1] for index in range(1, len(lines))]
    normal_gap = sorted(gaps)[len(gaps) // 2] if gaps else 0.0
    split_gap = max(22.0, normal_gap * 2.4)

    segments: list[list[list[WordItem]]] = []
    current: list[list[WordItem]] = [lines[0]]
    for index, line in enumerate(lines[1:], start=1):
        starts_new_header = (
            len(current) >= 3
            and line[0][0] <= current[0][0][0] + 12.0
            and _line_looks_like_table_header(line)
        )
        if line[0][1] - lines[index - 1][0][1] > split_gap or starts_new_header:
            if len(current) >= 3:
                segments.append(current)
            current = [line]
        else:
            current.append(line)
    if len(current) >= 3:
        segments.append(current)
    return segments


def _line_looks_like_table_header(line: Sequence[WordItem]) -> bool:
    return _looks_like_table_header([word[4] for word in line])


def _cluster_words_by_line(words: Sequence[WordItem]) -> list[list[WordItem]]:
    ordered = sorted(words, key=lambda word: ((word[1] + word[3]) / 2, word[0]))
    lines: list[list[WordItem]] = []
    for word in ordered:
        center_y = (word[1] + word[3]) / 2
        for line in lines:
            line_center = sum((item[1] + item[3]) / 2 for item in line) / len(line)
            if abs(center_y - line_center) <= 4.0:
                line.append(word)
                line.sort(key=lambda item: item[0])
                break
        else:
            lines.append([word])
    return lines


def _rebuild_table_from_word_lines(
    lines: Sequence[Sequence[WordItem]],
) -> tuple[list[list[str]], BBox] | None:
    starts = _recurring_column_starts(lines)
    if len(starts) < 2:
        return None

    rows: list[list[str]] = []
    used_words: list[WordItem] = []
    for line in lines:
        cell_words: list[list[WordItem]] = [[] for _ in starts]
        for word in line:
            col = _table_column_for_x(word[0], starts)
            cell_words[col].append(word)
        row = [_join_table_words(words) for words in cell_words]
        non_empty = sum(1 for cell in row if cell.strip())
        if non_empty == 0:
            continue
        if _starts_new_logical_table_row(row, rows):
            rows.append(row)
        elif rows and any(cell.strip() for cell in row[1:]):
            _append_table_row_cells(rows[-1], row)
        elif rows:
            break
        else:
            continue
        used_words.extend(word for words in cell_words for word in words)

    if not _looks_like_geometric_table(rows):
        return None

    bbox = _union_bboxes([(word[0], word[1], word[2], word[3]) for word in used_words])
    return rows, bbox


def _starts_new_logical_table_row(row: list[str], existing_rows: Sequence[list[str]]) -> bool:
    first_cell = row[0].strip() if row else ""
    non_empty = sum(1 for cell in row if cell.strip())
    if first_cell:
        return True
    return not existing_rows and non_empty >= 2 and _looks_like_table_header(row)


def _append_table_row_cells(target: list[str], continuation: Sequence[str]) -> None:
    for index, text in enumerate(continuation):
        text = text.strip()
        if not text:
            continue
        if index >= len(target):
            target.append(text)
        elif target[index].strip():
            target[index] = f"{target[index].strip()} {text}"
        else:
            target[index] = text


def _recurring_column_starts(lines: Sequence[Sequence[WordItem]]) -> list[float]:
    stable_starts = _stable_word_column_starts(lines)

    for line in lines:
        header_row = [_join_table_words([word]) for word in line]
        if _looks_like_table_header(header_row) and len(line) >= 2:
            return _dedupe_column_starts(
                [word[0] for word in sorted(line, key=lambda item: item[0])],
                stable_starts=stable_starts,
            )

    return _dedupe_column_starts(stable_starts)


def _stable_word_column_starts(lines: Sequence[Sequence[WordItem]]) -> list[float]:
    clusters: list[list[tuple[float, int]]] = []
    for line_index, line in enumerate(lines):
        for word in line:
            for cluster in clusters:
                cluster_center = sum(start for start, _ in cluster) / len(cluster)
                if abs(word[0] - cluster_center) <= 8.0:
                    cluster.append((word[0], line_index))
                    break

            else:
                clusters.append([(word[0], line_index)])

    starts: list[float] = []
    for cluster in clusters:
        line_count = len({line_index for _, line_index in cluster})
        if line_count >= 2:
            starts.append(sum(start for start, _ in cluster) / len(cluster))
    return sorted(starts)


def _dedupe_column_starts(
    starts: Sequence[float], stable_starts: Sequence[float] | None = None
) -> list[float]:
    deduped: list[float] = []
    stable = sorted(stable_starts or [])
    for start in sorted(starts):
        if (
            not deduped
            or start - deduped[-1] >= 18.0
            or _is_supported_close_column_start(deduped[-1], start, stable)
        ):
            deduped.append(start)
    return deduped[:4]


def _is_supported_close_column_start(
    previous: float,
    current: float,
    stable_starts: Sequence[float],
) -> bool:
    if current - previous < 10.0:
        return False

    previous_support = _nearest_stable_column_start(previous, stable_starts)
    current_support = _nearest_stable_column_start(current, stable_starts)
    if previous_support is None or current_support is None:
        return False
    return current_support - previous_support >= 10.0


def _nearest_stable_column_start(
    start: float,
    stable_starts: Sequence[float],
) -> float | None:
    nearby = [stable for stable in stable_starts if abs(stable - start) <= 8.0]
    if not nearby:
        return None
    return min(nearby, key=lambda stable: abs(stable - start))


def _looks_like_geometric_table(rows: list[list[str]]) -> bool:
    if len(rows) < 3 or not rows:
        return False
    column_count = max(len(row) for row in rows)
    if column_count < 2 or not _looks_like_table_header(rows[0]):
        return False

    body_rows = rows[1:]
    if len(body_rows) < 2:
        return False

    significant_columns = 0
    for column_index in range(column_count):
        column_non_empty = sum(
            1 for row in rows if column_index < len(row) and row[column_index].strip()
        )
        if column_non_empty >= 2:
            significant_columns += 1
    if significant_columns < 2:
        return False

    first_column_data_rows = sum(1 for row in body_rows if row and row[0].strip())
    if first_column_data_rows < max(2, len(body_rows) - 1):
        return False

    avg_non_empty = _table_non_empty_cell_count(rows) / len(rows)
    return avg_non_empty >= 1.6


def _looks_like_table_header(row: Sequence[str]) -> bool:
    non_empty = [cell.strip() for cell in row if cell.strip()]
    if len(non_empty) < 2:
        return False
    return any(_is_die_header(cell) or _has_uppercase_header_shape(cell) for cell in non_empty)


def _is_die_header(text: str) -> bool:
    return _DIE_HEADER_RE.match(text.strip()) is not None


def _has_uppercase_header_shape(text: str) -> bool:
    letters = [char for char in text if char.isalpha()]
    return bool(letters) and len(text) <= 32 and all(char.isupper() for char in letters)


def _rebuild_temporal_units_table_from_words(
    words: Sequence[WordItem],
) -> tuple[list[list[str]], BBox] | None:
    header = _temporal_units_header(words)
    if header is None:
        return None

    header_row, starts, header_bottom, header_words = header
    row_starts = _temporal_units_row_starts(words, header_bottom)
    if len(row_starts) != 3:
        return None

    bands = _labeled_table_row_bands(row_starts)
    rows_by_label = {label: ["" for _ in starts] for label, _, _ in row_starts}
    cell_words: dict[tuple[str, int], list[WordItem]] = defaultdict(list)

    first_top = min(top for _, top, _ in row_starts) - 12.0
    last_bottom = max(bottom for _, _, bottom in row_starts) + 40.0
    for word in words:
        center_y = (word[1] + word[3]) / 2
        if center_y <= header_bottom or center_y < first_top or center_y > last_bottom:
            continue
        label = _labeled_table_row_for_y(center_y, bands)
        if label is None:
            continue
        col = _table_column_for_x(word[0], starts)
        cell_words[(label, col)].append(word)

    for (label, col), grouped_words in cell_words.items():
        rows_by_label[label][col] = _join_table_words(grouped_words)

    ordered_rows = [rows_by_label[label] for label, _, _ in row_starts]
    rows = [header_row, *ordered_rows]
    if any(not cell.strip() for row in ordered_rows for cell in row):
        return None

    table_words = [*header_words, *(word for grouped in cell_words.values() for word in grouped)]
    bbox = _union_bboxes([(word[0], word[1], word[2], word[3]) for word in table_words])
    return rows, bbox


def _temporal_units_header(
    words: Sequence[WordItem],
) -> tuple[list[str], list[float], float, list[WordItem]] | None:
    for unita in words:
        if unita[4] != "UNITÀ":
            continue
        temporali = _find_word(
            words, "TEMPORALI", x=unita[0], min_y=unita[1], max_y=unita[3] + 16.0
        )
        if temporali is None:
            continue
        header_y = (temporali[1] + temporali[3]) / 2
        durata = _find_word_on_line(words, "DURATA", header_y, min_x=temporali[2])
        tempo = _find_word_on_line(words, "TEMPO", header_y, min_x=durata[2] if durata else None)
        necessario = _find_word_on_line(
            words, "NECESSARIO", header_y, min_x=tempo[2] if tempo else None
        )
        per = _find_word_on_line(
            words, "PER", header_y, min_x=necessario[2] if necessario else None
        )
        if durata is None or tempo is None or necessario is None or per is None:
            continue
        header_words = [unita, temporali, durata, tempo, necessario, per]
        return (
            ["UNITÀ TEMPORALI", "DURATA", "TEMPO NECESSARIO PER"],
            [unita[0], durata[0], tempo[0]],
            max(word[3] for word in header_words),
            header_words,
        )
    return None


def _find_word(
    words: Sequence[WordItem],
    text: str,
    x: float,
    min_y: float,
    max_y: float,
) -> WordItem | None:
    for word in words:
        if word[4] == text and abs(word[0] - x) <= 3.0 and min_y <= word[1] <= max_y:
            return word
    return None


def _find_word_on_line(
    words: Sequence[WordItem],
    text: str,
    center_y: float,
    min_x: float | None = None,
) -> WordItem | None:
    for word in words:
        word_center_y = (word[1] + word[3]) / 2
        if word[4] != text or abs(word_center_y - center_y) > 3.0:
            continue
        if min_x is not None and word[0] <= min_x:
            continue
        return word
    return None


def _temporal_units_row_starts(
    words: Sequence[WordItem], header_bottom: float
) -> list[tuple[str, float, float]]:
    labels = {"Round", "Intervallo", "Periodo"}
    starts = [
        (word[4], word[1], word[3])
        for word in words
        if word[4] in labels and word[1] > header_bottom
    ]
    starts.sort(key=lambda item: item[1])
    return starts


def _labeled_table_row_bands(
    row_starts: list[tuple[str, float, float]],
) -> dict[str, tuple[float, float]]:
    bands = {}
    for index, (label, y0, y1) in enumerate(row_starts):
        top = row_starts[index - 1][1] + 2.0 if index > 0 else y0 - 12.0
        bottom = row_starts[index + 1][1] - 2.0 if index + 1 < len(row_starts) else y1 + 40.0
        bands[label] = (top, bottom)
    return bands


def _labeled_table_row_for_y(center_y: float, bands: dict[str, tuple[float, float]]) -> str | None:
    for label, (top, bottom) in bands.items():
        if top <= center_y <= bottom:
            return label
    return None


def _table_column_for_x(x0: float, starts: list[float]) -> int:
    # Header starts mark left cell edges; table words can extend close to the next edge.
    thresholds = [starts[index + 1] - 2.0 for index in range(len(starts) - 1)]
    for index, threshold in enumerate(thresholds):
        if x0 < threshold:
            return index
    return len(starts) - 1


def _join_table_words(words: Sequence[WordItem]) -> str:
    ordered = sorted(words, key=lambda item: (item[1], item[0]))
    return " ".join(word[4] for word in ordered).strip()


def _table_non_empty_cell_count(rows: list[list[str]]) -> int:
    return sum(1 for row in rows for cell in row if cell.strip())


def _vector_table_candidate_regions_from_drawings(drawings: Sequence[object]) -> list[BBox]:
    regions: list[BBox] = []
    for drawing in drawings:
        if not isinstance(drawing, dict) or "rect" not in drawing:
            continue
        try:
            rect = fitz.Rect(drawing["rect"])
        except Exception:
            continue
        if rect.is_empty or rect.is_infinite or rect.width < 20.0 or rect.height < 20.0:
            continue
        regions.append((rect.x0, rect.y0, rect.x1, rect.y1))
    return sorted(regions, key=lambda bbox: (bbox[1], bbox[0]))


def _is_meaningful_table(rows: list[list[str]]) -> bool:
    if not rows:
        return False

    non_empty_rows = sum(1 for row in rows if any(cell.strip() for cell in row))
    if non_empty_rows < 2:
        return False

    non_empty_cells = _table_non_empty_cell_count(rows)
    if non_empty_cells < 4:
        return False

    total_cells = sum(len(row) for row in rows)
    if total_cells == 0 or non_empty_cells / total_cells < 0.12:
        return False

    column_count = max((len(row) for row in rows), default=0)
    significant_columns = 0
    for column_index in range(column_count):
        column_non_empty = sum(
            1 for row in rows if column_index < len(row) and row[column_index].strip()
        )
        if column_non_empty >= 2:
            significant_columns += 1

    return significant_columns >= 2


def _table_fragments_non_empty_in_region(tables: Sequence[TableBlock], region: BBox) -> int:
    return sum(
        _table_non_empty_cell_count(table.rows)
        for table in tables
        if _bbox_contains(region, table.bbox) or _bbox_overlap_ratio(table.bbox, region) >= 0.8
    )


def _bbox_contains(
    outer: tuple[float, float, float, float],
    inner: tuple[float, float, float, float],
    tolerance: float = 2.5,
) -> bool:
    return (
        outer[0] <= inner[0] + tolerance
        and outer[1] <= inner[1] + tolerance
        and outer[2] >= inner[2] - tolerance
        and outer[3] >= inner[3] - tolerance
    )


def _bbox_overlap_ratio(
    source: tuple[float, float, float, float],
    target: tuple[float, float, float, float],
) -> float:
    area = max(_bbox_area(source), 1.0)
    return _bbox_intersection_area(source, target) / area


def _bbox_overlaps_any(bbox: tuple, excluded: list[tuple], threshold: float = 0.3) -> bool:
    x0, y0, x1, y1 = bbox
    area = max((x1 - x0) * (y1 - y0), 1)
    for ex in excluded:
        ex0, ey0, ex1, ey1 = ex
        ix = max(0.0, min(x1, ex1) - max(x0, ex0))
        iy = max(0.0, min(y1, ey1) - max(y0, ey0))
        if (ix * iy) / area > threshold:
            return True
    return False


def _bbox_area(bbox: tuple[float, float, float, float]) -> float:
    width = max(0.0, bbox[2] - bbox[0])
    height = max(0.0, bbox[3] - bbox[1])
    return width * height


def _bbox_intersection_area(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> float:
    x0 = max(first[0], second[0])
    y0 = max(first[1], second[1])
    x1 = min(first[2], second[2])
    y1 = min(first[3], second[3])
    return _bbox_area((x0, y0, x1, y1))


def _overlap_ratio_against_bbox(
    dict_bbox: tuple[float, float, float, float],
    candidate_bbox: tuple[float, float, float, float],
) -> float:
    area = _bbox_area(dict_bbox)
    if area == 0.0:
        return 0.0
    return _bbox_intersection_area(dict_bbox, candidate_bbox) / area


def _best_text_block_for_bbox(
    dict_bbox: tuple[float, float, float, float],
    blocks: list[tuple[float, float, float, float, str, int, int]],
    min_overlap: float = 0.5,
) -> tuple[float, float, float, float, str, int, int] | None:
    best_block = None
    best_overlap = 0.0

    for block in blocks:
        if block[6] != 0 or not _text_from_block(block):
            continue
        overlap = _overlap_ratio_against_bbox(dict_bbox, block[:4])
        if overlap > best_overlap:
            best_block = block
            best_overlap = overlap

    if best_overlap < min_overlap:
        return None
    return best_block


@dataclass
class _DictBlockMatch:
    dict_bbox: tuple[float, float, float, float]
    dict_text: str
    matched_block: tuple[float, float, float, float, str, int, int] | None
    source_spans: list[TextSpan] | None = None


def _group_consecutive_dict_block_matches(
    matches: list[_DictBlockMatch],
) -> list[list[_DictBlockMatch]]:
    groups: list[list[_DictBlockMatch]] = []

    for match in matches:
        if (
            groups
            and match.matched_block is not None
            and groups[-1][-1].matched_block == match.matched_block
        ):
            groups[-1].append(match)
        else:
            groups.append([match])

    return groups


def _text_block_from_dict_match_group(group: list[_DictBlockMatch]) -> TextBlock | None:
    if not group:
        return None

    matched_block = group[0].matched_block
    if matched_block is None:
        return None
    if any(match.matched_block != matched_block for match in group):
        return None

    block_hint_text = _text_from_block(matched_block)
    if not block_hint_text:
        return None

    fallback_text = _fallback_text_from_dict_match_group(group)
    text = _best_text_for_dict_match_group(block_hint_text, fallback_text)

    bbox = _union_bboxes([match.dict_bbox for match in group])
    source_span = _first_source_span(group)
    span = TextSpan(
        text=text,
        font=source_span.font if source_span is not None else "",
        size=source_span.size if source_span is not None else 10.0,
        bold=source_span.bold if source_span is not None else False,
        italic=source_span.italic if source_span is not None else False,
        bbox=bbox,
    )
    return TextBlock(spans=[span], bbox=bbox)


def _rebuild_text_blocks_from_block_hints(
    text_blocks: list[TextBlock],
    block_hints: list[tuple[float, float, float, float, str, int, int]],
) -> list[TextBlock]:
    matches = [
        _DictBlockMatch(
            dict_bbox=text_block.bbox,
            dict_text=text_block.text,
            matched_block=_best_text_block_for_bbox(text_block.bbox, block_hints),
            source_spans=text_block.spans,
        )
        for text_block in text_blocks
    ]
    groups = _group_consecutive_dict_block_matches(matches)
    rebuilt: list[TextBlock] = []
    index = 0

    for group in groups:
        if len(group) > 1:
            text_block = _text_block_from_dict_match_group(group)
            if text_block is not None:
                rebuilt.append(text_block)
            else:
                rebuilt.extend(text_blocks[index : index + len(group)])
        else:
            text_block = _text_block_from_single_dict_match_if_better(group[0])
            rebuilt.append(text_block if text_block is not None else text_blocks[index])
        index += len(group)

    return rebuilt


def _text_block_from_single_dict_match_if_better(match: _DictBlockMatch) -> TextBlock | None:
    if match.matched_block is None:
        return None

    dict_text = " ".join(match.dict_text.strip().split())
    block_hint_text = _text_from_block(match.matched_block)
    if not block_hint_text:
        return None
    if not _same_text_ignoring_spaces(dict_text, block_hint_text):
        return None
    if _fragment_artifact_score(block_hint_text) >= _fragment_artifact_score(dict_text):
        return None

    source_span = match.source_spans[0] if match.source_spans else None
    span = TextSpan(
        text=block_hint_text,
        font=source_span.font if source_span is not None else "",
        size=source_span.size if source_span is not None else 10.0,
        bold=source_span.bold if source_span is not None else False,
        italic=source_span.italic if source_span is not None else False,
        bbox=match.dict_bbox,
    )
    return TextBlock(spans=[span], bbox=match.dict_bbox)


def _fallback_text_from_dict_match_group(group: list[_DictBlockMatch]) -> str:
    clean_matches = [match for match in group if match.dict_text.strip()]
    if not clean_matches:
        return ""

    text = " ".join(clean_matches[0].dict_text.strip().split())
    previous = clean_matches[0]
    for match in clean_matches[1:]:
        text = _join_dict_fragment_matches(text, previous, match)
        previous = match
    return text


def _join_dict_fragment_matches(
    current_text: str,
    left_match: _DictBlockMatch,
    right_match: _DictBlockMatch,
) -> str:
    right_text = " ".join(right_match.dict_text.strip().split())
    if not current_text:
        return right_text
    if not right_text:
        return current_text
    if right_text[0] in ",.;:!?)]»":
        return f"{current_text}{right_text}"
    if _should_join_dict_matches_without_space(left_match, right_match):
        return f"{current_text}{right_text}"
    return f"{current_text} {right_text}"


def _should_join_dict_matches_without_space(
    left_match: _DictBlockMatch,
    right_match: _DictBlockMatch,
) -> bool:
    left_text = " ".join(left_match.dict_text.strip().split())
    right_text = " ".join(right_match.dict_text.strip().split())
    if not left_text or not right_text:
        return True
    if not left_text[-1].isalnum() or not right_text[0].isalnum():
        return False
    if not _bboxes_are_on_same_line(left_match.dict_bbox, right_match.dict_bbox):
        return False

    horizontal_gap = right_match.dict_bbox[0] - left_match.dict_bbox[2]
    if horizontal_gap > 1.5:
        return False

    left_last_word = left_text.rsplit(maxsplit=1)[-1]
    right_first_word = right_text.split(maxsplit=1)[0]
    if len(left_last_word) == 1 or len(right_first_word) == 1:
        return True
    return len(right_first_word) <= 4 and len(left_last_word) >= 3 and horizontal_gap <= 1.0


def _best_text_for_dict_match_group(block_hint_text: str, fallback_text: str) -> str:
    if not fallback_text:
        return block_hint_text

    if _same_text_ignoring_spaces(block_hint_text, fallback_text):
        block_hint_score = _fragment_artifact_score(block_hint_text)
        fallback_score = _fragment_artifact_score(fallback_text)
        if fallback_score < block_hint_score:
            return fallback_text
        return block_hint_text

    if _has_fragment_artifact(block_hint_text) and not _has_fragment_artifact(fallback_text):
        return fallback_text
    return block_hint_text


def _same_text_ignoring_spaces(left: str, right: str) -> bool:
    return "".join(left.split()) == "".join(right.split())


def _fragment_artifact_score(text: str) -> int:
    words = text.split()
    return sum(
        1
        for left, right in zip(words, words[1:], strict=False)
        if _looks_like_fragment_boundary(left, right)
    ) + sum(
        _word_artifact_score(word, previous)
        for previous, word in zip(["", *words], words, strict=False)
    )


def _word_artifact_score(word: str, previous: str) -> int:
    clean_word = word.strip(",.;:!?)]»")
    clean_previous = previous.strip(",.;:!?)]»")
    if not clean_word:
        return 0

    score = 0
    if "’" in clean_word:
        apostrophe_suffix = clean_word.rsplit("’", 1)[-1]
        if len(apostrophe_suffix) == 1:
            score += 1
    if (
        clean_word.isupper()
        and clean_previous.isupper()
        and len(clean_previous) > 1
        and len(clean_word) > 12
    ):
        score += 1
    return score


def _has_fragment_artifact(text: str) -> bool:
    words = text.split()
    return any(
        _looks_like_fragment_boundary(left, right)
        for left, right in zip(words, words[1:], strict=False)
    )


def _looks_like_fragment_boundary(left: str, right: str) -> bool:
    clean_left = left.strip(",.;:!?)]»")
    clean_right = right.strip(",.;:!?)]»")
    if not clean_left or not clean_right:
        return False
    if not clean_left[-1].islower() or not clean_right[0].islower():
        return False
    if len(clean_left) == 1:
        return clean_left.isascii() and len(clean_right) >= 5
    if len(clean_right) == 1:
        return clean_right.isascii()
    return len(clean_left) >= 3 and clean_right in {"mata", "rale"}


def _bboxes_are_on_same_line(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> bool:
    first_top, first_bottom = first[1], first[3]
    second_top, second_bottom = second[1], second[3]
    overlap = min(first_bottom, second_bottom) - max(first_top, second_top)
    if overlap <= 0:
        return False

    min_height = min(max(first_bottom - first_top, 1.0), max(second_bottom - second_top, 1.0))
    first_center = (first_top + first_bottom) / 2
    second_center = (second_top + second_bottom) / 2
    return overlap >= min_height * 0.5 or abs(first_center - second_center) <= 2.0


def _union_bboxes(
    bboxes: list[tuple[float, float, float, float]],
) -> tuple[float, float, float, float]:
    return (
        min(bbox[0] for bbox in bboxes),
        min(bbox[1] for bbox in bboxes),
        max(bbox[2] for bbox in bboxes),
        max(bbox[3] for bbox in bboxes),
    )


def _first_source_span(group: list[_DictBlockMatch]) -> TextSpan | None:
    for match in group:
        if match.source_spans:
            return match.source_spans[0]
    return None


def _should_join_span_without_space(first: TextSpan, second: TextSpan) -> bool:
    left = first.text.strip()
    right = second.text.strip()
    if not left or not right:
        return True

    if right[0] in ",.;:!?)]»":
        return True
    if left[-1] in "’'":
        return True

    if not _spans_are_on_same_line(first, second):
        return False

    gap = second.bbox[0] - first.bbox[2]
    has_very_short_fragment = len(left) == 1 or len(right) == 1
    if left[-1].isalnum() and right[0].isalnum() and has_very_short_fragment and gap <= 1.5:
        return True

    return len(left) == 1 and left.isupper() and right.isupper() and gap <= 4.0


def _spans_are_on_same_line(first: TextSpan, second: TextSpan) -> bool:
    first_top, first_bottom = first.bbox[1], first.bbox[3]
    second_top, second_bottom = second.bbox[1], second.bbox[3]

    overlap = min(first_bottom, second_bottom) - max(first_top, second_top)
    if overlap <= 0:
        return False

    first_height = max(first_bottom - first_top, 1.0)
    second_height = max(second_bottom - second_top, 1.0)
    min_height = min(first_height, second_height)
    first_center = (first.bbox[1] + first.bbox[3]) / 2
    second_center = (second.bbox[1] + second.bbox[3]) / 2
    return overlap >= min_height * 0.5 or abs(first_center - second_center) <= 2.0


@dataclass
class ImageBlock:
    """Immagine raster embedded nel PDF."""

    image_data: bytes
    ext: str
    bbox: tuple[float, float, float, float]
    page_num: int
    index: int
    saved_path: str | None = None
    description: str | None = None
    is_background: bool = False
    """True se l'immagine copre >60% della pagina (sfondo/texture).
    Non viene aggiunta a excluded_bboxes: il testo soprastante viene conservato."""
    is_duplicate: bool = False
    """True se questo hash e gia stato salvato in una pagina precedente.
    Il file esiste gia su disco; nell'EPUB l'occorrenza viene saltata."""


@dataclass
class VectorBlock:
    """Gruppo di path vettoriali che formano un'illustrazione."""

    bbox: tuple[float, float, float, float]
    page_num: int
    index: int
    saved_path: str | None = None
    description: str | None = None


@dataclass
class TableBlock:
    rows: list[list[str]]
    bbox: tuple[float, float, float, float]
    page_num: int
    index: int
    saved_path: str | None = None
    description: str | None = None


@dataclass
class PageData:
    page_num: int
    text_blocks: list[TextBlock]
    images: list[ImageBlock]
    vectors: list[VectorBlock]
    tables: list[TableBlock]
    width: float
    height: float


# ---------------------------------------------------------------------------
# Asset Index — registro CSV di tutti gli asset estratti
# ---------------------------------------------------------------------------

_INDEX_FIELDS = ["sha", "nome_file", "tipo", "pagina", "titolo", "descrizione", "modificato"]


class AssetIndex:
    """
    Registro centrale degli asset estratti, salvato come CSV in
    _extracted/asset_index.csv.

    Logica di merge su build esistente:
    - Se il CSV non esiste: creato da zero.
    - Se esiste e nessuna entry ha modificato=si: sovrascritto senza chiedere.
    - Se esiste con almeno una entry modificato=si: le entry marcate sono
      protette; le entry nuove (SHA non presente) vengono aggiunte; le entry
      con modificato=no vengono aggiornate.

    Il SHA è calcolato sul contenuto binario dell'asset (MD5 hex, già usato
    per la dedup inline). È la chiave stabile che sopravvive ai rename.
    """

    def __init__(self, index_path: Path):
        self.path = index_path
        # sha -> dict con i campi del CSV
        self._entries: dict[str, dict] = {}
        self._protected: set = set()  # SHA con modificato=si
        self._loaded = False

    def load(self) -> bool:
        """
        Carica il CSV esistente. Restituisce True se esisteva almeno
        una entry con modificato=si (build protetta).
        """
        if not self.path.exists():
            return False
        try:
            with open(self.path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sha = row.get("sha", "").strip()
                    if not sha:
                        continue
                    self._entries[sha] = dict(row)
                    if row.get("modificato", "no").strip().lower() == "si":
                        self._protected.add(sha)
            self._loaded = True
            return bool(self._protected)
        except Exception as e:
            print(f"  [warn] asset_index.csv: errore lettura ({e}), ricreo da zero")
            return False

    def has_protected(self) -> bool:
        return bool(self._protected)

    def is_protected(self, sha: str) -> bool:
        return sha in self._protected

    def get(self, sha: str) -> dict | None:
        return self._entries.get(sha)

    def add_or_update(
        self,
        sha: str,
        nome_file: str,
        tipo: str,
        pagina: int,
        titolo: str | None,
        descrizione: str | None,
    ) -> None:
        """
        Aggiunge una nuova entry o aggiorna una esistente non protetta.
        Le entry con modificato=si non vengono toccate.
        """
        if sha in self._protected:
            return
        self._entries[sha] = {
            "sha": sha,
            "nome_file": nome_file,
            "tipo": tipo,
            "pagina": str(pagina + 1),  # 1-based per leggibilità
            "titolo": titolo or "",
            "descrizione": descrizione or "",
            "modificato": "no",
        }

    def get_title(self, sha: str) -> str | None:
        """Restituisce il titolo leggibile (eventualmente modificato dall'utente)."""
        entry = self._entries.get(sha)
        if not entry:
            return None
        return entry.get("titolo") or None

    def get_description(self, sha: str) -> str | None:
        """Restituisce la descrizione (eventualmente modificata dall'utente)."""
        entry = self._entries.get(sha)
        if not entry:
            return None
        return entry.get("descrizione") or None

    def get_current_name(self, sha: str) -> str | None:
        """Restituisce il nome file corrente (eventualmente rinominato dall'utente)."""
        entry = self._entries.get(sha)
        if not entry:
            return None
        return entry.get("nome_file") or None

    def save(self) -> None:
        """Scrive il CSV su disco."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_INDEX_FIELDS)
            writer.writeheader()
            for entry in self._entries.values():
                writer.writerow(entry)


# ---------------------------------------------------------------------------
# Rilevamento pagine sommario / indice
# ---------------------------------------------------------------------------

_TOC_LINE_RE = _re.compile(r".{3,}\s+\d{1,3}\s*$")


def is_toc_page(page: PageData) -> bool:
    """
    Rileva se una pagina e un sommario/indice stampato.

    Algoritmo: conta i blocchi di testo che seguono il pattern
    tipico di un indice: testo descrittivo seguito da un numero
    di pagina ("Introduzione ............ 9").
    Se piu del 40% dei blocchi ha questa struttura, la pagina
    viene classificata come indice.
    """
    if len(page.text_blocks) < 3:
        return False
    matches = sum(1 for b in page.text_blocks if _TOC_LINE_RE.search(b.text.strip()))
    return (matches / len(page.text_blocks)) > 0.40


# ---------------------------------------------------------------------------
# Filtro intestazioni / piè di pagina / filigrane
# ---------------------------------------------------------------------------


def _normalize_text(text: str) -> str:
    """Rimuove cifre e normalizza per confronto. 'Pagina 42' == 'Pagina 103'."""
    return _re.sub(r"\d+", "", text).strip().lower()


def filter_repeated_blocks(
    pages: list[PageData],
    header_footer_zone: float = 0.08,
    repetition_threshold: float = 0.25,
) -> list[PageData]:
    """
    Rimuove blocchi di testo che si ripetono alla stessa posizione Y su molte
    pagine (intestazioni, piè di pagina, filigrane, watermark testuali).

    Due passate:
      1. Costruisce firme (zona, testo_normalizzato) e conta occorrenze per pagina
      2. Rimuove i blocchi le cui firme superano la soglia

    Soglie asimmetriche: header/footer → 25% pagine, body → 60%.
    Il body ha soglia più alta perché nomi di abilità o titoli di tabella
    possono legittimamente ripetersi molte volte.
    """
    if not pages:
        return pages

    n = len(pages)
    min_edge = max(2, int(n * repetition_threshold))
    min_body = max(2, int(n * 0.60))

    sig_pages: dict = defaultdict(set)

    for page in pages:
        h = page.height or 1.0
        for block in page.text_blocks:
            y_norm = block.bbox[1] / h
            if y_norm < header_footer_zone:
                zone = "header"
            elif y_norm > (1.0 - header_footer_zone):
                zone = "footer"
            else:
                zone = "body"
            norm = _normalize_text(block.text)
            if norm:
                sig_pages[(zone, norm)].add(page.page_num)

    to_remove: set = set()
    for sig, pset in sig_pages.items():
        limit = min_edge if sig[0] in ("header", "footer") else min_body
        if len(pset) >= limit:
            to_remove.add(sig)

    if not to_remove:
        return pages

    removed = 0
    result = []
    for page in pages:
        h = page.height or 1.0
        clean = []
        for block in page.text_blocks:
            y_norm = block.bbox[1] / h
            zone = (
                "header"
                if y_norm < header_footer_zone
                else "footer"
                if y_norm > (1.0 - header_footer_zone)
                else "body"
            )
            norm = _normalize_text(block.text)
            if (zone, norm) in to_remove:
                removed += 1
            else:
                clean.append(block)
        result.append(
            PageData(
                page_num=page.page_num,
                text_blocks=clean,
                images=page.images,
                vectors=page.vectors,
                tables=page.tables,
                width=page.width,
                height=page.height,
            )
        )

    unique = len(to_remove)
    print(f"  Filtro ripetizioni: {unique} pattern rimossi ({removed} blocchi totali)")
    return result


# ---------------------------------------------------------------------------
# Filtro glifi decorativi e numeri di pagina
# ---------------------------------------------------------------------------

# Font simbolici/icona noti: i loro glifi vengono estratti come lettere
# normali ma rappresentano bullets, ornamenti, frecce ecc.
_SYMBOL_FONT_KEYWORDS = frozenset(
    [
        "symbol",
        "dingbat",
        "wingding",
        "zapf",
        "webding",
        "icon",
        "ornament",
        "glyph",
        "bullet",
        "arrow",
    ]
)

# Singole lettere che non sono mai parole standalone in italiano/inglese
# (tipicamente glifi di font icona mappati su lettere ASCII)
# Escluse le vocali e 'I': possono essere articoli/congiunzioni reali
_LONE_GLYPH_CHARS = frozenset(
    "bcdfghjklmnpqrstuvwxyz"  # consonanti minuscole
    "BCDFGHJKLMNPQRSTUVWXYZ"  # consonanti maiuscole
    "0123456789"  # cifre standalone gia coperte dal check numerico
)

# Regex per caratteri non-standard che compaiono spesso come glifi decorativi:
# caratteri di controllo, PUA Unicode, simboli non comuni


def _title_to_slug(title: str, max_words: int = 3) -> str:
    """
    Converte un titolo breve (generato dall'AI tramite generate_title)
    in uno slug per nome file: minuscolo, solo alfanumerici e trattini.
    Esempio: "Luna Crescente Ornata" → "luna-crescente-ornata"
    """
    clean = []
    for w in title.strip().split():
        w_norm = _re.sub(r"[^\w]", "", w, flags=_re.UNICODE).lower()
        if w_norm:
            clean.append(w_norm)
        if len(clean) >= max_words:
            break
    slug = "-".join(clean)
    slug = _re.sub(r"-+", "-", slug).strip("-")
    return slug


def _desc_to_slug(description: str, max_words: int = 4) -> str:
    """
    Fallback: estrae parole contenutistiche dalla descrizione completa,
    usato solo se generate_title() non è disponibile o ritorna vuoto.
    """
    SKIP = {
        "questa",
        "questo",
        "quest",
        "l",
        "la",
        "lo",
        "le",
        "il",
        "i",
        "un",
        "una",
        "uno",
        "immagine",
        "illustrazione",
        "foto",
        "figura",
        "disegno",
        "mostra",
        "raffigura",
        "rappresenta",
        "ritrae",
        "è",
        "e",
        "di",
        "del",
        "della",
        "dello",
        "dei",
        "degli",
        "delle",
        "con",
        "che",
        "in",
        "da",
        "per",
        "su",
        "al",
        "alla",
        "probabilmente",
        "forse",
    }
    clean = []
    for w in description.strip().split():
        w_norm = _re.sub(r"[^\w]", "", w, flags=_re.UNICODE).lower()
        if w_norm and w_norm not in SKIP:
            clean.append(w_norm)
        if len(clean) >= max_words:
            break
    slug = "-".join(clean)
    slug = _re.sub(r"-+", "-", slug).strip("-")
    return slug or "img"


def _raster_image_bytes_for_debug(
    image_bytes: bytes,
    original_ext: str,
) -> tuple[bytes, str]:
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.load()
        if img.mode in {"RGBA", "LA"} or (img.mode == "P" and "transparency" in img.info):
            rgba = img.convert("RGBA")
            background = Image.new("RGB", rgba.size, (255, 255, 255))
            background.paste(rgba, mask=rgba.getchannel("A"))
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return buffer.getvalue(), "jpeg"
    except Exception:
        return image_bytes, original_ext


def _is_noise_block(spans: list) -> bool:
    """
    Restituisce True se il blocco e quasi certamente rumore decorativo:
      - tutti gli span usano font simbolici (Wingdings, Dingbats, ecc.)
      - oppure il testo e un singolo carattere consonante (glifo icona)
      - oppure e un numero di pagina standalone (solo cifre, 1-3 chars, bold)
    """
    if not spans:
        return True

    full_text = " ".join(s.text for s in spans).strip()

    # Tutti gli span usano font simbolici?
    if all(any(kw in s.font.lower() for kw in _SYMBOL_FONT_KEYWORDS) for s in spans):
        return True

    # Singolo carattere consonante = quasi sicuramente glifo decorativo
    if len(full_text) == 1 and full_text in _LONE_GLYPH_CHARS:
        return True

    # Numero di pagina standalone: solo cifre, 1-3 chars, bold
    if full_text.isdigit() and len(full_text) <= 3 and any(s.bold for s in spans):
        return True

    # Caratteri non-standard (PUA Unicode, simboli rari): quasi sicuramente glifi
    return len(full_text) <= 4 and _NONSTANDARD_CHAR_RE.match(full_text) is not None

    return False


# ---------------------------------------------------------------------------
# Estrattore principale
# ---------------------------------------------------------------------------


class PDFExtractor:
    def __init__(self, pdf_path: Path, config: LayoutConfig):
        self.pdf_path = pdf_path
        self.config = config
        self.doc = fitz.open(str(pdf_path))
        self.page_count = len(self.doc)

        # Cartella estratti: output/NomePDF/extracted/
        extracted = Path(config.output_dir) / "extracted"
        self.images_dir = extracted / "images"
        self.vectors_dir = extracted / "vectors"
        self.tables_dir = extracted / "tables"
        for d in (self.images_dir, self.vectors_dir, self.tables_dir):
            d.mkdir(parents=True, exist_ok=True)

        # Contatori per il riepilogo finale del rilevamento colonne
        self._col_stats: dict = {1: 0, 2: 0}

        # Dedup inline immagini: hash MD5 -> path del file gia salvato
        # Evita di salvare piu volte lo stesso sfondo/texture su pagine diverse
        self._seen_image_hashes: dict = {}

        # Asset index: registro CSV degli asset estratti
        self.asset_index = AssetIndex(extracted / "asset_index.csv")

    def check_existing_index(self) -> str:
        """
        Controlla se esiste già un asset_index.csv con entry protette.
        Restituisce:
          'none'      — nessun CSV esistente
          'clean'     — CSV esiste, nessuna entry modificato=si
          'protected' — CSV esiste con entry modificato=si (richiede conferma)
        """
        if not self.asset_index.path.exists():
            return "none"
        has_protected = self.asset_index.load()
        if has_protected:
            return "protected"
        return "clean"

    def save_index(self) -> None:
        """Salva l'asset_index.csv a fine estrazione."""
        self.asset_index.save()

    def extract_all(self, describer=None) -> list[PageData]:
        pages = []
        with pdfplumber.open(str(self.pdf_path)) as plumb:
            for i in range(self.page_count):
                print(f"  Pagina {i + 1}/{self.page_count}...", end="\r", flush=True)
                pages.append(self._extract_page(i, plumb.pages[i], describer))
        print(f"  Estratte {self.page_count} pagine.             ")
        if self.config.columns is None:
            p1 = self._col_stats[1]
            p2 = self._col_stats[2]
            print(f"  Layout rilevato: {p1} pag. singola colonna, {p2} pag. doppia colonna")
        return pages

    def get_toc(self) -> list[tuple[int, str, int]]:
        """
        Legge l'outline (bookmarks) del PDF.
        Restituisce [(livello, titolo, pagina_0based), ...].
        Lista vuota se il PDF non ha outline.
        """
        raw = self.doc.get_toc(simple=True)
        return [
            (level, title.strip(), page - 1)
            for level, title, page in raw
            if title and title.strip()
        ]

    # -----------------------------------------------------------------------
    # Estrazione per singola pagina
    # -----------------------------------------------------------------------

    def _extract_page(self, page_num: int, plumb_page, describer) -> PageData:
        fitz_page = self.doc[page_num]
        width = fitz_page.rect.width
        height = fitz_page.rect.height

        table_candidate_regions = (
            _find_table_regions(plumb_page) if self.config.extract_tables else []
        )

        images = self._extract_images(fitz_page, page_num, describer)
        vectors = []
        if self.config.extract_vectors:
            vectors = self._extract_vectors(
                fitz_page,
                page_num,
                describer,
                excluded_bboxes=table_candidate_regions,
            )

        tables = []
        if self.config.extract_tables:
            tables = self._extract_tables(plumb_page, fitz_page, page_num, describer)

        table_asset_regions = [table.bbox for table in tables]
        text_blocks = self._extract_text(fitz_page, width, table_asset_regions)

        return PageData(
            page_num=page_num,
            text_blocks=text_blocks,
            images=images,
            vectors=vectors,
            tables=tables,
            width=width,
            height=height,
        )

    # -----------------------------------------------------------------------
    # Immagini raster
    # -----------------------------------------------------------------------

    def _extract_images(self, page, page_num: int, describer) -> list[ImageBlock]:
        results = []

        for idx, img_info in enumerate(page.get_images(full=True)):
            xref = img_info[0]
            try:
                raw = self.doc.extract_image(xref)
                original_bytes = raw["image"]
                original_ext = raw["ext"]
                img_bytes, ext = _raster_image_bytes_for_debug(original_bytes, original_ext)

                # Filtra immagini troppo piccole quando Pillow riesce a leggerle.
                try:
                    pil = Image.open(io.BytesIO(img_bytes))
                    pil.load()
                    w, h = pil.size
                    if w < self.config.min_image_width or h < self.config.min_image_height:
                        continue
                except Exception:
                    pass

                bbox = self._get_image_bbox(page, xref)

                # Rileva se e uno sfondo: copre >60% della pagina
                page_area = page.rect.width * page.rect.height
                x0, y0, x1, y1 = bbox
                bbox_area = max((x1 - x0) * (y1 - y0), 1)
                is_bg = (bbox_area / page_area) > 0.60

                # Dedup inline: se questa immagine e gia stata salvata
                # in una pagina precedente, riusa il file esistente
                img_hash = hashlib.md5(img_bytes).hexdigest()
                if img_hash in self._seen_image_hashes:
                    existing_path = self._seen_image_hashes[img_hash]
                    # Recupera la descrizione già salvata dall'index
                    cached_desc = self.asset_index.get_description(img_hash)
                    results.append(
                        ImageBlock(
                            image_data=b"",
                            ext=ext,
                            bbox=bbox,
                            page_num=page_num,
                            index=idx,
                            saved_path=existing_path,
                            description=cached_desc,
                            is_background=is_bg,
                            is_duplicate=True,
                        )
                    )
                    continue

                # Nome provvisorio: verrà rinominato dopo la descrizione AI
                fname_tmp = f"p{page_num + 1}_img{idx + 1}.{ext}"
                save_path = self.images_dir / fname_tmp
                save_path.write_bytes(img_bytes)

                title = None
                description = None
                if describer and not is_bg:
                    title, description = describer.describe_image(img_bytes, ext)
                    # Rinomina il file usando le prime 4 parole della descrizione
                    if description:
                        slug = _title_to_slug(title) if title else None
                        if not slug:
                            slug = _desc_to_slug(description)
                        fname = f"{slug}.{ext}"
                        new_path = self.images_dir / fname
                        # Evita collisioni aggiungendo suffisso numerico
                        counter = 1
                        while new_path.exists():
                            fname = f"{slug}_{counter}.{ext}"
                            new_path = self.images_dir / fname
                            counter += 1
                        save_path.rename(new_path)
                        save_path = new_path
                    else:
                        fname = fname_tmp  # mantieni nome numerico se no descrizione

                self._seen_image_hashes[img_hash] = str(save_path)

                # Registra nell'index (non sovrascrive entry protette)
                self.asset_index.add_or_update(
                    sha=img_hash,
                    nome_file=save_path.name,
                    tipo="image",
                    pagina=page_num,
                    titolo=title,
                    descrizione=description,
                )

                results.append(
                    ImageBlock(
                        image_data=img_bytes,
                        ext=ext,
                        bbox=bbox,
                        page_num=page_num,
                        index=idx,
                        saved_path=str(save_path),
                        description=description,
                        is_background=is_bg,
                    )
                )
            except Exception as e:
                print(f"\n  [warn] immagine p{page_num + 1} #{idx}: {e}")

        return results

    def _get_image_bbox(self, page, xref: int) -> tuple[float, float, float, float]:
        try:
            rects = list(page.get_image_rects(xref))
            if rects:
                r = rects[0]
                return (r.x0, r.y0, r.x1, r.y1)
        except Exception:
            pass
        return (0.0, 0.0, page.rect.width, page.rect.height)

    # -----------------------------------------------------------------------
    # Illustrazioni vettoriali
    # -----------------------------------------------------------------------

    def _extract_vectors(
        self,
        page,
        page_num: int,
        describer,
        excluded_bboxes: list[tuple] | None = None,
    ) -> list[VectorBlock]:
        """
        Rileva gruppi di path vettoriali che formano illustrazioni, li esporta
        come SVG ritagliando la regione dal PDF.

        Pipeline:
          1. get_drawings() → tutti i path della pagina
          2. Filtra path troppo piccoli o che coprono l'intera pagina
             (bordi, linee di separazione)
          3. Clustering union-find sui bounding box espansi di 5pt:
             path vicini appartengono alla stessa illustrazione
          4. Filtra cluster sotto la dimensione minima
          5. Per ogni cluster: show_pdf_page con clip → get_svg_image
        """
        results = []
        pw, ph = page.rect.width, page.rect.height
        min_sz = self.config.min_vector_size

        drawings = page.get_drawings()
        if not drawings:
            return results

        # Filtra path irrilevanti:
        # - coprono >70% di larghezza o altezza della pagina → bordi/linee
        # - area < 4pt² → punti/tratti invisibili
        def is_relevant(d) -> bool:
            r = fitz.Rect(d["rect"])
            if r.is_empty or r.width * r.height < 4:
                return False
            return not (r.width > pw * 0.70 or r.height > ph * 0.70)

        relevant = [d for d in drawings if is_relevant(d)]
        if not relevant:
            return results

        # Union-Find clustering
        n = len(relevant)
        parent = list(range(n))
        margin = 5.0

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x: int, y: int) -> None:
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        # Espandi i bbox di un margine prima di confrontarli
        expanded = [
            fitz.Rect(
                fitz.Rect(d["rect"]).x0 - margin,
                fitz.Rect(d["rect"]).y0 - margin,
                fitz.Rect(d["rect"]).x1 + margin,
                fitz.Rect(d["rect"]).y1 + margin,
            )
            for d in relevant
        ]

        for i in range(n):
            for j in range(i + 1, n):
                if expanded[i].intersects(expanded[j]):
                    union(i, j)

        # Raggruppa e calcola bbox unione per ogni cluster
        clusters: dict = defaultdict(list)
        for i, d in enumerate(relevant):
            clusters[find(i)].append(fitz.Rect(d["rect"]))

        # Esporta i cluster che superano la dimensione minima
        vec_idx = 0
        for bbox_list in clusters.values():
            merged = fitz.Rect()
            for r in bbox_list:
                merged |= r
            # Scarta bbox degeneri (area zero o non finiti) che causano
            # "clip must be finite and not empty" in get_svg_image
            if merged.is_empty or merged.is_infinite:
                continue
            if merged.width < min_sz or merged.height < min_sz:
                continue

            # Escludi se sovrapposto a immagine raster già estratta
            # (verifica fatta a posteriori nell'_extract_page, qui non abbiamo
            # ancora quella lista — la gestione overlap è nel chiamante)

            fname_tmp = f"p{page_num + 1}_vec{vec_idx + 1}.svg"
            save_path = self.vectors_dir / fname_tmp
            bbox_tuple = (merged.x0, merged.y0, merged.x1, merged.y1)
            if _bbox_overlaps_any(bbox_tuple, excluded_bboxes or [], threshold=0.8):
                continue

            ok = self._export_region_as_svg(page_num, merged, save_path)
            if not ok:
                continue

            # Descrizione AI: renderizza come PNG e invia all'API
            vec_title = None
            description = None
            if describer:
                thumb = self._render_region_as_png(page_num, merged)
                if thumb:
                    vec_title, description = describer.describe_image(thumb, "png")
                    if description:
                        slug = _title_to_slug(vec_title) if vec_title else None
                        if not slug:
                            slug = _desc_to_slug(description)
                        fname = f"{slug}.svg"
                        new_path = self.vectors_dir / fname
                        counter = 1
                        while new_path.exists():
                            fname = f"{slug}_{counter}.svg"
                            new_path = self.vectors_dir / fname
                            counter += 1
                        save_path.rename(new_path)
                        save_path = new_path

            # Calcola SHA sul contenuto SVG salvato
            vec_sha = hashlib.md5(save_path.read_bytes()).hexdigest()
            self.asset_index.add_or_update(
                sha=vec_sha,
                nome_file=save_path.name,
                tipo="vector",
                pagina=page_num,
                titolo=vec_title,
                descrizione=description,
            )

            results.append(
                VectorBlock(
                    bbox=bbox_tuple,
                    page_num=page_num,
                    index=vec_idx,
                    saved_path=str(save_path),
                    description=description,
                )
            )
            vec_idx += 1

        return results

    def _export_region_as_svg(self, page_num: int, clip: fitz.Rect, save_path: Path) -> bool:
        """
        Esporta una regione della pagina come SVG.

        Tecnica: crea un documento temporaneo di una pagina delle dimensioni
        della clip region, ci mappa il contenuto PDF originale con
        show_pdf_page(), poi chiama get_svg_image() sulla pagina risultante.
        Questo preserva la grafica vettoriale (path, curve, font embedded)
        senza rasterizzare.
        """
        if clip.is_empty or clip.width < 5 or clip.height < 5:
            return False
        try:
            tmp = fitz.open()
            tmp_page = tmp.new_page(width=clip.width, height=clip.height)
            tmp_page.show_pdf_page(
                tmp_page.rect,
                self.doc,
                page_num,
                clip=clip,
            )
            svg = tmp_page.get_svg_image()
            tmp.close()
            save_path.write_text(svg, encoding="utf-8")
            return True
        except Exception as e:
            print(f"\n  [warn] SVG export p{page_num + 1}: {e}")
            return False

    def _render_region_as_png(self, page_num: int, clip: fitz.Rect) -> bytes | None:
        """
        Renderizza una regione come PNG (per le descrizioni AI).
        Non serve alta risoluzione: 2x è sufficiente per la comprensione.
        """
        try:
            page = self.doc[page_num]
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat, clip=clip)
            return pix.tobytes("png")
        except Exception:
            return None

    # -----------------------------------------------------------------------
    # Tabelle
    # -----------------------------------------------------------------------

    def _extract_tables(self, plumb_page, fitz_page, page_num: int, describer) -> list[TableBlock]:
        results = []
        default_tables: list[TableBlock] = []
        try:
            found = plumb_page.find_tables()
        except Exception:
            found = []

        for idx, tbl_obj in enumerate(found):
            try:
                raw_rows = tbl_obj.extract()
                if not raw_rows or len(raw_rows) < 2:
                    continue

                rows = [
                    [(cell or "").replace("\n", " ").strip() for cell in row] for row in raw_rows
                ]
                if not _is_meaningful_table(rows):
                    continue
                bbox = _table_bbox(tbl_obj)
                if bbox is None:
                    continue
                default_tables.append(
                    TableBlock(rows=rows, bbox=bbox, page_num=page_num, index=idx)
                )
            except Exception as e:
                print(f"\n  [warn] tabella p{page_num + 1} #{idx}: {e}")

        fallback_tables = self._table_like_fallback_tables(
            plumb_page, fitz_page, page_num, default_tables
        )
        fallback_regions = [table.bbox for table in fallback_tables]

        pending_tables = [
            table
            for table in default_tables
            if not any(
                _bbox_contains(region, table.bbox) or _bbox_overlap_ratio(table.bbox, region) >= 0.8
                for region in fallback_regions
            )
        ]
        pending_tables.extend(fallback_tables)
        pending_tables.sort(key=lambda table: (table.bbox[1], table.bbox[0]))

        for idx, table in enumerate(pending_tables):
            try:
                saved = self._save_table_block(table, page_num, idx, describer)
                results.append(saved)
            except Exception as e:
                print(f"\n  [warn] tabella p{page_num + 1} #{idx}: {e}")

        return results

    def _table_like_fallback_tables(
        self,
        plumb_page,
        fitz_page,
        page_num: int,
        default_tables: list[TableBlock],
    ) -> list[TableBlock]:
        try:
            words = _normalize_words(fitz_page.get_text("words"))
        except Exception:
            return []

        fallback_tables: list[TableBlock] = []
        for region in _table_like_regions(plumb_page):
            rows = _rebuild_numbered_table_from_words(words, region)
            if rows is None:
                continue
            if len(rows[0]) < 3 or len(rows) < 4:
                continue
            if not _is_meaningful_table(rows):
                continue
            fallback_non_empty = _table_non_empty_cell_count(rows)
            fragment_non_empty = _table_fragments_non_empty_in_region(default_tables, region)
            if fallback_non_empty <= fragment_non_empty:
                continue
            word_bboxes: list[BBox] = [
                (word[0], word[1], word[2], word[3])
                for word in _words_in_bbox(words, region, padding=16.0)
            ]
            fallback_bbox = _union_bboxes([region, *word_bboxes]) if word_bboxes else region
            fallback_tables.append(
                TableBlock(
                    rows=rows,
                    bbox=fallback_bbox,
                    page_num=page_num,
                    index=0,
                )
            )

        temporal_table = _rebuild_temporal_units_table_from_words(words)
        if temporal_table is not None:
            rows, bbox = temporal_table
            if _is_meaningful_table(rows) and not any(
                _bbox_overlap_ratio(bbox, table.bbox) >= 0.8 for table in fallback_tables
            ):
                fallback_tables.append(TableBlock(rows=rows, bbox=bbox, page_num=page_num, index=0))

        try:
            vector_regions = _vector_table_candidate_regions_from_drawings(fitz_page.get_drawings())
        except Exception:
            vector_regions = []
        for rows, bbox in _rebuild_tables_from_vector_regions(words, vector_regions):
            if not any(_bbox_overlap_ratio(bbox, table.bbox) >= 0.8 for table in fallback_tables):
                fallback_tables.append(TableBlock(rows=rows, bbox=bbox, page_num=page_num, index=0))
        return fallback_tables

    def _save_table_block(
        self, table: TableBlock, page_num: int, index: int, describer
    ) -> TableBlock:
        fname = f"p{page_num + 1}_tbl{index + 1}.csv"
        save_path = self.tables_dir / fname
        with open(save_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(table.rows)

        description = None
        if describer:
            description = describer.describe_table(table.rows)

        # SHA sul contenuto CSV
        csv_bytes = save_path.read_bytes()
        tbl_sha = hashlib.md5(csv_bytes).hexdigest()
        self.asset_index.add_or_update(
            sha=tbl_sha,
            nome_file=save_path.name,
            tipo="table",
            pagina=page_num,
            titolo=None,
            descrizione=description,
        )

        return TableBlock(
            rows=table.rows,
            bbox=table.bbox,
            page_num=page_num,
            index=index,
            saved_path=str(save_path),
            description=description,
        )

    # -----------------------------------------------------------------------
    # Testo
    # -----------------------------------------------------------------------

    def _extract_text(
        self,
        page,
        width: float,
        excluded_bboxes: list[tuple],
    ) -> list[TextBlock]:
        raw = page.get_text("dict")
        text_blocks: list[TextBlock] = []

        for block in raw.get("blocks", []):
            if block.get("type") != 0:
                continue
            bbox = tuple(block["bbox"])
            if self._overlaps_any(bbox, excluded_bboxes):
                continue

            spans: list[TextSpan] = []
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    txt = span.get("text", "").strip()
                    if not txt:
                        continue
                    flags = span.get("flags", 0)
                    spans.append(
                        TextSpan(
                            text=txt,
                            font=span.get("font", ""),
                            size=span.get("size", 10.0),
                            bold=bool(flags & 16),
                            italic=bool(flags & 2),
                            bbox=tuple(span["bbox"]),
                        )
                    )

            if spans and not _is_noise_block(spans):
                text_blocks.append(TextBlock(spans=spans, bbox=bbox))

        block_hints = page.get_text("blocks")
        text_blocks = _rebuild_text_blocks_from_block_hints(text_blocks, block_hints)

        # Determina layout colonne per questa pagina
        forced = self.config.columns
        if forced == 1:
            n_cols, split_ratio = 1, 0.5
        elif forced == 2:
            split_ratio = self.config.column_split or self._find_split_ratio(text_blocks, width)
            n_cols = 2
        else:
            # None = auto: rileva per questa pagina
            n_cols, split_ratio = self._detect_page_columns(text_blocks, width)

        if n_cols == 2:
            text_blocks = self._sort_double_column(text_blocks, width * split_ratio, width)
            self._col_stats[2] += 1
        else:
            text_blocks.sort(key=lambda b: b.bbox[1])
            self._col_stats[1] += 1

        return text_blocks

    def _detect_page_columns(self, blocks: list[TextBlock], width: float) -> tuple[int, float]:
        """
        Rileva se una pagina e a singola o doppia colonna.

        Esclude blocchi larghi (>60% pagina) come titoli full-width che non
        rappresentano il layout del corpo. Cerca il gap orizzontale piu ampio
        nella fascia centrale 25%-75%. Se supera column_gap_threshold e ci
        sono blocchi da entrambi i lati, la pagina e a doppia colonna.
        """
        if len(blocks) < 4:
            return 1, 0.5

        fw_limit = width * 0.60
        content_blocks = [b for b in blocks if (b.bbox[2] - b.bbox[0]) < fw_limit]

        if len(content_blocks) < 4:
            return 1, 0.5

        split_ratio = self._find_split_ratio(content_blocks, width)
        split_x = width * split_ratio

        left_count = sum(1 for b in content_blocks if b.bbox[0] < split_x)
        right_count = sum(1 for b in content_blocks if b.bbox[0] >= split_x)
        if left_count < 2 or right_count < 2:
            return 1, 0.5

        centers = sorted(
            (b.bbox[0] + b.bbox[2]) / 2
            for b in content_blocks
            if 0.25 * width < (b.bbox[0] + b.bbox[2]) / 2 < 0.75 * width
        )
        if len(centers) < 2:
            return 1, 0.5

        max_gap = max(centers[i + 1] - centers[i] for i in range(len(centers) - 1))

        if max_gap >= self.config.column_gap_threshold * width:
            return 2, split_ratio
        return 1, 0.5

    def _find_split_ratio(self, blocks: list[TextBlock], width: float) -> float:
        """Posizione X del gap piu ampio nella zona centrale della pagina."""
        centers = sorted(
            (b.bbox[0] + b.bbox[2]) / 2
            for b in blocks
            if 0.25 * width < (b.bbox[0] + b.bbox[2]) / 2 < 0.75 * width
        )
        if len(centers) < 2:
            return 0.5
        max_gap, split_x = 0.0, width / 2
        for i in range(len(centers) - 1):
            gap = centers[i + 1] - centers[i]
            if gap > max_gap:
                max_gap = gap
                split_x = (centers[i] + centers[i + 1]) / 2
        return split_x / width

    def _sort_double_column(
        self, blocks: list[TextBlock], split_x: float, page_width: float
    ) -> list[TextBlock]:
        """
        Ordina blocchi per doppia colonna separando quelli a piena larghezza
        (titoli, intestazioni di sezione) dai blocchi di colonna veri.

        I blocchi piu larghi del 60% della pagina vengono trattati come
        full-width e posizionati prima/dopo i blocchi di colonna in base
        alla loro posizione Y relativa alla zona colonnata.
        """
        fw_limit = page_width * 0.60
        full_w = sorted(
            [b for b in blocks if (b.bbox[2] - b.bbox[0]) >= fw_limit], key=lambda b: b.bbox[1]
        )
        col_b = [b for b in blocks if (b.bbox[2] - b.bbox[0]) < fw_limit]

        if not col_b:
            return full_w

        col_top = min(b.bbox[1] for b in col_b)
        col_bottom = max(b.bbox[3] for b in col_b)

        fw_above = [b for b in full_w if b.bbox[3] <= col_top]
        fw_below = [b for b in full_w if b.bbox[1] >= col_bottom]
        fw_inside = [b for b in full_w if b not in fw_above and b not in fw_below]

        left = sorted([b for b in col_b if b.bbox[0] < split_x], key=lambda b: b.bbox[1])
        right = sorted([b for b in col_b if b.bbox[0] >= split_x], key=lambda b: b.bbox[1])

        return fw_above + fw_inside + left + right + fw_below

    @staticmethod
    def _overlaps_any(bbox: tuple, excluded: list[tuple], threshold: float = 0.3) -> bool:
        return _bbox_overlaps_any(bbox, excluded, threshold)

    def __del__(self):
        if hasattr(self, "doc"):
            with contextlib.suppress(Exception):
                self.doc.close()
