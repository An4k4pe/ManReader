"""Estrae gli alt-text (/Alt) degli elementi /Figure dell'albero di struttura, con la pagina (/Pg)
quando c'e'. Serve solo come controllo indipendente delle note scritte a vista: le note sono
state scritte senza leggere questo file.
Uso: python 05_alt_text_editore.py <pdf> <out.json>
"""
import fitz, json, sys, re
d = fitz.open(sys.argv[1])
pg_of = {d[i].xref: i + 1 for i in range(d.page_count)}
out = []
for x in range(1, d.xref_length()):
    try:
        t, v = d.xref_get_key(x, 'Alt')
    except Exception:
        continue
    if t == 'null':
        continue
    s = d.xref_get_key(x, 'S')[1]
    pg = d.xref_get_key(x, 'Pg')
    page = pg_of.get(int(pg[1].split()[0])) if pg[0] == 'xref' else None
    out.append(dict(xref=x, S=s, page=page, alt=v))
json.dump(out, open(sys.argv[2], 'w'), indent=1, ensure_ascii=False)
print(len(out), 'alt-text;', sum(1 for o in out if o['page']), 'con pagina')
