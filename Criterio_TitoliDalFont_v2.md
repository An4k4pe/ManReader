# Criterio — i titoli dal font, v2. **Il veto principale sono le schede**

Dichiarato il 7 settembre 2026, **prima** della misura che decide.

## 0. Che cosa cade della v1, e perché era già scritto in albero

La v1 aveva come perno il **filtro della famiglia**: una faccia intesta se la sua
famiglia è diversa da quella del corpo. L'avevo giustificato con **un confronto su
un manuale** — su Dag `QuestaSans-Bold` (dove stanno le 188 `CARATTERISTICHE`
delle schede) contro `EvelethCleanRegular` (dove sta `PANORAMICA`).

**`Esito_TitoloSopraIlParagrafo_v1.md` §3 aveva già misurato quell'ipotesi su
sedici manuali, e dice che non separa**: 152 promozioni cambiano famiglia, 90
cambiano peso, con controesempi da entrambe le parti.

```
famiglia diversa e NON titolo:   Kul 'alle Dormienti.'      GrenzeGotisch / Bonyland
                                 Wil 'Incendi.'             Zedou-Bold / GaramondPremrPro
solo il peso e SÌ titolo:        Dag 'Il potere di Sprout'  QuestaSans-Bold / QuestaSans-Regular
                                 Fab 'Base' / 'Avanzato' / 'Superiore'
```

`Zedou-Bold` su Wil è una delle facce che la mia esplorazione promuoveva, con 578
righe. Il filtro cade in **entrambe** le direzioni, ed è la quarta volta in questa
serie che dichiaro su una tabella troppo piccola.

**Che cosa NON cade**: quel ramo confrontava il font della riga con quello del
**blocco**, riga per riga. Questo guarda le statistiche della faccia sul
**documento** e aggiunge tre filtri che quello non aveva. È un meccanismo diverso
sulla stessa intuizione, e per questo si misura invece di darlo per morto.

## 1. La regola

> **La faccia da intestazione.** Sotto il tetto della prosa, considerando le
> righe **governate** da un font — quello della maggioranza dei caratteri, che è
> ciò che `document_heading_measurements.governing_font` calcola già — quel font è
> una faccia da intestazione se tutte e tre:
>
> 1. almeno il **60%** dei suoi testi ha due o più caratteri e contiene una
>    lettera;
> 2. la sua **mediana di lunghezza riga** è al più **metà** di quella del corpo;
> 3. compare su almeno **tre pagine**.
>
> **Il guardiano del blocco.** Una riga governata da una faccia da intestazione è
> un titolo **solo se il suo blocco non contiene righe alla dimensione del
> corpo**.
>
> Prende **un solo livello**: quello successivo all'ultima fascia di dimensione,
> al più il terzo.

**I tre filtri sono quelli delle fasce**, con gli stessi valori, su un'altra
popolazione. Nessun numero nuovo.

**Emendamento del 7 settembre 2026, dichiarato prima della misura**: la prima
stesura chiedeva la riga composta **interamente** in un font. Uso invece il font
**governante**, cioè quello della maggioranza dei caratteri, per due ragioni che
reggono senza sapere come andrà la misura: è la nozione che
`document_heading_measurements.governing_font` definisce già e documenta **per
questo identico problema** — «un paragrafo che comincia con una parola in
grassetto è governato dal font…» — e l'unanimità è fragile a un glifo solo, per
esempio un punto elenco o un simbolo dentro un titolo altrimenti omogeneo. La
prosa con l'enfasi dentro resta governata dalla faccia di prosa, quindi il fine
del vincolo è servito lo stesso.

**Conseguenza sull'esplorazione del §3**: quei numeri erano contati con
l'unanimità, quindi non coincideranno esattamente con la misura che decide.

**Il guardiano del blocco è dell'utente** (6 settembre 2026), ed è più solido
della mia prima stesura: la faccia è una proprietà **globale** del documento, il
blocco è il **contesto** della riga. Una riga dentro un blocco di prosa è prosa
qualunque sia il suo font, e questo tiene fuori il grassetto che apre un paragrafo
senza dedurlo dalle statistiche.

**Che cosa il guardiano NON fa, e va detto**: protegge dall'enfasi dentro la
prosa, **non** dalle schede. Una cella di scheda sta in un blocco che non contiene
prosa di corpo, quindi lo passa. Le schede sono l'oggetto del veto principale, non
di una condizione.

## 2. **Il punto fisso, emendato e accettato**

> Una riga è prosa se sta a una **dimensione** di prosa **e** in un **blocco** di
> prosa. Due assi, non uno.

Emendamento al punto fisso dell'utente del 2 settembre, nella forma che l'utente
stesso ha corretto il 6 settembre — «più che una faccia di prosa, un blocco di
prosa» — e accettato prima di questa misura.

## 3. Il campione e le esclusioni

**Sedici manuali**, la stessa popolazione su cui il ramo precedente è caduto: non
riduco il campione a otto, perché il ramo precedente è caduto proprio su manuali
che un campione più piccolo avrebbe escluso. Seed **`20260902`**.

**Esplorazione dichiarata** (`AGENTS.MD` §16): ho applicato i filtri alle facce di
otto manuali e ho visto che passano `EvelethCleanRegular` su Dag, `Antonio-*` su
Fab, `Kirsty-Bold` su BiD, `Zedou-*` su Wil, `Calluna-*` su Apo e Vil, e che passa
anche spazzatura — la filigrana DRM di Fab (`'Andrea bruna - 273133'`, 363 righe
su 362 pagine), le testatine di Vil, le etichette di scheda di Dag. **Quella
esplorazione non applicava l'arredo**, che nella pipeline toglie filigrana e
testatine, e **non applicava il guardiano del blocco**, che non esisteva ancora.

## 4. Pass/fail — **il veto delle schede è il principale**

### A. Veto principale — le schede

> Cade se **una sola** riga promossa è una cella di scheda, un'etichetta di scheda
> o una riga di tabella, sulle tre pagine su cui il ramo precedente è caduto:
> **Wil idx 148** (scheda d'area), **DIE idx 195** (scheda mostro), **Fab idx 175**
> (tabella di classe, numero stampato 174).

`Esito_TitoloSopraIlParagrafo_v1.md` §2: quelle tre pagine hanno prodotto **161
righe su 242**, ed è il quarto meccanismo che le schede fanno cadere dopo il
produttore di tabelle, la ricorrenza di posizione e il giudizio degli elenchi.

**Le schede si gestiscono a parte** — indicazione dell'utente del 7 settembre
2026 — quindi questo criterio non prova a trattarle: le deve **non toccare**. Se
le tocca, cade, e il debito passa al meccanismo delle schede.

### B. Veto — la filigrana

> Su Fab `'Andrea bruna - 273133'` e `'9788831334921'` non devono essere promossi.

363 righe su 362 pagine: il nome dell'acquirente stampato su ogni pagina.

### C. Veto — il bersaglio

> Su Dag devono essere promosse `PANORAMICA`, `PRINCIPI DEL GM` e
> `COS'È UN GIOCO DI RUOLO DA TAVOLO?`. Cade altrimenti: senza il bersaglio la
> regola non paga nessun debito.

### D. Veto — il giudizio, sul delta

> Cade se una riga promossa **che non era promossa prima di questa regola** non è
> un titolo, su un campione sorteggiato.

### E. Globale — nessuna dimensione con due livelli

### F. Globale — regressione

> `check_eb.py` 9/10 con la sola differenza a verbale (Fab idx 126);
> `check_list_regression.py` e `check_numbered_lists.py` invariati.

### Se cade

- **A**: cade il criterio, e il debito passa al meccanismo dedicato alle schede.
  **Non si aggiunge una condizione sulle schede in questo giro**: sarebbe il
  quinto tentativo di trattarle di sfuggita dentro un meccanismo che parla d'altro,
  ed è esattamente come sono cadute le prime quattro volte.
- **B**: cade. Se l'arredo non prende una filigrana su 362 pagine, il difetto è
  dell'arredo e si riporta lì.
- **C**: la regola non raggiunge il debito. Cade.
- **D**: si riporta quale riga e perché.

## 5. Che cosa resta fuori

- **Le schede**, che da qui in poi hanno un meccanismo proprio da scrivere.
- **`TONO E ATMOSFERA`**: senza il filtro della famiglia non è più escluso di
  proposito, e se esce è un guadagno non previsto da riportare.
- **La gerarchia**: un livello solo per tutte le facce.
- **Il testo raddoppiato** (`'Valois Valois'`), difetto di composizione della riga.
