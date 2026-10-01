"""Misure per classificare gli asset senza guardarli (v2).
Per ogni xref: su quante pagine compare lo stesso contenuto (SHA-1 dei pixel,
regola di ManReader: document_asset_recurrence_measurements), la collocazione
piu' stretta e piu' larga in pt, la lettera piu' piccola che il documento stampa
(regola BELOW_TEXT_SCALE di document_asset_policy), quanta area della collocazione
e' coperta da testo, e la densita' di bordi dell'immagine (quanto 'disegno' c'e').
Scrive _lavoro/v2/misure_asset.json.
Uso: python misura_asset.py <pdf> <radice>
"""
import fitz, json, sys, os, collections
from PIL import Image, ImageFilter
PDF, R = sys.argv[1], sys.argv[2]
d = fitz.open(PDF)
inv = json.load(open(os.path.join(R, '_lavoro/raw/inventario.json')))
os.makedirs(os.path.join(R, '_lavoro/v2'), exist_ok=True)

# lettera piu' piccola stampata: corpo minimo tra le righe con almeno una lettera,
# escluso l'alt-text incorporato (corpo > 60) e i corpi degeneri (< 1)
sizes = collections.Counter()
text_rects = collections.defaultdict(list)
for p in d:
    for b in p.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            for s in l['spans']:
                if any(c.isalnum() for c in s['text']) and 1 <= s['size'] <= 60:
                    sizes[round(s['size'], 1)] += len(s['text'])
                    text_rects[p.number + 1].append(fitz.Rect(s['bbox']))
min_letter = min(sizes)
# corpo del testo: la dimensione che porta piu' caratteri
body = sizes.most_common(1)[0][0]

def edge_density(path):
    try:
        im = Image.open(path).convert('RGBA')
    except Exception:
        return None   # file che Pillow non legge (su Draw Steel alcune inline): segnato, non blocca
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
    g = bg.convert('L'); g.thumbnail((256, 256))
    e = g.filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 40 else 0)
    return e.histogram()[255] / (e.width * e.height)

by_sha = collections.defaultdict(set)
for i in inv:
    by_sha[i['sha1']].add(i['page'])
out = {}
for i in inv:
    key = str(i['xref']) if i['xref'] else i['file']
    r = fitz.Rect(i['bbox']) & d[i['page'] - 1].rect
    w, h = r.width, r.height
    cov = 0.0
    if r.get_area() > 0:
        cov = sum((t & r).get_area() for t in text_rects[i['page']]) / r.get_area()
    o = out.setdefault(key, dict(xref=i['xref'], file=i['file'], pages=sorted(by_sha[i['sha1']]),
                                 min_side=1e9, max_side=0, text_cover=0.0, inline=i['xref'] == 0))
    if w * h > 0:
        o['min_side'] = min(o['min_side'], min(w, h))
        o['max_side'] = max(o['max_side'], max(w, h))
    o['text_cover'] = max(o['text_cover'], cov)
for o in out.values():
    o['edges'] = edge_density(os.path.join(R, '_lavoro/raw', o['file']))
json.dump(dict(min_letter=min_letter, body=body, assets=out),
          open(os.path.join(R, '_lavoro/v2/misure_asset.json'), 'w'), indent=1)
print('illeggibili:', sum(1 for o in out.values() if o['edges'] is None), '|', 'lettera minima', min_letter, 'pt | corpo', body, 'pt | asset misurati', len(out))
