"""Il materiale di giudizio per `Criterio_MarcatoreDaFont_v3.md` §2.

**La moneta e' la voce prodotta, non il carattere ammesso**: si giudicano tutte
le voci d'elenco che il ramo aggiunge rispetto a una revisione di base, ognuna
sulla **pagina resa intera** in cui compare.

Riproducibile dal repo, `AGENTS.MD` §18: la base non e' un file in una cartella
di lavoro ma una **revisione git**, estratta al volo con ``git show``. Chi rifa'
la misura passa la stessa revisione e ottiene le stesse voci.

Il giudizio e' cieco su cio' che conta: la pagina si vede per intero, le voci da
giudicare sono nominate, e **non si dice quale meccanismo le ha prodotte** ne'
che sono aggiunte da un cambiamento.

Uso::

    ./venv/bin/python scripts/build_marker_item_material.py --pdf-dir . \\
        --base-rev f14321d --out <dir>
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from document_line_start_measurements import (  # noqa: E402
    count_block_signatures,
    measure_document_line_starts,
)
from document_list_policy import (  # noqa: E402
    list_item_flags,
    list_markers,
    value_scale_signatures,
)
from ir2_builder import bind_marker_glyphs, body_font, group_source_lines  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

MANUALS = (
    "Apo", "BiD", "BoB", "DB", "DIE", "Dag", "DrM", "DrW",
    "FW", "FWK", "Fab", "Kul", "Lan", "SV", "Vil", "Wil",
)


def baseline_measure(revision: str, workspace: Path):
    """`measure_document_line_starts` come stava alla revisione data."""

    source = subprocess.run(
        ["git", "show", f"{revision}:document_line_start_measurements.py"],
        capture_output=True,
        check=True,
        cwd=PROJECT_ROOT,
        text=True,
    ).stdout
    path = workspace / "baseline_line_starts.py"
    path.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("baseline_line_starts", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("la revisione di base non si carica come modulo")
    module = importlib.util.module_from_spec(spec)
    # Va registrato **prima** di eseguirlo: i dataclass con `slots=True` cercano
    # il proprio modulo in `sys.modules` mentre si costruiscono.
    sys.modules["baseline_line_starts"] = module
    spec.loader.exec_module(module)
    return module.measure_document_line_starts


def capture(pdf: Path, window: int) -> tuple[list, list[int]]:
    pages: list = []
    indices: list[int] = []
    with fitz.open(pdf) as document:
        first = max(0, len(document) // 2 - window // 2)
        for index in range(first, min(len(document), first + window)):
            page = document[index]
            if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
                continue
            indices.append(index)
            pages.append(
                normalize_backend_page_capture(
                    capture_pymupdf_page(
                        page,
                        source_id="marker-items",
                        page_id=f"page:{index:04d}",
                        capture_id=f"marker-items:{index:04d}",
                    )
                )
            )
    return pages, indices


def items_by_page(pages, indices, markers) -> dict[int, list[str]]:
    scales = value_scale_signatures(count_block_signatures(pages, markers))
    found: dict[int, list[str]] = defaultdict(list)
    for index, page in zip(indices, pages, strict=True):
        lines = bind_marker_glyphs(group_source_lines(page.text_primitives), markers)
        keyed = [(line.block, line.text) for line in lines]
        for flag, (_block, text) in zip(list_item_flags(keyed, markers, scales), keyed, strict=True):
            if flag:
                found[index].append(" ".join(text.split()))
    return found


def render(pdf: Path, index: int, workspace: Path) -> str:
    """La resa completa della pagina, dal prototipo.

    Il percorso del PDF va **risolto**: il sottoprocesso gira nella radice del
    progetto, e un `--pdf-dir .` relativo alla checkout da cui si lancia lo
    script non esiste li'. Senza, tutte le rese uscivano `(resa non prodotta)` --
    e un materiale di giudizio senza pagine e' il difetto che l'etichettatore ha
    gia' segnalato una volta.
    """

    pdf = pdf.resolve()
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
    return rendered.read_text(encoding="utf-8") if rendered.is_file() else "(resa non prodotta)"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--base-rev", required=True, help="revisione git da cui si misura la differenza")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--finestra", type=int, default=20)
    arguments = parser.parse_args()

    arguments.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as raw:
        workspace = Path(raw)
        baseline = baseline_measure(arguments.base_rev, workspace)

        voci: list[tuple[str, int, str, list[str]]] = []
        for name in MANUALS:
            pdf = arguments.pdf_dir / f"{name}.pdf"
            if not pdf.is_file():
                continue
            pages, indices = capture(pdf, arguments.finestra)
            if not pages:
                continue
            font = body_font([p for page in pages for p in page.text_primitives])
            before = items_by_page(pages, indices, list_markers(baseline(pages, font)))
            after = items_by_page(pages, indices, list_markers(measure_document_line_starts(pages, font)))
            with fitz.open(pdf) as document:
                for index in sorted(set(before) | set(after)):
                    added = Counter(after.get(index, [])) - Counter(before.get(index, []))
                    if added:
                        # Il numero **stampato**, che il documento dichiara o che
                        # il ramo 3 deduce: e' quello che il lettore vede.
                        label = (document[index].get_label() or "").strip() or "?"
                        voci.append((name, index, label, list(added.elements())))

        lines = [
            "# Giudizio — sono voci d'elenco?",
            "",
            f"{sum(len(v) for _n, _i, _l, v in voci)} voci su {len(voci)} pagine.",
            "",
            "Per ogni pagina trovi la **resa completa** e sotto le righe da giudicare.",
            "Per ognuna: `voce d'elenco`, `non voce`, oppure `incerto`.",
            "",
            "`incerto` è una risposta piena: usalo quando la pagina non basta a decidere,",
            "e scrivi che cosa ti manca. Una riserva accanto a un'etichetta netta",
            "viene contata come `incerto`.",
            "",
            "---",
            "",
        ]
        for position, (name, index, label, texts) in enumerate(voci, start=1):
            pdf = arguments.pdf_dir / f"{name}.pdf"
            lines.append(f"## Pagina {position:02d} — {name}, pagina stampata «{label}»")
            lines.append("")
            lines.append("### La resa")
            lines.append("")
            lines.append("```markdown")
            lines.append(render(pdf, index, workspace).rstrip())
            lines.append("```")
            lines.append("")
            lines.append("### Le righe da giudicare")
            lines.append("")
            for order, text in enumerate(texts, start=1):
                lines.append(f"{position:02d}.{order}  `{text}`")
            lines.append("")
        (arguments.out / "GIUDIZIO_voci.md").write_text("\n".join(lines), encoding="utf-8")
        print(f"{sum(len(v) for _n, _i, _l, v in voci)} voci su {len(voci)} pagine → {arguments.out / 'GIUDIZIO_voci.md'}")


if __name__ == "__main__":
    main()
