from __future__ import annotations

import unittest

from page_analysis_co_reference_candidate_reference import (
    CoReferencedPageCandidateReference,
)
from resolution_model import ResolvedCandidateOutcome, ResolvedPageCandidates


def _reference(candidate_id: str = "candidate:1") -> CoReferencedPageCandidateReference:
    return CoReferencedPageCandidateReference(
        producer_name="producer",
        producer_version="0.1",
        configuration_id="config-v1",
        generation_id="gen-1",
        candidate_id=candidate_id,
    )


class ResolvedCandidateOutcomeTest(unittest.TestCase):
    def test_accepted_requires_no_reason_token(self) -> None:
        outcome = ResolvedCandidateOutcome(
            candidate_reference=_reference(),
            outcome="accepted",
            reason_token=None,
        )
        self.assertEqual(outcome.outcome, "accepted")
        self.assertIsNone(outcome.reason_token)

    def test_accepted_with_reason_token_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "reason_token must be None"):
            ResolvedCandidateOutcome(
                candidate_reference=_reference(),
                outcome="accepted",
                reason_token="superseded_by_more_specific",
            )

    def test_rejected_requires_a_known_reason_token(self) -> None:
        outcome = ResolvedCandidateOutcome(
            candidate_reference=_reference(),
            outcome="rejected",
            reason_token="superseded_by_more_specific",
        )
        self.assertEqual(outcome.reason_token, "superseded_by_more_specific")

    def test_unresolved_requires_a_known_reason_token(self) -> None:
        outcome = ResolvedCandidateOutcome(
            candidate_reference=_reference(),
            outcome="unresolved",
            reason_token="no_applicable_rule",
        )
        self.assertEqual(outcome.reason_token, "no_applicable_rule")

    def test_rejected_without_reason_token_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "reason_token must not be None"):
            ResolvedCandidateOutcome(
                candidate_reference=_reference(),
                outcome="rejected",
                reason_token=None,
            )

    def test_unknown_reason_token_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown reason_token"):
            ResolvedCandidateOutcome(
                candidate_reference=_reference(),
                outcome="rejected",
                reason_token="not_a_real_token",
            )

    def test_unknown_outcome_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "outcome must be one of"):
            ResolvedCandidateOutcome(
                candidate_reference=_reference(),
                outcome="approved",  # type: ignore[arg-type]
                reason_token=None,
            )

    def test_reason_detail_is_free_form_and_unconstrained(self) -> None:
        outcome = ResolvedCandidateOutcome(
            candidate_reference=_reference(),
            outcome="unresolved",
            reason_token="no_applicable_rule",
            reason_detail="anything the caller wants to note",
        )
        self.assertEqual(outcome.reason_detail, "anything the caller wants to note")


class ResolvedPageCandidatesTest(unittest.TestCase):
    def test_accepts_empty_outcomes(self) -> None:
        resolved = ResolvedPageCandidates(page_id="page-1", outcomes=())
        self.assertEqual(resolved.outcomes, ())

    def test_accepts_distinct_outcomes(self) -> None:
        resolved = ResolvedPageCandidates(
            page_id="page-1",
            outcomes=(
                ResolvedCandidateOutcome(
                    candidate_reference=_reference("candidate:1"),
                    outcome="unresolved",
                    reason_token="no_applicable_rule",
                ),
                ResolvedCandidateOutcome(
                    candidate_reference=_reference("candidate:2"),
                    outcome="unresolved",
                    reason_token="no_applicable_rule",
                ),
            ),
        )
        self.assertEqual(len(resolved.outcomes), 2)

    def test_rejects_empty_page_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "page_id"):
            ResolvedPageCandidates(page_id="", outcomes=())

    def test_rejects_duplicate_candidate_reference(self) -> None:
        duplicate_reference = _reference("candidate:1")
        with self.assertRaisesRegex(ValueError, "must not reference the same candidate twice"):
            ResolvedPageCandidates(
                page_id="page-1",
                outcomes=(
                    ResolvedCandidateOutcome(
                        candidate_reference=duplicate_reference,
                        outcome="unresolved",
                        reason_token="no_applicable_rule",
                    ),
                    ResolvedCandidateOutcome(
                        candidate_reference=duplicate_reference,
                        outcome="unresolved",
                        reason_token="no_applicable_rule",
                    ),
                ),
            )

    def test_rejects_non_tuple_outcomes(self) -> None:
        with self.assertRaisesRegex(ValueError, "outcomes must be a tuple"):
            ResolvedPageCandidates(page_id="page-1", outcomes=[])  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
