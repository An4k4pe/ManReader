"""I corridoi respinti dall'ammissione di `layout.column_band`.

Milestone 44, Fase 1. Verificano tre cose: che un corridoio respinto non sparisca
piu', che uno ammesso non venga riportato come respinto, e che il record rifiuti
gli stati impossibili invece di lasciarli passare -- in particolare un respinto
**senza motivo**, che sarebbe uno scarto silenzioso registrato come tale.
"""

from __future__ import annotations

import unittest

from geometry_model import PageGeometry
from page_analysis_column_band import column_band_gutter_rows
from page_analysis_column_band_rejected_gutters import (
    RejectedGutter,
    measure_rejected_gutters,
)
from primitive_model import NormalizedPrimitivePage, TextPrimitive


def _span(block: int, text: str, bbox: tuple[float, float, float, float]) -> TextPrimitive:
    return TextPrimitive(
        primitive_id=f"p:{block}",
        bbox=bbox,
        text=text,
        source_observation_id=f"text:b{block:04d}:l0000:s0000",
    )


def _page(primitives: tuple[TextPrimitive, ...]) -> NormalizedPrimitivePage:
    return NormalizedPrimitivePage(
        schema_version="1",
        source_capture_id="capture-1",
        source_id="source-1",
        page_id="page:0001",
        page_index=0,
        page_geometry=PageGeometry(
            width=600.0, height=800.0, unit="pt", coordinate_system="top_left_y_down"
        ),
        capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
        text_primitives=primitives,
        image_primitives=(),
        drawing_primitives=(),
    )


def _tabella_con_colonna_di_numeri() -> NormalizedPrimitivePage:
    """Una colonna di numeri da un carattere accanto a una di testo.

    E' la forma che l'ammissione respinge con `too_few_wordy_lines`: nessuna
    riga del lato sinistro porta cinque caratteri."""

    primitives: list[TextPrimitive] = []
    for index in range(12):
        y = 100.0 + index * 14.0
        primitives.append(_span(index, str(index % 10), (60.0, y, 70.0, y + 11.0)))
        primitives.append(
            _span(index + 100, "descrizione lunga dell'effetto", (100.0, y, 540.0, y + 11.0))
        )
    return _page(tuple(primitives))


def _due_colonne_di_prosa() -> NormalizedPrimitivePage:
    primitives: list[TextPrimitive] = []
    for index in range(12):
        y = 100.0 + index * 14.0
        primitives.append(
            _span(index, "colonna sinistra con testo lungo", (60.0, y, 280.0, y + 11.0))
        )
        primitives.append(
            _span(index + 100, "colonna destra con testo lungo", (320.0, y, 540.0, y + 11.0))
        )
    return _page(tuple(primitives))


class RejectedGutterValidationTest(unittest.TestCase):
    def _valido(self, **override: object) -> dict[str, object]:
        campi: dict[str, object] = {
            "page_id": "page:0001",
            "x0": 70.0,
            "x1": 100.0,
            "y0": 100.0,
            "y1": 260.0,
            "height_in_page_lines": 11.4,
            "left_lines": 12,
            "right_lines": 12,
            "left_chars_total": 12,
            "right_chars_total": 360,
            "reject_reason": "too_few_wordy_lines",
            "rejected_only_by_wordiness": True,
        }
        campi.update(override)
        return campi

    def test_a_rejected_gutter_must_carry_its_reason(self) -> None:
        with self.assertRaises(ValueError):
            RejectedGutter(**self._valido(reject_reason=""))  # type: ignore[arg-type]

    def test_x1_must_exceed_x0(self) -> None:
        with self.assertRaises(ValueError):
            RejectedGutter(**self._valido(x1=70.0))  # type: ignore[arg-type]

    def test_y1_must_exceed_y0(self) -> None:
        with self.assertRaises(ValueError):
            RejectedGutter(**self._valido(y1=100.0))  # type: ignore[arg-type]

    def test_counts_must_not_be_negative(self) -> None:
        with self.assertRaises(ValueError):
            RejectedGutter(**self._valido(left_chars_total=-1))  # type: ignore[arg-type]

    def test_only_by_wordiness_requires_that_reason(self) -> None:
        with self.assertRaises(ValueError):
            RejectedGutter(  # type: ignore[arg-type]
                **self._valido(reject_reason="too_short", rejected_only_by_wordiness=True)
            )


class MeasureRejectedGuttersTest(unittest.TestCase):
    def test_an_accepted_gutter_is_not_reported_as_rejected(self) -> None:
        righe = column_band_gutter_rows(_due_colonne_di_prosa())
        self.assertTrue(any(row["reject_reason"] is None for row in righe))

        misure = measure_rejected_gutters("page:0001", righe)

        for misura in misure:
            self.assertNotEqual((misura.x0, misura.x1), (280.0, 320.0))

    def test_the_number_column_gutter_is_reported_with_its_reason(self) -> None:
        righe = column_band_gutter_rows(_tabella_con_colonna_di_numeri())

        misure = measure_rejected_gutters("page:0001", righe)

        respinti = [m for m in misure if m.reject_reason == "too_few_wordy_lines"]
        self.assertTrue(respinti, "il corridoio della colonna di numeri deve essere riportato")
        piu_alto = max(respinti, key=lambda m: m.y1 - m.y0)
        self.assertGreater(piu_alto.left_lines, 1)
        # Dodici righe da un carattere: la somma le vede, la regola per riga no.
        self.assertEqual(piu_alto.left_chars_total, 12)
        self.assertGreater(piu_alto.right_chars_total, piu_alto.left_chars_total)

    def test_rejects_an_empty_page_id(self) -> None:
        with self.assertRaises(ValueError):
            measure_rejected_gutters("", [])

    def test_an_empty_page_has_nothing_to_report(self) -> None:
        vuota = _page(())

        self.assertEqual(column_band_gutter_rows(vuota), [])
        self.assertEqual(measure_rejected_gutters("page:0001", []), ())


if __name__ == "__main__":
    unittest.main()
