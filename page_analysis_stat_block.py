"""Producer delle schede: i blocchi di righe che portano campi, pagina per pagina.

**Che cosa propone.** Una scheda e' un blocco di righe che portano **campi**:
`Ferocia: 3   Taglia: Enorme`, `Movimento: 24   Armatura: 6   PF: 84`,
`Difficolta': 14 | Soglie: 9/18 | PF: 5 | Stress: 3`. La regola e' quella che il
modulo delle schede si e' dato per primo e che `State.md:903` scrive alla lettera
(«campi etichetta:valore da preservare»): **almeno due coppie etichetta/valore
in un blocco di righe**, una per riga se e' cosi' che il manuale le scrive.

**Perche' il producer non puo' fare di piu'.** Un producer riceve una pagina e
basta: non vede le altre pagine e non vede i candidati degli altri producer. Le
due cose che sappiamo separare bene una scheda da una tabella non stanno qui:

- la **ripetizione** — quali combinazioni di etichette il documento usa davvero,
  e se le mette sempre nello stesso posto — e' un fatto di documento, e vive in
  una policy che si calcola una volta sola, come `heading_bands`;
- il **riquadro disegnato** e' un candidato di `interior_visual_frame` o di
  `embedded_visual`, e a vedere i candidati altrui e' il consumer.

Quindi questo producer **propone in eccesso**, ed e' il suo mestiere: «un
candidato non e' un fatto di impaginato approvato, ne' una rivendicazione di
proprieta', ne' una decisione». Prendera' anche box di regole e scatole di
trappole; il consumer li scarta.

**L'etichetta deve dichiararsi.** `label_spans` rileva alternanze di stile, non
campi: su una riga andata a capo con dentro una parola in grassetto chiama
«etichetta» tutto il testo che la precede. Chi si appoggia alla ripetizione ne e'
protetto — un'etichetta inventata cosi' non si ripete — ma qui, pagina per
pagina, quella protezione non c'e'. Si contano quindi solo le coppie la cui
etichetta finisce con i due punti: `Criterio_RigheDellaSchedaACapo_v1.md` §5.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from geometry_model import BBox
from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionCandidate,
)
from page_analysis_validate import validate_page_analysis_against_primitive_page
from primitive_model import NormalizedPrimitivePage, TextPrimitive
from stat_block_regions import field_labels, normalised_label

_OBSERVATION_ID_PATTERN = re.compile(r"^text:b(\d+):l(\d+):s(\d+)$")

# **Una coppia dichiarata basta a fare una riga di campi**, ma il blocco deve
# dichiarare almeno due etichette DISTINTE: `Criterio_UnaCoppiaPerRiga_v2.md`,
# indicazione dell'utente — «una scheda e' fatta da una struttura che ripete, e
# nella tabella armi questo non c'e'».
#
# «Almeno due coppie» non sparisce: si sposta dalla riga al blocco. E' la
# differenza fra `Sentieri:` / `Mostri:` / `Umani:` — tre righe, un campo
# ciascuna, una struttura — e `Versatile:` dentro una cella della tabella delle
# armi, che e' un blocco di uno. Misurato: la regola vecchia scartava tutte e tre
# le righe di Wilder, e 1.349 righe su sei manuali mai toccati ne dichiarano una.
_MINIMO_COPPIE_PER_RIGA = 1
MINIMO_ETICHETTE_PER_BLOCCO = 2

# **Una riga sola basta**, `Criterio_SchedaDaUnaRigaSola_v1.md`. Il minimo di due
# righe era una seconda guardia nel posto sbagliato: chiedeva al producer di
# distinguere una scheda da una tabella, che e' cio' che il producer non puo'
# fare — la ripetizione nel documento non si vede da una pagina sola. A
# scartare le proposte sbagliate e' il consumer. Misurato: i colossi di
# Daggerheart dichiarano `Soglie: 11/22 | Stress: 6` su una riga che nella
# pagina sta da sola, e il minimo le faceva sparire.
#
# Non e' la regola «una **coppia** per riga», che l'utente ha rifiutato l'11
# settembre: la riga deve portarne due come prima.
_MINIMO_RIGHE_PER_SCHEDA = 1

# Due righe di campi separate da piu' di questo non sono la stessa scheda. E' il
# raggruppamento gia' misurato in `stat_block_field_lines.field_line_groups`: fra
# `Ferocia` e `Movimento` c'e' in mezzo il nome del tratto, fra due schede
# diverse ci sono molte righe.
_SALTO_MASSIMO = 2


def source_lines_of_page(page: NormalizedPrimitivePage) -> list[list[TextPrimitive]]:
    """Le primitive raggruppate nella riga di sorgente che le porta.

    Il blocco e la riga stanno in `source_observation_id`, come li legge gia'
    `page_analysis_column_band`. Una primitiva con un id che non riconosciamo
    non forma riga: non e' il posto per indovinarlo."""

    gruppi: dict[tuple[int, int], list[tuple[int, TextPrimitive]]] = {}
    for primitive in page.text_primitives:
        match = _OBSERVATION_ID_PATTERN.match(primitive.source_observation_id)
        if match is None:
            continue
        chiave = (int(match.group(1)), int(match.group(2)))
        gruppi.setdefault(chiave, []).append((int(match.group(3)), primitive))
    return [
        [primitive for _indice, primitive in sorted(gruppi[chiave], key=lambda p: p[0])]
        for chiave in sorted(gruppi)
    ]


def declared_labels(line: Sequence[TextPrimitive]) -> tuple[str, ...]:
    """Le etichette della riga che si dichiarano tali, normalizzate.

    Sta qui, nel livello piu' basso, perche' la serve anche la misura di
    documento: `page_analysis_stat_block` non puo' importare da chi lo importa."""

    return tuple(
        etichetta
        for etichetta in (
            normalised_label(span.text)
            for span in field_labels(line)
            if span.text.strip().endswith(":")
        )
        if etichetta
    )


def declared_field_pairs(line: Sequence[TextPrimitive]) -> int:
    """Quante coppie etichetta/valore la riga dichiara con i due punti."""

    return sum(1 for span in field_labels(line) if span.text.strip().endswith(":"))


def _bbox_of(righe: Sequence[Sequence[TextPrimitive]]) -> BBox | None:
    spans = [p for riga in righe for p in riga if p.text.strip()]
    if not spans:
        return None
    return (
        min(p.bbox[0] for p in spans),
        min(p.bbox[1] for p in spans),
        max(p.bbox[2] for p in spans),
        max(p.bbox[3] for p in spans),
    )


def blocks_of_field_lines(
    righe: Sequence[Sequence[TextPrimitive]],
) -> list[list[Sequence[TextPrimitive]]]:
    """I blocchi di righe di campi della pagina: **l'unita' che si ripete**.

    Un blocco e' una corsa di righe consecutive che dichiarano almeno un campo,
    e deve dichiarare almeno due etichette distinte in tutto. La serve anche la
    misura di documento, che conta le strutture che il documento ripete."""

    return [[righe[i] for i in gruppo] for gruppo in _groups_of_field_lines(righe)]


def _groups_of_field_lines(righe: Sequence[Sequence[TextPrimitive]]) -> list[list[int]]:
    con_campi = [
        indice
        for indice, riga in enumerate(righe)
        if declared_field_pairs(riga) >= _MINIMO_COPPIE_PER_RIGA
    ]
    gruppi: list[list[int]] = []
    for indice in con_campi:
        if gruppi and indice - gruppi[-1][-1] <= _SALTO_MASSIMO:
            gruppi[-1].append(indice)
        else:
            gruppi.append([indice])
    return [
        g
        for g in gruppi
        if len(g) >= _MINIMO_RIGHE_PER_SCHEDA
        and len({e for i in g for e in declared_labels(righe[i])})
        >= MINIMO_ETICHETTE_PER_BLOCCO
    ]


def build_stat_block_page_analysis(
    primitive_page: NormalizedPrimitivePage, *, generation_id: str
) -> PageAnalysis:
    """Proponi le schede di una pagina, senza aprire file e senza persistere."""

    righe = source_lines_of_page(primitive_page)
    candidates: list[RegionCandidate] = []
    for numero, gruppo in enumerate(_groups_of_field_lines(righe)):
        # Il gruppo va dalla prima all'ultima riga di campi, quelle in mezzo
        # comprese: dentro una scheda fra due campi c'e' il nome di un tratto,
        # e lasciarlo fuori spezzerebbe la scheda in due.
        del_gruppo = righe[gruppo[0] : gruppo[-1] + 1]
        bbox = _bbox_of(del_gruppo)
        if bbox is None or bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
            continue
        candidates.append(
            RegionCandidate(
                candidate_id=f"candidate:stat_block:fields:{numero:04d}",
                page_id=primitive_page.page_id,
                bbox=bbox,
                proposed_structural_kind="layout.stat_block",
                primitive_ids=tuple(
                    primitive.primitive_id for riga in del_gruppo for primitive in riga
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
            producer_name="page_analysis.stat_block",
            producer_version="0.1",
            configuration_id="stat_block:declared_field_pairs:v1",
        ),
        regions=(),
        relations=(),
        candidates=tuple(candidates),
    )
    validate_page_analysis_against_primitive_page(analysis, primitive_page)
    return analysis
