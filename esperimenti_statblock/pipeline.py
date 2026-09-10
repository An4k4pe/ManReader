"""Catena: zona deterministica -> modello che ETICHETTA -> assemblaggio verbatim -> verifica.

Tesi sotto test: se il modello restituisce SOLO indici e ruoli, e il testo lo
copiamo noi dalla sorgente, l'invenzione di contenuto diventa strutturalmente
impossibile e resta solo l'errore di etichetta, che e' controllabile.
Il modello e' simulato: qui si prova il CONTRATTO, non un LLM.
"""
from __future__ import annotations
import statistics as st, pymupdf
from collections import Counter

src = open("detect.py").read().replace("\nmain()\n", "\n"); ns = {}
exec(compile(src, "detect.py", "exec"), ns)

def spans_of(line):
    """Segmenti (testo, id_stile) della riga, in ordine di x."""
    return [(s, k) for s, k in zip(_split(line), line["keys"])]

def _split(line):
    """PyMuPDF non ci ridà i testi per span da lines_of: li ricostruiamo."""
    return line["_texts"]

# lines_of non conserva i testi per span: lo estendo qui (non tocco detect.py)
def lines_rich(page):
    out = []
    for blk in page.get_text("dict")["blocks"]:
        for ln in blk.get("lines", []):
            sp = [s for s in ln["spans"] if s["text"].strip()]
            if not sp: continue
            out.append({"y0": ln["bbox"][1], "y1": ln["bbox"][3],
                        "x0": ln["bbox"][0], "x1": ln["bbox"][2],
                        "text": "".join(s["text"] for s in sp),
                        "_texts": [s["text"] for s in sp],
                        "keys": [(s["font"], round(s["size"], 1), s["color"]) for s in sp]})
    return sorted(out, key=lambda l: (round(l["y0"], 1), l["x0"]))


# ---------- 1. zona deterministica, in modalita' RICHIAMO ----------
def find_zones(pages, min_distinct: int, min_density: float):
    MED = st.median([k[1] for pg in pages for l in pg for k in l["keys"]])
    def lab(l):
        if len(set(l["keys"])) < 2: return None
        return l["_texts"][0].strip(": ").lower()
    labels = Counter(x for pg in pages for l in pg if (x := lab(l)))
    rec = {k for k, n in labels.items() if n >= 2}
    zones = []
    for pi, pg in enumerate(pages):
        idx = [i for i, l in enumerate(pg) if max(k[1] for k in l["keys"]) > MED]
        for n, i in enumerate(idx):
            end = idx[n+1]-1 if n+1 < len(idx) else len(pg)-1
            body = pg[i+1:end+1]
            if not body: continue
            labs = [lab(l) for l in body if lab(l) in rec]
            if len(labs)/len(body) >= min_density and len(set(labs)) >= min_distinct:
                zones.append((pi, i, end))
    return zones, rec


# ---------- 2. serializzazione che CONSERVA lo stile ----------
def serialize(pg, a, b):
    styles, legend = {}, []
    def sid(k):
        if k not in styles:
            styles[k] = f"S{len(styles)+1}"
            legend.append(f"{styles[k]} = {k[0]} {k[1]}pt colore {k[2]}")
        return styles[k]
    out = []
    for n, l in enumerate(pg[a:b+1]):
        segs = " ".join(f"[{sid(k)}]{t.strip()}" for t, k in zip(l["_texts"], l["keys"]) if t.strip())
        out.append(f"L{n} {segs}")
    return "\n".join(legend) + "\n---\n" + "\n".join(out)


# ---------- 3. assemblaggio VERBATIM dai ruoli ----------
def assemble(pg, a, b, roles):
    """roles: {indice_riga: ('name'|'field'|'prose'|'ignore', indice_span_chiave)}"""
    zone = pg[a:b+1]
    entries, name, leftovers = [], None, []
    for n, l in enumerate(zone):
        role, ks = roles.get(n, ("ignore", None))
        if role == "name":
            name = l["text"].strip()
        elif role == "field" and ks is not None and ks < len(l["_texts"]):
            key = l["_texts"][ks].strip(": ").strip()
            val = "".join(t for j, t in enumerate(l["_texts"]) if j != ks).strip()
            entries.append((key, val))
        else:
            leftovers.append(l["text"])
    return {"name": name, "entries": entries, "raw_extra": leftovers,
            "zone_text": "".join(l["text"] for l in zone)}


# ---------- 4. verifica di conservazione ----------
def nonspace(s): return Counter(c for c in s if not c.isspace())

SEPARATORI = ":"   # normalizzazione DICHIARATA, l'unica ammessa

def verify(res, vocab):
    """Due allarmi distinti, non un booleano.

    inventato = caratteri nell'uscita che non sono nella sorgente -> il modello
                ha aggiunto testo. Impossibile se copiamo verbatim: se scatta,
                qualcuno ha violato il contratto.
    perso     = caratteri nella sorgente che non sono nell'uscita -> contenuto
                caduto in silenzio. E' il guasto che il progetto vieta.
    """
    def norm(t):
        return Counter(c for c in t if not c.isspace() and c not in SEPARATORI)
    prodotto = norm("".join([res["name"] or ""] + [k + v for k, v in res["entries"]]
                            + res["raw_extra"]))
    sorgente = norm(res["zone_text"])
    inventato = prodotto - sorgente
    perso = sorgente - prodotto
    fuori = [k for k, _ in res["entries"] if k.lower() not in vocab]
    return inventato, perso, fuori


# ---------- prova ----------
pages = [lines_rich(p) for p in pymupdf.open("synth.pdf")]

print("=== 1. la zona, al variare della severita' ===")
print(f"{'soglie':34} {'zone':>5}  {'su pagine di bestiario':>22} {'su negative':>12}")
for md, dn in [(3, 0.5), (2, 0.4), (1, 0.25), (0, 0.0)]:
    z, _ = find_zones(pages, md, dn)
    print(f"  distinte>={md}, densita'>={dn:<4}{'':<16} {len(z):>5}  "
          f"{sum(1 for x in z if x[0] < 2):>22} {sum(1 for x in z if x[0] >= 2):>12}")

zones, vocab = find_zones(pages, 3, 0.5)
pi, a, b = zones[0]
print(f"\n=== 2. cosa riceve il modello (zona pag{pi} righe {a}-{b}) ===")
print(serialize(pages[pi], a, b))

print("\n=== 3. tre modelli simulati, stesso contratto ===")
zone = pages[pi][a:b+1]
fedele = {0: ("name", None), **{n: ("field", 0) for n in range(1, len(zone)-1)},
          len(zone)-1: ("prose", None)}
allucinato = dict(fedele)          # stessi ruoli: il modello NON puo' toccare il testo
dimenticone = dict(fedele); dimenticone[2] = ("ignore_drop", None)

for nome, roles, drop in [("fedele", fedele, False),
                          ("che tenta di inventare", allucinato, False),
                          ("che dimentica una riga", dimenticone, True)]:
    res = assemble(pages[pi], a, b, roles)
    if drop:                        # simula la perdita: la riga sparisce davvero
        res["raw_extra"] = [x for x in res["raw_extra"] if "Soglie" not in x]
        res["entries"] = [e for e in res["entries"] if e[0] != "Soglie"]
    if nome == "che tenta di inventare":
        res["entries"] = res["entries"] + [("Debolezza", "fuoco sacro")]   # testo mai visto
    inv, perso, fuori = verify(res, vocab)
    def sm(c): return "".join(sorted(c.elements()))[:28] or "-"
    print(f"  {nome:26} inventato={sm(inv):30} perso={sm(perso):16} "
          f"chiavi fuori vocab.={fuori or '-'}")
    if nome == "fedele":
        print(f"      -> {res['name']}: {res['entries'][:3]} ... ({len(res['entries'])} campi)")
