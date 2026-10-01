"""v2: stessa bozza della 02, ma i ruoli non nominano nessun font: si ricavano dal
documento con una prima passata di misure (principio di ManReader: document_heading_
measurements, document_text_recurrence, marcatori di elenco dedotti). Vedi FATTI.

--- docstring della v1, per il resto invariata ---
Bozza Markdown pagina per pagina dal livello testo del PDF (PyMuPDF).

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



import collections


def fam(font):
    return font.split('-')[0].split('+')[-1]


def measure_facts(doc):
    """Prima passata: fatti del documento, nessun nome di font cablato.
    - corpo: (font, dimensione) che porta piu' caratteri; gabbia = estensione delle sue righe
    - arredo di testo: firma (font, dimensione, rotazione) che sta fuori dalla gabbia in almeno
      meta' delle righe e compare su piu' di una pagina (testatine, numeri di pagina)
    - famiglie d'annotazione: famiglie con la maggioranza delle righe ruotate (scrittura a mano)
    - font marcatore: font i cui span sono quasi sempre un solo carattere a inizio riga
    - titoli: dimensioni maggiori del corpo, righe orizzontali, famiglie non d'annotazione;
      livello = rango della dimensione tra quelle presenti su piu' di una pagina
    """
    chars = collections.Counter(); sig_lines = collections.defaultdict(list)
    fam_rot = collections.Counter(); fam_all = collections.Counter()
    font_spans = collections.Counter(); font_marker = collections.Counter()
    size_pages = collections.defaultdict(set)
    for p in doc:
        for b in p.get_text('dict')['blocks']:
            for l in b.get('lines', []):
                sp = [s for s in l['spans'] if s['text'].strip() and s['size'] <= 60]
                if not sp:
                    continue
                for i, s in enumerate(sp):
                    font_spans[s['font']] += 1
                    if i == 0 and len(s['text'].strip()) == 1 and len(sp) > 1:
                        font_marker[s['font']] += 1
                main = max(sp, key=lambda s: len(s['text']))
                if not any(c.isalnum() for s in sp for c in s['text']):
                    continue
                rot = l['dir'] != (1.0, 0.0)
                k = (main['font'], round(main['size'], 1), rot)
                chars[(main['font'], round(main['size'], 1))] += sum(len(s['text']) for s in sp)
                sig_lines[k].append((p.number, l['bbox']))
                fam_all[fam(main['font'])] += 1; fam_rot[fam(main['font'])] += rot
                size_pages[(fam(main['font']), round(main['size']))].add(p.number)
    body_font, body_size = chars.most_common(1)[0][0]
    bl = sig_lines[(body_font, body_size, False)]
    cage = (min(b[0] for _, b in bl), min(b[1] for _, b in bl), max(b[2] for _, b in bl), max(b[3] for _, b in bl))
    outside = lambda b: b[0] >= cage[2] - 1 or b[2] <= cage[0] + 1 or b[1] >= cage[3] - 1 or b[3] <= cage[1] + 1
    furniture = {k for k, v in sig_lines.items()
                 if len({pg for pg, _ in v}) > 1 and sum(outside(b) for _, b in v) >= len(v) / 2}
    hand = {f for f in fam_all if fam_rot[f] > fam_all[f] / 2}
    marker = {f for f in font_spans if font_spans[f] >= 3 and font_marker[f] >= 0.9 * font_spans[f]}
    hsizes = sorted({sz for (f, sz), pgs in size_pages.items()
                     if sz > body_size + 0.5 and f not in hand and len(pgs) > 1}, reverse=True)
    return dict(body_font=body_font, body_size=body_size, body_family=fam(body_font), cage=cage,
                furniture=furniture, hand=hand, marker=marker, heading_sizes=hsizes)


FATTI = None


def heading_level(size):
    hs = FATTI['heading_sizes']
    for i, h in enumerate(hs):
        if size >= h - 0.5:
            return i + 1
    return len(hs)


def line_text(line):
    """Testo della riga con stile inline e spazi ricostruiti dai caratteri."""
    out = []  # (text, bold, italic)
    prev_x1 = None
    for s in line['spans']:
        f = s['font']
        bold = 'Bold' in f
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
        if f in FATTI['marker']:
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
    if (f, round(sz, 1), not horiz) in FATTI['furniture']:
        return 'runner'
    if fam(f) in FATTI['hand']:
        return 'hand'
    if horiz and sz > FATTI['body_size'] + 0.5 and FATTI['heading_sizes']:
        return 'h%d' % min(heading_level(sz), 4)
    if horiz and abs(sz - FATTI['body_size']) < 0.5 and fam(f) != FATTI['body_family'] \
            and len(''.join(c['c'] for s in line['spans'] for c in s['chars'])) < 60:
        return 'boxtitle'
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
                     ]
            if not spans:
                continue
            r = role(spans[0], l)
            if r in ('alt', 'runner'):
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
            elif r == 'h4':
                out.append(f'#### {txt}')
            elif r == 'boxtitle':
                out.append(f'> **{txt}**')
            elif r == 'hand':
                out.append(f'> [manoscritto] {txt}')
            else:
                out.append(('> ' if inbox else '') + txt)
            out.append('>' if inbox and g is not groups[-1] else '')
    return '\n'.join(out)


if __name__ == '__main__':
    PDF, OUT = sys.argv[1], sys.argv[2]
    os.makedirs(OUT, exist_ok=True)
    d = fitz.open(PDF)
    FATTI = measure_facts(d)
    print({k: (sorted(v) if isinstance(v, set) else v) for k, v in FATTI.items()})
    for p in d:
        n = p.number + 1
        open(os.path.join(OUT, f'p{n:03d}.md'), 'w').write(f'<!-- p. {n} -->\n\n' + page_md(p) + '\n')
    print('scritte', d.page_count, 'pagine')
