"""Inventario dei glifi dei font di simboli di un manuale: per ogni carattere, dove compare nella
riga (inizio, mezzo, fine, solo), quante volte, e tre esempi con il contesto e la pagina.
E' il materiale per chi compila il profilo del manuale (profilo.json, chiave 'glifi').
Uso: python inventario_glifi.py <pdf> <uscita.json>
"""
import collections, json, os, sys
import fitz
sys.path.insert(0, os.path.dirname(__file__))
import bozza_testo_v2 as B
d = fitz.open(sys.argv[1])
F = B.measure_facts(d)
inv = collections.defaultdict(lambda: dict(n=collections.Counter(), esempi=[]))
for p in d:
    for b in p.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            sp = [s for s in l['spans'] if s['text'].strip()]
            for i, s in enumerate(sp):
                if s['font'] not in F['marker']:
                    continue
                where = 'solo' if len(sp) == 1 else ('inizio' if i == 0 else ('fine' if i == len(sp) - 1 else 'mezzo'))
                for ch in s['text'].strip():
                    e = inv[ch]; e['n'][where] += 1
                    if len(e['esempi']) < 3:
                        ctx = ''.join(('⟦' + x['text'] + '⟧') if x is s else x['text'] for x in sp)
                        e['esempi'].append(dict(pagina=p.number + 1, contesto=ctx[:120], bbox=[round(v) for v in s['bbox']]))
out = {'font_simboli': sorted(F['marker']), 'glifi': {k: dict(n=dict(v['n']), esempi=v['esempi']) for k, v in inv.items()}}
json.dump(out, open(sys.argv[2], 'w'), indent=1, ensure_ascii=False)
print(len(inv), 'glifi in', sorted(F['marker']))
