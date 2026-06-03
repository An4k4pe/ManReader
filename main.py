"""
main.py — CLI per la conversione PDF→EPUB di manuali GDR.

Uso base:
  python main.py manuale.pdf

Esempi pratici:
  # Manuale doppia colonna, con descrizioni AI
  python main.py dnd5e.pdf --columns 2 --title "D&D 5e - Player's Handbook"

  # Singola colonna, senza AI (più veloce)
  python main.py pathfinder.pdf --no-ai --title "Pathfinder 2e"

  # Doppia colonna con divisione manuale (0.52 = divisione al 52% della larghezza)
  python main.py manuale.pdf --columns 2 --column-split 0.52

  # Test su prime 10 pagine
  python main.py manuale.pdf --pages 1-10 --no-ai

Variabili d'ambiente:
  ANTHROPIC_API_KEY=sk-ant-...   (backend anthropic, alternativa a --api-key)
  GEMINI_API_KEY=AIza...          (backend gemini, alternativa a --api-key)

Backend vision disponibili (--vision-backend):
  anthropic  — Claude via API Anthropic (a pagamento)
  gemini     — Google Gemini Flash, tier gratuito (1500 req/giorno)
  ollama     — inferenza locale, nessuna API key (richiede Ollama in esecuzione)
"""

import argparse
import os
import sys
from pathlib import Path

# Permette di eseguire main.py da qualsiasi directory:
# aggiunge la cartella dello script al Python path
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).parent))

from config import LayoutConfig
from extractor import PDFExtractor
from epub_builder import EPUBBuilder


def _column_type(value: str):
    """Tipo argparse per --columns: accetta auto, 1, 2."""
    if value.lower() == "auto":
        return None
    try:
        v = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"valore non valido: {value!r}. Usa auto, 1 o 2.")
    if v not in (1, 2):
        raise argparse.ArgumentTypeError("deve essere 1, 2 o auto")
    return v


def parse_args():
    parser = argparse.ArgumentParser(
        description="Converti PDF di manuali GDR in EPUB ottimizzato per e-reader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("pdf", help="Path al file PDF da convertire")

    # Metadati
    meta = parser.add_argument_group("Metadati libro")
    meta.add_argument("--title", help="Titolo (default: nome file senza estensione)")
    meta.add_argument("--author", default="", help="Autore del manuale")

    # Layout
    layout = parser.add_argument_group("Layout pagina")
    layout.add_argument(
        "--columns", type=_column_type, default=None, metavar="auto|1|2",
        help=(
            "Numero di colonne: 1 (forza singola), 2 (forza doppia), "
            "auto (rileva pagina per pagina). Default: auto."
        ),
    )
    layout.add_argument(
        "--column-gap", type=float, default=0.08, metavar="0.0-1.0",
        help=(
            "Soglia gap colonne in modalita auto: frazione della larghezza "
            "pagina. Default 0.08. Aumenta se rileva doppie colonne per errore; "
            "abbassa se non rileva doppie colonne reali."
        ),
    )
    layout.add_argument(
        "--column-split", type=float, default=None, metavar="0.0-1.0",
        help=(
            "Posizione manuale del divisore tra colonne, come frazione della "
            "larghezza pagina. Esempio: 0.5 = metà pagina. "
            "Se non specificato, viene rilevato automaticamente (solo con --columns 2)."
        ),
    )
    layout.add_argument(
        "--heading-threshold", type=float, default=1.3, metavar="MULT",
        help=(
            "Moltiplicatore font per rilevare i titoli. "
            "Default 1.3 = font ≥ 130%% della mediana. "
            "Abbassa se i tuoi titoli sono piccoli; aumenta se rileva troppi falsi titoli."
        ),
    )
    layout.add_argument(
        "--min-image-size", type=int, default=80, metavar="PX",
        help="Dimensione minima (pixel) per includere un'immagine (default: 80)",
    )

    # Funzionalità
    feat = parser.add_argument_group("Funzionalità")
    feat.add_argument(
        "--no-tables", action="store_true",
        help="Non estrarre tabelle (più veloce, utile per test)",
    )
    feat.add_argument(
        "--no-vectors", action="store_true",
        help="Non estrarre illustrazioni vettoriali",
    )
    feat.add_argument(
        "--no-ai", action="store_true",
        help="Non usare l'AI per descrivere immagini e tabelle",
    )
    feat.add_argument(
        "--ai-language", default="italiano",
        help="Lingua per le descrizioni AI (default: italiano)",
    )
    feat.add_argument(
        "--no-filter", action="store_true",
        help="Non rimuovere intestazioni/piè di pagina/filigrane ripetute",
    )
    feat.add_argument(
        "--header-zone", type=float, default=0.08, metavar="0.0-1.0",
        help=(
            "Altezza della zona header/footer come frazione della pagina. "
            "Default 0.08 = top e bottom 8%%. Aumenta se le intestazioni "
            "sono alte; abbassa se i titoli di capitolo venissero rimossi."
        ),
    )
    feat.add_argument(
        "--repeat-threshold", type=float, default=0.25, metavar="0.0-1.0",
        help=(
            "Soglia ripetizione: testo presente su più di questa frazione "
            "di pagine viene rimosso. Default 0.25 = >25%% delle pagine."
        ),
    )
    feat.add_argument(
        "--keep-toc-pages", action="store_true",
        help=(
            "Non rimuovere le pagine di indice/sommario dal corpo EPUB. "
            "Di default vengono rimosse e sostituite con una pagina TOC navigabile."
        ),
    )
    feat.add_argument(
        "--pages", metavar="N o N-M",
        help="Elabora solo queste pagine, es: '1-20' o '5'. Utile per test.",
    )

    # Output
    out = parser.add_argument_group("Output")
    out.add_argument(
        "--output", default="output",
        help="Cartella di output (default: ./output)",
    )

    # AI Vision backend
    api = parser.add_argument_group("AI Vision backend")
    api.add_argument(
        "--vision-backend", default="anthropic",
        choices=["anthropic", "gemini", "ollama"],
        metavar="BACKEND",
        help=(
            "Backend per le descrizioni AI: "
            "anthropic (default, richiede ANTHROPIC_API_KEY), "
            "gemini (gratuito, richiede GEMINI_API_KEY), "
            "ollama (locale, nessuna API key). "
            "Ignorato se --no-ai è attivo."
        ),
    )
    api.add_argument(
        "--api-key",
        help=(
            "API key per il backend scelto. "
            "Alternativa alle variabili d'ambiente ANTHROPIC_API_KEY / GEMINI_API_KEY."
        ),
    )
    api.add_argument(
        "--ollama-model", default=None, metavar="NOME",
        help="Modello Ollama da usare (default: llama3.2-vision). Esempi: llava, bakllava",
    )
    api.add_argument(
        "--ollama-host", default=None, metavar="URL",
        help="URL server Ollama (default: http://localhost:11434)",
    )

    return parser.parse_args()


def parse_page_range(spec: str, total: int):
    """Converti '1-20' o '5' in (start, end) 0-based."""
    try:
        if "-" in spec:
            a, b = spec.split("-", 1)
            return int(a) - 1, min(int(b), total)
        else:
            n = int(spec)
            return n - 1, n
    except ValueError:
        print(f"Errore: formato pagine non valido '{spec}'. Usa '5' o '1-20'.")
        sys.exit(1)


def main():
    args = parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Errore: file non trovato: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    title = args.title or pdf_path.stem
    book_name = title.replace(" ", "_").replace("/", "-")[:60]

    config = LayoutConfig(
        columns=args.columns,
        column_split=args.column_split,
        column_gap_threshold=args.column_gap,
        min_image_width=args.min_image_size,
        min_image_height=args.min_image_size,
        heading_font_size_threshold=args.heading_threshold,
        extract_tables=not args.no_tables,
        extract_vectors=not args.no_vectors,
        describe_with_ai=not args.no_ai,
        ai_language=args.ai_language,
        filter_repeated=not args.no_filter,
        header_footer_zone=args.header_zone,
        repetition_threshold=args.repeat_threshold,
        output_dir=args.output,
        book_name=book_name,
    )

    # Setup AI describer
    describer = None
    if config.describe_with_ai:
        backend = args.vision_backend  # argparse converte i trattini in underscore
        from describer import create_describer

        # API key: prima --api-key, poi variabile d'ambiente specifica del backend
        api_key = args.api_key
        if not api_key and backend == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY")
        elif not api_key and backend == "gemini":
            api_key = os.environ.get("GEMINI_API_KEY")
        # ollama non usa api_key

        try:
            describer = create_describer(
                backend=backend,
                language=config.ai_language,
                api_key=api_key,
                ollama_model=args.ollama_model,
                ollama_host=args.ollama_host,
            )
        except (ValueError, ImportError) as e:
            print(f"  [warn] Describer non disponibile: {e}\n  Descrizioni AI disabilitate.")
            config.describe_with_ai = False

    # Stampa riepilogo
    print(f"\n{'='*50}")
    print(f"  PDF   : {pdf_path.name}")
    print(f"  Titolo: {title}")
    if config.columns is None:
        print("  Colonne: auto-detect per pagina")
    elif config.columns == 2:
        if config.column_split:
            print(f"  Colonne: 2 (divisore fisso a {config.column_split:.0%})")
        else:
            print("  Colonne: 2 (divisore auto-detect)")
    else:
        print("  Colonne: 1 (singola, forzata)")
    print(f"  Tabelle: {'sì' if config.extract_tables else 'no'}")
    print(f"  Descrizioni AI: {'sì (' + args.vision_backend + ')' if config.describe_with_ai else 'no'}")
    print(f"  Output: {Path(args.output).resolve()}")
    print(f"{'='*50}\n")

    # Estrazione
    extractor = PDFExtractor(pdf_path, config)
    total_pages = extractor.page_count

    # Gestione --pages
    page_start, page_end = 0, total_pages
    if args.pages:
        page_start, page_end = parse_page_range(args.pages, total_pages)
        print(f"  Elaboro pagine {page_start+1}–{page_end} di {total_pages}")

    # Estrazione TOC (outline/bookmarks embedded nel PDF)
    toc = extractor.get_toc()
    if toc:
        print(f"  TOC trovata: {len(toc)} voci (livelli: {sorted(set(l for l,_,_ in toc))})")
    else:
        print("  TOC non trovata: userò euristica font per i capitoli")

    print(f"  Pagine totali: {total_pages}")

    import pdfplumber
    from extractor import filter_repeated_blocks
    pages_data = []
    with pdfplumber.open(str(pdf_path)) as plumb:
        for i in range(page_start, page_end):
            print(f"  Pagina {i+1}/{page_end}...", end="\r", flush=True)
            pages_data.append(extractor._extract_page(i, plumb.pages[i], describer))
    print(f"  Estratte {len(pages_data)} pagine.            ")

    # Rimozione intestazioni, piè di pagina e filigrane ripetute
    if config.filter_repeated and len(pages_data) >= 4:
        # Con meno di 4 pagine la statistica non ha senso
        pages_data = filter_repeated_blocks(
            pages_data,
            header_footer_zone=config.header_footer_zone,
            repetition_threshold=config.repetition_threshold,
        )
    elif config.filter_repeated:
        print("  Filtro ripetizioni: saltato (troppo poche pagine per statistica affidabile)")

    # Rimozione pagine sommario/indice dal corpo EPUB
    if not args.keep_toc_pages:
        from extractor import is_toc_page
        before = len(pages_data)
        pages_data = [p for p in pages_data if not is_toc_page(p)]
        removed = before - len(pages_data)
        if removed:
            print(f"  Rimosse {removed} pagine indice dal corpo (disponibili come TOC navigabile)")

    # Build EPUB
    print("\n  Costruzione EPUB...")
    builder = EPUBBuilder(config, title, args.author)
    epub_path = builder.build(pages_data, toc=toc)

    # Riepilogo finale
    img_count = sum(len(p.images)  for p in pages_data)
    vec_count = sum(len(p.vectors) for p in pages_data)
    tbl_count = sum(len(p.tables)  for p in pages_data)
    extracted = Path(args.output) / f"{book_name}_extracted"

    print(f"\n{'='*50}")
    print(f"  ✓ EPUB:      {epub_path}")
    print(f"  ✓ Immagini:  {img_count} → {extracted / 'images'}")
    print(f"  ✓ Vettoriali:{vec_count} → {extracted / 'vectors'}")
    print(f"  ✓ Tabelle:   {tbl_count} → {extracted / 'tables'}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()

