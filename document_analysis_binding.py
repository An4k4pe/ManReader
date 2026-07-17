"""Pure in-memory positional binding of document page references and analyses."""

from __future__ import annotations

from dataclasses import dataclass

from document_analysis_model import DocumentAnalysis, PageAnalysisReference
from page_analysis_model import PageAnalysis


@dataclass(frozen=True, slots=True)
class BoundPageAnalysis:
    """One logical page reference paired with its matching in-memory analysis."""

    reference: PageAnalysisReference
    analysis: PageAnalysis

    def __post_init__(self) -> None:
        if not isinstance(self.reference, PageAnalysisReference):
            raise ValueError("reference must be a PageAnalysisReference")
        if not isinstance(self.analysis, PageAnalysis):
            raise ValueError("analysis must be a PageAnalysis")
        if self.reference.page_id != self.analysis.page_id:
            raise ValueError("reference page_id must match analysis page_id")
        if self.reference.page_analysis_schema_version != self.analysis.schema_version:
            raise ValueError("reference schema_version must match analysis schema_version")
        if self.reference.page_analysis_generation_id != self.analysis.generation_id:
            raise ValueError(
                "reference generation_id must match analysis generation_id"
            )
        if self.reference.provenance != self.analysis.provenance:
            raise ValueError("reference provenance must match analysis provenance")


@dataclass(frozen=True, slots=True)
class BoundDocumentAnalysis:
    """A complete positional binding for all references in one document analysis."""

    document_analysis: DocumentAnalysis
    pages: tuple[BoundPageAnalysis, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.document_analysis, DocumentAnalysis):
            raise ValueError("document_analysis must be a DocumentAnalysis")
        if not isinstance(self.pages, tuple):
            raise ValueError("pages must be a tuple")
        if len(self.pages) != len(self.document_analysis.pages):
            raise ValueError("pages length must match document_analysis pages")

        for index, bound_page in enumerate(self.pages):
            if not isinstance(bound_page, BoundPageAnalysis):
                raise ValueError(f"pages[{index}] must be a BoundPageAnalysis")
            if bound_page.reference != self.document_analysis.pages[index]:
                raise ValueError(
                    f"pages[{index}] reference must match document_analysis pages"
                )


def bind_document_analysis(
    document_analysis: DocumentAnalysis,
    *,
    analyses: tuple[PageAnalysis, ...],
) -> BoundDocumentAnalysis:
    """Bind every document reference to the analysis at the same tuple position."""

    if not isinstance(document_analysis, DocumentAnalysis):
        raise ValueError("document_analysis must be a DocumentAnalysis")
    if not isinstance(analyses, tuple):
        raise ValueError("analyses must be a tuple")
    if len(analyses) != len(document_analysis.pages):
        raise ValueError("analyses length must match document_analysis pages")

    bound_pages: list[BoundPageAnalysis] = []
    for index, analysis in enumerate(analyses):
        if not isinstance(analysis, PageAnalysis):
            raise ValueError(f"analyses[{index}] must be a PageAnalysis")
        bound_pages.append(
            BoundPageAnalysis(
                reference=document_analysis.pages[index],
                analysis=analysis,
            )
        )

    return BoundDocumentAnalysis(
        document_analysis=document_analysis,
        pages=tuple(bound_pages),
    )
