# Esito — le due riparazioni della regione tabella in IR 2: **CADE sul veto**

Misurato l'11 settembre 2026 contro `Criterio_RiparazioneRegioneIR2_v1.md`,
dichiarato ed emendato (§2, il piè di pagina) prima di qualunque uscita. Prima:
`output/resa/fase2-dopo/`; dopo: `output/resa/riparo/`. Confronto con
`output/resa/riparo_confronto.py`, campione con `output/resa/riparo_campione.py`,
immagini in `output/resa/fase2-pagine/`.

## Verdetto

**Cade.** La barra regge, nessuna primitiva esce da una tabella, e il conteggio
passa in qualunque lettura; ma **il veto scatta su cinque regioni**, e su almeno
una — Dag p229 — per un errore che è della riparazione e di nessun altro.

## §4.A — Barra

1680 test verdi (5 nuovi), ruff pulito. E-B **9 su 10**, l'unica diversa Fab
idx 126, già a verbale (`output/resa/eb-riparo.log`).

## §4.B — Nessuna primitiva esce da una tabella

| manuale | prima | dopo | uguali | cambiate | nuove | violazioni |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DB  | 70 | 70 | 19 | 51 | 0 | **0** |
| Apo | 16 | 16 |  0 | 16 | 0 | **0** |
| Dag | 61 | 64 | 12 | 49 | 3 | **0** |

## §4.C — Il giudizio

119 tabelle cambiate o nuove, più di 40: campione del §3, le 9 delle pagine
nominate più una ogni 4 delle altre 110, **37 tabelle**. Ognuna guardata
sull'immagine della pagina.

| manuale | idx | stampata | che cosa aggiunge | giudizio |
| --- | ---: | ---: | --- | --- |
| DB  |   8 |   7 | seconda riga d'intestazione e righe di UNITÀ TEMPORALI | meglio |
| DB  |  10 |   9 | `D12 STIRPE` e `12 Lupinide` | meglio |
| DB  |  20 |  19 | la riga `2 Rattonero` / `5 Lingua Forcuta` | meglio |
| DB  |  27 |  26 | prosa, il banner CAPACITÀ ALTERNATIVE: regione a cavallo di due tabelle e prosa | peggio |
| DB  |  43 |  42 | le righe mancanti del riquadro AZIONI, due colonne di punti elenco | **peggio, veto** |
| DB  |  61 |  60 | le 5 righe tagliate (9, 14, 15, 16, 18) **e** il piè di pagina | misto |
| DB  |  74 |  73 | l'ultima riga `Grande Elmo` | meglio |
| DB  |  79 |  78 | fine riga di Maglio, Martello, Piccone | meglio |
| DB  |  86 |  85 | righe 2, 3, 4, 6 degli attacchi mostruosi | meglio |
| DB  |  92 |  91 | righe 2-6 degli attacchi mostruosi | meglio |
| DB  |  97 |  96 | una riga delle due colonne di prosa sopra | peggio |
| DB  | 104 | 103 | `6 Cervo` | meglio |
| DB  | 107 | 106 | i nomi tagliati delle righe 2, 10, 13, 17, 18 | meglio |
| DB  | 112 | 111 | righe 3-20 con le celle a capo | meglio |
| DB  | 121 | 120 | sinistra: punti elenco tagliati, `6 Lampadario` coi suoi | meglio |
| DB  | 121 | 120 | destra: punti elenco tagliati | meglio |
| DB  | 123 | 122 | righe 6, 13, 15 complete **e** titolo e piè di pagina | misto |
| Apo |  16 |  13 | la voce 1493-1497 della cronologia **e** il piè `Prologo` | misto |
| Apo |  36 |  33 | la riga di contenuto del riquadro COSA PENSA | meglio |
| Apo |  54 |  51 | l'intestazione `D6 NOME …` | meglio |
| Apo |  86 |  83 | titolo della sfida **e** intestazione DIFFICOLTÀ | misto |
| Dag |  23 |  22 | etichette della scheda personaggio d'esempio | peggio |
| Dag | 116 | 115 | la colonna destra della prosa esplicativa | **peggio, veto** |
| Dag | 120 | 119 | intestazione e 5 righe **e** le etichette delle illustrazioni | misto |
| Dag | 124 | 123 | l'intestazione | meglio |
| Dag | 129 | 128 | le caratteristiche tagliate delle armature | meglio |
| Dag | 132 | 131 | `avversario.` | peggio |
| Dag | 135 | 134 | intestazione della tabella destra, righe 14, 17, 24, 30, 34 | meglio |
| Dag | 162 | 161 | le prime righe dei tre blocchi | meglio |
| Dag | 197 | 196 | `potete utilizzare:` **e** l'ultima riga `Effrazione` | misto |
| Dag | 230 | 229 | tabella **nuova** da tre schede avversario, piè di pagina compreso | **peggio, veto** |
| Dag | 285 | 284 | `20 Secrezione` | meglio |
| Dag | 285 | 284 | `20 Scorza` | meglio |
| Dag | 311 | 310 | titolo `LA SCHEDA MADRE` e i paragrafi Fase 1 / Fase 2 | **peggio, veto** |
| Dag | 352 | 351 | etichette della scheda personaggio vuota | peggio |
| Dag | 356 | 355 | titoli e una riga della guida al gioco | peggio |
| Dag | 361 | 360 | gran parte della scheda del compagno, paragrafi compresi | **peggio, veto** |

**meglio 20, misti 6, peggio 11.** Il criterio non diceva come contare una
tabella che è insieme meglio e peggio; lo dico adesso e riporto entrambe le
letture: misti contati peggio, **20 contro 17**; contati meglio, **26 contro
11**. Il conteggio passa in tutte e due, e il verdetto non ne dipende.

**Il veto**: cinque regioni assorbono un paragrafo. Verificato sul markdown per
tre — Dag p229, Dag p115, DB p42 —; Dag p310 e p360 dalle righe aggiunte.

## Che cosa è caduto — il veto apre la diagnosi

**Non la moneta del veto.** Su Dag p229 la riparazione **costruisce una tabella
che prima non esisteva** da tre schede avversario: dentro le righe della SIRENA e
del SOLDATO, le etichette `SCINTILLANTE` / `GIOVANE` e il piè di pagina, fuori le
intestazioni `CARATTERISTICHE`. La scheda esce spezzata fra tabella e paragrafi.
È l'errore grande che il veto doveva fermare, e l'ha fermato. Su DB p42 e Dag p115
la riparazione **completa** una tabella che sulla pagina non c'è: il testo che
sporgeva passa da paragrafo a cella. Il veto le conta, e ha ragione.

**La forma della caduta è netta:**

- **tutte e 20 le tabelle migliorate sono tabelle vere**, e nei 6 misti la parte
  di tabella vera migliora anch'essa;
- **10 degli 11 peggio stanno su regioni che non sono tabelle** — prosa a due
  colonne, riquadri, schede personaggio e avversario — e l'undicesimo è
  `avversario.`;
- i danni dei misti sono **testo adiacente a una tabella vera**: titoli, piè di
  pagina, etichette di illustrazione.

Le due riparazioni fanno il loro mestiere dove la regione è una tabella, e
**ingrandiscono l'errore dove non lo è**. Il discriminante fra le due cose è
esattamente ciò che manca da Milestone 35 («`table_candidate` emette candidati
anche sulle pagine di prosa») e che tre criteri di Milestone 39 hanno cercato e
non trovato. La riparazione non lo risolve e senza di esso non si può limitare.

## Che cosa resta, e che cosa non si è misurato

- Le intestazioni a riga unica (DB p11, p60, p120) restano fuori, come previsto.
- Due guardie note per i danni adiacenti, **non misurate**: gli slot d'arredo,
  che `run()` conosce prima di costruire la pagina, fermerebbero i piè di pagina;
  i titoli non hanno una guardia esistente.
- Dag p131 `18` resta fuori per il gutter di un'altra banda, come previsto.

## La decisione, che è dell'utente

`--tabelle` è spento di default: senza, questo lavoro non cambia niente. Con,
la riparazione porta le intestazioni e le ultime righe delle tabelle vere e
guasta le regioni che tabelle non sono. Il criterio caduto dice di **non
collegarla così**. Le strade: toglierla dal percorso `--tabelle` tenendo codice,
test e verbale (non si cancella, si tagga); oppure tenerla e affrontare prima il
discriminante tabella / non tabella, che è il problema vero.

## Per `Verbale_RegioneTabella_v1.md`: due rettifiche e una mezza risposta

Il verbale della chat tabelle (11 settembre, worktree `table-region-producer-005fb8`,
non committato) è arrivato dopo questa misura. Tre cose che questa misura gli
aggiunge:

- **Dag idx 197 (pag198), il secondo fallimento cieco di
  `Criterio_TabellaNormale_v1.md`, non è la regione.** Con
  `prototype_table_columns_and_rows.py --repair none` la tabella esce giusta
  (`| Amicizia con la Natura | Imboscata | Sapienza Magica |`); con `--repair xy`
  parte da `potete utilizzare:` e spezza `Amicizia` / `con la Natura`. La causa è
  `repair_region_y`. Dei tre casi ciechi, quindi: uno la regione (BiD pag228),
  uno la riparazione (Dag pag198), uno la riga (Wil pag59). Tocca
  `Esito_TabellaNormale_v1.md` §2 e il §5.1 del verbale, che scrivono «due su tre
  la regione».
- **Il controllo di collegamento del §9.2, a metà.** Su Dag idx 136 V4 ammette il
  corridoio `x95-102`, alto il 99% della tabella, e con i confini della Fase 2
  collegati la tabella esce con `TIRO` staccato da `BOTTINO`
  (`Esito_ConfiniFase2InIR2_v1.md`). È una misura d'esplorazione, **senza la
  predizione scritta prima** che il §9.2 chiede. Vil idx 166 non misurato.
- **Il caso peggiore di questo esito ha già una regola.** Su `e05ebfa` (ramo
  `claude/statblock-markdown-ir2-7b2573`): con `--tabelle`, una regione che
  attraversa il confine di una scheda non si costruisce, scritta proprio perché
  su Daggerheart `table_candidate` copre colonne di tre schede. È Dag p229. Non
  copre gli altri quattro casi del veto: due colonne di prosa (Dag p115, p310), un
  riquadro (DB p42), una scheda personaggio (Dag p360).
