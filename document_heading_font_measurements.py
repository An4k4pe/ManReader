"""Le facce di carattere sotto il tetto della prosa, misurate e basta.

**IL MECCANISMO E' CADUTO E QUESTO MODULO NON E' COLLEGATO.**
`Esito_TitoliDalFont_v2.md`: il veto delle schede cade con 29 righe su Wil idx
148 (`'[D] <= 4'`, `'Mostri: hutangwa, kala-kala...'`), la filigrana di Fab passa
su 362 pagine, e il volume e' fuori scala -- 5871 righe promosse su Dag contro un
bersaglio di 1900.

**La diagnosi, che e' il motivo per cui resta in albero.** Sotto il tetto della
prosa, «non e' prosa di corpo» e' una popolazione enorme: numeri di pagina,
didascalie, etichette, voci d'indice, celle di scheda, filigrane. Il compositore
usa **le stesse facce** per tutte, perche' fanno lo stesso mestiere tipografico --
stare fuori dal flusso. Quindi il font distingue il **flusso dal non-flusso** e
non distingue le parti del non-flusso **fra loro**: su Dag `PANORAMICA` e `220`
sono entrambe in `EvelethCleanRegular`, ed e' corretto che lo siano.

Chi affrontera' le schede riparte da qui, perche' quel meccanismo dovra'
distinguere proprio dentro il non-flusso.

**Misura, non politica.** Conta le righe composte **interamente** in un font solo,
sotto il tetto della prosa, e riporta quante sono, quante portano parole, quanto
sono lunghe e su quante pagine compaiono. Non decide che cosa sia un titolo: lo
decide `document_heading_font_policy` con i filtri di
`Criterio_TitoliDalFont_v2.md` §1.

**Perche' la riga e non la primitiva.** Nella prosa il grassetto sta **dentro** la
riga -- `**Vali Quanto la Tua Parola:**` apre un paragrafo e non e' un titolo.
Contare le primitive misurerebbe l'enfasi, che e' un'altra cosa.

**E il font della riga e' quello GOVERNANTE**, cioe' della maggioranza dei
caratteri (`document_heading_measurements.governing_font`), non l'unanimita':
l'unanimita' e' fragile a un glifo solo -- un punto elenco, un simbolo dentro un
titolo omogeneo -- mentre la prosa con l'enfasi dentro resta governata dalla
faccia di prosa, che e' il fine del vincolo.
"""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from dataclasses import dataclass, field

from document_heading_band_measurements import is_word
from document_heading_measurements import SizedLine

SAMPLE_TEXTS_PER_FONT = 3


@dataclass(frozen=True, slots=True)
class FontMassMeasurements:
    """Per font: righe, parole, lunghezze, pagine, e qualche testo d'esempio."""

    line_count: dict[str, int] = field(default_factory=dict)
    word_count: dict[str, int] = field(default_factory=dict)
    median_line_length: dict[str, float] = field(default_factory=dict)
    page_indices: dict[str, frozenset[int]] = field(default_factory=dict)
    sample_texts: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def word_share(self, font: str) -> float:
        """La quota di testi che sono parole. Zero se il font non e' stato visto."""

        total = self.line_count.get(font, 0)
        return self.word_count.get(font, 0) / total if total else 0.0


def measure_font_lines(
    pages: Sequence[Sequence[SizedLine]],
    *,
    ceiling: float | None,
) -> FontMassMeasurements:
    """Le righe a font unico sotto ``ceiling``, una sequenza di righe per pagina.

    ``ceiling`` e' il tetto della prosa: sopra di esso i titoli li trova gia'
    l'asse della dimensione, e misurarli qui li conterebbe due volte. Quando e'
    ``None`` la misura e' vuota, che e' lo stesso verso in cui tace il tetto.
    """

    if ceiling is None:
        return FontMassMeasurements()

    lengths: dict[str, list[int]] = {}
    words: dict[str, int] = {}
    pages_by_font: dict[str, set[int]] = {}
    samples: dict[str, list[str]] = {}
    for index, lines in enumerate(pages):
        for line in lines:
            text = " ".join(line.text.split())
            if not text or not line.font or line.size > ceiling:
                continue
            lengths.setdefault(line.font, []).append(len(text))
            pages_by_font.setdefault(line.font, set()).add(index)
            if is_word(text):
                words[line.font] = words.get(line.font, 0) + 1
                shown = samples.setdefault(line.font, [])
                if len(shown) < SAMPLE_TEXTS_PER_FONT:
                    shown.append(text)
    return FontMassMeasurements(
        line_count={font: len(values) for font, values in lengths.items()},
        word_count=dict(words),
        median_line_length={
            font: float(statistics.median(values)) for font, values in lengths.items()
        },
        page_indices={
            font: frozenset(indices) for font, indices in pages_by_font.items()
        },
        sample_texts={font: tuple(shown) for font, shown in samples.items()},
    )
