"""Conta le occorrenze immagine che escono dal rettangolo della pagina.

Nasce dal crash trovato dal campione cieco di Criterio_UscitaIR2Minima su
Wil idx 71: un'occorrenza a x 699-1284 su una pagina larga 581, senza xref
risolvibile, manda il ramo `rasterized_clip` della fetta verticale a
rasterizzare un clip vuoto.

Distingue due popolazioni che NON vanno confuse:

- **interamente fuori**: intersezione vuota con la pagina. Non contribuisce un
  solo pixel alla pagina resa, quindi non e' contenuto. Fatto, non politica.
- **parzialmente fuori**: al vivo. E' impaginazione normale -- le illustrazioni
  a filo margine si stampano debordanti -- e va RITAGLIATA, mai scartata.

Il secondo numero e' la ragione per cui la correzione ingenua («scarta cio' che
esce dalla pagina») distruggerebbe meta' degli asset di un manuale.

Read-only, nessuna scrittura.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import fitz


def scan_document(path: Path) -> dict[str, object]:
    document = fitz.open(path)
    total = 0
    fully_outside = 0
    partially_outside = 0
    pages_with_fully_outside: set[int] = set()

    for page_index in range(len(document)):
        page = document[page_index]
        page_rect = page.rect
        for info in page.get_image_info(hashes=False, xrefs=True):
            bbox = fitz.Rect(info["bbox"])
            total += 1
            intersection = bbox & page_rect
            if intersection.is_empty:
                fully_outside += 1
                pages_with_fully_outside.add(page_index)
            elif abs(intersection.get_area() - bbox.get_area()) > 1.0:
                partially_outside += 1

    return {
        "pages": len(document),
        "occurrences": total,
        "fully_outside": fully_outside,
        "partially_outside": partially_outside,
        "pages_with_fully_outside": sorted(pages_with_fully_outside),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--manuals", nargs="+", required=True)
    args = parser.parse_args()

    for name in args.manuals:
        path = args.pdf_dir / f"{name}.pdf"
        if not path.is_file():
            print(f"MANCANTE: {path}")
            continue
        result = scan_document(path)
        occurrences = max(1, int(result["occurrences"]))
        fully = int(result["fully_outside"])
        partially = int(result["partially_outside"])
        pages_with = list(result["pages_with_fully_outside"])
        print(f"{name}: {result['pages']} pagine, {result['occurrences']} occorrenze")
        print(
            f"  interamente fuori: {fully} "
            f"({fully / occurrences:.1%}) su {len(pages_with)} pagine"
        )
        print(f"  parzialmente fuori (al vivo): {partially} ({partially / occurrences:.1%})")
        print(f"  indici 0-based con occorrenze interamente fuori: {pages_with[:20]}")


if __name__ == "__main__":
    main()
