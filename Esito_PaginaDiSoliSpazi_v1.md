# Esito di `Criterio_PaginaDiSoliSpazi_v1.md` — **passa, dopo due emendamenti**

Scritto il 10 settembre 2026.

## 0. Stato in una riga

**Vil rende 272 pagine su 272**, per la prima volta da quando il difetto è stato
trovato l'8 settembre. La correzione è di cinque righe; il contenuto del giro sono
i **due emendamenti**, perché la prima stesura era inapplicabile e il veto
principale era in parte sbagliato nel merito.

## 1. I veti

| veto | esito |
| --- | --- |
| **A** — la pagina si rende | **passa**: Vil 272/272 |
| **B** — la copertura su tutti | **passa**: 1646 test verdi, nessuna pagina caduta |
| **C** — niente di visibile in uscita | **passa** |
| **D** — `check_eb.py` | **9/10**, sola Fab idx 126 già a verbale |

## 2. Il difetto, e perché la scelta precedente andava rivista

Vil idx 268 (stampata **265**) contiene **una sola primitiva di testo**, ed è uno
spazio: `' '` a 8,0 pt. `ir2_builder` porta le spaziature sul nodo successivo e a
fine pagina sull'ultimo; qui non c'era né l'uno né l'altro, e il codice sceglieva
di fallire — **dichiarandolo**: «se non c'è nessun paragrafo la copertura resta
scoperta, e **deve** farlo rumorosamente».

Non era una svista, quindi non è stata corretta di nascosto. È stata **rivista**,
e la ragione è che il rumore era nel posto sbagliato: il fallimento si sentiva nel
**log** e non nel **prodotto**. Il markdown passava da `page:0268` a `page:0270`
senza dirlo, e la pagina spariva dall'IR insieme al suo contenuto.

Fallire è giusto quando l'alternativa è inventare. Qui non si inventa: la pagina
**è** bianca, e renderla bianca è ciò che la sorgente dice.

## 3. Primo emendamento — la regola era inapplicabile

La prima stesura diceva «un **paragrafo di testo vuoto** che le copre».
`ir2_model` lo **vieta**: «text must not be empty».

La regola emendata: il testo del nodo è quello **verbatim** delle primitive che
copre. Su Vil è uno spazio.

**È anche più fedele**, e regge indipendentemente dall'esito: un nodo con testo
vuoto affermerebbe che lì non c'è nulla, mentre c'è una primitiva con un
carattere. Il progetto trascrive, non riassume.

**Una guardia non dichiarata è stata aggiunta e va detta**: se le primitive
portate avessero testo di lunghezza **zero**, il nodo non si crea e la copertura
torna a fallire rumorosamente. Non si inventa un carattere per far passare un
invariante, e quel caso resta fuori.

## 4. Secondo emendamento — il veto A conflava due cose, e una era sbagliata

Il veto A chiedeva anche che `<!-- page:0269 -->` comparisse nel markdown. **Non
dipende da questa correzione**: `main_ir2` salta le pagine il cui corpo è tutto
spazi (`if body.strip()`), riga che esisteva già. Prima la pagina mancava perché
falliva, dopo manca perché è bianca.

**E la richiesta era sbagliata nel merito.** Il markdown **non è l'unico
registro**: la pagina sta in `document_ir2.json` con la sua primitiva coperta,
esattamente come gli asset ricorrenti stanno in `asset_index.csv` senza lasciare
una nota nel corpo. Non è un'esclusione silenziosa — è la distinzione, che il
progetto fa già altrove, fra ciò che è **registrato** e ciò che è **reso**.

Indicazione dell'utente del 10 settembre 2026: «la pagina non è scomparsa, come
non scompaiono gli asset, sono salvati nei registri ma non renderizzati».

Il mio inquadramento — «un buco nella mappa delle pagine» — dava per scontato che
il markdown fosse la mappa. Non lo è.

## 5. Che cosa resta aperto

- **La riga `if body.strip()`** in `main_ir2` resta com'è, per decisione: le
  pagine bianche non compaiono nel markdown e stanno nell'IR.
- I quattro difetti di resa già a verbale: `GNOSI` orfano su Kul, `DEMIURGO`
  raddoppiato, l'URL promosso su Wil, il folio fuso su FWK.
- **La collisione delle Milestone 42** fra questo ramo e quello delle schede.
