"""Le combinazioni di campi che un documento usa, e dove le mette.

Misura di documento, nella forma di `measure_size_mass`: si passa sulle pagine
catturate una volta sola e si consegna alla policy, che decide. Qui non si
decide niente.

**La riga e' quella del `source_observation_id`**, come la legge
`page_analysis_column_band` e come la legge il producer delle schede. Non e' la
riga dell'ordine di lettura: quella vuole la catena di lettura e una passata
intera del documento, e le due devono almeno partire dalla stessa nozione di
riga del producer che poi si giudica.

**Si contano solo le coppie che si dichiarano**, cioe' l'etichetta finisce con i
due punti. `label_spans` rileva alternanze di stile, non campi, e su una riga
andata a capo con dentro una parola in grassetto chiama «etichetta» tutto il
testo che la precede: `Criterio_RigheDellaSchedaACapo_v1.md` §5.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from page_analysis_stat_block import source_lines_of_page
from primitive_model import NormalizedPrimitivePage, TextPrimitive
from stat_block_field_lines import position_profile
from stat_block_regions import field_labels, line_facts, normalised_label

Profilo = tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class FieldCombinationMeasurements:
    """Per ogni combinazione di etichette dichiarate che sta su **una riga
    sola**: quante volte il documento la usa, e con quali profili di posizione.

    Il profilo e' lo scostamento di ogni etichetta dal bordo sinistro della
    riga, in larghezze di carattere dell'etichetta: adimensionale, quindi non
    cambia se il manuale e' composto a un corpo diverso."""

    occurrences: Mapping[frozenset[str], int]
    profiles: Mapping[frozenset[str], Mapping[Profilo, int]]


def declared_labels(line: Sequence[TextPrimitive]) -> tuple[str, ...]:
    """Le etichette della riga che si dichiarano tali, normalizzate."""

    return tuple(
        etichetta
        for etichetta in (
            normalised_label(span.text)
            for span in field_labels(line)
            if span.text.strip().endswith(":")
        )
        if etichetta
    )


def measure_field_combinations(
    pages: Sequence[NormalizedPrimitivePage],
) -> FieldCombinationMeasurements:
    """Passa sulle pagine e conta le combinazioni con i loro profili."""

    quante: Counter[frozenset[str]] = Counter()
    profili: dict[frozenset[str], Counter[Profilo]] = {}
    for page in pages:
        for riga in source_lines_of_page(page):
            etichette = frozenset(declared_labels(riga))
            if len(etichette) < 2:
                continue
            fatti = line_facts(riga)
            quante[etichette] += 1
            profili.setdefault(etichette, Counter())[
                position_profile(fatti, etichette)
            ] += 1
    return FieldCombinationMeasurements(occurrences=dict(quante), profiles=dict(profili))
