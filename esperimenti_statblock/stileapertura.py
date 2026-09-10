"""Lo stile di apertura si DERIVA dallo schema, non da una soglia di dimensione.

Principio: le etichette dello schema localizzano i record (148/148, gia'
misurato). Lo stile di apertura e' allora lo stile che, ripetutamente, precede
la prima etichetta di schema di un record. Nessun confronto di dimensione,
nessun delta, nessun livello scelto: si guarda chi sta davanti.

Predizione, prima di eseguire: lo stile eletto e' quello dei nomi
(EvelethCleanRegular 12) e le regioni riprodotte coincidono con il riferimento.
"""
from __future__ import annotations
import re, unicodedata
from collections import Counter
import pymupdf

D = "/root/.claude/uploads/bf3622c8-0f6b-51f8-8f58-2201291c077f/2261baf5-DaggerheartSRD90925.pdf"
def squash(t): return re.sub(r"\s+", "", unicodedata.normalize("NFKC", t)).lower()
def clean(t):  return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", t)).strip()

PAGES = []
for p in pymupdf.open(D):
    ls = []
    for blk in p.get_text("dict")["blocks"]:
        for ln in blk.get("lines", []):
            sp = [s for s in ln["spans"] if s["text"].strip()]
            if sp: ls.append({"y0": ln["bbox"][1], "x0": ln["bbox"][0],
                              "spans": [(s["text"], (s["font"].split("+")[-1],
                                         round(s["size"],1), s["color"])) for s in sp]})
    if ls:
        xs = sorted({round(l["x0"],1) for l in ls})
        gr, cur = [], [xs[0]]
        for a, b in zip(xs, xs[1:]):
            (cur.append(b) if b-a <= 30.0 else (gr.append(cur), cur := [b]))
        gr.append(cur); bordi = [min(g) for g in gr]
        colof = lambda l: max(i for i, x in enumerate(bordi) if l["x0"] >= x-0.5)
        ls = sorted(ls, key=lambda l: (colof(l), round(l["y0"],1), l["x0"]))
    PAGES.append(ls)

def etichetta(l):
    st = [k for _, k in l["spans"]]
    if len(set(st)) < 2: return None
    return clean(l["spans"][0][0]).rstrip(":").strip()

freq = Counter()
for pg in PAGES:
    for l in pg:
        e = etichetta(l)
        if e: freq[e] += 1
SCHEMA = {k for k, c in freq.items() if c >= 20}

# --- corse di etichette di schema = nuclei di record ---
nuclei = []
for pi, pg in enumerate(PAGES):
    run, gap = [], 0
    for i, l in enumerate(pg):
        if etichetta(l) in SCHEMA: run.append(i); gap = 0
        elif run:
            gap += 1
            if gap > 2: nuclei.append((pi, run[0], run[-1])); run, gap = [], 0
    if run: nuclei.append((pi, run[0], run[-1]))

# --- chi sta davanti al nucleo? si contano gli stili delle righe precedenti ---
davanti = Counter()
for pi, a, b in nuclei:
    for k in range(1, 5):
        if a-k < 0: break
        l = PAGES[pi][a-k]
        for _, st in l["spans"]: davanti[(st, k)] += 1
print("stili che precedono un nucleo, per distanza (primi 8):")
for (st, k), c in davanti.most_common(8):
    print(f"   {st}  a {k} righe prima:  {c} volte")

# lo stile di apertura: quello che precede piu' nuclei, a QUALUNQUE distanza,
# e che non compare MAI dentro un nucleo (un'apertura non e' una riga di campo)
dentro = Counter()
for pi, a, b in nuclei:
    for l in PAGES[pi][a:b+1]:
        for _, st in l["spans"]: dentro[st] += 1
punteggio = Counter()
for (st, k), c in davanti.items():
    if dentro[st] == 0: punteggio[st] += c
print(f"\nstili candidati ad apertura (mai dentro un nucleo):")
for st, c in punteggio.most_common(5): print(f"   {st}: {c}")
APERTURA = punteggio.most_common(1)[0][0]
print(f"\n>>> stile di apertura DERIVATO: {APERTURA}")

# --- regioni con quello stile, confrontate col riferimento ---
def regioni_con(stile):
    out = []
    for pi, pg in enumerate(PAGES):
        idx = [i for i, l in enumerate(pg) if any(st == stile for _, st in l["spans"])]
        for n, i in enumerate(idx):
            out.append((pi, i, idx[n+1]-1 if n+1 < len(idx) else len(pg)-1))
    return out
vera = lambda z: "difficulty:" in squash("".join(t for l in PAGES[z[0]][z[1]:z[2]+1]
                                                 for t, _ in l["spans"]))
R = regioni_con(APERTURA)
Rv = [z for z in R if vera(z)]
print(f"    regioni totali: {len(R)}   di cui vere: {len(Rv)} (attese 148)")

rif = {}
for pi, pg in enumerate(PAGES):
    idx = [i for i, l in enumerate(pg) if max(k[1] for _, k in l["spans"]) >= 11.0]
    for n, i in enumerate(idx):
        z = (pi, i, idx[n+1]-1 if n+1 < len(idx) else len(pg)-1)
        if vera(z): rif[(pi, i)] = z
esatte = sum(1 for z in Rv if (z[0], z[1]) in rif and rif[(z[0], z[1])] == z)
print(f"    regioni IDENTICHE al riferimento a dimensione: {esatte}/{len(rif)}")
