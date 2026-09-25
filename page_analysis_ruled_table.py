"""Producer delle tabelle a filetti: le griglie che le righe disegnate risolvono.

`Criterio_TabellaAFiletti_v1.md`, dall'idea di `Criterio_TabellaRisolvibile_v1.md`
(20 agosto 2026, mai eseguito): «una regione che una strategia a filetti risolve
con celle piene e' una tabella».

**Perche' serve accanto a `table_candidate`.** `table_candidate` cerca le colonne
dove il testo si allinea e le righe dove c'e' un filetto. Su una pagina a due
colonne di prosa con un filetto di separazione vede una tabella che non esiste:
Dag idx 108, due colonne di pura prosa; DB idx 43, un elenco puntato in una
cornice. Qui si cercano **sia le colonne sia le righe** fra le linee disegnate e i
bordi dei rettangoli — la strategia di default di pdfplumber — e una tabella vera
le ha: filetti, oppure righe ombreggiate, i cui rettangoli danno i bordi.

**Le due soglie sono quelle registrate ad agosto**, non tarate qui: una griglia
deve avere almeno due celle, e almeno l'80% di celle non vuote. Nell'esplorazione
di oggi, su dieci pagine etichettate prima di guardare, le tabelle vere danno
100% (86% la tabella degli ingredienti di Wilder) e i fantasmi 0-50%.

Il producer propone e basta: decidere che una regione di `table_candidate` e' un
fantasma e' del consumer.
"""

from __future__ import annotations

from typing import Any

from page_analysis_candidate_primitive_overlap_measurements import (
    measure_candidate_primitive_overlap_ratio,
)
from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionCandidate,
)
from page_analysis_table_candidate_binding import BoundTableCandidatePage
from page_analysis_validate import validate_page_analysis_against_primitive_page

MINIMO_CELLE = 2
QUOTA_CELLE_PIENE = 0.8


def filled_share(table: Any) -> tuple[int, float]:
    """Quante celle ha la griglia, e quale quota non e' vuota."""

    celle = [cella for riga in table.extract() for cella in riga]
    piene = sum(1 for cella in celle if isinstance(cella, str) and cella.strip())
    return len(celle), (piene / len(celle) if celle else 0.0)


def build_ruled_table_page_analysis(
    bound_page: BoundTableCandidatePage, *, generation_id: str
) -> PageAnalysis:
    """Le griglie a filetti ben piene della pagina, senza aprire file."""

    primitive_page = bound_page.primitive_page
    larghezza = primitive_page.page_geometry.width
    altezza = primitive_page.page_geometry.height
    candidates: list[RegionCandidate] = []
    for numero, table in enumerate(bound_page.plumber_page.find_tables()):
        celle, quota = filled_share(table)
        if celle < MINIMO_CELLE or quota < QUOTA_CELLE_PIENE:
            continue
        x0, y0, x1, y1 = (float(v) for v in table.bbox)
        x0, y0, x1, y1 = max(x0, 0.0), max(y0, 0.0), min(x1, larghezza), min(y1, altezza)
        if x0 >= x1 or y0 >= y1:
            continue
        bbox = (x0, y0, x1, y1)
        candidates.append(
            RegionCandidate(
                candidate_id=f"candidate:ruled_table:{numero:04d}",
                page_id=primitive_page.page_id,
                bbox=bbox,
                proposed_structural_kind="layout.ruled_table",
                primitive_ids=tuple(
                    primitive.primitive_id
                    for primitive in primitive_page.text_primitives
                    if measure_candidate_primitive_overlap_ratio(bbox, primitive.bbox) > 0.0
                ),
            )
        )

    analysis = PageAnalysis(
        schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        generation_id=generation_id,
        page_id=primitive_page.page_id,
        provenance=PageAnalysisProvenance(
            source_id=primitive_page.source_id,
            source_capture_id=primitive_page.source_capture_id,
            source_page_id=primitive_page.page_id,
            source_primitive_schema_version=primitive_page.schema_version,
            producer_name="page_analysis.ruled_table",
            producer_version="0.1",
            configuration_id="ruled_table:lines:min2:filled80",
        ),
        regions=(),
        relations=(),
        candidates=tuple(candidates),
    )
    validate_page_analysis_against_primitive_page(analysis, primitive_page)
    return analysis
