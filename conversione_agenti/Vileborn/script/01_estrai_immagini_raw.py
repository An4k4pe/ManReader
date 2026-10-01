"""Estrae tutte le immagini del PDF alla risoluzione nativa.
- immagini con xref: una volta per xref. Se hanno soft mask -> PNG RGBA
  (colore + maschera). Altrimenti i byte originali dello stream (nessuna
  ricompressione); se MuPDF non li restituisce, PNG dal pixmap.
- immagini inline (xref 0): dai blocchi immagine di page.get_text('dict')
  il cui bbox coincide con un'occorrenza xref 0, una per occorrenza.
Scrive <out>/inventario.json con ogni occorrenza (pagina, xref, bbox, file, sha1 dei pixel).
Uso: python 01_estrai_immagini_raw.py <pdf> <out>
"""
import fitz, json, hashlib, sys, os
PDF, OUT = sys.argv[1], sys.argv[2]
d = fitz.open(PDF)
os.makedirs(OUT, exist_ok=True)

def rgb(pix):
    if pix.colorspace and pix.colorspace.n > 3:
        pix = fitz.Pixmap(fitz.csRGB, pix)
    return pix

def pixhash(pix):
    return hashlib.sha1(pix.samples + f'{pix.width}x{pix.height}x{pix.n}'.encode()).hexdigest()

def save_xref(x):
    smask = d.xref_get_key(x, 'SMask')
    smask = int(smask[1].split()[0]) if smask[0] == 'xref' else 0
    pix = rgb(fitz.Pixmap(d, x))
    if smask and not pix.alpha:
        try:
            pix = fitz.Pixmap(pix, fitz.Pixmap(d, smask))
        except Exception as e:
            print('maschera non applicata', x, e)
    if smask:
        fn = f'x{x:05d}.png'; pix.save(os.path.join(OUT, fn))
    else:
        try:
            base = d.extract_image(x)
            fn = f'x{x:05d}.{base["ext"]}'
            open(os.path.join(OUT, fn), 'wb').write(base['image'])
        except Exception as e:
            print('stream originale non disponibile, salvo PNG', x, e)
            fn = f'x{x:05d}.png'; pix.save(os.path.join(OUT, fn))
    return fn, pixhash(pix), pix.width, pix.height, bool(smask)

inv, done = [], {}
for p in d:
    infos = p.get_image_info(xrefs=True)
    for info in infos:
        x = info['xref']
        if x == 0:
            continue
        if x not in done:
            done[x] = save_xref(x)
        fn, h, w, hh, sm = done[x]
        inv.append(dict(page=p.number + 1, xref=x, bbox=[round(v, 1) for v in info['bbox']],
                        file=fn, sha1=h, w=w, h=hh, smask=sm))
    inl = [tuple(round(v) for v in i['bbox']) for i in infos if i['xref'] == 0]
    k = 0
    for b in p.get_text('dict', flags=fitz.TEXT_PRESERVE_IMAGES)['blocks']:
        if b['type'] != 1 or tuple(round(v) for v in b['bbox']) not in inl:
            continue
        k += 1
        fn = f'inline_p{p.number+1:03d}_{k}.{b["ext"]}'
        open(os.path.join(OUT, fn), 'wb').write(b['image'])
        inv.append(dict(page=p.number + 1, xref=0, bbox=[round(v, 1) for v in b['bbox']],
                        file=fn, sha1=hashlib.sha1(b['image']).hexdigest(),
                        w=b['width'], h=b['height'], smask=bool(b.get('mask'))))
json.dump(inv, open(os.path.join(OUT, 'inventario.json'), 'w'), indent=1)
print(len(done), 'xref distinti;', len(inv), 'occorrenze;', sum(1 for i in inv if i['xref'] == 0), 'inline')
