"""Validated construction of one document-local page analysis reference."""

from __future__ import annotations

from document_analysis_model import PageAnalysisReference
from page_analysis_model import PageAnalysis
from page_analysis_validate import validate_page_analysis_against_primitive_page
from primitive_model import NormalizedPrimitivePage


def build_validated_page_analysis_reference(
    primitive_page: NormalizedPrimitivePage,
    *,
    analysis: PageAnalysis,
) -> PageAnalysisReference:
    """Build one logical reference only after fully validating analysis against page."""

    validate_page_analysis_against_primitive_page(analysis, primitive_page)
    return PageAnalysisReference(
        page_index=primitive_page.page_index,
        page_id=analysis.page_id,
        page_analysis_schema_version=analysis.schema_version,
        page_analysis_generation_id=analysis.generation_id,
        provenance=analysis.provenance,
    )
