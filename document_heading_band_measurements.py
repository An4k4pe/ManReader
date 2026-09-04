"""Massa, pagine e forma delle righe per ogni dimensione. `Criterio_TitoliPerFascia_v1.md`.

**Misura, non politica.** Qui non si decide che cosa e' corpo e che cosa e'
titolo: si contano i caratteri che ogni dimensione porta, su quante pagine
compare, quanti dei suoi testi sono parole e quanto sono lunghe le sue righe.
`document_heading_band_policy` decide.

**Perche' una misura nuova e non un campo in piu' su `FontSizeMeasurements`.**
Quella misura conta **righe** e ne misura la lunghezza mediana; questa conta
**caratteri** e li attribuisce alle pagine. Sono due popolazioni diverse -- riga
contro primitiva -- e i numeri del criterio sono stati presi cosi'. Fonderle
cambierebbe di nascosto la popolazione su cui il criterio e' stato dichiarato,
che e' esattamente l'errore che `CLAUDE.md` chiama «tracciare la popolazione
sull'asse sbagliato».

La lunghezza mediana di riga **non** si rimisura qui: si riusa
`FontSizeMeasurements.median_length`, perche' e' la stessa grandezza e averne due
definizioni sarebbe un modo per farle divergere.
"""

from __future__ import annotations

import collections
from collections.abc import Sequence
from dataclasses import dataclass

from primitive_model import NormalizedPrimitivePage

# Quanti testi d'esempio si conservano per dimensione. Servono a chi legge
# l'esito del criterio -- §4.B chiede un giudizio riga per riga -- e non entrano
# in nessuna decisione. Il tetto evita di trascinarsi dietro un manuale intero.
SAMPLE_TEXTS_PER_SIZE = 8


def is_word(text: str) -> bool:
    """Due caratteri e almeno una lettera: cio' che separa una parola da un ornamento.

    E' il filtro 2 del §1 del criterio, e sta qui perche' e' una constatazione sul
    testo, non una scelta. Cio' che toglie e' misurato: su Fab `'y'` a 172 pt e
    `'W'` su 358 pagine, su BiD `'2'`, `'3'`, `'4'` a 292 pt, su Dag `'••'` a 24 pt.
    """

    return len(text) >= 2 and any(character.isalpha() for character in text)


@dataclass(frozen=True, slots=True)
class SizeMassMeasurements:
    """Quanto testo porta ogni dimensione, e di che forma."""

    characters: dict[float, int]
    page_indices: dict[float, frozenset[int]]
    word_count: dict[float, int]
    text_count: dict[float, int]
    sample_texts: dict[float, tuple[str, ...]]

    @property
    def total_characters(self) -> int:
        return sum(self.characters.values())


def measure_size_mass(
    pages: Sequence[NormalizedPrimitivePage],
    *,
    excluded_primitive_ids: Sequence[frozenset[str]] | None = None,
) -> SizeMassMeasurements:
    """Una passata sulle primitive di testo, arrotondando le dimensioni al decimo.

    L'arrotondamento non e' una soglia: e' la precisione con cui il backend
    riporta il corpo del font, ed e' lo stesso `round(..., 1)` che
    `document_heading_measurements.sized_lines` usa gia'.

    ``excluded_primitive_ids`` toglie dal **voto** -- numeratore e denominatore
    della quota di parole -- le primitive che non potrebbero comunque diventare
    titoli, **una frozenset per pagina, nell'ordine di `pages`**: gli id di
    primitiva non sono unici fra pagine.

    **Il parametro c'e', ma oggi nessuno lo riempie, ed e' un debito dichiarato.**
    Il meccanismo A di `Criterio_Capolettera_v1.md` voleva passargli l'arredo, ed
    e' **caduto**: l'arredo e' un fatto di **finestra**, e chiamarlo sull'intero
    documento restituisce zero slot su tutti i rami -- misurato su Wil, 316
    pagine: etichetta 0, ricorrenza 0, sequenza 0, testo ripetuto 0, testatine 0,
    **0 primitive escluse su 217 numeri a 19,8-21,0 pt**. E' l'errore contro cui
    `Criterio_AmbitoDeiFatti_v2.md` mette in guardia: la finestra dei fatti si
    **sposta**, non si allarga. Chi vorra' riprendere il meccanismo deve
    raccogliere l'arredo **finestra per finestra** e aggregarlo per pagina.

    **Scartare i testi di un carattere e' caduto con lui**, e la misura dice
    perche' non si adotta da solo: su Wil porta la fascia dei nomi di insediamento
    dal 33% al **52%**, sotto la soglia del 60% che serviva a sbloccarla, e
    intanto su Fab alza sopra soglia le fasce di **prosa da display** -- 88 titoli
    diventano 631, con dentro un paragrafo di 314 caratteri. La quota di parole
    proteggeva anche da quelle, e i capolettera erano parte di cio' che la teneva
    bassa.

    **La massa in caratteri non cambia** comunque: le esclusioni valgono per la
    quota di parole e per il conteggio dei testi, non per `characters`, che serve
    a trovare il corpo e deve vedere tutto il testo del documento.
    """

    characters: dict[float, int] = collections.Counter()
    page_indices: dict[float, set[int]] = collections.defaultdict(set)
    word_count: dict[float, int] = collections.Counter()
    text_count: dict[float, int] = collections.Counter()
    samples: dict[float, list[str]] = collections.defaultdict(list)

    for index, page in enumerate(pages):
        escluse: frozenset[str] = frozenset()
        if excluded_primitive_ids is not None and index < len(excluded_primitive_ids):
            escluse = excluded_primitive_ids[index]
        for primitive in page.text_primitives:
            text = " ".join(primitive.text.split())
            if not primitive.font_size or not text:
                continue
            size = round(primitive.font_size, 1)
            characters[size] += len(text)
            page_indices[size].add(index)
            # Da qui in giu' vota solo chi potrebbe diventare un titolo.
            if primitive.primitive_id in escluse:
                continue
            text_count[size] += 1
            if is_word(text):
                word_count[size] += 1
                if len(samples[size]) < SAMPLE_TEXTS_PER_SIZE:
                    samples[size].append(text)

    return SizeMassMeasurements(
        characters=dict(characters),
        page_indices={size: frozenset(v) for size, v in page_indices.items()},
        word_count=dict(word_count),
        text_count=dict(text_count),
        sample_texts={size: tuple(v) for size, v in samples.items()},
    )
