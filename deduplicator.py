"""
deduplicator.py — Rilevamento e gestione di asset grafici ripetuti.

Problema: i manuali GDR riccamente illustrati spesso hanno sfondi di
pergamena, ribbon decorativi, bordi di pagina o watermark che si ripetono
su ogni pagina o su ogni pagina di un certo tipo. Estrarre questi elementi
come asset separati per ogni pagina produce decine di file identici e
ingombra l'EPUB con centinaia di riferimenti inutili.

Soluzione: dopo l'estrazione, confronta gli asset per hash e presenta
all'utente i gruppi di elementi identici che superano una soglia di
ripetizione, con tre opzioni:
  - sfondo: salva una copia in _extracted/backgrounds/, rimuove dall'EPUB
  - ignora: cancella tutti i file estratti, rimuove dall'EPUB
  - mantieni: nessuna modifica (trattato come asset normale)

Hashing:
  - Immagini raster: MD5 dei byte grezzi dell'immagine
  - Vettoriali: MD5 del contenuto SVG salvato su disco
  Entrambi sono deterministici: due asset identici estratti da pagine diverse
  avranno lo stesso hash se il contenuto PDF è identico.
"""

import hashlib
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

from extractor import ImageBlock, PageData, VectorBlock


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class AssetGroup:
    """Un gruppo di asset grafici identici trovati su più pagine."""
    kind: str                                          # "image" o "vector"
    asset_hash: str                                    # MD5 hex
    pages: List[int]                                   # page_num (0-based) delle occorrenze
    instances: List[Union[ImageBlock, VectorBlock]]    # tutti i blocchi
    representative: Union[ImageBlock, VectorBlock]     # prima occorrenza (file da tenere)


# ---------------------------------------------------------------------------
# Rilevamento
# ---------------------------------------------------------------------------

def find_repeated_assets(
    pages: List[PageData],
    threshold: float = 0.15,
) -> List[AssetGroup]:
    """
    Trova gruppi di immagini/vettoriali identici che compaiono su più pagine.

    threshold: frazione di pagine. Un asset che appare su >threshold*N pagine
    viene considerato potenzialmente decorativo/ripetuto.
    Default 0.15 = >15% delle pagine. Su un manuale di 300 pagine: >45 pagine.

    Nota: due asset identici estratti da posizioni diverse della stessa pagina
    (es. due ribbon ai lati dello stesso foglio) hanno lo stesso hash ma
    page_num diversi — vengono comunque raggruppati. Se vuoi distinguerli,
    abbassa la threshold.
    """
    if not pages:
        return []

    n_pages = len(pages)
    min_occurrences = max(2, int(n_pages * threshold))

    # hash → lista di (block, page_num)
    from collections import defaultdict
    hash_map: dict = defaultdict(list)

    for page in pages:
        for img in page.images:
            h = _hash_image(img)
            if h:
                hash_map[("image", h)].append((img, page.page_num))
        for vec in page.vectors:
            h = _hash_vector(vec)
            if h:
                hash_map[("vector", h)].append((vec, page.page_num))

    groups: List[AssetGroup] = []
    for (kind, asset_hash), occurrences in hash_map.items():
        # Conta pagine distinte (non occorrenze totali)
        distinct_pages = list(dict.fromkeys(pn for _, pn in occurrences))
        if len(distinct_pages) < min_occurrences:
            continue

        instances = [block for block, _ in occurrences]
        groups.append(AssetGroup(
            kind=kind,
            asset_hash=asset_hash,
            pages=distinct_pages,
            instances=instances,
            representative=instances[0],
        ))

    # Ordina per numero di occorrenze decrescente (i più ripetuti prima)
    groups.sort(key=lambda g: len(g.pages), reverse=True)
    return groups


# ---------------------------------------------------------------------------
# Applicazione decisioni
# ---------------------------------------------------------------------------

def apply_decision(
    pages: List[PageData],
    group: AssetGroup,
    decision: str,
    backgrounds_dir: Optional[Path] = None,
) -> List[PageData]:
    """
    Applica la decisione dell'utente a un gruppo di asset ripetuti.

    decision:
      "background" → salva la prima occorrenza in backgrounds_dir,
                     cancella le altre, rimuove tutti dall'EPUB
      "ignore"     → cancella tutti i file estratti, rimuove dall'EPUB
      "keep"       → non fa nulla

    Restituisce la lista di PageData aggiornata.
    """
    if decision == "keep":
        return pages

    paths_to_remove = {inst.saved_path for inst in group.instances if inst.saved_path}

    if decision == "background":
        if backgrounds_dir:
            backgrounds_dir.mkdir(parents=True, exist_ok=True)
            rep_path = Path(group.representative.saved_path)
            if rep_path.exists():
                dest = backgrounds_dir / rep_path.name
                shutil.copy2(rep_path, dest)
                # Copia anche il .txt descrizione se esiste
                txt = rep_path.with_suffix(".txt")
                if txt.exists():
                    shutil.copy2(txt, dest.with_suffix(".txt"))
                print(f"    → Salvato come sfondo: {dest.name}")

    # Cancella tutti i file estratti del gruppo
    for inst in group.instances:
        if inst.saved_path:
            p = Path(inst.saved_path)
            if p.exists():
                p.unlink()
            txt = p.with_suffix(".txt")
            if txt.exists():
                txt.unlink()

    # Rimuove le istanze dai PageData
    return _remove_from_pages(pages, paths_to_remove)


# ---------------------------------------------------------------------------
# Interazione utente
# ---------------------------------------------------------------------------

def interactive_dedup(
    pages: List[PageData],
    groups: List[AssetGroup],
    backgrounds_dir: Path,
    n_total_pages: int,
) -> List[PageData]:
    """
    Presenta ogni gruppo all'utente e chiede cosa fare.
    Usato in modalità interattiva (terminale).
    """
    print(f"\n  Trovati {len(groups)} gruppi di asset ripetuti:\n")

    for i, group in enumerate(groups):
        kind_label = "Immagine raster" if group.kind == "image" else "Vettoriale"
        rep_name = Path(group.representative.saved_path).name if group.representative.saved_path else "?"
        pct = len(group.pages) / n_total_pages * 100

        print(f"  [{i+1}/{len(groups)}] {kind_label}")
        print(f"      File: {rep_name}")
        print(f"      Pagine: {len(group.pages)} ({pct:.0f}% del documento)")
        print(f"      Prime occorrenze: {group.pages[:8]}{' ...' if len(group.pages) > 8 else ''}")
        print()
        print("      [s] Salva come sfondo (una copia, rimosso dall'EPUB)")
        print("      [i] Ignora (cancella tutti i file estratti)")
        print("      [m] Mantieni (tratta come asset normale)")
        print("      [?] Mostra path completo del file rappresentativo")
        print()

        while True:
            choice = input("      Scelta [s/i/m, default=s]: ").strip().lower()
            if choice == "?":
                print(f"      {group.representative.saved_path}")
                print()
                continue
            if choice in ("", "s", "i", "m"):
                break
            print("      Inserisci s, i, m o ? ")

        decision_map = {"": "background", "s": "background", "i": "ignore", "m": "keep"}
        decision = decision_map[choice]
        pages = apply_decision(pages, group, decision, backgrounds_dir)
        print()

    return pages


def auto_dedup(
    pages: List[PageData],
    groups: List[AssetGroup],
    backgrounds_dir: Path,
) -> List[PageData]:
    """
    Modalità automatica: salva tutti i gruppi ripetuti come sfondo senza chiedere.
    Usata con --auto-background.
    """
    for group in groups:
        kind_label = "immagine" if group.kind == "image" else "vettoriale"
        name = Path(group.representative.saved_path).name if group.representative.saved_path else "?"
        print(f"  Auto-sfondo: {kind_label} {name} ({len(group.pages)} pagine)")
        pages = apply_decision(pages, group, "background", backgrounds_dir)
    return pages


# ---------------------------------------------------------------------------
# Utilità interne
# ---------------------------------------------------------------------------

def _hash_image(img: ImageBlock) -> Optional[str]:
    """MD5 dei byte dell'immagine. Deterministico: stessa immagine = stesso hash."""
    if not img.image_data:
        return None
    return hashlib.md5(img.image_data).hexdigest()


def _hash_vector(vec: VectorBlock) -> Optional[str]:
    """MD5 del contenuto SVG salvato su disco."""
    if not vec.saved_path:
        return None
    path = Path(vec.saved_path)
    if not path.exists():
        return None
    try:
        content = path.read_bytes()
        return hashlib.md5(content).hexdigest()
    except Exception:
        return None


def _remove_from_pages(
    pages: List[PageData],
    paths_to_remove: set,
) -> List[PageData]:
    """Ricostruisce i PageData senza le istanze specificate (per saved_path)."""
    result = []
    for page in pages:
        result.append(PageData(
            page_num=page.page_num,
            text_blocks=page.text_blocks,
            images=[img for img in page.images  if img.saved_path not in paths_to_remove],
            vectors=[vec for vec in page.vectors if vec.saved_path not in paths_to_remove],
            tables=page.tables,
            width=page.width,
            height=page.height,
        ))
    return result
