"""Tests for table candidate/TextPrimitive overlap measurements."""

from __future__ import annotations

import unittest

from page_analysis_candidate_primitive_overlap_measurements import (
    measure_candidate_primitive_overlap_ratio,
)


class CandidatePrimitiveOverlapMeasurementsTests(unittest.TestCase):
    def test_disjoint_bboxes_have_zero_overlap(self) -> None:
        self.assertEqual(
            measure_candidate_primitive_overlap_ratio(
                (0.0, 0.0, 10.0, 10.0),
                (20.0, 20.0, 30.0, 30.0),
            ),
            0.0,
        )

    def test_full_primitive_containment_has_ratio_one(self) -> None:
        self.assertEqual(
            measure_candidate_primitive_overlap_ratio(
                (0.0, 0.0, 10.0, 10.0),
                (2.0, 2.0, 4.0, 4.0),
            ),
            1.0,
        )

    def test_partial_overlap_is_relative_to_primitive_area(self) -> None:
        self.assertEqual(
            measure_candidate_primitive_overlap_ratio(
                (0.0, 0.0, 5.0, 10.0),
                (0.0, 0.0, 10.0, 10.0),
            ),
            0.5,
        )

    def test_zero_area_primitive_returns_zero(self) -> None:
        self.assertEqual(
            measure_candidate_primitive_overlap_ratio(
                (0.0, 0.0, 10.0, 10.0),
                (2.0, 2.0, 2.0, 4.0),
            ),
            0.0,
        )


if __name__ == "__main__":
    unittest.main()
