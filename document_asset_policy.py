"""Dove va ogni asset estratto, e quale di essi lascia una nota nel corpo.

**Politica, non misura.** `document_asset_recurrence_measurements` osserva e non
decide; questo modulo decide, e sta separato per quello. Non tocca primitive, non
scrive niente su un nodo, non introduce nessun `kind`: restituisce **destinazioni
per digest**, e chi estrae e chi rende decidono che farne.

Quattro destinazioni, e nessuna soglia cablata.

**`NO_STORED_RESOURCE` -- non c'e' niente da estrarre.** La sorgente non conserva
un raster per questa collocazione: `page.get_image_info()` non legge le risorse
del PDF, fa percorrere la pagina al renderer e registra **anche i raster che il
renderer sintetizza** da contenuto che immagine non e'. Misurato sul corpus il 31
agosto 2026, **19168 collocazioni su 39727 -- il 48%** -- sono cosi'; su Fab il
91% (riempimenti a gradiente, `PatternType 2, ShadingType 2`), su DB il 48%
(maschere morbide di `ExtGState`: 153 voci `/SMask` = 153 collocazioni). Operatori
di immagine inline nel corpus: **zero**.

Niente file e niente nota, perche' il file sarebbe una fotografia della regione di
pagina col testo dentro -- misurato: su dodici campioni di Fab, dodici sono
screenshot di paragrafi e tabelle del manuale.

**Ma la primitiva resta, e la riga resta nell'indice**, ed e' il punto: un
rettangolo con lo sfondo a gradiente **non e' rumore**, e' l'indizio tipografico
di un callout o di una regione di tabella -- i due riquadri `322x129` e `322x118`
di Fab idx 126 sono i fondi colorati delle sue tabelle, e
`interior_visual_frame` li propone gia' come riquadri. Toglierli alla cattura li
toglierebbe anche a lui e a qualunque futuro producer di callout, che sono i posti
dove quel gradiente e' **il segnale**. Istruzione dell'utente del 31 agosto 2026:
«non si cancellano le cose, ma si taggano per usi futuri, tipo i box con sfondo
colorato di fab».

**`CONTENT` -- il contenuto.** Un raster che il documento colloca su **una pagina
sola**. E' l'illustrazione: va nella cartella delle immagini e **lascia una nota
nel corpo**, che e' meta' dell'obiettivo di `AGENTS.MD` §Obiettivo.

**`RECURRING` -- l'arredo.** Un raster che il documento colloca su piu' di una
pagina: sfondi, bordi, barre di piede, linguette di capitolo. Va nella sua
cartella, **una volta sola**, e non lascia niente nel corpo. Decisione dell'utente
del 31 agosto 2026, che risolve una tensione reale: §Obiettivo chiede note anche
per «sfondi ed elementi ripetuti», ma il giudizio delle dieci pagine dice di BoB
idx 297 «il riferimento alla banda laterale non serve che sia visualizzato». La
lettura che tiene entrambe: l'elemento resta **tracciato** -- cartella e indice
dicono che c'era e su quante pagine -- e non entra nel flusso di lettura.

Il confine e' `page_count > 1`, che non e' una soglia tarata ma la lettura
letterale di «ripetuto». Sulle 75 note del campione la distribuzione lo giustifica
da sola: 52 contenuti su una pagina, 1 su due, 22 fra 7 e 358.

**`BELOW_TEXT_SCALE` -- cio' che non raffigura niente.** Un raster la cui
collocazione piu' stretta e' piu' sottile della lettera piu' piccola che il
documento stampa. Non ha un file e non ha una nota, ma **e' nell'indice**:
`AGENTS.MD` §Coverage vuole che nessuna esclusione sia silenziosa.

La scala viene dal documento -- `document_heading_policy.prose_sizes` -- e non da
una costante. E' il rimpiazzo di `config.min_image_width/height = 80` px del
legacy, che e' cablato e per giunta in pixel intrinseci invece che in punti
collocati. Misurato su Fab idx 126: quaranta occorrenze su quarantasei sono i
filetti di separazione delle righe di due tabelle, uno per cella, alti 1-2 pt
contro una prosa che il documento dichiara a 8,0.

**L'ordine dei rami conta, ed e' dichiarato**, dal fatto piu' duro al piu'
inferito: prima la risorsa memorizzata, che e' una constatazione del backend; poi
la scala tipografica, che il documento dichiara; poi la ricorrenza. Un filetto
ripetuto su venti pagine e' un filetto, non un arredo da inventariare come
sfondo, e mescolarlo alle bande di pagina sporcherebbe la cartella che l'utente ha
chiesto di tenere pulita.

**Cio' che questo modulo non decide.** Non decide il *testo* della nota -- lo
compone `ir2_markdown.render_asset_note` -- e non sa nulla di
`proposed_structural_kind` ne' di `resolution`. Quest'ultimo era l'asse su cui il
cancello precedente era scritto, e non poteva funzionare: Resolution ha una regola
sola, che accetta soltanto un `interior_visual_frame` gemello di un
`embedded_visual`, quindi nel corpo poteva entrare solo un riquadro. Sulle dieci
pagine del campione, 10 note rese su 10 sono riquadri e nessuna delle 65
trattenute lo e'.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from document_asset_recurrence_measurements import (
    DocumentAssetRecurrenceMeasurements,
)

CONTENT = "content"
RECURRING = "recurring"
BELOW_TEXT_SCALE = "below_text_scale"
NO_STORED_RESOURCE = "no_stored_resource"

AssetDestination = Literal[
    "content", "recurring", "below_text_scale", "no_stored_resource"
]

# I nomi delle due cartelle. Stanno qui e non nello script perche' sono parte
# della decisione -- «uno per le immagini, uno per le immagini di asset, quindi
# le ripetute» -- e non un dettaglio di invocazione. `images/` conserva il nome
# che la pipeline legacy usa gia' (`extractor.py` §Struttura cartelle).
FOLDER_OF_DESTINATION: Mapping[str, str | None] = {
    CONTENT: "images",
    RECURRING: "assets",
    BELOW_TEXT_SCALE: None,
    NO_STORED_RESOURCE: None,
}


@dataclass(frozen=True, slots=True)
class AssetDecision:
    """Che cosa il documento fa di un contenuto raster."""

    digest: str
    destination: AssetDestination
    page_count: int
    occurrence_count: int
    smallest_placed_extent: float
    text_scale: float | None
    has_stored_resource: bool | None = None

    @property
    def folder(self) -> str | None:
        """La cartella in cui scrivere il file, o None se non va scritto."""

        return FOLDER_OF_DESTINATION[self.destination]

    @property
    def renders_body_note(self) -> bool:
        """Se questo contenuto lascia una nota nel flusso di lettura."""

        return self.destination == CONTENT


def decide_document_assets(
    measurements: DocumentAssetRecurrenceMeasurements,
    *,
    text_scale: float | None,
) -> tuple[AssetDecision, ...]:
    """Una decisione per contenuto distinto, nell'ordine della misura.

    ``text_scale`` e' la dimensione della lettera piu' piccola che il documento
    stampa, tipicamente ``min(prose_sizes)``. **Quando e' None il ramo tace**: un
    documento su cui la scala non e' stata misurata non ha con che confrontare, e
    scartare per una scala inventata sarebbe perdita di contenuto travestita da
    politica. E' lo stesso verso in cui sbaglia `document_furniture_policy`, dove
    il ramo 1 non rimuove niente sui manuali che non dichiarano l'etichetta.
    """

    if not isinstance(measurements, DocumentAssetRecurrenceMeasurements):
        raise ValueError(
            "measurements must be a DocumentAssetRecurrenceMeasurements"
        )
    if text_scale is not None:
        if isinstance(text_scale, bool) or not isinstance(text_scale, (int, float)):
            raise ValueError("text_scale must be a number or None")
        if text_scale <= 0:
            raise ValueError("text_scale must be positive")

    decisions: list[AssetDecision] = []
    for asset in measurements.assets:
        if asset.has_stored_resource is False:
            destination: AssetDestination = NO_STORED_RESOURCE
        elif text_scale is not None and asset.smallest_placed_extent < text_scale:
            destination = BELOW_TEXT_SCALE
        elif asset.page_count > 1:
            destination = RECURRING
        else:
            destination = CONTENT
        decisions.append(
            AssetDecision(
                digest=asset.digest,
                destination=destination,
                page_count=asset.page_count,
                occurrence_count=asset.occurrence_count,
                smallest_placed_extent=asset.smallest_placed_extent,
                text_scale=text_scale,
                has_stored_resource=asset.has_stored_resource,
            )
        )
    return tuple(decisions)


def digests_with_body_note(
    decisions: tuple[AssetDecision, ...],
) -> frozenset[str]:
    """I contenuti che lasciano una nota nel corpo.

    E' la forma che il consumer di resa vuole: un insieme di digest, non un
    giudizio su un nodo. Sta a `ir2_markdown.is_rendered_in_body` la stessa
    relazione che `document_furniture_policy.furniture_node_ids` ha con
    ``excluded_node_ids`` -- una politica che il chiamante calcola, non un marchio
    scritto sul contratto.
    """

    return frozenset(
        decision.digest for decision in decisions if decision.renders_body_note
    )


def decisions_by_digest(
    decisions: tuple[AssetDecision, ...],
) -> Mapping[str, AssetDecision]:
    """Le decisioni indicizzate per digest, per chi estrae i file."""

    return {decision.digest: decision for decision in decisions}
