"""Che cosa vedono i producer WIRED su una pagina, attraverso il job runner.

Non riesegue il meccanismo per conto proprio: apre un job, cattura la pagina e
chiama `run_job_page_analysis`, cioe' il percorso che il progetto considera
reale. Rende i candidati sulla pagina, un colore per producer.

`layout.side_band` NON compare: non e' fra i sei producer wired: Milestone 6 lo
ha congelato come baseline diagnostica, non come detector affidabile. Le
linguette di capitolo che sono TESTO ruotato restano quindi senza un producer
che le tolga; quelle che sono VISUALI le vede `page_edge_visual`.

Read-only sui PDF; il job viene creato in una cartella temporanea.

Uso:

    ./venv/bin/python scripts/render_wired_producers.py --pdf-dir . \
        --pages DrM:35 --outdir output/wired
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from job_capture_page_runner import capture_job_page  # noqa: E402
from job_initializer import initialize_job  # noqa: E402
from job_page_analysis_runner import run_job_page_analysis  # noqa: E402

COLORS = {
    "column_band": (0.0, 0.0, 0.9),
    "page_edge_visual": (0.9, 0.4, 0.0),
    "table_candidate": (0.85, 0.0, 0.0),
    "embedded_visual": (0.0, 0.55, 0.0),
    "interior_visual_frame": (0.6, 0.0, 0.6),
    "page_covering_visual": (0.5, 0.5, 0.5),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--pages", nargs="+", required=True, help="Nome:idx0based")
    parser.add_argument(
        "--producers",
        nargs="+",
        default=["column_band", "page_edge_visual"],
        help="fra i sei wired",
    )
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    for spec in args.pages:
        name, raw = spec.split(":")
        index = int(raw)
        source = args.pdf_dir / f"{name}.pdf"
        document = fitz.open(source)
        page = document[index]
        print(f"\n### {name} idx {index} (pagina file {index + 1})")

        with tempfile.TemporaryDirectory() as temporary:
            job_dir = Path(temporary) / "job"
            manifest = initialize_job(
                source_path=source,
                job_dir=job_dir,
                job_id=f"job-{name}-{index}",
                page_count=len(document),
            )
            manifest_path = job_dir / manifest.workspace.manifest_path
            capture_job_page(
                job_dir=job_dir, manifest_path=manifest_path, page_num=index + 1
            )
            for producer in args.producers:
                result = run_job_page_analysis(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=index + 1,
                    producer_name=producer,
                    generation_id=f"wired:{producer}",
                )
                candidates = result.analysis.candidates
                print(f"   {producer}: {len(candidates)} candidati")
                for candidate in candidates:
                    x0, y0, x1, y1 = candidate.bbox
                    print(
                        f"      {candidate.proposed_structural_kind:28s} "
                        f"({x0:6.1f},{y0:6.1f},{x1:6.1f},{y1:6.1f})  "
                        f"{len(candidate.primitive_ids)} primitive"
                    )
                    shape = page.new_shape()
                    shape.draw_rect(fitz.Rect(x0, y0, x1, y1))
                    shape.finish(
                        color=COLORS.get(producer, (0, 0, 0)),
                        width=2.0,
                        dashes="[4 3] 0",
                    )
                    shape.commit()

        out = args.outdir / f"{name}_pagina{index + 1:04d}_wired.png"
        page.get_pixmap(dpi=110).save(out)
        print(f"   reso: {out}")


if __name__ == "__main__":
    main()
