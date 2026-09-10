"""La regola V4 di Resolution: i corridoi respinti dentro una tabella.

Milestone 44, Fase 2. Testano cio' che la regola DECIDE, e i quattro esiti
possibili: ammesso dentro una tabella, non ammesso perche' fuori, non ammesso
perche' un lato e' vuoto, non ammesso perche' lo scarto aveva un altro motivo.
Nessun corridoio respinto resta senza esito.
"""

from __future__ import annotations

import unittest

from page_analysis_column_band_rejected_gutters import RejectedGutter
from page_analysis_model import RegionCandidate
from resolution_column_boundaries import (
    ResolvedColumnBoundary,
    resolve_column_boundaries,
)

PAGINA = "page:0001"


def _gutter(
    *,
    x0: float = 80.0,
    x1: float = 90.0,
    left: int = 6,
    right: int = 1200,
    reason: str = "too_few_wordy_lines",
    solo_parole: bool = True,
) -> RejectedGutter:
    return RejectedGutter(
        page_id=PAGINA,
        x0=x0,
        x1=x1,
        y0=100.0,
        y1=400.0,
        height_in_page_lines=20.0,
        left_lines=6,
        right_lines=30,
        left_chars_total=left,
        right_chars_total=right,
        reject_reason=reason,
        rejected_only_by_wordiness=solo_parole,
    )


def _tabella(bbox: tuple[float, float, float, float] = (60.0, 90.0, 520.0, 500.0)):  # type: ignore[no-untyped-def]
    return RegionCandidate(
        candidate_id="candidate:table:page:0001:1",
        page_id=PAGINA,
        bbox=bbox,
        proposed_structural_kind="layout.table_candidate",
        primitive_ids=("p:1",),
    )


class ResolveColumnBoundariesTest(unittest.TestCase):
    def test_a_gutter_inside_a_table_with_text_on_both_sides_is_admitted(self) -> None:
        risolti = resolve_column_boundaries(
            page_id=PAGINA, rejected_gutters=(_gutter(),), table_candidates=(_tabella(),)
        )

        self.assertEqual(len(risolti.admitted), 1)
        self.assertEqual(risolti.boundaries[0].outcome, "admitted")
        self.assertEqual(risolti.boundaries[0].reason_token, "admitted_by_table_context")

    def test_an_empty_flank_is_not_admitted_even_inside_a_table(self) -> None:
        risolti = resolve_column_boundaries(
            page_id=PAGINA,
            rejected_gutters=(_gutter(left=0),),
            table_candidates=(_tabella(),),
        )

        self.assertEqual(risolti.admitted, ())
        self.assertEqual(risolti.boundaries[0].reason_token, "empty_flank")

    def test_outside_any_table_nothing_changes(self) -> None:
        risolti = resolve_column_boundaries(
            page_id=PAGINA, rejected_gutters=(_gutter(),), table_candidates=()
        )

        self.assertEqual(risolti.admitted, ())
        self.assertEqual(risolti.boundaries[0].reason_token, "outside_table_candidate")

    def test_a_gutter_rejected_for_another_reason_is_left_alone(self) -> None:
        risolti = resolve_column_boundaries(
            page_id=PAGINA,
            rejected_gutters=(_gutter(reason="too_short", solo_parole=False),),
            table_candidates=(_tabella(),),
        )

        self.assertEqual(risolti.admitted, ())
        self.assertEqual(risolti.boundaries[0].reason_token, "other_reject_reason")

    def test_a_table_that_does_not_cover_the_gutter_does_not_count(self) -> None:
        risolti = resolve_column_boundaries(
            page_id=PAGINA,
            rejected_gutters=(_gutter(),),
            table_candidates=(_tabella(bbox=(200.0, 90.0, 520.0, 500.0)),),
        )

        self.assertEqual(risolti.boundaries[0].reason_token, "outside_table_candidate")

    def test_every_rejected_gutter_gets_an_outcome(self) -> None:
        gutters = (_gutter(), _gutter(x0=200.0, x1=210.0, left=0))

        risolti = resolve_column_boundaries(
            page_id=PAGINA, rejected_gutters=gutters, table_candidates=(_tabella(),)
        )

        self.assertEqual(len(risolti.boundaries), len(gutters))

    def test_rejects_a_gutter_from_another_page(self) -> None:
        with self.assertRaises(ValueError):
            resolve_column_boundaries(
                page_id="page:0002", rejected_gutters=(_gutter(),), table_candidates=()
            )


class ResolvedColumnBoundaryValidationTest(unittest.TestCase):
    def test_admitted_must_carry_the_admission_token(self) -> None:
        with self.assertRaises(ValueError):
            ResolvedColumnBoundary(
                page_id=PAGINA, x0=1.0, x1=2.0, y0=1.0, y1=2.0,
                outcome="admitted", reason_token="empty_flank",
            )

    def test_not_admitted_must_not_carry_the_admission_token(self) -> None:
        with self.assertRaises(ValueError):
            ResolvedColumnBoundary(
                page_id=PAGINA, x0=1.0, x1=2.0, y0=1.0, y1=2.0,
                outcome="not_admitted", reason_token="admitted_by_table_context",
            )

    def test_unknown_reason_token_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            ResolvedColumnBoundary(
                page_id=PAGINA, x0=1.0, x1=2.0, y0=1.0, y1=2.0,
                outcome="not_admitted", reason_token="perche_si",
            )


if __name__ == "__main__":
    unittest.main()
