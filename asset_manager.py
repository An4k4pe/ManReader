"""
ManReader — asset_manager: applica modifiche dall'asset_index.csv all'EPUB.

USO
  python asset_manager.py <cartella_output>

ESEMPI
  python asset_manager.py output/NomePDF/
  python asset_manager.py output/DnD5e_Players_Handbook/

FLUSSO
  1. Legge extracted/asset_index.csv nella cartella indicata.
  2. Trova le entry con  modificato=si  (modificate manualmente nel CSV).
  3. Rinomina i file fisici nella sottocartella corretta (images/vectors/tables/).
  4. Aggiorna i file .xhtml dell'EPUB: titolo visibile inline e path in footnote.
  5. Resetta  modificato=no  nelle entry applicate e salva il CSV.

COME MODIFICARE UN ASSET
  1. Apri  extracted/asset_index.csv  con qualsiasi editor o foglio di calcolo.
  2. Modifica  nome_file  e/o  titolo  nella riga dell'asset da rinominare.
  3. Imposta  modificato=si  su quella riga.
  4. Salva il CSV ed esegui questo script.

NOTE
  - Il campo  sha  è la chiave stabile: il rename non lo modifica.
  - La ricerca del file su disco avviene per SHA, non per nome:
    funziona anche se il file era già stato rinominato a mano.
  - Le entry con  modificato=no  vengono ignorate.
"""

import argparse
import csv
import re
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Lettura dell'index
# ---------------------------------------------------------------------------

_INDEX_FIELDS = ["sha", "nome_file", "tipo", "pagina", "titolo", "descrizione", "modificato"]

_SUBDIR = {
    "image":  "images",
    "vector": "vectors",
    "table":  "tables",
}


def load_index(index_path: Path) -> List[dict]:
    if not index_path.exists():
        print(f"  [errore] asset_index.csv non trovato: {index_path}")
        sys.exit(1)
    entries = []
    with open(index_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(dict(row))
    return entries


def save_index(index_path: Path, entries: List[dict]) -> None:
    with open(index_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_INDEX_FIELDS)
        writer.writeheader()
        for entry in entries:
            writer.writerow(entry)


# ---------------------------------------------------------------------------
# Ricerca del file attuale su disco per un dato SHA
# ---------------------------------------------------------------------------

def find_current_file(extracted_dir: Path, tipo: str, sha: str) -> Optional[Path]:
    """
    Trova il file corrispondente a questo SHA nella sottocartella giusta.
    Cerca per contenuto (ricalcola MD5) perché il file potrebbe essere già
    stato rinominato manualmente senza aggiornare il CSV.
    """
    import hashlib
    subdir = extracted_dir / _SUBDIR.get(tipo, "images")
    if not subdir.exists():
        return None
    for f in subdir.iterdir():
        if f.is_file():
            try:
                content_sha = hashlib.md5(f.read_bytes()).hexdigest()
                if content_sha == sha:
                    return f
            except Exception:
                continue
    return None


# ---------------------------------------------------------------------------
# Patch dei file XHTML dentro l'EPUB (zip)
# ---------------------------------------------------------------------------

def patch_epub(epub_path: Path, old_fname: str, new_fname: str,
               old_title: str, new_title: str, tipo: str) -> int:
    """
    Apre l'EPUB (zip), cerca nei file .xhtml le occorrenze di old_fname
    e old_title, le sostituisce con new_fname e new_title.
    Restituisce il numero di file xhtml modificati.

    Struttura delle stringhe cercate (da epub_builder.py):
      Inline:   &#128444; Titolo Vecchio   oppure  &#9672; Titolo Vecchio
      Footnote: extracted/images/vecchio-nome.png
    """
    if not epub_path.exists():
        print(f"  [warn] EPUB non trovato: {epub_path}")
        return 0

    subdir = _SUBDIR.get(tipo, "images")
    old_path_ref = f"extracted/{subdir}/{old_fname}"
    new_path_ref = f"extracted/{subdir}/{new_fname}"

    # Leggi tutto il contenuto dello zip in memoria
    with zipfile.ZipFile(epub_path, "r") as zin:
        names = zin.namelist()
        contents: Dict[str, bytes] = {}
        for name in names:
            contents[name] = zin.read(name)

    modified = 0
    for name in names:
        if not name.endswith(".xhtml"):
            continue
        try:
            text = contents[name].decode("utf-8")
        except Exception:
            continue

        new_text = text

        # 1. Sostituisce il path nella footnote (nome file fisico)
        if old_path_ref in new_text:
            new_text = new_text.replace(old_path_ref, new_path_ref)

        # 2. Sostituisce il titolo nel testo visibile inline
        #    Cerca la forma:  >&#NNNNN; Titolo Vecchio</a>  oppure >&#NNNNN; Titolo Vecchio
        #    Il titolo è HTML-escaped, quindi usiamo html.escape per sicurezza
        import html as _html
        esc_old = _html.escape(old_title)
        esc_new = _html.escape(new_title)
        if esc_old and esc_old != esc_new and esc_old in new_text:
            # Sostituisce solo nel contesto di asset-ref per evitare
            # false sostituzioni su testo identico nel corpo del manuale
            new_text = _replace_in_asset_context(new_text, esc_old, esc_new)

        if new_text != text:
            contents[name] = new_text.encode("utf-8")
            modified += 1

    if modified == 0:
        return 0

    # Riscrivi lo zip con i file modificati
    tmp_path = epub_path.with_suffix(".epub.tmp")
    with zipfile.ZipFile(epub_path, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for name in names:
                zout.writestr(name, contents[name])
    tmp_path.replace(epub_path)
    return modified


def _replace_in_asset_context(html_text: str, old_title: str, new_title: str) -> str:
    """
    Sostituisce old_title con new_title solo all'interno dei blocchi
    class="asset-ref" e class="note-ref", per evitare false sostituzioni
    su eventuali occorrenze identiche nel testo del manuale.
    """
    # Pattern: dentro un tag <p class="asset-ref"> o un <a class="note-ref">
    # cattura il titolo dopo l'icona unicode (&#NNNNN; seguito da spazio)
    pattern = re.compile(
        r'(class="(?:asset-ref|note-ref)"[^>]*>(?:.*?)&#\d+;\s*)' + re.escape(old_title),
        re.DOTALL
    )
    return pattern.sub(r'\g<1>' + new_title, html_text)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="asset_manager",
        description="Applica modifiche dall'asset_index.csv all'EPUB già buildato.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
        add_help=False,
    )
    parser.add_argument(
        "-h", "--help", action="help", default=argparse.SUPPRESS,
        help="Mostra questo messaggio ed esci.",
    )
    parser.add_argument(
        "output_dir", metavar="CARTELLA",
        help=(
            "Cartella di output che contiene l'EPUB e la sottocartella extracted/. "
            "Esempio: output/NomePDF/"
        ),
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help=(
            "Mostra cosa verrebbe fatto senza applicare nessuna modifica. "
            "Utile per verificare prima di procedere."
        ),
    )

    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    extracted_dir = out_dir / "extracted"
    index_path = extracted_dir / "asset_index.csv"

    # Trova l'EPUB nella cartella output
    epub_files = list(out_dir.glob("*.epub"))
    if not epub_files:
        print(f"  [errore] Nessun file .epub trovato in {out_dir}")
        sys.exit(1)
    if len(epub_files) > 1:
        print(f"  [warn] Trovati più EPUB, uso il primo: {epub_files[0].name}")
    epub_path = epub_files[0]

    if args.dry_run:
        print(f"\n  [dry-run] Nessuna modifica verrà applicata.\n")

    print(f"\n  EPUB:  {epub_path}")
    print(f"  Index: {index_path}")

    entries = load_index(index_path)
    protected = [e for e in entries if e.get("modificato", "no").strip().lower() == "si"]

    if not protected:
        print("\n  Nessuna entry con modificato=si trovata. Nulla da applicare.")
        return

    print(f"\n  Entry da applicare: {len(protected)}\n")

    applied = 0
    errors = 0

    for entry in protected:
        sha       = entry["sha"].strip()
        new_name  = entry["nome_file"].strip()
        tipo      = entry["tipo"].strip()
        new_title = entry["titolo"].strip() or Path(new_name).stem

        subdir = extracted_dir / _SUBDIR.get(tipo, "images")

        # Trova il file corrente su disco tramite SHA
        current_file = find_current_file(extracted_dir, tipo, sha)
        if not current_file:
            print(f"  [warn] SHA {sha[:8]}... — file non trovato su disco, skip")
            errors += 1
            continue

        old_name  = current_file.name
        old_title = Path(old_name).stem

        # --- Rename fisico se il nome è cambiato ---
        if old_name != new_name:
            new_path = subdir / new_name
            if args.dry_run:
                print(f"  [dry-run] Rinominerebbe: {old_name} → {new_name}")
            elif new_path.exists() and new_path != current_file:
                print(f"  [warn] {new_name} già esiste su disco, skip rename fisico")
            else:
                current_file.rename(new_path)
                print(f"  ✓ Rinominato: {old_name} → {new_name}")
        else:
            print(f"  · Nome invariato: {old_name}")

        # --- Patch EPUB ---
        if args.dry_run:
            print(f"    [dry-run] Aggiornerebbe EPUB: '{old_title}' → '{new_title}', "
                  f"path {old_name} → {new_name}")
        else:
            n = patch_epub(epub_path, old_name, new_name, old_title, new_title, tipo)
            if n > 0:
                print(f"    ✓ EPUB aggiornato ({n} capitoli modificati)")
            else:
                print(f"    · Nessuna occorrenza trovata nell'EPUB "
                      f"(normale se l'asset non aveva descrizione AI)")

        # Resetta il flag solo se non dry-run
        if not args.dry_run:
            entry["modificato"] = "no"
        applied += 1

    # Salva il CSV aggiornato
    if not args.dry_run:
        save_index(index_path, entries)

    print(f"\n{'='*50}")
    if args.dry_run:
        print(f"  [dry-run] Sarebbero state applicate: {applied}  Errori: {errors}")
    else:
        print(f"  Applicate: {applied}  Errori: {errors}")
        print(f"  asset_index.csv aggiornato.")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
