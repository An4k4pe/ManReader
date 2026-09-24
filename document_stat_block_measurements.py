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

from page_analysis_stat_block import (
    MINIMO_ETICHETTE_PER_BLOCCO,
    blocks_of_field_lines,
    declared_labels,
    source_lines_of_page,
)
from primitive_model import NormalizedPrimitivePage, TextPrimitive
from stat_block_regions import LineFacts, line_facts

Profilo = tuple[tuple[str, int], ...]


def declared_labels_of_facts(facts: LineFacts) -> tuple[str, ...]:
    """Le etichette di una riga gia' misurata che si dichiarano con i due punti."""

    return tuple(
        etichetta
        for etichetta, dichiara in zip(facts.labels, facts.label_declares, strict=True)
        if dichiara
    )


@dataclass(frozen=True, slots=True)
class FieldCombinationMeasurements:
    """Per ogni combinazione di etichette dichiarate che sta su **una riga
    sola**: quante volte il documento la usa, e con quali profili di posizione.

    Il profilo e' lo scostamento di ogni etichetta dal bordo sinistro della
    riga, in larghezze di carattere dell'etichetta: adimensionale, quindi non
    cambia se il manuale e' composto a un corpo diverso."""

    occurrences: Mapping[frozenset[str], int]
    profiles: Mapping[frozenset[str], Mapping[Profilo, int]]


def measure_field_combinations(
    pages: Sequence[NormalizedPrimitivePage],
) -> FieldCombinationMeasurements:
    """Passa sulle pagine e conta le combinazioni con i loro profili."""

    quante: Counter[frozenset[str]] = Counter()
    profili: dict[frozenset[str], Counter[Profilo]] = {}
    for page in pages:
        for blocco in blocks_of_field_lines(source_lines_of_page(page)):
            etichette = frozenset(e for riga in blocco for e in declared_labels(riga))
            if len(etichette) < MINIMO_ETICHETTE_PER_BLOCCO:
                continue
            quante[etichette] += 1
            profili.setdefault(etichette, Counter())[_profilo_del_blocco(blocco)] += 1
    return FieldCombinationMeasurements(occurrences=dict(quante), profiles=dict(profili))


def _profilo_del_blocco(blocco: Sequence[Sequence[TextPrimitive]]) -> Profilo:
    """Dove stanno le etichette del blocco, rispetto al suo bordo sinistro.

    Il profilo di una riga si misurava dal bordo della riga; quello di un blocco
    dal bordo del blocco, perche' e' il blocco l'unita' che si ripete. Resta
    adimensionale: larghezze di carattere dell'etichetta."""

    fatti = [line_facts(riga) for riga in blocco]
    riquadri = [f.bbox for f in fatti if f.bbox is not None]
    if not riquadri:
        return ()
    sinistra = min(b[0] for b in riquadri)
    voci: list[tuple[str, int]] = []
    for f in fatti:
        dichiarate = set(declared_labels_of_facts(f))
        for etichetta, (inizio, larghezza) in zip(f.labels, f.label_starts, strict=True):
            if etichetta in dichiarate and larghezza > 0:
                voci.append((etichetta, round((inizio - sinistra) / larghezza)))
    return tuple(sorted(voci))
