# Criterio di accettazione — la subordinazione si decide sui probatori

Scritto **prima** dell'implementazione, come i tre criteri precedenti di questa
sessione. È il primo che tocca **`column_band` stesso**
(`scripts/prototype_derived_column_bands.py`) e non la diagnostica intorno:
finora in questa sessione quel file non era stato modificato, e l'ultimo commit
che lo tocca è `619f4f8`, precedente alla sessione.

---

## 1. Il cambio, in una condizione

`_is_subordinate(inner, outer)` decide se `inner` viva dentro una colonna di
`outer`, con tre condizioni. La terza usa lo **span**:

```python
return inner.span_y0 < outer.span_y1 and outer.span_y0 < inner.span_y1
```

Passa agli estremi **probatori** (`y0`/`y1`), che sono gli stessi già usati
dalla seconda condizione — oggi la funzione misura la stessa cosa in due modi
diversi al proprio interno.

**Perché**: `span_y0`/`span_y1` dicono fin dove si **presume** che la
separazione continui; `y0`/`y1` dicono dove è **dimostrata**, cioè dove
entrambi i lati sono attivi. Una claim strutturale — «questa struttura sta
dentro quella» — deve poggiare sulla dimostrazione. È la stessa separazione che
`_GapRect` già documenta e che State.md:94 impone ai criteri di ammissione, non
una regola nuova.

Nient'altro cambia: né i criteri di ammissione, né `_segment_bands`, né il
minimo di larghezza ai bordi, né il consumer.

## 2. Il caso che l'ha fatto emergere

DB p.53, rilievo dell'utente («qui non ci sono gutter, perché c'è una banda?»,
«non ha senso questo pezzo»).

| gutter | probatorio | span |
| --- | --- | --- |
| box `LESIONI GRAVI` (295-314) | 60 – 120 | 46 – 176 |
| tabella (167-178) | 160 – 504 | 120 – 582 |

Quaranta punti di vuoto separano le due strutture; solo l'estensione li colma.
Con lo span il box diventa figlio della tabella ed eredita `x0 = 178`, un
confine che nel box non esiste — 5 primitive lo scavalcano e **4 su 17** hanno
il centro sotto di esso, quindi escono dalla banda del box e finiscono in quella
della tabella.

## 3. Predizioni pre-registrate

Non concorrono a pass/fail; servono a poter sbagliare.

- **DB p.53**: il box diventa banda di **primo livello**, `x 0-612`, gutter
  295-314. Il taglio verticale a 178 sparisce e nessuna primitiva del box finisce
  nella banda della tabella.
- **DrW p.97 e DB p.50**: nessun cambiamento. Su DrW p.97 c'è una sola banda e
  nessuna subordinazione; su DB p.50 le due bande sono già di primo livello.

## 4. Regola di accettazione

**G1 — conservazione, ed è la porta.** `_segment_tree` promette che **ogni
gutter accettato compaia esattamente una volta nell'albero**; il criterio di
successo dichiarato quando fu scritta era 1.636 gutter su cinque manuali, zero
pagine divergenti. Deve reggere identico. È la guardia che distingue la
correzione dal trucco: le scorciatoie ovvie riparano una pagina **scartando** un
gutter subordinato, e su una pagina a 3 colonne sopra e 2 sotto perderebbero
struttura vera in silenzio.

**G2 — nessuna banda taglia parole.** Formulazione dell'utente, ed è la hard
rule che il difetto viola: nessun confine x di banda deve cadere dentro il bbox
di una primitiva testuale che quella banda contiene. Si conta prima e dopo su un
insieme di pagine; deve scendere, e in nessun caso salire.

**G3 — giudizio a vista**, sulle pagine già lette dall'utente: DB p.53,
DrW p.97, Dag p.164, DB p.50. Nessuna deve peggiorare.

Il numero di bande **cambierà** su alcune pagine, e non è un difetto di per sé:
un gutter che smette di essere subordinato diventa massimale e genera bande
proprie. Va contato e riportato, non usato come criterio.

## 5. Limiti

Le pagine di verifica sono ancore già viste. Nessuna affermazione di accuratezza
può uscire da questo giro. Il campione cieco non viene ripetuto qui.

## 6. Dopo

L'esito si scrive e **nessun altro giro viene proposto dall'interno di questo**.
Se G1 cade, la correzione è sbagliata e si ferma lì.
