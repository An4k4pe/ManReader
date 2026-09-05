"""Rilevamento SENZA alcun uso della dimensione del carattere.
Predizione in CRITERIO_SENZA_CORPO.md, scritta prima di eseguire."""
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

# --- etichetta SENZA dimensione: primo span di una riga a piu' stili ---
def etichetta(l):
    st = [k for _, k in l["spans"]]
    if len(set(st)) < 2: return None
    return clean(l["spans"][0][0]).rstrip(":").strip()

freq = Counter()
for pg in PAGES:
    for l in pg:
        e = etichetta(l)
        if e: freq[e] += 1
SCHEMA = {k for k, c in freq.items() if c >= 20}     # ricorrenti nel documento
print(f"etichette ricorrenti (>=20 occorrenze) senza usare la dimensione: {len(SCHEMA)}")
print("   ", sorted(SCHEMA)[:16])

# --- record = corsa di righe con etichette dello schema, max 2 righe di stacco ---
regioni = []
for pi, pg in enumerate(PAGES):
    run, gap = [], 0
    for i, l in enumerate(pg):
        if etichetta(l) in SCHEMA:
            run.append(i); gap = 0
        elif run:
            gap += 1
            if gap > 2:
                regioni.append((pi, run[0], run[-1])); run, gap = [], 0
    if run: regioni.append((pi, run[0], run[-1]))
print(f"regioni trovate senza dimensione: {len(regioni)}")

vera = lambda z: "difficulty:" in squash("".join(t for l in PAGES[z[0]][z[1]:z[2]+1]
                                                 for t, _ in l["spans"]))
vr = [z for z in regioni if vera(z)]
print(f"di cui contengono 'Difficulty:': {len(vr)}   (attese 148)")

# --- confronto di estensione con il risultato che usa la dimensione ---
rif = {}
for pi, pg in enumerate(PAGES):
    idx = [i for i, l in enumerate(pg) if max(k[1] for _, k in l["spans"]) >= 11.0]
    for n, i in enumerate(idx):
        z = (pi, i, idx[n+1]-1 if n+1 < len(idx) else len(pg)-1)
        if vera(z): rif[(pi, i)] = z
print(f"regioni di riferimento (con dimensione): {len(rif)}")

testa = coda = esatte = 0
for (pi, i), (_, a, b) in rif.items():
    cand = [r for r in vr if r[0] == pi and a <= r[1] <= b]
    if not cand: continue
    r = cand[0]
    dt, dc = r[1] - a, b - r[2]
    testa += dt; coda += dc
    if dt == 0 and dc == 0: esatte += 1
print(f"\nsu {len(rif)} schede di riferimento:")
print(f"   righe perse in TESTA (la riga-nome e simili): {testa}")
print(f"   righe perse in CODA  (features, prosa):       {coda}")
print(f"   regioni con estensione IDENTICA:              {esatte}")

print("\n" + "="*66)
print("SECONDA PROVA — i confini dalle SOLE localizzazioni, per affiancamento.")
print("Predizione: se le etichette localizzano tutti i record, allora il record N")
print("va dalla fine del record N-1 all'inizio del record N+1, e la dimensione")
print("non serve piu' nemmeno per l'estensione.")

# regioni-nucleo (solo etichette) ordinate per colonna/pagina; poi si affiancano
per_pag = {}
for z in vr: per_pag.setdefault(z[0], []).append(z)
affianca = []
for pi, zs in per_pag.items():
    zs = sorted(zs, key=lambda z: z[1])
    # correzione: il confine fra due record si mette UNA volta sola.
    # inizio esteso del record n = fine del nucleo n-1 + 1; il record n finisce
    # subito prima dell'inizio esteso del record n+1.
    est = [0 if n == 0 else zs[n-1][2] + 1 for n in range(len(zs))]
    for n, z in enumerate(zs):
        fine = est[n+1] - 1 if n+1 < len(zs) else len(PAGES[pi]) - 1
        affianca.append((pi, est[n], fine))

testa = coda = esatte = 0; conf = []
for (pi, i), (_, a, b) in rif.items():
    cand = [r for r in affianca if r[0] == pi and r[1] <= a <= r[2]]
    if not cand: continue
    r = cand[0]
    dt, dc = a - r[1], r[2] - b       # ora possono essere in ECCESSO
    testa += abs(dt); coda += abs(dc)
    conf.append((dt, dc))
    if dt == 0 and dc == 0: esatte += 1
print(f"\nsu {len(rif)} schede di riferimento:")
print(f"   scarto totale in testa: {testa} righe   in coda: {coda} righe")
print(f"   regioni con estensione IDENTICA al riferimento: {esatte}")
from collections import Counter as C2
print(f"   distribuzione scarto testa: {dict(sorted(C2(d for d,_ in conf).items())[:6])}")
print(f"   distribuzione scarto coda:  {dict(sorted(C2(c for _,c in conf).items())[:6])}")

# conservazione: le regioni affiancate coprono tutto il testo delle pagine 37-55?
tot = sum(len("".join(t for t,_ in l["spans"]).strip()) for i in range(37,56) for l in PAGES[i])
cop = sum(len("".join(t for t,_ in l["spans"]).strip())
          for r in affianca if 37 <= r[0] <= 55 for l in PAGES[r[0]][r[1]:r[2]+1])
print(f"\n   copertura del testo pagine 37-55: {cop}/{tot} ({100*cop/tot:.1f}%)")
