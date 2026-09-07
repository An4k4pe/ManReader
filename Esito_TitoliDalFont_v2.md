# Esito di `Criterio_TitoliDalFont_v2.md` — **cade, ed è il quinto sulle schede**

Scritto il 7 settembre 2026, dopo la misura sui manuali.

## 0. Stato in una riga

Il veto **C** passa — il bersaglio è raggiungibile. I veti **A**, **B** e **D**
cadono. Il criterio è ritirato, e il debito del font passa al meccanismo delle
schede, che va scritto a parte.

## 1. I veti

| veto | esito |
| --- | --- |
| **A** — le schede | **CADE**: Wil idx 148, **29 righe** promosse |
| **B** — la filigrana | **CADE**: Fab, **362 righe** `'Andrea bruna - 273133'` |
| **C** — il bersaglio | **passa**: su Dag `PANORAMICA`, `PRINCIPI DEL GM` e `COS'È UN GIOCO DI RUOLO DA TAVOLO?` sono promosse |
| **D** — il giudizio | **CADE**, e non serve un campione cieco per vederlo |

### A — le schede, per la quinta volta

Su **Wil idx 148**, la scheda d'area, la regola promuove 29 righe, e sono
letteralmente le stesse che avevano ucciso il ramo precedente:

```
GaramondPremrPro-Med  'Sentieri: Myusei, Colline Nakwon, Fiume Yhayhe'
GaramondPremrPro-Med  'Mostri: hutangwa, kala-kala, ko-ketak, radicapode,'
GaramondPremrPro-Bd   '[D] ≤ 4'
GaramondPremrPro-Bd   '[D] ≥ 5'
Zedou-Black           'Paperalata' | 'Stordifungo' | 'Fungo' | 'Chelocchio'
```

`'[D] ≤ 4'` è citato **testualmente** in `Esito_TitoloSopraIlParagrafo_v1.md` §2
come uno dei falsi positivi che fecero cadere quel ramo. Il guardiano del blocco
non le ferma, ed era previsto: una cella di scheda sta in un blocco che non
contiene prosa di corpo, quindi lo passa. Il §1 del criterio lo dichiarava.

**DIE idx 195 dà zero** e **Fab idx 175 una sola riga** (la filigrana), ma una
pagina pulita su tre non salva niente.

### B — la filigrana

**362 righe** su 362 pagine: `'Andrea bruna - 273133'` e `'9788831334921'`, cioè
il nome dell'acquirente e l'ISBN stampati su ogni pagina in `Helvetica`, che passa
i tre filtri senza sforzo.

Nella pipeline vera l'**arredo** dovrebbe toglierli, e questa misura non lo
applica. Ma il veto è scritto sul meccanismo, non sulla pipeline, e il meccanismo
li promuove.

### C — il bersaglio, che passa

`PANORAMICA`, `PRINCIPI DEL GM` e `COS'È UN GIOCO DI RUOLO DA TAVOLO?` escono
promosse su Dag. **Il debito del font è raggiungibile**: non è che l'asse non
veda i titoli: li vede.

### D — il giudizio

I conti grezzi bastano: **Dag 5871 righe promosse**, BiD 2705, Fab 2236, Wil 1465.
Il bersaglio su Dag era di circa 1900 righe, e la regola ne promuove **tre volte
tanto**. Il campione dice di che cosa è fatto il resto:

```
numeri di pagina     Dag '220' '131'    Apo '50'    Vil '13'    Fab '55'
voci di indice       BoB 'distruggere, 71, 294-295' | 'sgattaiolare, 71, 286-287'
prosa spezzata       Wil 'può effettuare una PRESA anziché un MOVIMENTO.'
                     DIE 'sono davvero' | 'era giocata la' | 'volta!'
celle di scheda      Wil 'BECCO. Portata: 1 (COLPO PRECISO).'   Fab 'Iniz. 6'
filigrana            Fab 'Andrea bruna - 273133'
titoli veri          Apo 'S E CO N D O AT TO' | 'S OT T E R F U G I O'
                     Vil 'V O LO N TÀ' | 'R E TA G G I O O S C U R O'
```

## 2. La diagnosi: l'asse vede il bersaglio ma **non si può puntare**

È il risultato che vale la pena portare avanti, ed è più preciso di «non
funziona».

**Sotto il tetto della prosa, «non è prosa di corpo» è una popolazione enorme**:
numeri di pagina, didascalie, etichette, voci d'indice, celle di scheda,
filigrane. Il compositore usa **le stesse facce da display** per tutte quante,
perché tipograficamente fanno lo stesso mestiere — stare fuori dal flusso del
testo.

Quindi il font distingue benissimo **il flusso dal non-flusso**, e non distingue
per niente **le parti del non-flusso fra loro**. `PANORAMICA` e `220` sono
entrambe in `EvelethCleanRegular` su Dag, ed è corretto che lo siano: sono
entrambe fuori dal flusso. Solo una delle due è un titolo.

Nessun filtro statistico sulla faccia può separarle, perché la differenza non è
nella faccia: è in **che cosa la riga fa nella pagina**.

## 3. È il quinto meccanismo che le schede fanno cadere

Dopo il produttore di tabelle, la ricorrenza di posizione, il giudizio degli
elenchi e `Criterio_TitoloSopraIlParagrafo_v1`. Indicazione dell'utente del 7
settembre 2026: **le schede si gestiscono a parte**, e questo criterio le ha
lasciate fuori di proposito invece di provare a trattarle di sfuggita — che è
esattamente il modo in cui sono cadute le prime quattro volte.

Il §4 del criterio vietava di aggiungere una condizione sulle schede in questo
giro, e non la aggiungo.

## 4. Due errori miei, a verbale

**Primo: la v1 di questo criterio.** Avevo dichiarato come perno il filtro della
**famiglia**, giustificandolo con un confronto su **un** manuale, quando
`Esito_TitoloSopraIlParagrafo_v1.md` §3 lo aveva già misurato su **sedici** e
scartato. L'ho scoperto leggendo il codice prima di implementare, cioè nel posto
giusto ma tardi: la v1 era già scritta e dichiarata.

**Secondo: l'esplorazione ha sottostimato il danno**, e lo sapevo. Avevo scritto
nel §3 che non applicava l'arredo né il guardiano del blocco. Non avevo previsto
che il problema vero non fosse la spazzatura che avevo visto, ma il **volume**:
5871 righe su Dag contro un bersaglio di 1900.

## 5. Che cosa resta in albero

`document_heading_font_measurements.py` e `document_heading_font_policy.py`
**restano, non collegati**, con questo esito citato nei loro docstring. Non si
cancella, si tagga: la misura del §2 — l'asse vede il non-flusso e non lo separa —
è il punto da cui deve ripartire chi affronterà le schede, perché **quel**
meccanismo dovrà distinguere proprio dentro il non-flusso.

## 6. Che cosa resta aperto

- **Il debito del font**: raggiungibile ma non puntabile da solo. Vive finché non
  c'è qualcosa che distingua le parti del non-flusso.
- **Le schede**, che adesso hanno cinque cadute alle spalle e nessun meccanismo
  proprio. È il prossimo lavoro.
- **`TONO E ATMOSFERA`**: senza il filtro della famiglia sarebbe stato
  raggiungibile, ma il criterio cade prima.
