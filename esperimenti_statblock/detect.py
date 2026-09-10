"""Quattro detector di confini di scheda, scritti prima di eseguire.

Nessuno viene ritoccato dopo aver visto i risultati: se lo fosse, sarebbe
dichiarato come correzione e il risultato precedente resterebbe a verbale.
"""
from __future__ import annotations
import json, statistics as st, pymupdf
from collections import Counter

BASE = "/tmp/claude-0/-home-user-ManReader/bf3622c8-0f6b-51f8-8f58-2201291c077f/scratchpad/sb"
TOL = 3.0


def lines_of(page):
    """Righe con i loro span, ordinate per y. Chiave di stile per span."""
    out = []
    for blk in page.get_text("dict")["blocks"]:
        for ln in blk.get("lines", []):
            spans = [s for s in ln["spans"] if s["text"].strip()]
            if not spans:
                continue
            out.append({
                "y0": ln["bbox"][1], "y1": ln["bbox"][3],
                "x0": ln["bbox"][0], "x1": ln["bbox"][2],
                "text": "".join(s["text"] for s in spans),
                "keys": [(s["font"], round(s["size"], 1), s["color"]) for s in spans],
            })
    return sorted(out, key=lambda l: (round(l["y0"], 1), l["x0"]))


# --- chiavi di riga: due varianti, F3 -----------------------------------
def key_full(line):   # tutta la sequenza di stili della riga
    seen, o = set(), []
    for k in line["keys"]:
        if k not in seen:
            seen.add(k); o.append(k)
    return tuple(o)

def key_first(line):  # solo il primo span
    return line["keys"][0]


# --- D1: motivo di stile ricorrente -------------------------------------
def d1(pages_lines, keyfn):
    allk = [keyfn(l) for pg in pages_lines for l in pg]
    freq = Counter(allk)
    body = freq.most_common(1)[0][0]
    # apertura = stile che ricorre >=3 volte, non e' il corpo, ed e' seguito
    # entro 2 righe da una riga a piu' stili (etichetta+valore)
    openers = set()
    for k, n in freq.items():
        if k == body or n < 3:
            continue
        ok = 0
        for pg in pages_lines:
            ks = [keyfn(l) for l in pg]
            for i, kk in enumerate(ks):
                if kk != k:
                    continue
                if any(len(pg[j]["keys"]) >= 2 for j in range(i + 1, min(i + 3, len(ks)))):
                    ok += 1
        if ok >= 3:
            openers.add(k)
    recs = []
    for pi, pg in enumerate(pages_lines):
        ks = [keyfn(l) for l in pg]
        idx = [i for i, kk in enumerate(ks) if kk in openers]
        for n, i in enumerate(idx):
            end = idx[n + 1] - 1 if n + 1 < len(idx) else len(pg) - 1
            recs.append((pi, i, end))
    return recs


# --- D2: densita' di due punti / righe corte ----------------------------
def d2(pages_lines):
    recs = []
    for pi, pg in enumerate(pages_lines):
        if not pg:
            continue
        wmax = max(l["x1"] - l["x0"] for l in pg)
        run = []
        for i, l in enumerate(pg):
            short = (l["x1"] - l["x0"]) < 0.6 * wmax
            if ":" in l["text"] and short:
                run.append(i)
            else:
                if len(run) >= 3:
                    recs.append((pi, run[0], run[-1]))
                run = []
        if len(run) >= 3:
            recs.append((pi, run[0], run[-1]))
    return recs


# --- D3: gruppi separati da vuoti verticali -----------------------------
def d3(pages_lines):
    recs = []
    for pi, pg in enumerate(pages_lines):
        if len(pg) < 3:
            continue
        gaps = [pg[i + 1]["y0"] - pg[i]["y1"] for i in range(len(pg) - 1)]
        thr = st.median(gaps) * 1.5
        groups, cur = [], [0]
        for i, g in enumerate(gaps):
            if g > thr:
                groups.append(cur); cur = [i + 1]
            else:
                cur.append(i + 1)
        groups.append(cur)
        for gr in groups:
            if len(gr) >= 3:
                recs.append((pi, gr[0], gr[-1]))
    return recs


# --- D4: solo il corpo piu' grande (ingenuo) ----------------------------
def d4(pages_lines):
    sizes = [k[1] for pg in pages_lines for l in pg for k in l["keys"]]
    med = st.median(sizes)
    recs = []
    for pi, pg in enumerate(pages_lines):
        idx = [i for i, l in enumerate(pg) if max(k[1] for k in l["keys"]) > med]
        for n, i in enumerate(idx):
            end = idx[n + 1] - 1 if n + 1 < len(idx) else len(pg) - 1
            recs.append((pi, i, end))
    return recs


def gt_indices(pages, gt):
    """Confini veri come indici di riga, localizzando il testo del nome.

    Correzione dichiarata: la prima versione confrontava y di baseline (ground
    truth) con y di bbox (righe estratte), ~11pt di scarto. I detector non
    erano stati valutati; la loro logica non e' cambiata.
    """
    out = []
    for pi, pg in enumerate(pages):
        names = [i for i, l in enumerate(pg)
                 if any(g["page"] == pi and l["text"].strip() == g["name"] for g in gt)]
        for n, i in enumerate(names):
            end = names[n + 1] - 1 if n + 1 < len(names) else len(pg) - 1
            out.append((pi, i, end))
    return out


def score(recs, truth):
    tset = set(truth)
    tp = len(tset & set(recs))
    return tp, len(recs) - tp, len(tset) - tp, sum(1 for r in recs if r not in tset and r[0] >= 2)


def main():
    doc = pymupdf.open(BASE + "/synth.pdf")
    pages = [lines_of(p) for p in doc]
    gt = json.load(open(BASE + "/ground_truth.json"))
    truth = gt_indices(pages, gt)
    print(f"righe per pagina: {[len(p) for p in pages]}   schede vere: {len(truth)}\n")
    print(f"{'metodo':34} {'TP':>3} {'FP':>3} {'FN':>3} {'FP su pagine negative':>22}")
    print("-" * 92)
    for name, recs in [
        ("D1 motivo stile (chiave completa)", d1(pages, key_full)),
        ("D1 motivo stile (primo span)",      d1(pages, key_first)),
        ("D2 due punti + righe corte",        d2(pages)),
        ("D3 vuoti verticali",                d3(pages)),
        ("D4 corpo piu' grande (ingenuo)",    d4(pages)),
    ]:
        tp, fp, fn, fpn = score(recs, truth)
        print(f"{name:34} {tp:>3} {fp:>3} {fn:>3} {fpn:>22}")

    print("\n--- F3: quante righe hanno span di stili diversi ---")
    mixed = sum(1 for pg in pages for l in pg if len(set(l['keys'])) > 1)
    tot = sum(len(pg) for pg in pages)
    print(f"righe con piu' di uno stile: {mixed}/{tot}")
    print(f"chiavi di stile distinte, variante completa: {len({key_full(l) for pg in pages for l in pg})}")
    print(f"chiavi di stile distinte, variante primo span: {len({key_first(l) for pg in pages for l in pg})}")

main()
