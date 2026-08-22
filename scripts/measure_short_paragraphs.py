"""Conta i paragrafi corti in una uscita IR 2, secondo `Criterio_FormaMancante_v3.md` §2.

Il proxy e' quello del criterio, e nessuna parte di esso e' negoziabile qui:

- **paragrafo emesso** = nodo con ``kind == "text.paragraph"``, letto da
  ``document_ir2.json`` e non dal Markdown reso. I nodi ``asset.note`` hanno
  ``text=None`` per l'invariante a tre braccia di ``NodeIR2`` e non possono
  entrare nel conteggio; l'esclusione e' per ``kind`` ed e' ermetica.
- **paragrafo corto** = ``len(text.split()) <= 2``. Separazione sui soli spazi,
  **nessuna pulizia**: niente rimozione di punteggiatura, niente scarto dei
  token di soli simboli. Ogni pulizia sarebbe un giudizio, e un giudizio si puo'
  ricalibrare dopo aver visto l'esito. La chiusura di Milestone 38 ha mostrato
  un caso in cui i caratteri non sono cio' che sembrano: sui badge di DrW p.97
  ``a`` accentata e' U+00E1 e il simbolo del bersaglio e' la lettera ``o``.
- **pagina troppo corta** = meno di 10 paragrafi emessi. Non entra nella
  distribuzione e si elenca a parte: una quota su tre paragrafi e' rumore.

Non decide niente. Il criterio fa decidere il **verdetto di pagina** dato da una
persona sul ``page_ir2.md``; questo conteggio si riporta (§6.C) e serve al veto
del §6.B.

Uso::

    ./venv/bin/python scripts/measure_short_paragraphs.py <dir-o-json> [...]
    ./venv/bin/python scripts/measure_short_paragraphs.py --frammenti <dir> [...]

Ogni argomento e' una directory prodotta da ``scripts/prototype_ir2_page.py``
oppure un ``document_ir2.json``. L'etichetta della riga e' il nome della
directory, che per convenzione porta manuale e indice.

Con ``--frammenti`` stampa il **foglio di etichettatura** del §4 passo 5: ogni
paragrafo corto in **ordine di lettura**, con il suo testo e una casella vuota.
Le categorie sono quelle del §5 e non se ne aggiungono dopo aver visto i
frammenti. Il conteggio per pagina non compare nel foglio: il §4 chiede che la
quota non sia mostrata prima della fine dell'etichettatura, e dichiara che la
protezione e' parziale perche' chi etichetta vede comunque quante righe ha
davanti.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

CATEGORIES = (
    "titolo",
    "etichetta-valore",
    "arredo",
    "elenco",
    "spezzone",
    "corto-legittimo",
    "altro",
)

PARAGRAPH_KIND = "text.paragraph"
SHORT_WORDS = 2
MIN_PARAGRAPHS = 10


def _iter_nodes(document: dict) -> list[dict]:
    return [node for page in document["pages"] for node in page["nodes"]]


def measure(path: Path) -> tuple[int, int]:
    """Ritorna (paragrafi emessi, paragrafi corti) per una uscita IR 2."""

    document = json.loads(path.read_text(encoding="utf-8"))
    paragraphs = [n for n in _iter_nodes(document) if n["kind"] == PARAGRAPH_KIND]
    short = [n for n in paragraphs if len((n["text"] or "").split()) <= SHORT_WORDS]
    return len(paragraphs), len(short)


def short_fragments(path: Path) -> list[tuple[int, str]]:
    """I paragrafi corti in **ordine di lettura**, come (order, testo)."""

    document = json.loads(path.read_text(encoding="utf-8"))
    nodes = [
        node
        for node in _iter_nodes(document)
        if node["kind"] == PARAGRAPH_KIND
        and len((node["text"] or "").split()) <= SHORT_WORDS
    ]
    nodes.sort(key=lambda node: node["order"])
    return [(node["order"], node["text"] or "") for node in nodes]


def _resolve(argument: str) -> Path:
    path = Path(argument)
    return path / "document_ir2.json" if path.is_dir() else path


def _print_labelling_sheet(arguments: list[str]) -> None:
    print("# Foglio di etichettatura — `Criterio_FormaMancante_v3.md` §4 passo 5\n")
    print("Categorie ammesse, una sola per frammento, la dominante:\n")
    for category in CATEGORIES:
        print(f"- `{category}`")
    print(
        "\nSpareggio `titolo` / `etichetta-valore`: se sulla pagina il frammento ha un"
        "\nvalore attaccato — adiacente, sulla stessa riga o subito a destra o sotto, e si"
        "\nlegge come il suo valore — e' `etichetta-valore`. Altrimenti e' `titolo`."
        "\n\nL'etichetta si da' **sul render**, non sul Markdown. `altro` richiede una nota.\n"
    )
    for argument in arguments:
        path = _resolve(argument)
        if not path.is_file():
            print(f"MANCANTE: {path}", file=sys.stderr)
            continue
        label = path.parent.name or path.stem
        print(f"\n## {label}\n")
        print("| # | order | testo del frammento | categoria |")
        print("| --- | --- | --- | --- |")
        for position, (order, text) in enumerate(short_fragments(path), start=1):
            cell = text.replace("|", "\\|").replace("\n", " ")
            print(f"| {position} | {order} | `{cell}` | |")


def main() -> None:
    arguments = sys.argv[1:]
    if not arguments:
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)

    if arguments[0] == "--frammenti":
        _print_labelling_sheet(arguments[1:])
        return

    rows: list[tuple[str, int, int]] = []
    for argument in arguments:
        path = _resolve(argument)
        if not path.is_file():
            print(f"MANCANTE: {path}", file=sys.stderr)
            continue
        emitted, short = measure(path)
        label = path.parent.name or path.stem
        rows.append((label, emitted, short))

    print(f"{'pagina':<28} {'emessi':>7} {'corti':>7} {'quota':>8}")
    for label, emitted, short in rows:
        quota = f"{short / emitted:.1%}" if emitted else "n/d"
        flag = "  <10, fuori distribuzione" if emitted < MIN_PARAGRAPHS else ""
        print(f"{label:<28} {emitted:>7} {short:>7} {quota:>8}{flag}")

    usable = [(label, e, s) for label, e, s in rows if e >= MIN_PARAGRAPHS]
    excluded = len(rows) - len(usable)
    if not usable:
        print("\nnessuna pagina sopra i 10 paragrafi: distribuzione non calcolabile")
        return

    quotas = sorted(s / e for _, e, s in usable)
    print(
        f"\npagine nella distribuzione: {len(usable)}"
        f"   escluse perche' sotto i 10 paragrafi: {excluded}"
    )
    print(
        f"min {quotas[0]:.1%}   "
        f"mediana {statistics.median(quotas):.1%}   "
        f"max {quotas[-1]:.1%}"
    )


if __name__ == "__main__":
    main()
