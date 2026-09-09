# Criterio — il titolo impilato: unire le righe composte una sull'altra

Dichiarato il 9 settembre 2026, **prima** della misura che decide.

## 0. Che cosa ripara, e perché non è quello da cui siamo partiti

`Esito_TitoloComposto_v1.md` ha ritirato il meccanismo B — unire righe di titolo a
corpi diversi nello stesso blocco — perché produceva 83 unioni in maggioranza
sbagliate: incollava l'intestazione di sezione al primo elemento che introduce.
Il vincolo che rendeva sicura la regola vecchia era la **pari dimensione**, e
toglierlo la scopriva.

Il bersaglio era Kul, dove `ORRORI DELLA GNOSI` esce in tre pezzi. **Ma la misura
sui sedici manuali dice che il bersaglio è più largo**: escono spezzati anche

```
Dag  'CAPITOLO UNO:'  + 'PREPARARSI ALL'AVVENTURA'
BiD  'CAPITOLO 1'     + 'le basi'                    (e 2..9)
Lan  'SEZIONE 0'      + 'PER INIZIARE'               (e 1..6)
SV   'CAPITOLO 1'     + 'LE BASI'                    (e 2..10)
Wil  'ZUPPA DI TAGLIATELLE E' + 'P O L P E T T E'
```

cioè **il numero di capitolo separato dal suo titolo su cinque manuali**, che nel
markdown spezza in due ogni apertura di capitolo.

## 1. La regola

> Due righe **consecutive dello stesso blocco**, entrambe titoli, di dimensioni
> diverse, sono **un solo titolo** se sono composte **una sull'altra**:
>
> — **impilate**: la seconda comincia **sotto** la prima, e non più in basso di
>   **una scatola e mezza**;
> — **strette**: le scatole si **compenetrano** per almeno il **22%** della più
>   piccola, ma **nessuna contiene l'altra**.
>
> Le misure sono rapportate all'altezza della **scatola più piccola** delle due.
> Il livello è quello della dimensione **maggiore**.

**Perché queste due e non «stesso blocco» e basta.** Un titolo display impilato è
composto con l'**interlinea negativa** — le parole si incastrano — mentre
un'intestazione e ciò che introduce hanno interlinea normale, e due colonne
affiancate hanno scatole che si contengono. Sono tre figure diverse, e la
composizione le distingue.

**I tre confini stanno tutti dentro vuoti misurati**, su 114 coppie candidate dei
sedici manuali:

| confine | vuoto misurato | che cosa separa |
| --- | --- | --- |
| sovrapposizione ≥ **0,22** | **0,167 → 0,264** | l'interlinea normale da quella negativa |
| sovrapposizione < **1,00** | **0,871 → 1,025** | l'impilato dall'affiancato |
| avanzamento ≤ **1,50** | **1,182 → 3,898** | il titolo che continua dal paragrafo sotto |

Il quarto confine, **avanzamento > 0**, non è una soglia ma un **verso**: dice che
la seconda riga sta *sotto* e non *accanto*. È ciò che toglie le 22 coppie di BoB
(`'sgattaiolare' + 'ESEMPI'`, `'orologio da 8' + 'MIGLIORARE LE MISSIONI'`), che
hanno avanzamento **negativo** perché stanno in colonne diverse che il blocco ha
messo insieme.

**Il livello dalla dimensione maggiore**: un titolo è prominente almeno quanto la
sua parola più prominente. Su Kul i corpi crescono parola per parola — 86, 95,
102 — e quella crescita è un effetto grafico, non una gerarchia.

## 2. Il campione e le esclusioni

**Sedici manuali**, e non otto: il ramo che è caduto per ultimo è caduto proprio
su manuali che un campione ridotto avrebbe escluso. Seed **`20260902`**.

**Esplorazione dichiarata** (`AGENTS.MD` §16). Le tre tabelle di vuoti del §1 sono
misure fatte **prima** di questa dichiarazione, ed è il motivo per cui i confini
sono quelli. Applicando la regola alle 114 coppie ne restano **47**, e sono:
BiD 10, Kul 14, SV 10, Lan 7, Dag 5, Wil 1. **Non ho misurato l'uscita**, che è
ciò che i veti decidono.

## 3. Pass/fail

### A. Veto principale — le colonne affiancate di BoB

> **Nessuna** delle 22 coppie di BoB deve essere unita: `'sgattaiolare' + 'ESEMPI'`
> e le sue dieci sorelle, `'orologio da 8' + 'MIGLIORARE LE MISSIONI'` e le sue
> quattro. Cade altrimenti.

Sono il modo proprio di sbagliare del meccanismo precedente, e la ragione per cui
è stato ritirato.

### B. Veto — il bersaglio largo

> Devono essere unite `'CAPITOLO UNO:' + 'PREPARARSI ALL'AVVENTURA'` su Dag,
> `'CAPITOLO 1' + 'le basi'` su BiD, `'SEZIONE 0' + 'PER INIZIARE'` su Lan,
> `'CAPITOLO 1' + 'LE BASI'` su SV, e su Kul `'ORRORI' + 'DELLA'`. Cade
> altrimenti.

### C. Veto — il giudizio, sul delta

> Cade se una riga promossa **che non era promossa prima** non è un titolo, o se
> **due titoli distinti sono stati uniti**, su un campione sorteggiato.

### D. Veto — la copertura

> Nessuna primitiva di testo resta scoperta. `AGENTS.MD` §Coverage.

### E. Veto — l'ordine di lettura

> `check_eb.py` 9/10 con la sola differenza a verbale (Fab idx 126);
> `check_list_regression.py` e `check_numbered_lists.py` invariati.

Tocca la composizione della riga di tutti e sedici i manuali: se cade, cade tutto.

### Se cade

- **A**: cade il criterio. È il secondo tentativo su questa figura e il verbale
  dirà che l'asse geometrico non basta.
- **B**: la regola non paga il debito e cade.
- **C**: si riporta quale riga e quale metà del veto.
- **D**, **E**: difetto di costruzione o regressione, si diagnostica prima di
  decidere.

**In nessun caso si aggiunge un quarto confine in questo giro.** Tre sono già
molti, e girare intorno a una misura finché non passa è ciò che il §4 dei criteri
precedenti vieta.

## 4. Il costo dichiarato **prima**

Sotto 0,22 restano spezzate unioni che sono giuste, e si contano invece di
sparire:

```
DIE  'GOBLIN' + '(E HOBGOBLIN)'        sov 0,060
DIE  'GUARDIE' + '(E SOLDATI)'         sov 0,060
DIE  'HALFLING' + '(E GNOMI)'          sov 0,060
DIE  'ALBERI' + '(TREANT E DRIADI)'    sov 0,137
BoB  'LA CREATURA' + 'CON LE CORNA'    sov 0,117
```

Sono cinque, contro quarantasette guadagnate. Il costo è che una parentetica
composta con interlinea normale non si distingue da un'intestazione seguita da
altro, e su questo asse **non si può** distinguere.

## 5. Che cosa resta fuori

- **`REALTAÀ`** su Kul, la À doppia: corruzione del testo sorgente.
- **Le schede**, nella chat dedicata. **Il debito del font**, aperto.
- **La gerarchia**: il livello viene dalla dimensione maggiore, non da un albero.
