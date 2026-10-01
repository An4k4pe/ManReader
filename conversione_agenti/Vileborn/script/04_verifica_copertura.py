"""Verifica di conservazione del testo, pagina per pagina: bozza (estratta) vs finale (rivista).
Criterio fissato prima della misura: per ogni pagina la copertura (parole della bozza,
come multinsieme, ritrovate nel finale) >= 0.99. Le parole in piu' nel finale devono stare
in note immagine, trascrizioni dichiarate o tratti <!-- da render -->: le conto a parte.
Un paragrafo spezzato tra due pagine sposta parole dalla pagina N+1 alla N: il confronto
si fa quindi anche sul totale del documento.
Uso: python 04_verifica_copertura.py <radice>
"""
import re, sys, os, collections
R = sys.argv[1]
B, F = os.path.join(R, '_lavoro/bozza2'), os.path.join(R, '_lavoro/finale')

def words(s):
    s = re.sub(r'<!--.*?-->', ' ', s, flags=re.S)
    s = re.sub(r'\*\[IMMAGINE: [^\]]*\]\*', ' ', s)
    s = re.sub(r'\[(manoscritto|dattiloscritto)\]', ' ', s)
    s = s.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    return collections.Counter(w.lower() for w in re.findall(r"[A-Za-z0-9À-ÿ]+(?:'[A-Za-z]+)?", s))

def split_final(s):
    """Separa il testo 'di contenuto' da note immagine e trascrizioni."""
    extra, main = [], []
    in_tr = False
    for line in s.splitlines():
        if re.match(r'^\*\[(Illustrazione|Mappa|Documento|Scheda|Simbolo|Oggetto)', line):
            extra.append(line); in_tr = False; continue
        if "[Testo nell'immagine" in line:
            in_tr = True; extra.append(line); continue
        if in_tr and (line.startswith('>') or line.strip()):
            extra.append(line); continue
        if in_tr and line.strip() == '':
            continue
        in_tr = False
        if '<!-- da render -->' in line:
            extra.append(line)
            # marcatore su riga propria: vale per il blocco che segue
            in_tr = line.strip() == '<!-- da render -->'
            continue
        main.append(line)
    return '\n'.join(main), '\n'.join(extra)

tot_b, tot_f, tot_x = collections.Counter(), collections.Counter(), collections.Counter()
rows = []
for n in range(1, 273):
    fb, ff = os.path.join(B, f'p{n:03d}.md'), os.path.join(F, f'p{n:03d}.md')
    if not os.path.exists(ff):
        rows.append((n, None)); continue
    wb = words(open(fb).read())
    main, extra = split_final(open(ff).read())
    wf, wx = words(main), words(extra)
    tot_b += wb; tot_f += wf; tot_x += wx
    nb = sum(wb.values())
    miss = wb - wf - wx
    add = wf - wb
    cov = 1 - sum(miss.values()) / nb if nb else 1.0
    rows.append((n, dict(nb=nb, cov=cov, miss=miss, add=add, nx=sum(wx.values()))))
print('pagina  parole_bozza  copertura  mancanti  in_piu_nel_testo  parole_note/trascr')
low = []
for n, r in rows:
    if r is None:
        print(f'{n:4d}   MANCA il finale'); continue
    flag = '' if r['cov'] >= 0.99 else '  <-- sotto soglia'
    if flag: low.append(n)
    print(f"{n:4d}  {r['nb']:6d}  {r['cov']:8.3f}  {sum(r['miss'].values()):6d}  {sum(r['add'].values()):6d}  {r['nx']:6d}{flag}")
    if flag or sum(r['add'].values()) > 5:
        print('        mancanti:', dict(r['miss'].most_common(15)))
        print('        in piu:  ', dict(r['add'].most_common(15)))
m = tot_b - tot_f - tot_x
print('\nTOTALE documento: parole bozza', sum(tot_b.values()), '| mancanti nel finale (testo+note)', sum(m.values()),
      f"| copertura {1-sum(m.values())/sum(tot_b.values()):.4f}")
print('pagine sotto soglia:', low)
