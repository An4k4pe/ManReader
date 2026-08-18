# Esiti delle precondizioni — IR 2 minima

Verbale di quattro esiti, tutti ottenuti **prima** di qualunque implementazione
di IR 2. Il terzo ha richiesto una correzione al consumer, che è comunque
precedente allo stadio nuovo.

---

## 1. Precondizione di `Criterio_ParagrafoDaRiga_v1.md` §4 — **REGGE**

Il criterio superava `Criterio_ParagrafoDaBlocco_v1.md` e si dichiarava caduto se
su **DB p.53** — la pagina su cui il criterio precedente era stato verificato — il
blocco fosse ancora servito.

Regole a righe applicate a DB p.53 (idx 52), blocchi `b0003`-`b0007`:

```
b0003: In questo gioco, puoi subire sei diverse condizioni, …   (un paragrafo)
b0004: ✦Esausto – FOR
b0005: ✦Malaticcio – COS
b0006: ✦Disorientato – AGI
b0007: ✦Arrabbiato – INT
```

Identico a quanto produceva la regola a blocchi: un paragrafo di prosa e le voci
di elenco separate. **Il blocco non serve nemmeno lì**, e il superamento è
legittimo.

Due precisazioni sul criterio, che ne aveva sbagliate le premesse minori:

- le voci sono **quattro**, non tre: il criterio citava
  `Esausto`/`Malaticcio`/`Disorientato` e c'è anche `Arrabbiato`;
- a separarle non è la punteggiatura ma il glifo `✦`, che non è una minuscola e
  quindi fa scattare l'interruzione. La regola regge, ma per una via diversa da
  quella che il criterio aveva in mente.

## 2. Giudizio a vista sul campione cieco — ordine **corretto 9 su 9**

Eseguita `scripts/prototype_vertical_slice_page.py --emit-order-variants` sulle
dieci pagine di `Campione_UscitaIR2Minima_v1.md`. Nove eseguibili, una in crash
(§3).

Giudizio dell'utente sulle nove, nella sua formulazione: **l'ordine di lettura è
già corretto, a parte le tabelle, che sono ovviamente sbagliate perché il producer
di tabelle non è implementato.**

Condizioni, che sono ciò che rende il giudizio utilizzabile: pagine estratte a
caso da un pool non condizionato con seed pre-registrato, mai viste prima,
giudicate **prima che IR 2 esista**.

**Conseguenza sul criterio di uscita**: l'ordine non è il rischio, è acquisito. Il
rischio è che IR 2 lo rompa. `Criterio_UscitaIR2Minima_v2.md` riscrive E-B su
questa base.

Cinque delle nove pagine non producono bande, il che per pagine a colonna singola
è l'esito giusto.

## 3. Difetto `Wil` idx 71 — tre parti, da non confondere

La fetta verticale **crasha**: `pymupdf.mupdf.FzErrorArgument: code=4: Invalid
bandwriter header dimensions/setup`, in `_extract_image_bytes`, ramo
`rasterized_clip`.

**Causa.** L'occorrenza `info[1]` ha `xref=0` — nessuna risorsa incorporata
risolvibile — quindi cade nel ramo di rasterizzazione, e la sua bbox è
`x 699,3-1284,0` su una pagina `0-581,1`. Il clip è **interamente fuori pagina**,
il pixmap esce vuoto, `tobytes("png")` muore.

**Misura**, con `scripts/scan_offpage_image_occurrences.py` su `Wil` (316 pagine,
2.820 occorrenze):

| | | |
| --- | --- | --- |
| interamente fuori pagina | **47** | 1,7% delle occorrenze, su 46 pagine |
| parzialmente fuori (al vivo) | **1.257** | **44,6%** delle occorrenze |

Misurato su **un manuale solo**. Non è una misura di corpus e non va citata come
tale.

### Le tre parti

1. **Il crash è un difetto del consumer.** Il ramo `rasterized_clip` deve
   intersecare la bbox con il rettangolo della pagina e rifiutarsi di rasterizzare
   se l'intersezione è vuota. Va corretto comunque, indipendentemente dal resto.
2. **Un'occorrenza interamente fuori pagina non deve produrre né asset né nota.**
   Non contribuisce un solo pixel alla pagina resa, quindi non è contenuto. È un
   **fatto**, non una politica: intersezione vuota, nessun parametro, niente da
   desumere — a differenza della rimozione dell'arredo, che una politica la
   richiede.
3. **Le parzialmente fuori si ritagliano, non si scartano.** Sono il 44,6% su
   `Wil`, ed è impaginazione normale: le illustrazioni a filo margine si stampano
   debordanti. È il numero che vieta la correzione ingenua «scarta ciò che esce
   dalla pagina», che distruggerebbe metà degli asset del manuale.

### Stato: **CHIUSO** nel commit `2d6052b`

Il ritaglio interseca ora il rettangolo della pagina. Le parzialmente fuori
vengono ritagliate, l'interamente fuori non produce raster e viene registrata con
`extraction_method = offpage_no_raster` più una riga esplicita in `review.md`.

Criteri dichiarati prima della correzione e tutti verificati: le nove pagine della
base restano **byte-identiche** (9 su 9), `Wil` idx 71 gira con conservazione
1553=1553 e integrità dei riferimenti verde, l'occorrenza è registrata, nessun
asset perso (4 su 4).

Le parti 2 e 3 restano fatti misurati e validi per chiunque tocchi l'estrazione
asset in futuro: interamente fuori non è contenuto, parzialmente fuori è il vivo
e va ritagliato.

## 4. Giudizio sulla decima pagina — il campione torna a **dieci**

`Wil` idx 71 (apertura di capitolo *IL BANCHETTO*: illustrazione, prosa, tre
riquadri). Giudizio dell'utente sull'uscita prodotta dopo la correzione:
**l'ordine è corretto**, con la precisazione che *restano delle rifiniture da
fare*.

**La distinzione va tenuta, ed è ciò che rende la base utilizzabile.** Il giudizio
è sull'**ordine di lettura**, che è quanto E-B misura. Le rifiniture riguardano la
**resa delle parole** — spazi fra span, sillabazione, segmentazione in paragrafi —
che sono esattamente ciò che le regole di
`Criterio_ParagrafoDaRiga_v1.md` cambiano e che **non sono ancora implementate**.
Non sono difetti d'ordine e non concorrono a E-B.

**Conseguenza**, per il §3 di `Criterio_UscitaIR2Minima_v2.md`, che prevedeva
questo caso: la condizione «il crash è chiuso» è soddisfatta, l'esclusione decade,
e **la base di E-B è di dieci pagine**, tutte giudicate a vista dall'utente prima
che IR 2 esista.

Bilancio del campione cieco: **ordine corretto 10 su 10**, tabelle escluse per
assenza del producer, e un difetto vero trovato e chiuso.
