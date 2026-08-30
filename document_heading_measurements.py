"""Le dimensioni del carattere di un documento, e quanto sono lunghe le loro righe.

`Criterio_Titoli_v2.md` §1. Misura, non decide: quali dimensioni siano prosa e
quali titolo lo stabilisce `document_heading_policy`.

**Perche' la lunghezza delle righe e non il numero di caratteri.** La v1 di quel
criterio assumeva **una** dimensione di corpo per documento, la piu' frequente. E'
falso, e misurato: su Apo idx 76 (pagina stampata 73) il flusso a 10,6 e' il
**95% della pagina**, mentre la dimensione che il documento dichiara corpo (11,6)
quasi non compare. Ci sono due o tre flussi di prosa, non uno.

Cio' che distingue la prosa da un titolo non e' quanto testo c'e' a quella
dimensione, ma **quanto sono lunghe le sue righe**: una riga di prosa che va a
capo e' lunga quanto le altre, un titolo no.

Si contano solo le righe che portano **almeno una lettera o cifra**: su Kul
l'82% delle righe alla dimensione del corpo e' un singolo `.` -- i puntini
decorativi gia' incontrati scrivendo `Criterio_Elenchi_v2.md` -- e una mediana su
quei dati non misura niente.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from statistics import median

from primitive_model import NormalizedPrimitivePage

_OBSERVATION = re.compile(r"^text:(b\d+):(l\d+):s\d+$")


@dataclass(frozen=True, slots=True)
class SizedLine:
    """Una riga sorgente col blocco a cui appartiene, la dimensione e l'estensione.

    `x0`, `x1` e `font` servono al `Criterio_TitoloSopraIlParagrafo_v1.md`, che
    riconosce un titolo **non** dalla dimensione ma dal font che lo governa e da
    dove finisce rispetto al margine del suo blocco. Hanno un valore neutro perche'
    chi misura solo le dimensioni non deve costruirli.
    """

    block: str
    text: str
    size: float
    x0: float = 0.0
    x1: float = 0.0
    font: str | None = None


@dataclass(frozen=True, slots=True)
class FontSizeMeasurements:
    """Per ogni dimensione, quante righe porta e quanto sono lunghe in mediana."""

    line_count: dict[float, int]
    median_length: dict[float, float]

    def __post_init__(self) -> None:
        for name, values in (
            ("line_count", self.line_count),
            ("median_length", self.median_length),
        ):
            for size, value in values.items():
                if size <= 0:
                    raise ValueError(f"{name}: font size must be greater than zero")
                if value < 0:
                    raise ValueError(f"{name}: value cannot be negative")


def sized_lines(page: NormalizedPrimitivePage) -> list[SizedLine]:
    """Le righe sorgente della pagina, ognuna con blocco e dimensione massima.

    La dimensione della riga e' la **massima** delle sue primitive: una riga in
    cui una parola e' piu' grande e' governata da quella, ed e' cosi' che si
    comporta la tipografia.
    """

    grouped: dict[tuple[str, str], list] = defaultdict(list)
    for primitive in page.text_primitives:
        match = _OBSERVATION.match(primitive.source_observation_id or "")
        if match:
            grouped[(match.group(1), match.group(2))].append(primitive)

    lines: list[SizedLine] = []
    for (block, _line), primitives in grouped.items():
        text = "".join(p.text for p in sorted(primitives, key=lambda z: z.bbox[0])).strip()
        sizes = [p.font_size for p in primitives if p.font_size]
        if text and sizes:
            lines.append(
                SizedLine(
                    block=block,
                    text=text,
                    size=round(max(sizes), 1),
                    x0=min(p.bbox[0] for p in primitives),
                    x1=max(p.bbox[2] for p in primitives),
                    font=governing_font(primitives),
                )
            )
    return lines


def governing_font(primitives: Sequence) -> str | None:
    """Il font della **maggioranza dei caratteri**, non della prima primitiva.

    Un paragrafo che comincia con una parola in grassetto e' governato dal font
    del resto -- misurato su Apo idx 79, dove `b0002 l0000` ha un inciso in
    `ArnoPro-Bold` dentro una riga di `ArnoPro-Regular` -- mentre un titolo e'
    scritto tutto nel suo. Prendere la prima primitiva confonderebbe i due.
    """

    weight: dict[str, int] = defaultdict(int)
    for primitive in primitives:
        if primitive.font_name:
            weight[primitive.font_name] += len(primitive.text)
    if not weight:
        return None
    return max(weight.items(), key=lambda item: (item[1], item[0]))[0]


def measure_font_sizes(
    pages: Sequence[NormalizedPrimitivePage],
) -> FontSizeMeasurements:
    """Le due misure per dimensione, su tutte le pagine date."""

    lengths: dict[float, list[int]] = defaultdict(list)
    for page in pages:
        for line in sized_lines(page):
            if any(character.isalnum() for character in line.text):
                lengths[line.size].append(len(line.text))
    return FontSizeMeasurements(
        line_count={size: len(values) for size, values in lengths.items()},
        median_length={size: float(median(values)) for size, values in lengths.items()},
    )
