"""Pure page-local collection of co-referenced page analyses.

The collection records only declared co-reference: source, capture, page, and
primitive schema.  It neither revalidates analyses against primitives nor
merges, selects, or interprets their contents.
"""

from __future__ import annotations

from dataclasses import dataclass

from page_analysis_model import PageAnalysis


def _require_non_empty_string(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")


def _analysis_stream_key(analysis: PageAnalysis) -> tuple[str, str, str, str]:
    provenance = analysis.provenance
    return (
        provenance.producer_name,
        provenance.producer_version,
        provenance.configuration_id,
        analysis.generation_id,
    )


def _validate_co_reference(
    analyses: tuple[PageAnalysis, ...],
    *,
    source_id: str,
    source_capture_id: str,
    page_id: str,
    source_primitive_schema_version: str,
) -> None:
    expected_schema_version: str | None = None
    for index, analysis in enumerate(analyses):
        if not isinstance(analysis, PageAnalysis):
            raise ValueError(f"analyses[{index}] must be a PageAnalysis")

        provenance = analysis.provenance
        if provenance.source_id != source_id:
            raise ValueError("analyses must share source_id")
        if provenance.source_capture_id != source_capture_id:
            raise ValueError("analyses must share source_capture_id")
        if analysis.page_id != page_id:
            raise ValueError("analyses must share page_id")
        if provenance.source_primitive_schema_version != source_primitive_schema_version:
            raise ValueError("analyses must share source_primitive_schema_version")

        if expected_schema_version is None:
            expected_schema_version = analysis.schema_version
        elif analysis.schema_version != expected_schema_version:
            raise ValueError("analyses must share schema_version")


@dataclass(frozen=True, slots=True)
class CoReferencedPageAnalyses:
    """Ordered page analyses with one shared declared page-local subject."""

    source_id: str
    source_capture_id: str
    page_id: str
    source_primitive_schema_version: str
    analyses: tuple[PageAnalysis, ...]

    def __post_init__(self) -> None:
        _require_non_empty_string(self.source_id, "source_id")
        _require_non_empty_string(self.source_capture_id, "source_capture_id")
        _require_non_empty_string(self.page_id, "page_id")
        _require_non_empty_string(
            self.source_primitive_schema_version,
            "source_primitive_schema_version",
        )
        if not isinstance(self.analyses, tuple):
            raise ValueError("analyses must be a tuple")
        if not self.analyses:
            raise ValueError("analyses must not be empty")

        _validate_co_reference(
            self.analyses,
            source_id=self.source_id,
            source_capture_id=self.source_capture_id,
            page_id=self.page_id,
            source_primitive_schema_version=self.source_primitive_schema_version,
        )

        previous_key: tuple[str, str, str, str] | None = None
        for analysis in self.analyses:
            current_key = _analysis_stream_key(analysis)
            if previous_key is not None and current_key <= previous_key:
                raise ValueError(
                    "analyses must be strictly ordered by analysis stream key"
                )
            previous_key = current_key


def build_co_referenced_page_analyses(
    analyses: tuple[PageAnalysis, ...],
) -> CoReferencedPageAnalyses:
    """Canonicalize a non-empty tuple of analyses sharing one declared page."""

    if not isinstance(analyses, tuple):
        raise ValueError("analyses must be a tuple")
    if not analyses:
        raise ValueError("analyses must not be empty")
    for index, analysis in enumerate(analyses):
        if not isinstance(analysis, PageAnalysis):
            raise ValueError(f"analyses[{index}] must be a PageAnalysis")

    first_analysis = analyses[0]
    first_provenance = first_analysis.provenance
    source_id = first_provenance.source_id
    source_capture_id = first_provenance.source_capture_id
    page_id = first_analysis.page_id
    source_primitive_schema_version = first_provenance.source_primitive_schema_version

    _validate_co_reference(
        analyses,
        source_id=source_id,
        source_capture_id=source_capture_id,
        page_id=page_id,
        source_primitive_schema_version=source_primitive_schema_version,
    )
    canonical_analyses = tuple(sorted(analyses, key=_analysis_stream_key))
    return CoReferencedPageAnalyses(
        source_id=source_id,
        source_capture_id=source_capture_id,
        page_id=page_id,
        source_primitive_schema_version=source_primitive_schema_version,
        analyses=canonical_analyses,
    )
