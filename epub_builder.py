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
import re
import statistics

# Rimuove trattini di sillabazione da fine riga:
# 'affronta- re' → 'affrontare', 'parola- continuazione' → 'parolacontinuazione'
# Agisce solo se sia il char prima del trattino che quello dopo sono lettere
# minuscole (incluse accentate): non tocca compound-word, em-dash, ecc.
_HYPHEN_RE = re.compile(
    r'([a-z\u00e0-\u00fc\u00df])-\s+([a-z\u00e0-\u00fc\u00df])'
)


def _dehyphenate(text: str) -> str:
    """Rimuove i trattini di sillabazione da fine riga PDF."""
    return _HYPHEN_RE.sub(r'\1\2', text)

from pathlib import Path
from typing import List, Optional, Tuple

from ebooklib import epub

from config import LayoutConfig
from extractor import ImageBlock, PageData, TableBlock, TextBlock, VectorBlock


_ANCHOR_SLUG_RE = re.compile(r'[^a-z0-9]+')
_anchor_counter: list = [0]


def _anchor_id(text: str) -> str:
    """Genera un id HTML stabile per un heading (slug + contatore)."""
    _anchor_counter[0] += 1
    slug = _ANCHOR_SLUG_RE.sub('-', text.lower().strip())[:35].strip('-')
    return f"h{_anchor_counter[0]}-{slug}"


class EPUBBuilder:
    def __init__(self, config: LayoutConfig, title: str, author: str = ""):
        self.config = config
        self.title = title
        self.author = author
        self.out_dir = Path(config.output_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        # Nome cartella estratti (solo il nome, non il path completo)
        self.extracted_dir = "extracted"

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
        heading_map: dict = {}  # testo_heading → (file_name, anchor_id)

        for ch_idx, (ch_title, ch_pages) in enumerate(chapters_data):
            ch_file = f"chap_{ch_idx:03d}.xhtml"
            body = self._render_chapter(
                ch_pages, threshold,
                heading_map=heading_map,
                chapter_file=ch_file,
            )

            if not body.strip():
                first = ch_pages[0].page_num + 1 if ch_pages else "?"
                body = f'<p><em>[Pagina {first} — nessun testo estratto]</em></p>'

            ch = epub.EpubHtml(
                title=ch_title,
                file_name=ch_file,
                lang="it",
            )
            ch.content = self._wrap_xhtml(ch_title, body).encode("utf-8")
            ch.add_item(css)
            book.add_item(ch)
            epub_chapters.append(ch)

        # Pagina TOC navigabile in cima all'EPUB
        toc_ch = self._build_toc_chapter(toc, epub_chapters, heading_map, css)
        book.add_item(toc_ch)

        # Nested book.toc per e-reader (usa livelli PDF se disponibili)
        book.toc = self._build_epub_toc(toc, epub_chapters, heading_map)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ["nav", toc_ch] + epub_chapters

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

    def _render_chapter(
        self,
        pages: List[PageData],
        threshold: float,
        heading_map: dict = None,
        chapter_file: str = "",
    ) -> str:
        parts = []
        # note_entries: lista di (note_id, fname, descrizione) per le note a fine capitolo
        note_entries = []
        note_counter = [0]  # lista per mutabilità nel loop

        def _next_note_id(fname: str) -> str:
            note_counter[0] += 1
            slug = fname.replace(".", "-").replace("_", "-")[:30]
            return f"{slug}-{note_counter[0]}"

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
                    parts.append(self._render_text(
                        elem, threshold, heading_map, chapter_file
                    ))
                elif kind == "image":
                    fname = Path(elem.saved_path).name if elem.saved_path else f"img_{elem.index+1}"
                    note_id = None
                    if elem.description:
                        note_id = _next_note_id(fname)
                        note_entries.append((note_id, fname, elem.description))
                    parts.append(self._render_image(elem, note_id=note_id))
                elif kind == "vector":
                    fname = Path(elem.saved_path).name if elem.saved_path else f"vec_{elem.index+1}"
                    note_id = None
                    if elem.description:
                        note_id = _next_note_id(fname)
                        note_entries.append((note_id, fname, elem.description))
                    parts.append(self._render_vector(elem, note_id=note_id))
                elif kind == "table":
                    parts.append(self._render_table(elem))

        body = "\n".join(p for p in parts if p)

        # Aggiungi sezione note a fine capitolo se ci sono descrizioni
        if note_entries:
            notes_html = ['<div class="notes-section"><h4>Note alle illustrazioni</h4><ol>']
            for note_id, fname, desc in note_entries:
                esc_desc = html.escape(desc)
                esc_fname = html.escape(fname)
                notes_html.append(
                    f'<li id="note-{note_id}">'
                    f'<span class="note-fname"><code>{esc_fname}</code></span> '
                    f'<a href="#ref-{note_id}" class="note-backref">↩</a><br/>'
                    f'{esc_desc}'
                    f'</li>'
                )
            notes_html.append('</ol></div>')
            body = body + "\n" + "\n".join(notes_html)

        return body

    def _render_text(
        self,
        block: TextBlock,
        threshold: float,
        heading_map: dict = None,
        chapter_file: str = "",
    ) -> str:
        """
        Renderizza un blocco di testo.
        heading_map: se fornito, raccoglie {testo_heading: (chapter_file, anchor_id)}
        per costruire il TOC navigabile.
        """
        txt = html.escape(_dehyphenate(block.text))
        if not txt.strip():
            return ""
        size = block.avg_font_size
        if size >= threshold * 1.6:
            aid = _anchor_id(block.text)
            if heading_map is not None:
                heading_map[block.text.strip()] = (chapter_file, aid)
            return f'<h1 id="{aid}">{txt}</h1>'
        elif size >= threshold * 1.3:
            aid = _anchor_id(block.text)
            if heading_map is not None:
                heading_map[block.text.strip()] = (chapter_file, aid)
            return f'<h2 id="{aid}">{txt}</h2>'
        elif size >= threshold:
            aid = _anchor_id(block.text)
            if heading_map is not None:
                heading_map[block.text.strip()] = (chapter_file, aid)
            return f'<h3 id="{aid}">{txt}</h3>'
        elif block.is_bold and block.is_italic:
            return f'<p><strong><em>{txt}</em></strong></p>'
        elif block.is_bold:
            return f'<p><strong>{txt}</strong></p>'
        elif block.is_italic:
            return f'<p><em>{txt}</em></p>'
        else:
            return f'<p>{txt}</p>'

    def _render_image(self, img: ImageBlock, note_id: str = None) -> str:
        """
        Blocco di riferimento per immagine raster.
        Se la descrizione AI è disponibile, aggiunge un link [📷] alla nota a fine capitolo.
        """
        fname = Path(img.saved_path).name if img.saved_path else f"img_{img.index+1}.{img.ext}"
        ref   = html.escape(f"{self.extracted_dir}/images/{fname}")

        note_link = ""
        if img.description and note_id:
            short = Path(fname).stem
            note_link = f' <a href="#note-{note_id}" id="ref-{note_id}" class="note-ref">[{html.escape(short)}]</a>'

        return (
            f'<div class="asset-ref-block">\n'
            f'  <p class="asset-label">&#128444; Immagine raster{note_link}</p>\n'
            f'  <p class="asset-path"><code>{ref}</code></p>\n'
            f'</div>'
        )

    def _render_vector(self, vec: VectorBlock, note_id: str = None) -> str:
        """
        Blocco di riferimento per illustrazione vettoriale (SVG).
        """
        fname = Path(vec.saved_path).name if vec.saved_path else f"vec_{vec.index+1}.svg"
        ref   = html.escape(f"{self.extracted_dir}/vectors/{fname}")

        note_link = ""
        if vec.description and note_id:
            short = Path(fname).stem
            note_link = f' <a href="#note-{note_id}" id="ref-{note_id}" class="note-ref">[{html.escape(short)}]</a>'

        return (
            f'<div class="asset-ref-block">\n'
            f'  <p class="asset-label">&#9672; Illustrazione vettoriale{note_link}</p>\n'
            f'  <p class="asset-path"><code>{ref}</code></p>\n'
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
    # TOC navigabile e anchor ID
    # -----------------------------------------------------------------------

    def _build_toc_chapter(
        self,
        toc: list,
        epub_chapters,
        heading_map: dict,
        css,
    ):
        """
        Crea una pagina XHTML "Indice" con link cliccabili ai capitoli.
        Usa la TOC embedded del PDF se disponibile (con livelli gerarchici),
        altrimenti lista piatta dei capitoli EPUB.
        """
        items = []
        if toc:
            # Mappa titolo capitolo → file (per livello 1)
            ch_map = {ch.title: ch.file_name for ch in epub_chapters}
            for level, title, _ in toc:
                esc_title = html.escape(title)
                if level == 1:
                    fname = ch_map.get(title, epub_chapters[0].file_name if epub_chapters else "#")
                    items.append(
                        f'<p class="toc-l1"><a href="{html.escape(fname)}">{esc_title}</a></p>'
                    )
                else:
                    # Cerca l'anchor nel heading_map per link diretto alla sezione
                    entry = heading_map.get(title)
                    if entry:
                        fname, aid = entry
                        href = f"{html.escape(fname)}#{aid}"
                        indent_class = f"toc-l{min(level, 3)}"
                        items.append(
                            f'<p class="{indent_class}"><a href="{href}">{esc_title}</a></p>'
                        )
                    else:
                        indent_class = f"toc-l{min(level, 3)}"
                        items.append(f'<p class="{indent_class}">{esc_title}</p>')
        else:
            # Nessuna TOC PDF: lista piatta dei capitoli EPUB
            for ch in epub_chapters:
                esc = html.escape(ch.title)
                items.append(
                    f'<p class="toc-l1"><a href="{html.escape(ch.file_name)}">{esc}</a></p>'
                )

        body = '<h1>Indice</h1>\n' + "\n".join(items)
        ch = epub.EpubHtml(title="Indice", file_name="toc_page.xhtml", lang="it")
        ch.content = self._wrap_xhtml("Indice", body).encode("utf-8")
        ch.add_item(css)
        return ch

    def _build_epub_toc(self, toc: list, epub_chapters, heading_map: dict):
        """
        Costruisce book.toc con struttura annidata per la navigazione e-reader.
        Usa la TOC PDF con livelli se disponibile.
        """
        if not toc:
            return tuple(epub_chapters)

        ch_map = {ch.title: ch.file_name for ch in epub_chapters}
        result = []
        current_l1 = None
        current_children = []

        def flush():
            if current_l1 is None:
                return
            if current_children:
                result.append((current_l1, current_children[:]))
            else:
                result.append(current_l1)

        for level, title, _ in toc:
            if level == 1:
                flush()
                current_children = []
                fname = ch_map.get(title)
                if fname:
                    current_l1 = epub.Link(fname, title, _anchor_id(title))
                else:
                    current_l1 = epub.Section(title)
            else:
                entry = heading_map.get(title)
                if entry:
                    fname, aid = entry
                    href = f"{fname}#{aid}"
                    current_children.append(
                        epub.Link(href, title, _anchor_id(title))
                    )
        flush()
        return tuple(result) if result else tuple(epub_chapters)

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

/* Pagina Indice / TOC navigabile */
p.toc-l1 { margin: 0.5em 0; font-size: 1em; font-weight: bold; }
p.toc-l2 { margin: 0.2em 0 0.2em 1.5em; font-size: 0.95em; }
p.toc-l3 { margin: 0.1em 0 0.1em 3em; font-size: 0.9em; color: #444; }
p.toc-l1 a, p.toc-l2 a, p.toc-l3 a { text-decoration: none; color: inherit; }

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
/* Note alle illustrazioni */
a.note-ref { font-size: 0.8em; vertical-align: super; text-decoration: none; color: #2a6ebb; }
div.notes-section { border-top: 1px solid #ccc; margin-top: 2em; padding-top: 1em; }
div.notes-section h4 { font-size: 0.9em; color: #666; margin-bottom: 0.5em; }
div.notes-section ol { font-size: 0.82em; line-height: 1.5; padding-left: 1.5em; }
div.notes-section li { margin-bottom: 0.8em; }
span.note-fname { font-size: 0.85em; color: #888; }
a.note-backref { text-decoration: none; color: #2a6ebb; font-size: 0.85em; }
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



