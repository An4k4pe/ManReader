# Le schede in Markdown, verbatim con la nota — criterio scritto PRIMA

Il bersaglio di questo giro e' il **Markdown**, non l'EPUB: l'EPUB e' a valle e
non si giudica qui.

## Cosa si costruisce
Il testo di un manuale che esce in Markdown, dove le regioni a forma di record
escono come **blocco delimitato, verbatim, con una nota che dice cosa sono** —
riconosciute o no. La regola di non-perdita di `COMPITO_APERTO_schede_rare.md`:
una regione a forma di record che nessuno schema spiega **non si scarta**, si
emette con la nota «struttura non riconosciuta».

## Legatura alla IR e ai principi, che e' il punto del giro
- Il Markdown **non** viene stampato dall'esperimento: si costruisce un
  `DocumentIR` (`ir_model.py`) e lo si rende con `markdown_builder.build_markdown`,
  cioe' il renderer del repo, **invariato**. Se la resa e' brutta, e' un fatto
  sulla IR e sul renderer, non un difetto dello script.
- Le righe e le colonne vengono dal percorso di produzione gia' usato in
  `colonne.py`: cattura -> primitive normalizzate -> producer `layout.column_band`
  -> ordine a bande. La riga viene dalla sorgente, mai ricomposta per geometria.
- **Nessuna invenzione**: il testo dei blocchi e' quello delle primitive.
- **Nessun nuovo tipo di blocco, nessuna modifica al renderer.** La regione usa
  `role="callout"`, che e' la sola forma delimitata che IR 1 sa gia' rendere.
  E' una scelta di RESA, dichiarata e reversibile: non afferma che una scheda
  sia un callout.
- Niente wiring, niente producer nuovo, niente Resolution: giro esplorativo.

## Cosa diventa una regione, senza soglie nuove
1. **Record del rilevatore** (`pila2.py`): titolo della nota = firma del gruppo.
   Nessun filtro: quello che il metodo sa e' quello che esce, anche se e' molto.
2. **Corse residue con firma ricorrente su >= 3 pagine** (il criterio gia'
   fissato in `CRITERIO_COPERTURA.md`, non uno nuovo): nota «struttura non
   riconosciuta».
3. Una riga sta in **al massimo una** regione: dove un record copre, il residuo
   non riapre.
4. Tutto il resto: testo normale, e il renderer fa il suo mestiere.

## Fuori scope, dichiarato
La nota per lo **sfondo decorativo** della scheda (l'asset). Il testo e' coperto
qui; la sostituzione di sfondi e cornici con una nota che li referenzia richiede
l'estrazione degli asset, che questo giro non fa. Riporto quante primitive
visive cadono dentro le regioni, cosi' il prossimo giro ha il numero.

## Predizioni registrate
- **R1 — conservazione.** Il multiset dei caratteri non-spazio dei blocchi IR
  dev'essere **identico** a quello delle primitive testuali della pagina, su
  tutte le pagine. Verifica sulla IR e non sul Markdown, perche' il renderer
  aggiunge legittimamente `#`, `**`, `>`. Se differisce, il giro perde o inventa
  contenuto e si ferma.
- **R2 — la scheda esce come blocco unico.** Sulle 4 pagine di scheda del
  manuale 2 il testo della scheda esce dentro **un solo** callout. Predico
  **2 su 4**: su 29 e 31 il record parte dalla riga del nome, su 33 e 35 parte in
  mezzo alla prosa della descrizione (misurato nel giro precedente, non e' una
  previsione a caso). Se escono 4 su 4 ho sbagliato in meglio e va spiegato.
- **R3 — il rumore.** Conto i callout su tutto il manuale 2. Con 64 record su 47
  pagine predico **un muro**: piu' di un callout ogni due pagine. Se e' cosi', la
  resa per-record non e' la resa giusta, e questo giro lo deve dire invece di
  nasconderlo scegliendo una pagina che viene bene.

## Criterio di accettazione
Il giro si accetta se **R1 regge** — senza conservazione non c'e' niente da
guardare. R2 e R3 si riportano: sono la misura di quanto la resa e' pronta, non
la condizione per averla fatta.
