# Criterio — il marcatore si toglie **per primitiva**, non per posizione

**Non è un meccanismo nuovo**: è la chiusura di un buco in quello spedito. Non
cambia cosa viene riconosciuto elenco; cambia solo che cosa la resa può togliere.

## 0. Il buco

`Criterio_MarcatoreDaFont_v1.md` ha aperto la via del **font**: un carattere
alfanumerico è marcatore se la sua primitiva è **il solo carattere** in un font
diverso dal corpo. La condizione «primitiva sua» sta a monte, nella misura.

`ir2_markdown.render_list_item` toglieva il marcatore **per posizione**:

```python
dropped = len(node.text) - len(strip_marker(node.text, markers))
```

I caratteri non sanno in che font stanno. Su Fab, pagina stampata 171 — la
tabella dei nomi — con `O` ammessa marcatore in `oldretrolabelstfb` la resa
diceva:

```
- de          ← Ode          in PTSans-Narrow, il font del corpo
- livia       ← Olivia
- inter       ← Winter
```

Non è una classificazione sbagliata: è **contenuto distrutto**, contro il primo
invariante del progetto.

**Ed è latente, non innocuo.** Misurato sul codice spedito, 673 voci su 16
manuali: **zero** lettere perse. I marcatori alfanumerici che la v1 ammette —
`w` su Fab, `x` `á` `é` `í` su DrW, `R` su DrM — stanno tutti in font di simboli
e sono primitive loro. La garanzia regge **per l'alfabeto**, non per costruzione:
`w` in venti pagine di italiano compare 25 volte.

Rilievo dell'utente, ed è quello che ha trovato il caso: «le `O` di Fab sono lo
stesso font del resto… se una lettera deriva da un font simbolico invece sì».

## 1. La regola

> Un marcatore **non alfanumerico** si toglie sempre: un `✦` dentro la primitiva
> del testo è comunque un pallino — `✦Effetto Pieno:` su DB, già a verbale.
>
> Un marcatore **alfanumerico** si toglie **solo se la prima primitiva del nodo è
> esattamente quel carattere**. Altrimenti è una lettera, e resta.

È la stessa condizione di `_is_a_glyph_marker`, che decide la candidatura.
L'unica cosa che cambia è che ora vale **anche dove si toglie**: erano due
decisioni sullo stesso fatto, e una delle due non lo guardava.

## 2. Il contratto

> `NodeIR2` porta un campo nuovo, `marker: str | None`: **il prefisso che la resa
> può togliere**, o `None` se non c'è niente da togliere o se toglierlo
> distruggerebbe contenuto.

Additivo come `heading_level`, e con la stessa forma di validazione: se c'è, dev'essere
un **prefisso di `text`** e il nodo dev'essere una voce d'elenco. Uno stato che
non significa niente non è rappresentabile.

**Il marcatore continua a uscire dalla resa e non dall'IR**: `node.text` conserva
tutto. Ciò che cambia è che la decisione si prende **dove le primitive ci sono**,
nel costruttore, invece di essere indovinata a valle dai soli caratteri.

E `render_list_item` perde il parametro `markers`: non gli serve più. Non doveva
servirgli nemmeno prima — è il nodo che sa com'è fatto.

## 3. Pass/fail

Non c'è verdetto da dare e non c'è campione: è una correzione, e le sue barre
sono di regressione.

### A. Niente cambia su ciò che è spedito

> Con i marcatori spediti, la resa di **ogni** voce dei sedici manuali dev'essere
> identica a prima.

**Misurato: 673 voci, 0 rese cambiate.**

### B. Il caso che l'ha imposta

> Sulle primitive vere di Fab pagina 172, con `O` fra i marcatori, i nomi devono
> restare interi.

**Misurato: 8 righe cambiano, tutte nel verso giusto** — `de`→`Ode`,
`livia`→`Olivia`, `inter`→`Winter`.

### C. I test nascono falliti

> Il test del caso Fab deve fallire sul codice di prima.

Verificato: `strip_marker("Olivia", {"O"})` torna `"livia"`.

## 4. Che cosa resta fuori, e va detto

**Il confronto di conservazione E-B è ancora cieco allo stesso modo.**
`prototype_ir2_page._normalised_sequence` toglie i marcatori dichiarati da
**entrambi i lati**, per carattere e su tutto il documento — l'emendamento del
`Criterio_Elenchi_v1.md` §5.E. Ammessa `O`, ogni `O` sparisce da tutt'e due i
lati e il confronto passa qualunque cosa succeda all'uscita:

```
marcatori spediti   Fab  0,1%   DrM 0,6%   DrW 0,5%   dei caratteri tolti dal confronto
```

Oggi è poco, per la stessa ragione per cui il danno era latente. Ora che il nodo
**dichiara** il suo marcatore, il confronto potrebbe togliere quello invece che
ogni occorrenza del carattere. **Non lo faccio in questo giro**: è un secondo
emendamento a un criterio diverso, e va dichiarato prima come questo.

**E non riapre la questione dei marcatori.** Che `h` di Vil debba diventare un
marcatore resta una decisione a parte, con le sue condizioni da dichiarare.
Questa correzione toglie **uno** dei suoi costi, non la decide.
