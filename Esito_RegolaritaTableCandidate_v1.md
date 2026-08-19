# Esito di `Criterio_RegolaritaTableCandidate_v1.md` — **CADUTO**

## 1. Il verdetto

| candidato | etichetta data prima | quota campi modali | esito |
| --- | --- | --- | --- |
| DB idx 89 `x346-531` — pannello statistiche | **SCHEDA** | 100% (13 righe, tutte 1 campo) | **REGOLARE** |
| DB idx 89 `x62-249` — `D6 ATTACCO` | TABELLA | 81% | REGOLARE |
| DrM idx 86 — Devil Legate | **SCHEDA** | 46% | IRREGOLARE |
| Vil idx 222 | MISTO, non concorre | 43% | IRREGOLARE |

Il criterio §4 diceva: *«cade se anche una sola SCHEDA risulta regolare»*. La
scheda di DB misura regolare al 100%. **Il discriminante cade.**

**Candidati annidati: zero** su tutte e tre le pagine (seconda misura, senza
verdetto per costruzione).

## 2. Perché è caduto — diagnosi post-hoc, che NON ribalta il verdetto

Su DB idx 89 i campi affiancati stanno su **una sola riga di sorgente**, separati
da spazi tipografici:

```
b0002:l0000  'Ferocia: 2    Taglia: Normale'
b0003:l0000  'Movimento: 12    Armatura: —    PF: 27'
```

Su **DB p.99 — stesso manuale, stesso tipo di pannello** — `Movimento:`,
`Danno Bonus:` e `PF` sono **tre righe di sorgente distinte** (misurato nella
sessione della Milestone 38).

**Il metro è instabile sullo stesso oggetto.** Il numero di righe di sorgente per
riga visiva non misura la struttura della pagina, misura come PyMuPDF ha
raggruppato quella volta. Non è un problema della soglia: con qualunque soglia,
due pannelli identici danno 1 campo e 3 campi.

Questo invalida la metrica, non solo il suo esito. Va oltre il criterio, che
chiedeva soltanto se il discriminante reggesse.

## 3. Osservazione emersa, che NON salva questo giro

Dove i campi stanno su una riga sola, il separatore è uno **spazio tipografico**
(` ` EM SPACE, ` ` EN SPACE), che è dato di sorgente e non geometria.
Dove stanno su righe distinte, a separarli è l'interruzione di riga.

Un'unità «campo» delimitata **o** da un'interruzione di riga **o** da una corsa di
spazi tipografici sarebbe un segnale unico e derivato dalla sorgente.

**Non è una scappatoia per questo criterio**: è un meccanismo diverso, misurato su
zero pagine, e andrebbe pre-registrato e provato per conto suo. Registrarlo qui
serve a non riscoprirlo, non a salvare l'esito.

## 4. Conseguenza sulla milestone

Il meccanismo «regolarità dentro un `table_candidate`» **non apre la milestone**.

Resta valido, e non è messo in discussione da questa misura, il fatto che
`table_candidate` scatti su regolari e irregolari indistintamente — quindi il
discriminante non poteva comunque essere la sua presenza.

E resta l'ispezione visiva che precede: su tre manuali le schede hanno **tre
forme che non si somigliano** (incorniciata; fascia tinta senza cornice; pila di
barre-titolo con tabelle). La categoria unica non ha ancora una base osservata.

## 5. Limite già dichiarato prima della misura

Tre pagine, tre manuali. Non è un campione. Il limite valeva per confermare e vale
per smentire: questa misura dice che il meccanismo non regge **su queste tre
pagine**, non che nessun meccanismo possa reggere.
