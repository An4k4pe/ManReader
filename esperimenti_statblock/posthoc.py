"""D5 e D6: progettati DOPO aver visto i fallimenti di D1-D4. Post-hoc, dichiarato.

Il loro valore non e' il punteggio (dati sintetici = tautologia) ma se
sopravvivono alle pagine negative, che sono costruite per ucciderli.
"""
from __future__ import annotations
import json, statistics as st, pymupdf
from collections import Counter

src = open("detect.py").read().replace("\nmain()\n", "\n")
ns = {}; exec(compile(src, "detect.py", "exec"), ns)
doc = pymupdf.open("synth.pdf")
pages = [ns["lines_of"](p) for p in doc]
truth = set(ns["gt_indices"](pages, json.load(open("ground_truth.json"))))

def openers(pg, med):
    return [i for i, l in enumerate(pg) if max(k[1] for k in l["keys"]) > med]

def label_of(line):
    """Etichetta candidata: testo del primo span se la riga ha piu' stili."""
    if len(set(line["keys"])) < 2:
        return None
    t = line["text"]
    return t.split(":")[0].strip().lower() if ":" in t else None

sizes = [k[1] for pg in pages for l in pg for k in l["keys"]]
MED = st.median(sizes)

# ---- D5: apertura tipografica AND densita' di campi nel blocco che segue ----
def d5(require_short: bool):
    recs = []
    for pi, pg in enumerate(pages):
        idx = openers(pg, MED)
        wmax = max((l["x1"] - l["x0"] for l in pg), default=1.0)
        for n, i in enumerate(idx):
            end = idx[n + 1] - 1 if n + 1 < len(idx) else len(pg) - 1
            body = pg[i + 1:end + 1]
            if not body:
                continue
            def is_field(l):
                ok = len(set(l["keys"])) >= 2 and ":" in l["text"]
                return ok and ((l["x1"] - l["x0"]) < 0.6 * wmax if require_short else ok)
            if sum(map(is_field, body)) / len(body) >= 0.5:
                recs.append((pi, i, end))
    return recs

# ---- D6: le etichette si ripetono fra istanze (nessun vocabolario esterno) ----
labels = Counter(x for pg in pages for l in pg if (x := label_of(l)))
recurring = {k for k, n in labels.items() if n >= 2}

def d6():
    recs = []
    for pi, pg in enumerate(pages):
        idx = openers(pg, MED)
        for n, i in enumerate(idx):
            end = idx[n + 1] - 1 if n + 1 < len(idx) else len(pg) - 1
            body = pg[i + 1:end + 1]
            if body and sum(1 for l in body if label_of(l) in recurring) / len(body) >= 0.5:
                recs.append((pi, i, end))
    return recs

def score(recs):
    tp = len(truth & set(recs))
    return tp, len(recs) - tp, len(truth) - tp, sum(1 for r in recs if r not in truth and r[0] >= 2)

print(f"{'metodo (post-hoc)':52} {'TP':>3} {'FP':>3} {'FN':>3} {'FP negativi':>12}")
print("-" * 88)
for nm, r in [("D5 apertura + densita' campi (con righe corte)", d5(True)),
              ("D5b apertura + densita' campi (senza corte)", d5(False)),
              ("D6 apertura + etichette RICORRENTI", d6())]:
    tp, fp, fn, fpn = score(r)
    print(f"{nm:52} {tp:>3} {fp:>3} {fn:>3} {fpn:>12}")

print("\n--- il segnale di D6, per pagina (frazione di righe con etichetta ricorrente) ---")
for pi, pg in enumerate(pages):
    f = sum(1 for l in pg if label_of(l) in recurring) / max(len(pg), 1)
    kind = ["bestiario", "bestiario var", "PROSA (neg)", "LISTA REGOLE (neg)", "TITOLI (neg)"][pi]
    print(f"  pag {pi} {kind:22} {f:5.2f}   righe {len(pg)}")
print(f"\netichette ricorrenti indotte dal documento: {sorted(recurring)}")
print(f"etichette viste una volta sola (scartate): {sorted(k for k,n in labels.items() if n<2)}")
