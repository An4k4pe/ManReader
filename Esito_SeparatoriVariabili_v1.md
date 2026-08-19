# Esito di `Criterio_SeparatoriVariabili_v1.md` — **CADUTO**

Secondo tentativo sul discriminante tabella/scheda. Anche questo cade, e cade sul
caso che era stato aggiunto apposta per metterlo alla prova.

## 1. Il verdetto

| regione | etichetta data prima | righe con separatore | quota cluster modale | esito |
| --- | --- | --- | --- | --- |
| DB idx 89 — pannello FANTASMA | **SCHEDA** | 2 / 13 | 50% | VARIABILE ✔ |
| DB idx 89 — `D6 ATTACCO` | **TABELLA** | 6 / 27 | 83% | ALLINEATO ✔ |
| DrM idx 86 — Devil Legate | **SCHEDA** | 19 / 28 | 32% | VARIABILE ✔ |
| **DB idx 98 — GUERRIERO/ARCIERE/CAMPIONE** | **SCHEDA** | 4 / 16 | 75% | **ALLINEATO ✘** |
| Vil idx 222 | MISTO, non concorre | 8 / 14 | 75% | ALLINEATO |

Il §4 diceva: *«cade se anche una sola SCHEDA risulta allineata»*. DB idx 98 lo è.
**Cade.**

## 2. Cade dove era stato progettato per cadere

DB idx 98 era stata aggiunta **prima** di misurare, come **controcaso** di DB idx
89: stesso manuale, stesso tipo di pannello, raggruppamento di sorgente opposto.
Il criterio §5 diceva: *«se il segnale è stabile deve dare lo stesso esito sulle
due»*.

Danno esiti **opposti**: VARIABILE e ALLINEATO.

Quindi non è che il segnale sia debole — **non è invariante rispetto a come
PyMuPDF raggruppa il testo**, che è la stessa causa per cui era caduto il primo
criterio, ricomparsa in una forma che era stata progettata per esserne immune. La
riformulazione non ha rimosso la dipendenza, l'ha spostata.

## 3. Debolezza del metro, che non cambia il verdetto ma va scritta

Le righe che contengono un separatore sono **2 su 13** su DB idx 89 e **4 su 16**
su DB idx 98. Le percentuali sono quindi «un mezzo» e «tre quarti»: con basi così
il metro è fragile a prescindere dall'esito.

Questo indebolisce anche i due esiti che **tornavano**: il VARIABILE di DB idx 89
poggia su due righe.

L'unica misura con una base decente è DrM (19 righe su 28), e quella torna.

## 4. Conseguenza, e cosa NON si fa

Il §6 del criterio diceva: *«Se cade, la milestone non si apre e la terza
formulazione non si cerca dentro questo giro.»*

La milestone **non si apre**. Non si propone una terza formulazione qui.

**Cosa insegnano i due giri messi insieme.** Il primo contava le righe di sorgente
per riga visiva; il secondo guardava dove cadono i separatori. Sono caduti per la
stessa ragione: **entrambi i segnali dipendono da come la cattura ha raggruppato
il testo**, e quel raggruppamento cambia fra due pannelli identici dello stesso
manuale.

Ne segue un fatto che vale oltre questa milestone e che non era stato formulato
così: **al livello dei candidati, la differenza fra una tabella e una scheda non è
stata trovata con nessuno dei segnali disponibili**. Non che non esista — che due
tentativi pre-registrati non l'hanno vista.

## 5. Limiti dichiarati prima, validi anche per smentire

Quattro regioni utili, tre manuali. Non è un campione. Questo dice che i due
meccanismi provati non reggono **su queste pagine**, non che nessun meccanismo
possa reggere.
