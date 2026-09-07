# Esito di `Criterio_TitoliPerFascia_v2.md` — **il punto fisso tiene, il capolettera no**

**Stato in una riga**: il veto **A** passa su otto manuali su otto e il **D**
pure; il veto **C** **cade su Wil**, e FWK produce **zero** titoli. Entrambe le
cadute hanno **una sola causa**, e non sta né nel punto fisso dell'utente né
nell'architettura a fasce: sta nel **capolettera**.

---

## 1. Veto A — il punto fisso. **Passa, 8 su 8**

> Cade se una sola riga promossa ha dimensione minore o uguale al tetto della prosa.

| manuale | tetto | righe promosse | al tetto o sotto |
| --- | ---: | ---: | ---: |
| Dag | 12,1 | 93 | **0** |
| Fab | 14,0 | 103 | **0** |
| BoB | 10,2 | 777 | **0** |
| BiD | 9,5 | 606 | **0** |
| Wil | 10,3 | 618 | **0** |
| FWK | 58,0 | 0 | **0** |
| Apo | 12,0 | 66 | **0** |
| Vil | 12,0 | 92 | **0** |

«Ciò che è prosa non è mai un titolo» regge senza eccezioni. È l'indicazione
dell'utente del 2 settembre 2026, ed è la parte del meccanismo che si può
considerare acquisita.

## 2. Veto D — nessuna dimensione con due livelli. **Passa, 8 su 8**

Zero dimensioni con due livelli su tutti i manuali.

**Una distinzione che va scritta perché non si confondano due cose.** Contando i
*testi* che escono a livelli diversi, BoB ne ha 19 e BiD 12 — ma sono legittimi:
`DOVERI` compare una volta come capitolo e una volta nel sommario, a **dimensioni
diverse**. Non è instabilità del meccanismo, che lavora su dimensione→livello ed
è quello che il veto D misura.

## 3. Il tetto che accorpa. **Recupera ciò che la v1 buttava**

| manuale | v3 | v1 (scarta) | **v2 (accorpa)** |
| --- | ---: | ---: | ---: |
| BoB | 1086 | 229 | **743** |
| BiD | 1164 | 68 | **592** |
| Wil | 1293 | 100 | **524** |
| Vil | — | 82 | **90** |
| Dag | 2035 | 50 | **93** |
| Fab | — | 88 | **88** |
| Apo | 81 | 66 | **66** |
| FWK | 394 | 100 | **0** |

Il difetto A della v1 è chiuso. Che la v2 resti sotto la v3 è atteso e voluto: il
numero della v3 era gonfiato dall'instabilità, e su Dag comprendeva **188
occorrenze di `CARATTERISTICHE`**, che è l'etichetta di un campo di scheda.

## 4. Veto C — **cade su Wil**

L'elenco completo delle sedici righe **non è conservato nel repo**:
`Esito_Titoli_v1.md` ne nomina quattro, e una (`KINGFISSURE WORM`, DrM) è fuori
campione. Il veto è quindi verificato su **quattro casi nominati, non sedici**, e
va letto sapendolo.

| riga | manuale | esito |
| --- | --- | --- |
| `ALLEVIARE LO STRESS` | BiD | **promossa** |
| `RECUPERARE` | BiD | **promossa** |
| `QUANDO IL DISASTRO È IMMINENTE` | Dag | 11,0 pt, **sotto** il tetto 12,1 — costo dichiarato |
| `PIOGGIA DI POZIONI` | Fab | 10,0-11,0 pt, **sotto** il tetto 14,0 — costo dichiarato |
| `◈ villaggio di lala` | Wil | 20,0 pt, **sopra** il tetto 10,3, non promossa — **CADE** |

Il §4 della v2 dice: «**C** sopra il tetto: cade». Cade.

## 5. La causa, ed è **una sola** per entrambe le cadute

### Wil — il capolettera contamina la fascia

La riga esiste, è a 20,0 pt, è sopra il tetto, ed è **sola alla sua dimensione
nel suo blocco**: la regola di riga la promuoverebbe. Non lo fa perché la sua
**fascia** è stata scartata prima.

```
fascia 19.8-21.0   298 pagine   33% parole   ->  scartata dal filtro 2
   228 testi sono parole      'LA PISTA', 'LA CACCIA', 'villaggio di lala'
   457 testi NON sono parole  'C' x50, 'S' x30, 'M' x24, 'L' x23, 'G' x14...
   font delle non-parole: IM_FELL_English_Roman-SC (241), Zedou-Bold (215)
```

Sono **capolettera**: lettere singole maiuscole in due facce da display, alla
stessa dimensione dei nomi di insediamento. Il filtro 2 si calcola **sulla
fascia**, quindi una fascia che mescola titoli veri e ornamento viene scartata
**per intero**, e con essa i titoli.

### FWK — lo stesso capolettera, sull'altro estremo

```
prose_sizes include 58.0 pt   4 righe   mediana 53.5   massa 0.00%   testo: '"S'
```

Un capolettera a 58 pt. La sua «riga» risulta lunga perché il capolettera si
raggruppa col paragrafo che apre, quindi `prose_sizes` lo classifica come prosa e
`max()` lo elegge a **tetto**. Sopra 58 pt non c'è niente: **zero fasce
candidate, zero titoli**.

**E questa non è coperta dall'eccezione del veto C.** Quell'eccezione conta come
debito del font le righe «sotto il tetto della prosa», e la sua giustificazione è
la decisione dell'utente — *la prosa non è mai titolo*. Su FWK 58 pt **non è
prosa**: è un errore di misura. Usare l'eccezione lì sarebbe far passare il
criterio con la propria scappatoia, ed è esattamente il salvataggio che
`CLAUDE.md` vieta.

## 6. Che cosa è caduto, e che cosa no

**Non è caduto** il punto fisso (veto A, 8 su 8), non è caduta l'architettura a
fasce, non è caduto il tetto che accorpa, non è caduto il corpo per massa.

**È caduto un presupposto implicito che nessuna delle due versioni ha mai
dichiarato**: che ogni primitiva di testo appartenga al testo della propria
dimensione. Il capolettera no. È un ornamento tipografico che appartiene al
paragrafo che apre, e finché viene contato come testo della sua dimensione
avvelena **due** statistiche diverse — la quota di parole della fascia e
l'insieme della prosa.

`redrawn_duplicates` in `ir2_builder` risolve un problema della stessa famiglia
per i ridisegni. Il capolettera non ha ancora il suo meccanismo.

## 7. Che cosa non è stato eseguito

- **Veto B** (giudizio riga per riga): **eseguito il 7 settembre 2026**, dopo che
  il meccanismo era stato adottato attraverso `Criterio_TettoDallaMassa_v1`.
  Campione di **45 righe promosse**, cinque per manuale su nove, seed
  `20260902`, con indice posizionale e numero stampato.

  **Esito: 42 titoli su 45.** Le tre bocciate dall'utente:

  | # | manuale | riga | attribuzione |
  | --- | --- | --- | --- |
  | 21 | Wil | `https://grumpybearstuff.com/pregenerati-wilderfeast/` | **pre-esistente** |
  | 25 | Wil | `ACUME: (Costo: 1 Successo) Definisci un dettaglio…` | **pre-esistente** |
  | 26 | FWK | `ave ai vittoriosi morti! di nathan d. paoletta 58` | **nuova** |

  **L'attribuzione viene dal delta di `Esito_TettoDallaMassa_v1.md` §3**, non da
  una stima: su Wil le regole adottate hanno prodotto **zero entrate** (618 → 596,
  22 uscite), quindi 21 e 25 erano promosse anche prima. Su FWK **tutte le 100**
  righe sono entrate, perché prima il manuale ne produceva zero: la 26 è
  attribuibile.

  **E la 26 non è una promozione sbagliata**: `ave ai vittoriosi morti! di nathan
  d. paoletta` **è** un titolo, con il **numero di pagina fuso in coda**. Il
  difetto sta nel testo della riga, non nella decisione di promuoverla, ed è la
  stessa classe di `'benvenuti nel Kosmohedron 10'` già a verbale.

  **Alla lettera il veto cade** — dichiarava «una sola riga promossa che non è un
  titolo» — e si riporta così. Nella forma emendata, che giudica il delta, resta
  **un caso su 45**, ed è un difetto di composizione del testo.

  Segnalata dall'utente anche la **44**, `ANGELI ANGELI CADUTI CADUTI` su Kul:
  giudicata **titolo, ma ripetuto**. È il difetto del testo raddoppiato, come
  `'Valois Valois'`, e non riguarda la promozione.

- **Veto E** (`check_eb.py`): non lanciato, per la stessa ragione della v1 —
  un'ora e venti di macchina su un meccanismo non adottato.

## 8. Stato del codice

`document_heading_band_policy` implementa la v2 e resta in albero: la parte
confermata è quella che serve al passo successivo. **1628 test verdi**, ruff
pulito. Il collegamento è attivo, quindi in questo stato FWK esce senza titoli.
