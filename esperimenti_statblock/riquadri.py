"""Separare i riquadri che il raggruppamento vettoriale ha fuso.

Passo 1 dell'ordine deciso il 10 settembre 2026; criterio in
CRITERIO_SEPARA_RIQUADRI.md.

Il producer non si tocca: `_DEFAULT_CLUSTER_MARGIN = 5.0` resta dov'e', e su
Daggerheart fonde riquadri distanti meno di 10 pt. Ma il candidato fuso porta i
singoli riquadri nei suoi `primitive_ids`, quindi chi lo consuma puo' separarli
senza rileggere la pagina e senza una soglia: il contenimento e la
condivisione di una riga sono relazioni, non misure.

Funzione pura, pensata per essere spostata (non copiata) nell'innesto IR 2
quando il passo 3 lo aprira'.
"""
from __future__ import annotations

from dataclasses import dataclass

from markdown_ir import _dentro

Bbox = tuple[float, float, float, float]


@dataclass(frozen=True)
class RiquadroSeparato:
    """Un pezzo di candidato.

    Porta `bbox` come `RegionCandidate`, perche' e' il solo campo che
    `markdown_ir.regioni_di_pagina` legge, e l'identita' del candidato da cui
    viene: separare non e' inventare un candidato nuovo."""

    bbox: Bbox
    primitive_ids: tuple[str, ...]
    candidate_id: str


def _contiene(esterno: Bbox, interno: Bbox) -> bool:
    return (
        esterno[0] <= interno[0]
        and esterno[1] <= interno[1]
        and interno[2] <= esterno[2]
        and interno[3] <= esterno[3]
    )


def _unione(a: Bbox, b: Bbox) -> Bbox:
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def riquadri_del_candidato(candidato, visivi: dict, righe: list[dict]) -> list:
    """I riquadri dentro un candidato, o il candidato stesso se ce n'e' uno.

    1. membri visivi del candidato;
    2. massimali: il bbox non sta dentro quello di un altro membro con bbox
       diverso (due membri con lo stesso bbox restano entrambi, e il punto 4
       li unisce);
    3. solo i massimali che contengono almeno una riga di testo;
    4. massimali che condividono una riga sono lo stesso riquadro;
    5. almeno due riquadri: il candidato si separa; altrimenti resta com'e'."""
    membri = [
        (pid, tuple(visivi[pid].bbox)) for pid in candidato.primitive_ids if pid in visivi
    ]
    massimali = [
        (pid, bbox)
        for pid, bbox in membri
        if not any(altro != bbox and _contiene(altro, bbox) for _q, altro in membri)
    ]
    gruppi: list[tuple[list[str], Bbox, set[int]]] = []
    for pid, bbox in massimali:
        indici = {i for i, riga in enumerate(righe) if _dentro(bbox, riga)}
        if not indici:
            continue
        pids = [pid]
        for gruppo in [g for g in gruppi if g[2] & indici]:
            gruppi.remove(gruppo)
            pids = gruppo[0] + pids
            bbox = _unione(bbox, gruppo[1])
            indici = indici | gruppo[2]
        gruppi.append((pids, bbox, indici))
    if len(gruppi) < 2:
        return [candidato]
    gruppi.sort(key=lambda g: (g[1][1], g[1][0]))
    return [
        RiquadroSeparato(
            bbox=bbox, primitive_ids=tuple(sorted(pids)), candidate_id=candidato.candidate_id
        )
        for pids, bbox, _indici in gruppi
    ]


def separa_riquadri(candidati: dict, righe: list[dict]) -> dict:
    """I candidati di `markdown_ir.candidati_di_pagina`, coi riquadri fusi
    separati. `divisi` conta i candidati che si sono separati."""
    pagina = candidati["primitive_page"]
    visivi = {
        p.primitive_id: p
        for p in list(pagina.drawing_primitives) + list(pagina.image_primitives)
    }
    fuori = dict(candidati)
    divisi = 0
    for chiave in ("embedded", "riquadri"):
        nuovi: list = []
        for candidato in candidati[chiave]:
            pezzi = riquadri_del_candidato(candidato, visivi, righe)
            divisi += 1 if len(pezzi) > 1 else 0
            nuovi.extend(pezzi)
        fuori[chiave] = nuovi
    fuori["divisi"] = divisi
    return fuori
