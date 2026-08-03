"""Standalone real-manual smoke check for the page_covering_visual job wiring.

Diagnostico soltanto, senza stage CLI dedicato (esplicitamente fuori scope nella
Milestone 23). Committato in sanatoria: sostiene le "11 pagine campione" citate
in State.md, Milestone 23, e senza di esso quell'esempio non e' riproducibile.
Esercita il percorso di produzione gia' committato,
job_page_analysis_runner.run_job_page_analysis(producer_name="page_covering_visual"),
su pagine reali di manuali, ciascuna in un workspace di job temporaneo separato, e
stampa quali candidate (se presenti) sono state prodotte.

Non modifica nessun manuale, non scrive nulla fuori da una directory temporanea,
non fa commit.

Uso, dalla radice del repository (dove i moduli del progetto sono importabili):

    python3 scripts/verify_page_covering_visual_real_pages.py \
        --dag /percorso/reale/Dag.pdf \
        --vil /percorso/reale/Vil.pdf \
        --db /percorso/reale/DB.pdf

Se un flag viene omesso, il default cerca Dag.pdf/Vil.pdf/DB.pdf nella directory
corrente. Se un file non esiste, quel manuale viene saltato per intero (le pagine
degli altri manuali vengono comunque verificate).
"""

from __future__ import annotations

import argparse
import sys
import tempfile
import traceback
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from job_capture_page_runner import capture_job_page  # noqa: E402
from job_initializer import initialize_job  # noqa: E402
from job_page_analysis_runner import run_job_page_analysis  # noqa: E402

_PAGES_TO_CHECK: dict[str, tuple[int, ...]] = {
    "dag": (27, 55, 73),
    "vil": (95, 124, 131, 143),
    "db": (118, 122, 100, 84),
}


def _check_one_page(*, manual_label: str, source_path: Path, page_num: int) -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        job_dir = Path(temporary_directory) / f"job-{manual_label}-{page_num:04d}"

        document = fitz.open(source_path)
        try:
            page_count = document.page_count
            if not (1 <= page_num <= page_count):
                print(
                    f"[{manual_label} p.{page_num}] FUORI RANGE "
                    f"(il PDF ha {page_count} pagine) - saltata"
                )
                return
            page = document.load_page(page_num - 1)
            rotation = page.rotation
            mediabox = page.mediabox
            cropbox = page.cropbox
        finally:
            document.close()

        manifest = initialize_job(
            source_path=source_path,
            job_dir=job_dir,
            job_id=f"job-{manual_label}-{page_num:04d}",
            page_count=page_count,
        )
        manifest_path = job_dir / manifest.workspace.manifest_path
        capture_job_page(job_dir=job_dir, manifest_path=manifest_path, page_num=page_num)

        try:
            result = run_job_page_analysis(
                job_dir=job_dir,
                manifest_path=manifest_path,
                page_num=page_num,
                producer_name="page_covering_visual",
                generation_id=f"generation:smoke:{manual_label}:{page_num:04d}",
            )
        except ValueError as exc:
            print(
                f"[{manual_label} p.{page_num}] RIFIUTATA dal runner: {exc} "
                f"(rotation={rotation}, mediabox={mediabox}, cropbox={cropbox})"
            )
            return
        except Exception:
            print(f"[{manual_label} p.{page_num}] ERRORE INATTESO:")
            traceback.print_exc()
            return

        candidates = result.analysis.candidates
        if not candidates:
            print(
                f"[{manual_label} p.{page_num}] nessuna candidate page_covering_visual "
                f"(pagina width={mediabox.width:.1f} height={mediabox.height:.1f})"
            )
            return

        for candidate in candidates:
            x0, y0, x1, y1 = candidate.bbox
            page_width = mediabox.width
            page_height = mediabox.height
            width_ratio = (x1 - x0) / page_width if page_width else float("nan")
            height_ratio = (y1 - y0) / page_height if page_height else float("nan")
            print(
                f"[{manual_label} p.{page_num}] candidate {candidate.candidate_id} "
                f"kind={candidate.proposed_structural_kind} "
                f"bbox=({x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f}) "
                f"width_ratio={width_ratio:.4f} height_ratio={height_ratio:.4f} "
                f"primitive_ids={candidate.primitive_ids}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dag", type=Path, default=Path("Dag.pdf"))
    parser.add_argument("--vil", type=Path, default=Path("Vil.pdf"))
    parser.add_argument("--db", type=Path, default=Path("DB.pdf"))
    args = parser.parse_args()

    sources = {"dag": args.dag, "vil": args.vil, "db": args.db}
    for manual_label, page_numbers in _PAGES_TO_CHECK.items():
        source_path = sources[manual_label]
        if not source_path.is_file():
            print(f"[{manual_label}] file non trovato: {source_path} - saltato interamente")
            continue
        for page_num in page_numbers:
            _check_one_page(
                manual_label=manual_label,
                source_path=source_path,
                page_num=page_num,
            )


if __name__ == "__main__":
    main()
