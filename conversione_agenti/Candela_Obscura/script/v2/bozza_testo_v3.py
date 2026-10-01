"""v3: bozza con i paragrafi ricostruiti a livello di riga e le correzioni meccaniche
che nella fase 1 facevano a mano gli agenti.

Ruoli, spazi e stili vengono da bozza_testo_v2 (ruoli misurati sul documento).
Cambia il montaggio:
- le righe si leggono nell'ordine del content stream, ma il paragrafo non si ferma
  al confine del blocco PyMuPDF: una riga continua il paragrafo se ha lo stesso ruolo,
  scende di al piu' 1,3 volte il corpo e si sovrappone in orizzontale alla riga
  precedente (stessa colonna). E' quello che spezzava voci di elenco e paragrafi
  attorno alle immagini.
- una riga che comincia col marcatore d'elenco apre una voce `- `.
- correzioni meccaniche: niente commenti di blocco; lineetta a fine riga senza spazio
  dopo; trattino morbido (U+00AD) a fine riga ricucito; spazi a larghezza zero tolti;
  marcatori di enfasi vuoti tolti; note a mano come `> *[Nota manoscritta]*`.
Uso: python bozza_testo_v3.py <pdf> <outdir>
"""
import os
import re
import sys

import fitz

sys.path.insert(0, os.path.dirname(__file__))
import bozza_testo_v2 as B  # noqa: E402

PITCH = 1.3  # interlinea massima dentro un paragrafo, in corpi


def page_lines(p):
    out = []
    blocks = p.get_text('rawdict', flags=fitz.TEXT_PRESERVE_WHITESPACE | fitz.TEXT_PRESERVE_LIGATURES)['blocks']
    for bi, b in enumerate(blocks):
        if b['type'] != 0:
            continue
        rows = []
        for l in b['lines']:
            spans = [s for s in l['spans'] if ''.join(c['c'] for c in s['chars']).strip() and s['size'] <= 60]
            if not spans:
                continue
            r = B.role(spans[0], l)
            if r in ('alt', 'runner'):
                continue
            if r == 'body' and any(B.role(s, l) == 'hand' for s in spans):
                r = 'hand'
            l = dict(l, spans=spans)
            # un carattere di controllo a inizio riga (su Candela U+0007 nel corsivo del corpo)
            # e' un marcatore d'elenco: si toglie dallo span e la riga diventa una voce
            first = spans[0]['chars']
            ctrl = bool(first) and ord(first[0]['c']) < 32 and first[0]['c'] not in '\t\n'
            if ctrl:
                spans = [dict(spans[0], chars=first[1:])] + spans[1:]
                spans = [s for s in spans if ''.join(c['c'] for c in s['chars']).strip()]
                if not spans:
                    continue
                l = dict(l, spans=spans)
            ital = all('Italic' in s['font'] for s in spans)
            text = B.styled(B.line_text(l), block_italic=ital).strip()
            if ctrl and not text.startswith('•'):
                text = '• ' + text
            if not text:
                continue
            rows.append(dict(role=r, bbox=l['bbox'], size=spans[0]['size'], text=text, ital=ital, block=bi))
        inbox = any(x['role'] == 'boxtitle' for x in rows)
        for x in rows:
            x['inbox'] = inbox
        out.extend(rows)
    return out


def continues(par, ln):
    last = par['lines'][-1]
    if ln['role'] != par['role'] or ln['inbox'] != par['inbox'] or ln['text'].startswith('•'):
        return False
    if ln['role'] == 'boxtitle':
        return False
    dy = ln['bbox'][1] - last['bbox'][1]
    if not (0 < dy <= PITCH * max(ln['size'], last['size'])):
        return False
    a0, a1, b0, b1 = last['bbox'][0], last['bbox'][2], ln['bbox'][0], ln['bbox'][2]
    overlap = min(a1, b1) - max(a0, b0)
    return overlap > 0.5 * min(a1 - a0, b1 - b0)


def join(txt, t):
    if not txt:
        return t
    if txt.endswith('­'):
        return txt[:-1] + t
    if txt.endswith('-') and len(txt) > 1 and txt[-2].isalpha():
        return txt + t
    if txt.endswith('—'):
        return txt + t
    return txt + ' ' + t


def clean(t):
    t = t.replace('​', '').replace('­ ', '').replace('­', '')
    # due enfasi uguali separate da uno spazio si fondono; mai toccare '** *' (grassetto + corsivo)
    t = re.sub(r'(?<![*])\*\* \*\*(?![*])', ' ', t)
    t = re.sub(r'(?<![*])\* \*(?![*])', ' ', t)
    t = re.sub(r'(?<!\*)\*([.,;:—])\*(?!\*)', r'\1', t)   # enfasi vuota su punteggiatura
    t = re.sub(r'\*\*\*\*', '', t)
    t = re.sub(r'[ \t]+', ' ', t).strip()
    return t


def frames(p):
    """Riquadri disegnati: rettangoli di almeno meta' della gabbia in larghezza e alti
    piu' di due corpi. Il disegno aiuta, non decide: vedi box_groups."""
    c = B.FATTI['cage']; body = B.FATTI['body_size']
    return [g['rect'] for g in p.get_drawings()
            if g['rect'].width >= 0.5 * (c[2] - c[0]) and g['rect'].height > 2 * body
            and g['rect'].width < p.rect.width * 0.95]


def inside(par, rect):
    return all(rect.contains(fitz.Point((ln['bbox'][0] + ln['bbox'][2]) / 2, (ln['bbox'][1] + ln['bbox'][3]) / 2))
               for ln in par['lines'])


def box_groups(p, pars):
    """Un gruppo di paragrafi dentro lo stesso riquadro diventa riquadro solo se il primo
    e' un titolo (titolo di sezione o a corpo di testo): una fascia di tabella non lo e'."""
    for rect in frames(p):
        idx = [i for i, par in enumerate(pars) if inside(par, rect)]
        if len(idx) < 2:
            continue
        first = pars[idx[0]]
        titled = bool(re.fullmatch(r'h[1-6]', first['role']) or first['role'] == 'boxtitle')
        if not titled:
            # riquadro senza titolo solo se i paragrafi stanno in una colonna sola:
            # celle affiancate (fasce di tabella) hanno inizi di riga diversi
            x0s = [pars[i]['lines'][0]['bbox'][0] for i in idx]
            if max(x0s) - min(x0s) > B.FATTI['body_size']:
                continue
        else:
            first['role'] = 'boxtitle'
        for i in idx:
            pars[i]['inbox'] = True
            pars[i]['boxid'] = id(rect)


def page_md(p):
    pars = []
    for ln in page_lines(p):
        if pars and continues(pars[-1], ln):
            pars[-1]['lines'].append(ln)
        else:
            pars.append(dict(role=ln['role'], inbox=ln['inbox'], lines=[ln], boxid=('b', ln['block']) if ln['inbox'] else None))
    box_groups(p, pars)
    out = []
    for k, par in enumerate(pars):
        txt = ''
        for ln in par['lines']:
            txt = join(txt, ln['text'])
        txt = clean(txt)
        if all(ln['ital'] for ln in par['lines']) and par['role'] in ('body', 'boxtitle'):
            txt = f'*{txt}*'
        r = par['role']
        if re.fullmatch(r'h[1-6]', r):
            line = '#' * int(r[1]) + ' ' + txt.replace('**', '')
        elif r == 'boxtitle':
            line = f'> **{txt.replace("**", "")}**'
        elif r == 'hand':
            line = f'> *[Nota manoscritta]* {txt}'
        else:
            if txt.startswith('• '):
                txt = '- ' + txt[2:]
            line = ('> ' if par['inbox'] else '') + txt
        nxt = pars[k + 1] if k + 1 < len(pars) else None
        sep = '>' if par['inbox'] and nxt is not None and nxt['inbox'] and nxt.get('boxid') == par.get('boxid') else ''
        out.append(line)
        out.append(sep)
    return '\n'.join(out)


if __name__ == '__main__':
    PDF, OUT = sys.argv[1], sys.argv[2]
    os.makedirs(OUT, exist_ok=True)
    d = fitz.open(PDF)
    B.FATTI = B.measure_facts(d)
    for p in d:
        n = p.number + 1
        open(os.path.join(OUT, f'p{n:03d}.md'), 'w').write(f'<!-- pdf p. {n} -->\n\n' + page_md(p).strip() + '\n')
    print('scritte', d.page_count, 'pagine')
