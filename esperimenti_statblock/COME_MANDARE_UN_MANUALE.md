# Come far arrivare un manuale senza mandare il PDF

Il rilevatore non usa **niente** di cio' che pesa in un PDF di manuale: non
apre le immagini, non legge i font incorporati, non guarda i disegni. Gli
servono solo, per ogni riga: posizione, e per ogni span testo, nome del font,
dimensione e colore.

`dump_spans.py` estrae esattamente quello. Misurato:

| manuale | PDF | dump |
| --- | --- | --- |
| Daggerheart SRD, 68 pagine | 868 KB | 331 KB |
| Dragonbane Quickstart, 47 pagine | 17,0 MB | 76 KB (230x piu' piccolo) |

Circa **1,3 KB per pagina**. Un manuale da 300 pagine sta in ~400 KB, e in
30 MB ci stanno una settantina di manuali interi.

## Uso

```
python3 dump_spans.py manuale.pdf manuale.spans.json.gz
python3 dump_spans.py manuale.pdf parte.spans.json.gz --da 30 --a 60
```

Poi il dump si analizza con:

```
python3 pila_da_dump.py manuale.spans.json.gz [--verita REGEX]
```

## Equivalenza, verificata e non assunta

`pila_da_dump.py --verifica manuale.pdf` confronta i due percorsi riga per
riga. Su entrambi i manuali disponibili: **righe identiche e analisi identica**.

La verifica e' servita: la prima versione arrotondava le coordinate a due
decimali, e questo **ribaltava l'ordine di righe quasi complanari** — quattro
righe su 3174 sul Dragonbane. Non cambiava l'esito su quel manuale, ma un dump
che non e' identico al PDF non puo' fare da ingresso a una validazione.
L'arrotondamento e' stato tolto; il dump cresce di poco e torna equivalente.

## Avvertenza

Il dump contiene **tutto il testo del manuale**: ai fini dei diritti vale come
il manuale. Non va committato ne' pubblicato, esattamente come i PDF di
benchmark (`AGENTS.MD` §Vincoli permanenti: output, workspace e dump non
committati).
