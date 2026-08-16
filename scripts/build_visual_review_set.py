"""Un set di verifiche a vista, dove ogni pagina porta l'affermazione da
falsificare invece del solo disegno.

Nasce da un fatto di questa sessione: quattro volte un'opinione di Chat A e' caduta
davanti a un controllo, e in tre casi su quattro il controllo era **guardare la
pagina**. Un overlay senza una domanda scritta accanto si guarda e si annuisce;
un overlay con «se vedi X, l'affermazione e' falsa» si puo' solo confermare o
smentire.

Per ogni pagina produce:

  - l'overlay (`render_corridor_interruption_overlay.py`): gutter sulla propria
    fascia probatoria in verde, bande prima in blu, dopo in arancione, blocker
    attraversanti in rosso e inerti in grigio;
  - il markdown della fetta verticale nelle sue varianti, cosi' si legge il
    testo che quella struttura produce davvero;
  - una voce in `INDICE.md` con l'affermazione, cosa la falsificherebbe, e lo
    spazio per l'esito.

Le tre classi corrispondono a cio' che al 16 agosto 2026 resta **non guardato**,
per rilievo della revisione indipendente:

  interruzione   le 42 bande toccate dalla regola dei filetti, di cui nessuna e'
                 mai stata ispezionata (rilievo B4);
  tagli          le pagine dove un confine di banda cade dentro una parola e che
                 restano dopo la correzione (109 sull'apertura, 25 sul corpo),
                 mai attribuite (rilievo B5);
  paragrafo      la segmentazione in paragrafi dal blocco, il cui verdetto a
                 vista non e' mai stato dato (rilievo B1, criterio 3).

I numeri di pagina sono POSIZIONALI. Non un producer. Non wired.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import cast

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

_CLAIMS: dict[str, tuple[str, str]] = {
    "interruzione": (
        "Lo spezzamento del corridoio non peggiora la lettura di questa pagina.",
        "L'affermazione e' FALSA se nel markdown compare testo di una colonna "
        "infilato dentro un'altra, o un paragrafo spezzato da contenuto estraneo. "
        "Confronta `page_bands.md` (senza) con `page_bands_cut.md` (con).",
    ),
    "tagli": (
        "I confini di banda che cadono dentro una parola su questa pagina sono "
        "un artefatto del conteggio, non un difetto reale.",
        "L'affermazione e' FALSA se nell'overlay un bordo blu o arancione passa "
        "in mezzo a parole che appartengono chiaramente alla stessa colonna, e "
        "nel markdown quelle parole finiscono separate.",
    ),
    "paragrafo": (
        "La segmentazione in paragrafi presa dal blocco della sorgente e' "
        "corretta su questa pagina.",
        "L'affermazione e' FALSA se due paragrafi distinti finiscono uniti, o se "
        "un paragrafo unico viene spezzato dove il testo continua. Guarda "
        "`page_bands.md` contro la pagina renderizzata.",
    ),
    "subordinazione": (
        "La struttura di bande dopo la correzione sulla subordinazione descrive "
        "questa pagina meglio di prima.",
        "L'affermazione e' FALSA se una banda arancione raggruppa cose che la "
        "pagina tiene separate, o separa cose che la pagina tiene insieme.",
    ),
}


def _run(argv: list[str]) -> bool:
    result = subprocess.run(argv, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    fallito: {' '.join(argv[-4:])}", file=sys.stderr)
        print(f"    {result.stderr.strip()[:200]}", file=sys.stderr)
    return result.returncode == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument(
        "--pages",
        nargs="+",
        required=True,
        help="voci `Manuale,pagina_posizionale`, per esempio Dag,164 DB,53",
    )
    parser.add_argument("--claim", choices=sorted(_CLAIMS), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    args = parser.parse_args(argv)

    output_dir = cast(Path, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    claim, falsifier = _CLAIMS[args.claim]

    lines = [
        f"# Verifica a vista — classe «{args.claim}»",
        "",
        f"**Affermazione da falsificare:** {claim}",
        "",
        f"**Cosa la smentisce:** {falsifier}",
        "",
        "Guarda l'overlay e il markdown insieme: l'overlay dice *dove* il",
        "meccanismo ha messo i confini, il markdown dice *cosa* ne esce. Un",
        "confine sbagliato che non cambia il testo non è un difetto di lettura,",
        "e un testo sbagliato senza un confine sbagliato ha un'altra causa.",
        "",
        "Legenda overlay: **verde** i gutter accettati sulla loro fascia",
        "probatoria; **blu** le bande prima dell'interruzione; **arancione**",
        "dopo; **rosso** i blocker che attraversano davvero; **grigio** quelli",
        "raccolti e inerti.",
        "",
        "| pagina | overlay | markdown | esito | note |",
        "| --- | --- | --- | --- | --- |",
    ]

    for entry in args.pages:
        manual, _, page = entry.partition(",")
        if not page.isdigit():
            print(f"voce non valida: {entry}", file=sys.stderr)
            continue
        pdf = cast(Path, args.pdf_dir) / f"{manual}.pdf"
        if not pdf.is_file():
            print(f"manca: {pdf}", file=sys.stderr)
            continue

        stem = f"{manual}_{page}"
        png = output_dir / f"{stem}.png"
        md_dir = output_dir / stem
        print(f"  {manual} p.{page}")
        _run([
            str(args.python), str(SCRIPT_DIR / "render_corridor_interruption_overlay.py"),
            str(pdf), "--page", page, "--output", str(png), "--blockers", "drawings",
        ])
        _run([
            str(args.python), str(SCRIPT_DIR / "prototype_vertical_slice_page.py"),
            "--pdf", str(pdf), "--page-number", page,
            "--output-dir", str(md_dir),
            "--emit-order-variants", "--interrupt-corridor", "drawings",
        ])
        lines.append(
            f"| {manual} p.{page} | `{png.name}` | `{stem}/page_bands.md` "
            f"(+ `page_bands_cut.md`, `page_lines.md`) |  |  |"
        )

    lines += [
        "",
        "## Come si chiude",
        "",
        "Ogni riga va riempita con **regge** o **cade**, e se cade con cosa si è",
        "visto. Una riga vuota non è un esito: è una pagina non guardata, ed è",
        "esattamente ciò che questo set esiste per non lasciare implicito.",
    ]

    index = output_dir / "INDICE.md"
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nscritto {index}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
