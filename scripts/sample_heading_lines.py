"""Il campione di `Criterio_Titoli_v2.md` §3, e il materiale per giudicarlo.

**Due meta', e la seconda e' quella che conta.** Sedici righe che la regola
**promuove** a titolo e sedici che stanno **sopra la prosa** e che la regola
**scarta**. Il giro precedente ha mostrato che serve: `Esito_ElencoNumerato_v1.md`
ha trovato tutti e sette gli errori nella lista delle scartate, che un campione
delle sole promosse non avrebbe mostrato.

**Il materiale si costruisce dalla resa**, non dalla sorgente: ogni pagina
campionata si rende col prototipo e si mostra cio' che uscirebbe. E' la
correzione dichiarata dopo il difetto di `Esito_Elenchi_v1.md` §6.

**L'arredo e' escluso**, perche' in molti manuali il numero di pagina e' piu'
grande della prosa e senza l'esclusione sarebbe un titolo di primo livello.

Uso::

    ./venv/bin/python scripts/sample_heading_lines.py --pdf-dir . --out <dir> --seed 20260926
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

from document_furniture_policy import furniture_slots, slot_of  # noqa: E402
from document_heading_measurements import measure_font_sizes, sized_lines  # noqa: E402
from document_heading_policy import (  # noqa: E402
    SIZE_EPSILON,
    heading_levels,
    heading_lines,
    prose_sizes,
)
from document_text_recurrence_measurements import (  # noqa: E402
    measure_document_text_recurrence,
    normalize_text,
)
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

# **DrM e DrW escono dalla popolazione**, e `Criterio_Titoli_v3.md` §3 lo
# dichiara **prima** del sorteggio. Nel giro precedente DrM da solo dava 13 righe
# su 32 e 11 delle 11 «non titolo»: un manuale decideva un terzo del giudizio, su
# una categoria -- le schede mostro -- che il progetto sa di non gestire.
#
# Dichiararlo prima e' cio' che lo distingue dallo scartare i casi scomodi dopo,
# che e' quello che `AGENTS.MD` §15 vieta. Il prezzo si paga per intero: cio' che
# la regola fa su di loro si riporta separatamente nell'esito.
MANUALS = (
    "Apo", "BiD", "BoB", "DB", "DIE", "Dag",
    "FW", "FWK", "Fab", "Kul", "Lan", "SV", "Vil", "Wil",
)
EXCLUDED_STAT_BLOCK_MANUALS = ("DrM", "DrW")
PER_HALF = 16
RENDER_DPI = 150


def furniture_texts(pages, labels, indices) -> dict[int, set[str]]:
    """I testi che l'arredo toglie dal corpo, per indice di pagina."""

    measured = measure_document_text_recurrence(pages)
    slots = furniture_slots(list(zip(pages, labels, strict=True)), measured).all_slots
    out: dict[int, set[str]] = {}
    for page, index in zip(pages, indices, strict=True):
        texts = {
            normalize_text(primitive.text)
            for primitive in page.text_primitives
            if slot_of(primitive, page) in slots and normalize_text(primitive.text)
        }
        out[index] = texts
    return out


def collect(pdf_path: Path, window: int) -> list[dict]:
    """Le righe sopra la prosa, con la classe che la regola gli assegna."""

    with fitz.open(pdf_path) as document:
        first = max(0, len(document) // 2 - window // 2)
        pages, labels, indices = [], [], []
        for index in range(first, min(len(document), first + window)):
            page = document[index]
            if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
                continue
            capture = capture_pymupdf_page(
                page,
                source_id="headings",
                page_id=f"page:{index:04d}",
                capture_id=f"headings:{index:04d}",
            )
            pages.append(normalize_backend_page_capture(capture))
            labels.append((page.get_label() or "").strip())
            indices.append(index)
        if not pages:
            return []

        measurements = measure_font_sizes(pages)
        prose = prose_sizes(measurements)
        levels = heading_levels(measurements, prose)
        if not prose or not levels:
            return []
        limit = max(prose)
        removed = furniture_texts(pages, labels, indices)

        found: list[dict] = []
        for page, index in zip(pages, indices, strict=True):
            lines = sized_lines(page)
            promoted = heading_lines(lines, prose, levels, frozenset(removed.get(index, ())))
            for position, line in enumerate(lines):
                if line.size <= limit + SIZE_EPSILON or len(line.text) <= 1:
                    continue
                if normalize_text(line.text) in removed.get(index, ()):
                    continue
                found.append(
                    {
                        "manuale": pdf_path.stem,
                        "pagina_idx": index,
                        "testo": line.text,
                        "dimensione": line.size,
                        "livello": promoted.get(position),
                        "classe": "promossa" if position in promoted else "scartata",
                    }
                )
        return found


def render_page(pdf: Path, index: int, workspace: Path) -> str:
    out = workspace / f"{pdf.stem}_{index}"
    subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "prototype_ir2_page.py"),
            "--pdf", str(pdf),
            "--page-number", str(index + 1),
            "--output-dir", str(out),
            "--arredo", "--elenchi", "--arredo-pagine", "20",
        ],
        capture_output=True,
        check=False,
        cwd=PROJECT_ROOT,
    )
    rendered = out / "page_ir2.md"
    return rendered.read_text(encoding="utf-8") if rendered.is_file() else ""


def _bare(text: str) -> str:
    return "".join(c for c in text if c.isalnum()).lower()


def rendered_around(markdown: str, needle: str, span: int = 5) -> list[str]:
    target = _bare(needle)[:22]
    lines = markdown.splitlines()
    if target:
        for position, line in enumerate(lines):
            if target and target in _bare(line):
                start = max(0, position - 1)
                return [entry for entry in lines[start : start + span] if entry.strip()]
    return ["(non trovata nella resa)"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--pagine", type=int, default=10)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    everything: list[dict] = []
    for name in MANUALS:
        path = args.pdf_dir / f"{name}.pdf"
        if not path.is_file():
            continue
        found = collect(path, args.pagine)
        promoted = sum(1 for item in found if item["classe"] == "promossa")
        print(f"{name}: {promoted} promosse, {len(found) - promoted} scartate", file=sys.stderr)
        everything.extend(found)

    rng = random.Random(args.seed)
    chosen: list[dict] = []
    for klass in ("promossa", "scartata"):
        pool = [item for item in everything if item["classe"] == klass]
        chosen.extend(rng.sample(pool, min(PER_HALF, len(pool))))
    rng.shuffle(chosen)

    lines = [
        "# Righe da etichettare — titoli",
        "",
        "Per ognuna: **titolo**, **non titolo**, oppure **incerto**.",
        "",
        f"Righe: **{len(chosen)}**. Estratte con seed `{args.seed}`, dichiarato prima.",
        "",
        "Il render della pagina sta accanto a questo file.",
        "",
    ]
    chiave = ["# Chiave", "", "| # | manuale | idx | dim | classe | livello |", "| --- | --- | --- | --- | --- | --- |"]

    with tempfile.TemporaryDirectory() as workspace:
        root = Path(workspace)
        rendered_cache: dict[tuple[str, int], str] = {}
        for position, item in enumerate(chosen, start=1):
            idx = item["pagina_idx"]
            key = (item["manuale"], idx)
            if key not in rendered_cache:
                rendered_cache[key] = render_page(args.pdf_dir / f"{item['manuale']}.pdf", idx, root)
            stem = f"{item['manuale']}_pagina{idx + 1:04d}_idx{idx:04d}"

            lines.append(f"## Riga {position:02d} — render `{stem}.png`")
            lines.append("")
            lines.append(f"Manuale **{item['manuale']}**. La riga e':")
            lines.append("")
            lines.append("```")
            lines.append(item["testo"][:100])
            lines.append("```")
            lines.append("")
            lines.append("**Come esce nel Markdown, col suo contorno:**")
            lines.append("")
            lines.append("```markdown")
            lines.extend(entry[:100] for entry in rendered_around(rendered_cache[key], item["testo"]))
            lines.append("```")
            lines.append("")
            lines.append("Giudizio: ")
            lines.append("")

            chiave.append(
                f"| {position:02d} | {item['manuale']} | {idx} | {item['dimensione']} "
                f"| {item['classe']} | {item['livello'] or '-'} |"
            )

            target = args.out / f"{stem}.png"
            if not target.is_file():
                with fitz.open(args.pdf_dir / f"{item['manuale']}.pdf") as document:
                    target.write_bytes(document[idx].get_pixmap(dpi=RENDER_DPI).tobytes("png"))

    (args.out / "Righe_da_etichettare.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (args.out.parent / f"CHIAVE_{args.out.name}.md").write_text("\n".join(chiave) + "\n", encoding="utf-8")
    print(f"\nrighe totali {len(everything)}, campionate {len(chosen)}")


if __name__ == "__main__":
    main()
