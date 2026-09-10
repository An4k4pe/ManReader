# Criterio — la pagina di soli spazi

Dichiarato il 10 settembre 2026, **prima** della misura che decide.

## 0. Il difetto

**Vil idx 268** (numero stampato **265**) non si rende:

```
ValueError: 1 text primitives are covered by no node
```

La pagina contiene **una sola primitiva di testo**, ed è uno **spazio**:
`' '` a 8,0 pt, bbox `(390.2, 617.9, 392.0, 627.6)`.

`ir2_builder` porta le primitive di sola spaziatura sul nodo successivo, e a fine
pagina sull'ultimo. Qui non c'è né l'uno né l'altro: la pagina non ha paragrafi.
Il codice lo dichiara e sceglie di fallire:

```python
# Se non c'e' nessun paragrafo la copertura resta scoperta, e
# **deve** farlo rumorosamente -- `ir2_validate` lo dira'.
if carried and paragraphs:
```

**Non era una svista, ed è la ragione per cui questo criterio esiste**: la scelta
va rivista, non corretta di nascosto.

## 1. Perché la scelta va rivista

Il fallimento è rumoroso **nel log** e silenzioso **nel prodotto**. Misurato
sull'uscita di Vil:

```
7044:  <!-- page:0268 -->
7054:  <!-- page:0270 -->      <- la 0269 non c'e'
```

Il markdown salta la pagina senza dirlo. `AGENTS.MD` §Coverage — «nessuna
esclusione può essere silenziosa» — è violato **dal fallimento stesso**: chi legge
il documento non vede che manca una pagina, e il numero stampato delle successive
non torna più con l'indice.

Fallire è la scelta giusta quando l'alternativa è inventare. Qui l'alternativa non
inventa niente: la pagina **è** bianca, e renderla bianca è ciò che la sorgente
dice.

## 2. La regola

> Se una pagina finisce con primitive di sola spaziatura e **nessun paragrafo che
> le accolga**, quelle primitive formano un paragrafo che le copre, il cui testo è
> quello **verbatim** delle primitive stesse.

**Emendato il 10 settembre 2026**: la prima stesura diceva «paragrafo di testo
vuoto», ed era **inapplicabile** — `ir2_model` vieta `text` vuoto («text must not
be empty»). Il testo verbatim è anche più fedele: su Vil è uno spazio, e il nodo
dice che c'è uno spazio invece di dire che non c'è niente. Il progetto trascrive,
non riassume.

Se le primitive portate avessero testo di lunghezza **zero** il nodo non si crea e
la copertura torna a fallire rumorosamente: non si inventa un carattere per far
passare un invariante.

Il nodo non stampa niente — `ir2_markdown` rende `node.text or ""` — quindi
l'uscita guadagna il commento di pagina e nient'altro, che è esattamente ciò che
una pagina bianca deve produrre.

**È il completamento minimo della regola che c'è già**, non una regola nuova: il
docstring di `ir2_builder` dice da sempre «every text primitive of a paragraph
goes into the node, including the ones whose text is empty… leaving them out would
be a silent exclusion». Oggi le spaziature viaggiano con un paragrafo vicino;
quando non ce n'è nessuno, hanno il loro.

## 3. Pass/fail

### A. Veto — la pagina si rende

> Vil deve rendere **272 pagine su 272**. Cade altrimenti.

**Emendato il 10 settembre 2026**, e la metà tolta va detta: chiedeva anche che
`<!-- page:0269 -->` comparisse nel markdown. Conflava due cose — la **copertura**
e la **mappa delle pagine nel markdown** — e la seconda non dipende da questa
correzione: `main_ir2` salta le pagine il cui corpo è tutto spazi
(`if body.strip()`), riga che esisteva già.

**E la seconda metà era sbagliata nel merito**, non solo fuori posto. Il markdown
**non è l'unico registro**: la pagina sta in `document_ir2.json` con la sua
primitiva coperta, esattamente come gli asset ricorrenti stanno in
`asset_index.csv` senza lasciare una nota nel corpo. Non è un'esclusione
silenziosa — è la stessa distinzione, già adottata altrove, fra ciò che è
**registrato** e ciò che è **reso**.

Indicazione dell'utente del 10 settembre 2026: «la pagina non è scomparsa, come
non scompaiono gli asset, sono salvati nei registri ma non renderizzati».

### B. Veto — la copertura, su tutti

> Nessuna primitiva scoperta su nessuno dei sedici manuali. `AGENTS.MD`
> §Coverage, verificabile a macchina.

### C. Veto — l'uscita non guadagna niente di visibile

> Il markdown non deve guadagnare testo visibile. Cade se la pagina bianca stampa
> qualcosa.

### D. Veto — regressione

> `check_eb.py` 9/10 con la sola differenza a verbale (Fab idx 126).

### Se cade

- **A**: la causa non era quella diagnosticata, e si ridiagnostica.
- **B**: la correzione ne ha aperta un'altra altrove.
- **C**: il nodo vuoto non è invisibile come previsto, e va reso tale o ritirato.
- **D**: si diagnostica prima di decidere.

## 4. Che cosa resta fuori

- Le pagine **senza nessuna primitiva di testo**, che non passano di qui perché
  non hanno niente da coprire.
- I quattro difetti di resa già a verbale (`GNOSI` orfano su Kul, `DEMIURGO`
  raddoppiato, l'URL di Wil, il folio fuso di FWK).
