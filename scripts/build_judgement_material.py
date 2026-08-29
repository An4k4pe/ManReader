"""Il materiale di giudizio, costruito da cio' che la pipeline **ha davvero fatto**.

Uno strumento solo per tutti i criteri, e nasce da quattro difetti che sono
costati altrettanti giri di giudizio. Vale la pena elencarli, perche' ognuno e'
una regola di questo modulo:

1. **arredo** — le voci mostrate senza il contesto della pagina, e i rilievi
   uscivano deboli. Qui si mostra **la pagina intera**.
2. **elenchi** — le voci troncate a fine riga fisica, e un rilievo e' arrivato su
   un difetto che non esisteva. Qui **non si tronca niente**.
3. **titoli v2** — il contorno cercava la stringa e mostrava la **prima**
   occorrenza del documento, non la riga giudicata. Qui si mostrano **tutte**.
4. **titoli v3** — il campione **ricalcolava** la classificazione, e la sua non
   era quella della pipeline: il builder unisce i titoli che vanno a capo prima
   di decidere, il campione no, e meta' giudizio ha risposto a una domanda che la
   pipeline non pone.

> **La regola che le riassume: il materiale non ricalcola niente.** Fa girare la
> pipeline e legge `document_ir2.json`, dove il `kind` del nodo dice gia' che cosa
> il meccanismo ha deciso, e `heading_level` dice il livello.

5. **titoli, primo giro con questo strumento** — leggere l'IR non basta:
   `document_ir2.json` contiene **tutti** i nodi, anche quelli che l'arredo toglie,
   perche' l'esclusione e' una decisione di **resa** e il contratto dice «il nodo
   resta, cambia la resa». Il materiale mostrava come marcati sei numeri di pagina
   che nel corpo non compaiono, e il giudizio li ha giustamente chiamati non
   titoli -- ma su cose che il lettore non vede. Ora i nodi esclusi si leggono da
   `review_ir2.md` e **non entrano nel materiale**.

**E una scelta di forma, che viene dallo stesso errore.** Il giudizio non ha piu'
due meta' -- «promosse» e «scartate» -- perche' la meta' scartata richiedeva di
ricostruire un insieme di candidati, ed e' li' che la classificazione divergeva.
Al suo posto: si mostra **la pagina intera** e si chiede, oltre al giudizio sulle
voci marcate, **che cosa sulla pagina avrebbe dovuto essere marcato e non lo e'**.
La copertura si misura guardando la pagina, non un insieme ricostruito.

Uso::

    ./venv/bin/python scripts/build_judgement_material.py --pdf-dir . \\
        --manuali BiD Dag DB --kind text.heading --seed 20261024 --pagine 12 \\
        --out <dir>
"""

from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
import sys
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RENDER_DPI = 150

KIND_LABEL = {
    "text.heading": "titolo",
    "text.list_item": "voce d'elenco",
    "text.list_item_ordered": "voce d'elenco numerato",
    "text.paragraph": "paragrafo",
}


def render(pdf: Path, index: int, out: Path, flags: list[str]) -> tuple[str, dict, str]:
    """Fa girare la pipeline e torna (markdown, documento IR 2, canale review)."""

    subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "prototype_ir2_page.py"),
            "--pdf", str(pdf),
            "--page-number", str(index + 1),
            "--output-dir", str(out),
            *flags,
        ],
        capture_output=True,
        check=False,
        cwd=PROJECT_ROOT,
    )
    markdown = out / "page_ir2.md"
    document = out / "document_ir2.json"
    review = out / "review_ir2.md"
    return (
        markdown.read_text(encoding="utf-8") if markdown.is_file() else "",
        json.loads(document.read_text(encoding="utf-8")) if document.is_file() else {},
        review.read_text(encoding="utf-8") if review.is_file() else "",
    )


_REVIEW_NODE = re.compile(r"^- `([^`]+)` kind=", re.M)


def excluded_node_ids(review: str) -> set[str]:
    """Gli id dei nodi che **non entrano nel corpo**, letti dal canale review.

    Servono perche' `document_ir2.json` li contiene tutti: l'esclusione
    dell'arredo e' una decisione di resa, non una proprieta' del nodo. Giudicare
    un nodo che il lettore non vede e' chiedere un parere su niente.
    """

    return set(_REVIEW_NODE.findall(review))


def nodes_of_kind(document: dict, kind: str, escluded: set[str]) -> list[dict]:
    """I nodi del genere richiesto **che entrano nel corpo**, in ordine di lettura.

    Letti, non dedotti: il `kind` viene dalla pipeline.
    """

    found = []
    for page in document.get("pages", ()):
        for node in sorted(page.get("nodes", ()), key=lambda n: n.get("order", 0)):
            if node.get("kind") == kind and node.get("node_id") not in escluded:
                found.append(node)
    return found


def occurrences(rendered: str, needle: str, window: int = 110) -> list[str]:
    """**Tutte** le occorrenze del testo nella resa, col loro contorno.

    Il confronto normalizza i due lati -- la resa inserisce il grassetto e toglie
    i marcatori -- e non si ferma alla prima: mostrarne una sola e' il difetto che
    ha fatto giudicare tre righe sul posto sbagliato.
    """

    bare = [(position, c.lower()) for position, c in enumerate(rendered) if c.isalnum()]
    joined = "".join(c for _p, c in bare)
    target = "".join(c for c in needle if c.isalnum()).lower()
    if not target:
        return []
    found, start = [], 0
    while True:
        at = joined.find(target, start)
        if at < 0:
            break
        left = bare[max(0, at - window)][0]
        right = bare[min(len(bare) - 1, at + len(target) + window)][0]
        found.append(rendered[left : right + 1].replace("\n", " "))
        start = at + 1
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--manuali", nargs="+", required=True)
    parser.add_argument("--kind", required=True, help="il `kind` di NodeIR2 da giudicare")
    parser.add_argument("--seed", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pagine", type=int, default=12, help="pagine campionate in tutto")
    parser.add_argument("--finestra", type=int, default=20, help="finestra della scansione")
    parser.add_argument(
        "--flags",
        nargs="*",
        default=["--arredo", "--elenchi"],
        help="i flag del prototipo: quello che si giudica e' cio' che esce con questi",
    )
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)

    # Le pagine si sorteggiano PRIMA di renderle: sorteggiare fra quelle che
    # hanno prodotto qualcosa sceglierebbe il campione in funzione dell'esito.
    candidati: list[tuple[str, int]] = []
    for name in args.manuali:
        path = args.pdf_dir / f"{name}.pdf"
        if not path.is_file():
            print(f"MANCANTE: {path}", file=sys.stderr)
            continue
        with fitz.open(path) as document:
            first = max(0, len(document) // 2 - args.finestra // 2)
            for index in range(first, min(len(document), first + args.finestra)):
                page = document[index]
                if page.rotation == 0 and tuple(page.mediabox) == tuple(page.cropbox):
                    candidati.append((name, index))
    scelte = rng.sample(candidati, min(args.pagine, len(candidati)))
    scelte.sort()

    etichetta = KIND_LABEL.get(args.kind, args.kind)
    righe = [
        f"# Pagine da giudicare — {etichetta}",
        "",
        f"Pagine: **{len(scelte)}**, sorteggiate con seed `{args.seed}` dichiarato prima.",
        "",
        "Per ogni pagina trovi **la pagina intera come esce**, senza tagli, e sotto",
        f"l'elenco di cio' che il meccanismo ha marcato come **{etichetta}**.",
        "",
        "**Due domande, e la seconda conta quanto la prima:**",
        "",
        f"1. ogni voce marcata **e' davvero un {etichetta}**?",
        f"2. c'e' sulla pagina qualcosa che **avrebbe dovuto essere un {etichetta}**",
        "   e non e' marcato? Elencalo.",
        "",
        "Il render della pagina sorgente sta accanto a questo file.",
        "",
        "---",
        "",
    ]
    chiave = ["# Chiave", "", "| pagina | manuale | idx | voci marcate |", "| --- | --- | --- | --- |"]

    workspace = args.out / "_resa"
    workspace.mkdir(exist_ok=True)
    for numero, (name, index) in enumerate(scelte, start=1):
        pdf = args.pdf_dir / f"{name}.pdf"
        rendered, document, review = render(
            pdf, index, workspace / f"{name}_{index}", args.flags
        )
        marcati = nodes_of_kind(document, args.kind, excluded_node_ids(review))
        stem = f"{name}_pagina{index + 1:04d}_idx{index:04d}"

        righe.append(f"## Pagina {numero:02d} — {name}, idx {index} — render `{stem}.png`")
        righe.append("")
        righe.append("**La pagina come esce:**")
        righe.append("")
        righe.append("```markdown")
        righe.extend(rendered.splitlines())
        righe.append("```")
        righe.append("")
        if marcati:
            righe.append(f"**Marcate come {etichetta}** — giudica ognuna:")
            righe.append("")
            for posizione, node in enumerate(marcati, start=1):
                testo = (node.get("text") or "").strip()
                livello = node.get("heading_level")
                suffisso = f" (livello {livello})" if livello else ""
                righe.append(f"- **{numero:02d}.{posizione}**{suffisso}: `{testo[:96]}`")
                for excerpt in occurrences(rendered, testo)[:3]:
                    righe.append(f"  - nella resa: …{excerpt[:150]}…")
                righe.append("  - Giudizio: ")
        else:
            righe.append(f"**Nessuna voce marcata come {etichetta}** su questa pagina.")
        righe.append("")
        righe.append(f"**Manca qualcosa?** Elenca cio' che avrebbe dovuto essere un {etichetta}:")
        righe.append("")
        righe.append("- ")
        righe.append("")
        righe.append("---")
        righe.append("")

        chiave.append(f"| {numero:02d} | {name} | {index} | {len(marcati)} |")
        target = args.out / f"{stem}.png"
        if not target.is_file():
            with fitz.open(pdf) as opened:
                target.write_bytes(opened[index].get_pixmap(dpi=RENDER_DPI).tobytes("png"))

    (args.out / "Pagine_da_giudicare.md").write_text("\n".join(righe) + "\n", encoding="utf-8")
    (args.out.parent / f"CHIAVE_{args.out.name}.md").write_text(
        "\n".join(chiave) + "\n", encoding="utf-8"
    )
    print(f"{len(scelte)} pagine, {sum(1 for _ in scelte)} rese, materiale in {args.out}")


if __name__ == "__main__":
    main()
