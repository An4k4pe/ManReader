# Proposta v2 — le tabelle vere: il difetto è la **riga**, non la regione

Modalità P. Sostituisce `Proposta_RegioneTabella_v1.md`, di cui **ritira la tesi
centrale**. Non committare: le proposte stanno fuori dal repo.

---

## 0. Changelog rispetto alla v1, e perché

**La v1 proponeva un producer nuovo di regioni tabella. È ritirata.**

La v1 era costruita su sette pagine in cui nessuna delle tre fonti di regione dava
il risultato giusto. Sei di quelle sette **non contengono una tabella vera**: Apo
idx 46 sono tre blocchi a due colonne, Vil idx 166 due elenchi a fondo alternato,
Wil idx 244 una scheda mostro, DrM/FW/Fab non le avevo aperte. L'unica con una
tabella vera era Dag idx 136, e lì il difetto era reale ma parziale.

Su indicazione dell'utente — «*proverei un po' di reali tabelle e cercherei di
risolvere quelle*» — ho preso **cinque tabelle vere** e le ho fatte passare per il
percorso IR 2 esistente, con `--tables` acceso.

**Tutte e cinque producono una tabella**, `tables=1/1`, e quattro su cinque
producono Markdown utilizzabile. Il meccanismo di Milestone 39 — regione da
`table_candidate`, colonne dai `gutter_x_intervals` di `column_band`, righe dalle
righe di sorgente — **funziona sulle tabelle vere**.

Due correzioni dell'utente integrate: il bersaglio di IR 2 è il **Markdown**, non
l'EPUB, e la v1 usava il metro sbagliato; **Wil idx 244 esce dal perimetro**, non è
una tabella e non va risolta adesso.

---

## 1. Le cinque tabelle vere, e cosa esce

Trovate con una scansione su otto manuali, poi **guardate**. Indici 0-based.

| pagina | cosa è | esito |
| --- | --- | --- |
| **DB idx 75** (stampata 74) | «ARMI DA MISCHIA», 9 colonne, 28 righe | tabella **corretta**, ogni riga di dati giusta |
| **Lan idx 118** | armi, 5 colonne | tabella **corretta** |
| **Fab idx 284** | equipaggiamento, 4 colonne | corretta, **con l'intestazione al posto giusto** |
| **Lan idx 284** | classi per ruolo, 2 colonne | parziale: una riga fonde quattro voci |
| **Dag idx 136** (stampata 135) | due tabelle affiancate | regione troncata (vedi v1 §1.1) |

Riga presa da DB idx 75, per far vedere che non è un caso fortunato:

```
| Spada Corta | 1M | 7 | 2 | D10 | 12 | 8 oro | Comune | Perforante, tagliente |
```

Nove colonne, tutte appaiate correttamente.

---

## 2. I quattro difetti, osservati, in ordine di quanto sporcano l'uscita

### 2.1 Una cella che va a capo diventa una riga in più

Il difetto più frequente. Su DB idx 75:

```
| Ogg. Contundente, | 1M | — | FOR | D8 | 3 | — | — | Contundente, può essere |
| Leggero           |    |   |     |    |   |   |   | lanciato                |
```

Sono **una riga sola** sulla pagina. Le righe della griglia vengono dalle righe di
sorgente raggruppate per sovrapposizione in `y`, e una cella che va a capo è una
seconda riga di sorgente. Stesso difetto su Fab idx 284, dove la descrizione di
ogni oggetto diventa una riga vuota in tutte le altre colonne.

**È lo stesso difetto che ha fatto cadere `Criterio_ParagrafoDaRiga_v1.md` §5**, sul
lato opposto: là la riga di sorgente si spezzava per campo, qui non si ricompone
per cella.

### 2.2 L'intestazione resta fuori dalla regione

Su DB idx 75 l'intestazione esce **come paragrafi sciolti dopo la tabella**:
`IMP.`, `FOR`, `POR-`, `TATA`, `DANNO`, `DURA-`, `BILITÀ`, `COSTO`, `DISPO-`,
`NIBILITÀ`, `QUALITÀ` — undici frammenti. La prima riga di **dati** («Mani Nude»)
finisce a fare da intestazione Markdown, perché l'emettitore rende come
intestazione la prima riga e lo dichiara.

**Nulla è perso**: è collocato male. E su Fab idx 284 l'intestazione entra
correttamente, quindi non è un difetto strutturale del meccanismo ma del bordo
superiore della regione.

### 2.3 Testo che sfugge dai bordi della regione

Su DB idx 75 la riga `Infido, perforante, tagliente,` — la prima riga della cella
QUALITÀ del Pugnale — **non è nella tabella**: esce come paragrafo dopo. La regione
ha `x1 = 539.6` e quel testo arriva più a destra.

**È la stessa classe di difetto della v1 §1.1 su Dag idx 136**, dove la regione
esclude un'intera colonna. Là un intero campo, qui una riga sola. La differenza è
di grado.

### 2.4 Righe che si fondono

Su Lan idx 284:

```
| ASSALTO Assassino Asso Assaltatore | Robusto, infligge danni in modo costante.
  Estremamente mobile, eccelle nel dare la caccia a singoli bersagli. Unità
  volante capace di evitare i danni ad area. |
```

Quattro voci in una riga. Il raggruppamento per sovrapposizione in `y` unisce righe
di sorgente che appartengono a righe di tabella diverse.

**2.1 e 2.4 sono lo stesso parametro visto dai due lati**: la tolleranza con cui
due righe di sorgente sono «la stessa riga di tabella».

---

## 3. I gutter non sono il problema, misurato

Su DB idx 75, tabella a **nove** colonne, `column_band` con i parametri di default
trova **otto confini di colonna su otto**: `x159`, `x183`, `x209`, `x244`, `x284`,
`x321`, `x358`, `x422`. Verificati sul render, uno per uno. È lo stesso fenomeno che
`State.md` registra come «*i sette gutter annidati di DB p.76 … la descrizione
corretta di una tabella a nove colonne*».

### Lo sweep dei parametri, richiesto dall'utente, ed è quasi tutto negativo

Sette configurazioni (`min_flanking_chars` 5→2→1, `min_gutter_lines` 3→2→1,5,
`min_column_chars` 10→3, e tutte insieme) su quattro pagine:

| pagina | effetto dell'allentamento |
| --- | --- |
| **DB idx 75** | **nessuno**: 8 gutter con tutte e sette le configurazioni |
| **Apo idx 46** | **nessuno**: 3 gutter con tutte e sette |
| Dag idx 136 | `chars 5→2` aggiunge `x95-102`, il confine `TIRO\|BOTTINO` — una colonna di numeri |
| Vil idx 166 | solo allentando tutto insieme aggiunge `x46-59`, la colonna `#` — di nuovo numeri |

**L'unica cosa che l'allentamento recupera è la colonna di numeri.** Lo dice già la
docstring di `_reject_reason`: «*un gutter con un solo carattere numerico per lato
… è un forte indizio di TABELLA — è proprio la colonna dei numeri di riga — e va
passato a chi rileva tabelle, non perso*».

### E qui c'è un vincolo che va rispettato

`State.md` §Cosa NON rifare chiude **esplicitamente** due cose:

> **Non tarare `--min-flanking-chars`**: ha fatto il giro 5 → 2 → 3 → 4 → 5 con tre
> correzioni, e la conclusione non è un valore ma una proprietà del criterio.
>
> **Non far decidere a `column_band` se una regione è una tabella**: deve dire dove
> sono i confini di colonna, e i gutter che trova sono materiale per il consumer di
> tabelle.

La ragione è misurata: `M=2..4` rompe Vil p.223 e circa dodici pagine del bestiario
Vil, perché **cambia l'ordine di lettura**.

**La via che non viola nulla**: i parametri sono già **argomenti di funzione**, non
costanti. `column_band_tree(page, min_flanking_chars=…)` esiste. Il percorso tabella
può chiedere allo stesso meccanismo una domanda diversa **senza toccare l'uscita di
`column_band` per l'ordine di lettura**, che resta ai default. Non è una taratura: è
un secondo interrogante. Ed è ciò che la frase «materiale per il consumer di
tabelle» prevede.

**Ma non serve adesso**, perché su DB idx 75 non cambia niente: va tenuto per quando
un difetto osservato lo richieda.

---

## 4. Perché Milestone 39 ha concluso il contrario

Il criterio è caduto su **1 pagina su 12**, e quella pagina era Wil idx 244, una
**scheda**. Le altre undici davano 7 regioni candidate e 0 tabelle.

Il campione era cieco e va bene così. Ma **conteneva quasi nessuna tabella vera**:
la scansione su otto manuali che ho fatto per questa v2 trova tabelle rigate su una
frazione piccola delle pagine, e un campione uniforme di 12 pagine ne pesca in media
meno di una.

**Il meccanismo non era inadeguato: non aveva nulla su cui lavorare, e l'unica cosa
che ha trovato non era una tabella.** È la stessa forma dell'errore che
`Esito_TabellaInIR2_v1.md` §1-quinquies aveva già identificato — la domanda era mal
posta — solo un gradino più indietro.

---

## 5. La proposta

**Non un producer nuovo. Chiudere i quattro difetti del §2 sulle tabelle vere.**

Perimetro, in ordine di quanto sporca l'uscita:

1. **La riga di tabella non è la riga di sorgente** (§2.1 e §2.4). Serve una regola
   che dica quando due righe di sorgente sono la stessa riga di tabella. Il segnale
   disponibile senza soglie nuove: una riga di continuazione **non ha testo nella
   prima colonna** — su DB idx 75 `Leggero` è nella colonna ARMA, quindi quel
   segnale da solo non basta, e va cercato quello giusto guardando le pagine.
2. **Il bordo superiore della regione perde l'intestazione** (§2.2). Su Fab idx 284
   non succede: il caso che funziona è a disposizione per capire perché.
3. **I bordi laterali perdono testo** (§2.3), che è la versione lieve della
   troncatura su Dag idx 136.

**Fuori scope, dichiarato**: un producer nuovo di regioni; qualunque modifica a
`column_band` o ai suoi default; qualunque modifica a `table_candidate`; le schede
mostro; tutta la lista aperta di Milestone 39.

**`--tables` resta spento** finché un criterio non lo riaccende, e
`Criterio_TabellaInIR2_v1.md` resta caduto: il suo errore squalificante — una
regressione fuori dalla tabella — non è stato riesaminato qui.

---

## 6. Il criterio di accettazione, da scrivere prima di implementare

Non lo fisso in questa versione, e lo dico invece di improvvisarlo: i quattro
difetti del §2 sono stati **osservati oggi**, su cinque pagine scelte perché
contengono tabelle. Un criterio scritto adesso sarebbe tarato su di esse.

Quello che serve prima, e che questa proposta chiede di autorizzare:

1. **Un campione di tabelle vere**, estratto con una regola dichiarata prima e non
   scelto da Chat A, dai 16 manuali. Le cinque pagine di cui sopra sono **pagine di
   sviluppo** ed escluse per costruzione.
2. **Il giudizio a vista dell'utente sul Markdown**, tabella per tabella, prima di
   qualunque conteggio: «si legge come la pagina» / «no, e perché».

Solo dopo si scrive il criterio, e si committa senza codice.

---

## 7. Cosa ho verificato

**Eseguito**: `prototype_ir2_page.py --tables` su DB idx 75, Lan idx 118, Lan idx
284, Fab idx 284 — `tables=1/1` su tutte e quattro; lo sweep di sette configurazioni
di `column_band_tree` su quattro pagine; la scansione delle griglie rigate su otto
manuali.

**Guardato**: DB idx 75 con le tre fonti disegnate sopra; il Markdown prodotto per
tutte e quattro.

**Non verificato**: se i quattro difetti del §2 siano gli unici — cinque pagine sono
poche; se il difetto §2.1 abbia una regola senza soglie (il primo segnale che ho
provato **non regge già su DB idx 75**, ed è scritto nel §5.1); il conteggio esatto
delle primitive che sfuggono dai bordi.
