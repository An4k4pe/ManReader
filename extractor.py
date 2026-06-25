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

import csv
import hashlib
import io
import re as _re
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF
import pdfplumber
from PIL import Image

from config import LayoutConfig

_NONSTANDARD_CHAR_RE = _re.compile(r"^[^\w\s]+$")
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
    bbox: tuple[float, float, float, float]


@dataclass
class TextBlock:
    spans: list[TextSpan]
    bbox: tuple[float, float, float, float]

    @property
    def text(self) -> str:
        return _join_text_spans(self.spans)

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


def _join_text_spans(spans: list[TextSpan]) -> str:
    clean_spans = [span for span in spans if span.text.strip()]
    if not clean_spans:
        return ""

    text = clean_spans[0].text.strip()
    previous = clean_spans[0]

    for span in clean_spans[1:]:
        current = span.text.strip()
        if _should_join_span_without_space(previous, span):
            text += current
        else:
            text += f" {current}"
        previous = span

    return text


def _line_text_from_words(
    words: list[tuple[float, float, float, float, str, int, int, int]],
) -> str:
    clean_words = sorted((word for word in words if word[4].strip()), key=lambda word: word[0])
    if not clean_words:
        return ""

    text = clean_words[0][4].strip()
    for word in clean_words[1:]:
        current = word[4].strip()
        if current[0] in ",.;:!?)]»":
            text += current
        else:
            text += f" {current}"

    return text


def _text_from_block(block: tuple[float, float, float, float, str, int, int]) -> str:
    return " ".join(block[4].strip().split())


def _bbox_area(bbox: tuple[float, float, float, float]) -> float:
    width = max(0.0, bbox[2] - bbox[0])
    height = max(0.0, bbox[3] - bbox[1])
    return width * height


def _bbox_intersection_area(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> float:
    x0 = max(first[0], second[0])
    y0 = max(first[1], second[1])
    x1 = min(first[2], second[2])
    y1 = min(first[3], second[3])
    return _bbox_area((x0, y0, x1, y1))


def _overlap_ratio_against_bbox(
    dict_bbox: tuple[float, float, float, float],
    candidate_bbox: tuple[float, float, float, float],
) -> float:
    area = _bbox_area(dict_bbox)
    if area == 0.0:
        return 0.0
    return _bbox_intersection_area(dict_bbox, candidate_bbox) / area


def _best_text_block_for_bbox(
    dict_bbox: tuple[float, float, float, float],
    blocks: list[tuple[float, float, float, float, str, int, int]],
    min_overlap: float = 0.5,
) -> tuple[float, float, float, float, str, int, int] | None:
    best_block = None
    best_overlap = 0.0

    for block in blocks:
        if block[6] != 0 or not _text_from_block(block):
            continue
        overlap = _overlap_ratio_against_bbox(dict_bbox, block[:4])
        if overlap > best_overlap:
            best_block = block
            best_overlap = overlap

    if best_overlap < min_overlap:
        return None
    return best_block


@dataclass
class _DictBlockMatch:
    dict_bbox: tuple[float, float, float, float]
    dict_text: str
    matched_block: tuple[float, float, float, float, str, int, int] | None
    source_spans: list[TextSpan] | None = None


def _group_consecutive_dict_block_matches(
    matches: list[_DictBlockMatch],
) -> list[list[_DictBlockMatch]]:
    groups: list[list[_DictBlockMatch]] = []

    for match in matches:
        if (
            groups
            and match.matched_block is not None
            and groups[-1][-1].matched_block == match.matched_block
        ):
            groups[-1].append(match)
        else:
            groups.append([match])

    return groups


def _text_block_from_dict_match_group(group: list[_DictBlockMatch]) -> TextBlock | None:
    if not group:
        return None

    matched_block = group[0].matched_block
    if matched_block is None:
        return None
    if any(match.matched_block != matched_block for match in group):
        return None

    text = _text_from_block(matched_block)
    if not text:
        return None

    bbox = _union_bboxes([match.dict_bbox for match in group])
    source_span = _first_source_span(group)
    span = TextSpan(
        text=text,
        font=source_span.font if source_span is not None else "",
        size=source_span.size if source_span is not None else 10.0,
        bold=source_span.bold if source_span is not None else False,
        italic=source_span.italic if source_span is not None else False,
        bbox=bbox,
    )
    return TextBlock(spans=[span], bbox=bbox)


def _rebuild_text_blocks_from_block_hints(
    text_blocks: list[TextBlock],
    block_hints: list[tuple[float, float, float, float, str, int, int]],
) -> list[TextBlock]:
    matches = [
        _DictBlockMatch(
            dict_bbox=text_block.bbox,
            dict_text=text_block.text,
            matched_block=_best_text_block_for_bbox(text_block.bbox, block_hints),
            source_spans=text_block.spans,
        )
        for text_block in text_blocks
    ]
    groups = _group_consecutive_dict_block_matches(matches)
    rebuilt: list[TextBlock] = []
    index = 0

    for group in groups:
        if len(group) > 1:
            text_block = _text_block_from_dict_match_group(group)
            if text_block is not None:
                rebuilt.append(text_block)
            else:
                rebuilt.extend(text_blocks[index : index + len(group)])
        else:
            rebuilt.append(text_blocks[index])
        index += len(group)

    return rebuilt


def _union_bboxes(
    bboxes: list[tuple[float, float, float, float]],
) -> tuple[float, float, float, float]:
    return (
        min(bbox[0] for bbox in bboxes),
        min(bbox[1] for bbox in bboxes),
        max(bbox[2] for bbox in bboxes),
        max(bbox[3] for bbox in bboxes),
    )


def _first_source_span(group: list[_DictBlockMatch]) -> TextSpan | None:
    for match in group:
        if match.source_spans:
            return match.source_spans[0]
    return None


def _should_join_span_without_space(first: TextSpan, second: TextSpan) -> bool:
    left = first.text.strip()
    right = second.text.strip()
    if not left or not right:
        return True

    if right[0] in ",.;:!?)]»":
        return True
    if left[-1] in "’'":
        return True

    if not _spans_are_on_same_line(first, second):
        return False

    gap = second.bbox[0] - first.bbox[2]
    has_very_short_fragment = len(left) == 1 or len(right) == 1
    if left[-1].isalnum() and right[0].isalnum() and has_very_short_fragment and gap <= 1.5:
        return True

    return len(left) == 1 and left.isupper() and right.isupper() and gap <= 4.0


def _spans_are_on_same_line(first: TextSpan, second: TextSpan) -> bool:
    first_top, first_bottom = first.bbox[1], first.bbox[3]
    second_top, second_bottom = second.bbox[1], second.bbox[3]

    overlap = min(first_bottom, second_bottom) - max(first_top, second_top)
    if overlap <= 0:
        return False

    first_height = max(first_bottom - first_top, 1.0)
    second_height = max(second_bottom - second_top, 1.0)
    min_height = min(first_height, second_height)
    first_center = (first.bbox[1] + first.bbox[3]) / 2
    second_center = (second.bbox[1] + second.bbox[3]) / 2
    return overlap >= min_height * 0.5 or abs(first_center - second_center) <= 2.0


@dataclass
class ImageBlock:
    """Immagine raster embedded nel PDF."""

    image_data: bytes
    ext: str
    bbox: tuple[float, float, float, float]
    page_num: int
    index: int
    saved_path: str | None = None
    description: str | None = None
    is_background: bool = False
    """True se l'immagine copre >60% della pagina (sfondo/texture).
    Non viene aggiunta a excluded_bboxes: il testo soprastante viene conservato."""
    is_duplicate: bool = False
    """True se questo hash e gia stato salvato in una pagina precedente.
    Il file esiste gia su disco; nell'EPUB l'occorrenza viene saltata."""


@dataclass
class VectorBlock:
    """Gruppo di path vettoriali che formano un'illustrazione."""

    bbox: tuple[float, float, float, float]
    page_num: int
    index: int
    saved_path: str | None = None
    description: str | None = None


@dataclass
class TableBlock:
    rows: list[list[str]]
    bbox: tuple[float, float, float, float]
    page_num: int
    index: int
    saved_path: str | None = None
    description: str | None = None


@dataclass
class PageData:
    page_num: int
    text_blocks: list[TextBlock]
    images: list[ImageBlock]
    vectors: list[VectorBlock]
    tables: list[TableBlock]
    width: float
    height: float


# ---------------------------------------------------------------------------
# Asset Index — registro CSV di tutti gli asset estratti
# ---------------------------------------------------------------------------

_INDEX_FIELDS = ["sha", "nome_file", "tipo", "pagina", "titolo", "descrizione", "modificato"]


class AssetIndex:
    """
    Registro centrale degli asset estratti, salvato come CSV in
    _extracted/asset_index.csv.

    Logica di merge su build esistente:
    - Se il CSV non esiste: creato da zero.
    - Se esiste e nessuna entry ha modificato=si: sovrascritto senza chiedere.
    - Se esiste con almeno una entry modificato=si: le entry marcate sono
      protette; le entry nuove (SHA non presente) vengono aggiunte; le entry
      con modificato=no vengono aggiornate.

    Il SHA è calcolato sul contenuto binario dell'asset (MD5 hex, già usato
    per la dedup inline). È la chiave stabile che sopravvive ai rename.
    """

    def __init__(self, index_path: Path):
        self.path = index_path
        # sha -> dict con i campi del CSV
        self._entries: dict[str, dict] = {}
        self._protected: set = set()  # SHA con modificato=si
        self._loaded = False

    def load(self) -> bool:
        """
        Carica il CSV esistente. Restituisce True se esisteva almeno
        una entry con modificato=si (build protetta).
        """
        if not self.path.exists():
            return False
        try:
            with open(self.path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sha = row.get("sha", "").strip()
                    if not sha:
                        continue
                    self._entries[sha] = dict(row)
                    if row.get("modificato", "no").strip().lower() == "si":
                        self._protected.add(sha)
            self._loaded = True
            return bool(self._protected)
        except Exception as e:
            print(f"  [warn] asset_index.csv: errore lettura ({e}), ricreo da zero")
            return False

    def has_protected(self) -> bool:
        return bool(self._protected)

    def is_protected(self, sha: str) -> bool:
        return sha in self._protected

    def get(self, sha: str) -> dict | None:
        return self._entries.get(sha)

    def add_or_update(
        self,
        sha: str,
        nome_file: str,
        tipo: str,
        pagina: int,
        titolo: str | None,
        descrizione: str | None,
    ) -> None:
        """
        Aggiunge una nuova entry o aggiorna una esistente non protetta.
        Le entry con modificato=si non vengono toccate.
        """
        if sha in self._protected:
            return
        self._entries[sha] = {
            "sha": sha,
            "nome_file": nome_file,
            "tipo": tipo,
            "pagina": str(pagina + 1),  # 1-based per leggibilità
            "titolo": titolo or "",
            "descrizione": descrizione or "",
            "modificato": "no",
        }

    def get_title(self, sha: str) -> str | None:
        """Restituisce il titolo leggibile (eventualmente modificato dall'utente)."""
        entry = self._entries.get(sha)
        if not entry:
            return None
        return entry.get("titolo") or None

    def get_description(self, sha: str) -> str | None:
        """Restituisce la descrizione (eventualmente modificata dall'utente)."""
        entry = self._entries.get(sha)
        if not entry:
            return None
        return entry.get("descrizione") or None

    def get_current_name(self, sha: str) -> str | None:
        """Restituisce il nome file corrente (eventualmente rinominato dall'utente)."""
        entry = self._entries.get(sha)
        if not entry:
            return None
        return entry.get("nome_file") or None

    def save(self) -> None:
        """Scrive il CSV su disco."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_INDEX_FIELDS)
            writer.writeheader()
            for entry in self._entries.values():
                writer.writerow(entry)


# ---------------------------------------------------------------------------
# Rilevamento pagine sommario / indice
# ---------------------------------------------------------------------------

_TOC_LINE_RE = _re.compile(r".{3,}\s+\d{1,3}\s*$")


def is_toc_page(page: PageData) -> bool:
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
    matches = sum(1 for b in page.text_blocks if _TOC_LINE_RE.search(b.text.strip()))
    return (matches / len(page.text_blocks)) > 0.40


# ---------------------------------------------------------------------------
# Filtro intestazioni / piè di pagina / filigrane
# ---------------------------------------------------------------------------


def _normalize_text(text: str) -> str:
    """Rimuove cifre e normalizza per confronto. 'Pagina 42' == 'Pagina 103'."""
    return _re.sub(r"\d+", "", text).strip().lower()


def filter_repeated_blocks(
    pages: list[PageData],
    header_footer_zone: float = 0.08,
    repetition_threshold: float = 0.25,
) -> list[PageData]:
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
                "header"
                if y_norm < header_footer_zone
                else "footer"
                if y_norm > (1.0 - header_footer_zone)
                else "body"
            )
            norm = _normalize_text(block.text)
            if (zone, norm) in to_remove:
                removed += 1
            else:
                clean.append(block)
        result.append(
            PageData(
                page_num=page.page_num,
                text_blocks=clean,
                images=page.images,
                vectors=page.vectors,
                tables=page.tables,
                width=page.width,
                height=page.height,
            )
        )

    unique = len(to_remove)
    print(f"  Filtro ripetizioni: {unique} pattern rimossi ({removed} blocchi totali)")
    return result


# ---------------------------------------------------------------------------
# Filtro glifi decorativi e numeri di pagina
# ---------------------------------------------------------------------------

# Font simbolici/icona noti: i loro glifi vengono estratti come lettere
# normali ma rappresentano bullets, ornamenti, frecce ecc.
_SYMBOL_FONT_KEYWORDS = frozenset(
    [
        "symbol",
        "dingbat",
        "wingding",
        "zapf",
        "webding",
        "icon",
        "ornament",
        "glyph",
        "bullet",
        "arrow",
    ]
)

# Singole lettere che non sono mai parole standalone in italiano/inglese
# (tipicamente glifi di font icona mappati su lettere ASCII)
# Escluse le vocali e 'I': possono essere articoli/congiunzioni reali
_LONE_GLYPH_CHARS = frozenset(
    "bcdfghjklmnpqrstuvwxyz"  # consonanti minuscole
    "BCDFGHJKLMNPQRSTUVWXYZ"  # consonanti maiuscole
    "0123456789"  # cifre standalone gia coperte dal check numerico
)

# Regex per caratteri non-standard che compaiono spesso come glifi decorativi:
# caratteri di controllo, PUA Unicode, simboli non comuni
import re as _re_slug


def _title_to_slug(title: str, max_words: int = 3) -> str:
    """
    Converte un titolo breve (generato dall'AI tramite generate_title)
    in uno slug per nome file: minuscolo, solo alfanumerici e trattini.
    Esempio: "Luna Crescente Ornata" → "luna-crescente-ornata"
    """
    clean = []
    for w in title.strip().split():
        w_norm = _re_slug.sub(r"[^\w]", "", w, flags=_re_slug.UNICODE).lower()
        if w_norm:
            clean.append(w_norm)
        if len(clean) >= max_words:
            break
    slug = "-".join(clean)
    slug = _re_slug.sub(r"-+", "-", slug).strip("-")
    return slug


def _desc_to_slug(description: str, max_words: int = 4) -> str:
    """
    Fallback: estrae parole contenutistiche dalla descrizione completa,
    usato solo se generate_title() non è disponibile o ritorna vuoto.
    """
    SKIP = {
        "questa",
        "questo",
        "quest",
        "l",
        "la",
        "lo",
        "le",
        "il",
        "i",
        "un",
        "una",
        "uno",
        "immagine",
        "illustrazione",
        "foto",
        "figura",
        "disegno",
        "mostra",
        "raffigura",
        "rappresenta",
        "ritrae",
        "è",
        "e",
        "di",
        "del",
        "della",
        "dello",
        "dei",
        "degli",
        "delle",
        "con",
        "che",
        "in",
        "da",
        "per",
        "su",
        "al",
        "alla",
        "probabilmente",
        "forse",
    }
    clean = []
    for w in description.strip().split():
        w_norm = _re_slug.sub(r"[^\w]", "", w, flags=_re_slug.UNICODE).lower()
        if w_norm and w_norm not in SKIP:
            clean.append(w_norm)
        if len(clean) >= max_words:
            break
    slug = "-".join(clean)
    slug = _re_slug.sub(r"-+", "-", slug).strip("-")
    return slug or "img"


def _is_noise_block(spans: list) -> bool:
    """
    Restituisce True se il blocco e quasi certamente rumore decorativo:
      - tutti gli span usano font simbolici (Wingdings, Dingbats, ecc.)
      - oppure il testo e un singolo carattere consonante (glifo icona)
      - oppure e un numero di pagina standalone (solo cifre, 1-3 chars, bold)
    """
    if not spans:
        return True

    full_text = " ".join(s.text for s in spans).strip()

    # Tutti gli span usano font simbolici?
    if all(any(kw in s.font.lower() for kw in _SYMBOL_FONT_KEYWORDS) for s in spans):
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

        # Cartella estratti: output/NomePDF/extracted/
        extracted = Path(config.output_dir) / "extracted"
        self.images_dir = extracted / "images"
        self.vectors_dir = extracted / "vectors"
        self.tables_dir = extracted / "tables"
        for d in (self.images_dir, self.vectors_dir, self.tables_dir):
            d.mkdir(parents=True, exist_ok=True)

        # Contatori per il riepilogo finale del rilevamento colonne
        self._col_stats: dict = {1: 0, 2: 0}

        # Dedup inline immagini: hash MD5 -> path del file gia salvato
        # Evita di salvare piu volte lo stesso sfondo/texture su pagine diverse
        self._seen_image_hashes: dict = {}

        # Asset index: registro CSV degli asset estratti
        self.asset_index = AssetIndex(extracted / "asset_index.csv")

    def check_existing_index(self) -> str:
        """
        Controlla se esiste già un asset_index.csv con entry protette.
        Restituisce:
          'none'      — nessun CSV esistente
          'clean'     — CSV esiste, nessuna entry modificato=si
          'protected' — CSV esiste con entry modificato=si (richiede conferma)
        """
        if not self.asset_index.path.exists():
            return "none"
        has_protected = self.asset_index.load()
        if has_protected:
            return "protected"
        return "clean"

    def save_index(self) -> None:
        """Salva l'asset_index.csv a fine estrazione."""
        self.asset_index.save()

    def extract_all(self, describer=None) -> list[PageData]:
        pages = []
        with pdfplumber.open(str(self.pdf_path)) as plumb:
            for i in range(self.page_count):
                print(f"  Pagina {i + 1}/{self.page_count}...", end="\r", flush=True)
                pages.append(self._extract_page(i, plumb.pages[i], describer))
        print(f"  Estratte {self.page_count} pagine.             ")
        if self.config.columns is None:
            p1 = self._col_stats[1]
            p2 = self._col_stats[2]
            print(f"  Layout rilevato: {p1} pag. singola colonna, {p2} pag. doppia colonna")
        return pages

    def get_toc(self) -> list[tuple[int, str, int]]:
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
        width = fitz_page.rect.width
        height = fitz_page.rect.height

        images = self._extract_images(fitz_page, page_num, describer)
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

    def _extract_images(self, page, page_num: int, describer) -> list[ImageBlock]:
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
                bbox_area = max((x1 - x0) * (y1 - y0), 1)
                is_bg = (bbox_area / page_area) > 0.60

                # Dedup inline: se questa immagine e gia stata salvata
                # in una pagina precedente, riusa il file esistente
                img_hash = hashlib.md5(img_bytes).hexdigest()
                if img_hash in self._seen_image_hashes:
                    existing_path = self._seen_image_hashes[img_hash]
                    # Recupera la descrizione già salvata dall'index
                    cached_desc = self.asset_index.get_description(img_hash)
                    results.append(
                        ImageBlock(
                            image_data=b"",
                            ext=ext,
                            bbox=bbox,
                            page_num=page_num,
                            index=idx,
                            saved_path=existing_path,
                            description=cached_desc,
                            is_background=is_bg,
                            is_duplicate=True,
                        )
                    )
                    continue

                # Nome provvisorio: verrà rinominato dopo la descrizione AI
                fname_tmp = f"p{page_num + 1}_img{idx + 1}.{ext}"
                save_path = self.images_dir / fname_tmp
                save_path.write_bytes(img_bytes)

                title = None
                description = None
                if describer and not is_bg:
                    title, description = describer.describe_image(img_bytes, ext)
                    # Rinomina il file usando le prime 4 parole della descrizione
                    if description:
                        slug = _title_to_slug(title) if title else None
                        if not slug:
                            slug = _desc_to_slug(description)
                        fname = f"{slug}.{ext}"
                        new_path = self.images_dir / fname
                        # Evita collisioni aggiungendo suffisso numerico
                        counter = 1
                        while new_path.exists():
                            fname = f"{slug}_{counter}.{ext}"
                            new_path = self.images_dir / fname
                            counter += 1
                        save_path.rename(new_path)
                        save_path = new_path
                    else:
                        fname = fname_tmp  # mantieni nome numerico se no descrizione

                self._seen_image_hashes[img_hash] = str(save_path)

                # Registra nell'index (non sovrascrive entry protette)
                self.asset_index.add_or_update(
                    sha=img_hash,
                    nome_file=save_path.name,
                    tipo="image",
                    pagina=page_num,
                    titolo=title,
                    descrizione=description,
                )

                results.append(
                    ImageBlock(
                        image_data=img_bytes,
                        ext=ext,
                        bbox=bbox,
                        page_num=page_num,
                        index=idx,
                        saved_path=str(save_path),
                        description=description,
                        is_background=is_bg,
                    )
                )
            except Exception as e:
                print(f"\n  [warn] immagine p{page_num + 1} #{idx}: {e}")

        return results

    def _get_image_bbox(self, page, xref: int) -> tuple[float, float, float, float]:
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

    def _extract_vectors(self, page, page_num: int, describer) -> list[VectorBlock]:
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
            fitz.Rect(
                fitz.Rect(d["rect"]).x0 - margin,
                fitz.Rect(d["rect"]).y0 - margin,
                fitz.Rect(d["rect"]).x1 + margin,
                fitz.Rect(d["rect"]).y1 + margin,
            )
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

            fname_tmp = f"p{page_num + 1}_vec{vec_idx + 1}.svg"
            save_path = self.vectors_dir / fname_tmp
            bbox_tuple = (merged.x0, merged.y0, merged.x1, merged.y1)

            ok = self._export_region_as_svg(page_num, merged, save_path)
            if not ok:
                continue

            # Descrizione AI: renderizza come PNG e invia all'API
            vec_title = None
            description = None
            if describer:
                thumb = self._render_region_as_png(page_num, merged)
                if thumb:
                    vec_title, description = describer.describe_image(thumb, "png")
                    if description:
                        slug = _title_to_slug(vec_title) if vec_title else None
                        if not slug:
                            slug = _desc_to_slug(description)
                        fname = f"{slug}.svg"
                        new_path = self.vectors_dir / fname
                        counter = 1
                        while new_path.exists():
                            fname = f"{slug}_{counter}.svg"
                            new_path = self.vectors_dir / fname
                            counter += 1
                        save_path.rename(new_path)
                        save_path = new_path

            # Calcola SHA sul contenuto SVG salvato
            vec_sha = hashlib.md5(save_path.read_bytes()).hexdigest()
            self.asset_index.add_or_update(
                sha=vec_sha,
                nome_file=save_path.name,
                tipo="vector",
                pagina=page_num,
                titolo=vec_title,
                descrizione=description,
            )

            results.append(
                VectorBlock(
                    bbox=bbox_tuple,
                    page_num=page_num,
                    index=vec_idx,
                    saved_path=str(save_path),
                    description=description,
                )
            )
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
            print(f"\n  [warn] SVG export p{page_num + 1}: {e}")
            return False

    def _render_region_as_png(self, page_num: int, clip: fitz.Rect) -> bytes | None:
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

    def _extract_tables(self, plumb_page, page_num: int, describer) -> list[TableBlock]:
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
                    [(cell or "").replace("\n", " ").strip() for cell in row] for row in raw_rows
                ]
                bbox = tuple(tbl_obj.bbox)

                fname = f"p{page_num + 1}_tbl{idx + 1}.csv"
                save_path = self.tables_dir / fname
                with open(save_path, "w", encoding="utf-8") as f:
                    for row in rows:
                        f.write(",".join(f'"{c}"' for c in row) + "\n")

                description = None
                if describer:
                    description = describer.describe_table(rows)

                # SHA sul contenuto CSV
                csv_bytes = open(save_path, "rb").read()
                tbl_sha = hashlib.md5(csv_bytes).hexdigest()
                self.asset_index.add_or_update(
                    sha=tbl_sha,
                    nome_file=save_path.name,
                    tipo="table",
                    pagina=page_num,
                    titolo=None,
                    descrizione=description,
                )

                results.append(
                    TableBlock(
                        rows=rows,
                        bbox=bbox,
                        page_num=page_num,
                        index=idx,
                        saved_path=str(save_path),
                        description=description,
                    )
                )
            except Exception as e:
                print(f"\n  [warn] tabella p{page_num + 1} #{idx}: {e}")

        return results

    # -----------------------------------------------------------------------
    # Testo
    # -----------------------------------------------------------------------

    def _extract_text(
        self,
        page,
        width: float,
        excluded_bboxes: list[tuple],
    ) -> list[TextBlock]:
        raw = page.get_text("dict")
        text_blocks: list[TextBlock] = []

        for block in raw.get("blocks", []):
            if block.get("type") != 0:
                continue
            bbox = tuple(block["bbox"])
            if self._overlaps_any(bbox, excluded_bboxes):
                continue

            spans: list[TextSpan] = []
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    txt = span.get("text", "").strip()
                    if not txt:
                        continue
                    flags = span.get("flags", 0)
                    spans.append(
                        TextSpan(
                            text=txt,
                            font=span.get("font", ""),
                            size=span.get("size", 10.0),
                            bold=bool(flags & 16),
                            italic=bool(flags & 2),
                            bbox=tuple(span["bbox"]),
                        )
                    )

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

    def _detect_page_columns(self, blocks: list[TextBlock], width: float) -> tuple[int, float]:
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

        left_count = sum(1 for b in content_blocks if b.bbox[0] < split_x)
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

        max_gap = max(centers[i + 1] - centers[i] for i in range(len(centers) - 1))

        if max_gap >= self.config.column_gap_threshold * width:
            return 2, split_ratio
        return 1, 0.5

    def _find_split_ratio(self, blocks: list[TextBlock], width: float) -> float:
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
            gap = centers[i + 1] - centers[i]
            if gap > max_gap:
                max_gap = gap
                split_x = (centers[i] + centers[i + 1]) / 2
        return split_x / width

    def _sort_double_column(
        self, blocks: list[TextBlock], split_x: float, page_width: float
    ) -> list[TextBlock]:
        """
        Ordina blocchi per doppia colonna separando quelli a piena larghezza
        (titoli, intestazioni di sezione) dai blocchi di colonna veri.

        I blocchi piu larghi del 60% della pagina vengono trattati come
        full-width e posizionati prima/dopo i blocchi di colonna in base
        alla loro posizione Y relativa alla zona colonnata.
        """
        fw_limit = page_width * 0.60
        full_w = sorted(
            [b for b in blocks if (b.bbox[2] - b.bbox[0]) >= fw_limit], key=lambda b: b.bbox[1]
        )
        col_b = [b for b in blocks if (b.bbox[2] - b.bbox[0]) < fw_limit]

        if not col_b:
            return full_w

        col_top = min(b.bbox[1] for b in col_b)
        col_bottom = max(b.bbox[3] for b in col_b)

        fw_above = [b for b in full_w if b.bbox[3] <= col_top]
        fw_below = [b for b in full_w if b.bbox[1] >= col_bottom]
        fw_inside = [b for b in full_w if b not in fw_above and b not in fw_below]

        left = sorted([b for b in col_b if b.bbox[0] < split_x], key=lambda b: b.bbox[1])
        right = sorted([b for b in col_b if b.bbox[0] >= split_x], key=lambda b: b.bbox[1])

        return fw_above + fw_inside + left + right + fw_below

    @staticmethod
    def _overlaps_any(bbox: tuple, excluded: list[tuple], threshold: float = 0.3) -> bool:
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
