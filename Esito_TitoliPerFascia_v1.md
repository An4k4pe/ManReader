# Esito di `Criterio_TitoliPerFascia_v1.md` — **il corpo regge, il tetto cade**

**Stato in una riga**: il veto **A** passa su tutti i manuali ammessi e il veto
**D** pure; il veto **C** **cade**, e cade sul proprio caso di riferimento. Il
criterio **non è adottato**. Ciò che cade non è la fascia: è la clausola «oltre
la terza è corpo», scritta nella moneta sbagliata.

---

## 1. Che cosa è stato eseguito

La regola §1 è stata implementata come dichiarata, in due moduli separati come il
resto della codebase — `document_heading_band_measurements` conta,
`document_heading_band_policy` decide — e collegata a `document_scan` con ambito
**documento**, mentre arredo, marcatori e scale restano sulla finestra di
`Criterio_AmbitoDeiFatti_v2.md`.

**Prima di misurare qualunque cosa**, il modulo di produzione è stato confrontato
con `scripts/measure_heading_bands.py`, cioè lo script da cui vengono i numeri
del §0 del criterio: corpo, fasce candidate e livelli coincidono **identici** su
Dag, Fab e BoB. È il controllo che separa «ho eseguito quel criterio» da «ho
eseguito qualcosa di simile».

## 2. Veto A — l'ancora. **Passa.**

> Cade se su un solo manuale ammesso la fascia del corpo non è la dimensione che
> un lettore riconosce come testo corrente della pagina.

| manuale | corpo per massa | ancora vecchia (`min(prose_sizes)`) |
| --- | --- | --- |
| Dag | **8,9-9,2** | 2,8 |
| Fab | **9,9-10,3** | 9,8 |
| BoB | **9,8-10,2** | 9,8 |
| BiD | **9,2-9,5** | 9,3 |
| Wil | **9,8-10,2** | 8,2 |
| FWK | **11,7-12,0** | 9,6 |
| Apo | **11,6-12,0** | 9,0 |
| Vil | **11,6-12,0** | 11,6 |

Vil e' l'eccezione che il §0 del criterio aveva gia' dichiarato: li'
`prose_sizes` restituisce **una** dimensione sola e coincide con la moda, quindi
l'ancora vecchia era gia' giusta e il corpo per fascia la conferma.

Il caso da cui l'affermazione è nata — Dag, dove l'ancora era **2,8 pt**, una
dimensione che porta lo 0,15% del testo — è risolto: il corpo è la moda per
massa. Questa metà del criterio è **confermata**.

## 3. Veto D — nessuna dimensione con due livelli. **Passa.**

Verificabile a macchina, e verificato: la mappa dimensione→livello è **una sola
per documento**, identica su tutte le pagine. Prima ne veniva stampata una
diversa per pagina. Il difetto C del §0 — su Dag `28,0→h1` e `27,9→h2`, due
livelli per quello che sulla pagina è un titolo solo — è chiuso, perché ogni
dimensione della fascia riceve lo stesso livello.

**E la stabilità è il guadagno vero**, misurato sull'uscita di Dag:

| | prima | dopo |
| --- | ---: | ---: |
| occorrenze di titolo su testi che escono a livelli diversi | 241 (11,8%) | 2 (4,0%) |
| testi instabili | 19 | 1 |

Il caso peggiore, `**CARATTERISTICHE**` — h2 su 33 pagine e h3 su 156 — non
esiste più.

## 4. Veto C — la regressione. **Cade.**

> Le 16 righe che il giudizio della v2 ha confermato titoli devono restare
> promosse, e nessuna deve cambiare livello rispetto alla v3 senza che il cambio
> sia spiegato.

**Cade su ogni manuale che ha un termine di paragone**, e non di poco:

| manuale | corpo | titoli prima | instabili | titoli dopo | instabili | persi |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Dag | 8,9-9,2 | 2035 | 241 | 50 | 2 | **97%** |
| BiD | 9,2-9,5 | 1164 | 70 | 68 | 0 | **94%** |
| Wil | 9,8-10,2 | 1293 | 60 | 100 | 0 | **92%** |
| BoB | 9,8-10,2 | 1086 | 78 | 229 | 0 | **78%** |
| FWK | 11,7-12,0 | 394 | 51 | 100 | 0 | **74%** |
| Apo | 11,6-12,0 | 81 | 5 | 66 | 5 | **18%** |
| Fab | 9,9-10,3 | — | — | 88 | 0 | — |
| Vil | 11,6-12,0 | — | — | 82 | 0 | — |

La colonna «instabili» è il guadagno del criterio e va **a zero quasi ovunque**;
la colonna «persi» è il suo costo, e nessuna delle due si può leggere senza
l'altra. Apo è l'eccezione in entrambe le direzioni: perde poco e non guadagna
niente, perché ha venti dimensioni in tutto.

Sul caso da cui l'affermazione è nata, Dag: le occorrenze di titolo passano da
**2035 a 50**, ne mancano **1985**.
Fra le perse c'è `QUANDO IL DISASTRO È IMMINENTE`, che è **la riga per cui
`Criterio_Titoli_v3.md` è stato scritto** (`Esito_Titoli_v1.md` §3, riga 14). Con
lei, titoli di sezione che nessuno definirebbe arredo:

```
PANORAMICA          8 occorrenze → prosa
PRINCIPI DEL GM     7            → prosa
TONO E ATMOSFERA    6            → prosa
TEMI                6            → prosa
ISPIRAZIONI         6            → prosa
```

Passare da `###` a **testo corrente** è il cambio di livello più estremo
possibile, e il criterio non lo spiega: aveva previsto il costo come «BoB perde
un livello», e il costo misurato è il **97,5% dei titoli**.

## 5. Che cosa è caduto, e che cosa no

**Non le fasce.** Ciò che resta promosso su Dag è uno scheletro corretto: 44
titoli distinti su 379 pagine — `SOMMARIO`, `INTRODUZIONE`, `CAPITOLO
UNO…CINQUE`, i nomi delle nove classi, i nomi delle campagne. I filtri fanno il
loro lavoro; il corpo è giusto; la stabilità è guadagnata.

**È caduta la clausola «Oltre la terza è corpo»**, perché confonde due grandezze:

- **quali** fasce sono titoli — lo decidono i quattro filtri, e lo decidono bene:
  8 fasce candidate su Dag, 9 su BoB, 9 su Wil, 7 su BiD;
- **quanti livelli** ha Markdown — che è una decisione dell'utente, e vale **tre**.

`document_heading_policy.heading_levels` collassava (`min(rango, MAX_LEVEL)`):
oltre il terzo rango tutto diventava `###`. Il criterio nuovo invece **scarta**.

**E su un manuale con tipografia di copertina il danno è totale**, perché le tre
fasce più grandi sono il frontespizio:

| manuale | h1 | h2 | h3 | fasce vere oltre la terza |
| --- | --- | --- | --- | --- |
| Dag | 26,4-28,0 | 20,8-21,6 | 18,0-19,0 | 17,0-17,6 · 14,0-14,8 · 11,4-12,1 · 10,7-11,3 · 10,0-10,6 |
| Fab | **83,0-87,5** | **40,0** | 24,9-25,0 | 12,3-13,0 · 11,6-12,0 |
| BiD | **71,3-72,0** | **59,4-60,0** | 30,0-31,0 | 28,0-29,0 · 17,0-18,0 · 13,7-14,0 · 12,8-13,0 |
| BoB | 24,5-24,6 | 21,8-22,0 | 19,6-20,6 | 18,3-19,2 · 17,2-18,0 · 15,7-16,6 · 15,0-15,4 · 13,0 · 11,9-12,0 |
| Wil | 39,0-41,0 | 36,0-38,0 | 33,9-35,7 | *(sei fasce)* |

Su Fab `h1 = 83-87 pt` e `h2 = 40 pt` sono corpi da copertina, e **ogni** titolo
di sezione del manuale sta oltre il terzo rango.

## 6. L'emendamento, misurato come **esplorazione** (`AGENTS.MD` §16)

Non è un giudizio e non salva questo criterio. È il numero che serve a decidere
il prossimo: quanti titoli produrrebbe la stessa selezione di fasce se il tetto a
tre **accorpasse** (`min(rango, 3)`, come la v3) invece di scartare.

| manuale | scarta (regola come dichiarata) | accorpa (emendamento) | v3, per confronto |
| --- | ---: | ---: | ---: |
| Dag | 50 | **2164** | 2035 |
| Fab | 103 | **697** | — |
| BoB | 250 | **777** | 1086 |
| BiD | 68 | **606** | 1164 |

Su BoB e BiD l'emendamento resta **sotto** la v3, ed è coerente: i quattro filtri
scartano fasce che la v3 promuoveva — decorazione, prosa grande, fasce su meno di
tre pagine. È il lavoro che devono fare.

**Perché l'emendamento regge senza sapere se il meccanismo poi passa**, che è la
prova che `CLAUDE.md` chiede per separarlo da un salvataggio:

1. è ciò che `document_heading_policy` faceva già, e il veto C esiste
   **precisamente** per proteggere quel guadagno;
2. è ciò che l'utente ha deciso il 1 settembre 2026 — «sono consapevole che a
   volte uno dei titoli si perderà limitandoli a 3» descrive **un livello che
   collassa**, non 1985 titoli che diventano prosa;
3. il §1 del criterio stesso, parlando di BoB, dice «ha quattro livelli veri e ne
   **perde uno**»: la clausola scritta non fa quello che la sua stessa
   motivazione dichiara.

Non lo adotto qui. Va dichiarato come `Criterio_TitoliPerFascia_v2.md`, e il
giudizio si rifà.

## 6-bis. Un difetto **pre-esistente** trovato dal giro, e non è di questo criterio

Vil rende **271 pagine su 272**. La pagina che cade è **idx 268 (numero stampato
`265`)**, con `ValueError: 1 text primitives are covered by no node` — una
violazione di `AGENTS.MD` §Coverage.

**Non è causata dalle fasce**: rimettendo l'ancora della v3 e rilanciando la sola
pagina, l'errore si riproduce **identico**. È il quarto difetto che un giro sul
documento intero trova e che la suite non vede, dopo i tre di Wil, BiD e
`ir2_builder`. Va aperto a parte, non qui.

## 7. Che cosa non è stato eseguito, e perché

- **Veto B** (giudizio riga per riga sulle promosse): il materiale c'è — con la
  regola come dichiarata sono 44 righe distinte su Dag, leggibili per intero — ma
  chiedere un giudizio umano su un meccanismo che ha già fallito C spenderebbe
  l'attenzione dell'utente sul candidato sbagliato.
- **Veto E** (`check_eb.py` 9/10): non lanciato. Sono un'ora e venti di macchina
  dell'utente su un meccanismo che non viene adottato. Si esegue sulla versione
  che può esserlo.

## 8. Stato del codice

I due moduli nuovi e il collegamento **restano in albero**, perché la metà
confermata è quella che serve al criterio successivo. 23 test nuovi, ruff pulito.
L'ancora vecchia (`prose_sizes`, `heading_levels`, `sizes_that_carry_headings`)
non è cancellata: resta in `document_heading_policy`, e `prose_sizes` continua a
servire la scala tipografica di `document_asset_policy`, che è un'altra domanda.
