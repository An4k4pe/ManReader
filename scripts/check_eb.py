"""La barra E-B: l'ordine emesso contro la base, sulle dieci pagine dichiarate.

`Criterio_UscitaIR2Minima_v2.md` §2 — *l'ordine emesso da IR 2 deve essere
identico alla base* — reso eseguibile in un comando solo.

**Perche' esiste.** Fino a oggi E-B era un flag opzionale su una pagina alla
volta, e la base andava rigenerata a mano con un secondo script. Fra Milestone 38
e il 30 agosto 2026 **tre meccanismi di fila** -- gli elenchi, i titoli, i run --
lo hanno rotto senza che nessuno se ne accorgesse, mentre la suite sintetica
restava verde: 1495 test verdi e il confronto che divergeva **al carattere 0** su
qualunque pagina con elenchi. Un test sintetico verifica cio' che ho pensato di
verificare; questo verifica che l'insieme non abbia perso o riordinato niente.

**La base non e' mia.** Le dieci pagine escono da
`Campione_UscitaIR2Minima_v1.md`, sorteggiate con seed dichiarato **prima** della
misura da un pool non condizionato di 5.194 pagine; e cio' che «giusto» significa
lo ha stabilito l'utente guardando le pagine **prima che IR 2 esistesse**
(`Criterio_UscitaIR2Minima_v2.md` §1). Qui nessuno scrive un valore atteso.

**E la base e' pinnata a un commit.** Si genera dentro un worktree temporaneo
alla revisione dichiarata, non col codice corrente: altrimenti basterebbe un
cambiamento alla fetta verticale perche' il confronto misuri un riferimento che
si e' spostato, senza dirlo. Verificato il 30 agosto 2026 che le due basi
coincidono su tutte e dieci -- ma coincidevano per fortuna, non per costruzione.

**Che cosa «identico» NON dice.** Questa barra e' un controllo di
**non-regressione sull'ordine e sull'inclusione**, e nient'altro. Il giudizio
umano che la fonda copriva **il solo ordine di lettura**, tabelle escluse, su una
pipeline che non aveva paragrafi, elenchi, titoli, enfasi ne' arredo -- e il
confronto toglie di mezzo tutti quei meccanismi per costruzione. Dieci pagine
identiche non dicono che l'uscita sia buona: dicono che IR 2 non ha riordinato ne'
perso niente rispetto alla fetta verticale.

**E dove IR 2 e' MIGLIORE della base, qui risulta una differenza.** Fab idx 126 e'
il primo caso: la deduplicazione dei ridisegni gemelli e' un miglioramento e il
confronto la segnala. Man mano che i miglioramenti atterrano l'elenco delle
differenze da spiegare cresce, e la base resta ancorata a un'uscita piu' vecchia.
E' il limite strutturale di questa barra, non un difetto da correggere qui.

**Non decide se una differenza e' accettabile.** Il §2 del criterio dice che ogni
differenza va **spiegata**, e se sia spiegata lo sa il verbale, non uno script:
qui una differenza fa fallire, e chi la legge va a vedere se e' gia' a verbale.
Al 30 agosto 2026 ce n'e' **una**: su Fab idx 126 la base scrive `CAPITOLO` due
volte e IR 2 una, perche' `redrawn_duplicates` fonde i due ridisegni gemelli
(`Criterio_ConfrontoEB_v4.md` §4).

Uso::

    ./venv/bin/python scripts/check_eb.py --pdf-dir .
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# La fetta verticale al commit in cui **tutte e dieci** le pagine sono
# eseguibili. Il criterio nomina `3a2238d`; `Wil` idx 71 ci faceva crashare e la
# pagina e' rientrata con `2d6052b`, che il Campione dichiara. E' quello.
BASE_REVISION = "2d6052b"

_SAMPLE_ROW = re.compile(r"^\|\s*\d+\s*\|\s*(\w+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|", re.M)


def sample(campione: Path) -> list[tuple[str, int]]:
    """(manuale, `--page-number`) dal documento del campione, non da qui.

    Il campione si legge dove e' dichiarato: duplicarlo in questo file lo
    renderebbe due verita' che possono divergere.
    """

    rows = _SAMPLE_ROW.findall(campione.read_text(encoding="utf-8"))
    return [(manual, int(page_number)) for manual, _index, page_number in rows]


def base_worktree(revision: str, where: Path) -> Path:
    """Un worktree usa e getta alla revisione della base."""

    subprocess.run(
        ["git", "worktree", "add", "--detach", str(where), revision],
        capture_output=True,
        check=True,
        cwd=PROJECT_ROOT,
    )
    return where


def drop_worktree(where: Path) -> None:
    subprocess.run(
        ["git", "worktree", "remove", "--force", str(where)],
        capture_output=True,
        check=False,
        cwd=PROJECT_ROOT,
    )


def build_base(worktree: Path, pdf: Path, page_number: int, out: Path) -> Path:
    subprocess.run(
        [
            sys.executable,
            str(worktree / "scripts" / "prototype_vertical_slice_page.py"),
            "--pdf", str(pdf.resolve()),
            "--page-number", str(page_number),
            "--output-dir", str(out),
            "--emit-order-variants",
        ],
        capture_output=True,
        check=False,
        cwd=worktree,
    )
    return out / "page_bands.md"


def compare(pdf: Path, page_number: int, base: Path, out: Path) -> tuple[str, list[str]]:
    """Torna la riga di esito e le eventuali righe di contenuto perso."""

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "prototype_ir2_page.py"),
            "--pdf", str(pdf.resolve()),
            "--page-number", str(page_number),
            "--output-dir", str(out),
            "--arredo", "--elenchi", "--arredo-pagine", "20",
            "--base", str(base),
        ],
        capture_output=True,
        check=False,
        cwd=PROJECT_ROOT,
        text=True,
    )
    verdict = "(non eseguita)"
    losses: list[str] = []
    for line in result.stderr.splitlines():
        if line.startswith("E-B: ordine "):
            verdict = line[len("E-B: ") :]
        elif "PERSO" in line:
            losses.append(line.strip())
    return (verdict, losses)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--base-rev", default=BASE_REVISION)
    parser.add_argument(
        "--campione", type=Path, default=PROJECT_ROOT / "Campione_UscitaIR2Minima_v1.md"
    )
    arguments = parser.parse_args()

    pages = sample(arguments.campione)
    if not pages:
        print("FAIL: il campione non si legge", file=sys.stderr)
        raise SystemExit(3)

    started = time.monotonic()
    identical = 0
    diverging: list[str] = []
    lost: list[str] = []
    print(f"Barra E-B — {len(pages)} pagine, base alla revisione {arguments.base_rev}\n")
    with tempfile.TemporaryDirectory() as raw:
        workspace = Path(raw)
        worktree = base_worktree(arguments.base_rev, workspace / "base_rev")
        try:
            for manual, page_number in pages:
                pdf = arguments.pdf_dir / f"{manual}.pdf"
                if not pdf.is_file():
                    print(f"{manual:<5} idx {page_number - 1:<4} PDF assente")
                    continue
                base = build_base(
                    worktree, pdf, page_number, workspace / f"base_{manual}_{page_number}"
                )
                if not base.is_file():
                    print(f"{manual:<5} idx {page_number - 1:<4} base non prodotta")
                    diverging.append(f"{manual} idx {page_number - 1}")
                    continue
                verdict, losses = compare(
                    pdf, page_number, base, workspace / f"new_{manual}_{page_number}"
                )
                print(f"{manual:<5} idx {page_number - 1:<4} {verdict}")
                if verdict.startswith("ordine IDENTICO"):
                    identical += 1
                else:
                    diverging.append(f"{manual} idx {page_number - 1}")
                for line in losses:
                    print(f"      {line}")
                    lost.append(line)
        finally:
            drop_worktree(worktree)

    elapsed = time.monotonic() - started
    print(f"\nidentiche {identical} su {len(pages)}   ({elapsed:.0f} s)")
    print("«identico» = IR 2 non ha riordinato ne' perso niente rispetto alla base.")
    print("NON dice che l'uscita sia buona: il giudizio che fonda questa barra")
    print("copriva il solo ordine di lettura, prima che IR 2 esistesse.")
    if lost:
        print(f"\n**La resa ha perso contenuto in {len(lost)} nodi.** Non e' una")
        print("differenza da spiegare: e' un difetto dell'emettitore.")
    if diverging:
        print("\nDifferenze da spiegare, `Criterio_UscitaIR2Minima_v2.md` §2:")
        for name in diverging:
            print(f"  - {name}")
        print("\nUna differenza gia' a verbale non e' un fallimento: va CONFRONTATA")
        print("col verbale, e questo script non puo' farlo al posto di chi legge.")
        print("Al 30 agosto 2026 l'unica a verbale e' Fab idx 126, il ridisegno")
        print("deduplicato di `Criterio_ConfrontoEB_v4.md` §4.")
        raise SystemExit(1)
    print("\nE-B: nessuna differenza.")


if __name__ == "__main__":
    main()
