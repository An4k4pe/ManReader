from __future__ import annotations

import math
import unittest
from dataclasses import FrozenInstanceError
from typing import cast

from page_analysis_candidate_extent_relation_measurements import (
    CandidateExtentRelationMeasurements,
    CandidateNonCandidateExtentRelationMeasurements,
    measure_candidate_non_candidate_extent_relations,
)
from page_analysis_candidate_page_context_measurements import (
    CandidatePageContextMeasurements,
)


class CandidateExtentRelationMeasurementsTests(unittest.TestCase):
    def test_dataclasses_are_equal_immutable_and_slotted(self) -> None:
        relation = _relation()
        self.assertEqual(relation, _relation())
        with self.assertRaises(FrozenInstanceError):
            relation.horizontal_gap = 2.0  # type: ignore[misc]
        self.assertFalse(hasattr(relation, "__dict__"))

        result = _result(text_extent=(20.0, 0.0, 30.0, 10.0), text_relation=relation)
        self.assertEqual(
            result,
            _result(text_extent=(20.0, 0.0, 30.0, 10.0), text_relation=_relation()),
        )
        with self.assertRaises(FrozenInstanceError):
            result.candidate_id = "other"  # type: ignore[misc]
        self.assertFalse(hasattr(result, "__dict__"))

    def test_rejects_runtime_input_that_is_not_page_context_measurements(self) -> None:
        with self.assertRaisesRegex(ValueError, "CandidatePageContextMeasurements"):
            measure_candidate_non_candidate_extent_relations(cast(CandidatePageContextMeasurements, object()))

    def test_all_missing_extents_remain_none(self) -> None:
        result = measure_candidate_non_candidate_extent_relations(_context())

        self.assertIsNone(result.non_candidate_visible_text_extent_bbox)
        self.assertIsNone(result.non_candidate_visible_text_extent_relation)
        self.assertIsNone(result.non_candidate_visible_image_extent_bbox)
        self.assertIsNone(result.non_candidate_visible_image_extent_relation)
        self.assertIsNone(result.non_candidate_visible_drawing_extent_bbox)
        self.assertIsNone(result.non_candidate_visible_drawing_extent_relation)

    def test_is_deterministic_and_does_not_mutate_input(self) -> None:
        context = _context(text_extent=(20.0, 2.0, 30.0, 8.0))
        before = context

        self.assertEqual(
            measure_candidate_non_candidate_extent_relations(context),
            measure_candidate_non_candidate_extent_relations(context),
        )
        self.assertEqual(context, before)

    def test_horizontal_gap_with_vertical_overlap(self) -> None:
        result = measure_candidate_non_candidate_extent_relations(
            _context(text_extent=(20.0, 2.0, 30.0, 8.0))
        )

        self.assertEqual(
            result.non_candidate_visible_text_extent_relation,
            _relation(horizontal_gap=10.0, vertical_overlap=6.0),
        )

    def test_vertical_gap_with_horizontal_overlap(self) -> None:
        result = measure_candidate_non_candidate_extent_relations(
            _context(image_extent=(2.0, 20.0, 8.0, 30.0))
        )

        self.assertEqual(
            result.non_candidate_visible_image_extent_relation,
            _relation(vertical_gap=10.0, horizontal_overlap=6.0),
        )

    def test_positive_intersection_is_observable_from_both_overlaps(self) -> None:
        result = measure_candidate_non_candidate_extent_relations(
            _context(drawing_extent=(2.0, 3.0, 8.0, 9.0))
        )

        relation = result.non_candidate_visible_drawing_extent_relation
        self.assertIsNotNone(relation)
        assert relation is not None
        self.assertEqual(relation.horizontal_overlap, 6.0)
        self.assertEqual(relation.vertical_overlap, 6.0)

    def test_border_touch_has_zero_gap_and_overlap_on_touched_axis(self) -> None:
        result = measure_candidate_non_candidate_extent_relations(
            _context(text_extent=(10.0, 2.0, 20.0, 8.0))
        )

        relation = result.non_candidate_visible_text_extent_relation
        self.assertIsNotNone(relation)
        assert relation is not None
        self.assertEqual(relation.horizontal_gap, 0.0)
        self.assertEqual(relation.horizontal_overlap, 0.0)
        self.assertEqual(relation.vertical_gap, 0.0)
        self.assertEqual(relation.vertical_overlap, 6.0)

    def test_candidate_contains_extent_inclusively(self) -> None:
        result = measure_candidate_non_candidate_extent_relations(
            _context(text_extent=(2.0, 2.0, 8.0, 8.0))
        )

        relation = result.non_candidate_visible_text_extent_relation
        self.assertIsNotNone(relation)
        assert relation is not None
        self.assertTrue(relation.candidate_contains_extent)
        self.assertFalse(relation.extent_contains_candidate)

    def test_extent_contains_candidate_inclusively(self) -> None:
        result = measure_candidate_non_candidate_extent_relations(
            _context(text_extent=(-2.0, -2.0, 12.0, 12.0))
        )

        relation = result.non_candidate_visible_text_extent_relation
        self.assertIsNotNone(relation)
        assert relation is not None
        self.assertFalse(relation.candidate_contains_extent)
        self.assertTrue(relation.extent_contains_candidate)

    def test_identical_bboxes_contain_each_other(self) -> None:
        result = measure_candidate_non_candidate_extent_relations(
            _context(text_extent=(0.0, 0.0, 10.0, 10.0))
        )

        relation = result.non_candidate_visible_text_extent_relation
        self.assertIsNotNone(relation)
        assert relation is not None
        self.assertTrue(relation.candidate_contains_extent)
        self.assertTrue(relation.extent_contains_candidate)

    def test_relations_remain_separate_by_primitive_family(self) -> None:
        result = measure_candidate_non_candidate_extent_relations(
            _context(
                text_extent=(20.0, 0.0, 30.0, 10.0),
                image_extent=(0.0, 20.0, 10.0, 30.0),
                drawing_extent=(2.0, 2.0, 8.0, 8.0),
            )
        )

        self.assertEqual(
            result.non_candidate_visible_text_extent_relation,
            _relation(horizontal_gap=10.0, vertical_overlap=10.0),
        )
        self.assertEqual(
            result.non_candidate_visible_image_extent_relation,
            _relation(vertical_gap=10.0, horizontal_overlap=10.0),
        )
        self.assertEqual(
            result.non_candidate_visible_drawing_extent_relation,
            _relation(horizontal_overlap=6.0, vertical_overlap=6.0, candidate_contains_extent=True),
        )

    def test_candidate_bbox_is_used_unchanged_when_outside_the_page(self) -> None:
        context = _context(
            candidate_bbox=(-20.0, -10.0, -5.0, -1.0),
            text_extent=(0.0, 0.0, 10.0, 10.0),
        )
        result = measure_candidate_non_candidate_extent_relations(context)

        self.assertEqual(result.candidate_bbox, (-20.0, -10.0, -5.0, -1.0))
        self.assertEqual(
            result.non_candidate_visible_text_extent_relation,
            _relation(horizontal_gap=5.0, vertical_gap=1.0),
        )

    def test_direct_construction_rejects_invalid_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "horizontal_gap"):
            _relation(horizontal_gap=-0.1)
        with self.assertRaisesRegex(ValueError, "vertical_gap"):
            _relation(vertical_gap=math.inf)
        with self.assertRaisesRegex(ValueError, "horizontal_overlap"):
            _relation(horizontal_overlap=True)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "candidate_contains_extent"):
            _relation(candidate_contains_extent=1)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "candidate_id"):
            _result(candidate_id="")
        with self.assertRaisesRegex(ValueError, "candidate_bbox"):
            CandidateNonCandidateExtentRelationMeasurements(
                candidate_id="candidate:context",
                page_id="page-1",
                candidate_bbox=(0.0, 0.0, 0.0, 10.0),
                candidate_primitive_ids=(),
                non_candidate_visible_text_extent_bbox=None,
                non_candidate_visible_text_extent_relation=None,
                non_candidate_visible_image_extent_bbox=None,
                non_candidate_visible_image_extent_relation=None,
                non_candidate_visible_drawing_extent_bbox=None,
                non_candidate_visible_drawing_extent_relation=None,
            )
        with self.assertRaisesRegex(ValueError, "candidate_primitive_ids"):
            _result(candidate_primitive_ids=("p1", "p1"))
        with self.assertRaisesRegex(ValueError, "candidate_primitive_ids"):
            _result(candidate_primitive_ids=("",))
        with self.assertRaisesRegex(ValueError, "both be None or present"):
            _result(text_extent=(20.0, 0.0, 30.0, 10.0))
        with self.assertRaisesRegex(ValueError, "both be None or present"):
            _result(text_relation=_relation())

    def test_public_dataclasses_do_not_expose_forbidden_fields(self) -> None:
        forbidden_terms = (
            "ratio",
            "distance",
            "intersects",
            "score",
            "confidence",
            "ranking",
            "evidence",
            "classification",
        )
        public_fields = {
            *CandidateExtentRelationMeasurements.__dataclass_fields__,
            *CandidateNonCandidateExtentRelationMeasurements.__dataclass_fields__,
        }
        for forbidden_term in forbidden_terms:
            self.assertFalse(any(forbidden_term in field_name for field_name in public_fields))


def _context(
    *,
    candidate_bbox: tuple[float, float, float, float] = (0.0, 0.0, 10.0, 10.0),
    candidate_primitive_ids: tuple[str, ...] = ("candidate",),
    text_extent: tuple[float, float, float, float] | None = None,
    image_extent: tuple[float, float, float, float] | None = None,
    drawing_extent: tuple[float, float, float, float] | None = None,
) -> CandidatePageContextMeasurements:
    return CandidatePageContextMeasurements(
        candidate_id="candidate:context",
        page_id="page-1",
        candidate_bbox=candidate_bbox,
        candidate_primitive_ids=candidate_primitive_ids,
        non_candidate_visible_text_primitive_count=_count_for(text_extent),
        non_candidate_visible_text_extent_bbox=text_extent,
        non_candidate_visible_image_primitive_count=_count_for(image_extent),
        non_candidate_visible_image_extent_bbox=image_extent,
        non_candidate_visible_drawing_primitive_count=_count_for(drawing_extent),
        non_candidate_visible_drawing_extent_bbox=drawing_extent,
    )


def _count_for(extent: tuple[float, float, float, float] | None) -> int:
    return 0 if extent is None else 1


def _relation(
    *,
    horizontal_gap: float = 0.0,
    vertical_gap: float = 0.0,
    horizontal_overlap: float = 0.0,
    vertical_overlap: float = 0.0,
    candidate_contains_extent: bool = False,
    extent_contains_candidate: bool = False,
) -> CandidateExtentRelationMeasurements:
    return CandidateExtentRelationMeasurements(
        horizontal_gap=horizontal_gap,
        vertical_gap=vertical_gap,
        horizontal_overlap=horizontal_overlap,
        vertical_overlap=vertical_overlap,
        candidate_contains_extent=candidate_contains_extent,
        extent_contains_candidate=extent_contains_candidate,
    )


def _result(
    *,
    candidate_id: str = "candidate:context",
    candidate_primitive_ids: tuple[str, ...] = ("candidate",),
    text_extent: tuple[float, float, float, float] | None = None,
    text_relation: CandidateExtentRelationMeasurements | None = None,
) -> CandidateNonCandidateExtentRelationMeasurements:
    return CandidateNonCandidateExtentRelationMeasurements(
        candidate_id=candidate_id,
        page_id="page-1",
        candidate_bbox=(0.0, 0.0, 10.0, 10.0),
        candidate_primitive_ids=candidate_primitive_ids,
        non_candidate_visible_text_extent_bbox=text_extent,
        non_candidate_visible_text_extent_relation=text_relation,
        non_candidate_visible_image_extent_bbox=None,
        non_candidate_visible_image_extent_relation=None,
        non_candidate_visible_drawing_extent_bbox=None,
        non_candidate_visible_drawing_extent_relation=None,
    )


if __name__ == "__main__":
    unittest.main()
