"""Lo SCHEMA come test di ammissione. Nessun modello.

Domande separate:
  (a) questa zona e' una scheda?          -> ci sta nello schema, con motivo
  (b1) dove finisce l'etichetta?          -> cambio di stile (gia' misurato)
  (b2) dove finisce un valore su piu' righe? -> dove ricomincia un'etichetta DELLO SCHEMA
  (b3) prosa o capacita' con nome?        -> resta al modello, una volta per template
"""
from __future__ import annotations
import re, statistics as st, pymupdf
from collections import Counter

def lines_rich(page):
    out = []
    for blk in page.get_text("dict")["blocks"]:
        for ln in blk.get("lines", []):
            sp = [s for s in ln["spans"] if s["text"].strip()]
            if not sp: continue
            out.append({"y0": ln["bbox"][1], "x0": ln["bbox"][0], "x1": ln["bbox"][2],
                        "text": "".join(s["text"] for s in sp),
                        "_texts": [s["text"] for s in sp],
                        "keys": [(s["font"], round(s["size"],1), s["color"]) for s in sp]})
    return sorted(out, key=lambda l: (round(l["y0"],1), l["x0"]))

def forma(v):
    if re.fullmatch(r"[+-]?\d+", v): return "intero"
    if re.fullmatch(r"\d+/\d+", v): return "coppia"
    if re.search(r"\d+d\d+", v): return "dado"
    return "testo"

def zones_of(pages):
    MED = st.median([k[1] for pg in pages for l in pg for k in l["keys"]])
    z = []
    for pi, pg in enumerate(pages):
        idx = [i for i, l in enumerate(pg) if max(k[1] for k in l["keys"]) > MED]
        for n, i in enumerate(idx):
            z.append((pi, i, idx[n+1]-1 if n+1 < len(idx) else len(pg)-1))
        if idx and idx[0] > 0:
            z.append((pi, -1, idx[0]-1))          # testa orfana
    return z

def join_continuations(rf):
    """Una riga senza etichetta e rientrata continua il valore precedente.
    Correzione d'ordine: va fatto PRIMA del test di forma, altrimenti un valore
    andato a capo si presenta come 'testo' e fa scartare una scheda valida."""
    if not rf: return rf
    x_base = min(x for _, _, _, x in rf)
    out = []
    for t, k, v, x in rf:
        if t == "L" and out and out[-1][0] == "F" and x - x_base > 1.0:
            tt, kk, vv, xx = out[-1]
            out[-1] = (tt, kk, (vv + " " + v).strip(), xx)
        else:
            out.append((t, k, v, x))
    return out


def raw_fields(pg, a, b):
    """(b1) etichetta = span di stile diverso. Nessuna interpretazione."""
    out = []
    for l in pg[max(a,0)+ (1 if a >= 0 else 0): b+1]:
        if len(set(l["keys"])) >= 2:
            out.append(("F", l["_texts"][0].strip(": ").strip(),
                        "".join(l["_texts"][1:]).strip(), l["x0"]))
        else:
            out.append(("L", None, l["text"].strip(), l["x0"]))
    return out

# ---------- schema indotto dal nucleo pulito ----------
core = [lines_rich(p) for p in pymupdf.open("synth.pdf")]
sk = []
for pi, a, b in zones_of(core):
    if a < 0: continue
    fs = [(k, v) for t, k, v, _ in join_continuations(raw_fields(core[pi], a, b)) if t == "F"]
    if len(fs) >= 3: sk.append(fs)
tutte = Counter(k for f in sk for k, _ in f)
ric = {k for k, c in tutte.items() if c >= 2}
sk = [f for f in sk if sum(1 for k, _ in f if k in ric)/len(f) >= 0.5]   # due assi
n = len(sk)
freq = Counter(k for f in sk for k, _ in f)
SCHEMA = {"obbligatori": {k for k, c in freq.items() if c == n},
          "opzionali":   {k for k, c in freq.items() if c < n},
          "ordine":      [k for k, _ in max(sk, key=len)],
          "forme":       {k: Counter(forma(v) for f in sk for kk, v in f if kk == k).most_common(1)[0][0]
                          for k in freq}}
print(f"schema indotto da {n} schede")
print(f"  obbligatori: {sorted(SCHEMA['obbligatori'])}")
print(f"  opzionali:   {sorted(SCHEMA['opzionali'])}")
print(f"  ordine base: {SCHEMA['ordine']}")
print(f"  forme:       {SCHEMA['forme']}\n")

# ---------- (a) test di ammissione, con motivo ----------
def sottoseq(small, big):
    it = iter(big); return all(x in it for x in small)

def giudica(pg, a, b):
    rf = join_continuations(raw_fields(pg, a, b))
    fs = [(k, v) for t, k, v, _ in rf if t == "F"]
    if not fs: return "SCARTATA", "nessun campo etichettato"
    noti = [k for k, _ in fs if k in freq]
    if len(noti)/len(fs) < 0.5:
        return "SCARTATA", f"{len(fs)-len(noti)}/{len(fs)} etichette estranee allo schema"
    manca = SCHEMA["obbligatori"] - set(noti)
    if not sottoseq(noti, SCHEMA["ordine"]):
        return "SCARTATA", "ordine dei campi incompatibile con lo schema"
    male = [k for k, v in fs if k in SCHEMA["forme"] and forma(v) != SCHEMA["forme"][k]]
    if male: return "SCARTATA", f"forma del valore incoerente: {male}"
    if manca:
        tipo = "CODA/CONTINUAZIONE" if a < 0 else "INCOMPLETA"
        return tipo, f"mancano {sorted(manca)}"
    return "SCHEDA", f"{len(fs)} campi, tutti gli obbligatori"

print("--- (a) e' una scheda? il test e' lo schema, e dice PERCHE' ---")
for nome, pdf in [("bestiario+negative", "synth.pdf"), ("troncamento+richiami", "confound.pdf"),
                  ("valore a capo", "wrap.pdf")]:
    pgs = [lines_rich(p) for p in pymupdf.open(pdf)]
    print(f"\n  {pdf}")
    for pi, a, b in zones_of(pgs):
        et = pgs[pi][a]["text"][:24] if a >= 0 else "(testa orfana)"
        v, why = giudica(pgs[pi], a, b)
        print(f"    pag{pi} {et:26} -> {v:19} {why}")

# ---------- (b2) valore su piu' righe ----------
print("\n--- (b2) dove finisce un valore che va a capo ---")
pgs = [lines_rich(p) for p in pymupdf.open("wrap.pdf")]
pi, a, b = [z for z in zones_of(pgs) if z[1] >= 0][0]
rf = raw_fields(pgs[pi], a, b)
x_base = min(x for _, _, _, x in rf)
cur = None
for t, k, v, x in rf:
    if t == "F":
        cur = k; print(f"    campo {k!r} = {v!r}")
    else:
        rientro = x - x_base
        deciso = "continuazione del campo precedente" if cur and rientro > 1.0 else "riga a se'"
        print(f"    riga senza etichetta (rientro {rientro:.0f}pt) -> {deciso}: {v!r}")
