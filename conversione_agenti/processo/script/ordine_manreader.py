"""Ordine di lettura e livelli dei titoli presi da ManReader, non ricostruiti qui.

Chiama il producer `column_band` di ManReader (Milestone 37, wired) e l'ordinatore ad albero
della fetta verticale (`_tree_aware_order`: vince la banda piu' profonda), sulle primitive di
testo della pagina; restituisce per ogni primitiva il suo rango. La bozza ordina le sue righe
con quei ranghi. Vedi CONSULTAZIONI_MANREADER.md (28 set 2026).
"""
import os
import sys

MR = os.environ.get('MANREADER_REPO',
                    '/home/an4k4pe/Documenti/ManReader (Copia)/.claude/worktrees/asset-note-visibility-e14deb')
for p in (MR, os.path.join(MR, 'scripts')):
    if p not in sys.path:
        sys.path.insert(0, p)

from pymupdf_capture import capture_pymupdf_page  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from page_analysis_column_band import build_column_band_page_analysis_with_measurements  # noqa: E402
from compare_reading_order_with_column_bands import _tree_aware_order  # noqa: E402
from prototype_vertical_slice_page import _tree_rows_from_contract  # noqa: E402


def primitive_ranks(page):
    """[(bbox, rango)] delle primitive di testo nell'ordine di ManReader, e l'albero di bande."""
    n = page.number + 1
    cap = capture_pymupdf_page(page, source_id='bozza', page_id=f'page:{n:04d}', capture_id=f'bozza:{n:04d}')
    prim = normalize_backend_page_capture(cap)
    an, meas = build_column_band_page_analysis_with_measurements(prim, generation_id=f'bozza:{n:04d}')
    tree = _tree_rows_from_contract(an.candidates, meas)
    ordered, _ = _tree_aware_order(list(prim.text_primitives), tree)
    return [(tuple(p.bbox), i) for i, (p, _) in enumerate(ordered)], tree


def heading_size_levels(doc):
    """{dimensione: livello 1-3} dei titoli, decisi sull'intero documento dalla politica per fascia di
    ManReader (`document_heading_band_policy.heading_bands`, Criterio_TitoliPerFascia_v2): dimensioni
    vicine = stesso livello su tutte le pagine, prosa mai titolo, al massimo tre livelli (decisione
    dell'utente). Restituisce anche il tetto della prosa."""
    from document_heading_band_measurements import measure_size_mass
    from document_heading_band_policy import heading_bands
    from document_heading_measurements import measure_font_sizes
    pages = []
    for page in doc:
        n = page.number + 1
        cap = capture_pymupdf_page(page, source_id='bozza', page_id=f'page:{n:04d}', capture_id=f'bozza:{n:04d}')
        pages.append(normalize_backend_page_capture(cap))
    bands = heading_bands(measure_size_mass(pages), measure_font_sizes(pages).median_length)
    return bands.size_levels, bands.ceiling
