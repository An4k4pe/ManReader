"""I due confondenti che in un manuale vero rompono un metodo a etichette:
   1. una scheda spezzata dal salto di pagina (la coda non ha riga-nome);
   2. richiami ricorrenti ('Esempio:', 'Nota:') che non sono schede.
Dichiarato: sono casi che ho scelto per rompere D6, non per confermarlo.
"""
from __future__ import annotations
import statistics as st, pymupdf
from collections import Counter

BOLD, REG = "hebo", "helv"
BODY, NAME = 9.0, 12.0
BLACK, DARKRED = (0, 0, 0), (0.5, 0.05, 0.05)
X0, TOP, LEAD = 60.0, 70.0, 13.0

def line(page, y, spans):
    x = X0
    for t, f, s, c in spans:
        page.insert_text((x, y), t, fontname=f, fontsize=s, color=c)
        x += pymupdf.get_text_length(t, fontname=f, fontsize=s)

def fields(page, y, fs):
    for lab, val in fs:
        line(page, y, [(lab + ": ", BOLD, BODY, BLACK), (val, REG, BODY, BLACK)]); y += LEAD
    return y

doc = pymupdf.open()
# --- pag 0: bestiario normale + ultima scheda TRONCATA dal salto pagina ---
p = doc.new_page(width=612, height=792); y = TOP
line(p, y, [("LUPO D'OMBRA", BOLD, NAME, DARKRED)]); y += LEAD + 4
y = fields(p, y, [("Difficolta", "12"), ("Soglie", "6/11"), ("PF", "4"),
                  ("Stress", "3"), ("Attacco", "+2"), ("Arma", "Morso, mischia, 1d6 fis")])
y += 10
line(p, y, [("TROLL DI PIETRA", BOLD, NAME, DARKRED)]); y += LEAD + 4
y = fields(p, y, [("Difficolta", "16"), ("Soglie", "14/28")])   # <- si interrompe qui

# --- pag 1: CODA della scheda precedente, senza riga-nome, poi una nuova ---
p = doc.new_page(width=612, height=792); y = TOP
y = fields(p, y, [("PF", "10"), ("Stress", "7"), ("Attacco", "+5"),
                  ("Arma", "Pugni, mischia, 2d10+4 fis"), ("Moventi", "Difendere il ponte")])
y += 10
line(p, y, [("SCIACALLO", BOLD, NAME, DARKRED)]); y += LEAD + 4
y = fields(p, y, [("Difficolta", "8"), ("Soglie", "2/5"), ("PF", "1"),
                  ("Stress", "1"), ("Attacco", "+0")])

# --- pag 2: richiami ricorrenti che NON sono schede ---
p = doc.new_page(width=612, height=792); y = TOP
line(p, y, [("USARE LE PROVE", BOLD, NAME, DARKRED)]); y += LEAD + 4
for testo in ["il giocatore descrive cosa tenta, poi tira.",
              "un fallimento non blocca la scena, la complica.",
              "il narratore puo' offrire un costo invece di un no."]:
    line(p, y, [("Esempio: ", BOLD, BODY, BLACK), (testo, REG, BODY, BLACK)]); y += LEAD
for testo in ["le prove contrastate usano il valore piu' alto.",
              "le prove di gruppo si risolvono con un solo tiro."]:
    line(p, y, [("Nota: ", BOLD, BODY, BLACK), (testo, REG, BODY, BLACK)]); y += LEAD
doc.save("confound.pdf")

# ---------- valutazione ----------
src = open("detect.py").read().replace("\nmain()\n", "\n"); ns = {}
exec(compile(src, "detect.py", "exec"), ns)
pages = [ns["lines_of"](p) for p in pymupdf.open("confound.pdf")]

def label_of(l):
    if len(set(l["keys"])) < 2: return None
    return l["text"].split(":")[0].strip().lower() if ":" in l["text"] else None

MED = st.median([k[1] for pg in pages for l in pg for k in l["keys"]])
labels = Counter(x for pg in pages for l in pg if (x := label_of(l)))
recurring = {k for k, n in labels.items() if n >= 2}

print("etichette giudicate ricorrenti:", sorted(recurring), "\n")
for pi, pg in enumerate(pages):
    idx = [i for i, l in enumerate(pg) if max(k[1] for k in l["keys"]) > MED]
    frac = sum(1 for l in pg if label_of(l) in recurring) / len(pg)
    kind = ["schede + una TRONCATA", "CODA orfana + una nuova", "richiami ricorrenti (neg)"][pi]
    print(f"pag {pi} {kind:28} righe={len(pg):2}  aperture={idx}  frazione_etichette={frac:.2f}")
    for n, i in enumerate(idx):
        end = idx[n+1]-1 if n+1 < len(idx) else len(pg)-1
        body = pg[i+1:end+1]
        d = sum(1 for l in body if label_of(l) in recurring)/len(body) if body else 0
        print(f"      apertura riga {i} {pg[i]['text'][:26]!r:30} densita'={d:.2f} -> {'SCHEDA' if d>=0.5 else 'scartata'}")
    if not idx:
        print("      NESSUNA APERTURA: le righe di questa pagina non sono attribuite a nessuna scheda")
