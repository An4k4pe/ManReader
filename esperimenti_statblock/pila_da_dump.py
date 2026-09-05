"""Esegue il rilevatore congelato su un dump di span invece che sul PDF.

Non modifica `pila.py`: ne sostituisce solo la funzione di caricamento con una
che legge il dump. L'equivalenza va verificata, non assunta — vedi --verifica.

Uso:  python3 pila_da_dump.py manuale.spans.json.gz [--verita REGEX]
      python3 pila_da_dump.py manuale.spans.json.gz --verifica manuale.pdf
"""
from __future__ import annotations
import gzip, json, sys
sys.path.insert(0, "/home/user/ManReader/esperimenti_statblock")
import pila


def carica_dump(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        d = json.load(f)
    pagine = []
    for righe in d["pagine"]:
        out = []
        for y0, x0, spans in righe:
            out.append({"y0": y0, "x0": x0,
                        "testo": "".join(s[0] for s in spans),
                        "stili": [(s[1], s[2], s[3]) for s in spans],
                        "span": [s[0] for s in spans]})
        # stesso ordinamento a colonne di pila.carica
        if out:
            xs = sorted({round(r["x0"], 1) for r in out})
            gruppi, cur = [], [xs[0]]
            for a, b in zip(xs, xs[1:]):
                if b - a <= pila.COL_GAP: cur.append(b)
                else: gruppi.append(cur); cur = [b]
            gruppi.append(cur)
            bordi = [min(g) for g in gruppi]
            col = lambda r: max(i for i, x in enumerate(bordi) if r["x0"] >= x - 0.5)
            out.sort(key=lambda r: (col(r), round(r["y0"], 1), r["x0"]))
        pagine.append(out)
    return pagine


def _riassunto(pagine):
    nuclei, schema = pila.nuclei_di(pagine)
    gruppi = pila.raggruppa(nuclei, pagine, schema)
    righe = [f"schema={len(schema)} nuclei={len(nuclei)} gruppi={len(gruppi)}"]
    for g in gruppi[:12]:
        righe.append(f"  {len(g['nuclei'])} {sorted(g['firma'])[:6]}")
    return "\n".join(righe)


if __name__ == "__main__":
    dump = sys.argv[1]
    pagine = carica_dump(dump)
    if "--verifica" in sys.argv:
        pdf = sys.argv[sys.argv.index("--verifica") + 1]
        da_pdf = pila.carica(pdf)
        uguali = len(da_pdf) == len(pagine) and all(
            len(a) == len(b) and all(
                abs(x["y0"] - y["y0"]) < 0.02 and abs(x["x0"] - y["x0"]) < 0.02
                and x["testo"] == y["testo"] and x["stili"] == y["stili"]
                for x, y in zip(a, b))
            for a, b in zip(da_pdf, pagine))
        print(f"righe identiche riga per riga: {uguali}")
        ra, rb = _riassunto(da_pdf), _riassunto(pagine)
        print(f"analisi identica: {ra == rb}")
        if ra != rb:
            print("--- da PDF ---\n" + ra + "\n--- da dump ---\n" + rb)
    else:
        print(_riassunto(pagine))
