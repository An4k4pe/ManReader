# Criterio — chi può essere un titolo, e chi non vota. **Tre meccanismi, tre veti**

Dichiarato il 2 settembre 2026, **prima** della misura che decide.

## 0. Che cosa questo criterio ripara

`Esito_TitoliPerFascia_v2.md` ha lasciato in piedi il punto fisso — «ciò che è
prosa non è mai un titolo», veto A a 8 su 8 — e due cadute: **Wil** perde
`◈ villaggio di lala`, **FWK** produce zero titoli. In più l'utente ha rilevato
sull'uscita che gli h3 di BoB sono troppi, e la coda è misurata: **19 righe
promosse più lunghe di 60 caratteri**, di cui 18 a 12,0 pt sulle pagine idx 6-8.

Tre cause distinte, e per questo tre veti distinti: **se cade, si deve sapere
quale**. L'utente ha chiesto di trattarle insieme perché nascono dallo stesso
lavoro; la riserva è a verbale: A e B sono lo stesso oggetto tipografico, C no.

## 1. Meccanismo A — **chi non può essere un titolo non vota**

> La quota di parole di una fascia si calcola **solo sui testi che potrebbero
> diventare titoli**. Sono esclusi dal conteggio, come numeratore e come
> denominatore:
>
> 1. i testi di **un carattere solo**;
> 2. i testi che l'**arredo** ha già tolto dal corpo — numeri di pagina e
>    testatine correnti.

**Non è una soglia nuova né un filtro in più**: è togliere il diritto di voto a
chi è già fuori dal ballottaggio. Entrambe le esclusioni esistono **già** a
valle: `document_heading_policy.heading_lines` scarta le righe di un carattere
(`len(line.text) <= 1`, in due punti), e `document_furniture_policy` toglie folii
e testatine. La quota di parole invece si calcola sulle primitive grezze, quindi
li conta.

Indicazione dell'utente del 2 settembre 2026: «se sono un solo carattere non sono
titolo».

**Misurato su Wil**, fascia `19,8-21,0` su 298 pagine, che contiene i nomi di
insediamento:

```
685 testi:  228 parole | 244 non-parole di UN carattere | 213 numeri di pagina
quota parole ora ................. 33%   (soglia 60%)  -> fascia scartata
togliendo i caratteri singoli .... 52%                 -> ancora scartata
togliendo anche i folii .......... 100%                -> passa
```

I 244 caratteri singoli sono capolettera: `'C'` ×50, `'S'` ×30, `'M'` ×24, in
`IM_FELL_English_Roman-SC` e `Zedou-Bold`. I 213 sono `'10'`, `'11'`, … `'1115'`.

## 2. Meccanismo B — **la riga va alla dimensione che la porta**

> La dimensione di una riga è quella che ne porta **più caratteri**, non la
> massima delle sue primitive.

`document_heading_measurements.sized_lines` usa oggi `round(max(sizes), 1)`, e lo
motiva: «una riga in cui una parola è più grande è governata da quella, ed è così
che si comporta la tipografia». È vero per un titolo con una parola grande; è
falso per un **capolettera**, che è un carattere solo e si prende una riga di
cinquanta.

**Misurato — il tetto della prosa prima e dopo:**

| manuale | con `max()` | con la dominante |
| --- | ---: | ---: |
| **FWK** | **58,0** | **14,0** |
| Dag | 12,1 | 12,1 |
| BoB | 10,0 | 10,0 |
| Wil | 10,3 | 12,9 |

Su FWK `prose_sizes` includeva 58,0 pt — **4 righe, mediana 53,5 caratteri, 0,00%
della massa, testo `'"S'`** — perché il capolettera si prendeva la prima riga del
paragrafo. Diventando il massimo della prosa, diventava il tetto, e sopra 58 pt
non c'era niente: zero fasce candidate.

**Il cambio va fatto in due punti, non uno.** `ir2_builder` costruisce le proprie
`SizedLine` con la stessa formula `max`. Se si cambiasse solo la misura, i livelli
sarebbero indicizzati sulle dimensioni dominanti e cercati con le massime, e non
si troverebbero. È la ragione per cui questo meccanismo richiede `check_eb.py`
vero e non la sola suite.

## 3. Meccanismo C — **il filetto di guida non è un titolo**

> Una riga che contiene una **sequenza di quattro o più caratteri non
> alfanumerici identici consecutivi** è una voce di sommario, e non è un titolo.

Quattro e non tre, perché tre punti sono i **puntini di sospensione**, che stanno
dentro una frase legittima. Il filetto di guida è una ripetizione tipografica, e
si riconosce dal carattere ripetuto, non da una lunghezza tarata.

**Misurato su BoB:** delle 19 righe promosse più lunghe di 60 caratteri, **18
sono a 12,0 pt** sulle pagine idx 6-8, cioè il sommario di apertura. Ognuna è
sola alla sua dimensione nel proprio blocco (1-4 righe per blocco), quindi passa
la regola di riga della v3; e la sua fascia `11,9-12,0` passa il filtro 3 con
rapporto **0,45** contro una soglia di 0,50.

```
'la struttura del gioco...............................11 azioni e attributi....'
'stress e trauma.................. 14 corruzione e flagelli.......16 orologi...'
'il tempo scorre................ 254 azioni campagna............... 254 avanz...'
```

**Questo non è lo stesso oggetto di A e B**, ed è dichiarato: il capolettera è un
ornamento di paragrafo, il sommario è una regione di documento. Stanno nello
stesso criterio per decisione dell'utente, con veti separati.

## 4. Il campione e le esclusioni

Popolazione: le righe che la regola promuove dopo i tre meccanismi, e quelle che
promuoveva prima. Seed **`20260902`**, già dichiarato nella v2 e mantenuto.

**Fuori**: DrM e DrW, per le ragioni di `Criterio_TitoliPerFascia_v1.md` §3.
**Dentro e da guardare**: Kul.

**Esplorazione già fatta e dichiarata** (`AGENTS.MD` §16): i numeri dei §1, §2 e
§3 sono misure fatte **prima** di questa dichiarazione, ed è il motivo per cui i
tre meccanismi sono scritti così e non altrimenti. Non ho misurato l'effetto
congiunto sull'uscita, che è ciò che i veti decidono.

## 5. Pass/fail — **un veto per meccanismo, più i tre globali**

### A. Meccanismo A — la fascia contaminata si sblocca

> Su Wil, `◈ villaggio di lala` deve essere promossa. Cade altrimenti.

È il caso su cui il veto C della v2 è caduto, ed è il bersaglio dichiarato.

### B. Meccanismo B — il tetto smette di essere un capolettera

> Su FWK il tetto della prosa deve scendere sotto i 20 pt e il manuale deve
> produrre titoli. Cade se resta a 58,0 o se FWK resta a zero.

### C. Meccanismo C — il sommario esce dai titoli

> Nessuna riga promossa deve contenere un filetto di guida, su nessun manuale.
> Verificabile a macchina.

### D. Globale — il punto fisso regge ancora

> Nessuna riga promossa ha dimensione minore o uguale al tetto della prosa, su
> nessun manuale. È il veto A della v2 e **non si indebolisce**.

### E. Globale — nessuna dimensione con due livelli

### F. Globale — regressione

> `check_eb.py` 9/10 con la sola differenza a verbale (Fab idx 126);
> `check_list_regression.py` e `check_numbered_lists.py` invariati.
> **Il meccanismo B lo richiede davvero**, perché tocca `sized_lines` e
> `ir2_builder`, che sono sulla strada dell'ordine di lettura.

### Se cade

- **A**, **B** o **C**: cade **quel** meccanismo, si riporta, e gli altri due si
  giudicano lo stesso. È la ragione per cui i veti sono separati.
- **D**: cade tutto. Il punto fisso non si negozia.
- **F**: si diagnostica prima di decidere; una regressione dell'ordine di lettura
  vale più di un titolo guadagnato.

### Il rischio dichiarato, e dove guardare

Il meccanismo A muove le fasce **in una direzione sola** — misurato su otto
manuali, sempre `scartata → candidata`, mai il contrario. Aggiunge titoli e non
ne toglie: non può far cadere D, ma **espone il giudizio sulle righe promosse**.
Le fasce che passano al pelo vanno guardate per prime:

| manuale | fascia | pagine | parole |
| --- | --- | ---: | --- |
| Wil | 13,4-14,0 | 153 | 56% → **60%** |
| Dag | 15,7-16,3 | 6 | 47% → **62%** |
| BiD | 10,4-11,0 | 254 | 36% → 76% |

## 6. Che cosa resta fuori

- **L'asse del font**, debito della v2, non ancora pagato: su Dag `PANORAMICA` a
  12,0 pt in `EvelethCleanRegular` resta sotto il tetto e resta prosa.
- **Le schede mostro**, debito aperto e dichiarato quattro volte.
- **Il capolettera come nodo semantico**: qui viene tolto dalle *statistiche*, non
  dal documento. Resta una primitiva coperta, e `AGENTS.MD` §Coverage regge.
