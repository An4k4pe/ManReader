"""Quanta parte della forma dello YAML e' DERIVABILE dalle sole schede,
e quanta resta al modello?

Scheletro = trascrizione pura di una zona: (etichetta, valore) per stile,
riga-nome, righe senza etichetta. Nessuna interpretazione.
Poi si induce dalla statistica sugli scheletri tutto cio' che si puo',
e si stampa il RESIDUO, cioe' le sole domande che restano aperte.
"""
from __future__ import annotations
import statistics as st, pymupdf
from collections import Counter, defaultdict

def lines_rich(page):
    out = []
    for blk in page.get_text("dict")["blocks"]:
        for ln in blk.get("lines", []):
            sp = [s for s in ln["spans"] if s["text"].strip()]
            if not sp: continue
            out.append({"y0": ln["bbox"][1], "x0": ln["bbox"][0],
                        "text": "".join(s["text"] for s in sp),
                        "_texts": [s["text"] for s in sp],
                        "keys": [(s["font"], round(s["size"], 1), s["color"]) for s in sp]})
    return sorted(out, key=lambda l: (round(l["y0"], 1), l["x0"]))

pages = [lines_rich(p) for p in pymupdf.open("synth.pdf")]
MED = st.median([k[1] for pg in pages for l in pg for k in l["keys"]])

def skeleton(pg, a, b):
    """Trascrizione: nessuna decisione, solo cosa si vede."""
    sk = {"nome": pg[a]["text"].strip(), "campi": [], "senza_etichetta": []}
    for l in pg[a+1:b+1]:
        if len(set(l["keys"])) >= 2:                      # cambio di stile = etichetta+valore
            sk["campi"].append((l["_texts"][0].strip(": ").strip(),
                                "".join(l["_texts"][1:]).strip()))
        else:
            sk["senza_etichetta"].append(l["text"].strip())
    return sk

# zone (aperture tipografiche, filtro largo come deciso)
skels = []
for pi, pg in enumerate(pages):
    idx = [i for i, l in enumerate(pg) if max(k[1] for k in l["keys"]) > MED]
    for n, i in enumerate(idx):
        end = idx[n+1]-1 if n+1 < len(idx) else len(pg)-1
        sk = skeleton(pg, i, end)
        if len(sk["campi"]) >= 3:
            skels.append(sk)

print(f"scheletri estratti: {len(skels)}\n")
print("--- esempio di scheletro (trascrizione pura, nessuna interpretazione) ---")
s0 = skels[0]
print(f"  nome: {s0['nome']}")
for k, v in s0["campi"]: print(f"  campo: {k!r} = {v!r}")
for t in s0["senza_etichetta"]: print(f"  senza etichetta: {t!r}")

# ---------- cosa si induce SENZA modello ----------
n = len(skels)
freq = Counter(k for s in skels for k, _ in s["campi"])
ripetuti = Counter()
for s in skels:
    for k, c in Counter(k for k, _ in s["campi"]).items():
        if c > 1: ripetuti[k] += 1
ordini = Counter(tuple(k for k, _ in s["campi"]) for s in skels)
prefissi = [tuple(k for k, _ in s["campi"]) for s in skels]

print("\n--- FORMA DERIVATA dalla statistica, senza modello ---")
print(f"{'campo':16} {'presenza':>9}  stato")
for k, c in freq.most_common():
    stato = "obbligatorio" if c == n else f"opzionale ({c}/{n})"
    if k in ripetuti: stato += " + RIPETUTO -> lista"
    print(f"  {k:16} {c:>4}/{n}   {stato}")

comune = [k for k, c in freq.items() if c == n]
print(f"\n  ordine dei campi stabile fra le schede? "
      f"{'si' if len(ordini) == 1 else f'no, {len(ordini)} ordini distinti'}")
# l'ordine e' stabile come SOTTOSEQUENZA?
base = max(prefissi, key=len)
def sottoseq(small, big):
    it = iter(big); return all(x in it for x in small)
print(f"  ogni scheda e' una sottosequenza dell'ordine piu' lungo? "
      f"{all(sottoseq(p, base) for p in prefissi)}   (base: {list(base)})")

# valori: forma sintattica ricorrente per campo (senza vocabolario)
import re
def forma(v):
    if re.fullmatch(r"[+-]?\d+", v): return "intero"
    if re.fullmatch(r"\d+/\d+", v): return "coppia N/M"
    if re.search(r"\d+d\d+", v): return "notazione di dado"
    return "testo"
print("\n  forma dei valori, per campo:")
for k in freq:
    fs = Counter(forma(v) for s in skels for kk, v in s["campi"] if kk == k)
    coerente = len(fs) == 1
    print(f"    {k:16} {dict(fs)}  {'coerente' if coerente else 'MISTA -> tenere stringa'}")

# ---------- il residuo: cosa il modello deve ancora decidere ----------
print("\n--- RESIDUO: le sole domande che la statistica non chiude ---")
orfane = [t for s in skels for t in s["senza_etichetta"]]
print(f"  1. {len(orfane)} righe senza etichetta. Sono prosa, o sono voci strutturate")
print(f"     con il nome incorporato? Esempi:")
for t in orfane[:3]: print(f"        {t!r}")
print(f"  2. i campi vanno raggruppati in sotto-oggetti? (nessun segnale nella")
print(f"     trascrizione lo dice: e' una scelta di forma)")
print(f"  3. mappatura verso un vocabolario bersaglio (PF->hp): serve solo se")
print(f"     si vuole lo schema di un consumatore esterno, non per leggere")
