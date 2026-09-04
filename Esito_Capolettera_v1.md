# Esito di `Criterio_Capolettera_v1.md` — **C regge, A cade, B è uno scambio**

Scritto il 3 settembre 2026, dopo le misure e dopo `check_eb.py`.

## 0. Stato in una riga

Il meccanismo **C** passa pulito. Il meccanismo **A** cade, e la causa è un mio
errore d'ambito, non un difetto del meccanismo. Il meccanismo **B** passa il veto
che gli ho dichiarato, ma il veto era **incompleto**: cura FWK e rompe Fab, e non
avevo dichiarato niente che potesse accorgersene.

`check_eb.py`: **9 su 10**, unica differenza Fab idx 126, già a verbale
(`Criterio_ConfrontoEB_v4.md` §4). Nessuno dei meccanismi ha riordinato o perso
testo. **1643 test verdi**, ruff pulito.

## 1. Meccanismo C — il filetto di guida. **Passa.**

> Veto: nessuna riga promossa deve contenere un filetto di guida, su nessun
> manuale.

**Zero filetti su otto manuali su otto.** Le voci di sommario di BoB —
`la struttura del gioco...............................11` — non escono più come
titoli. Nessun effetto collaterale misurato: è l'unico dei tre che tocca una sola
popolazione e la tocca tutta.

La soglia di quattro caratteri identici regge sulla prova che la motiva: i
puntini di sospensione sono tre e restano dentro le frasi.

## 2. Meccanismo A — chi non può essere titolo non vota. **Cade.**

> Veto: su Wil `◈ villaggio di lala` deve essere promossa.

**Non è promossa.** La fascia `19,8-21,0` resta al **52%** di parole contro una
soglia del 60%, ed è esattamente il numero che avevo previsto per «tolti i soli
caratteri singoli». La seconda esclusione — l'arredo — **non ha tolto niente**.

**La causa è un errore d'ambito, ed è mio.** L'arredo trova numeri di pagina e
testatine dalla ricorrenza nella stessa posizione fra pagine vicine: è un fatto
di **finestra**. L'ho interrogato sulle 316 pagine in blocco. Misurato, stessa
funzione e stesso manuale:

| ambito | slot trovati | primitive escluse |
| --- | --- | ---: |
| finestra 20 pagine (idx 100) | ricorrenza 2, sequenza 2 | **20** |
| finestra 20 pagine (idx 140) | ricorrenza 2, sequenza 2, testatine 2 | **20** |
| finestra 20 pagine (idx 180) | ricorrenza 1, sequenza 1 | **8** |
| **documento intero (316 pagine)** | **tutti zero** | **0** |

È l'errore contro cui `Criterio_AmbitoDeiFatti_v2.md` mette in guardia: la
finestra dei fatti **si sposta, non si allarga**.

**Non è una smentita dell'ambito documento per i titoli**, che resta e regge: il
tetto e la mappa dimensione→livello sono uno per manuale, ed è ciò che ha ucciso
le 241 occorrenze difformi di Dag. È che **una statistica di documento aveva
bisogno di un dato per pagina**, e sono andato a prenderlo all'ambito sbagliato.

**Da dove riprenderlo**: raccogliere l'arredo finestra per finestra, come già fa
la pipeline, aggregarlo per pagina, e passare *quell'insieme* alla statistica di
documento. Decisione a documento, ingresso a finestra. Il parametro
`excluded_primitive_ids` e `document_furniture_primitive_ids` **restano in
albero**, taggati con questa misura sopra.

## 3. Meccanismo B — la riga va alla dimensione che la porta. **Passa il veto, ma il veto era incompleto.**

> Veto: su FWK il tetto deve scendere sotto i 20 pt e il manuale deve produrre
> titoli.

**Passa**: tetto da 58,0 a 14,0, da **0 a 99 titoli**. Il capolettera ha smesso di
prendersi la riga del paragrafo.

**Ma tocca tre manuali su otto, e su uno è una regressione.** Confronto fra i due
giri di produzione, entrambi a log:

| manuale | tetto v2 (massima) | tetto finale (dominante) | titoli | esito |
| --- | ---: | ---: | --- | --- |
| **FWK** | **58,0** | **14,0** | 0 → **99** | guarito |
| **Fab** | **14,0** | **10,3** | 88 → **626** | **rotto** |
| **Wil** | 10,3 | **12,9** | 524 → **235** | da giudicare |
| Dag | 12,1 | 12,1 | 93 → 93 | invariato |
| BoB | 10,2 | 10,2 | 743 → 775 | invariato |
| BiD | 9,5 | 9,5 | 592 → 582 | invariato |
| Apo | 12,0 | 12,0 | 66 → 66 | invariato |
| Vil | 12,0 | 12,0 | 90 → 90 | invariato |

Su Fab, abbassando il tetto da 14,0 a 10,3, entrano fra i candidati le fasce di
**prosa da display**: 25 righe promosse più lunghe di 60 caratteri, fra cui un
paragrafo di **314** e le citazioni d'apertura.

```
h3 len=314  'Fabula Ultima è il Gioco di Ruolo da tavolo ispirato ai JRPG…'
h3 len= 90  'Questo è un racconto di eroi e tenebre. Di grande speranza…'
h3 len= 53  'Il potere senza armonia conduce solo alla sofferenza.'
```

## 4. I tre errori della mia dichiarazione, a verbale

**Primo: la tabella del §2 non conteneva Fab.** Ho dichiarato l'effetto del
meccanismo B sul tetto misurandolo su quattro manuali, e Fab — l'unico su cui si
rompe — non era fra quelli. Non è un caso che sia sfuggito: Fab è anche l'unico
senza un giro «v3» di confronto, quindi era già fuori da un altro paragone.

**Secondo: al meccanismo A non ho dato un veto di giudizio.** Nel §5 ho *scritto*
il rischio — «aggiunge titoli e non ne toglie, quindi espone il giudizio sulle
righe promosse» — e poi gli ho dato solo un veto di bersaglio. Sia la v1 sia la
v2 avevano il veto «una sola riga promossa che non è un titolo lo fa cadere», e
l'ho lasciato cadere proprio nel giro in cui serviva.

**Terzo: ho attribuito la regressione di Fab al meccanismo sbagliato.** Ho
riferito che il salto 88 → 631 veniva dal meccanismo A. Ritirando A, Fab è
rimasto a **626**: veniva da B. Me ne sono accorto solo perché il giro finale
aveva un numero che non tornava.

Nessuno dei tre si emenda qui: si riportano, e il criterio successivo li eredita
come vincoli.

## 5. Che cosa è adottato e che cosa no

- **C: adottato.**
- **A: ritirato**, codice scollegato e taggato col punto da cui riprendere.
- **B: non deciso.** Passa il suo veto, ma è uno scambio — un manuale curato
  contro uno rotto, dalla stessa riga di codice — e chi lo decide deve saperlo.

**Perché B non lo decido da solo.** Le due strade non si equivalgono: tenerlo
guarisce un manuale che oggi produce **zero** titoli e ne peggiora uno che ne
produce già 88 di buoni; toglierlo lascia FWK a zero. È una scelta sul prodotto,
non sul meccanismo, e il verbale non ha un criterio dichiarato per farla.

## 6. Che cosa resta fuori

- **L'asse del font**, debito della v2, non pagato: su Dag `PANORAMICA` a 12,0 pt
  in `EvelethCleanRegular` resta sotto il tetto e resta prosa.
- **Le schede mostro**, debito aperto e dichiarato cinque volte.
- **Il difetto di copertura di Vil idx 268** (numero stampato 265), pre-esistente
  e verificato tale.
