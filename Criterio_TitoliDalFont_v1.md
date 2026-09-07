# Criterio — i titoli dal font, sotto il tetto della prosa

Dichiarato il 6 settembre 2026, **prima** della misura che decide.

## 0. Il debito che paga, e quanto è grosso

`Esito_TettoDallaMassa_v1.md` §6 lascia aperto l'asse del font con un esempio: su
Dag `PANORAMICA` sta a **12,0 pt** in `EvelethCleanRegular` mentre la prosa sta a
**12,1** in `QuestaSans-LightItalic`. Sull'asse della dimensione i titoli stanno
**sotto** la prosa, quindi nessuna regola di misura li può raggiungere.

La nota sulle citazioni in coda alla Milestone 41 lo ha quantificato, e l'esempio
lo sottostimava di due ordini di grandezza: sotto il tetto di Dag stanno anche
`INTRODUZIONE` (**1080 righe su 243 pagine**) e `DAGGERHEART TEAM` (822 righe su
308). Non sono otto occorrenze: sono **migliaia di righe per manuale**.

## 1. La regola

> **La faccia da intestazione.** Sotto il tetto della prosa, un font è una
> **faccia da intestazione** se, considerando solo le righe composte **interamente
> in quel font**, tutte e quattro:
>
> 1. la sua **famiglia** è diversa da quella del font di corpo;
> 2. almeno il **60%** dei suoi testi ha due o più caratteri e contiene una
>    lettera;
> 3. la sua **mediana di lunghezza riga** è al più **metà** di quella del corpo;
> 4. compare su almeno **tre pagine**.
>
> Una riga interamente composta in una faccia da intestazione è un titolo **se
> non sta dentro un blocco di prosa** -- cioè se il suo blocco non contiene righe
> alla dimensione del corpo. Prende **un solo livello**: quello successivo
> all'ultima fascia di dimensione, al più il terzo.

**I quattro filtri sono gli stessi delle fasce**, con gli stessi valori, applicati
a un'altra popolazione. Non introduco numeri: se il 60% e il mezzo separano
decorazione e prosa sull'asse della dimensione, separano le stesse cose
sull'asse della faccia, o non separavano neanche prima.

**Perché la riga intera e non la primitiva.** Nella prosa il grassetto sta
**dentro** la riga: `**Vali Quanto la Tua Parola:**` apre un paragrafo e non è un
titolo. Chiedere che **tutte** le primitive della riga siano nella stessa faccia è
ciò che distingue una riga intestata da una riga con dentro dell'enfasi. È lo
stesso principio con cui `Criterio_MarcatoreDaFont_v2` legge il marcatore dalla
primitiva e non dal paragrafo.

**Perché la famiglia e non il peso.** Misurato su Dag, `QuestaSans-Bold` e
`EvelethCleanRegular` sono **indistinguibili** su massa (3,88% contro 1,11%),
righe (2679 contro 1298), mediana (17 contro 7) e pagine (348 contro 352). Ma nel
primo stanno le **188 occorrenze di `CARATTERISTICHE`**, che sono etichette di
campo delle schede, e nel secondo `PANORAMICA`. L'unica cosa che li separa è che
`QuestaSans-Bold` è il corpo con un peso diverso.

**Il costo dichiarato**: `TONO E ATMOSFERA`, a 11,0 pt in `QuestaSans-Medium`, è
un titolo vero e **resta perso**. La famiglia che tiene fuori `CARATTERISTICHE`
tiene fuori anche lui, ed è un prezzo che pago consapevolmente perché l'errore
opposto — 188 etichette di scheda promosse — è peggiore.

**Un livello solo, e non un rango per faccia.** Le facce sotto il tetto non sono
ordinate fra loro da niente che il documento dichiari: inventare una gerarchia
guardando pagine o massa sarebbe rendere scritta nel meccanismo una struttura che
la sorgente non afferma. Stanno tutte sotto ogni fascia di dimensione, quindi
prendono il livello che viene dopo.

## 2. **L'emendamento al punto fisso dell'utente**

Il punto fisso del 2 settembre 2026 dice: «ciò che è identificato come prosa non è
mai un titolo». Questa regola **promuove righe che stanno al tetto o sotto**,
quindi lo contraddice come è enunciato.

La riformulazione, **accettata dall'utente il 6 settembre 2026**:

> Una riga è prosa se sta a una **dimensione** di prosa **e** in un **blocco** di
> prosa. Due assi, non uno.

Il secondo asse è **strutturale, non tipografico**, ed è una correzione
dell'utente alla mia prima stesura, che diceva «in una faccia di prosa». La sua
formulazione è migliore per una ragione che vale la pena scrivere: la faccia è una
proprietà **globale** del documento, il blocco è il **contesto** della riga. Una
riga che sta dentro un blocco di prosa è prosa **qualunque cosa sia il suo font**,
e questo tiene fuori il grassetto che apre un paragrafo senza doverlo dedurre
dalle statistiche della faccia.

Con essa `PANORAMICA` a 12,0 pt, sola nel suo blocco, non è prosa; mentre
`'Quando giocate a Daggerheart…'` a 12,1, dentro il suo paragrafo, lo resta.

Il font resta nel meccanismo come **segnale positivo** -- che cosa fa di una riga
un titolo -- mentre il blocco e' il **guardiano negativo** -- che cosa la
riporta a essere prosa. Due ruoli diversi, e per questo due condizioni separate al
§1.

## 3. Il campione, le esclusioni, e che cosa ho già visto

Seed **`20260902`**, mantenuto. Fuori **DrM** e **DrW**. Dentro e da guardare
**Kul**.

**Esplorazione dichiarata** (`AGENTS.MD` §16). Ho già applicato i quattro filtri
alle facce di otto manuali, ed è il motivo per cui la regola è scritta così. Le
facce che passano sono in maggioranza titoli veri, ma **passa anche della
spazzatura**, e la dichiaro adesso perché i veti la trovino invece di scoprirla:

```
Fab  Helvetica              363 righe  362 pag  'Andrea bruna - 273133'   filigrana DRM
Vil  ElfrethVF-Regular       30 righe   30 pag  '144 •Ambientazione'      testatine
Dag  QuestaSlab-BoldItalic  172 righe   58 pag  'Avversario Base di Rango' schede
Dag  TTOctosquaresTrl        46 righe    4 pag  'ABC' | 'JKL'             decorazione
Fab  MinionPro-Regular       20 righe    3 pag  'Questo è il tuo mondo,'  citazione
```

**La mia esplorazione sovrastima il danno**: filigrana e testatine sono **arredo**,
e la pipeline lo toglie mentre lo script no. Quanto ne resti lo dice il giro vero,
e **non l'ho misurato**.

## 4. Pass/fail

### A. Veto — il bersaglio

> Su Dag devono essere promosse `PANORAMICA`, `PRINCIPI DEL GM` e
> `COS'È UN GIOCO DI RUOLO DA TAVOLO?`. Cade altrimenti.

### B. Veto — la filigrana

> Su Fab `'Andrea bruna - 273133'` e `'9788831334921'` **non** devono essere
> promossi. Cade altrimenti.

È il caso peggiore visto nell'esplorazione: 363 righe su 362 pagine, cioè il
nome dell'acquirente stampato su ogni pagina. Se l'arredo non lo toglie, la regola
non è adottabile a nessun prezzo.

### C. Veto — le etichette di scheda

> Su Dag `CARATTERISTICHE` **non** deve essere promossa. Cade altrimenti.

È ciò che il filtro della famiglia esiste per impedire.

### D. Veto — il giudizio, **sul delta**

> Cade se una riga promossa **che non era promossa prima di questa regola** non è
> un titolo, su un campione sorteggiato.

Forma emendata di `Esito_TettoDallaMassa_v1.md` §3: un veto che giudica una
modifica guarda ciò che la modifica produce.

### E. Globale — nessuna dimensione con due livelli

Il livello dal font non deve entrare in conflitto con quello dalla dimensione: una
riga sopra il tetto continua a prendere il livello della sua fascia.

### F. Globale — regressione

> `check_eb.py` 9/10 con la sola differenza a verbale (Fab idx 126);
> `check_list_regression.py` e `check_numbered_lists.py` invariati.

### Se cade

- **A**: la regola non raggiunge il debito e non serve a niente. Cade.
- **B**: cade, e non si aggiunge un quinto filtro nello stesso giro.
- **C**: il filtro della famiglia non fa il suo lavoro. Cade.
- **D**: si riporta quale riga e perché.

## 5. Che cosa resta fuori

- **`TONO E ATMOSFERA`** e ogni titolo composto nella famiglia del corpo: costo
  dichiarato al §1.
- **Le schede mostro**, dichiarate otto volte.
- **Il testo raddoppiato** (`'Valois Valois'`), difetto di composizione della riga.
- **La gerarchia**: un livello solo per tutte le facce, per la ragione del §1.
