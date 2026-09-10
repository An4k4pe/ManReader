"""Schede SENZA due punti: 'PF 5' invece di 'PF: 5'. L'etichetta e' solo lo span
in grassetto. Testa se il metodo dipende dalla punteggiatura o dallo stile."""
from __future__ import annotations
import statistics as st, pymupdf
from collections import Counter
BOLD, REG, BODY, NAME = "hebo", "helv", 9.0, 12.0
BLACK, DARKRED, X0, TOP, LEAD = (0,0,0), (0.5,0.05,0.05), 60.0, 70.0, 13.0

def line(p, y, spans):
    x = X0
    for t, f, s, c in spans:
        p.insert_text((x, y), t, fontname=f, fontsize=s, color=c)
        x += pymupdf.get_text_length(t, fontname=f, fontsize=s)

doc = pymupdf.open()
for nome, fs in [("LUPO D'OMBRA", [("Difficolta","12"),("Soglie","6/11"),("PF","4"),
                                   ("Stress","3"),("Attacco","+2"),("Arma","Morso 1d6")]),
                 ("SCIACALLO",    [("Difficolta","8"),("Soglie","2/5"),("PF","1"),
                                   ("Stress","1"),("Attacco","+0"),("Arma","Zanne 1d4")])]:
    pass
p = doc.new_page(width=612, height=792); y = TOP
for nome, fs in [("LUPO D'OMBRA", [("Difficolta","12"),("Soglie","6/11"),("PF","4"),
                                   ("Stress","3"),("Attacco","+2"),("Arma","Morso 1d6")]),
                 ("SCIACALLO",    [("Difficolta","8"),("Soglie","2/5"),("PF","1"),
                                   ("Stress","1"),("Attacco","+0"),("Arma","Zanne 1d4")])]:
    line(p, y, [(nome, BOLD, NAME, DARKRED)]); y += LEAD + 4
    for lab, val in fs:
        line(p, y, [(lab + " ", BOLD, BODY, BLACK), (val, REG, BODY, BLACK)]); y += LEAD
    y += 10
p = doc.new_page(width=612, height=792); y = TOP     # negativo: titoli + prosa
for h, bs in [("USARE LE PROVE", ["il giocatore descrive cosa tenta, poi tira.",
                                  "un fallimento complica la scena."]),
              ("PROVE DI GRUPPO", ["si risolvono con un solo tiro condiviso.",
                                   "il valore piu' alto guida il risultato."])]:
    line(p, y, [(h, BOLD, NAME, DARKRED)]); y += LEAD + 4
    for b in bs: line(p, y, [(b, REG, BODY, BLACK)]); y += LEAD
    y += 10
doc.save("nocolon.pdf")

src = open("detect.py").read().replace("\nmain()\n", "\n"); ns = {}
exec(compile(src, "detect.py", "exec"), ns)
pages = [ns["lines_of"](pg) for pg in pymupdf.open("nocolon.pdf")]

def lab_colon(l):   # come prima: richiede i due punti
    if len(set(l["keys"])) < 2: return None
    return l["text"].split(":")[0].strip().lower() if ":" in l["text"] else None

def lab_style(l):   # generalizzata: l'etichetta e' il primo span, punto
    if len(set(l["keys"])) < 2: return None
    return l["keys"][0] and l["text"][:len(l["text"])].split()[0].strip(":").lower()

MED = st.median([k[1] for pg in pages for l in pg for k in l["keys"]])
for nome, fn in [("richiede i due punti", lab_colon), ("solo cambio di stile", lab_style)]:
    labels = Counter(x for pg in pages for l in pg if (x := fn(l)))
    rec = {k for k, n in labels.items() if n >= 2}
    print(f"\n--- etichetta = {nome} ---   ricorrenti: {sorted(rec)}")
    for pi, pg in enumerate(pages):
        idx = [i for i, l in enumerate(pg) if max(k[1] for k in l["keys"]) > MED]
        for n, i in enumerate(idx):
            end = idx[n+1]-1 if n+1 < len(idx) else len(pg)-1
            body = pg[i+1:end+1]
            labs = [fn(l) for l in body if fn(l) in rec]
            d = len(labs)/len(body) if body else 0
            print(f"   pag{pi} {pg[i]['text'][:22]:24} dens={d:.2f} distinte={len(set(labs))} "
                  f"-> {'SCHEDA' if d>=0.5 and len(set(labs))>=3 else 'scartata'}")
