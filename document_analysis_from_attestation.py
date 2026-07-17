"""Canonical construction of document analysis from a source attestation."""

from __future__ import annotations

from document_analysis_model import (
    DOCUMENT_ANALYSIS_SCHEMA_VERSION,
    DocumentAnalysis,
    DocumentAnalysisProvenance,
    PageAnalysisReference,
)
from document_source_attestation_model import DocumentSourceAttestation


def build_attested_document_analysis(
    attestation: DocumentSourceAttestation,
    *,
    generation_id: str,
    producer_name: str,
    producer_version: str,
    configuration_id: str,
    pages: tuple[PageAnalysisReference, ...] = (),
) -> DocumentAnalysis:
    """Build one document analysis from one attested source without altering pages."""

    if not isinstance(attestation, DocumentSourceAttestation):
        raise ValueError("attestation must be a DocumentSourceAttestation")

    provenance = DocumentAnalysisProvenance(
        source_id=attestation.source_id,
        producer_name=producer_name,
        producer_version=producer_version,
        configuration_id=configuration_id,
    )
    return DocumentAnalysis(
        schema_version=DOCUMENT_ANALYSIS_SCHEMA_VERSION,
        generation_id=generation_id,
        page_count=attestation.page_count,
        provenance=provenance,
        pages=pages,
    )
