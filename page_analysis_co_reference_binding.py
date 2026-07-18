"""Pure binding of co-referenced analyses to one normalized primitive page."""

from __future__ import annotations

from dataclasses import dataclass

from page_analysis_co_reference import CoReferencedPageAnalyses
from page_analysis_validate import validate_page_analysis_against_primitive_page
from primitive_model import NormalizedPrimitivePage


@dataclass(frozen=True, slots=True)
class BoundCoReferencedPageAnalyses:
    """Co-referenced analyses each validated against the same primitive page."""

    primitive_page: NormalizedPrimitivePage
    co_referenced_page_analyses: CoReferencedPageAnalyses

    def __post_init__(self) -> None:
        if not isinstance(self.primitive_page, NormalizedPrimitivePage):
            raise ValueError("primitive_page must be a NormalizedPrimitivePage")
        if not isinstance(
            self.co_referenced_page_analyses,
            CoReferencedPageAnalyses,
        ):
            raise ValueError(
                "co_referenced_page_analyses must be a CoReferencedPageAnalyses"
            )

        for analysis in self.co_referenced_page_analyses.analyses:
            validate_page_analysis_against_primitive_page(
                analysis,
                self.primitive_page,
            )


def bind_co_referenced_page_analyses(
    primitive_page: NormalizedPrimitivePage,
    *,
    co_referenced_page_analyses: CoReferencedPageAnalyses,
) -> BoundCoReferencedPageAnalyses:
    """Bind a valid co-referenced collection to one normalized primitive page."""

    return BoundCoReferencedPageAnalyses(
        primitive_page=primitive_page,
        co_referenced_page_analyses=co_referenced_page_analyses,
    )
