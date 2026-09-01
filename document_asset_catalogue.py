"""Il catalogo degli asset di un documento: che cosa c'e', dov'e' finito, perche'.

**Questo e' lo stadio che mancava.** La pipeline nuova misurava la ricorrenza
(`document_asset_recurrence_measurements`) e decideva la destinazione
(`document_asset_policy`), ma **non aveva un posto di produzione dove estrarre gli
asset e catalogarli**: quel pezzo viveva solo in `scripts/`, cioe' in
impalcatura. La pipeline legacy ce l'ha (`extractor.AssetIndex` e
`asset_manager.py`); la nuova no. Rilievo dell'utente del 31 agosto 2026.

**Il catalogo e' un contratto, non un CSV.** Il CSV e' una delle sue
serializzazioni e sta altrove: qui c'e' che cosa si sa di ogni contenuto raster
del documento, e chi consuma decide come scriverlo. `AGENTS.MD` §Confini vuole
l'asset fisico distinto dall'occorrenza, dalla regione e dal nodo semantico, e
questo modulo sta sul primo dei quattro.

**Nessun backend qui dentro.** L'estrazione dei byte e' iniettata come funzione,
perche' tirare fuori un raster da un PDF e' lavoro dell'adattatore -- lo fa
`pymupdf_asset_extraction`, che sta allo stesso piano di `pymupdf_capture`. Cosi'
il catalogo si prova senza aprire un PDF, e una sorgente che non sia un PDF non
richiede di riscriverlo.

**Ogni contenuto ha una voce, anche quello che non diventa un file.** E' la
copertura di `AGENTS.MD` §Coverage: «nessuna esclusione puo' essere silenziosa».
Un gradiente che non ha una risorsa da estrarre, o una striscia piu' sottile del
testo, restano **catalogati** con la ragione per cui non hanno un file --
istruzione dell'utente, «non si cancellano le cose, ma si taggano per usi
futuri». I riquadri a sfondo colorato di Fab si ritrovano da qui.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from document_asset_policy import AssetDecision

# (byte, estensione, metodo). Il **metodo** viaggia col file perche' i modi di
# ottenere un raster non sono intercambiabili: la risorsa incorporata, la stessa
# composta con la sua maschera, e la fotografia della regione di pagina sono tre
# cose diverse, e l'ultima non e' l'asset.
ExtractedRaster = tuple[bytes, str, str]

_UNSAFE_FILENAME_CHARACTERS = re.compile(r"[^A-Za-z0-9._-]")


def file_stem_for(digest: str) -> str:
    """Il nome del file viene dal **contenuto**, non dalla pagina.

    Il legacy nomina `p92_img11.jpeg`, cioe' per collocazione, e infatti la
    stessa immagine su due pagine ha due nomi. Qui la chiave e' il digest, che e'
    la stessa cosa che rende la deduplica possibile: un contenuto, un file, un
    nome.
    """

    if not isinstance(digest, str) or not digest:
        raise ValueError("digest must be a non-empty string")
    return _UNSAFE_FILENAME_CHARACTERS.sub("_", digest)


@dataclass(frozen=True, slots=True)
class AssetCatalogueEntry:
    """Un contenuto raster distinto del documento."""

    digest: str
    destination: str
    folder: str | None
    file_name: str | None
    extraction_method: str | None
    page_count: int
    occurrence_count: int
    first_page_index: int
    smallest_placed_extent: float
    has_stored_resource: bool | None
    renders_body_note: bool

    def __post_init__(self) -> None:
        if not isinstance(self.digest, str) or not self.digest:
            raise ValueError("digest must be a non-empty string")
        if not isinstance(self.destination, str) or not self.destination:
            raise ValueError("destination must be a non-empty string")
        if self.folder is None and self.file_name is not None:
            raise ValueError("a file_name needs a folder to live in")
        if self.file_name is None and self.extraction_method is not None:
            raise ValueError("an extraction_method without a file is meaningless")
        if self.renders_body_note and self.file_name is None:
            raise ValueError("a body note must point at a file")
        if self.page_count < 1 or self.occurrence_count < self.page_count:
            raise ValueError("occurrence_count cannot be lower than page_count")


@dataclass(frozen=True, slots=True)
class UncataloguedOccurrence:
    """Un'occorrenza che il catalogo non puo' identificare, e non nasconde."""

    page_index: int
    primitive_id: str
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.primitive_id, str) or not self.primitive_id:
            raise ValueError("primitive_id must be a non-empty string")
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("reason must be a non-empty string")


@dataclass(frozen=True, slots=True)
class AssetCatalogue:
    """Tutto cio' che il documento porta come raster, e dove e' finito."""

    entries: tuple[AssetCatalogueEntry, ...]
    uncatalogued: tuple[UncataloguedOccurrence, ...] = ()

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for entry in self.entries:
            if not isinstance(entry, AssetCatalogueEntry):
                raise ValueError("entries must contain AssetCatalogueEntry values")
            if entry.digest in seen:
                raise ValueError("entries must not repeat a digest")
            seen.add(entry.digest)
        names: set[tuple[str, str]] = set()
        for entry in self.entries:
            if entry.folder is None or entry.file_name is None:
                continue
            key = (entry.folder, entry.file_name)
            if key in names:
                raise ValueError("two entries must not claim the same file")
            names.add(key)

    def by_digest(self, digest: str) -> AssetCatalogueEntry | None:
        for entry in self.entries:
            if entry.digest == digest:
                return entry
        return None

    def digests_with_body_note(self) -> frozenset[str]:
        """La forma che l'emettitore Markdown vuole."""

        return frozenset(e.digest for e in self.entries if e.renders_body_note)

    def stored_files(self) -> tuple[tuple[str, str], ...]:
        """(cartella, nome) di ogni file davvero scritto."""

        return tuple(
            (e.folder, e.file_name)
            for e in self.entries
            if e.folder is not None and e.file_name is not None
        )


def build_asset_catalogue(
    *,
    decisions: Sequence[AssetDecision],
    first_page_index_of: Mapping[str, int],
    extract: Callable[[str], ExtractedRaster | None],
    store: Callable[[str, str, bytes], None],
    uncatalogued: Sequence[UncataloguedOccurrence] = (),
) -> AssetCatalogue:
    """Estrae una volta per contenuto e cataloga tutto, anche cio' che non esce.

    ``extract`` riceve un digest e restituisce il raster, o ``None`` quando non
    c'e' niente da estrarre -- un'occorrenza interamente fuori pagina, per dire.
    ``store`` riceve (cartella, nome, byte) e scrive: il catalogo non sa che cosa
    sia un filesystem.

    **Una estrazione per contenuto, non per occorrenza.** E' la deduplica, ed e'
    la stessa scelta del legacy (`extractor._seen_image_hashes`): la seconda
    collocazione dello stesso digest non riapre niente.
    """

    entries: list[AssetCatalogueEntry] = []
    for decision in decisions:
        if not isinstance(decision, AssetDecision):
            raise ValueError("decisions must contain AssetDecision values")
        folder = decision.folder
        file_name: str | None = None
        method: str | None = None

        if folder is not None:
            extracted = extract(decision.digest)
            if extracted is not None:
                raster, extension, method = extracted
                file_name = f"{file_stem_for(decision.digest)}.{extension}"
                store(folder, file_name, raster)

        entries.append(
            AssetCatalogueEntry(
                digest=decision.digest,
                destination=decision.destination,
                # Una destinazione con cartella che non ha prodotto un file resta
                # senza cartella: il catalogo dice quello che c'e', non quello che
                # si sperava. Succede sulle occorrenze interamente fuori pagina.
                folder=folder if file_name is not None else None,
                file_name=file_name,
                extraction_method=method,
                page_count=decision.page_count,
                occurrence_count=decision.occurrence_count,
                first_page_index=first_page_index_of.get(decision.digest, -1),
                smallest_placed_extent=decision.smallest_placed_extent,
                has_stored_resource=decision.has_stored_resource,
                renders_body_note=decision.renders_body_note and file_name is not None,
            )
        )
    return AssetCatalogue(entries=tuple(entries), uncatalogued=tuple(uncatalogued))
