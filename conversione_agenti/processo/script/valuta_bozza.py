"""Banco di prova della bozza su tutti i manuali con pagine rivedute.
Per ogni manuale rigenera la bozza (senza segnaposto immagine) in una cartella temporanea e la
confronta con le pagine rivedute (tolti note, trascrizioni, segnaposto, commenti, righe vuote).
Stampa: pagine confrontate, identiche, >=0.99, <0.95, mediana. Uso: python valuta_bozza.py [etichetta]
"""
import difflib, json, os, re, subprocess, sys, tempfile
P = '/home/an4k4pe/Documenti/ManReader (Copia)/venv/bin/python'
HERE = os.path.dirname(os.path.abspath(__file__))
M = [
    ('Candela', '/home/an4k4pe/Documenti/KDrive/ManualiGdr/Candela Obscura - DP - Core Rulebook (OEF, 2023-11).pdf',
     '/home/an4k4pe/Documenti/ManReader_prova/Candela_Obscura/_lavoro/finale', None),
    ('Vileborn', '/home/an4k4pe/Documenti/ManReader (Copia)/Vil.pdf',
     '/home/an4k4pe/Documenti/ManReader_prova/Vileborn/_lavoro/finale', None),
    ('DrW', '/home/an4k4pe/Documenti/ManReader (Copia)/DrW.pdf',
     '/home/an4k4pe/Documenti/ManReader_prova/DrawSteel/_lavoro/finale', '/home/an4k4pe/Documenti/ManReader_prova/DrawSteel/profilo.json'),
]

def norm(s, final):
    out, skip = [], False
    for l in s.splitlines():
        if final:
            if re.match(r'^\*\[(Illustrazione|Mappa|Documento|Scheda|Simbolo|Oggetto|Immagine)', l):
                skip = False; continue
            if "Testo nell'immagine" in l or l.strip() == '<!-- da render -->':
                skip = True; continue
            if skip and (l.startswith('>') or l.strip()):
                continue
            skip = False
        if re.fullmatch(r'\*\[IMMAGINE: [^\]]*\]\*', l.strip()):
            continue
        l = re.sub(r'<!--.*?-->', '', l).rstrip().rstrip('\\')
        # riquadri: la bozza usa i callout di Obsidian (scelta dell'utente, 28 set 2026), i riveduti il
        # blockquote con titolo in grassetto; si confrontano nella stessa forma
        l = re.sub(r'^> \[!NOTE\] (.+)$', r'> **\1**', l)
        if l.strip() == '> [!NOTE]':
            continue
        if l.strip() in ('', '>'):
            continue
        out.append(l)
    return '\n'.join(out)

if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else 'corrente'
    tot = {}
    solo = os.environ.get('VALUTA_SOLO')
    for name, pdf, fin, prof in M:
        if solo and name != solo:
            continue
        pages = sorted(int(f[1:4]) for f in os.listdir(fin) if re.fullmatch(r'p\d{3}\.md', f))
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, MANREADER_PROFILO=prof or '')
            subprocess.run([P, os.path.join(HERE, 'bozza_testo_v3.py'), pdf, tmp, '/nessuno.json'],
                           capture_output=True, env=env)
            rs, per = [], {}
            for n in pages:
                a = norm(open(os.path.join(tmp, f'p{n:03d}.md')).read(), False)
                b = norm(open(os.path.join(fin, f'p{n:03d}.md')).read(), True)
                rs.append(1.0 if a == b else difflib.SequenceMatcher(None, a, b, autojunk=False).ratio())
                per[n] = round(rs[-1], 4)
        rs.sort()
        tot[name] = dict(pagine=len(rs), identiche=sum(r == 1.0 for r in rs), ok99=sum(r >= 0.99 for r in rs),
                         sotto95=sum(r < 0.95 for r in rs), mediana=round(rs[len(rs) // 2], 3), perpagina=per)
        t = tot[name]
        print(f"{tag:12} {name:9} pagine {t['pagine']:3} | identiche {t['identiche']:3} | >=0.99 {t['ok99']:3} ({t['ok99']/t['pagine']:.0%}) | <0.95 {t['sotto95']:3} | mediana {t['mediana']}")
    json.dump(tot, open(os.path.join(HERE, f'../valutazioni_{tag}.json'), 'w'), indent=1)
