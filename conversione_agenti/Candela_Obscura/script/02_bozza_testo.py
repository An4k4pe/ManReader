"""Bozza Markdown pagina per pagina dal livello testo del PDF (PyMuPDF).

Non decide l'ordine di lettura finale: emette i blocchi nell'ordine del
content stream, ciascuno preceduto da un commento con bbox e ruolo, perche'
la revisione successiva (a vista, sui render) lo corregga.

Ruoli dal font (misurati su questo manuale, vedi VERBALE):
  Quelity-Bold >=20 orizzontale      -> titolo capitolo  (#)
  Quelity-Regular 16                 -> sezione          (##)
  MrsEavesOT-Bold 14/13              -> sottosezione     (###)
  MrsEavesOT-Bold 12                 -> titolo di riquadro (box)
  font manoscritti/dattiloscritti    -> nota in-world
Scartati: testatina verticale (Quelity-Bold 10 ruotato), numero di pagina
(Quelity-Bold 14 in basso), testo di corpo > 60 pt (alt-text incorporato),
righe vuote.
Spazi: ricostruiti dai caratteri (rawdict) quando lo stacco orizzontale
supera 0.1 del corpo (lo spazio di VendettaOT e' ~0.175 del corpo, la crenatura < 0.05) e il PDF non ha il glifo spazio.
Uso: python 02_bozza_testo.py <pdf> <outdir>
"""
import fitz, sys, os, re

PDF, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
d = fitz.open(PDF)

HAND = ('Dontheus', 'AntiquarianScribe', 'BakaToo', 'FilmotypeLaCrosse', 'Quentin',
        'P22CezannePro', 'IM_FELL', 'Vaderlands', 'AncientFairen')
TYPE = ('JMHTypewriter',)


def line_text(line):
    """Testo della riga con stile inline e spazi ricostruiti dai caratteri."""
    out = []  # (text, bold, italic)
    prev_x1 = None
    for s in line['spans']:
        f = s['font']
        bold = 'Bold' in f and not f.startswith(('Quelity', 'MrsEaves'))
        ital = 'Italic' in f
        buf = ''
        for ch in s['chars']:
            c = ch['c']
            x0 = ch['bbox'][0]
            if prev_x1 is not None and x0 - prev_x1 > 0.1 * s['size'] and c != ' ' \
                    and not (buf.endswith(' ') or (not buf and out and out[-1][0].endswith(' '))):
                buf += ' '
            buf += c
            prev_x1 = ch['bbox'][2]
        if f.startswith('BodoniOrnaments'):
            # font di ornamenti: '7' (167 volte) e' il punto elenco del manuale, '=' (4) un fregio
            buf = '• '
        out.append((buf, bold, ital))
    # fonde span con lo stesso stile
    merged = []
    for t, b, i in out:
        if merged and merged[-1][1] == b and merged[-1][2] == i:
            merged[-1] = (merged[-1][0] + t, b, i)
        else:
            merged.append((t, b, i))
    return merged


def styled(parts, block_italic=False):
    res = ''
    for t, b, i in parts:
        if not t.strip():
            res += t
            continue
        lead = t[:len(t) - len(t.lstrip())]
        trail = t[len(t.rstrip()):]
        core = t.strip()
        if i and not block_italic:
            core = f'*{core}*'
        if b:
            core = f'**{core}**'
        res += lead + core + trail
    return res


def role(span, line):
    f, sz = span['font'], span['size']
    horiz = line['dir'] == (1.0, 0.0)
    if sz > 60:
        return 'alt'
    if f.startswith('Quelity-Bold') and not horiz and sz < 12:
        return 'runner'
    if f.startswith('Quelity-Bold') and round(sz) == 14 and span['bbox'][1] > 650:
        return 'folio'
    if f.startswith('Quelity-Bold') and sz >= 20 and horiz:
        return 'h1'
    if f.startswith('Quelity-Regular') and round(sz) == 16:
        return 'h2'
    if f.startswith('MrsEavesOT-Bold') and round(sz) in (13, 14) and 'Italic' not in f:
        return 'h3'
    if f.startswith('MrsEavesOT-Bold') and round(sz) == 12:
        return 'boxtitle'
    if f.startswith(HAND):
        return 'hand'
    if f.startswith(TYPE):
        return 'type'
    return 'body'


def page_md(p):
    blocks = p.get_text('rawdict', flags=fitz.TEXT_PRESERVE_WHITESPACE | fitz.TEXT_PRESERVE_LIGATURES)['blocks']
    out = []
    for b in blocks:
        if b['type'] != 0:
            continue
        lines = []
        for l in b['lines']:
            # lo span alt-text (corpo > 60) puo' stare in mezzo a una riga di testo normale:
            # si filtra span per span, non solo dal primo (correzione dopo p. 195)
            spans = [s for s in l['spans'] if ''.join(c['c'] for c in s['chars']).strip() and s['size'] <= 60
                     and not (s['font'].startswith('Quelity-Bold') and round(s['size']) == 14 and s['bbox'][1] > 650)]
            if not spans:
                continue
            r = role(spans[0], l)
            if r in ('alt', 'runner', 'folio'):
                continue
            if r == 'body' and any(role(s, l) == 'hand' for s in spans):
                r = 'hand'
            l = dict(l, spans=spans)
            lines.append((r, l))
        if not lines:
            continue
        # raggruppa righe consecutive dello stesso ruolo; paragrafi per salto verticale
        groups = []
        for r, l in lines:
            y = l['bbox'][1]
            size = l['spans'][0]['size']
            if groups and groups[-1]['role'] == r and y - groups[-1]['last_y'] < 1.35 * size \
                    and y >= groups[-1]['last_y'] - 2:
                groups[-1]['lines'].append(l)
            else:
                groups.append(dict(role=r, lines=[l]))
            groups[-1]['last_y'] = y
        bb = [round(v) for v in b['bbox']]
        rot = '' if b['lines'][0]['dir'] == (1.0, 0.0) else ' ruotato'
        out.append(f'<!-- blocco {bb}{rot} -->')
        inbox = any(g['role'] == 'boxtitle' for g in groups)
        for g in groups:
            r = g['role']
            all_ital = all('Italic' in s['font'] for l in g['lines'] for s in l['spans'])
            texts = [styled(line_text(l), block_italic=all_ital).strip() for l in g['lines']]
            txt = ''
            for t in texts:
                if not txt:
                    txt = t
                elif txt.endswith('-') and len(txt) > 1 and txt[-2].isalpha():
                    txt += t  # a capo dopo trattino di composto: il trattino resta
                else:
                    txt += ' ' + t
            txt = re.sub(r'\*\* \*\*|\* \*', ' ', txt)
            txt = re.sub(r'\*\*\*\*|(?<!\*)\*\*(?!\*)(?=\*\*)', '', txt)
            txt = re.sub(r'[ \t]+', ' ', txt).strip()
            if all_ital and r in ('body', 'boxtitle'):
                txt = f'*{txt}*'
            if r == 'h1':
                out.append(f'# {txt}')
            elif r == 'h2':
                out.append(f'## {txt}')
            elif r == 'h3':
                out.append(f'### {txt}')
            elif r == 'boxtitle':
                out.append(f'> **{txt}**')
            elif r == 'hand':
                out.append(f'> [manoscritto] {txt}')
            elif r == 'type':
                out.append(f'> [dattiloscritto] {txt}')
            else:
                out.append(('> ' if inbox else '') + txt)
            out.append('>' if inbox and g is not groups[-1] else '')
    return '\n'.join(out)


for p in d:
    n = p.number + 1
    open(os.path.join(OUT, f'p{n:03d}.md'), 'w').write(f'<!-- p. {n} -->\n\n' + page_md(p) + '\n')
print('scritte', d.page_count, 'pagine')
