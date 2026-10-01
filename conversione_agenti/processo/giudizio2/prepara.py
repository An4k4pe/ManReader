"""Pagina del secondo giudizio a vista (vedi CRITERIO.md). Uso: python prepara.py"""
import os, re, json, random, shutil, html
HERE = os.path.dirname(os.path.abspath(__file__))
P = '/home/an4k4pe/Documenti/ManReader_prova'
VAL = lambda t: json.load(open(f'{P}/processo/valutazioni_{t}.json'))['Vileborn']['perpagina']
rnd = random.Random(20260929)
a, b = VAL('v10c_tabelle'), VAL('v11d_ordine')
migliorate = sorted((int(k) for k in a if b[k] > a[k] + 0.0005))
ordine = sorted(rnd.sample(migliorate, 12)) + [8]
def n_titoli(d, n):
    return sum(1 for l in open(f'{HERE}/{d}/p{n:03d}.md') if re.match(r'#{1,6} ', l))
vil_t = sorted(n for n in range(1, 273) if n_titoli('vil_nuova', n) >= 3 and n not in ordine)
can_t = sorted(n for n in range(1, 212) if n_titoli('can_nuova', n) >= 3)
titoli = [('Vileborn', n) for n in sorted(rnd.sample(vil_t, 8))] + [('Candela', n) for n in sorted(rnd.sample(can_t, 3))]
R = {'Vileborn': f'{P}/Vileborn/_lavoro', 'Candela': f'{P}/Candela_Obscura/_lavoro'}
items = [dict(m='Vileborn', n=n, g='ordine', old='vil_ordine_vecchio', new='vil_nuova') for n in ordine]
items += [dict(m=m, n=n, g='titoli', old=('vil' if m == 'Vileborn' else 'can') + '_titoli_vecchi',
               new=('vil' if m == 'Vileborn' else 'can') + '_nuova') for m, n in titoli]
items += [dict(m='Vileborn', n=n, g='mappe e callout', old='vil_ordine_vecchio', new='vil_nuova') for n in (2, 3, 85)]
json.dump(items, open(f'{HERE}/campione.json', 'w'), indent=1)
os.makedirs(f'{HERE}/img', exist_ok=True)
E = lambda p: html.escape(open(p).read()) if os.path.exists(p) else '(nessuna)'
Q = {'ordine': "Ordine di lettura della bozza nuova rispetto alla vecchia",
     'titoli': "Livelli dei titoli della bozza nuova rispetto alla vecchia",
     'mappe e callout': "Bozza nuova rispetto alla vecchia (etichette della mappa tolte, riquadri come callout)"}
cards = []
for k, it in enumerate(items, 1):
    key = f"{it['m'][:3]}{it['n']:03d}{it['g'][0]}"
    img = f"{it['m'][:3]}_p{it['n']:03d}.png"
    shutil.copy(f"{R[it['m']]}/render120/p{it['n']:03d}.png", f'{HERE}/img/{img}')
    f = f"p{it['n']:03d}.md"
    radio = lambda name, vals: ''.join(f'<label><input type="radio" name="{name}{key}" value="{v}"> {v}</label>' for v in vals)
    cards.append(f'''<section><h2>{k}/{len(items)} · {it['m']} pagina PDF {it['n']} · <span class="g">{it['g']}</span></h2>
<div class="row"><div class="col img"><img src="img/{img}"></div>
<div class="col"><h3>Bozza nuova</h3><pre>{E(f"{HERE}/{it['new']}/{f}")}</pre></div>
<div class="col"><h3>Bozza vecchia</h3><pre>{E(f"{HERE}/{it['old']}/{f}")}</pre></div>
<div class="col"><h3>Riveduto dagli agenti</h3><pre>{E(f"{R[it['m']]}/finale/{f}")}</pre></div></div>
<div class="q">{Q[it['g']]}: {radio('c', ('meglio', 'uguale', 'peggio'))}</div>
<div class="q">Bozza nuova: {radio('v', ('corretta', 'difetti minori', 'sbagliata'))}</div>
<div class="q"><input class="nota" data-k="{key}" placeholder="nota (facoltativa)"></div></section>''')
page = '''<!doctype html><html lang="it"><head><meta charset="utf-8"><title>Giudizio bozza 2</title><style>
body{font:14px system-ui;margin:0;padding:16px;background:#f4f4f2;color:#222}
section{background:#fff;border:1px solid #ccc;border-radius:6px;padding:12px;margin-bottom:24px}.g{color:#a33}
.row{display:flex;gap:10px;align-items:flex-start}.col{flex:1;min-width:0}.img{flex:1.1}
img{width:100%;border:1px solid #999;cursor:zoom-in}img.big{position:fixed;inset:0;margin:auto;width:auto;height:98vh;z-index:9;cursor:zoom-out}
pre{white-space:pre-wrap;font:12px ui-monospace,monospace;background:#fafafa;border:1px solid #ddd;padding:6px;max-height:85vh;overflow:auto}
.q{margin-top:8px}.q label{margin-right:14px}.nota{width:60%}#bar{position:sticky;top:0;background:#222;color:#fff;padding:8px;z-index:5;margin:-16px -16px 16px}
button{margin-left:12px}</style></head><body>
<div id="bar">Giudicate: <b id="n">0</b>/''' + str(len(items)) + ''' · i voti restano salvati in questo browser <button id="copia">Copia risultati</button></div>
<p>Il render è la verità; il riveduto è solo un aiuto. Per ogni pagina: la domanda in rosso (ordine, titoli, mappe) confronta nuova e vecchia; poi il giudizio sulla bozza nuova intera. Nella bozza nuova i riquadri sono callout <code>&gt; [!NOTE]</code>, i titoli hanno al massimo tre livelli (decisione registrata in ManReader). Clic sul render per ingrandirlo.</p>
''' + '\n'.join(cards) + '''
<script>
const K='giudizio2_20260929';let st={};try{st=JSON.parse(localStorage.getItem(K)||'{}')}catch(e){}
function save(){try{localStorage.setItem(K,JSON.stringify(st))}catch(e){};document.getElementById('n').textContent=Object.values(st).filter(x=>x.v&&x.c).length}
document.querySelectorAll('input[type=radio]').forEach(r=>{const p=r.name.slice(1),k=r.name[0];if(st[p]&&st[p][k]===r.value)r.checked=true;
 r.onchange=()=>{st[p]=st[p]||{};st[p][k]=r.value;save()}});
document.querySelectorAll('.nota').forEach(t=>{const p=t.dataset.k;if(st[p]&&st[p].n)t.value=st[p].n;t.oninput=()=>{st[p]=st[p]||{};st[p].n=t.value;save()}});
document.querySelectorAll('img').forEach(i=>i.onclick=()=>i.classList.toggle('big'));
document.getElementById('copia').onclick=()=>navigator.clipboard.writeText(JSON.stringify(st,null,1));
save();
</script></body></html>'''
open(f'{HERE}/giudizio.html', 'w').write(page)
print(len(items), 'pagine:', [(i['m'][:3], i['n'], i['g']) for i in items])
