# Le schede su un sistema diverso: Draw Steel: Monsters — criterio (scritto prima)

13 settembre 2026, ramo `claude/statblock-struttura-prova`, prima di aprire DrM.

## Che cosa si mette alla prova
La regola in prova per le schede statistiche, collegata in IR 2 dietro
`main_ir2.py --schede-struttura`:

- un riquadro disegnato (separato se fuso) e' una **candidata** se contiene
  almeno due righe a campi -- una coppia etichetta/valore basta -- che non
  cominciano dentro una colonna di tabella (confini di `column_band` e confini
  ammessi da Resolution);
- fra candidate sovrapposte vince la piu' stretta che contiene un nome, e senza
  nome la piu' ampia;
- una candidata e' una **scheda** se almeno due altre candidate del documento
  condividono con lei almeno due etichette (la struttura si ripete);
- il nome diventa titolo per eccezione dichiarata nello script dei titoli,
  sotto le fasce, con i filtri dei titoli;
- una tabella che attraversa una scheda non si costruisce.

Tutto e' stato progettato su **Daggerheart SRD** e **Dragonbane** (Quickstart e
DB, che sono lo stesso sistema). Draw Steel e' un terzo sistema, mai usato per
progettare questo riconoscimento. **Non e' un campione fresco in assoluto**:
`DrM.pdf` e' nel benchmark e piu' milestone lo hanno usato (colonne, elenchi,
titoli), anche sulle sue schede. Il file sigillato
`Draw_Steel_Monsters_v1.01.pdf` e' lo stesso al byte.

## Esecuzione
    ./venv/bin/python main_ir2.py DrM.pdf --out <cartella> --tabelle --schede-struttura

Stesso stato del codice per tutto il giro; se il codice cambia a giro iniziato, il
giro si butta e si rifa'. L'impronta del diff rispetto a `e05ebfa` si registra
nell'esito.

## Soglia di accettazione
**Nessuna numerica**, per decisione dell'utente: il verdetto e' il suo giudizio a
vista, «se lo script riconosce le schede e le rende bene, funziona».

## Materiale per il giudizio, deciso ora
Seed `20260913`.

1. **Le schede riconosciute**: provini ritagliati dalla pagina, col nome
   assegnato. Tutte se sono al piu' 60; altrimenti 60 estratte col seed, e il
   conteggio per struttura di tutte.
2. **Le schede mancate**: 10 pagine estratte col seed fra quelle con testo e
   **senza** schede riconosciute, a pagina intera.
3. **La resa**: il Markdown di 5 pagine con schede estratte col seed, con
   l'immagine della pagina accanto; il «prima» e' la stessa pagina senza
   `--schede-struttura`, sopra il «dopo».

## Che cosa si riporta comunque, prima del giudizio
Regioni candidate e schede tenute; strutture (le componenti della ricorrenza)
con le etichette piu' comuni; pagine con almeno una scheda; pagine cadute e
tempo.

## Predizione e modo di falsificarla
**P1**: la regola trova schede su DrM. Cade se le schede tenute sono zero.

Detto prima: la regola ha ancora bisogno di un **riquadro disegnato**. Se le
schede di Draw Steel non ne hanno, il risultato e' zero, ed e' un esito da
riportare e da diagnosticare, non un guasto da correggere in silenzio prima di
mostrarlo.
