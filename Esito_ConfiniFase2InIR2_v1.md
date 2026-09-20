# Esito — i confini ammessi dalla Fase 2 nelle tabelle di IR 2

Misurato l'11 settembre 2026 contro `Criterio_ConfiniFase2InIR2_v1.md`,
dichiarato prima della misura. Uscite in `output/resa/fase2-prima/` (a4e5090) e
`output/resa/fase2-dopo/`, confronto con `output/resa/fase2_confronto.py`,
immagini delle pagine giudicate in `output/resa/fase2-pagine/`.

## Verdetto

**Passa**, con il giudizio mio ancora da confermare a vista: **meglio 16, peggio
2, neutro 2**; nessuna tabella di prima perde una primitiva; le quattro tabelle
nuove cadono tutte su tabelle stampate, quindi il veto del §3.C non scatta.

## §3.A — Barra

- 1675 test verdi (i 4 nuovi compresi), ruff pulito.
- E-B: **9 su 10**, l'unica diversa Fab idx 126, già a verbale (`output/resa/eb-fase2.log`). Lo script esce con 1 perché non sono 10 su 10, come a ogni giro dal 30 agosto.

## §3.B — Nessuna riga esce

| manuale | prima | dopo | uguali | cambiate | nuove | **sparite** |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DB  | 67 | 70 | 59 | 8 | 3 | **0** |
| Apo | 16 | 16 | 16 | 0 | 0 | **0** |
| Dag | 60 | 61 | 52 | 8 | 1 | **0** |

Ogni tabella di prima ritrova dopo esattamente il suo insieme di primitive,
diviso fra più celle. Su Apo i 22 confini ammessi sono tutti strisce che il
cancello respinge, e non cambia niente.

## §3.C — Il giudizio, pagina per pagina

| manuale | idx | stampata | che cosa cambia | giudizio |
| --- | ---: | ---: | --- | --- |
| DB  |  12 |  11 | D6 NOME: il numero si stacca dal nome | meglio |
| DB  |  13 |  12 | idem | meglio |
| DB  |  14 |  13 | idem | meglio |
| DB  | 104 | 103 | CACCIARE: REQUISITO si stacca da RAZIONI | meglio |
| DB  | 107 | 106 | CREARE UN PNG: il numero si stacca dalla prima colonna | meglio |
| DB  | 110 | 109 | LA MISSIONE: idem | meglio |
| DB  | 111 | 110 | IL VIAGGIO: idem | meglio |
| DB  | 123 | 122 | TESORI 2: D20 si stacca da TESORO | meglio |
| DB  |  10 |   9 | **nuova**, D12 STIRPE: prima sei paragrafi, ora tabella; la riga 12 resta subito sotto, in ordine | meglio |
| DB  |  61 |  60 | **nuova**, IMPREVISTI MAGICI: 15 righe giuste, 5 (9, 14, 15, 16, 18) perdono la prima riga, che esce **dopo** la tabella | **peggio** |
| DB  | 121 | 120 | **nuova**, ARMI IMPROVVISATE: le righe lunghe restano fuori, in tabella solo numeri, nomi e code di riga | **peggio** |
| Dag | 132 | 131 | BOTTINO: TIRO si stacca da BOTTINO | meglio |
| Dag | 133 | 132 | idem | meglio |
| Dag | 135 | 134 | idem | meglio |
| Dag | 136 | 135 | idem | meglio |
| Dag | 161 | 160 | DIFFICOLTÀ: TIRO si stacca dalla prima azione | meglio |
| Dag | 162 | 161 | idem | meglio |
| Dag | 285 | 284 | **nuova**, BESTIA d20: prima un paragrafo unico, ora tabella; la riga 20 resta subito sotto, in ordine | meglio |
| Dag | 134 | 133 | BOTTINO: era rotta (i nomi non ci sono) e resta rotta, con una colonna vuota in più | neutro |
| Dag | 311 | 310 | KOHD: tabella fantasma, prima e dopo; ABC, DEF, GHI si separano come nel diagramma | neutro |

**A verbale, due cose.**

1. **Il «peggio» dichiarato non nominava il caso di DB p60 e p120**: il testo di
   una tabella stampata che finisce diviso fra cella e paragrafo. Li ho contati
   peggio, cioè più severamente di quanto il criterio chiedesse. Il verdetto non
   ne dipende: 16 contro 2, o contro 0.
2. **I due peggio sono entrambi tabelle nuove, e hanno la stessa causa**: la
   regione del `table_candidate` è più stretta del testo della tabella (Milestone
   39, punto aperto 4). Le righe più larghe ne restano fuori e restano paragrafi,
   le loro code entrano in cella. Il difetto c'era; il collegamento lo scopre
   perché fa tabella di regioni che prima avevano una colonna sola e tabella non
   erano. Delle quattro tabelle nuove, due sono meglio (DB p9, Dag p284) e due
   peggio.

## Che cosa resta aperto

- **Le tabelle nuove**: tenerle tutte e quattro, o lasciare che i confini
  dividano soltanto tabelle che esistono già (si perdono DB p9 e Dag p284, si
  tolgono DB p60 e p120). È una decisione dell'utente.
- I corridoi **ammessi** di altre bande dentro la regione (Dag p131, la colonna
  DESCRIZIONE): §4 del criterio, non toccato.
- La regione più stretta del testo: Milestone 39, punto 4.
- **Il giudizio è mio**: vale come ipotesi finché l'utente non guarda le pagine.
