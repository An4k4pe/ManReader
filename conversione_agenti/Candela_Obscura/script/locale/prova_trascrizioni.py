"""Prova 3: trascrizione del testo dentro le immagini.
Riferimento: le 30 trascrizioni degli agenti della fase 1 (blocchi 'Testo nell'immagine').
Misure per immagine: somiglianza parola per parola (SequenceMatcher) e quota di parole
della trascrizione locale assenti dal riferimento ('inventate').
Criterio (fissato prima): >= 21 su 30 con somiglianza >= 0.85; nessuna con inventate > 10%.
"""
import json, os, re, difflib, collections
import client
from client import chiedi
R = '../..'
md = open(f'{R}/Candela_Obscura_Core_Rulebook.md').read().splitlines()
casi = []
for i, line in enumerate(md):
    if "Testo nell'immagine, trascritto a vista" in line:
        head = next((md[j] for j in range(i - 1, max(i - 4, 0), -1) if '](immagini/' in md[j] or '](sfondi_e_ripetuti/' in md[j]), '')
        m = re.search(r'\(\[((?:immagini|sfondi_e_ripetuti)/[^\]]+)\]', head)
        if not m:
            print('saltato (nessuna nota con link sopra):', md[i - 1][:80]); continue
        body = []
        for l in md[i + 1:]:
            if not l.startswith('>'): break
            body.append(l[1:].strip())
        tipo = 'mano' if re.search(r'manoscritt|a mano|calligraf', head + ' '.join(body), re.I) else 'stampa'
        casi.append(dict(file=m.group(1), nota=head, rif='\n'.join(body), tipo=tipo))
SYSTEM = """Lavori a un progetto che converte manuali di giochi di ruolo da PDF in Markdown. Le immagini vengono tolte
dal testo; quando un'immagine contiene testo di contenuto (lettere, giornali, moduli, biglietti, documenti di gioco,
scritte a mano) quel testo va trascritto, perche' altrimenti il lettore lo perde.
Regole di trascrizione:
- trascrivi esattamente cio' che si legge, nella lingua originale, senza tradurre, correggere o riassumere;
- mantieni gli a capo delle lettere e dei testi scritti a mano;
- una parola che non riesci a leggere diventa [illeggibile]; non completarla per congettura, anche se il senso la suggerisce;
- testo coperto o tagliato dal bordo: [illeggibile];
- se ci sono scritte in un alfabeto inventato (glifi), non trascriverle: scrivi [iscrizione in alfabeto inventato];
- niente commenti: dopo il ragionamento, scrivi la trascrizione tra le righe TRASCRIZIONE: e FINE."""
def parole(s):
    s = re.sub(r'\[illeggibile\]|\[iscrizione[^\]]*\]', ' ', s).replace('’', "'").replace('\\', ' ')
    return [w.lower() for w in re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z]+)?", s)]
orig = client.image_part
client.image_part = lambda p, max_side=2048: orig(p, max_side)
out = []
for c in casi:
    t, pin, pout, dt, _ = chiedi("Trascrivi il testo di contenuto presente in questa immagine.", [f'{R}/{c["file"]}'],
                                 max_tokens=6000, temperature=0, system=SYSTEM, thinking=True, timeout=1200)
    m = re.search(r'TRASCRIZIONE:\s*(.*?)\s*FINE\s*$', t, re.S)
    tr = m.group(1) if m else None
    a, b = parole(c['rif']), parole(tr or '')
    sim = difflib.SequenceMatcher(None, a, b, autojunk=False).ratio() if a else None
    inv = sum((collections.Counter(b) - collections.Counter(a)).values()) / max(len(b), 1)
    out.append(dict(c, locale=tr, grezzo=t, somiglianza=sim, inventate=inv, parole_rif=len(a), parole_loc=len(b),
                    illeggibili=(tr or '').count('[illeggibile]'), secondi=dt, token_out=pout))
    print(f"{c['file']:32} {c['tipo']:6} sim {sim if sim is None else round(sim,3)} inv {inv:.2f} rif {len(a)} loc {len(b)} {dt}s {pout}tok", flush=True)
os.makedirs(f'{R}/_lavoro/locale', exist_ok=True)
json.dump(out, open(f'{R}/_lavoro/locale/prova_trascrizioni.json', 'w'), indent=1, ensure_ascii=False)
ok = [o for o in out if o['somiglianza'] is not None and o['somiglianza'] >= 0.85]
print('casi', len(out), '| sim>=0.85:', len(ok), '| inventate>10%:', [o['file'] for o in out if o['inventate'] > 0.10],
      '| senza risposta:', [o['file'] for o in out if o['locale'] is None], '| secondi', round(sum(o['secondi'] for o in out)))
