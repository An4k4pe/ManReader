"""Pure document-local references to a coherent ordered selection of page analyses."""

from __future__ import annotations

from dataclasses import dataclass

from page_analysis_model import PAGE_ANALYSIS_SCHEMA_VERSION, PageAnalysisProvenance

DOCUMENT_ANALYSIS_SCHEMA_VERSION = "1.0"


def _validate_non_empty_string(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class DocumentAnalysisProvenance:
    """Technical provenance for one document-local analysis generation."""

    source_id: str
    producer_name: str
    producer_version: str
    configuration_id: str

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.source_id, "source_id")
        _validate_non_empty_string(self.producer_name, "producer_name")
        _validate_non_empty_string(self.producer_version, "producer_version")
        _validate_non_empty_string(self.configuration_id, "configuration_id")


@dataclass(frozen=True, slots=True)
class PageAnalysisReference:
    """Logical reference to one page analysis without loading that analysis."""

    page_index: int
    page_id: str
    page_analysis_schema_version: str
    page_analysis_generation_id: str
    provenance: PageAnalysisProvenance

    def __post_init__(self) -> None:
        if isinstance(self.page_index, bool) or not isinstance(self.page_index, int):
            raise ValueError("page_index must be an int")
        if self.page_index < 0:
            raise ValueError("page_index must be non-negative")
        _validate_non_empty_string(self.page_id, "page_id")
        if self.page_analysis_schema_version != PAGE_ANALYSIS_SCHEMA_VERSION:
            raise ValueError("page_analysis_schema_version is not supported")
        _validate_non_empty_string(
            self.page_analysis_generation_id,
            "page_analysis_generation_id",
        )
        if not isinstance(self.provenance, PageAnalysisProvenance):
            raise ValueError("provenance must be a PageAnalysisProvenance")
        if self.page_id != self.provenance.source_page_id:
            raise ValueError("page_id must match provenance source_page_id")


@dataclass(frozen=True, slots=True)
class DocumentAnalysis:
    """Coherent ordered document-local selection of available page analyses."""

    schema_version: str
    generation_id: str
    page_count: int
    provenance: DocumentAnalysisProvenance
    pages: tuple[PageAnalysisReference, ...] = ()

    def __post_init__(self) -> None:
        if self.schema_version != DOCUMENT_ANALYSIS_SCHEMA_VERSION:
            raise ValueError("schema_version is not supported")
        _validate_non_empty_string(self.generation_id, "generation_id")
        if isinstance(self.page_count, bool) or not isinstance(self.page_count, int):
            raise ValueError("page_count must be an int")
        if self.page_count < 0:
            raise ValueError("page_count must be non-negative")
        if not isinstance(self.provenance, DocumentAnalysisProvenance):
            raise ValueError("provenance must be a DocumentAnalysisProvenance")
        if not isinstance(self.pages, tuple):
            raise ValueError("pages must be a tuple")

        previous_page_index = -1
        page_ids: set[str] = set()
        capture_ids: set[str] = set()
        expected_page_analysis_schema_version: str | None = None
        expected_primitive_schema_version: str | None = None
        expected_producer_name: str | None = None
        expected_producer_version: str | None = None
        expected_configuration_id: str | None = None

        for index, reference in enumerate(self.pages):
            if not isinstance(reference, PageAnalysisReference):
                raise ValueError(f"pages[{index}] must be a PageAnalysisReference")
            if reference.page_index >= self.page_count:
                raise ValueError("page_index must be less than page_count")
            if reference.page_index <= previous_page_index:
                raise ValueError("pages must be strictly increasing by page_index")
            previous_page_index = reference.page_index
            if reference.page_id in page_ids:
                raise ValueError("page_id values must be unique")
            page_ids.add(reference.page_id)
            if reference.provenance.source_capture_id in capture_ids:
                raise ValueError("source_capture_id values must be unique")
            capture_ids.add(reference.provenance.source_capture_id)
            if reference.provenance.source_id != self.provenance.source_id:
                raise ValueError("page reference source_id must match document source_id")

            if expected_page_analysis_schema_version is None:
                expected_page_analysis_schema_version = reference.page_analysis_schema_version
                expected_primitive_schema_version = reference.provenance.source_primitive_schema_version
                expected_producer_name = reference.provenance.producer_name
                expected_producer_version = reference.provenance.producer_version
                expected_configuration_id = reference.provenance.configuration_id
                continue

            if reference.page_analysis_schema_version != expected_page_analysis_schema_version:
                raise ValueError("page analysis schema versions must match")
            if reference.provenance.source_primitive_schema_version != expected_primitive_schema_version:
                raise ValueError("primitive schema versions must match")
            if reference.provenance.producer_name != expected_producer_name:
                raise ValueError("page analysis producer names must match")
            if reference.provenance.producer_version != expected_producer_version:
                raise ValueError("page analysis producer versions must match")
            if reference.provenance.configuration_id != expected_configuration_id:
                raise ValueError("page analysis configuration IDs must match")
