# Esito di `Criterio_Titoli_v2.md` — **zero falsi positivi, cinque titoli mancati**

**Stato in una riga**: su 16 righe promosse **nessuna** è stata giudicata «non
titolo»; su 16 scartate **cinque erano titoli**. Il veto §4.A è a zero in
entrambe le direzioni e **cade** sulla seconda. Il criterio **non è scaricato**.

---

## 1. Il confronto

| | |
| --- | ---: |
| righe promosse | 16 |
| **promosse ma non erano titoli** | **0** |
| righe scartate | 16 |
| **scartate ma lo erano** | **5** |
| incerte | 1 |

## 2. La direzione che regge

**Nessun falso positivo.** Le 16 promosse sono nomi di abilità (`PIOGGIA DI
POZIONI` su Fab), intestazioni di riquadro (`◈ VILLAGGIO DI LALA` su Wil),
titoli di scheda (`KINGFISSURE WORM` su DrM), nomi di insediamento su FWK.

**E le 11 «non titolo» fra le scartate sono tutte giuste.** L'etichettatore ha
osservato che stanno tutte in **un solo manuale** e in **due sole forme**: celle
della barra caratteristiche e righe di esito col badge di fascia — cioè la
**scala di valori** che `Criterio_ScalaDiValori_v1.md` ha già isolato. La regola
dei titoli le scarta tutte, ed è il comportamento voluto: su DrM 290 righe su 343
sopra la prosa vengono scartate.

## 3. La direzione che cade, e la causa è **una sola**

| riga | manuale | idx | testo |
| --- | --- | ---: | --- |
| 10 | Lan | 211 | `PISTOLA CATALITICA` |
| 14 | Dag | 186 | `QUANDO IL DISASTRO È IMMINENTE` |
| 19 | Lan | 213 | `ABITACOLO CAPOVOLTO` |
| 20 | BiD | 165 | `ALLEVIARE LO STRESS` |
| 24 | BiD | 164 | `RECUPERARE` |

Quattro su cinque falliscono per la **stessa ragione**, verificata:

```
Lan  'PISTOLA CATALITICA'              blocco di  3 righe, contiene prosa 9.0
Dag  'QUANDO IL DISASTRO È IMMINENTE'  blocco di 10 righe, contiene prosa 9.0 e 9.1
BiD  'ALLEVIARE LO STRESS'             blocco di  9 righe, contiene prosa 9.5 e 9.6
BiD  'RECUPERARE'                      blocco di 22 righe, contiene prosa 9.4 e 9.5
```

> **Il backend mette il titolo nello stesso blocco della prosa che introduce.**
> Le condizioni 2 e 3 del §1 — «il blocco non contiene prosa» e «al più due
> righe» — allora lo scartano.

**È la seconda volta che il blocco costa un meccanismo.** Sugli elenchi la
condizione «due righe nello stesso blocco» aveva fatto cadere la v1 del criterio,
perché su DB ogni voce è un blocco a sé; qui il difetto è il rovescio — il blocco
è troppo grande invece che troppo piccolo — e la causa è la stessa: **il blocco
di PyMuPDF non corrisponde a un'unità del documento**, e in entrambe le direzioni.

**Non è stato ritoccato**, come il criterio impone: «se cade verso "scartata e lo
era", si riporta quanto manca».

## 4. Due difetti del materiale, entrambi trovati da chi giudicava

**Gli estratti erano troppo corti.** Rilievo dell'utente: cinque righe di contorno
non bastano a dire se qualcosa è un'intestazione, perché quello lo dice **cosa le
sta sotto**. Il materiale è stato rifatto con la **pagina intera** — 24 pagine con
la resa completa che lo script produce oggi.

**E il contorno puntava alla riga sbagliata.** Rilievo dell'etichettatore, che
l'ha verificato su tre righe: la ricerca del testo nella resa trovava la **prima
occorrenza della stringa** nel documento, non il punto da cui la riga proviene. Su
Lan il contorno mostrava la banda `LICENZA II` invece della banda `PUNIZIONE`; su
riga 24 un paragrafo che la stringa non conteneva affatto.

> **Il verdetto regge lo stesso**, e va detto perché: l'etichettatore ha
> dichiarato di aver giudicato **sui render di pagina**, usando il contorno solo
> come indizio debole. La prova su cui ha deciso è l'immagine, che è la più forte
> disponibile.

Ma è un difetto mio da non ripetere, ed è il secondo giro di fila in cui il
materiale è più debole del giudizio: il giro precedente mostrava le voci troncate
a fine riga fisica.

## 5. La dispersione, che il §4.B obbliga a riportare

| manuale | promosse | scartate |
| --- | ---: | ---: |
| **DrM** | 53 | **290** |
| Wil | 53 | 23 |
| Fab | 48 | 8 |
| DB | 36 | 15 |
| DrW | 31 | 1 |
| Kul | 17 | 6 |
| **Apo** | **3** | 4 |
| **Vil** | **3** | 0 |

801 righe sopra la prosa in tutto. **DrM da solo ne fa 343**, e ne scarta 290:
sono le righe di scheda, e il giudizio conferma che scartarle è giusto.

La forbice fra Vil (3) e DrM (53) promosse non è un difetto: sono manuali fatti
diversamente. Ma va riportata, perché una media di 50 titoli per manuale non
direbbe niente di nessuno dei due.

## 6. L'incerta, e il canale che stavolta ha funzionato

Riga 26, DB: `PERMANENZA` compare due volte sulla pagina — come intestazione di
un incantesimo, e come rimando in maiuscolo dentro la prosa di un altro. Le due
forme sono identiche nel testo, e dal render non si può stabilire quale delle due
sia la riga estratta.

**È l'uso giusto di `incerto`**, ed è la prima volta in quattro giri che la
riserva arriva come etichetta invece che come frase accanto a un'etichetta netta.
Il rinforzo del protocollo — «una riserva scritta accanto a un'etichetta netta
viene contata come `incerto`» — ha funzionato.

Nota che l'ambiguità è **anche** un difetto del materiale: se il contorno avesse
puntato alla riga giusta, quella voce sarebbe stata decidibile.

## 7. Conseguenza

Come i numerati: la regola è **sicura ma stretta**. Non sbaglia mai nella
direzione che rovina il testo — promuovere prosa a titolo — e ne manca circa un
quarto.

Su 16 promosse e 21 titoli veri nel campione, la copertura è **76%**; la
precisione è **100%** su 16, che al 95% mette il tasso d'errore sotto il **17%**,
non a zero.

**Che cosa sbloccherebbe le cinque mancate**: il titolo va riconosciuto anche
quando sta nello stesso blocco della sua prosa, cioè guardando la **riga** e non
solo il blocco. Il segnale c'è già — quelle righe sono più grandi della prosa e
sole sulla loro riga — ma serve un criterio, perché allargare così tocca la
condizione che oggi dà zero falsi positivi.

## 8. Verifiche

Suite **1457** test, un solo fallimento, quello ambientale già a verbale. Le
barre di regressione degli elenchi e dei numerati danno lo stesso risultato di
prima: i titoli non le peggiorano.

**Il giudizio dell'utente sulle 24 pagine intere è in corso** e non è in questo
verbale. Se contraddice questo, vale quello: è fatto sul materiale che questo
esito dichiara migliore.
