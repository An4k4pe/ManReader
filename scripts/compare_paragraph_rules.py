"""Le due regole di paragrafo a confronto, sulla stessa pagina e sullo stesso ordine.

Diagnostico, nessuna modifica alla produzione. Serve a
`Criterio_RotturaParagrafo_v1.md`: mette accanto la regola **lessicale** oggi in
produzione (`ir2_builder.breaks_paragraph`, che rompe quando la riga successiva
non comincia in minuscola) e la regola a **blocco** (blocco nuovo → paragrafo
nuovo), che il progetto aveva gia' ratificato in
`Criterio_ParagrafoDaBlocco_v1.md` e poi abbandonato sull'evidenza di una pagina.

Le due segmentazioni ricevono **lo stesso ordine di lettura** e la **stessa
giunzione** (``join_lines``, quindi la stessa sillabazione): l'unica variabile e'
dove si rompe. Un confronto che cambiasse anche l'ordine misurerebbe due cose.

Il ``block_index`` non e' un dato nuovo: sta gia' in ogni
``source_observation_id`` (``text:b{block}:l{line}:s{span}``) ed e' gia' portato
da ``_SourceLine.block``, che oggi nessuno legge.

Uso::

    ./venv/bin/python scripts/compare_paragraph_rules.py \\
        --pdf DB.pdf --page-number 99 --out confronto.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
for entry in (str(PROJECT_ROOT), str(SCRIPTS_DIR)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from compare_reading_order_with_column_bands import _tree_aware_order  # noqa: E402
from prototype_vertical_slice_page import _tree_rows_from_contract  # noqa: E402

from ir2_builder import (  # noqa: E402
    _STARTS_LOWERCASE,
    group_source_lines,
    join_lines,
)
from page_analysis_column_band import (  # noqa: E402
    build_column_band_page_analysis_with_measurements,
)
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402


def _lexical(previous, following) -> bool:
    """La regola lessicale com'era in produzione prima di
    `Criterio_RotturaParagrafo_v2.md`. Riprodotta qui perche' il confronto
    resti eseguibile dopo che la produzione e' cambiata."""

    previous_text = previous.text.rstrip()
    text = following.text.lstrip()
    if not text:
        return False
    if previous_text.endswith(":") and re.match(r"^[-\u2022\u25cf\u25c6\d]", text):
        return True
    if not _STARTS_LOWERCASE.match(text):
        return True
    return previous_text.endswith((".", ";", "!", "?"))


def _segment(lines: list, breaks) -> list[str]:
    """Assembla i paragrafi con la regola data. `breaks(prev_line, next_line) -> bool`."""

    paragraphs: list[str] = []
    pending = ""
    previous = None
    for line in lines:
        if previous is None:
            pending = line.text
            previous = line
            continue
        if breaks(previous, line):
            paragraphs.append(pending.strip())
            pending = line.text
        else:
            pending = join_lines(pending, line.text)
        previous = line
    if previous is not None:
        paragraphs.append(pending.strip())
    return [p for p in paragraphs if p]


def source_lines_in_reading_order(pdf_path: Path, page_number: int) -> list:
    page_index = page_number - 1
    page_id = f"page:{page_number:04d}"
    with fitz.open(pdf_path) as document:
        page = document[page_index]
        if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
            print("page guard: rotation o mediabox != cropbox", file=sys.stderr)
            raise SystemExit(3)
        capture = capture_pymupdf_page(
            page,
            source_id="diagnostic-source",
            page_id=page_id,
            capture_id=f"rules:pymupdf:{page_id}",
        )
        primitive_page = normalize_backend_page_capture(capture)

    analysis, measures = build_column_band_page_analysis_with_measurements(
        primitive_page, generation_id=f"generation:rules:{page_number:04d}"
    )
    tree = _tree_rows_from_contract(analysis.candidates, measures)
    ordered, _inside = _tree_aware_order(list(primitive_page.text_primitives), tree)
    return group_source_lines([primitive for primitive, _group in ordered])


_TERMINATORS = (".", ";", "!", "?", ":", "…", "\u201d", "\u00bb", ")")


def truncated(paragraphs: list[str]) -> int:
    """Paragrafi che finiscono a meta' frase: proxy dell'ECCESSO di rotture.

    Punto cieco dichiarato: **non vede le fusioni**. Due paragrafi uniti per
    errore finiscono entrambi bene e questo conteggio li considera sani. Misura
    quindi una sola direzione dell'errore, e va letto sapendolo.
    """

    count = 0
    for paragraph in paragraphs:
        stripped = paragraph.rstrip()
        if stripped and not stripped.endswith(_TERMINATORS):
            count += 1
    return count


def _rules(lines: list) -> dict[str, list[str]]:
    return {
        "lessicale": _segment(lines, _lexical),
        "blocco": _segment(lines, lambda a, b: a.block != b.block),
        "combinata": _segment(
            lines,
            lambda a, b: a.block != b.block
            and not _STARTS_LOWERCASE.match(b.text.lstrip()),
        ),
    }


def _summary(pdf_dir: Path, tokens: list[str]) -> None:
    totals: dict[str, list[int]] = {name: [0, 0] for name in ("lessicale", "blocco", "combinata")}
    print(f"{'pagina':<12} {'righe':>6}   " + "   ".join(f"{n:>18}" for n in totals))
    print(f"{'':<12} {'':>6}   " + "   ".join(f"{'par/troncati':>18}" for _ in totals))
    for token in tokens:
        name, _, raw_index = token.partition(":")
        index = int(raw_index)
        lines = source_lines_in_reading_order(pdf_dir / f"{name}.pdf", index + 1)
        cells = []
        for rule, paragraphs in _rules(lines).items():
            trunc = truncated(paragraphs)
            totals[rule][0] += len(paragraphs)
            totals[rule][1] += trunc
            cells.append(f"{len(paragraphs):>8} /{trunc:>3}     ")
        print(f"{name + ' ' + str(index):<12} {len(lines):>6}   " + "   ".join(cells))
    print()
    for rule, (par, trunc) in totals.items():
        share = trunc / par if par else 0.0
        print(f"  {rule:<12} paragrafi {par:>5}   troncati {trunc:>4}   ({share:.1%})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=None)
    parser.add_argument("--page-number", type=int, default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--pdf-dir", type=Path, default=None)
    parser.add_argument("--summary", nargs="+", default=None, help="Nome:idx0based ...")
    args = parser.parse_args()

    if args.summary:
        if args.pdf_dir is None:
            parser.error("--summary richiede --pdf-dir")
        _summary(args.pdf_dir, args.summary)
        return
    if args.pdf is None or args.page_number is None:
        parser.error("servono --pdf e --page-number, oppure --summary")

    lines = source_lines_in_reading_order(args.pdf, args.page_number)

    lexical = _segment(lines, _lexical)
    by_block = _segment(lines, lambda a, b: a.block != b.block)
    combined = _segment(
        lines,
        lambda a, b: a.block != b.block and not _STARTS_LOWERCASE.match(b.text.lstrip()),
    )

    out = []
    out.append(f"# {args.pdf.stem} pagina {args.page_number} — le due regole\n")
    out.append(f"Righe di sorgente nell'ordine di lettura: **{len(lines)}**.\n")
    out.append(
        f"| regola | paragrafi emessi |\n| --- | --- |\n"
        f"| lessicale (in produzione) | **{len(lexical)}** |\n"
        f"| blocco | **{len(by_block)}** |\n"
        f"| blocco + veto minuscola | **{len(combined)}** |\n"
    )
    for title, paragraphs in (
        ("Regola LESSICALE — quella in produzione", lexical),
        ("Regola A BLOCCO", by_block),
        ("Regola A BLOCCO + VETO MINUSCOLA", combined),
    ):
        out.append(f"\n## {title}\n")
        for position, paragraph in enumerate(paragraphs, start=1):
            out.append(f"{position}. {paragraph}\n")

    text = "\n".join(out)
    if args.out is None:
        print(text)
    else:
        args.out.write_text(text, encoding="utf-8")
        print(
            f"scritto {args.out}  (lessicale {len(lexical)}, "
            f"blocco {len(by_block)}, combinata {len(combined)})"
        )


if __name__ == "__main__":
    main()
