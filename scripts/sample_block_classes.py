"""Il campione di `Criterio_ScalaDiValori_v1.md` §3, e il materiale per giudicarlo.

**L'unita' e' il blocco sorgente**, che e' cio' su cui la regola decide: elenco,
scala di valori, o nessuno dei due.

**Il materiale si costruisce dalla RESA, non dalla sorgente.** Difetto dichiarato
del giro precedente: il campione mostrava le voci troncate a fine riga fisica
perche' veniva dalle righe sorgente, mentre il renderer unisce le continuazioni.
Qui ogni pagina si rende davvero, col prototipo, e si mostra cio' che uscirebbe.

Uso::

    ./venv/bin/python scripts/sample_block_classes.py --pdf-dir . --out <dir> --seed 20260919
"""

from __future__ import annotations

import argparse
import random
import subprocess
import sys
import tempfile
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from document_line_start_measurements import (  # noqa: E402
    block_marker_signature,
    count_block_signatures,
    measure_document_line_starts,
    source_lines,
)
from document_list_policy import (  # noqa: E402
    list_item_flags,
    list_markers,
    value_scale_signatures,
)
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

CANDIDATES = ("Apo", "BiD", "BoB", "Dag", "DB", "DrM", "DrW", "FW", "FWK", "Vil")
PER_CLASS = 10
RENDER_DPI = 150


def classify(pdf_path: Path, window: int) -> list[dict]:
    """I blocchi di un manuale, con la classe che la regola gli assegna."""

    found: list[dict] = []
    with fitz.open(pdf_path) as document:
        first = max(0, len(document) // 2 - window // 2)
        pages, indices = [], []
        for index in range(first, min(len(document), first + window)):
            page = document[index]
            if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
                continue
            capture = capture_pymupdf_page(
                page,
                source_id="classes",
                page_id=f"page:{index:04d}",
                capture_id=f"classes:{index:04d}",
            )
            pages.append(normalize_backend_page_capture(capture))
            indices.append(index)
        if not pages:
            return found

        markers = list_markers(measure_document_line_starts(pages))
        if not markers:
            return found
        scales = value_scale_signatures(count_block_signatures(pages, markers))

        for page, index in zip(pages, indices, strict=True):
            lines = [(block, text) for block, text in source_lines(page)]
            flags = list_item_flags(lines, markers, scales)
            signatures = dict(block_marker_signature(page, markers))
            per_block: dict[str, list[str]] = {}
            for (block, text), flag in zip(lines, flags, strict=True):
                stripped = text.strip()
                if stripped and stripped[0] in markers:
                    per_block.setdefault(block, []).append(f"{'ITEM' if flag else '----'} {stripped}")
            for block, entries in per_block.items():
                is_scale = signatures.get(block) in scales
                is_list = any(e.startswith("ITEM") for e in entries)
                found.append(
                    {
                        "manuale": pdf_path.stem,
                        "blocco": block,
                        "pagina_idx": index,
                        "classe": "scala" if is_scale else "elenco" if is_list else "nessuno",
                        "firma": "".join(signatures.get(block, ())),
                        "righe": [e[5:] for e in entries][:8],
                    }
                )
    return found


def _bare(text: str) -> str:
    """Il testo senza cio' che la resa aggiunge o toglie.

    Serve per ritrovare nella resa una riga vista nella sorgente: la resa
    inserisce il grassetto (`**Round:**`) e toglie il marcatore, quindi un
    confronto letterale falliva e il materiale usciva col buco.
    """

    return "".join(character for character in text if character.isalnum()).lower()


def rendered_around(markdown: str, needle: str, span: int = 8) -> list[str]:
    """Le righe della resa attorno al testo cercato."""

    target = _bare(needle)[:24]
    lines = markdown.splitlines()
    if target:
        for position, line in enumerate(lines):
            if target in _bare(line):
                start = max(0, position - 1)
                return [entry for entry in lines[start : start + span] if entry.strip()]
    return ["(non trovato nella resa)"]


def render_page(pdf: Path, index: int, workspace: Path) -> str:
    out = workspace / f"{pdf.stem}_{index}"
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "prototype_ir2_page.py"),
        "--pdf", str(pdf),
        "--page-number", str(index + 1),
        "--output-dir", str(out),
        "--elenchi", "--arredo-pagine", "20",
    ]
    subprocess.run(command, capture_output=True, check=False, cwd=PROJECT_ROOT)
    rendered = out / "page_ir2.md"
    return rendered.read_text(encoding="utf-8") if rendered.is_file() else ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--pagine", type=int, default=20)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    everything: list[dict] = []
    for name in CANDIDATES:
        path = args.pdf_dir / f"{name}.pdf"
        if not path.is_file():
            continue
        found = classify(path, args.pagine)
        counts = {c: sum(1 for i in found if i["classe"] == c) for c in ("elenco", "scala", "nessuno")}
        print(f"{name}: {counts}", file=sys.stderr)
        everything.extend(found)

    rng = random.Random(args.seed)
    chosen: list[dict] = []
    for klass in ("elenco", "scala"):
        pool = [item for item in everything if item["classe"] == klass]
        chosen.extend(rng.sample(pool, min(PER_CLASS, len(pool))))
    rng.shuffle(chosen)

    lines = [
        "# Voci da etichettare — blocchi",
        "",
        "Per ognuno: **elenco**, **scala di valori**, **nessuno dei due**, o **incerto**.",
        "",
        f"Estratti con seed `{args.seed}`, dichiarato prima. Blocchi: **{len(chosen)}**.",
        "",
        "Il render della pagina sta accanto a questo file.",
        "",
    ]
    chiave = ["# Chiave", "", "| # | manuale | blocco | firma | classe |", "| --- | --- | --- | --- | --- |"]

    with tempfile.TemporaryDirectory() as workspace:
        root = Path(workspace)
        for position, item in enumerate(chosen, start=1):
            idx = item["pagina_idx"]
            stem = f"{item['manuale']}_pagina{idx + 1:04d}_idx{idx:04d}"
            markdown = render_page(args.pdf_dir / f"{item['manuale']}.pdf", idx, root)
            needle = item["righe"][0][1:].strip() if item["righe"] else ""

            lines.append(f"## Voce {position:02d} — render `{stem}.png`")
            lines.append("")
            lines.append(f"Manuale **{item['manuale']}**.")
            lines.append("")
            lines.append("**Come sta nella sorgente:**")
            lines.append("")
            lines.append("```")
            lines.extend(text[:104] for text in item["righe"])
            lines.append("```")
            lines.append("")
            lines.append("**Come esce nel Markdown:**")
            lines.append("")
            lines.append("```markdown")
            lines.extend(entry[:104] for entry in rendered_around(markdown, needle))
            lines.append("```")
            lines.append("")
            lines.append("Giudizio: ")
            lines.append("")

            chiave.append(
                f"| {position:02d} | {item['manuale']} | {item['blocco']} "
                f"| `{item['firma']}` | {item['classe']} |"
            )

            target = args.out / f"{stem}.png"
            if not target.is_file():
                with fitz.open(args.pdf_dir / f"{item['manuale']}.pdf") as document:
                    target.write_bytes(document[idx].get_pixmap(dpi=RENDER_DPI).tobytes("png"))

    (args.out / "Voci_da_etichettare.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (args.out.parent / f"CHIAVE_{args.out.name}.md").write_text("\n".join(chiave) + "\n", encoding="utf-8")
    print(f"\nblocchi totali {len(everything)}, campionati {len(chosen)}")


if __name__ == "__main__":
    main()
