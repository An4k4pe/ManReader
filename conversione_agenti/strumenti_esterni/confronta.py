"""Misure A e B (vedi CRITERIO.md) per bozza, marker, docling sulle pagine di campione.json."""
import json, re, sys, difflib, glob, os, statistics as st
sys.path.insert(0, '../processo/script'); from valuta_bozza import norm
FIN = {'Candela': '../Candela_Obscura/_lavoro/finale', 'Vileborn': '../Vileborn/_lavoro/finale', 'DrW': '../DrawSteel/_lavoro/finale'}
def tool_text(tool, m, n):
    if tool == 'bozza': p = f'out_bozza/{m}/p{n:03d}.md'
    elif tool == 'mineru': p = f'out_mineru/{m}_p{n:03d}.md'
    else:
        g = glob.glob(f'out_{tool}/{m}_p{n:03d}/*.md'); p = g[0] if g else None
    return open(p).read() if p and os.path.exists(p) else None
def strip_img(s):  # solo i link a immagini, e i marcatori di pagina/span di marker
    s = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', s); s = re.sub(r'<img[^>]*>', '', s); s = re.sub(r'</?div[^>]*>', '', s)
    s = re.sub(r'<table.*?</table>', lambda t: '\n'.join('| ' + ' | '.join(re.sub('<[^>]+>', '', c).strip() for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', r)) + ' |' for r in re.findall(r'<tr.*?</tr>', t.group(0), re.S)), s, flags=re.S); s = re.sub(r'<span id="[^"]*"></span>', '', s)
    return s.replace('<!-- image -->', '')
def words(s, final):
    s = norm(s, final).replace('’', "'").replace('&#x27;', "'")
    s = re.sub(r'<[^>]+>', ' ', s); s = re.sub(r'[#*_>|`\[\]\-–—:]+', ' ', s)
    return re.findall(r"\w+(?:['’]\w+)?", s.lower())
def ratio(a, b): return 1.0 if a == b else difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
import fitz
sel = json.load(open('campione.json')); res = {}; INV = {}
for m, g in sel.items():
    for grp in ('difficili', 'facili'):
        for n in g[grp]:
            ref = open(f'{FIN[m]}/p{n:03d}.md').read()
            for tool in ('bozza', 'marker', 'docling', 'mineru', 'paddle', 'pymupdf4llm', 'odl', 'liteparse'):
                t = tool_text(tool, m, n)
                if t is None: continue
                t = strip_img(t)
                A = ratio(norm(t, False), norm(ref, True)); B = ratio(words(t, False), words(ref, True))
                pw = set(re.findall(r"\w+(?:['’]\w+)?", fitz.open(f'pagine/{m}_p{n:03d}.pdf')[0].get_text().lower().replace('’', "'"))) | set(words(ref, True))
                tw = words(t, False); inv = sum(w not in pw for w in tw)
                INV.setdefault(tool, [0, 0]); INV[tool][0] += inv; INV[tool][1] += len(tw)
                res.setdefault(tool, {}).setdefault(m, {}).setdefault(grp, {})[n] = (round(A, 3), round(B, 3))
json.dump(res, open('risultati.json', 'w'), indent=1)
print(f"{'':9}{'':10}" + ''.join(f'{t:>19}' for t in res))
for m in sel:
    for grp in ('difficili', 'facili'):
        row = f'{m:9}{grp:10}'
        for tool in res:
            v = res[tool].get(m, {}).get(grp, {})
            row += f"{'A %.3f B %.3f' % (st.median(x[0] for x in v.values()), st.median(x[1] for x in v.values())) if v else '-':>19}"
        print(row)
print('parole assenti da PDF e riveduta:', {t: f'{a}/{b} = {a/b:.2%}' for t, (a, b) in INV.items()})
