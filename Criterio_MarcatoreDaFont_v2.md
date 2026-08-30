# Criterio — il marcatore da font, v2: **da solo sulla sua riga conta come separato**

**Scritto prima di implementarlo.** Emendamento a
`Criterio_MarcatoreDaFont_v1.md`, che è **scaricato** (18 voci su 18, esaustivo):
un criterio scaricato si emenda con una v2 e si riverifica, non si ritocca.

## 0. Che cosa deve chiudere

Rilievo dell'utente su Vil idx 131: «una lettera `h` che rappresenta il pallino
dell'elenco che viene spostata a caso e non renderizzata». La resa dice:

```
Gli effetti positivi di un dono si attivano istantaneamente. h
Gli effetti collaterali potrebbero attivarsi subito o dipendere da un tiro di h dado.
```

La sorgente dice che `h` è un pallino, e lo dice senza ambiguità:

```
b0004 l0001   dim 10,0  NelsonOrnaments   x 56,7→ 63,6   y 280,5→291,4   h
b0004 l0002   dim 11,6  ArnoPro-Regular   x 74,7→321,9   y 277,9→292,4   Gli effetti positivi…
```

Primitiva sua, font suo, **stesso blocco**, e le due fasce verticali si
sovrappongono: è il pallino della voce che gli sta a destra.

**Due difetti distinti**, e vanno separati perché cadono separati.

## 1. Primo difetto — `h` non è mai stato un candidato

`document_line_start_measurements.measure_document_line_starts` conta zero
aperture per `h`, su 82 occorrenze. La causa è una riga sola:

```python
if head.isalnum() and not (
    _is_a_glyph_marker(openers[position], head, body_font_name)
    and len(stripped) > 1
    and stripped[1].isspace()
):
    continue
```

La via del font chiede che **uno spazio** separi il glifo da ciò che segue. Su
Vil il glifo **è tutta la riga**: `len(stripped) == 1`, e la condizione lo scarta.

Il vincolo dello spazio è giusto e ha una misura sua — su FWK `Bruinloa` ha la
`B` in `ACaslonPro-Bold-SC700`, primitiva a sé, e senza quel vincolo il manuale
passava da 136 voci a 140. Ma il vincolo esprime una cosa più generale di come è
scritto: **il glifo deve essere separato da ciò che segue**.

> Un glifo che è **tutta la sua riga sorgente** è separato da ciò che segue più di
> quanto lo sia uno seguito da uno spazio.

E il resto del meccanismo lo sa già: le righe subito sotto trattano esattamente il
caso «il marcatore sta da solo sulla riga, il testo della voce è la riga dopo», ed
è così che `•` di FW entra. La via del font era l'unica a non poterlo fare.

### La regola

> Un carattere alfanumerico è candidato se la sua primitiva è **il solo
> carattere** in un **font diverso dal corpo**, **e** è separato da ciò che segue:
> o uno spazio lo separa, **oppure il glifo è tutta la riga**.

Invariato tutto il resto: non appaiato, maggioranza a inizio riga, testo che
segue, almeno due pagine, corse e firme di scala a valle.

### Il falsificatore, misurato prima

Su FWK, delle 30 righe che cominciano con una primitiva di un carattere solo in
un font diverso dal corpo:

```
'R' 8  'S' 6  'L' 5  'C' 4  'B' 3  'P' 2  'N' 2  'D' 2  'A' 2  'I' 1
da_solo = 0        spazio = 0        attaccato = 30
```

**Zero da sole.** `Bruinloa`, `Richiamare Armatura`, `Sua Maestà Anessa` sono tutte
maiuscolette attaccate alla parola. L'emendamento non le riammette, e questo è il
motivo per cui è un emendamento e non un rilassamento.

## 2. Secondo difetto — il glifo cerca il suo testo solo in avanti

`ir2_builder.bind_marker_glyphs` cerca il compagno **fra le righe che seguono**.
Su Vil il testo della voce sta **prima** del glifo nell'ordine di lettura, perché
l'ordine decide per posizione e il testo comincia 2,6 punti più in alto:

```
testo   y 277,9→292,4      ← viene prima
glifo   y 280,5→291,4      ← viene dopo
```

Il glifo non trova nessuno, resta una riga sua, e finisce in coda al paragrafo.

### La regola

> Il glifo cerca il suo testo **nel suo blocco e sulla sua riga visiva**, prima
> fra le righe che seguono e poi fra quelle che precedono. Il primo che trova è
> il suo.

Il vincolo verticale — che è ciò che impedisce a un glifo di rubare la
continuazione della voce precedente, misurato su DB — **non cambia**, e vale in
tutte e due le direzioni.

## 3. Pass/fail

Niente campione: le voci sono poche e si guardano tutte, come nella v1.

### A. Veto — cade a un carattere solo

> Si enumerano **tutti** i caratteri che diventano marcatori con la v2 e non lo
> erano con la v1, su tutti e sedici i manuali. Cade se **uno solo** non è un
> marcatore d'elenco.

### B. Il falsificatore dichiarato

> Su FWK il numero di voci d'elenco deve restare **136**. Le maiuscolette non
> devono entrare.

### C. Regressione dei marcatori

> Nessun marcatore che la v1 trova può sparire, su nessuno dei sedici.

### D. Il legame all'indietro non ruba niente

> Su FW p.168 — due colonne di glifi interlacciate, il caso per cui la ricerca in
> avanti è stata scritta — e su DB — dove senza il vincolo verticale usciva
> `✦nel tempo.` — il numero di voci resta invariato.

### E. Le regressioni di sempre

> `check_list_regression.py` e `check_numbered_lists.py` invariati salvo le voci
> che questo emendamento aggiunge, che si contano e si nominano.

### Se cade

- **A**: si nomina il carattere e si ritira l'emendamento. Non se ne aggiunge un
  altro nello stesso giro.
- **B**: il vincolo dello spazio non era generalizzabile come ho scritto, e il §1
  è sbagliato nella sua premessa.
- **D**: la ricerca all'indietro va tolta e il primo difetto si chiude da solo.

## 4. Che cosa resta fuori

- **Le schede**, ancora, e ancora dichiarate prima: la v1 si regge sul fatto che
  corse e firme di scala filtrano a valle, e quel fatto non cambia qui.
- **L'indentazione** delle voci, che su Vil distinguerebbe `↳` da `h` come due
  livelli. `Decisione_Annidamento_v1.md` l'ha rimandata e resta rimandata.
