"""
extractor.py — Estrazione strutturata da PDF.

Gestisce tre tipi di contenuto grafico:
  - Immagini raster (JPEG, PNG, JP2...): estratte direttamente dai metadati
    del PDF come file binari, salvate nel formato originale.
  - Illustrazioni vettoriali: rilevate tramite clustering dei path vettoriali
    (get_drawings), esportate come SVG ritagliando la regione su una pagina
    temporanea con show_pdf_page().
  - Tabelle: rilevate da pdfplumber, salvate come CSV.

Tutto il testo viene estratto con posizione spaziale per ricostruire l'ordine
di lettura corretto (singola o doppia colonna).

Il filtro `filter_repeated_blocks` rimuove intestazioni, piè di pagina e
filigrane identificandoli statisticamente per posizione Y e testo normalizzato.

Struttura cartelle output:
  {output_dir}/{book_name}_extracted/
      images/    ← raster (PNG, JPEG, ...)
      vectors/   ← illustrazioni vettoriali (SVG)
      tables/    ← tabelle (CSV)
"""

import io
import re as _re
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import hashlib
import fitz  # PyMuPDF
import pdfplumber
from PIL import Image

from config import LayoutConfig


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TextSpan:
    text: str
    font: str
    size: float
    bold: bool
    italic: bool
    bbox: Tuple[float, float, float, float]


@dataclass
class TextBlock:
    spans: List[TextSpan]
    bbox: Tuple[float, float, float, float]

    @property
    def text(self) -> str:
        return " ".join(s.text for s in self.spans if s.text.strip())

    @property
    def avg_font_size(self) -> float:
        sizes = [s.size for s in self.spans if s.text.strip()]
        return statistics.mean(sizes) if sizes else 0.0

    @property
    def is_bold(self) -> bool:
        return any(s.bold for s in self.spans if s.text.strip())

    @property
    def is_italic(self) -> bool:
        return all(s.italic for s in self.spans if s.text.strip())


@dataclass
class ImageBlock:
    """Immagine raster embedded nel PDF."""
    image_data: bytes
    ext: str
    bbox: Tuple[float, float, float, float]
    page_num: int
    index: int
    saved_path: Optional[str] = None
    description: Optional[str] = None
    is_background: bool = False
    """True se l'immagine copre >60% della pagina (sfondo/texture).
    Non viene aggiunta a excluded_bboxes: il testo soprastante viene conservato."""
    is_duplicate: bool = False
    """True se questo hash e gia stato salvato in una pagina precedente.
    Il file esiste gia su disco; nell'EPUB l'occorrenza viene saltata."""


@dataclass
class VectorBlock:
    """Gruppo di path vettoriali che formano un'illustrazione."""
    bbox: Tuple[float, float, float, float]
    page_num: int
    index: int
    saved_path: Optional[str] = None
    description: Optional[str] = None


@dataclass
class TableBlock:
    rows: List[List[str]]
    bbox: Tuple[float, float, float, float]
    page_num: int
    index: int
    saved_path: Optional[str] = None
    description: Optional[str] = None


@dataclass
class PageData:
    page_num: int
    text_blocks: List[TextBlock]
    images: List[ImageBlock]
    vectors: List[VectorBlock]
    tables: List[TableBlock]
    width: float
    height: float


# ---------------------------------------------------------------------------
# Rilevamento pagine sommario / indice
# ---------------------------------------------------------------------------

_TOC_LINE_RE = _re.compile(r'.{3,}\s+\d{1,3}\s*$')


def is_toc_page(page: "PageData") -> bool:
    """
    Rileva se una pagina e un sommario/indice stampato.

    Algoritmo: conta i blocchi di testo che seguono il pattern
    tipico di un indice: testo descrittivo seguito da un numero
    di pagina ("Introduzione ............ 9").
    Se piu del 40% dei blocchi ha questa struttura, la pagina
    viene classificata come indice.
    """
    if len(page.text_blocks) < 3:
        return False
    matches = sum(
        1 for b in page.text_blocks
        if _TOC_LINE_RE.search(b.text.strip())
    )
    return (matches / len(page.text_blocks)) > 0.40


# ---------------------------------------------------------------------------
# Filtro intestazioni / piè di pagina / filigrane
# ---------------------------------------------------------------------------

def _normalize_text(text: str) -> str:
    """Rimuove cifre e normalizza per confronto. 'Pagina 42' == 'Pagina 103'."""
    return _re.sub(r'\d+', '', text).strip().lower()


def filter_repeated_blocks(
    pages: List[PageData],
    header_footer_zone: float = 0.08,
    repetition_threshold: float = 0.25,
) -> List[PageData]:
    """
    Rimuove blocchi di testo che si ripetono alla stessa posizione Y su molte
    pagine (intestazioni, piè di pagina, filigrane, watermark testuali).

    Due passate:
      1. Costruisce firme (zona, testo_normalizzato) e conta occorrenze per pagina
      2. Rimuove i blocchi le cui firme superano la soglia

    Soglie asimmetriche: header/footer → 25% pagine, body → 60%.
    Il body ha soglia più alta perché nomi di abilità o titoli di tabella
    possono legittimamente ripetersi molte volte.
    """
    if not pages:
        return pages

    n = len(pages)
    min_edge = max(2, int(n * repetition_threshold))
    min_body = max(2, int(n * 0.60))

    sig_pages: dict = defaultdict(set)

    for page in pages:
        h = page.height or 1.0
        for block in page.text_blocks:
            y_norm = block.bbox[1] / h
            if y_norm < header_footer_zone:
                zone = "header"
            elif y_norm > (1.0 - header_footer_zone):
                zone = "footer"
            else:
                zone = "body"
            norm = _normalize_text(block.text)
            if norm:
                sig_pages[(zone, norm)].add(page.page_num)

    to_remove: set = set()
    for sig, pset in sig_pages.items():
        limit = min_edge if sig[0] in ("header", "footer") else min_body
        if len(pset) >= limit:
            to_remove.add(sig)

    if not to_remove:
        return pages

    removed = 0
    result = []
    for page in pages:
        h = page.height or 1.0
        clean = []
        for block in page.text_blocks:
            y_norm = block.bbox[1] / h
            zone = (
                "header" if y_norm < header_footer_zone
                else "footer" if y_norm > (1.0 - header_footer_zone)
                else "body"
            )
            norm = _normalize_text(block.text)
            if (zone, norm) in to_remove:
                removed += 1
            else:
                clean.append(block)
        result.append(PageData(
            page_num=page.page_num,
            text_blocks=clean,
            images=page.images,
            vectors=page.vectors,
            tables=page.tables,
            width=page.width,
            height=page.height,
        ))

    unique = len(to_remove)
    print(f"  Filtro ripetizioni: {unique} pattern rimossi ({removed} blocchi totali)")
    return result


# ---------------------------------------------------------------------------
# Filtro glifi decorativi e numeri di pagina
# ---------------------------------------------------------------------------

# Font simbolici/icona noti: i loro glifi vengono estratti come lettere
# normali ma rappresentano bullets, ornamenti, frecce ecc.
_SYMBOL_FONT_KEYWORDS = frozenset([
    'symbol', 'dingbat', 'wingding', 'zapf', 'webding',
    'icon', 'ornament', 'glyph', 'bullet', 'arrow',
])

# Singole lettere che non sono mai parole standalone in italiano/inglese
# (tipicamente glifi di font icona mappati su lettere ASCII)
# Escluse le vocali e 'I': possono essere articoli/congiunzioni reali
_LONE_GLYPH_CHARS = frozenset(
    'bcdfghjklmnpqrstuvwxyz'   # consonanti minuscole
    'BCDFGHJKLMNPQRSTUVWXYZ'   # consonanti maiuscole
    '0123456789'                # cifre standalone gia coperte dal check numerico
)

# Regex per caratteri non-standard che compaiono spesso come glifi decorativi:
# caratteri di controllo, PUA Unicode, simboli non comuni
import re as _noise_re


import re as _re_slug

def _desc_to_slug(description: str, max_words: int = 4) -> str:
    """
    Converte le prime max_words parole di una descrizione in uno slug
    per nome file: minuscolo, solo alfanumerici e trattini.
    Esempio: "Un sovrano su un trono" → "un-sovrano-su-un"
    """
    words = description.strip().split()[:max_words]
    slug = "-".join(words)
    slug = _re_slug.sub(r"[^\w\-]", "", slug, flags=_re_slug.UNICODE)
    slug = _re_slug.sub(r"-+", "-", slug).strip("-")
    return slug.lower() or "img"

_NONSTANDARD_CHAR_RE = _noise_re.compile(
    r'^[\x00-\x1f\x7f-\x9f\ue000-\uf8ff\u2000-\u206f\u2400-\u27ff]+$'
)


def _is_noise_block(spans: list) -> bool:
    """
    Restituisce True se il blocco e quasi certamente rumore decorativo:
      - tutti gli span usano font simbolici (Wingdings, Dingbats, ecc.)
      - oppure il testo e un singolo carattere consonante (glifo icona)
      - oppure e un numero di pagina standalone (solo cifre, 1-3 chars, bold)
    """
    if not spans:
        return True

    full_text = ' '.join(s.text for s in spans).strip()

    # Tutti gli span usano font simbolici?
    if all(
        any(kw in s.font.lower() for kw in _SYMBOL_FONT_KEYWORDS)
        for s in spans
    ):
        return True

    # Singolo carattere consonante = quasi sicuramente glifo decorativo
    if len(full_text) == 1 and full_text in _LONE_GLYPH_CHARS:
        return True

    # Numero di pagina standalone: solo cifre, 1-3 chars, bold
    if full_text.isdigit() and len(full_text) <= 3 and any(s.bold for s in spans):
        return True

    # Caratteri non-standard (PUA Unicode, simboli rari): quasi sicuramente glifi
    if len(full_text) <= 4 and _NONSTANDARD_CHAR_RE.match(full_text):
        return True

    return False


# ---------------------------------------------------------------------------
# Estrattore principale
# ---------------------------------------------------------------------------

class PDFExtractor:
    def __init__(self, pdf_path: Path, config: LayoutConfig):
        self.pdf_path = pdf_path
        self.config = config
        self.doc = fitz.open(str(pdf_path))
        self.page_count = len(self.doc)

        # Cartella estratti: output/{book_name}_extracted/
        extracted = Path(config.output_dir) / f"{config.book_name}_extracted"
        self.images_dir = extracted / "images"
        self.vectors_dir = extracted / "vectors"
        self.tables_dir  = extracted / "tables"
        for d in (self.images_dir, self.vectors_dir, self.tables_dir):
            d.mkdir(parents=True, exist_ok=True)

        # Contatori per il riepilogo finale del rilevamento colonne
        self._col_stats: dict = {1: 0, 2: 0}

        # Dedup inline immagini: hash MD5 -> path del file gia salvato
        # Evita di salvare piu volte lo stesso sfondo/texture su pagine diverse
        self._seen_image_hashes: dict = {}

    def extract_all(self, describer=None) -> List[PageData]:
        pages = []
        with pdfplumber.open(str(self.pdf_path)) as plumb:
            for i in range(self.page_count):
                print(f"  Pagina {i+1}/{self.page_count}...", end="\r", flush=True)
                pages.append(self._extract_page(i, plumb.pages[i], describer))
        print(f"  Estratte {self.page_count} pagine.             ")
        if self.config.columns is None:
            p1 = self._col_stats[1]
            p2 = self._col_stats[2]
            print(f"  Layout rilevato: {p1} pag. singola colonna, {p2} pag. doppia colonna")
        return pages

    def get_toc(self) -> List[Tuple[int, str, int]]:
        """
        Legge l'outline (bookmarks) del PDF.
        Restituisce [(livello, titolo, pagina_0based), ...].
        Lista vuota se il PDF non ha outline.
        """
        raw = self.doc.get_toc(simple=True)
        return [
            (level, title.strip(), page - 1)
            for level, title, page in raw
            if title and title.strip()
        ]

    # -----------------------------------------------------------------------
    # Estrazione per singola pagina
    # -----------------------------------------------------------------------

    def _extract_page(self, page_num: int, plumb_page, describer) -> PageData:
        fitz_page = self.doc[page_num]
        width  = fitz_page.rect.width
        height = fitz_page.rect.height

        images  = self._extract_images(fitz_page, page_num, describer)
        vectors = []
        if self.config.extract_vectors:
            vectors = self._extract_vectors(fitz_page, page_num, describer)

        tables = []
        if self.config.extract_tables:
            tables = self._extract_tables(plumb_page, page_num, describer)

        # Solo le tabelle vanno in excluded_bboxes: il loro testo e gia
        # estratto da pdfplumber e includerlo come testo libero creerebbe
        # duplicati. Immagini e vettoriali NON escludono il testo:
        # nel PDF il testo e un layer separato sopra questi elementi,
        # quindi escluderlo causerebbe la perdita di titoli nei cartigli
        # e testo sovrapposto a texture di sfondo.
        excluded = [b.bbox for b in tables]
        text_blocks = self._extract_text(fitz_page, width, excluded)

        return PageData(
            page_num=page_num,
            text_blocks=text_blocks,
            images=images,
            vectors=vectors,
            tables=tables,
            width=width,
            height=height,
        )

    # -----------------------------------------------------------------------
    # Immagini raster
    # -----------------------------------------------------------------------

    def _extract_images(self, page, page_num: int, describer) -> List[ImageBlock]:
        results = []
        book = self.config.book_name

        for idx, img_info in enumerate(page.get_images(full=True)):
            xref = img_info[0]
            try:
                raw = self.doc.extract_image(xref)
                img_bytes = raw["image"]
                ext = raw["ext"]

                # Filtra immagini troppo piccole
                try:
                    pil = Image.open(io.BytesIO(img_bytes))
                    if pil.mode == "CMYK":
                        pil = pil.convert("RGB")
                        buf = io.BytesIO()
                        pil.save(buf, format="PNG")
                        img_bytes = buf.getvalue()
                        ext = "png"
                    w, h = pil.size
                    if w < self.config.min_image_width or h < self.config.min_image_height:
                        continue
                except Exception:
                    continue

                bbox = self._get_image_bbox(page, xref)

                # Rileva se e uno sfondo: copre >60% della pagina
                page_area = page.rect.width * page.rect.height
                x0, y0, x1, y1 = bbox
                bbox_area = max((x1-x0) * (y1-y0), 1)
                is_bg = (bbox_area / page_area) > 0.60

                # Dedup inline: se questa immagine e gia stata salvata
                # in una pagina precedente, riusa il file esistente
                img_hash = hashlib.md5(img_bytes).hexdigest()
                if img_hash in self._seen_image_hashes:
                    existing_path = self._seen_image_hashes[img_hash]
                    # Recupera la descrizione già salvata dal .txt della prima occorrenza
                    cached_desc = None
                    try:
                        txt_path = Path(existing_path).with_suffix(".txt")
                        if txt_path.exists():
                            cached_desc = txt_path.read_text(encoding="utf-8").strip() or None
                    except Exception:
                        pass
                    results.append(ImageBlock(
                        image_data=b"", ext=ext, bbox=bbox,
                        page_num=page_num, index=idx,
                        saved_path=existing_path, description=cached_desc,
                        is_background=is_bg,
                        is_duplicate=True,
                    ))
                    continue

                # Nome provvisorio: verrà rinominato dopo la descrizione AI
                fname_tmp = f"{book}_p{page_num+1}_img{idx+1}.{ext}"
                save_path = self.images_dir / fname_tmp
                save_path.write_bytes(img_bytes)

                description = None
                print(f"  [debug] p{page_num+1} img{idx+1}: is_bg={is_bg}, describer={describer is not None}, bbox_area={bbox_area:.0f}, page_area={page_area:.0f}, ratio={bbox_area/page_area:.2f}")
                if describer and not is_bg:
                    print(f"  [debug] → chiamo describer per img{idx+1}")
                    description = describer.describe_image(img_bytes, ext)
                    print(f"  [debug] → descrizione: {repr(description[:60]) if description else 'None'}")
                    # Rinomina il file usando le prime 4 parole della descrizione
                    if description:
                        slug = _desc_to_slug(description, max_words=4)
                        fname = f"{book}_p{page_num+1}_{slug}.{ext}"
                        new_path = self.images_dir / fname
                        # Evita collisioni aggiungendo suffisso numerico
                        counter = 1
                        while new_path.exists():
                            fname = f"{book}_p{page_num+1}_{slug}_{counter}.{ext}"
                            new_path = self.images_dir / fname
                            counter += 1
                        save_path.rename(new_path)
                        save_path = new_path
                        save_path.with_suffix(".txt").write_text(description, encoding="utf-8")
                    else:
                        fname = fname_tmp  # mantieni nome numerico se no descrizione

                self._seen_image_hashes[img_hash] = str(save_path)

                results.append(ImageBlock(
                    image_data=img_bytes, ext=ext, bbox=bbox,
                    page_num=page_num, index=idx,
                    saved_path=str(save_path), description=description,
                    is_background=is_bg,
                ))
            except Exception as e:
                print(f"\n  [warn] immagine p{page_num+1} #{idx}: {e}")

        return results

    def _get_image_bbox(self, page, xref: int) -> Tuple[float, float, float, float]:
        try:
            rects = list(page.get_image_rects(xref))
            if rects:
                r = rects[0]
                return (r.x0, r.y0, r.x1, r.y1)
        except Exception:
            pass
        return (0.0, 0.0, page.rect.width, page.rect.height)

    # -----------------------------------------------------------------------
    # Illustrazioni vettoriali
    # -----------------------------------------------------------------------

    def _extract_vectors(self, page, page_num: int, describer) -> List[VectorBlock]:
        """
        Rileva gruppi di path vettoriali che formano illustrazioni, li esporta
        come SVG ritagliando la regione dal PDF.

        Pipeline:
          1. get_drawings() → tutti i path della pagina
          2. Filtra path troppo piccoli o che coprono l'intera pagina
             (bordi, linee di separazione)
          3. Clustering union-find sui bounding box espansi di 5pt:
             path vicini appartengono alla stessa illustrazione
          4. Filtra cluster sotto la dimensione minima
          5. Per ogni cluster: show_pdf_page con clip → get_svg_image
        """
        results = []
        book = self.config.book_name
        pw, ph = page.rect.width, page.rect.height
        min_sz = self.config.min_vector_size

        drawings = page.get_drawings()
        if not drawings:
            return results

        # Filtra path irrilevanti:
        # - coprono >70% di larghezza o altezza della pagina → bordi/linee
        # - area < 4pt² → punti/tratti invisibili
        def is_relevant(d) -> bool:
            r = fitz.Rect(d["rect"])
            if r.is_empty or r.width * r.height < 4:
                return False
            if r.width > pw * 0.70 or r.height > ph * 0.70:
                return False
            return True

        relevant = [d for d in drawings if is_relevant(d)]
        if not relevant:
            return results

        # Union-Find clustering
        n = len(relevant)
        parent = list(range(n))
        margin = 5.0

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x: int, y: int) -> None:
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        # Espandi i bbox di un margine prima di confrontarli
        expanded = [
            fitz.Rect(fitz.Rect(d["rect"]).x0 - margin,
                      fitz.Rect(d["rect"]).y0 - margin,
                      fitz.Rect(d["rect"]).x1 + margin,
                      fitz.Rect(d["rect"]).y1 + margin)
            for d in relevant
        ]

        for i in range(n):
            for j in range(i + 1, n):
                if expanded[i].intersects(expanded[j]):
                    union(i, j)

        # Raggruppa e calcola bbox unione per ogni cluster
        clusters: dict = defaultdict(list)
        for i, d in enumerate(relevant):
            clusters[find(i)].append(fitz.Rect(d["rect"]))

        # Esporta i cluster che superano la dimensione minima
        vec_idx = 0
        for bbox_list in clusters.values():
            merged = fitz.Rect()
            for r in bbox_list:
                merged |= r
            # Scarta bbox degeneri (area zero o non finiti) che causano
            # "clip must be finite and not empty" in get_svg_image
            if merged.is_empty or merged.is_infinite:
                continue
            if merged.width < min_sz or merged.height < min_sz:
                continue

            # Escludi se sovrapposto a immagine raster già estratta
            # (verifica fatta a posteriori nell'_extract_page, qui non abbiamo
            # ancora quella lista — la gestione overlap è nel chiamante)

            fname = f"{book}_p{page_num+1}_vec{vec_idx+1}.svg"
            save_path = self.vectors_dir / fname
            bbox_tuple = (merged.x0, merged.y0, merged.x1, merged.y1)

            ok = self._export_region_as_svg(page_num, merged, save_path)
            if not ok:
                continue

            # Descrizione AI: renderizza come PNG e invia all'API
            description = None
            if describer:
                thumb = self._render_region_as_png(page_num, merged)
                if thumb:
                    description = describer.describe_image(thumb, "png")
                    save_path.with_suffix(".txt").write_text(description, encoding="utf-8")

            results.append(VectorBlock(
                bbox=bbox_tuple,
                page_num=page_num,
                index=vec_idx,
                saved_path=str(save_path),
                description=description,
            ))
            vec_idx += 1

        return results

    def _export_region_as_svg(self, page_num: int, clip: fitz.Rect, save_path: Path) -> bool:
        """
        Esporta una regione della pagina come SVG.

        Tecnica: crea un documento temporaneo di una pagina delle dimensioni
        della clip region, ci mappa il contenuto PDF originale con
        show_pdf_page(), poi chiama get_svg_image() sulla pagina risultante.
        Questo preserva la grafica vettoriale (path, curve, font embedded)
        senza rasterizzare.
        """
        if clip.is_empty or clip.width < 5 or clip.height < 5:
            return False
        try:
            tmp = fitz.open()
            tmp_page = tmp.new_page(width=clip.width, height=clip.height)
            tmp_page.show_pdf_page(
                tmp_page.rect,
                self.doc,
                page_num,
                clip=clip,
            )
            svg = tmp_page.get_svg_image()
            tmp.close()
            save_path.write_text(svg, encoding="utf-8")
            return True
        except Exception as e:
            print(f"\n  [warn] SVG export p{page_num+1}: {e}")
            return False

    def _render_region_as_png(self, page_num: int, clip: fitz.Rect) -> Optional[bytes]:
        """
        Renderizza una regione come PNG (per le descrizioni AI).
        Non serve alta risoluzione: 2x è sufficiente per la comprensione.
        """
        try:
            page = self.doc[page_num]
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat, clip=clip)
            return pix.tobytes("png")
        except Exception:
            return None

    # -----------------------------------------------------------------------
    # Tabelle
    # -----------------------------------------------------------------------

    def _extract_tables(self, plumb_page, page_num: int, describer) -> List[TableBlock]:
        results = []
        book = self.config.book_name
        try:
            found = plumb_page.find_tables()
        except Exception:
            return []

        for idx, tbl_obj in enumerate(found):
            try:
                raw_rows = tbl_obj.extract()
                if not raw_rows or len(raw_rows) < 2:
                    continue

                rows = [
                    [(cell or "").replace("\n", " ").strip() for cell in row]
                    for row in raw_rows
                ]
                bbox = tuple(tbl_obj.bbox)

                fname = f"{book}_p{page_num+1}_tbl{idx+1}.csv"
                save_path = self.tables_dir / fname
                with open(save_path, "w", encoding="utf-8") as f:
                    for row in rows:
                        f.write(",".join(f'"{c}"' for c in row) + "\n")

                description = None
                if describer:
                    description = describer.describe_table(rows)
                    save_path.with_suffix(".txt").write_text(description, encoding="utf-8")

                results.append(TableBlock(
                    rows=rows, bbox=bbox,
                    page_num=page_num, index=idx,
                    saved_path=str(save_path), description=description,
                ))
            except Exception as e:
                print(f"\n  [warn] tabella p{page_num+1} #{idx}: {e}")

        return results

    # -----------------------------------------------------------------------
    # Testo
    # -----------------------------------------------------------------------

    def _extract_text(
        self,
        page,
        width: float,
        excluded_bboxes: List[Tuple],
    ) -> List[TextBlock]:
        raw = page.get_text("dict")
        text_blocks: List[TextBlock] = []

        for block in raw.get("blocks", []):
            if block.get("type") != 0:
                continue
            bbox = tuple(block["bbox"])
            if self._overlaps_any(bbox, excluded_bboxes):
                continue

            spans: List[TextSpan] = []
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    txt = span.get("text", "").strip()
                    if not txt:
                        continue
                    flags = span.get("flags", 0)
                    spans.append(TextSpan(
                        text=txt,
                        font=span.get("font", ""),
                        size=span.get("size", 10.0),
                        bold=bool(flags & 16),
                        italic=bool(flags & 2),
                        bbox=tuple(span["bbox"]),
                    ))

            if spans:
                if not _is_noise_block(spans):
                    text_blocks.append(TextBlock(spans=spans, bbox=bbox))

        # Determina layout colonne per questa pagina
        forced = self.config.columns
        if forced == 1:
            n_cols, split_ratio = 1, 0.5
        elif forced == 2:
            split_ratio = self.config.column_split or self._find_split_ratio(text_blocks, width)
            n_cols = 2
        else:
            # None = auto: rileva per questa pagina
            n_cols, split_ratio = self._detect_page_columns(text_blocks, width)

        if n_cols == 2:
            text_blocks = self._sort_double_column(text_blocks, width * split_ratio, width)
            self._col_stats[2] += 1
        else:
            text_blocks.sort(key=lambda b: b.bbox[1])
            self._col_stats[1] += 1

        return text_blocks

    def _detect_page_columns(
        self, blocks: List[TextBlock], width: float
    ) -> Tuple[int, float]:
        """
        Rileva se una pagina e a singola o doppia colonna.

        Esclude blocchi larghi (>60% pagina) come titoli full-width che non
        rappresentano il layout del corpo. Cerca il gap orizzontale piu ampio
        nella fascia centrale 25%-75%. Se supera column_gap_threshold e ci
        sono blocchi da entrambi i lati, la pagina e a doppia colonna.
        """
        if len(blocks) < 4:
            return 1, 0.5

        fw_limit = width * 0.60
        content_blocks = [b for b in blocks if (b.bbox[2] - b.bbox[0]) < fw_limit]

        if len(content_blocks) < 4:
            return 1, 0.5

        split_ratio = self._find_split_ratio(content_blocks, width)
        split_x = width * split_ratio

        left_count  = sum(1 for b in content_blocks if b.bbox[0] < split_x)
        right_count = sum(1 for b in content_blocks if b.bbox[0] >= split_x)
        if left_count < 2 or right_count < 2:
            return 1, 0.5

        centers = sorted(
            (b.bbox[0] + b.bbox[2]) / 2
            for b in content_blocks
            if 0.25 * width < (b.bbox[0] + b.bbox[2]) / 2 < 0.75 * width
        )
        if len(centers) < 2:
            return 1, 0.5

        max_gap = max(centers[i+1] - centers[i] for i in range(len(centers)-1))

        if max_gap >= self.config.column_gap_threshold * width:
            return 2, split_ratio
        return 1, 0.5

    def _find_split_ratio(self, blocks: List[TextBlock], width: float) -> float:
        """Posizione X del gap piu ampio nella zona centrale della pagina."""
        centers = sorted(
            (b.bbox[0] + b.bbox[2]) / 2
            for b in blocks
            if 0.25 * width < (b.bbox[0] + b.bbox[2]) / 2 < 0.75 * width
        )
        if len(centers) < 2:
            return 0.5
        max_gap, split_x = 0.0, width / 2
        for i in range(len(centers) - 1):
            gap = centers[i+1] - centers[i]
            if gap > max_gap:
                max_gap = gap
                split_x = (centers[i] + centers[i+1]) / 2
        return split_x / width

    def _sort_double_column(
        self, blocks: List[TextBlock], split_x: float, page_width: float
    ) -> List[TextBlock]:
        """
        Ordina blocchi per doppia colonna separando quelli a piena larghezza
        (titoli, intestazioni di sezione) dai blocchi di colonna veri.

        I blocchi piu larghi del 60% della pagina vengono trattati come
        full-width e posizionati prima/dopo i blocchi di colonna in base
        alla loro posizione Y relativa alla zona colonnata.
        """
        fw_limit = page_width * 0.60
        full_w = sorted([b for b in blocks if (b.bbox[2]-b.bbox[0]) >= fw_limit],
                        key=lambda b: b.bbox[1])
        col_b  = [b for b in blocks if (b.bbox[2]-b.bbox[0]) < fw_limit]

        if not col_b:
            return full_w

        col_top    = min(b.bbox[1] for b in col_b)
        col_bottom = max(b.bbox[3] for b in col_b)

        fw_above  = [b for b in full_w if b.bbox[3] <= col_top]
        fw_below  = [b for b in full_w if b.bbox[1] >= col_bottom]
        fw_inside = [b for b in full_w if b not in fw_above and b not in fw_below]

        left  = sorted([b for b in col_b if b.bbox[0] <  split_x], key=lambda b: b.bbox[1])
        right = sorted([b for b in col_b if b.bbox[0] >= split_x], key=lambda b: b.bbox[1])

        return fw_above + fw_inside + left + right + fw_below

    @staticmethod
    def _overlaps_any(bbox: Tuple, excluded: List[Tuple], threshold: float = 0.3) -> bool:
        x0, y0, x1, y1 = bbox
        area = max((x1 - x0) * (y1 - y0), 1)
        for ex in excluded:
            ex0, ey0, ex1, ey1 = ex
            ix = max(0.0, min(x1, ex1) - max(x0, ex0))
            iy = max(0.0, min(y1, ey1) - max(y0, ey0))
            if (ix * iy) / area > threshold:
                return True
        return False

    def __del__(self):
        if hasattr(self, "doc"):
            try:
                self.doc.close()
            except Exception:
                pass


