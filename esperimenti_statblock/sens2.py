"""Analisi di sensibilita': quali costanti reggono il risultato, e quali no.

Ogni costante che ho scelto io viene fatta variare da sola, tenendo le altre
al valore usato. Se il risultato regge su un intervallo largo, la costante non
e' portante e il metodo trasferisce; se cambia a ogni passo, e' taratura su
questo manuale e non trasferisce.
"""
from __future__ import annotations
import re, unicodedata
from collections import Counter
import pymupdf

D = "/root/.claude/uploads/bf3622c8-0f6b-51f8-8f58-2201291c077f/2261baf5-DaggerheartSRD90925.pdf"
def squash(t): return re.sub(r"\s+", "", unicodedata.normalize("NFKC", t)).lower()
def clean(t):  return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", t)).strip()

RAW = []
for p in pymupdf.open(D):
    ls = []
    for blk in p.get_text("dict")["blocks"]:
        for ln in blk.get("lines", []):
            sp = [s for s in ln["spans"] if s["text"].strip()]
            if sp: ls.append({"y0": ln["bbox"][1], "x0": ln["bbox"][0],
                              "spans": [(s["text"], (s["font"].split("+")[-1],
                                         round(s["size"],1), s["color"])) for s in sp]})
    RAW.append(ls)

P0 = dict(col_gap=30.0, open_delta=1.0, lab_delta=0.6, min_campi=3, lab_ric=3,
          nucleo_ratio=0.5, nucleo_distinte=3, condivise_frac=0.05, jaccard=0.4,
          obbl_frac=0.90, noti_frac=0.05, min_gruppo=5, min_obbl=3, lift=1.5)

def run(P):
    pages = []
    for ls in RAW:
        if not ls: pages.append([]); continue
        xs = sorted({round(l["x0"],1) for l in ls})
        gr, cur = [], [xs[0]]
        for a, b in zip(xs, xs[1:]):
            (cur.append(b) if b-a <= P["col_gap"] else (gr.append(cur), cur := [b]))
        gr.append(cur); bordi = [min(g) for g in gr]
        colof = lambda l: max(i for i, x in enumerate(bordi) if l["x0"] >= x-0.5)
        pages.append(sorted(ls, key=lambda l: (colof(l), round(l["y0"],1), l["x0"])))

    ch = Counter()
    for pg in pages:
        for l in pg:
            for t, k in l["spans"]: ch[k] += len(t.strip())
    BS = ch.most_common(1)[0][0][1]

    zones = []
    for pi, pg in enumerate(pages):
        idx = [i for i, l in enumerate(pg)
               if max(k[1] for _, k in l["spans"]) > BS + P["open_delta"]]
        for n, i in enumerate(idx):
            zones.append((pi, i, idx[n+1]-1 if n+1 < len(idx) else len(pg)-1))
        if idx and idx[0] > 0: zones.append((pi, -1, idx[0]-1))
        if not idx and pg:     zones.append((pi, -1, len(pg)-1))

    def labs(z):
        pi, a, b = z
        c = Counter()
        for l in pages[pi][max(a,0):b+1]:
            for t, k in l["spans"]: c[k] += len(t.strip())
        body = c.most_common(1)[0][0] if c else None
        out = []
        for l in pages[pi][max(a,0)+(1 if a >= 0 else 0):b+1]:
            sp, i = l["spans"], 0
            while i < len(sp):
                t, k = sp[i]
                if k != body and body and k[1] <= body[1]+P["lab_delta"] \
                   and i+1 < len(sp) and sp[i+1][1] == body:
                    out.append(clean(t).rstrip(":").strip()); i += 2
                else: i += 1
        return out
    EZ = {z: labs(z) for z in zones}
    def vera(z):
        pi, a, b = z
        return "difficulty:" in squash("".join(t for l in pages[pi][max(a,0):b+1]
                                               for t, _ in l["spans"]))

    tutte = Counter(k for v in EZ.values() for k in v)
    ric = {k for k, c in tutte.items() if c >= P["lab_ric"]}
    nucleo = [z for z in zones if len(EZ[z]) >= P["min_campi"]
              and sum(1 for k in EZ[z] if k in ric)/len(EZ[z]) >= P["nucleo_ratio"]
              and len(set(EZ[z])) >= P["nucleo_distinte"]]
    if not nucleo: return 0, 0, 0
    cond = Counter()
    for z in nucleo: cond.update(set(EZ[z]))
    CD = {k for k, c in cond.items() if c >= max(3, P["condivise_frac"]*len(nucleo))}
    firma = lambda z: set(EZ[z]) & CD
    jac = lambda a, b: len(a & b)/max(len(a | b), 1)
    gruppi = []
    for z in sorted(nucleo, key=lambda z: -len(firma(z))):
        s = firma(z)
        for g in gruppi:
            if jac(s, g["f"]) >= P["jaccard"]: g["z"].append(z); break
        else: gruppi.append({"f": set(s), "z": [z]})
    gruppi.sort(key=lambda g: -len(g["z"]))
    SC = []
    for g in gruppi:
        if len(g["z"]) < P["min_gruppo"]: continue
        n = len(g["z"]); fq = Counter(k for z in g["z"] for k in set(EZ[z]) & CD)
        ob = {k for k, c in fq.items() if c >= P["obbl_frac"]*n}
        if not ob: continue
        colpite = sum(1 for z in zones if ob <= set(EZ[z]))
        if colpite <= P["lift"] * n: SC.append(ob)   # specificita', non conteggio
    tp = fp = 0
    for z in zones:
        ok = len(set(EZ[z])) >= 3 and any(ob <= set(EZ[z]) for ob in SC)
        v = vera(z)
        tp += ok and v; fp += ok and not v
    return tp, fp, len(SC)

base = run(P0)
print(f"configurazione usata: riconosciute={base[0]}/148  falsi positivi={base[1]}  schemi={base[2]}\n")
print(f"{'costante':18} {'valore':>8}  {'ric./148':>9} {'falsi+':>7} {'schemi':>7}")
print("-"*58)
GRIGLIE = {
 "col_gap":        [10, 20, 30, 40, 60, 100],
 "open_delta":     [0.5, 1.0, 1.5, 2.0, 3.0],
 "lab_delta":      [0.0, 0.3, 0.6, 1.0, 2.0],
 "lab_ric":        [2, 3, 5, 10, 20],
 "nucleo_ratio":   [0.2, 0.3, 0.5, 0.7],
 "condivise_frac": [0.02, 0.05, 0.10, 0.20],
 "jaccard":        [0.2, 0.3, 0.4, 0.5, 0.7],
 "obbl_frac":      [0.7, 0.8, 0.9, 0.95, 1.0],
 "min_gruppo":     [2, 3, 5, 10, 20],
 "lift":           [1.0, 1.2, 1.5, 2.0, 3.0, 5.0, 10.0],
}
for nome, vals in GRIGLIE.items():
    for v in vals:
        P = dict(P0); P[nome] = v
        tp, fp, ns = run(P)
        mark = " <-- usato" if v == P0[nome] else ""
        flag = "" if (tp == 148 and fp == 0) else "   DIVERSO"
        print(f"{nome:18} {v:>8}  {tp:>9} {fp:>7} {ns:>7}{flag}{mark}")
    print()
