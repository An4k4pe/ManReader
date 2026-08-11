"""Driver: esegue ``dump_column_band_all_bands.py`` su ogni manuale e scrive un
CSV per manuale, senza aggregare nulla. L'aggregazione sta in
``summarize_intra_page_band_structure.py``, separata di proposito: lo scan e'
lungo (migliaia di pagine) e va rifatto solo se cambiano gli script, mentre la
domanda che si pone ai dati puo' cambiare piu' volte.

Motivo per cui esiste: l'utente ha osservato che il cambio di struttura di
colonna DENTRO la stessa pagina (titolo o intro a colonna singola, poi corpo
multicolonna; oppure illustrazione a piena larghezza che interrompe) e'
frequente, non particolare. Il caso Dag p.84 posizionale (State.md, "Fallimento
misurato su Dag") lo conferma su UNA pagina: cinque zone, tre strutture di
colonna. Una pagina non e' una statistica. Questo scan raccoglie il dato per
trasformare l'osservazione in una misura, o per smentirla.

**Limite dichiarato, da leggere prima di citare qualunque numero che ne esce**:
``_segment_column_bands`` viene dal percorso di Milestone 32, quello il cui
clustering di righe ha una sovra-fusione gia' misurata al 13,6%-45,7%
(``inspect_row_clustering_merge_diagnostics.py``). La sovra-fusione fonde righe
reali, quindi tende a NASCONDERE i confini fra bande, non a inventarne. Il
conteggio di bande per pagina che ne esce va quindi letto come **limite
inferiore**: se questo scan dice che le pagine multi-banda sono frequenti, lo
sono almeno altrettanto. Non vale il contrario -- un conteggio basso non
dimostra che le pagine siano omogenee.

Non un producer. Non wired. Diagnostica pura.

Uso:

    python3 scripts/scan_intra_page_band_structure.py --output-dir output/intra_page_bands
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR
for candidate_dir in (SCRIPT_DIR, SCRIPT_DIR.parent, SCRIPT_DIR.parent.parent):
    if (candidate_dir / "primitive_model.py").is_file():
        PROJECT_ROOT = candidate_dir
        break

# Esclusi: non sono manuali reali, sono fixture di test con una manciata di
# pagine. Includerli falserebbe qualunque tasso calcolato per pagina.
_EXCLUDED = {"TabellaManGrafic.pdf", "test.pdf"}


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Cartella dove scrivere un CSV per manuale.",
    )
    parser.add_argument(
        "--manuals",
        nargs="*",
        default=None,
        help="Nomi di PDF da processare. Default: tutti quelli nella radice del progetto.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Salta i manuali il cui CSV esiste gia', per riprendere uno scan interrotto.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.manuals:
        pdfs = [PROJECT_ROOT / name for name in args.manuals]
    else:
        pdfs = sorted(p for p in PROJECT_ROOT.glob("*.pdf") if p.name not in _EXCLUDED)

    dump_script = SCRIPT_DIR / "dump_column_band_all_bands.py"
    failures: list[str] = []

    for index, pdf_path in enumerate(pdfs, start=1):
        if not pdf_path.is_file():
            print(f"[{index}/{len(pdfs)}] MANCANTE {pdf_path.name}", flush=True)
            failures.append(pdf_path.name)
            continue

        destination = output_dir / f"{pdf_path.stem}_all_bands.csv"
        if args.skip_existing and destination.is_file():
            print(f"[{index}/{len(pdfs)}] salto {pdf_path.name} (CSV gia' presente)", flush=True)
            continue

        started = time.monotonic()
        print(f"[{index}/{len(pdfs)}] {pdf_path.name} ...", flush=True)
        completed = subprocess.run(
            [
                sys.executable,
                str(dump_script),
                str(pdf_path),
                "--output",
                str(destination),
            ],
            capture_output=True,
            text=True,
        )
        elapsed = time.monotonic() - started

        if completed.returncode != 0:
            tail = (completed.stderr or "").strip().splitlines()[-3:]
            print(
                f"[{index}/{len(pdfs)}] FALLITO {pdf_path.name} dopo {elapsed:.0f}s: "
                + " | ".join(tail),
                flush=True,
            )
            failures.append(pdf_path.name)
            continue

        print(f"[{index}/{len(pdfs)}] fatto {pdf_path.name} in {elapsed:.0f}s", flush=True)

    if failures:
        print(f"\nManuali falliti o mancanti: {', '.join(failures)}", flush=True)
        return 1

    print("\nScan completato su tutti i manuali.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
