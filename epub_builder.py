"""
epub_builder.py — Assemblaggio EPUB dai dati estratti.

Scelta di design: le immagini e i vettoriali NON sono embedded nell'EPUB.
Al loro posto viene inserito un blocco di riferimento con:
  - tipo (Immagine raster / Illustrazione vettoriale / Tabella)
  - nome del file estratto nella cartella _extracted/
  - descrizione AI (se disponibile)

Motivazioni:
  - L'EPUB rimane leggero e veloce da caricare sull'e-reader
  - Le immagini di manuali GDR sono spesso grandi e ad alta risoluzione;
    embeddarle gonfia il file e può mandare in crash alcuni e-reader
  - Il riferimento testuale è annotabile e ricercabile
  - I file estratti sono accessibili separatamente per consultazione

Rilevamento capitoli:
  - Priorità: TOC embedded nel PDF (get_toc)
  - Fallback: euristica font size (mediana documento)
"""

import html
import statistics
from pathlib import Path
from typing import List, Optional, Tuple

from ebooklib import epub

from config import LayoutConfig
from extractor import ImageBlock, PageData, TableBlock, TextBlock, VectorBlock


class EPUBBuilder:
    def __init__(self, config: LayoutConfig, title: str, author: str = ""):
        self.config = config
        self.title = title
        self.author = author
        self.out_dir = Path(config.output_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        # Nome cartella estratti (solo il nome, non il path completo)
        self.extracted_dir = f"{config.book_name}_extracted"

    # -----------------------------------------------------------------------
    # Entry point
    # -----------------------------------------------------------------------

    def build(self, pages: List[PageData], toc: list = None) -> Path:
        book = epub.EpubBook()
        book.set_title(self.title)
        if self.author:
            book.add_author(self.author)
        book.set_language("it")
        book.set_identifier(f"gdr-{self.config.book_name}")

        css = epub.EpubItem(
            uid="style_main",
            file_name="style.css",
            media_type="text/css",
            content=self._css().encode("utf-8"),
        )
        book.add_item(css)

        median_size = self._compute_median_font_size(pages)
        threshold = median_size * self.config.heading_font_size_threshold

        chapters_data = self._split_into_chapters(pages, threshold, toc)
        source = "TOC embedded" if toc else "euristica font"
        print(f"  Capitoli rilevati: {len(chapters_data)} (via {source})")

        epub_chapters = []
        for ch_idx, (ch_title, ch_pages) in enumerate(chapters_data):
            body = self._render_chapter(ch_pages, threshold)

            if not body.strip():
                first = ch_pages[0].page_num + 1 if ch_pages else "?"
                body = f'<p><em>[Pagina {first} — nessun testo estratto]</em></p>'

            ch = epub.EpubHtml(
                title=ch_title,
                file_name=f"chap_{ch_idx:03d}.xhtml",
                lang="it",
            )
            ch.content = self._wrap_xhtml(ch_title, body).encode("utf-8")
            ch.add_item(css)
            book.add_item(ch)
            epub_chapters.append(ch)

        book.toc = tuple(epub_chapters)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ["nav"] + epub_chapters

        out_path = self.out_dir / f"{self.config.book_name}.epub"
        epub.write_epub(str(out_path), book)
        return out_path

    # -----------------------------------------------------------------------
    # Capitoli
    # -----------------------------------------------------------------------

    def _compute_median_font_size(self, pages: List[PageData]) -> float:
        sizes = [
            b.avg_font_size
            for p in pages
            for b in p.text_blocks
            if b.avg_font_size > 0
        ]
        return statistics.median(sizes) if sizes else 10.0

    def _split_into_chapters(
        self, pages: List[PageData], threshold: float, toc: list = None
    ) -> List[Tuple[str, List[PageData]]]:
        if toc:
            return self._split_by_toc(pages, toc)
        return self._split_by_font_size(pages, threshold)

    def _split_by_toc(
        self, pages: List[PageData], toc: list
    ) -> List[Tuple[str, List[PageData]]]:
        page_nums = {p.page_num for p in pages}
        levels = [lv for lv, _, pg in toc if pg in page_nums]
        if not levels:
            return [(self.title, pages)]

        chapter_level = min(levels)
        starts = {
            pg: title
            for lv, title, pg in toc
            if lv == chapter_level and pg in page_nums
        }

        chapters, current_title, current_pages = [], self.title, []
        for page in pages:
            if page.page_num in starts:
                if current_pages:
                    chapters.append((current_title, current_pages))
                current_title = starts[page.page_num]
                current_pages = [page]
            else:
                current_pages.append(page)
        if current_pages:
            chapters.append((current_title, current_pages))
        return chapters if chapters else [(self.title, pages)]

    def _split_by_font_size(
        self, pages: List[PageData], threshold: float
    ) -> List[Tuple[str, List[PageData]]]:
        chapters, current_title, current_pages = [], self.title, []
        for page in pages:
            if page.text_blocks:
                first = page.text_blocks[0]
                if (first.avg_font_size >= threshold * 1.6
                        and len(first.text.strip()) < 100):
                    if current_pages:
                        chapters.append((current_title, current_pages))
                    current_title = first.text.strip()
                    current_pages = [page]
                    continue
            current_pages.append(page)
        if current_pages:
            chapters.append((current_title, current_pages))
        return chapters if chapters else [(self.title, pages)]

    # -----------------------------------------------------------------------
    # Rendering HTML
    # -----------------------------------------------------------------------

    def _render_chapter(self, pages: List[PageData], threshold: float) -> str:
        parts = []
        for page in pages:
            # Unifica tutti gli elementi per Y-position
            elements = []
            for b in page.text_blocks:
                elements.append(("text",   b.bbox[1], b))
            for img in page.images:
                # Sfondi e duplicati: salvati su disco ma silenziosi nell'EPUB
                if not img.is_background and not img.is_duplicate:
                    elements.append(("image",  img.bbox[1], img))
            for vec in page.vectors:
                elements.append(("vector", vec.bbox[1], vec))
            for tbl in page.tables:
                elements.append(("table",  tbl.bbox[1], tbl))

            elements.sort(key=lambda x: x[1])

            for kind, _, elem in elements:
                if kind == "text":
                    parts.append(self._render_text(elem, threshold))
                elif kind == "image":
                    parts.append(self._render_image(elem))
                elif kind == "vector":
                    parts.append(self._render_vector(elem))
                elif kind == "table":
                    parts.append(self._render_table(elem))

        return "\n".join(p for p in parts if p)

    def _render_text(self, block: TextBlock, threshold: float) -> str:
        txt = html.escape(block.text)
        if not txt.strip():
            return ""
        size = block.avg_font_size
        if size >= threshold * 1.6:
            return f'<h1>{txt}</h1>'
        elif size >= threshold * 1.3:
            return f'<h2>{txt}</h2>'
        elif size >= threshold:
            return f'<h3>{txt}</h3>'
        elif block.is_bold and block.is_italic:
            return f'<p><strong><em>{txt}</em></strong></p>'
        elif block.is_bold:
            return f'<p><strong>{txt}</strong></p>'
        elif block.is_italic:
            return f'<p><em>{txt}</em></p>'
        else:
            return f'<p>{txt}</p>'

    def _render_image(self, img: ImageBlock) -> str:
        """
        Blocco di riferimento per immagine raster.
        Non viene embedded: il file è nella cartella _extracted/images/.
        """
        fname = Path(img.saved_path).name if img.saved_path else f"img_{img.index+1}.{img.ext}"
        desc  = html.escape(img.description or "")
        ref   = html.escape(f"{self.extracted_dir}/images/{fname}")

        desc_line = f'\n  <p class="asset-desc">{desc}</p>' if desc else ""
        return (
            f'<div class="asset-ref-block">\n'
            f'  <p class="asset-label">&#128444; Immagine raster</p>\n'
            f'  <p class="asset-path"><code>{ref}</code></p>'
            f'{desc_line}\n'
            f'</div>'
        )

    def _render_vector(self, vec: VectorBlock) -> str:
        """
        Blocco di riferimento per illustrazione vettoriale (SVG).
        """
        fname = Path(vec.saved_path).name if vec.saved_path else f"vec_{vec.index+1}.svg"
        desc  = html.escape(vec.description or "")
        ref   = html.escape(f"{self.extracted_dir}/vectors/{fname}")

        desc_line = f'\n  <p class="asset-desc">{desc}</p>' if desc else ""
        return (
            f'<div class="asset-ref-block">\n'
            f'  <p class="asset-label">&#9672; Illustrazione vettoriale</p>\n'
            f'  <p class="asset-path"><code>{ref}</code></p>'
            f'{desc_line}\n'
            f'</div>'
        )

    def _render_table(self, tbl: TableBlock) -> str:
        """
        Le tabelle vengono renderizzate inline come HTML (gli e-reader le
        supportano) E riportano il riferimento al CSV esterno.
        """
        if not tbl.rows:
            return ""

        rows_html = []
        for i, row in enumerate(tbl.rows):
            cells = []
            for cell in row:
                txt = html.escape(cell)
                tag = "th" if i == 0 else "td"
                cells.append(f"<{tag}>{txt}</{tag}>")
            rows_html.append(f"<tr>{''.join(cells)}</tr>")

        fname = Path(tbl.saved_path).name if tbl.saved_path else f"tbl_{tbl.index+1}.csv"
        desc  = html.escape(tbl.description or "")
        ref   = html.escape(f"{self.extracted_dir}/tables/{fname}")

        desc_line = f'<p class="asset-desc">{desc}</p>\n' if desc else ""
        return (
            f'<div class="tbl-block">\n'
            f'<table>\n{"".join(rows_html)}\n</table>\n'
            f'{desc_line}'
            f'<p class="asset-path"><code>{ref}</code></p>\n'
            f'</div>'
        )

    # -----------------------------------------------------------------------
    # CSS
    # -----------------------------------------------------------------------

    def _css(self) -> str:
        return """\
body {
    font-family: Georgia, "Times New Roman", serif;
    font-size: 1em;
    line-height: 1.65;
    margin: 0.8em 1em;
    color: #111;
    background: transparent;
}
h1 {
    font-size: 1.7em;
    line-height: 1.2;
    margin: 1.8em 0 0.5em;
    page-break-before: always;
    border-bottom: 1px solid #555;
    padding-bottom: 0.2em;
}
h2 { font-size: 1.35em; margin: 1.4em 0 0.4em; }
h3 { font-size: 1.1em;  margin: 1.1em 0 0.3em; }
p  { margin: 0.35em 0; text-align: justify; orphans: 2; widows: 2; }

/* Blocchi di riferimento asset */
div.asset-ref-block {
    margin: 1em 0;
    padding: 0.5em 0.8em;
    border-left: 3px solid #999;
    background: transparent;
    page-break-inside: avoid;
}
p.asset-label {
    font-size: 0.8em;
    font-weight: bold;
    color: #555;
    margin: 0 0 0.2em;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
p.asset-path {
    margin: 0.1em 0;
    font-size: 0.85em;
}
p.asset-path code {
    font-family: "Courier New", monospace;
    font-size: 0.9em;
    word-break: break-all;
}
p.asset-desc {
    margin: 0.3em 0 0;
    font-size: 0.88em;
    font-style: italic;
    color: #333;
}

/* Tabelle */
div.tbl-block {
    margin: 1.2em 0;
    page-break-inside: avoid;
}
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.88em;
    margin-bottom: 0.4em;
}
th {
    background-color: #222;
    color: #fff;
    padding: 0.35em 0.5em;
    text-align: left;
    font-weight: bold;
}
td {
    padding: 0.25em 0.5em;
    border: 1px solid #aaa;
    vertical-align: top;
}
tr:nth-child(even) td { background-color: #f2f2f2; }
"""

    # -----------------------------------------------------------------------
    # Template XHTML
    # -----------------------------------------------------------------------

    def _wrap_xhtml(self, title: str, body: str) -> str:
        esc = html.escape(title)
        return (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="it" lang="it">\n'
            '<head>\n'
            f'  <title>{esc}</title>\n'
            '  <meta charset="utf-8"/>\n'
            '  <link rel="stylesheet" type="text/css" href="style.css"/>\n'
            '</head>\n'
            f'<body>\n{body}\n</body>\n'
            '</html>'
        )
