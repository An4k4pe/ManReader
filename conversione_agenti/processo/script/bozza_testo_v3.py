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
        nb = sum(1 for l in b['lines'] if any(''.join(c['c'] for c in s['chars']).strip() for s in l['spans']))
        for l in b['lines']:
            l['_block_lines'] = nb
            spans = [s for s in l['spans'] if ''.join(c['c'] for c in s['chars']).strip() and s['size'] <= 60]
            if not spans:
                continue
            # il ruolo viene dal primo span che non e' un glifo (Draw Steel: l'icona della distanza apre la riga)
            lead = next((sp for sp in spans if sp['font'] not in B.FATTI['marker']), spans[0])
            r = B.role(lead, l)
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
            rows.append(dict(role=r, bbox=l['bbox'], size=spans[0]['size'], text=text, ital=ital, block=bi,
                             font0=lead['font']))
        inbox = any(x['role'] == 'boxtitle' for x in rows)
        for x in rows:
            x['inbox'] = inbox
        out.extend(rows)
    return out


LABEL = re.compile(r'^\*\*[^*]{1,40}(:\*\*|\*{2,3}:)')   # anche '**Vileborn***:' (grassetto + corsivo)


def continues(par, ln):
    last = par['lines'][-1]
    # 'Keywords: …', 'Specialty: …': una riga che comincia con un'etichetta in grassetto apre un paragrafo
    if LABEL.match(ln['text']):
        return False
    if ln['role'] != par['role'] or ln['inbox'] != par['inbox'] or ln['text'].startswith('•'):
        return False
    if ln['role'] == 'boxtitle':
        return False
    # (provata e tolta il 28 set: la regola dei blocchi di ManReader, Criterio_RotturaParagrafo_v2, qui e'
    # neutra o peggiora: Candela 171->167/170, Vileborn 178->175/176 sul banco di prova)
    # rientro di prima riga: comincia tra 0,6 e 4 corpi piu' a destra della riga precedente E la riga dopo
    # torna al margine della precedente (ln['_next_x0'], impostato da page_md) -> capoverso nuovo
    ind = ln['bbox'][0] - last['bbox'][0]
    nx = ln.get('_next_x0')
    if B.FATTI.get('indent_style') and 0.6 * ln['size'] <= ind <= 4 * ln['size'] and nx is not None and abs(nx - last['bbox'][0]) <= 0.3 * ln['size']:
        return False
    dy = ln['bbox'][1] - last['bbox'][1]
    # interlinea misurata sul documento (v2: prima era 1,3 fisso e su Vileborn, a 1,38, spezzava ogni riga)
    if not (0 < dy <= max(1.3, 1.15 * B.FATTI['pitch_ratio']) * max(ln['size'], last['size'])):
        return False
    a0, a1, b0, b1 = last['bbox'][0], last['bbox'][2], ln['bbox'][0], ln['bbox'][2]
    overlap = min(a1, b1) - max(a0, b0)
    return overlap > 0.5 * min(a1 - a0, b1 - b0)


def join(txt, t):
    if not txt:
        return t
    # trattino di fine riga chiuso da un'enfasi ('visibil-**' + '**mente'): si sposta l'enfasi prima
    m = re.search(r'([^\W\d_])-(\*+)$', txt)
    if m:
        txt = txt[:m.start() + 1] + m.group(2) + '-'
    if txt.endswith('­'):
        return txt[:-1] + t
    if txt.endswith('-') and len(txt) > 1 and txt[-2].isalpha():
        # a capo con trattino: e' sillabazione se la parola intera compare nel documento
        a = re.search(r'([^\W\d_]+)-$', txt); b = re.match(r'([^\W\d_]+)', t)
        V = B.FATTI.get('vocab', {})
        if a and b and V.get((a.group(1) + b.group(1)).lower(), 0) > 0:
            return txt[:-1] + t
        # composto vero ('citta'-fortezza') solo se entrambi i pezzi sono parole di almeno 3 lettere
        if a and b and b.group(1)[0].islower() and not (len(a.group(1)) >= 3 and len(b.group(1)) >= 3
                                                      and V.get(a.group(1).lower(), 0) and V.get(b.group(1).lower(), 0)):
            return txt[:-1] + t
        return txt + t
    if txt.endswith('—'):
        return txt + t
    return txt + ' ' + t


def vocab_join(t):
    """Ricuce 'e- saurimento' e 'Vi leborn': si uniscono due pezzi solo se la parola intera
    compare nel documento e, per lo spazio, il secondo pezzo non compare mai da solo."""
    V = B.FATTI.get('vocab', {})
    # 'x- y' tra minuscole: residuo di sillabazione (le lineette vere del testo sono '–'/'—');
    # con maiuscola dopo si unisce solo se la parola intera e' nel documento
    def hy(m):
        w = m.group(1) + m.group(2)
        return w if (m.group(2)[0].islower() or V.get(w.lower(), 0) > 0) else m.group(0)
    t = re.sub(r'([^\W\d_]+)- ([^\W\d_]+)', hy, t)
    # la stessa sillabazione con l'enfasi chiusa e riaperta in mezzo: '**Vile**- **born**';
    # qui si chiede sempre la parola intera nel documento
    def hye(m):
        w = m.group(1) + m.group(3)
        return w if V.get(w.lower(), 0) > 0 else m.group(0)
    t = re.sub(r'([^\W\d_]+)(\*{1,3})- ?\2([^\W\d_]+)', hye, t)
    def sp(m):
        a, b = m.group(1), m.group(2)
        ab = V.get((a + b).lower(), 0)
        # un pezzo raro rispetto alla parola intera e' un frammento ('Ambienta zione'): conta il
        # meno frequente dei due, perche' i frammenti ricorrono dove la parola si spezza
        rare = min(V.get(a.lower(), 0), V.get(b.lower(), 0))
        if len(b) >= 2 and ab >= 2 and (rare == 0 or (ab >= 5 * rare and rare <= 20)):
            return a + b
        return m.group(0)
    return re.sub(r'(?<![^\W\d_])([^\W\d_]+) ([^\W\d_]+)(?![^\W\d_])', sp, t)


def clean(t):
    t = vocab_join(t)
    t = t.replace('​', '').replace('­ ', '').replace('­', '')
    # due enfasi uguali separate da uno spazio si fondono; mai toccare '** *' (grassetto + corsivo)
    t = re.sub(r'(?<![*])\*\* \*\*(?![*])', ' ', t)
    t = re.sub(r'(?<![*])\* \*(?![*])', ' ', t)
    t = re.sub(r'(?<!\*)\*([.,;:—])\*(?!\*)', r'\1', t)   # enfasi vuota su punteggiatura
    t = re.sub(r'\*\*\*\*', '', t)
    t = re.sub(r'[ \t]+', ' ', t).strip()
    return vocab_join(t)   # di nuovo: la fusione delle enfasi puo' creare 'e- saurimento'


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


IMMAGINI = {}   # pagina -> [{'file','bbox'}], impostato dal chiamante
TITOLI = None   # {dimensione: livello} dalla politica per fascia di ManReader, impostato dal chiamante


def margin_numbers(pars):
    """Numero isolato a margine in font da titolo (anno di una cronologia, Vil p. 19) alla stessa altezza dell'inizio di un
    paragrafo di testo alla sua destra: diventa l'inizio di quel paragrafo, in grassetto, invece di un
    titolo a se'. Un numero accanto a un titolo resta a postprocess ('#### 1' + '#### NOME')."""
    body = B.FATTI['body_size']
    drop = set()
    for i, par in enumerate(pars):
        t = ' '.join(l['text'] for l in par['lines']).replace('*', '').strip()
        # solo i numeri che uscirebbero come titoli: quelli nel testo sono celle di tabella (d6)
        if len(par['lines']) != 1 or not re.fullmatch(r'\d{1,4}', t) or not re.fullmatch(r'h[1-6]', par['role']):
            continue
        a = par['lines'][0]['bbox']
        # il vicino piu' prossimo a destra, di qualunque ruolo: si unisce solo se e' testo
        tgt = [q for q in pars if q is not par and q['lines'][0]['bbox'][0] > a[2]
               and abs(q['lines'][0]['bbox'][1] - a[1]) <= 0.5 * body]
        q = min(tgt, key=lambda q: q['lines'][0]['bbox'][0]) if tgt else None
        if q is not None and q['role'] == 'body':
            q['lines'][0] = dict(q['lines'][0], text=f'**{t}** ' + q['lines'][0]['text'])
            drop.add(i)
    return [par for i, par in enumerate(pars) if i not in drop]


def attach_bullets(pars):
    """Pallino su una riga a parte (Vileborn: 'h' di NelsonOrnaments allineato alla riga di testo):
    si unisce al paragrafo che comincia alla sua stessa altezza e alla sua destra; se non c'e',
    al paragrafo seguente purche' cominci entro un'interlinea e mezza; altrimenti si scarta."""
    body = B.FATTI['body_size']
    solo = lambda par: ''.join(l['text'] for l in par['lines']).strip() == '•'
    keep = [par for par in pars if not solo(par)]
    for i, b in enumerate(pars):
        if not solo(b):
            continue
        by, bx = b['lines'][0]['bbox'][1], b['lines'][0]['bbox'][2]
        cands = [t for t in keep if abs(t['lines'][0]['bbox'][1] - by) <= 0.5 * body and t['lines'][0]['bbox'][0] >= bx - 1]
        t = min(cands, key=lambda t: t['lines'][0]['bbox'][0]) if cands else None
        if t is None and i + 1 < len(pars) and not solo(pars[i + 1]) and \
                0 <= pars[i + 1]['lines'][0]['bbox'][1] - by <= 1.5 * B.FATTI['pitch_ratio'] * body:
            t = pars[i + 1]
        if t is not None and not t['lines'][0]['text'].startswith('•'):
            t['lines'][0] = dict(t['lines'][0], text='• ' + t['lines'][0]['text'])
            if re.fullmatch(r'h[1-6]', t['role']):
                t['role'] = 'body'
    return keep


def tables(pars):
    """Celle consecutive che cominciano alla stessa altezza formano una riga; almeno 3 righe con lo
    stesso numero di celle (>= 2) e colonne allineate (scarto <= 2 corpi) formano una tabella GFM.
    La prima riga fa da intestazione. Le celle restano col loro testo."""
    body = B.FATTI['body_size']
    y0 = lambda par: par['lines'][0]['bbox'][1]
    x0 = lambda par: par['lines'][0]['bbox'][0]

    def vover(a, b):
        ay0, ay1 = a['lines'][0]['bbox'][1], a['lines'][-1]['bbox'][3]
        by0, by1 = b['lines'][0]['bbox'][1], b['lines'][-1]['bbox'][3]
        return min(ay1, by1) - max(ay0, by0) > 0.3 * body

    def overlap(a, b):
        # stessa colonna: le estensioni orizzontali delle due celle si sovrappongono
        ax0, ax1 = min(l['bbox'][0] for l in a['lines']), max(l['bbox'][2] for l in a['lines'])
        bx0, bx1 = min(l['bbox'][0] for l in b['lines']), max(l['bbox'][2] for l in b['lines'])
        return min(ax1, bx1) - max(ax0, bx0) > 0
    rows, cur = [], []
    for i, par in enumerate(pars):
        # stessa riga di tabella: estensioni verticali sovrapposte (celle centrate in verticale, Draw Steel)
        # e cella a destra della precedente
        if par['role'] in ('body', 'boxtitle') and cur and vover(par, pars[cur[-1]]) \
                and x0(par) > x0(pars[cur[-1]]) + body:
            cur.append(i)
        else:
            if cur:
                rows.append(cur)
            cur = [i] if par['role'] in ('body', 'boxtitle') else []
            if not cur:
                rows.append([i])
    if cur:
        rows.append(cur)
    out, k = [], 0
    while k < len(rows):
        r = rows[k]
        run = [r]
        if len(r) >= 2:
            j = k + 1
            while j < len(rows) and len(rows[j]) == len(r) and rows[j][0] == run[-1][-1] + 1 and \
                    all(overlap(pars[rows[j][c]], pars[r[c]]) for c in range(len(r))):
                run.append(rows[j]); j += 1
        if len(run) >= 3 or (len(run) == 2 and len(run[0]) >= 3):
            def cell(i):
                t = ''
                for ln in pars[i]['lines']:
                    t = join(t, ln['text'])
                t = clean(t)
                # sequenze di tre o piu' caratteri singoli separati da spazi ('D 1 2'): spaziatura, si ricompone
                t = re.sub(r'(?<!\S)(?:\S ){2,}\S(?!\S)', lambda m: m.group(0).replace(' ', ''), t)
                t = re.sub(r'(?<!\S)([A-Za-z]) °', r'\1°', t)
                return t.replace('|', '\\|')
            nc = len(run[0])
            colx = [(min(min(l['bbox'][0] for l in pars[rr[c]]['lines']) for rr in run),
                     max(max(l['bbox'][2] for l in pars[rr[c]]['lines']) for rr in run)) for c in range(nc)]
            top = y0(pars[run[0][0]])
            # intestazione fuori dalla regione (come repair_region_y di ManReader): gli ultimi nc
            # paragrafi di una riga, appena sopra, ognuno dentro una colonna diversa (da 2 a nc:
            # la colonna dei numeri spesso non ha intestazione)
            head = None
            prev = []
            for q in reversed(out[-nc:]):
                if q.get('role') == 'table' or (prev and abs(y0(q) - y0(prev[0])) > body):
                    break
                prev.insert(0, q)
            if len(prev) < 2 and nc > 1:
                prev = []
            if prev and all(q.get('role') != 'table' and len(q['lines']) <= 2 for q in prev) and \
                    all(0 < top - q['lines'][-1]['bbox'][3] <= 2 * body for q in prev[-1:]) and \
                    max(y0(q) for q in prev) - min(y0(q) for q in prev) <= body:
                cols = []
                for q in prev:
                    qx0, qx1 = q['lines'][0]['bbox'][0], max(l['bbox'][2] for l in q['lines'])
                    cols.append(next((c for c in range(nc) if min(qx1, colx[c][1]) - max(qx0, colx[c][0]) > 0), None))
                if None not in cols and len(set(cols)) == len(prev):
                    head = ['' for _ in range(nc)]
                    for q, c in zip(prev, cols):
                        t = ''
                        for ln in q['lines']:
                            t = join(t, ln['text'])
                        head[c] = clean(t).replace('**', '').replace('|', '\\|')
                    del out[-len(prev):]
            body_rows = run
            if head is None:
                # la prima riga e' intestazione solo se si distingue dalle altre (grassetto, o tutta
                # maiuscola: le schede di Vileborn)
                caps = lambda t: bool(re.search(r'[^\W\d_]', t)) and t == t.upper()
                bold = lambda rr: all(cell(i).startswith('**') for i in rr)
                upper = lambda rr: all(caps(cell(i).replace('*', '')) for i in rr)
                if (bold(run[0]) and not bold(run[1])) or (upper(run[0]) and not upper(run[1])):
                    head, body_rows = [cell(i) for i in run[0]], run[1:]
                else:
                    head = ['' for _ in range(nc)]
            # didascalia: un paragrafo breve di testo appena sopra, senza punteggiatura finale
            if out and out[-1].get('role') == 'body' and not out[-1]['inbox'] and len(out[-1]['lines']) == 1:
                cap = out[-1]['lines'][0]['text'].replace('*', '').strip()
                if 0 < len(cap.split()) <= 6 and not re.search(r'[.:;,!?]$', cap):
                    out[-1] = dict(out[-1], role='h4')
            lines = ['| ' + ' | '.join(head) + ' |', '|' + '---|' * nc]
            lines += ['| ' + ' | '.join(cell(i) for i in rr) + ' |' for rr in body_rows]
            first = pars[run[0][0]]
            out.append(dict(role='table', inbox=False, lines=first['lines'], boxid=None, rendered='\n'.join(lines)))
            k += len(run)
        else:
            out.extend(pars[i] for i in r)
            k += 1
    return out


def reading_order(p, lines):
    """Ordine di lettura: la sorgente, corretta dove ManReader trova colonne lette nell'ordine sbagliato.

    Da ManReader (column_band + ordinatore ad albero, vedi ordine_manreader.py) si prendono le bande,
    i loro corridoi e il rango di ogni primitiva; l'ordine di base resta quello della sorgente, perche'
    fuori dalle bande l'ordinatore di ManReader e' geometrico e spezza gli elenchi (Vil p. 15: il
    pallino sta mezzo punto sotto la sua riga).
    Una banda si riordina, colonna per colonna da sinistra a destra, solo se nella sorgente ogni sua
    colonna e' contigua (Vil pp. 19, 43: tutta la colonna laterale, poi tutto il testo). Se le colonne
    si alternano, l'impaginatore le ha gia' messe in ordine di lettura per righe (voci a due parti,
    Vil p. 75; tabelle, p. 167) e si tiene la sorgente. Dentro una colonna riordinata vale il rango di
    ManReader, ma di due righe alla stessa altezza viene prima quella piu' a sinistra (pallino
    d'elenco, anno a margine di una cronologia)."""
    import ordine_manreader
    ranks, tree = ordine_manreader.primitive_ranks(p)
    rank, last = [], -1.0
    for ln in lines:
        x0, y0, x1, y1 = ln['bbox']
        r = [k for (a, b, c, d), k in ranks
             if x0 - 1 <= (a + c) / 2 <= x1 + 1 and y0 - 1 <= (b + d) / 2 <= y1 + 1]
        last = min(r) if r else last + 1e-3
        rank.append(last)
    keys = [float(i) for i in range(len(lines))]
    cx = lambda ln: (ln['bbox'][0] + ln['bbox'][2]) / 2
    cy = lambda ln: (ln['bbox'][1] + ln['bbox'][3]) / 2
    bands = []
    for band in tree:
        gut = sorted(tuple(map(float, g.split('-'))) for g in str(band['gutter_x_intervals']).split())
        if not gut:
            continue
        bx0, by0, bx1, by1 = (float(band[k]) for k in ('x0', 'y0', 'x1', 'y1'))
        idx = [i for i, ln in enumerate(lines) if bx0 <= cx(ln) < bx1 and by0 <= cy(ln) < by1]
        col = {i: sum(cx(lines[i]) >= g[0] for g in gut) for i in idx}
        seq = [col[i] for i in idx]
        runs = sum(1 for k in range(len(seq)) if k == 0 or seq[k] != seq[k - 1])
        bands.append((int(band['depth']), idx, col, runs == len(set(seq)) and runs >= 2))
    # una banda intrecciata nella sorgente (tabella, voci a due parti) e' un blocco: tiene l'ordine
    # della sorgente e prende il rango piu' basso delle sue righe (le piu' profonde prima)
    for _, idx, _, contiguous in sorted(bands, key=lambda b: -b[0]):
        if idx and not contiguous:
            base = min(rank[i] for i in idx)
            for n, i in enumerate(sorted(idx)):
                rank[i] = base + n * 1e-6
    for _, idx, col, contiguous in sorted(bands, key=lambda b: b[0]):   # le piu' profonde vincono
        if not contiguous:
            continue
        order = sorted(idx, key=lambda i: (col[i], rank[i]))
        for j in range(len(order) - 1):
            u, v = lines[order[j]]['bbox'], lines[order[j + 1]]['bbox']
            ov = min(u[3], v[3]) - max(u[1], v[1])
            if col[order[j]] == col[order[j + 1]] and ov > 0.5 * min(u[3] - u[1], v[3] - v[1]) and v[0] < u[0]:
                order[j], order[j + 1] = order[j + 1], order[j]
        base = min(keys[i] for i in idx)
        for n, i in enumerate(order):
            keys[i] = base + n * 1e-6
    return [ln for _, _, ln in sorted(zip(keys, range(len(lines)), lines))]


def drop_map_labels(pno, lines):
    """Le etichette di una mappa si tolgono con la mappa: senza di essa non servono (decisione
    dell'utente, 28 set 2026). Che un'immagine sia una mappa lo decide l'agente degli asset
    (`mappe` in classi_immagini.json, riportato da 03 come `mappa` in immagini_per_pagina.json):
    la geometria e la lunghezza delle righe non separano le etichette dai titoli stampati sopra
    un'illustrazione (Vil pp. 1, 60, 95: provato e scartato lo stesso giorno)."""
    boxes = [im['bbox'] for im in IMMAGINI.get(pno, []) if im.get('mappa')]
    inside = lambda ln, b: b[0] <= (ln['bbox'][0] + ln['bbox'][2]) / 2 <= b[2] and b[1] <= (ln['bbox'][1] + ln['bbox'][3]) / 2 <= b[3]
    return [ln for ln in lines if not any(inside(ln, b) for b in boxes)]


def page_md(p):
    pno = p.number + 1
    pars = []
    lines = drop_map_labels(pno, page_lines(p))
    if os.environ.get('MANREADER_ORDINE', '1') != '0':
        lines = reading_order(p, lines)
    for i, ln in enumerate(lines):
        ln['_next_x0'] = lines[i + 1]['bbox'][0] if i + 1 < len(lines) and lines[i + 1]['role'] == ln['role'] else None
    for ln in lines:
        if pars and continues(pars[-1], ln):
            pars[-1]['lines'].append(ln)
        else:
            pars.append(dict(role=ln['role'], inbox=ln['inbox'], lines=[ln], boxid=('b', ln['block']) if ln['inbox'] else None))
    box_groups(p, pars)
    # (provata e tolta il 28 set: riquadro dedotto dal font valido solo se box_groups trova il disegno;
    # sulle Origini di Vileborn il pannello di fondo lo conferma lo stesso, e Candela perde 2 pagine)
    pars = attach_bullets(pars)
    pars = margin_numbers(pars)
    pars = tables(pars)
    out = []
    # segnaposto delle immagini di contenuto: prima del primo paragrafo (in ordine di flusso) che
    # comincia sotto il bordo superiore dell'immagine; se nessuno, in fondo alla pagina
    pend = sorted({i['file']: i for i in IMMAGINI.get(pno, [])}.values(), key=lambda i: i['bbox'][1])
    for k, par in enumerate(pars):
        y0 = par['lines'][0]['bbox'][1]
        while pend and y0 >= pend[0]['bbox'][1]:
            out.append(f"*[IMMAGINE: {pend.pop(0)['file']}]*"); out.append('')
        if par['role'] == 'table':
            out.append(par['rendered']); out.append('')
            continue
        txt = ''
        for ln in par['lines']:
            txt = join(txt, ln['text'])
        txt = clean(txt)
        if all(ln['ital'] for ln in par['lines']) and par['role'] in ('body', 'boxtitle'):
            txt = f'*{txt}*'
        r = par['role']
        if TITOLI is not None and re.fullmatch(r'h[1-6]', r):
            # livello dalla fascia di ManReader, uguale su tutto il documento; fuori fascia (corpo del
            # testo in font di titolazione, dimensioni su meno di tre pagine) il terzo livello: il tetto a
            # tre accorpa, non scarta. Niente eccezione dei segnalibri: e' cio' che rendeva i livelli
            # diversi da pagina a pagina.
            r = 'h%d' % TITOLI.get(round(par['lines'][0]['size'], 1), 3)
        # un titolo che coincide con un segnalibro del PDF (stessa pagina, +-1) prende il livello del segnalibro
        elif re.fullmatch(r'h[1-6]', r):
            key = re.sub(r'[*_]', '', re.sub(r'\s+', ' ', txt)).strip().lower()
            lv = [l for t, pg, l in B.FATTI.get('toc', ()) if t == key and abs(pg - pno) <= 1]
            if lv:
                r = 'h%d' % min(lv[0], 6)
        # riquadri come callout di Obsidian, nella forma di ManReader (markdown_builder._render_callout):
        # '> [!NOTE] TITOLO', poi il corpo citato; un titolo dentro il riquadro resta nel riquadro
        # (prima usciva senza '>' e lo spezzava: Vil p. 85)
        prv = pars[k - 1] if k > 0 else None
        opens = par['inbox'] and not (prv is not None and prv['inbox'] and prv.get('boxid') == par.get('boxid'))
        if re.fullmatch(r'h[1-6]', r):
            line = ('> ' if par['inbox'] and not opens else '') + '#' * int(r[1]) + ' ' + txt.replace('**', '')
            if opens:
                line = f'> [!NOTE] {txt.replace("**", "")}'
        elif r == 'boxtitle':
            line = f'> [!NOTE] {txt.replace("**", "")}'
        elif r == 'hand':
            line = f'> *[Nota manoscritta]* {txt}'
        else:
            if txt.startswith('• '):
                txt = '- ' + txt[2:]
            line = ('> ' if par['inbox'] else '') + txt
            if opens:
                out.append('> [!NOTE]')
                out.append('>')
        nxt = pars[k + 1] if k + 1 < len(pars) else None
        sep = '>' if par['inbox'] and nxt is not None and nxt['inbox'] and nxt.get('boxid') == par.get('boxid') else ''
        out.append(line)
        out.append(sep)
    for i in pend:
        out.append(f"*[IMMAGINE: {i['file']}]*"); out.append('')
    return '\n'.join(postprocess(out))


def postprocess(out):
    """Etichetta sopra un titolo '#' -> grassetto; numero isolato come titolo + titolo -> 'N. TITOLO'."""
    L = [l for l in out]
    nz = [i for i, l in enumerate(L) if l.strip() and l.strip() != '>']
    for a, b in zip(nz, nz[1:]):
        la, lb = L[a], L[b]
        ma = re.match(r'^(#{2,6}) (.+)$', la)
        if ma and re.match(r'^# ', lb) and len(ma.group(2)) <= 40:
            L[a] = f'**{ma.group(2)}**'
        mn = re.match(r'^#{2,6} (\d{1,3})\.?$', la)
        mb = re.match(r'^(#{2,6}) (.+)$', lb)
        if mn and mb:
            L[b] = f'{mb.group(1)} {mn.group(1)}. {mb.group(2)}'
            L[a] = ''
    return L


if __name__ == '__main__':
    PDF, OUT = sys.argv[1], sys.argv[2]
    os.makedirs(OUT, exist_ok=True)
    d = fitz.open(PDF)
    B.FATTI = B.measure_facts(d)
    prof = os.environ.get('MANREADER_PROFILO')
    if prof and os.path.exists(prof):
        import json as _j
        B.PROFILO.update(_j.load(open(prof)))
    ipp = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'immagini_per_pagina.json')
    if len(sys.argv) > 3:
        ipp = sys.argv[3]
    if os.path.exists(ipp):
        import json
        IMMAGINI.update({int(k): v for k, v in json.load(open(ipp)).items()})
    if os.environ.get('MANREADER_TITOLI', '1') != '0':
        import ordine_manreader
        TITOLI = ordine_manreader.heading_size_levels(d)[0]
    for p in d:
        n = p.number + 1
        open(os.path.join(OUT, f'p{n:03d}.md'), 'w').write(f'<!-- pdf p. {n} -->\n\n' + page_md(p).strip() + '\n')
    print('scritte', d.page_count, 'pagine')
