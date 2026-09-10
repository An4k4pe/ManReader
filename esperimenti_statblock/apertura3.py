"""Il livello di apertura si CERCA, non si sceglie. Nessun delta in punti.

Per ogni livello di dimensione del documento si esegue l'induzione completa
usando quel livello come apertura, e si tiene quello che spiega piu' regioni
con schemi discriminanti. Criterio e predizioni in CRITERIO_APERTURA.md.
"""
from __future__ import annotations
import re, unicodedata
from collections import Counter
import pymupdf

D = "/root/.claude/uploads/bf3622c8-0f6b-51f8-8f58-2201291c077f/2261baf5-DaggerheartSRD90925.pdf"
def squash(t): return re.sub(r"\s+", "", unicodedata.normalize("NFKC", t)).lower()
def clean(t):  return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", t)).strip()

# --- righe, ordinate dentro la colonna ---
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

# --- i livelli di dimensione esistenti nel documento, per caratteri portati ---
peso = Counter()
for pg in PAGES:
    for l in pg:
        for t, k in l["spans"]: peso[k[1]] += len(t.strip())
LIVELLI = sorted(peso)
print("livelli di dimensione nel documento (dimensione: caratteri):")
print("   " + ", ".join(f"{s}:{peso[s]}" for s in LIVELLI))

def induci_con(livello: float):
    """Induzione completa usando `livello` come dimensione di apertura."""
    zones = []
    for pi, pg in enumerate(PAGES):
        idx = [i for i, l in enumerate(pg)
               if max(k[1] for _, k in l["spans"]) >= livello]   # il livello O SOPRA:
               # un titolo piu' grande chiude comunque un record. Correzione
               # post-hoc numero 2, dichiarata.
        for n, i in enumerate(idx):
            zones.append((pi, i, idx[n+1]-1 if n+1 < len(idx) else len(pg)-1))
        if idx and idx[0] > 0: zones.append((pi, -1, idx[0]-1))
    if len(zones) < 5: return None
    def labs(z):
        pi, a, b = z
        c = Counter()
        for l in PAGES[pi][max(a,0):b+1]:
            for t, k in l["spans"]: c[k] += len(t.strip())
        body = c.most_common(1)[0][0] if c else None
        out, = [[]]
        for l in PAGES[pi][max(a,0)+(1 if a >= 0 else 0):b+1]:
            sp, i = l["spans"], 0
            while i < len(sp):
                t, k = sp[i]
                if body and k != body and k[1] <= body[1]+0.6 \
                   and i+1 < len(sp) and sp[i+1][1] == body:
                    out.append(clean(t).rstrip(":").strip()); i += 2
                else: i += 1
        return out
    EZ = {z: labs(z) for z in zones}
    tutte = Counter(k for v in EZ.values() for k in v)
    ric = {k for k, c in tutte.items() if c >= 3}
    nucleo = [z for z in zones if len(EZ[z]) >= 3
              and sum(1 for k in EZ[z] if k in ric)/len(EZ[z]) >= 0.5
              and len(set(EZ[z])) >= 3]
    if not nucleo: return None
    cond = Counter()
    for z in nucleo: cond.update(set(EZ[z]))
    CD = {k for k, c in cond.items() if c >= max(3, 0.05*len(nucleo))}
    firma = lambda z: set(EZ[z]) & CD
    jac = lambda a, b: len(a & b)/max(len(a|b), 1)
    gruppi = []
    for z in sorted(nucleo, key=lambda z: -len(firma(z))):
        s = firma(z)
        for g in gruppi:
            if jac(s, g["f"]) >= 0.4: g["z"].append(z); break
        else: gruppi.append({"f": set(s), "z": [z]})
    gruppi.sort(key=lambda g: -len(g["z"]))
    SC = []
    for g in gruppi:
        if len(g["z"]) < 5: continue
        n = len(g["z"]); fq = Counter(k for z in g["z"] for k in set(EZ[z]) & CD)
        ob = {k for k, c in fq.items() if c >= 0.9*n}
        if not ob: continue
        colpite = sum(1 for z in zones if ob <= set(EZ[z]))
        if colpite <= 3.0 * n: SC.append(ob)          # test di specificita'
    # CORREZIONE POST-HOC, dichiarata: il conteggio delle regioni premia chi
    # frantuma il documento. Si normalizza sulla COPERTURA in caratteri: una
    # scheda copre centinaia di caratteri, un frammento di riga una decina.
    def car(z):
        return sum(len("".join(t for t, _ in l["spans"]).strip())
                   for l in PAGES[z[0]][max(z[1],0):z[2]+1])
    ammesse = [z for z in zones
               if len(set(EZ[z])) >= 3 and any(ob <= set(EZ[z]) for ob in SC)]
    spiegate = sum(car(z) for z in ammesse)
    n_amm = len(ammesse)
    vera = lambda z: "difficulty:" in squash("".join(
        t for l in PAGES[z[0]][max(z[1],0):z[2]+1] for t, _ in l["spans"]))
    tp = sum(1 for z in ammesse if vera(z))
    return {"zone": len(zones), "schemi": len(SC), "spiegate": spiegate,
            "n": n_amm, "tp": tp, "fp": n_amm - tp, "obbl": [sorted(o) for o in SC]}

print(f"\n{'livello':>8} {'zone':>6} {'schemi':>7} {'CARATTERI':>11} {'regioni':>8} {'vere':>6} {'non vere':>9}")
print("-"*56)
best, ris = None, {}
for s in LIVELLI:
    r = induci_con(s)
    ris[s] = r
    if r is None:
        print(f"{s:>8} {'-':>6} {'-':>7} {'-':>9}"); continue
    print(f"{s:>8} {r['zone']:>6} {r['schemi']:>7} {r['spiegate']:>11} {r['n']:>8} {r['tp']:>6} {r['fp']:>9}")
    if best is None or r["spiegate"] > ris[best]["spiegate"]: best = s

print(f"\n>>> livello scelto dalla ricerca: {best}")
r = ris[best]
print(f"    zone={r['zone']}  schemi={r['schemi']}  riconosciute={r['tp']}  falsi positivi={r['fp']}")
for o in r["obbl"]: print(f"    obbligatori: {o}")

print("\n--- cosa sono gli 11 'falsi positivi' del livello scelto? ---")
livello = best
zones = []
for pi, pg in enumerate(PAGES):
    idx = [i for i, l in enumerate(pg) if max(k[1] for _, k in l["spans"]) >= livello]
    for n, i in enumerate(idx):
        zones.append((pi, i, idx[n+1]-1 if n+1 < len(idx) else len(pg)-1))
    if idx and idx[0] > 0: zones.append((pi, -1, idx[0]-1))
def labs2(z):
    pi, a, b = z
    c = Counter()
    for l in PAGES[pi][max(a,0):b+1]:
        for t, k in l["spans"]: c[k] += len(t.strip())
    body = c.most_common(1)[0][0] if c else None
    out = []
    for l in PAGES[pi][max(a,0)+(1 if a>=0 else 0):b+1]:
        sp, i = l["spans"], 0
        while i < len(sp):
            t, k = sp[i]
            if body and k != body and k[1] <= body[1]+0.6 and i+1 < len(sp) and sp[i+1][1] == body:
                out.append(clean(t).rstrip(":").strip()); i += 2
            else: i += 1
    return out
EZ2 = {z: labs2(z) for z in zones}
terzo = {'mark a Stress', 'spend a Hope'}
vera2 = lambda z: "difficulty:" in squash("".join(t for l in PAGES[z[0]][max(z[1],0):z[2]+1] for t,_ in l["spans"]))
n = 0
for z in zones:
    if terzo <= set(EZ2[z]) and not vera2(z):
        n += 1
        nome = clean("".join(t for t,_ in PAGES[z[0]][z[1]]["spans"])) if z[1] >= 0 else "(orfana)"
        print(f"   pag{z[0]:>3} {nome[:44]}")
        if n >= 11: break
