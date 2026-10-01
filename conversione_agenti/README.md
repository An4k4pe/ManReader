# Conversione con script e agenti

Copia, sotto versione, del lavoro fatto in `~/Documenti/ManReader_prova/` fra settembre e il 1 ottobre 2026:
convertire un PDF TTRPG in un Markdown unico con script meccanici, agenti per il giudizio e un orchestratore.
È un percorso parallelo alla pipeline di ManReader, da cui riprende moduli e criteri (vedi
`processo/CONSULTAZIONI_MANREADER.md`).

## Che cosa c'è
- `processo/`: `orchestra.py` e `RUNBOOK.md` (fasi, stato, lotti, validazione), `modelli/` (istruzioni per gli
  agenti), `script/` (bozza del testo, estrazione e smistamento delle immagini, banco di prova, ponte verso
  ManReader), `valutazioni_*.json` (ogni giro del banco di prova, anche quelli falliti), `giudizio/` e
  `giudizio2/` (criteri scritti prima, campioni e voti dei giudizi a vista).
- `Candela_Obscura/`, `Vileborn/`: verbali delle due conversioni, script e istruzioni usati.
- `DrawSteel/`, `Fabula_Ultima/`: profili, decisioni e piano delle prove su altri due manuali.
- `strumenti_esterni/`: confronto di sette strumenti esterni con la bozza (criterio, script, risultati).

## Che cosa NON c'è, di proposito
Il repository è pubblico: restano solo sul disco il Markdown convertito dei manuali, le pagine rivedute, le
bozze, i render delle pagine e le immagini estratte (testo e illustrazioni di manuali commerciali), oltre
agli ambienti e agli output degli strumenti esterni. Il banco di prova e le pagine di giudizio li rigenerano
da quella cartella e dai PDF, che vanno procurati a parte.

## Stato al 1 ottobre 2026
Banco di prova (quota di pagine con somiglianza >= 0,99 alle pagine rivedute dagli agenti), senza i livelli
dei titoli per fascia: Candela 81%, Vileborn 73%, Draw Steel 50% (20 pagine). Un giudizio a vista su 25
pagine dice che la misura regge agli estremi e sbaglia la direzione fra 0,93 e 0,99. Aperti: il secondo
giudizio a vista (ordine di lettura, livelli dei titoli), i riquadri dedotti dal solo font, la regolarità dei
titoli al corpo del testo.

## Dipendenze
I percorsi negli script sono assoluti e puntano alla macchina su cui è nato il lavoro.
`processo/script/ordine_manreader.py` importa i moduli di ManReader dal ramo
`claude/asset-note-visibility-e14deb` (`column_band`, politica dei titoli per fascia): senza quel codice la
bozza va lanciata con `MANREADER_ORDINE=0 MANREADER_TITOLI=0`.
