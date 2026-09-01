"""I numeri di `Criterio_TitoliPerFascia_v1.md`: fasce, corpo per massa, livelli.

Produce le quattro tabelle citate nel criterio:

    --distribuzione   massa per dimensione, e dove cade `min(prose_sizes)`
    --stabilita       moda del documento contro moda delle finestre da 20 pagine
    --livelli         corpo e tre livelli per manuale, con un esempio di testo
    --sensibilita     come cambiano i livelli al variare della larghezza di fascia

Uso::

    ./venv/bin/python scripts/measure_heading_bands.py --pdf-dir . --livelli Dag Fab BoB
"""

from __future__ import annotations

import argparse
import collections
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from prototype_ir2_page import capture_document  # noqa: E402

from document_heading_measurements import measure_font_sizes  # noqa: E402
from document_heading_policy import prose_sizes  # noqa: E402

# I quattro numeri del §2 del criterio, dichiarati scelti a mano.
CORPO_TOLLERANZA = 0.04
TITOLI_TOLLERANZA = 0.06
QUOTA_PAROLE = 0.60
RAPPORTO_RIGA = 0.50
PAGINE_MINIME = 3


@dataclass
class Fascia:
    minimo: float
    massimo: float
    caratteri: int = 0
    pagine: set[int] = field(default_factory=set)
    testi: list[str] = field(default_factory=list)
    righe: list[float] = field(default_factory=list)

    @property
    def etichetta(self) -> str:
        if round(self.minimo, 1) == round(self.massimo, 1):
            return f"{self.massimo:.1f}"
        return f"{self.minimo:.1f}-{self.massimo:.1f}"

    @property
    def quota_parole(self) -> float:
        if not self.testi:
            return 0.0
        return sum(1 for t in self.testi if _e_parola(t)) / len(self.testi)

    @property
    def riga_mediana(self) -> float:
        return statistics.median(self.righe) if self.righe else 0.0

    def esempio(self) -> str:
        return next((t for t in self.testi if _e_parola(t)), self.testi[0] if self.testi else "")


def _e_parola(testo: str) -> bool:
    """Due caratteri e almeno una lettera: cio' che separa una parola da un ornamento."""

    return len(testo) >= 2 and any(c.isalpha() for c in testo)


def raccogli(captured) -> tuple[dict[float, int], dict[float, set[int]], dict[float, list[str]]]:
    caratteri: dict[float, int] = collections.Counter()
    pagine: dict[float, set[int]] = collections.defaultdict(set)
    testi: dict[float, list[str]] = collections.defaultdict(list)
    for indice in sorted(captured.pages):
        for primitiva in captured.pages[indice].text_primitives:
            testo = " ".join(primitiva.text.split())
            if not primitiva.font_size or not testo:
                continue
            dimensione = round(primitiva.font_size, 1)
            caratteri[dimensione] += len(testo)
            pagine[dimensione].add(indice)
            testi[dimensione].append(testo)
    return caratteri, pagine, testi


def accorpa(caratteri, pagine, testi, righe, tolleranza, sopra=None) -> list[Fascia]:
    """Dal piu' grande al piu' piccolo, accorpando cio' che sta entro la tolleranza."""

    fasce: list[Fascia] = []
    for dimensione in sorted(caratteri, reverse=True):
        if sopra is not None and dimensione <= sopra:
            continue
        if fasce and dimensione >= fasce[-1].massimo * (1 - tolleranza):
            fascia = fasce[-1]
            fascia.minimo = min(fascia.minimo, dimensione)
        else:
            fasce.append(Fascia(minimo=dimensione, massimo=dimensione))
            fascia = fasce[-1]
        fascia.caratteri += caratteri[dimensione]
        fascia.pagine |= pagine[dimensione]
        fascia.testi += testi[dimensione]
        if dimensione in righe:
            fascia.righe += [righe[dimensione]] * len(testi[dimensione])
    return fasce


def corpo_e_livelli(captured) -> tuple[Fascia, list[Fascia], list[Fascia]]:
    """Il corpo per massa, le fasce candidate, e le tre che diventano H1-H3."""

    pagine_ordinate = [captured.pages[i] for i in sorted(captured.pages)]
    righe = measure_font_sizes(pagine_ordinate).median_length
    caratteri, pagine, testi = raccogli(captured)
    corpo = max(
        accorpa(caratteri, pagine, testi, righe, CORPO_TOLLERANZA),
        key=lambda f: f.caratteri,
    )
    candidate = [
        fascia
        for fascia in accorpa(
            caratteri, pagine, testi, righe, TITOLI_TOLLERANZA, sopra=corpo.massimo
        )
        if fascia.minimo >= corpo.massimo * (1 + TITOLI_TOLLERANZA)
        and fascia.quota_parole >= QUOTA_PAROLE
        and len(fascia.pagine) >= PAGINE_MINIME
        and (
            fascia.riga_mediana / corpo.riga_mediana if corpo.riga_mediana else 9
        )
        <= RAPPORTO_RIGA
    ]
    return corpo, candidate, candidate[:3]


def _apri(pdf_dir: Path, manuale: str):
    documento = fitz.open(pdf_dir / f"{manuale}.pdf")
    return documento, capture_document(documento)


def distribuzione(pdf_dir: Path, manuali: list[str]) -> None:
    print(f"{'man':<5} {'dim.':>5} {'moda':>6} {'% moda':>7} {'top4 %':>7} "
          f"{'min(prose)':>11} {'massa del min':>14}")
    for manuale in manuali:
        documento, captured = _apri(pdf_dir, manuale)
        caratteri, _, _ = raccogli(captured)
        totale = sum(caratteri.values()) or 1
        prime = collections.Counter(caratteri).most_common(4)
        pagine = [captured.pages[i] for i in sorted(captured.pages)]
        prosa = prose_sizes(measure_font_sizes(pagine))
        minimo = min(prosa) if prosa else None
        print(f"{manuale:<5} {len(caratteri):>5} {prime[0][0]:>6} "
              f"{100 * prime[0][1] / totale:>6.1f}% "
              f"{100 * sum(c for _, c in prime) / totale:>6.1f}% "
              f"{minimo if minimo else '-':>11} "
              f"{100 * caratteri.get(minimo, 0) / totale:>13.3f}%")
        documento.close()


def stabilita(pdf_dir: Path, manuali: list[str], finestra: int = 20) -> None:
    def moda(pagine) -> float | None:
        massa: dict[float, int] = collections.Counter()
        for pagina in pagine:
            for primitiva in pagina.text_primitives:
                if primitiva.font_size:
                    massa[round(primitiva.font_size, 1)] += len(primitiva.text)
        return massa.most_common(1)[0][0] if massa else None

    print(f"{'man':<5} {'moda doc':>9} {'finestre':>9} {'concordi':>9} "
          f"{'valori di min(prose)':>21}")
    for manuale in manuali:
        documento, captured = _apri(pdf_dir, manuale)
        indici = sorted(captured.pages)
        riferimento = moda([captured.pages[i] for i in indici])
        concordi = totale = 0
        minimi: set[float] = set()
        for inizio in range(0, max(0, len(indici) - finestra), finestra):
            blocco = [captured.pages[i] for i in indici[inizio:inizio + finestra]]
            totale += 1
            if moda(blocco) == riferimento:
                concordi += 1
            prosa = prose_sizes(measure_font_sizes(blocco))
            if prosa:
                minimi.add(round(min(prosa), 1))
        print(f"{manuale:<5} {riferimento:>9} {totale:>9} "
              f"{concordi:>6}/{totale:<2} {len(minimi):>21}")
        documento.close()


def livelli(pdf_dir: Path, manuali: list[str]) -> None:
    for manuale in manuali:
        documento, captured = _apri(pdf_dir, manuale)
        corpo, candidate, tre = corpo_e_livelli(captured)
        print(f"\n=== {manuale} — corpo {corpo.etichetta} pt, "
              f"{len(candidate)} fasce candidate ===")
        for numero, fascia in enumerate(tre, start=1):
            print(f"  H{numero}  {fascia.etichetta:>11} pt  "
                  f"{len(fascia.pagine):>4} pag  "
                  f"parole {100 * fascia.quota_parole:>3.0f}%  "
                  f"{fascia.esempio()[:34]!r}")
        for fascia in candidate[3:]:
            print(f"  --  {fascia.etichetta:>11} pt  {len(fascia.pagine):>4} pag  "
                  f"(oltre il tetto) {fascia.esempio()[:28]!r}")
        documento.close()


def sensibilita(pdf_dir: Path, manuali: list[str]) -> None:
    global TITOLI_TOLLERANZA
    originale = TITOLI_TOLLERANZA
    for manuale in manuali:
        documento, captured = _apri(pdf_dir, manuale)
        print(f"\n=== {manuale} ===")
        for tolleranza in (0.02, 0.04, 0.06, 0.08, 0.12, 0.20):
            TITOLI_TOLLERANZA = tolleranza
            corpo, _, tre = corpo_e_livelli(captured)
            celle = "  ".join(
                f"H{n} {f.etichetta:>9}({len(f.pagine):>3}p)"
                for n, f in enumerate(tre, start=1)
            ) or "nessun livello"
            print(f"  toll {tolleranza:>4.0%}  corpo {corpo.etichetta:>11}  {celle}")
        documento.close()
    TITOLI_TOLLERANZA = originale


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--distribuzione", nargs="+", metavar="MAN")
    parser.add_argument("--stabilita", nargs="+", metavar="MAN")
    parser.add_argument("--livelli", nargs="+", metavar="MAN")
    parser.add_argument("--sensibilita", nargs="+", metavar="MAN")
    arguments = parser.parse_args()

    fatto = False
    for nome, funzione in (
        ("distribuzione", distribuzione),
        ("stabilita", stabilita),
        ("livelli", livelli),
        ("sensibilita", sensibilita),
    ):
        manuali = getattr(arguments, nome)
        if manuali:
            funzione(arguments.pdf_dir, manuali)
            fatto = True
    if not fatto:
        parser.print_help()
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
