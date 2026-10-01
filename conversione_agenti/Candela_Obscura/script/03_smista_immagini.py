"""Copia le immagini estratte (raw/) nelle cartelle finali secondo classi_immagini.json.
  immagini/                         contenuto, un file per xref: pNNN_KK.ext (pagina della prima
                                    occorrenza, KK = ordine sulla pagina dall'alto, poi da sinistra)
  sfondi_e_ripetuti/sfondi/         sfondi e carte sotto il testo
  sfondi_e_ripetuti/decorazioni/    scarabocchi, sigilli e filetti a margine, logotipo
  sfondi_e_ripetuti/ombre/          maschere d'ombra inline (xref 0), una per contenuto identico
  sfondi_e_ripetuti/ripetuti/       asset presenti piu' volte (gruppi 'doppi'): un file solo, il piu' grande
Scrive sfondi_e_ripetuti/INDICE.json (file -> descrizione, pagine) e _lavoro/immagini_per_pagina.json.
Uso: python 03_smista_immagini.py <radice_output>
"""
import json, os, shutil, sys, collections
R = sys.argv[1]
raw = os.path.join(R, '_lavoro/raw')
inv = json.load(open(os.path.join(raw, 'inventario.json')))
cl = json.load(open(os.path.join(R, 'script/classi_immagini.json')))
sf, dec = cl['sfondo'], cl['decorazione']
group_of = {}
for g in cl['doppi']:
    for x in g:
        group_of[int(x)] = g
S = os.path.join(R, 'sfondi_e_ripetuti')
for sub in ('sfondi', 'decorazioni', 'ombre', 'ripetuti'):
    os.makedirs(os.path.join(S, sub), exist_ok=True)
os.makedirs(os.path.join(R, 'immagini'), exist_ok=True)

final = {}        # chiave (xref o sha1 per inline) -> percorso relativo
index = collections.OrderedDict()   # percorso -> {descr, pagine}
per_page = collections.defaultdict(list)
occ = sorted(inv, key=lambda i: (i['page'], i['bbox'][1], i['bbox'][0]))
kcount = collections.Counter()
nomb = 0
nrip = 0
for i in occ:
    x = i['xref']; ext = os.path.splitext(i['file'])[1]
    if x == 0:
        key = 'sha' + i['sha1']
        if key not in final:
            nomb += 1
            final[key] = f'sfondi_e_ripetuti/ombre/ombra_{nomb:02d}{ext}'
            shutil.copy(os.path.join(raw, i['file']), os.path.join(R, final[key]))
            index[final[key]] = dict(descr="maschera d'ombra portata sotto un'illustrazione", tipo='ombra', pagine=[])
        index[final[key]]['pagine'].append(i['page'])
        continue
    if x in group_of:
        g = group_of[x]; key = 'g' + '_'.join(g)
        if key not in final:
            cands = [j for j in inv if str(j['xref']) in g]
            big = max(cands, key=lambda j: j['w'] * j['h'])
            e2 = os.path.splitext(big['file'])[1]
            tipo = 'sfondo' if str(x) in sf else 'contenuto'
            if tipo == 'contenuto':
                nrip += 1
            name = 'pergamena_pagina' if tipo == 'sfondo' else f'ripetuto_{nrip:02d}'
            final[key] = f'sfondi_e_ripetuti/ripetuti/{name}{e2}'
            shutil.copy(os.path.join(raw, big['file']), os.path.join(R, final[key]))
            index[final[key]] = dict(descr=sf.get(str(x), 'asset di contenuto ripetuto'), tipo=tipo,
                                     xref=g, pagine=[])
        index[final[key]]['pagine'].append(i['page'])
        if str(x) not in sf:
            per_page[i['page']].append(dict(xref=x, file=final[key], bbox=i['bbox'], w=i['w'], h=i['h'], ripetuto=True))
        continue
    if str(x) in sf or str(x) in dec:
        tipo = 'sfondo' if str(x) in sf else 'decorazione'
        key = 'sha' + i['sha1']   # file identici al pixel con xref diversi: uno solo
        if key not in final:
            final[key] = f'sfondi_e_ripetuti/{"sfondi" if tipo == "sfondo" else "decorazioni"}/x{x:05d}{ext}'
            shutil.copy(os.path.join(raw, i['file']), os.path.join(R, final[key]))
            index[final[key]] = dict(descr=(sf.get(str(x)) or dec.get(str(x))), tipo=tipo, xref=[x], pagine=[])
        if x not in index[final[key]]['xref']:
            index[final[key]]['xref'].append(x)
        index[final[key]]['pagine'].append(i['page'])
        continue
    if x not in final:
        kcount[i['page']] += 1
        final[x] = f'immagini/p{i["page"]:03d}_{kcount[i["page"]]:02d}{ext}'
        shutil.copy(os.path.join(raw, i['file']), os.path.join(R, final[x]))
    per_page[i['page']].append(dict(xref=x, file=final[x], bbox=i['bbox'], w=i['w'], h=i['h'], ripetuto=False))
for v in index.values():
    v['pagine'] = sorted(set(v['pagine']))
json.dump(index, open(os.path.join(S, 'INDICE.json'), 'w'), indent=1, ensure_ascii=False)
json.dump(per_page, open(os.path.join(R, '_lavoro/immagini_per_pagina.json'), 'w'), indent=1)
n_img = len(os.listdir(os.path.join(R, 'immagini')))
print('immagini di contenuto:', n_img, '| in sfondi_e_ripetuti:', len(index),
      {k: sum(1 for v in index.values() if v['tipo'] == k) for k in ('sfondo', 'decorazione', 'ombra', 'contenuto')})
