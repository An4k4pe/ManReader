"""Criterio_StrategiaTabella_v1.md — quale strategia taglia meno il testo."""
import random, sys
sys.path.insert(0, ".")
import fitz, pdfplumber
from pymupdf_capture import capture_pymupdf_page
from primitive_normalizer import normalize_backend_page_capture

SEED = "20260821"
N = 12
MANUALS = ("Apo","BiD","BoB","Dag","DB","DIE","DrM","DrW","Fab","FW","FWK","Kul","Lan","SV","Vil","Wil")
USED = {("DB",89),("DB",98),("DrM",86),("Vil",222),("DB",52),("DB",49),("Dag",163),("DrW",96),("DB",17),("Dag",83)}
STRATEGIES = {
    "lines/lines": {"vertical_strategy":"lines","horizontal_strategy":"lines"},
    "text/lines (producer)": {"vertical_strategy":"text","horizontal_strategy":"lines"},
    "lines_strict": {"vertical_strategy":"lines_strict","horizontal_strategy":"lines_strict"},
    "text/text": {"vertical_strategy":"text","horizontal_strategy":"text"},
}

docs = {n: (fitz.open(f"../../../{n}.pdf"), pdfplumber.open(f"../../../{n}.pdf")) for n in MANUALS}
pool = [(n,i) for n in MANUALS for i in range(len(docs[n][0])) if (n,i) not in USED]
rng = random.Random(); rng.seed(SEED)
sample = rng.sample(pool, N)
print(f"seed {SEED} — campione: {sorted(sample)}\n")

totals = {k: {"cut":0, "spans":0, "resolved":0, "found":0} for k in STRATEGIES}
pages_with_grid = 0
per_page = []

for name, idx in sample:
    fdoc, pdoc = docs[name]
    page = fdoc[idx]
    if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
        print(f"  SKIP {name} idx={idx}: guardia pagina"); continue
    cap = capture_pymupdf_page(page, source_id="x", page_id=f"page:{idx+1:04d}", capture_id="c")
    np_ = normalize_backend_page_capture(cap)
    spans = [p for p in np_.text_primitives if p.text.strip()]
    row = {"page": f"{name} idx {idx}"}
    any_grid = False
    for label, settings in STRATEGIES.items():
        tables = pdoc.pages[idx].find_tables(table_settings=settings)
        found = len(tables); resolved = 0; cut = 0; considered = 0
        for t in tables:
            cells = [c for r in t.extract() for c in r]
            full = sum(1 for c in cells if c and c.strip())
            if cells and full / len(cells) >= 0.80:
                resolved += 1
            xs = sorted({c[0] for c in t.cells if c} | {c[2] for c in t.cells if c})
            x0, y0, x1, y1 = t.bbox
            for s in spans:
                sx0, sy0, sx1, sy1 = s.bbox
                if sx1 <= x0 or sx0 >= x1 or sy1 <= y0 or sy0 >= y1:
                    continue
                considered += 1
                if any(sx0 + 0.5 < b < sx1 - 0.5 for b in xs):
                    cut += 1
        if found: any_grid = True
        totals[label]["cut"] += cut; totals[label]["spans"] += considered
        totals[label]["resolved"] += resolved; totals[label]["found"] += found
        row[label] = (found, resolved, cut, considered)
    if any_grid: pages_with_grid += 1
    per_page.append(row)

print(f"pagine con almeno una griglia (denominatore): {pages_with_grid}/{len(per_page)}\n")
print(f"{'pagina':14s} {'lines: tag/ris':>16s} {'producer: tag/ris':>18s}   verdetto per pagina")
dom=0; tie=0; lose=0; useful=0
for r in per_page:
    fL,rL,cL,sL = r["lines/lines"]; fP,rP,cP,sP = r["text/lines (producer)"]
    if fL==0 and fP==0: continue
    useful+=1
    v = "lines domina" if (cL<=cP and rL>=rP and (cL<cP or rL>rP)) else ("pari" if (cL==cP and rL==rP) else "producer meglio")
    if v=="lines domina": dom+=1
    elif v=="pari": tie+=1
    else: lose+=1
    print(f"  {r['page']:14s} {cL:6d}/{rL:<8d} {cP:8d}/{rP:<8d}   {v}")
print(f"\npagine utili: {useful}  lines domina: {dom} ({dom/max(1,useful):.0%})  pari: {tie}  producer meglio: {lose}")
print()
print(f"{'strategia':22s} {'trovate':>8s} {'risolte':>8s} {'span tagliati':>16s}")
for label, t in totals.items():
    pct = t["cut"]/t["spans"] if t["spans"] else 0.0
    print(f"{label:22s} {t['found']:8d} {t['resolved']:8d} {t['cut']:7d}/{t['spans']:<6d} ({pct:.0%})")
