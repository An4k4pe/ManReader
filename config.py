"""
config.py — Configurazione del layout per la conversione PDF→EPUB.

Ogni manuale può avere parametri diversi: numero di colonne, soglia per
i titoli, dimensione minima immagini da tenere, ecc.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class LayoutConfig:
    # ---- Layout pagina ----
    columns: int = 1
    """Numero di colonne: 1 (singola) o 2 (doppia)."""

    column_split: Optional[float] = None
    """
    Punto di divisione tra le colonne, espresso come frazione della larghezza
    pagina (0.0–1.0). Se None, viene rilevato automaticamente cercando il gap
    più ampio nella zona centrale della pagina.
    """

    # ---- Immagini ----
    min_image_width: int = 80
    min_image_height: int = 80
    """
    Dimensione minima (pixel) per considerare un'immagine. Filtra decorazioni
    di bordo, bullet grafici, separatori che sporcherebbero l'output.
    """

    # ---- Rilevamento titoli ----
    heading_font_size_threshold: float = 1.3
    """
    Moltiplicatore sulla mediana del corpo del testo per identificare titoli.
    Esempio: se la mediana è 10pt, con threshold=1.3 un titolo è >=13pt.
    Abbassare questo valore se i titoli nel PDF sono poco più grandi del corpo.
    """

    # ---- Estrazione ----
    extract_tables: bool = True
    """Se False, salta l'estrazione tabelle (più veloce, utile per test)."""

    extract_vectors: bool = True
    """
    Se True, rileva e salva come SVG le illustrazioni vettoriali embedded
    nel PDF (mappe disegnate, diagrammi, grafica decorativa strutturata).
    Le immagini raster vengono sempre estratte indipendentemente da questo flag.
    """

    min_vector_size: float = 50.0
    """
    Dimensione minima (punti PDF) di larghezza E altezza perché un gruppo
    di path vettoriali venga considerato un'illustrazione da estrarre.
    Filtra linee singole, separatori, bordi di pagina.
    """

    describe_with_ai: bool = True
    """Se True, chiama l'API Anthropic per descrivere immagini e tabelle."""

    ai_language: str = "italiano"
    """Lingua delle descrizioni AI generate."""

    # ---- Filtro intestazioni / piè di pagina / filigrane ----
    filter_repeated: bool = True
    """
    Se True, rimuove testo che si ripete alla stessa posizione su molte pagine:
    intestazioni, piè di pagina con numero pagina o titolo capitolo, filigrane.
    """

    header_footer_zone: float = 0.08
    """
    Percentuale dell'altezza pagina considerata "zona header" (dal top) e
    "zona footer" (dal bottom). Default 0.08 = top 8% e bottom 8%.
    Aumenta se il tuo manuale ha intestazioni alte; abbassa se i titoli di
    capitolo in cima alla prima pagina venissero erroneamente rimossi.
    """

    repetition_threshold: float = 0.25
    """
    Frazione di pagine su cui un testo deve apparire per essere considerato
    ripetuto. Default 0.25 = presente su >25% delle pagine → rimosso.
    Abbassa per PDF con molte varianti (es. titolo capitolo che cambia ogni
    sezione ma si ripete comunque); aumenta se rimuove troppo.
    """

    # ---- Output ----
    output_dir: str = "output"
    """Cartella radice dove salvare EPUB e assets."""

    book_name: str = "book"
    """
    Nome base per i file generati: book.epub, assets/images/book_p1_img1.png, ecc.
    """
