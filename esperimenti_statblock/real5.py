"""Catena su Daggerheart SRD. Generica: nessun nome di font o etichetta cablato.

etichetta = span il cui stile differisce dallo stile di corpo ED e' seguito
            sulla stessa riga da uno span di stile di corpo (piu' coppie per riga)
apertura  = riga il cui corpo massimo supera la dimensione del corpo testo
"""
from __future__ import annotations
import re, unicodedata, sys
from collections import Counter, defaultdict

import pymupdf
D = "/root/.claude/uploads/bf3622c8-0f6b-51f8-8f58-2201291c077f/2261baf5-DaggerheartSRD90925.pdf"

def squash(t): return re.sub(r"\s+", "", unicodedata.normalize("NFKC", t)).lower()
def clean(t):  return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", t)).strip()

def lines_of(page):
    out = []
    for blk in page.get_text("dict")["blocks"]:
        for ln in blk.get("lines", []):
            sp = [s for s in ln["spans"] if s["text"].strip()]
            if not sp: continue
            out.append({"y0": ln["bbox"][1], "x0": ln["bbox"][0],
                        "spans": [(s["text"], (s["font"].split("+")[-1], round(s["size"],1), s["color"]))
                                  for s in sp]})
    # colonne: raggruppa gli x0 di inizio riga, poi ordina DENTRO la colonna.
    # Sta al posto di column_band: senza, l'ordine interlaccia le colonne.
    if not out: return out
    xs = sorted({round(l["x0"], 1) for l in out})
    gruppi, cur = [], [xs[0]]
    for a, b in zip(xs, xs[1:]):
        (cur.append(b) if b - a <= 30.0 else (gruppi.append(cur), cur := [b]))
    gruppi.append(cur)
    bordi = [min(g) for g in gruppi]
    def col(l):
        return max(i for i, x in enumerate(bordi) if l["x0"] >= x - 0.5)
    return sorted(out, key=lambda l: (col(l), round(l["y0"], 1), l["x0"]))

doc = pymupdf.open(D)
pages = [lines_of(p) for p in doc]

# stile di corpo = quello con piu' CARATTERI (non piu' righe: errore del giro sintetico)
chars = Counter()
for pg in pages:
    for l in pg:
        for t, k in l["spans"]: chars[k] += len(t.strip())
BODY = chars.most_common(1)[0][0]
BODY_SIZE = BODY[1]
print(f"stile di corpo dedotto: {BODY}   (dimensione {BODY_SIZE})")

def pairs(line, body):
    """(etichetta, valore) multipli per riga: span non-corpo seguito da span corpo.
    `body` e' lo stile di corpo LOCALE della zona: correzione dichiarata, il
    corpo globale (9pt) non e' quello delle schede (8pt) e non estraeva nulla."""
    out, i, sp = [], 0, line["spans"]
    while i < len(sp):
        t, k = sp[i]
        if k != body and k[1] <= body[1] + 0.6 and i + 1 < len(sp) and sp[i+1][1] == body:
            val, j = "", i + 1
            while j < len(sp) and sp[j][1] == body:
                val += sp[j][0]; j += 1
            out.append((clean(t).rstrip(":").strip(), clean(val).strip(" |")))
            i = j
        else:
            i += 1
    return out

def is_opener(line):
    return max(k[1] for _, k in line["spans"]) > BODY_SIZE + 1.0

# ---- zone: da un'apertura alla successiva, dentro la pagina ----
zones = []
for pi, pg in enumerate(pages):
    idx = [i for i, l in enumerate(pg) if is_opener(l)]
    for n, i in enumerate(idx):
        zones.append((pi, i, idx[n+1]-1 if n+1 < len(idx) else len(pg)-1))
    if idx and idx[0] > 0: zones.append((pi, -1, idx[0]-1))
    if not idx and pg:     zones.append((pi, -1, len(pg)-1))
print(f"zone candidate su tutto il documento: {len(zones)}")

def local_body(pi, a, b):
    c = Counter()
    for l in pages[pi][max(a,0):b+1]:
        for t, k in l["spans"]: c[k] += len(t.strip())
    return c.most_common(1)[0][0] if c else BODY

def fields_of(pi, a, b):
    body = local_body(pi, a, b)
    fs = []
    for l in pages[pi][max(a,0) + (1 if a >= 0 else 0): b+1]:
        fs += pairs(l, body)
    return fs

# ---- verita': una zona e' una scheda se contiene 'difficulty:' ----
def vera(pi, a, b):
    txt = "".join(t for l in pages[pi][max(a,0):b+1] for t, _ in l["spans"])
    return "difficulty:" in squash(txt)

vere = [z for z in zones if vera(*z)]
print(f"zone che contengono 'Difficulty:' (verita'): {len(vere)}")

# ---- quante schede vere sono coperte da UNA zona? ----
attese = 148
print(f"schede attese dalla verita' testuale: {attese}")
multi = sum(1 for z in vere if "".join(t for l in pages[z[0]][max(z[1],0):z[2]+1]
                                        for t, _ in l["spans"]).lower().count("ifficulty") > 1)
print(f"zone vere che ne contengono PIU' DI UNA (aperture mancate): {multi}")

# ================= induzione dello schema e classificazione =================
print("\n" + "="*70)
etichette_zona = {z: [k for k, _ in fields_of(*z)] for z in zones}

# nucleo: zone con >=3 campi le cui etichette ricorrono nel documento
tutte = Counter(k for ks in etichette_zona.values() for k in ks)
ric = {k for k, c in tutte.items() if c >= 3}
nucleo = [z for z in zones
          if len(etichette_zona[z]) >= 3
          and sum(1 for k in etichette_zona[z] if k in ric)/len(etichette_zona[z]) >= 0.5
          and len(set(etichette_zona[z])) >= 3]
print(f"nucleo per l'induzione: {len(nucleo)} zone   (di cui vere: {sum(1 for z in nucleo if vera(*z))})")

# --- CORREZIONI dichiarate, dopo aver visto i due fallimenti:
#  (1) piu' template: si raggruppa e si induce uno schema per gruppo
#  (2) la firma usa solo etichette CONDIVISE dal nucleo (>=5%), non quelle
#      per-istanza (nomi di arma, nomi di capacita'), che frammentavano
#  (3) il test di rapporto e' rimosso: penalizzava le schede piu' ricche.
#      Resta il criterio assoluto: gli obbligatori del template devono esserci.
cond = Counter()
for z in nucleo: cond.update(set(etichette_zona[z]))
CONDIVISE = {k for k, c in cond.items() if c >= max(3, 0.05*len(nucleo))}
print(f"etichette condivise nel nucleo: {len(CONDIVISE)}")

def firma(z): return set(etichette_zona[z]) & CONDIVISE
def jac(a, b): return len(a & b)/max(len(a | b), 1)
gruppi = []
for z in sorted(nucleo, key=lambda z: -len(firma(z))):
    s_ = firma(z)
    for g in gruppi:
        if jac(s_, g["firma"]) >= 0.4:
            g["zone"].append(z); break
    else:
        gruppi.append({"firma": set(s_), "zone": [z]})
gruppi.sort(key=lambda g: -len(g["zone"]))
print(f"gruppi di template: {len(gruppi)}")
for gi, g in enumerate(gruppi[:4]):
    v = sum(1 for z in g["zone"] if vera(*z))
    print(f"  gruppo {gi}: {len(g['zone']):>4} zone ({v} vere)  firma: {sorted(g['firma'])}")

def induci(zs):
    n = len(zs)
    fq = Counter(k for z in zs for k in set(etichette_zona[z]) & CONDIVISE)
    return {"n": n, "obbl": {k for k, c in fq.items() if c >= 0.9*n},
            "noti": {k for k, c in fq.items() if c >= max(2, 0.05*n)}}

# uno schema serve da classificatore solo se e' DISCRIMINANTE: un template
# caratterizzato da una sola etichetta non e' un template. Minimo 3.
SCHEMI = [S for S in (induci(g["zone"]) for g in gruppi if len(g["zone"]) >= 5)
          if len(S["obbl"]) >= 3]
print(f"\nschemi indotti (gruppi con >=5 zone): {len(SCHEMI)}")
for i, S in enumerate(SCHEMI):
    print(f"  schema {i} (n={S['n']:>3}) obbligatori: {sorted(S['obbl'])}")

def giudica(z):
    ks = set(etichette_zona[z])
    if len(ks) < 3: return "SCARTATA", None
    for i, S in enumerate(SCHEMI):
        if S["obbl"] and S["obbl"] <= ks: return "SCHEDA", i
    for i, S in enumerate(SCHEMI):
        if S["obbl"] and len(S["obbl"] & ks) >= max(2, 0.6*len(S["obbl"])):
            return "INCOMPLETA", i
    return "SCARTATA", None

ris = Counter(); rifiutate=[]; incomplete=[]; falsi=[]
for z in zones:
    g, _i = giudica(z); v = vera(*z)
    ris[(g, v)] += 1
    if v and g == "SCARTATA": rifiutate.append(z)
    if v and g == "INCOMPLETA": incomplete.append(z)
    if not v and g == "SCHEDA": falsi.append(z)
print(f"\n  {'verdetto':12} {'vere':>6} {'non vere':>9}")
for g in ["SCHEDA", "INCOMPLETA", "SCARTATA"]:
    print(f"  {g:12} {ris[(g,True)]:>6} {ris[(g,False)]:>9}")
print(f"\n  su 148 schede vere: {ris[('SCHEDA',True)]} riconosciute, "
      f"{len(incomplete)} incomplete, {len(rifiutate)} RIFIUTATE")
print(f"  falsi positivi: {len(falsi)}")
for z in rifiutate[:8]:
    nome = clean("".join(t for t,_ in pages[z[0]][z[1]]["spans"])) if z[1]>=0 else "(orfana)"
    print(f"     rifiutata: pag{z[0]} {nome[:30]} campi={len(etichette_zona[z])}")
for z in falsi[:8]:
    nome = clean("".join(t for t,_ in pages[z[0]][z[1]]["spans"])) if z[1]>=0 else "(orfana)"
    print(f"     falso positivo: pag{z[0]} {nome[:34]}")

print("\n" + "="*70)
print("PROVA 1 — tolgo 'Diffi culty' dallo schema: il risultato dipende dalla")
print("          stringa che definisce anche la verita'?")
for S in SCHEMI: S["obbl"] = {k for k in S["obbl"] if "culty" not in k}
r2 = Counter()
for z in zones: r2[(giudica(z)[0], vera(*z))] += 1
print(f"   SCHEDA: {r2[('SCHEDA',True)]} vere / {r2[('SCHEDA',False)]} non vere;  "
      f"SCARTATE vere: {r2[('SCARTATA',True)]}")
print(f"   obbligatori residui: {[sorted(S['obbl']) for S in SCHEMI]}")

print("\nPROVA 2 — i CONFINI: la zona copre la scheda e non sborda?")
pag_adv = range(37, 56)
tot_car = sum(len("".join(t for t,_ in l["spans"]).strip()) for i in pag_adv for l in pages[i])
zone_adv = [z for z in zones if z[0] in pag_adv]
cop = sum(len("".join(t for t,_ in l["spans"]).strip())
          for z in zone_adv for l in pages[z[0]][max(z[1],0):z[2]+1])
print(f"   caratteri sulle pagine 37-55: {tot_car}   coperti dalle zone: {cop}  "
      f"({100*cop/tot_car:.1f}%)")
schede = [z for z in zone_adv if giudica(z)[0] == "SCHEDA"]
cop_s = sum(len("".join(t for t,_ in l["spans"]).strip())
            for z in schede for l in pages[z[0]][max(z[1],0):z[2]+1])
print(f"   coperti dalle sole zone-SCHEDA: {cop_s} ({100*cop_s/tot_car:.1f}%)")
print(f"   zone non-scheda su quelle pagine: {len(zone_adv)-len(schede)}")

print("\nPROVA 3 — una zona, per intero, a occhio:")
z = [x for x in schede if x[0] == 38][0]
for l in pages[z[0]][z[1]:z[2]+1]:
    print("     " + clean("".join(t for t,_ in l["spans"]))[:96])

print("\nPROVA 4 — ogni scheda finisce nel template giusto?")
conf = Counter()
for z in zones:
    g, i = giudica(z)
    if g != "SCHEDA": continue
    txt = squash("".join(t for l in pages[z[0]][max(z[1],0):z[2]+1] for t,_ in l["spans"]))
    tipo = "ambiente" if "impulses:" in txt else "avversario"
    conf[(tipo, i)] += 1
print("   (tipo reale, schema assegnato) -> conteggio:", dict(conf))

print("\nPROVA 5 — difetti di testo misurabili sulle pagine 37-55")
import unicodedata as U
pua = spazi = 0
for i in range(37, 56):
    for l in pages[i]:
        t = "".join(x for x, _ in l["spans"])
        pua += sum(1 for c in t if 0xE000 <= ord(c) <= 0xF8FF)
        spazi += len(re.findall(r"[a-z]\s{2,}[a-z]", t))
print(f"   glifi in area privata (persi in estrazione): {pua}")
print(f"   parole spezzate da spazi spuri (es. 'Diffi  culty'): {spazi}")
lig = sum(1 for z in zones for k in etichette_zona[z] if re.search(r"[a-z]\s+[a-z]", k))
print(f"   etichette indotte che contengono uno spazio spurio: {lig}")
