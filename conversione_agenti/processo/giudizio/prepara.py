"""Prepara la pagina di giudizio a vista (vedi CRITERIO.md). Uso: python prepara.py <bozza_nuova> <bozza_vecchia>"""
import sys, os, difflib, random, json, shutil, html
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'script'))
from valuta_bozza import norm
NEW, OLD = sys.argv[1], sys.argv[2]
R = '/home/an4k4pe/Documenti/ManReader_prova/Vileborn/_lavoro'
HERE = os.path.dirname(os.path.abspath(__file__))
def score(d, f, b):
    a = norm(open(os.path.join(d, f)).read(), False)
    return 1.0 if a == b else difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
S = {}
for f in sorted(os.listdir(R + '/finale')):
    if f.startswith('p'):
        b = norm(open(R + '/finale/' + f).read(), True)
        S[f] = (score(OLD, f, b), score(NEW, f, b))
rnd = random.Random(20260928)
better = sorted(f for f, (o, n) in S.items() if n - o > 0.001)
worse = sorted(f for f, (o, n) in S.items() if o - n > 0.001)
rest = [f for f in S if f not in better and f not in worse]
A = rnd.sample(better, min(6, len(better))); B = worse
C = rnd.sample(sorted(f for f in rest if S[f][1] >= 0.99), 10)
D = rnd.sample(sorted(f for f in rest if S[f][1] < 0.95), 5)
items = [(f, 'AB' if f in A or f in B else 'CD') for f in A + B + C + D]
rnd.shuffle(items)
key = {f: g for g, L in (('A', A), ('B', B), ('C', C), ('D', D)) for f in L}
json.dump(dict(gruppi=key, punteggi={f: [round(x, 4) for x in S[f]] for f in key}), open(os.path.join(HERE, 'chiave.json'), 'w'), indent=1)
os.makedirs(os.path.join(HERE, 'img'), exist_ok=True)
E = lambda p: html.escape(open(p).read())
cards = []
for i, (f, kind) in enumerate(items, 1):
    shutil.copy(f'{R}/render120/{f[:-3]}.png', os.path.join(HERE, 'img', f[:-3] + '.png'))
    n = int(f[1:4])
    old = f'<div class="col"><h3>Bozza vecchia</h3><pre>{E(os.path.join(OLD, f))}</pre></div>' if kind == 'AB' else ''
    cmp_ = ('<div class="q">Nuova rispetto alla vecchia: ' + ''.join(
        f'<label><input type="radio" name="c{f}" value="{v}"> {v}</label>' for v in ('meglio', 'uguale', 'peggio')) + '</div>') if kind == 'AB' else ''
    cards.append(f'''<section data-p="{f}"><h2>{i}/{len(items)} · pagina PDF {n}</h2>
<div class="row"><div class="col img"><img src="img/{f[:-3]}.png"></div>
<div class="col"><h3>Bozza nuova</h3><pre>{E(os.path.join(NEW, f))}</pre></div>{old}
<div class="col"><h3>Riveduto dagli agenti</h3><pre>{E(R + '/finale/' + f)}</pre></div></div>
<div class="q">Bozza nuova: ''' + ''.join(f'<label><input type="radio" name="v{f}" value="{v}"> {v}</label>' for v in ('corretta', 'difetti minori', 'sbagliata')) +
f'''</div>{cmp_}<div class="q"><input class="nota" data-p="{f}" placeholder="nota (facoltativa)"></div></section>''')
page = '''<!doctype html><html lang="it"><head><meta charset="utf-8"><title>Giudizio bozza Vileborn</title><style>
body{font:14px system-ui;margin:0;padding:16px;background:#f4f4f2;color:#222}
section{background:#fff;border:1px solid #ccc;border-radius:6px;padding:12px;margin-bottom:24px}
.row{display:flex;gap:10px;align-items:flex-start}.col{flex:1;min-width:0}.img{flex:1.2}
img{width:100%;border:1px solid #999;cursor:zoom-in}img.big{position:fixed;inset:0;margin:auto;width:auto;height:98vh;z-index:9;cursor:zoom-out}
pre{white-space:pre-wrap;font:12px ui-monospace,monospace;background:#fafafa;border:1px solid #ddd;padding:6px;max-height:85vh;overflow:auto}
.q{margin-top:8px}.q label{margin-right:14px}.nota{width:60%}#bar{position:sticky;top:0;background:#222;color:#fff;padding:8px;z-index:5;margin:-16px -16px 16px}
button{margin-left:12px}</style></head><body>
<div id="bar">Giudicate: <b id="n">0</b>/''' + str(len(items)) + ''' · i voti restano salvati in questo browser <button id="copia">Copia risultati</button></div>
<p>Per ogni pagina: il render è la verità. Giudica la <b>bozza nuova</b> come Markdown della pagina (testo, ordine, titoli, tabelle; immagini e note escluse, la bozza non le ha). Il riveduto è solo un aiuto e può essere sbagliato. Clic sul render per ingrandirlo.</p>
''' + '\n'.join(cards) + '''
<script>
const K='giudizio_vil_20260928';let st={};try{st=JSON.parse(localStorage.getItem(K)||'{}')}catch(e){}
function save(){try{localStorage.setItem(K,JSON.stringify(st))}catch(e){};document.getElementById('n').textContent=Object.values(st).filter(x=>x.v).length}
document.querySelectorAll('input[type=radio]').forEach(r=>{const p=r.name.slice(1),k=r.name[0];if(st[p]&&st[p][k]===r.value)r.checked=true;
 r.onchange=()=>{st[p]=st[p]||{};st[p][k]=r.value;save()}});
document.querySelectorAll('.nota').forEach(t=>{const p=t.dataset.p;if(st[p]&&st[p].n)t.value=st[p].n;t.oninput=()=>{st[p]=st[p]||{};st[p].n=t.value;save()}});
document.querySelectorAll('img').forEach(i=>i.onclick=()=>i.classList.toggle('big'));
document.getElementById('copia').onclick=()=>navigator.clipboard.writeText(JSON.stringify(st,null,1));
window.risultati=()=>st;save();
</script></body></html>'''
open(os.path.join(HERE, 'giudizio.html'), 'w').write(page)
print('pagine:', len(items), {g: len(L) for g, L in (('A', A), ('B', B), ('C', C), ('D', D))})
