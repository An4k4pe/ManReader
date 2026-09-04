"""Il tetto della prosa e i tre livelli, per fascia. `Criterio_TitoliPerFascia_v2.md` §1.

**Politica, non misura**: `document_heading_band_measurements` conta, questo
modulo decide. Sostituisce **l'ancora** di `document_heading_policy.prose_sizes`,
e **non** la regola di riga: `heading_lines` resta identica e continua ad
applicarsi dentro le fasce.

**Che cosa cade dell'ancora vecchia.** `prose_sizes` taglia al salto piu' grande
fra le mediane di lunghezza riga, senza guardare **quanta scrittura** ogni
dimensione porti. Misurato: su Dag `min(prose_sizes)` e' **2,8 pt**, una
dimensione che porta 2011 caratteri su 1.340.284 -- lo **0,15%**. Su sette
manuali su otto l'ancora cade sotto l'1% della massa. E si sposta: facendo
scorrere finestre di 20 pagine, `min(prose_sizes)` assume fino a **8 valori
diversi** sullo stesso manuale, mentre la moda per massa concorda con quella del
documento **90 volte su 101**.

E' il rilievo dell'utente del 1 settembre 2026: «sapere i caratteri di una pagina
ci fa creare dei titoli che non corrispondono a quella di due pagine dopo se le
pagine erano degli outlier». Misurato sull'uscita di Dag prima di questo modulo:
**241 occorrenze di titolo su 2035 -- l'11,8% -- escono a un livello che dipende
dalla pagina**, e 189 di quelle sono la sola stringa `**CARATTERISTICHE**`, h2 su
33 pagine e h3 su 156.

**L'ambito e' il documento, e qui e' una differenza voluta.**
`Criterio_AmbitoDeiFatti_v2.md` tiene arredo, marcatori e scale su una finestra
che **contiene** la pagina, e resta cosi'. Il corpo no: §1 dice «una sola per
documento, calcolata su tutte le pagine», perche' un corpo che cambia fra due
pagine e' esattamente il difetto da correggere.

**I quattro numeri sono scelti a mano**, e il criterio §2 lo dichiara invece di
nasconderlo. Cio' che la sensibilita' mostra e' che fra 4% e 8% gli otto manuali
danno la **stessa** struttura: la zona e' larga, non un punto.
"""

from __future__ import annotations

import statistics
from collections.abc import Mapping
from dataclasses import dataclass, field

from document_heading_band_measurements import SizeMassMeasurements

# I quattro numeri del §2 del criterio. Non sono desunti dal documento: sono
# tarati a mano su otto manuali, ed e' il debito dichiarato di questo criterio.
BODY_TOLERANCE = 0.04
HEADING_TOLERANCE = 0.06
WORD_SHARE = 0.60
LINE_RATIO = 0.50
MIN_PAGES = 3

# La quota della massa del CORPO sotto la quale una dimensione non e' piu' prosa.
# `Criterio_TettoDallaMassa_v1.md` §1. Misurato su otto manuali: da 1,5% a 2,0%
# danno tutti lo stesso tetto; sopra si rompe prima Dag (2,2%), sotto BiD (1,0%).
# 1,8% sta dentro l'altopiano e lontano da entrambi i bordi.
MASS_SHARE = 0.018

# Tre, come `document_heading_policy.MAX_LEVEL`, e per la stessa ragione: e' una
# decisione dell'utente sulla compatibilita' con Markdown e i lettori, non una
# misura. Il costo e' dichiarato: BoB ha **quattro** livelli veri e ne perde uno.
MAX_LEVEL = 3


@dataclass
class Band:
    """Un gruppo di dimensioni vicine, con la massa che portano."""

    minimum: float
    maximum: float
    characters: int = 0
    page_indices: set[int] = field(default_factory=set)
    word_count: int = 0
    text_count: int = 0
    sizes: list[float] = field(default_factory=list)
    _line_lengths: list[float] = field(default_factory=list)

    @property
    def label(self) -> str:
        if round(self.minimum, 1) == round(self.maximum, 1):
            return f"{self.maximum:.1f}"
        return f"{self.minimum:.1f}-{self.maximum:.1f}"

    @property
    def word_share(self) -> float:
        if not self.text_count:
            return 0.0
        return self.word_count / self.text_count

    @property
    def median_line_length(self) -> float:
        """Mediana **pesata sui testi**: ogni dimensione pesa quanto ha scritto.

        Non e' la mediana delle mediane. Una dimensione con quattro righe e una
        con quattromila peserebbero uguale, e la fascia direbbe la forma della
        piu' rara invece che la propria.
        """

        return statistics.median(self._line_lengths) if self._line_lengths else 0.0

    @property
    def page_count(self) -> int:
        return len(self.page_indices)


@dataclass(frozen=True, slots=True)
class HeadingBands:
    """L'esito della regola: il corpo, il tetto della prosa, e le candidate."""

    body: Band | None
    ceiling: float | None
    candidates: tuple[Band, ...]

    @property
    def size_levels(self) -> dict[float, int]:
        """Da dimensione a livello, la forma che `heading_lines` vuole.

        **Ogni** dimensione della fascia riceve **lo stesso** livello, ed e' cio'
        che chiude il difetto C: prima i ranghi si assegnavano a dimensioni
        singole, quindi su Dag `28,0` era h1 e `27,9` era h2 -- due livelli per
        quello che sulla pagina e' un titolo solo.

        **E il tetto a tre ACCORPA, non scarta.** Oltre la terza fascia il titolo
        resta un titolo e diventa `###`. E' il difetto A del §0 della v2: la v1
        contava i **titoli** dove la decisione dell'utente contava i **livelli**,
        e il costo misurato era dal 74% al 97% dei titoli di ogni manuale.
        """

        return {
            size: min(rank, MAX_LEVEL)
            for rank, band in enumerate(self.candidates, start=1)
            for size in band.sizes
        }

    @property
    def bands_by_level(self) -> dict[int, tuple[Band, ...]]:
        """Le fasce raggruppate per livello emesso, per chi riporta l'esito."""

        out: dict[int, list[Band]] = {}
        for rank, band in enumerate(self.candidates, start=1):
            out.setdefault(min(rank, MAX_LEVEL), []).append(band)
        return {level: tuple(bands) for level, bands in out.items()}

    @property
    def prose_anchor(self) -> frozenset[float]:
        """Le dimensioni del corpo, per il guardiano di `heading_lines`.

        La regola di riga usa `prose` solo per sapere se qualcosa e' stato
        misurato; il livello lo legge da `size_levels`. Passargli il corpo e'
        quindi fedele e non cambia la regola.
        """

        return frozenset(self.body.sizes) if self.body else frozenset()


def group_into_bands(
    measurements: SizeMassMeasurements,
    median_length: Mapping[float, float],
    tolerance: float,
    *,
    above: float | None = None,
) -> list[Band]:
    """Dal piu' grande al piu' piccolo, accorpando cio' che sta entro la tolleranza.

    L'accorpamento e' **relativo** al massimo della fascia in corso, non assoluto:
    quattro punti di differenza separano 9 pt da 13 pt e non separano 90 da 94, ed
    e' il verso giusto perche' il rango tipografico si legge in proporzione.
    """

    bands: list[Band] = []
    for size in sorted(measurements.characters, reverse=True):
        if above is not None and size <= above:
            continue
        if bands and size >= bands[-1].maximum * (1 - tolerance):
            band = bands[-1]
            band.minimum = min(band.minimum, size)
        else:
            bands.append(Band(minimum=size, maximum=size))
            band = bands[-1]
        texts = measurements.text_count.get(size, 0)
        band.characters += measurements.characters[size]
        band.page_indices |= measurements.page_indices.get(size, frozenset())
        band.word_count += measurements.word_count.get(size, 0)
        band.text_count += texts
        band.sizes.append(size)
        if size in median_length:
            band._line_lengths += [median_length[size]] * texts
    return bands


def prose_ceiling(
    measurements: SizeMassMeasurements, body: Band, *, share: float = MASS_SHARE
) -> float:
    """Il tetto della prosa, dalla **massa**. `Criterio_TettoDallaMassa_v1.md` §1.

    Una dimensione e' prosa se porta almeno ``share`` della massa in caratteri
    del **corpo**; il tetto e' la piu' grande fra queste, o la cima del corpo se
    e' piu' alta.

    **Perche' la massa e non le mediane di riga.** `prose_sizes` taglia al salto
    piu' grande fra le mediane di lunghezza riga, e non guarda quanto testo ci
    sia. Su Fab restituisce 9,7-9,9 -- **0,54% della massa, 41 righe su
    tredicimila** -- e lascia fuori 10,0 pt, che ne porta l'**86,56%** con 10772
    righe. Il tetto finiva a 10,3, che e' il *pavimento* della prosa, e sopra
    passavano 519 righe a 12,0 pt: `'Questo e' il tuo mondo,'`, cioe' citazioni
    d'apertura.

    Il corpo e' la massa del testo corrente; una dimensione che ne porta una
    frazione confrontabile e' ancora testo corrente. Una che ne porta un
    millesimo e' un titolo **per costruzione**: i titoli sono rari, ed e' cio' che
    li rende titoli.

    **Il taglio cumulativo e' stato provato e scartato**: al 98% Fab da' il tetto
    giusto (12,0) ma BoB salta a 18,0 e FWK a 20,0. Misura la forma della coda,
    non dove finisce la prosa.
    """

    limite = body.characters * share
    return max(
        [size for size, mass in measurements.characters.items() if mass >= limite]
        + [body.maximum]
    )


def heading_bands(
    measurements: SizeMassMeasurements,
    median_length: Mapping[float, float],
) -> HeadingBands:
    """Il tetto della prosa, il corpo per massa, e le fasce che intestano.

    **Il punto fisso: cio' che e' prosa non e' mai un titolo.** Indicazione
    dell'utente del 2 settembre 2026. Il tetto viene da `prose_ceiling`, che lo
    ricava dalla massa; le fasce si formano **sopra** di esso.

    I quattro filtri sono **l'ultima guardia**, non il meccanismo, e ognuno toglie
    una cosa diversa:

    1. **staccata dal tetto** -- il modo di sbagliare deve restare «tace», non
       «etichetta la prosa come titolo»;
    2. **porta parole** -- toglie la decorazione, che si riconosce dai caratteri
       singoli: `'y'` a 172 pt su Fab, `'2'`/`'3'`/`'4'` a 292 pt su BiD;
    3. **righe corte** -- sulla **mediana della fascia**, che e' una tendenza. Il
       limite sulla singola riga sta in `heading_lines`, ed e' un'altra domanda;
    4. **almeno tre pagine** -- una fascia che compare una volta non e' un rango,
       ed e' cio' che impedisce a `h1` di finire sul titolo del manuale usato una
       volta sola. Misurato: `h1` cade su fasce da 26 pagine su Dag, 18 su Fab,
       15 su BiD.

    **Senza testo misurato il meccanismo tace**, che e' il verso giusto quando
    l'alternativa e' promuovere prosa.
    """

    if not measurements.characters:
        return HeadingBands(body=None, ceiling=None, candidates=())

    body = max(
        group_into_bands(measurements, median_length, BODY_TOLERANCE),
        key=lambda band: band.characters,
    )
    ceiling = prose_ceiling(measurements, body)
    body_line = body.median_line_length
    candidates = tuple(
        band
        for band in group_into_bands(
            measurements, median_length, HEADING_TOLERANCE, above=ceiling
        )
        if band.minimum >= ceiling * (1 + HEADING_TOLERANCE)
        and band.word_share >= WORD_SHARE
        and band.page_count >= MIN_PAGES
        # Senza un corpo misurabile il rapporto non si puo' calcolare: il filtro
        # tace invece di inventare.
        and (band.median_line_length / body_line if body_line else 9.0) <= LINE_RATIO
    )
    return HeadingBands(body=body, ceiling=ceiling, candidates=candidates)
