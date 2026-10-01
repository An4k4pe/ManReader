"""Orchestratore della conversione di un manuale: fasi, stato, lotti per gli agenti, validazione.

Lo script fa tutto il lavoro meccanico e tiene lo stato in <radice>/stato.json; gli agenti (sotto-agenti
di Claude, o un altro esecutore) fanno solo il lavoro di giudizio, su compiti che lo script prepara in
<radice>/_lavoro/compiti/ e che lo script stesso valida quando tornano. Chi orchestra segue RUNBOOK.md.

Fasi (in ordine; ognuna si puo' rilanciare):
  init       crea la radice e manuale.json (pdf, titolo, lingua)
  immagini   estrae le immagini, le misura, le classifica in automatico, prepara i fogli provini e il
             compito 'asset' (revisione della classificazione) per un agente
  profilo    inventario dei glifi dei font di simboli e compito 'profilo' per un agente
  bozza      smista le immagini secondo la classificazione approvata e genera la bozza (con profilo e
             segnaposto immagine) in _lavoro/bozza/
  compiti    prepara i lotti: 'pagine' (tutte, o segnalate + campione se --smistamento) e 'immagini'
  valida     controlla le consegne degli agenti; segna i lotti OK o DA RIFARE con il motivo
  assembla   uniforma (etichette sopra i titoli), inserisce le note, ricuce i paragrafi tra pagine,
             scrive il file unico e l'indice di sfondi_e_ripetuti, stampa i controlli finali
  stato      riepilogo

Uso: python orchestra.py <fase> <radice> [opzioni]
"""
import argparse, glob, json, os, random, re, shutil, subprocess, sys, collections, difflib

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(HERE, 'script')
M = os.path.join(HERE, 'modelli')
PY = '/home/an4k4pe/Documenti/ManReader (Copia)/venv/bin/python'


def run(*args, env=None):
    r = subprocess.run([PY, *args], capture_output=True, text=True, env=env)
    out = '\n'.join(l for l in (r.stdout + r.stderr).splitlines() if 'structure tree' not in l and l.strip())
    if r.returncode:
        sys.exit(f'errore in {args[0]}:\n{out}')
    return out


def load(path, default=None):
    return json.load(open(path)) if os.path.exists(path) else default


def save(path, obj):
    json.dump(obj, open(path, 'w'), indent=1, ensure_ascii=False)


class Man:
    def __init__(self, root):
        self.r = os.path.abspath(root)
        self.cfg = load(self.p('manuale.json'), {})
        self.st = load(self.p('stato.json'), {'fasi': {}, 'lotti': {}})

    def p(self, *a):
        return os.path.join(self.r, *a)

    def w(self, *a):
        return self.p('_lavoro', *a)

    def done(self, fase, **info):
        self.st['fasi'][fase] = dict(fatto=True, **info)
        save(self.p('stato.json'), self.st)

    @property
    def pdf(self):
        return self.cfg['pdf']

    def env(self):
        e = dict(os.environ)
        if os.path.exists(self.p('profilo.json')):
            e['MANREADER_PROFILO'] = self.p('profilo.json')
        return e


def modello(nome, man, **extra):
    """Istruzioni per gli agenti: modello generico + decisioni del manuale (decisioni.md, se c'e')."""
    t = open(os.path.join(M, nome)).read()
    dec = man.p('decisioni.md')
    t = t.replace('{RADICE}', man.r).replace('{PDF}', man.pdf).replace('{PY}', PY).replace('{LINGUA}', man.cfg.get('lingua', ''))
    for k, v in extra.items():
        t = t.replace('{' + k + '}', str(v))
    if os.path.exists(dec):
        t += '\n\n## Decisioni proprie di questo manuale (valgono sopra le regole generali)\n\n' + open(dec).read()
    return t


# ---------------------------------------------------------------- fasi

def f_init(man, a):
    os.makedirs(man.w('compiti'), exist_ok=True)
    for d in ('script', 'immagini', 'sfondi_e_ripetuti'):
        os.makedirs(man.p(d), exist_ok=True)
    man.cfg = dict(pdf=os.path.abspath(a.pdf), titolo=a.titolo or os.path.basename(a.pdf), lingua=a.lingua)
    save(man.p('manuale.json'), man.cfg)
    import fitz
    d = fitz.open(man.pdf)
    man.done('init', pagine=d.page_count, segnalibri=len(d.get_toc()))
    print(f'{man.cfg["titolo"]}: {d.page_count} pagine, {len(d.get_toc())} segnalibri')


def f_immagini(man, a):
    print(run(os.path.join(S, '01_estrai_immagini_raw.py'), man.pdf, man.w('raw')))
    print(run(os.path.join(S, 'misura_asset.py'), man.pdf, man.r))
    print(run(os.path.join(S, 'classifica_asset.py'), man.r))
    # fogli provini per classe automatica: materiale del compito 'asset'
    from PIL import Image, ImageDraw
    mis = load(man.w('v2', 'misure_asset.json'))['assets']; dec = load(man.w('v2', 'classi_auto.json'))
    by = collections.defaultdict(list)
    for k, c in dec.items():
        if mis[k]['xref']:
            by[c].append(k)
    sheets = []
    for c, ks in by.items():
        ks.sort(key=lambda k: mis[k]['pages'][0])
        for part in range(0, len(ks), 60):
            sub = ks[part:part + 60]; SZ, W = 150, 10
            im = Image.new('RGB', (W * SZ, ((len(sub) + W - 1) // W) * (SZ + 12)), (90, 90, 90)); dr = ImageDraw.Draw(im)
            for i, k in enumerate(sub):
                try:
                    t = Image.open(man.w('raw', mis[k]['file'])).convert('RGBA'); t.thumbnail((SZ, SZ))
                except Exception:
                    t = Image.new('RGBA', (SZ, SZ), (255, 0, 0, 255))   # illeggibile: riquadro rosso
                X, Y = (i % W) * SZ, (i // W) * (SZ + 12); im.paste(t, (X, Y + 12), t)
                dr.text((X + 2, Y), f"{k} p{mis[k]['pages'][0]}", fill=(255, 255, 0))
            f = man.w(f'provini_{c}_{part // 60}.png'); im.save(f); sheets.append(os.path.basename(f))
    open(man.w('compiti', 'asset.md'), 'w').write(modello('ISTRUZIONI_ASSET.md', man, PROVINI=', '.join(sorted(sheets))))
    man.done('immagini', classi=dict(collections.Counter(dec.values())))
    print('compito per l\'agente:', man.w('compiti', 'asset.md'), '| fogli:', len(sheets))


def f_profilo(man, a):
    print(run(os.path.join(S, 'inventario_glifi.py'), man.pdf, man.w('inventario_glifi.json')))
    open(man.w('compiti', 'profilo.md'), 'w').write(modello('ISTRUZIONI_PROFILO.md', man))
    man.done('profilo')
    print('compito per l\'agente:', man.w('compiti', 'profilo.md'))


def f_bozza(man, a):
    if not os.path.exists(man.p('script', 'classi_immagini.json')):
        sys.exit('manca script/classi_immagini.json: prima il compito asset (o --auto per la sola classificazione automatica)')
    shutil.copy(os.path.join(S, '03_smista_immagini.py'), man.p('script'))
    for d in ('immagini', 'sfondi_e_ripetuti'):
        shutil.rmtree(man.p(d), ignore_errors=True)
    print(run(os.path.join(S, '03_smista_immagini.py'), man.r))
    print(run(os.path.join(S, 'bozza_testo_v3.py'), man.pdf, man.w('bozza'), man.w('immagini_per_pagina.json'), env=man.env()))
    print(run(os.path.join(S, 'smistamento.py'), man.pdf, man.r))
    man.done('bozza')


def auto_classi(man):
    """Classificazione automatica senza revisione: converte classi_auto.json nel formato di 03."""
    dec = load(man.w('v2', 'classi_auto.json')); mis = load(man.w('v2', 'misure_asset.json'))['assets']
    D = {'ricorrente': 'arredo ripetuto', 'sotto_scala': 'fregio o filetto sottile', 'carta': 'carta o texture di fondo',
         'segno': 'segno decorativo', 'listello': 'striscia o frammento sottile'}
    sf = {k: D[c] for k, c in dec.items() if mis[k]['xref'] and c in D and c != 'segno'}
    de = {k: D[c] for k, c in dec.items() if mis[k]['xref'] and c == 'segno'}
    save(man.p('script', 'classi_immagini.json'), dict(_nota='classificazione automatica non rivista', sfondo=sf, decorazione=de, doppi=[]))


def f_compiti(man, a):
    n_pag = man.st['fasi']['init']['pagine']
    sm = {int(k): v for k, v in load(man.w('smistamento.json'), {}).items()}
    if a.smistamento:
        flag = sorted(n for n, s in sm.items() if s)
        unf = sorted(n for n, s in sm.items() if not s)
        random.seed(a.seed); camp = sorted(random.sample(unf, min(a.campione, len(unf))))
        pagine = sorted(set(flag) | set(camp))
        for n in range(1, n_pag + 1):
            if n not in pagine:
                shutil.copy(man.w('bozza', f'p{n:03d}.md'), man.w('finale', f'p{n:03d}.md'))
    else:
        pagine, camp = list(range(1, n_pag + 1)), []
    os.makedirs(man.w('finale'), exist_ok=True); os.makedirs(man.w('log'), exist_ok=True); os.makedirs(man.w('note'), exist_ok=True)
    k = a.pagine_per_lotto
    lotti = {f'pagine_{i // k + 1:02d}': dict(tipo='pagine', pagine=pagine[i:i + k], stato='da fare') for i in range(0, len(pagine), k)}
    ipp = load(man.w('immagini_per_pagina.json'), {})
    imgs = collections.defaultdict(set)
    for p, v in ipp.items():
        for i in v:
            imgs[i['file']].add(int(p))
    files = sorted(imgs, key=lambda f: min(imgs[f]))
    k2 = a.immagini_per_lotto
    for i in range(0, len(files), k2):
        lotti[f'immagini_{i // k2 + 1:02d}'] = dict(tipo='immagini', immagini=[dict(file=f, pagine=sorted(imgs[f])) for f in files[i:i + k2]], stato='da fare')
    man.st['lotti'] = lotti; man.st['campione'] = camp
    save(man.p('stato.json'), man.st)
    for nome, l in lotti.items():
        t = modello('ISTRUZIONI_PAGINE.md' if l['tipo'] == 'pagine' else 'ISTRUZIONI_IMMAGINI.md', man, LOTTO=nome)
        elenco = ', '.join(map(str, l['pagine'])) if l['tipo'] == 'pagine' else '\n' + '\n'.join(f"- `{x['file']}` (pagine {x['pagine']})" for x in l['immagini'])
        t += f'\n\n## Il tuo lotto: `{nome}`\n\n' + (f'Pagine: {elenco}\n' if l['tipo'] == 'pagine' else f'Immagini: {elenco}\n')
        if camp and l['tipo'] == 'pagine':
            t += f'\nPagine di controllo in questo lotto (non segnalate dallo smistamento): {[n for n in l["pagine"] if n in camp]}\n'
        open(man.w('compiti', nome + '.md'), 'w').write(t)
    man.done('compiti', lotti=len(lotti), pagine=len(pagine), campione=camp)
    print(f'{len(lotti)} lotti in {man.w("compiti")}: ' + ', '.join(lotti))


def parole(s):
    s = re.sub(r'<!--.*?-->', ' ', s, flags=re.S); s = re.sub(r'\*\[IMMAGINE: [^\]]*\]\*', ' ', s)
    s = s.replace('’', "'").replace('­', '')
    return collections.Counter(w.lower() for w in re.findall(r"[^\W_]+(?:'[^\W_]+)?", s))


def f_valida(man, a):
    """Controlli sulle consegne. Pagine: file presente, prima riga, segnaposto identici alla bozza, parole
    della bozza conservate (>= soglia; le parole ricucite contano come conservate se la loro unione c'e'),
    log presente. Immagini: una voce per immagine, campi e lunghezza della nota."""
    esiti = {}
    for nome, l in man.st['lotti'].items():
        prob = []
        if l['tipo'] == 'pagine':
            if not os.path.exists(man.w('log', nome + '.md')):
                prob.append('log mancante')
            for n in l['pagine']:
                f = man.w('finale', f'p{n:03d}.md')
                if not os.path.exists(f):
                    prob.append(f'p{n}: manca'); continue
                s = open(f).read(); b = open(man.w('bozza', f'p{n:03d}.md')).read()
                if not s.startswith(f'<!-- pdf p. {n} -->'):
                    prob.append(f'p{n}: prima riga')
                pb = sorted(re.findall(r'\*\[IMMAGINE: [^\]]*\]\*', b)); ps = sorted(re.findall(r'\*\[IMMAGINE: [^\]]*\]\*', s))
                if pb != ps:
                    prob.append(f'p{n}: segnaposto diversi dalla bozza')
                wb, ws = parole(b), parole(s)
                miss = wb - ws
                # una parola 'mancante' spiegata da una ricucitura (pezzo + pezzo = parola presente) non conta
                joined = ''.join(ws.keys())
                miss = {w: c for w, c in miss.items() if not (len(w) <= 12 and w in joined and any(w in x and w != x for x in ws))}
                tot = sum(wb.values())
                cov = 1 - sum(miss.values()) / tot if tot else 1
                if cov < a.soglia:
                    prob.append(f'p{n}: parole della bozza conservate {cov:.3f} (mancano {dict(list(miss.items())[:6])})')
        else:
            nf = man.w('note', nome + '.json')
            note = load(nf, None)
            if note is None:
                prob.append('file note mancante')
            else:
                for x in l['immagini']:
                    v = note.get(x['file'])
                    if not v or not v.get('nota'):
                        prob.append(f"{x['file']}: nota mancante")
                    elif not 3 <= len(v['nota'].split()) <= 25:
                        prob.append(f"{x['file']}: nota di {len(v['nota'].split())} parole")
        l['stato'] = 'OK' if not prob else 'DA RIFARE'
        l['problemi'] = prob
        esiti[nome] = (l['stato'], len(prob))
    save(man.p('stato.json'), man.st)
    for nome, (s_, k) in esiti.items():
        print(f'{nome:14} {s_:10} {k} problemi' + ('' if not k else ': ' + '; '.join(man.st['lotti'][nome]['problemi'][:4])))
    # campione di controllo: quanto la bozza bastava
    camp = man.st.get('campione') or []
    if camp:
        def norm(x): return '\n'.join(l.rstrip() for l in re.sub(r'<!--.*?-->', '', x, flags=re.S).splitlines() if l.strip() not in ('', '>'))
        rs = [difflib.SequenceMatcher(None, norm(open(man.w('bozza', f'p{n:03d}.md')).read()), norm(open(man.w('finale', f'p{n:03d}.md')).read()), autojunk=False).ratio() for n in camp if os.path.exists(man.w('finale', f'p{n:03d}.md'))]
        print(f'campione di controllo: {sum(r >= 0.99 for r in rs)}/{len(rs)} pagine con bozza gia\' sufficiente (>= 0,99)')


def f_assembla(man, a):
    shutil.copy(os.path.join(S, 'assembla.py'), man.p('script'))
    print(run(os.path.join(S, 'assembla.py'), man.r, a.nome or (re.sub(r'\W+', '_', man.cfg['titolo']).strip('_') + '.md')))
    man.done('assembla')


def f_stato(man, a):
    print(json.dumps(man.cfg, ensure_ascii=False))
    for f, v in man.st['fasi'].items():
        print(f'  {f:10} {v}')
    c = collections.Counter(l['stato'] for l in man.st.get('lotti', {}).values())
    print('  lotti:', dict(c))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('fase', choices=['init', 'immagini', 'profilo', 'bozza', 'compiti', 'valida', 'assembla', 'stato', 'auto_classi'])
    ap.add_argument('radice')
    ap.add_argument('--pdf'); ap.add_argument('--titolo'); ap.add_argument('--lingua', default='')
    ap.add_argument('--smistamento', action='store_true'); ap.add_argument('--campione', type=int, default=15)
    ap.add_argument('--seed', type=int, default=11)
    ap.add_argument('--pagine-per-lotto', type=int, default=18); ap.add_argument('--immagini-per-lotto', type=int, default=30)
    ap.add_argument('--soglia', type=float, default=0.99); ap.add_argument('--nome')
    a = ap.parse_args()
    man = Man(a.radice)
    {'init': f_init, 'immagini': f_immagini, 'profilo': f_profilo, 'bozza': f_bozza, 'compiti': f_compiti,
     'valida': f_valida, 'assembla': f_assembla, 'stato': f_stato,
     'auto_classi': lambda m, a: auto_classi(m)}[a.fase](man, a)
