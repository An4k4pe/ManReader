"""Pure recurrence counts of the same image content, across a document's pages.

**Misura, non classificazione.** Dice che un certo contenuto raster compare su N
pagine in M collocazioni, e quanto e' piccola la sua collocazione piu' stretta;
non dice che sia uno sfondo, non toglie niente, e nessuna primitiva viene toccata
-- `AGENTS.MD` §Primitive vuole le primitive immutabili e senza ruoli semantici.
Chi decide la cartella e la nota e' `document_asset_policy`, tardi, dove il
progetto ha gia' ratificato che si decide.

**Perche' document-level, e perche' era l'asse sbagliato prima.** La resa delle
note d'asset era governata da `resolution`, che dice se Resolution ha accettato
un candidato -- e Resolution ha una regola sola, che accetta soltanto un
`interior_visual_frame` gemello di un `embedded_visual`. Ne segue che nel corpo
poteva entrare **solo** un riquadro: misurato sulle dieci pagine del campione,
10 note rese su 10 sono `layout.interior_visual_frame` e nessuna delle 65
trattenute lo e'. Un'illustrazione non poteva essere annunciata per costruzione,
e su Dag idx 199 non lo era: quattro immagini estratte, zero note.

Cio' che separa un'illustrazione da un arredo non e' un fatto della pagina, e'
un fatto del documento -- lo sfondo sta su duecento pagine, l'illustrazione su
una. Stessa firma dell'arredo di testo, e stesso rimedio:
`document_text_recurrence_measurements` misura la ricorrenza di posizione, questo
misura la ricorrenza di contenuto. Misurato sulle 75 note del campione: 52 su una
pagina sola, 1 su due, 22 fra 7 e 358 pagine.

**La chiave e' il contenuto, non la collocazione.** Due bande ai lati della stessa
pagina hanno lo stesso digest e collocazioni diverse: sono lo stesso asset messo
due volte, e la deduplica ne vuole un file solo. Per questo `page_count` e
`occurrence_count` sono due numeri distinti e nessuno dei due si deriva dall'altro.

**L'estensione minore, e perche' e' qui e non nella policy.** Una striscia alta un
punto non raffigura niente: su Fab idx 126 quaranta occorrenze su quarantasei sono
i filetti di separazione delle righe di tabella, uno per cella, alti 1-2 pt contro
una prosa che il documento dichiara a 8,0. Quanto sia piccolo «troppo piccolo» e'
una politica e non sta qui; **quanto e' piccolo** e' una misura e sta qui.

**Precedente nel repo, e va citato perche' e' autorevole**: la pipeline legacy
risolve gia' la deduplica con `extractor._seen_image_hashes` -- MD5 dei byte, la
seconda occorrenza riusa il file della prima -- e scarta le immagini minute con
`config.min_image_width/height = 80` px. `deduplicator.find_repeated_assets` vi
aggiunge il raggruppamento su piu' pagine con soglia 0,15, ma **non e' importato
da nessun modulo**: la cartella `backgrounds/` che documenta non e' mai stata
prodotta. Quel modulo **decide**; questo **misura**. Le sue soglie non sono
riprodotte qui di proposito, ed erano cablate: 80 px e 0,15 non si desumono da
nessun documento, e la regola di sfondo del legacy -- bbox oltre il 60% della
pagina, `extractor.py:3726` -- manca la barra dorata di Dag, larga il 4% della
pagina e presente su 342 pagine su 379.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from primitive_model import NormalizedPrimitivePage


def _validate_int(value: int, field_name: str, *, positive: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if positive and value <= 0:
        raise ValueError(f"{field_name} must be positive")
    if not positive and value < 0:
        raise ValueError(f"{field_name} must be non-negative")


@dataclass(frozen=True, slots=True)
class AssetRecurrence:
    """One image content, and where the document places it."""

    digest: str
    page_count: int
    page_indices: tuple[int, ...]
    occurrence_count: int
    smallest_placed_extent: float
    largest_placed_extent: float
    # Vero se **almeno una** collocazione di questo contenuto ha una risorsa
    # memorizzata: il contenuto esiste da qualche parte e si puo' estrarre. Falso
    # se nessuna ce l'ha. `None` se il backend non lo dichiara.
    has_stored_resource: bool | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.digest, str) or not self.digest:
            raise ValueError("digest must be a non-empty string")
        if self.has_stored_resource is not None and not isinstance(
            self.has_stored_resource, bool
        ):
            raise ValueError("has_stored_resource must be a bool or None")
        _validate_int(self.page_count, "page_count", positive=True)
        _validate_int(self.occurrence_count, "occurrence_count", positive=True)
        if len(self.page_indices) != self.page_count:
            raise ValueError("page_indices must have page_count entries")
        if len(set(self.page_indices)) != len(self.page_indices):
            raise ValueError("page_indices must not repeat")
        if tuple(sorted(self.page_indices)) != self.page_indices:
            raise ValueError("page_indices must be sorted")
        if self.occurrence_count < self.page_count:
            raise ValueError("occurrence_count cannot be lower than page_count")
        for name in ("smallest_placed_extent", "largest_placed_extent"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be a number")
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if self.smallest_placed_extent > self.largest_placed_extent:
            raise ValueError(
                "smallest_placed_extent cannot exceed largest_placed_extent"
            )


@dataclass(frozen=True, slots=True)
class DigestlessOccurrence:
    """One placement whose content the capture could not identify.

    Registrata e non scartata: `AGENTS.MD` §Coverage vuole che nessuna esclusione
    sia silenziosa, e un'occorrenza senza digest non e' deduplicabile ne'
    contabile fra le ricorrenze. Chi consuma decide che farne; qui si dichiara
    soltanto che c'e'.
    """

    page_index: int
    primitive_id: str

    def __post_init__(self) -> None:
        _validate_int(self.page_index, "page_index")
        if not isinstance(self.primitive_id, str) or not self.primitive_id:
            raise ValueError("primitive_id must be a non-empty string")


@dataclass(frozen=True, slots=True)
class DocumentAssetRecurrenceMeasurements:
    """Every distinct image content of a document, with no threshold applied.

    Nessuna soglia: chi consuma sceglie la sua, e cambiarla non richiede di rifare
    la misura. Riportare tutto costa poco -- i contenuti su una pagina sola sono
    la maggioranza, ma escluderli qui sarebbe gia' una decisione.
    """

    page_count: int
    assets: tuple[AssetRecurrence, ...]
    digestless: tuple[DigestlessOccurrence, ...] = ()

    def __post_init__(self) -> None:
        _validate_int(self.page_count, "page_count", positive=True)
        seen: set[str] = set()
        for asset in self.assets:
            if not isinstance(asset, AssetRecurrence):
                raise ValueError("assets must contain AssetRecurrence values")
            if asset.digest in seen:
                raise ValueError("assets must not repeat a digest")
            seen.add(asset.digest)
            if asset.page_count > self.page_count:
                raise ValueError(
                    "an asset cannot occupy more pages than the document has"
                )
        for occurrence in self.digestless:
            if not isinstance(occurrence, DigestlessOccurrence):
                raise ValueError("digestless must contain DigestlessOccurrence values")

    def by_digest(self, digest: str) -> AssetRecurrence | None:
        """The measurement for one content, or None when it was never placed."""

        for asset in self.assets:
            if asset.digest == digest:
                return asset
        return None

    def placed_on_more_than_one_page(self) -> tuple[AssetRecurrence, ...]:
        """I contenuti che il documento ripete.

        Non e' una soglia: e' la lettura letterale di «ripetuto». Una frazione la
        sceglie il chiamante con `placed_on_at_least`.
        """

        return tuple(asset for asset in self.assets if asset.page_count > 1)

    def placed_on_at_least(self, share: float) -> tuple[AssetRecurrence, ...]:
        """I contenuti presenti su almeno una frazione delle pagine.

        Una comodita' per chi consuma, **non una soglia del modulo**: la frazione
        la passa il chiamante e la misura non ne conosce nessuna.
        """

        if not 0.0 < share <= 1.0:
            raise ValueError("share must be in (0, 1]")
        minimum = self.page_count * share
        return tuple(asset for asset in self.assets if asset.page_count >= minimum)


def measure_document_asset_recurrence(
    pages: Sequence[NormalizedPrimitivePage],
) -> DocumentAssetRecurrenceMeasurements:
    """Count which image content the document places, on how many pages.

    L'indice viene **dalla pagina**, non dal chiamante: un documento si misura
    giusto senza che nessuno dichiari nulla, e non c'e' un secondo posto dove
    l'indice possa sbagliarsi.
    """

    if not pages:
        raise ValueError("pages must not be empty")

    page_indices: dict[str, set[int]] = defaultdict(set)
    occurrences: dict[str, int] = defaultdict(int)
    extents: dict[str, list[float]] = defaultdict(list)
    stored: dict[str, list[bool | None]] = defaultdict(list)
    digestless: list[DigestlessOccurrence] = []
    seen_indices: set[int] = set()

    for primitive_page in pages:
        if not isinstance(primitive_page, NormalizedPrimitivePage):
            raise ValueError("pages must carry NormalizedPrimitivePage values")
        page_index = primitive_page.page_index
        if page_index in seen_indices:
            raise ValueError("a page index must not repeat")
        seen_indices.add(page_index)

        for primitive in primitive_page.image_primitives:
            digest = primitive.content_digest
            if digest is None:
                digestless.append(
                    DigestlessOccurrence(
                        page_index=page_index,
                        primitive_id=primitive.primitive_id,
                    )
                )
                continue
            x0, y0, x1, y1 = primitive.bbox
            page_indices[digest].add(page_index)
            occurrences[digest] += 1
            extents[digest].append(min(abs(x1 - x0), abs(y1 - y0)))
            stored[digest].append(primitive.has_stored_resource)

    def _stored_for(digest: str) -> bool | None:
        """Vero se ALMENO UNA collocazione ha una risorsa: allora si estrae.

        Il verso conta. Se lo stesso contenuto compare una volta come immagine
        memorizzata e una volta sintetizzato, il contenuto **esiste** e va preso
        da dove c'e'; il contrario perderebbe un asset vero per via della sua
        seconda collocazione.
        """

        values = stored[digest]
        if any(value is True for value in values):
            return True
        if values and all(value is False for value in values):
            return False
        return None

    assets = tuple(
        AssetRecurrence(
            digest=digest,
            page_count=len(page_indices[digest]),
            page_indices=tuple(sorted(page_indices[digest])),
            occurrence_count=occurrences[digest],
            smallest_placed_extent=min(extents[digest]),
            largest_placed_extent=max(extents[digest]),
            has_stored_resource=_stored_for(digest),
        )
        for digest in sorted(page_indices)
    )
    return DocumentAssetRecurrenceMeasurements(
        page_count=len(pages),
        assets=assets,
        digestless=tuple(digestless),
    )
