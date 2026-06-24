"""
ManReader — converte PDF di manuali GDR in EPUB per e-reader.

USO BASE
  python main.py manuale.pdf

ESEMPI
  # Conversione standard, layout rilevato automaticamente
  python main.py dnd5e.pdf --title "D&D 5e - Player's Handbook"

  # Forza doppia colonna, senza AI (più veloce)
  python main.py pathfinder.pdf --columns 2 --no-ai

  # Doppia colonna con divisore manuale al 52% della larghezza pagina
  python main.py manuale.pdf --columns 2 --column-split 0.52

  # Solo prime 10 pagine (test rapido)
  python main.py manuale.pdf --pages 1-10 --no-ai

  # Descrizioni AI via Ollama locale
  python main.py manuale.pdf --ollama-model gemma4:12b

STRUMENTI COLLEGATI
  asset_manager.py  — applica rename e modifiche dall'asset_index.csv all'EPUB già buildato
                      python asset_manager.py output/NomePDF/
"""

import argparse
import sys

# Permette di eseguire main.py da qualsiasi directory:
# aggiunge la cartella dello script al Python path
import sys as _sys
from pathlib import Path
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).parent))

from config import LayoutConfig
from epub_builder import EPUBBuilder
from extractor import AssetIndex, PDFExtractor
from ir_builder import build_document_ir
from ir_store import save_document_ir


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
        prog="manreader",
        description="Converti PDF di manuali GDR in EPUB ottimizzato per e-reader.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
        add_help=False,  # gestiamo -h manualmente per avere sia -h che --help
    )

    # Help esplicito: -h e --help
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Mostra questo messaggio ed esci.",
    )

    parser.add_argument("pdf", help="Path al file PDF da convertire.")

    # ── Metadati ────────────────────────────────────────────────────────────
    meta = parser.add_argument_group("metadati libro")
    meta.add_argument(
        "--title",
        help="Titolo del libro (default: nome file senza estensione).",
    )
    meta.add_argument(
        "--author",
        default="",
        help="Autore del manuale (default: vuoto).",
    )

    # ── Layout ──────────────────────────────────────────────────────────────
    layout = parser.add_argument_group("layout pagina")
    layout.add_argument(
        "--columns",
        type=_column_type,
        default=None,
        metavar="auto|1|2",
        help=(
            "Colonne di testo: 1 = singola (forza), 2 = doppia (forza), "
            "auto = rileva pagina per pagina (default)."
        ),
    )
    layout.add_argument(
        "--column-gap",
        type=float,
        default=0.08,
        metavar="N",
        help=(
            "Gap minimo tra colonne in modalità auto, come frazione della "
            "larghezza pagina (default: 0.08). "
            "Aumenta se rileva doppie colonne per errore."
        ),
    )
    layout.add_argument(
        "--column-split",
        type=float,
        default=None,
        metavar="N",
        help=(
            "Punto di divisione manuale tra le colonne (0.0–1.0). "
            "Esempio: 0.5 = metà pagina. Solo con --columns 2. "
            "Default: rilevamento automatico."
        ),
    )
    layout.add_argument(
        "--heading-threshold",
        type=float,
        default=1.3,
        metavar="N",
        help=(
            "Moltiplicatore font per identificare i titoli di capitolo. "
            "Default: 1.3 (= font ≥ 130%% della dimensione mediana). "
            "Abbassa se i titoli non vengono rilevati; aumenta per ridurre i falsi positivi."
        ),
    )
    layout.add_argument(
        "--min-image-size",
        type=int,
        default=80,
        metavar="PX",
        help="Ignora immagini più piccole di PX pixel (larghezza o altezza). Default: 80.",
    )

    # ── Funzionalità ────────────────────────────────────────────────────────
    feat = parser.add_argument_group("funzionalità")
    feat.add_argument(
        "--no-tables",
        action="store_true",
        help="Non estrarre tabelle.",
    )
    feat.add_argument(
        "--no-vectors",
        action="store_true",
        help="Non estrarre illustrazioni vettoriali.",
    )
    feat.add_argument(
        "--no-ai",
        action="store_true",
        help="Non usare l'AI per descrivere immagini e tabelle. Più veloce.",
    )
    feat.add_argument(
        "--ai-language",
        default="italiano",
        metavar="LINGUA",
        help="Lingua per le descrizioni AI (default: italiano).",
    )
    feat.add_argument(
        "--no-filter",
        action="store_true",
        help="Non rimuovere header, footer e filigrane ripetute.",
    )
    feat.add_argument(
        "--header-zone",
        type=float,
        default=0.08,
        metavar="N",
        help=(
            "Altezza della zona header/footer come frazione della pagina "
            "(default: 0.08 = top e bottom 8%%). "
            "Aumenta se le intestazioni sono alte."
        ),
    )
    feat.add_argument(
        "--repeat-threshold",
        type=float,
        default=0.25,
        metavar="N",
        help=(
            "Soglia ripetizione header/footer: testo presente su più di questa "
            "frazione di pagine viene rimosso (default: 0.25 = >25%% delle pagine)."
        ),
    )
    feat.add_argument(
        "--keep-toc-pages",
        action="store_true",
        help=(
            "Mantieni le pagine di indice/sommario nel corpo EPUB. "
            "Di default vengono rimosse e sostituite con una TOC navigabile."
        ),
    )
    feat.add_argument(
        "--no-dedup",
        action="store_true",
        help="Non eseguire la deduplicazione degli asset grafici ripetuti.",
    )
    feat.add_argument(
        "--auto-background",
        action="store_true",
        help="Classifica automaticamente come sfondo gli asset ripetuti (senza prompt interattivo).",
    )
    feat.add_argument(
        "--pages",
        metavar="N o N-M",
        help="Elabora solo un intervallo di pagine. Esempi: '5', '1-20'. Utile per test.",
    )

    # ── Output ──────────────────────────────────────────────────────────────
    out = parser.add_argument_group("output")
    out.add_argument(
        "--output",
        default="output",
        metavar="DIR",
        help="Cartella di destinazione (default: ./output).",
    )

    # ── AI Vision backend ───────────────────────────────────────────────────
    api = parser.add_argument_group("AI vision backend")
    api.add_argument(
        "--ollama-model",
        default=None,
        metavar="MODELLO",
        help="Modello Ollama da usare (default: gemma4:12b). Esempi: llava, llama3.2-vision.",
    )
    api.add_argument(
        "--ollama-host",
        default=None,
        metavar="URL",
        help="URL del server Ollama (default: http://localhost:11434).",
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
        output_dir=str(Path(args.output) / book_name),
        book_name=book_name,
    )

    # Setup AI describer
    describer = None
    if config.describe_with_ai:
        from describer import create_describer

        try:
            describer = create_describer(
                backend="ollama",
                language=config.ai_language,
                ollama_model=args.ollama_model,
                ollama_host=args.ollama_host,
            )
        except (ValueError, ImportError) as e:
            print(f"  [warn] Describer non disponibile: {e}\n  Descrizioni AI disabilitate.")
            config.describe_with_ai = False

    # Stampa riepilogo
    print(f"\n{'=' * 50}")
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
    print(f"  Descrizioni AI: {'sì (ollama)' if config.describe_with_ai else 'no'}")
    print(f"  Output: {(Path(args.output) / book_name).resolve()}")
    print(f"{'=' * 50}\n")

    # Estrazione
    extractor = PDFExtractor(pdf_path, config)
    total_pages = extractor.page_count

    # Controlla se esiste già un asset_index.csv con modifiche manuali
    index_status = extractor.check_existing_index()
    if index_status == "protected":
        print("\n  [!] asset_index.csv esistente contiene entry modificate manualmente.")
        print("      Opzioni:")
        print("      [m] Merge — mantieni le entry modificate, aggiorna le altre (consigliato)")
        print("      [s] Sovrascrivi — ricrea l'index da zero (perdi le modifiche manuali)")
        print("      [q] Esci senza procedere")
        choice = input("  Scelta [m/s/q]: ").strip().lower()
        if choice == "q":
            print("  Operazione annullata.")
            return
        elif choice == "s":
            # Resetta l'index: non caricare nulla, verrà riscritto da zero
            extractor.asset_index = AssetIndex(extractor.asset_index.path)
            print("  Index verrà sovrascritto.")
        else:
            # Merge: l'index è già caricato con le entry protette da check_existing_index
            print("  Merge: le entry con modificato=si saranno preservate.")
    elif index_status == "clean":
        print("  asset_index.csv esistente senza modifiche manuali: verrà aggiornato.")

    # Gestione --pages
    page_start, page_end = 0, total_pages
    if args.pages:
        page_start, page_end = parse_page_range(args.pages, total_pages)
        print(f"  Elaboro pagine {page_start + 1}–{page_end} di {total_pages}")

    # Estrazione TOC (outline/bookmarks embedded nel PDF)
    toc = extractor.get_toc()
    if toc:
        print(f"  TOC trovata: {len(toc)} voci (livelli: {sorted(set(l for l, _, _ in toc))})")
    else:
        print("  TOC non trovata: userò euristica font per i capitoli")

    print(f"  Pagine totali: {total_pages}")

    import pdfplumber

    from extractor import filter_repeated_blocks

    pages_data = []
    with pdfplumber.open(str(pdf_path)) as plumb:
        for i in range(page_start, page_end):
            print(f"  Pagina {i + 1}/{page_end}...", end="\r", flush=True)
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

    ir_path = Path(config.output_dir) / "ir" / "document_ir.json"
    document_ir = build_document_ir(
        pages == list(pages_data),
        source_path=str(pdf_path),
        title=title,
        author=args.author,
        toc=toc,
    )
    save_document_ir(document_ir, ir_path)
    print(f"  ✓ IR: {ir_path}")

    # Build EPUB
    print("\n  Salvataggio asset index...")
    extractor.save_index()

    print("\n  Costruzione EPUB...")
    builder = EPUBBuilder(config, title, args.author, asset_index=extractor.asset_index)
    epub_path = builder.build(pages_data, toc=toc)

    # Riepilogo finale
    img_count = sum(len(p.images) for p in pages_data)
    vec_count = sum(len(p.vectors) for p in pages_data)
    tbl_count = sum(len(p.tables) for p in pages_data)
    # Struttura: output/NomePDF/NomePDF.epub + output/NomePDF/extracted/
    extracted = Path(config.output_dir) / "extracted"

    print(f"\n{'=' * 50}")
    print(f"  ✓ EPUB:      {epub_path}")
    print(f"  ✓ Immagini:  {img_count} → {extracted / 'images'}")
    print(f"  ✓ Vettoriali:{vec_count} → {extracted / 'vectors'}")
    print(f"  ✓ Tabelle:   {tbl_count} → {extracted / 'tables'}")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    main()
