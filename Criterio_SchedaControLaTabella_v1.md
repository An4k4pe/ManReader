# Criterio — le righe di una scheda sono della scheda, non della tabella

Dichiarato il 17 settembre 2026, **prima** della misura che decide.

## 0. Perché, e che cosa esiste già

Indicazione dell'utente: **le tabelle non si decidono da sole, ma insieme agli
altri elementi della pagina; se il producer delle schede riconosce una scheda,
deve intervenire e dirlo.** È anche la regola del progetto: `AGENTS.MD` §Layout e
candidati mette il rapporto fra candidati di producer diversi in Resolution o nel
consumer.

Oggi il percorso tabella ignora le schede, e l'esito della riparazione della
regione (`Esito_RiparazioneRegioneIR2_v1.md`) cade sul veto anche per questo: su
Dag p229 la riparazione fa **una tabella di tre schede di avversari**, col piè di
pagina dentro e le intestazioni fuori.

**Il riconoscimento delle schede esiste** ed è della chat delle schede:
`stat_block_regions.py`, ramo `claude/statblock-markdown-ir2-7b2573`, punta
`7a90f5e`. Qui è **portato come è scritto**, con i suoi 30 test. Si usa la strada
dei **riquadri disegnati**; quella dalla struttura ripetuta è dichiarata in prova
su quel ramo, chiede una passata su tutto il documento, e non si porta.

Quel ramo ha già una regola per le tabelle: *una tabella che attraversa il
confine di una scheda non si costruisce*. Misurata qui sulle 35 pagine giudicate:
toglie Dag p229, ma **cancella due tabelle vere** — DB p106 «CREARE UN PNG», che
sfiora di 14 pt il riquadro sotto, e DB p91, che esce dal riquadro solo dopo la
riparazione.

## 1. La regola

> **Le righe di una scheda sono della scheda.** Una tabella che non sta **dentro**
> quella scheda non le prende: né quando si costruisce, né quando la regione si
> ripara, e la riparazione si ferma a loro. Una tabella **dentro** la scheda — la
> tabella degli attacchi di una creatura — le usa: è contenuto della scheda.

Due differenze dichiarate rispetto alla regola del ramo schede:

1. **Non si butta via la tabella intera**: le si tolgono le righe della scheda.
   È ciò che salva DB p106.
2. Il contenimento si misura sul **seme** della regione, non sulla regione
   riparata: così una riparazione che cresce verso un'altra scheda non se la può
   inghiottire.

Nessuna soglia nuova: contenimento e appartenenza di una riga sono relazioni.
Si calcola solo a tabelle accese.

## 2. Esplorazione dichiarata

Sulle 35 pagine già giudicate per la riparazione, **6 hanno schede** — DB p42,
p85, p91, p96, p106 e Dag p229 — e sulle altre 29 non cambia niente. Misurato,
prima di guardare qualunque uscita:

| pagina | che cosa succede |
| --- | --- |
| Dag p229 | la tabella sulle tre schede resta con **0 righe**: non si costruisce. La tabella dentro la scheda dello Scintillante tiene le sue 30 |
| DB p85 | la tabella finta sul riquadro della scheda resta con 0 righe; la tabella vera degli attacchi tiene tutte e 32 le sue |
| DB p106 | la tabella vera tiene **153 righe su 154**: lascia solo il titolo `ATTRIBUTI DEI PNG` del riquadro sotto |
| DB p42 | il riquadro AZIONI è preso per una scheda: la tabella finta passa da 58 righe a 16 |
| DB p96 | nessun effetto: la scheda è altrove nella pagina |
| **DB p91** | **costo noto**: la scheda riconosciuta è un falso positivo (`x0-524 y174-791`, le sue righe sono la prosa introduttiva) e si prende **8 delle 13 righe** della tabella vera degli attacchi |

**Non ho guardato l'uscita**: è ciò che il §4 decide.

## 3. La popolazione

DB, Apo e Dag **interi**, con `--tabelle`. Prima: `output/resa/riparo`, lo stato
dell'11 settembre con la riparazione collegata. Dopo: `output/resa/schede`. Si
giudica ogni tabella che cambia; se sono più di 40, tutte quelle delle pagine
nominate al §2 e poi una ogni *k* delle altre, in ordine di pagina, fino a 40.

## 4. Pass/fail

### A. Barra
Test verdi, ruff pulito, `scripts/check_eb.py --pdf-dir .` 9 su 10 con la sola
Fab idx 126 già a verbale.

### B. Per costruzione: nessuna tabella cresce
Ogni tabella di prima resta uguale, perde primitive, o sparisce. Una che ne
**guadagna** è un difetto d'implementazione e ferma tutto prima del giudizio.

### C. Il giudizio, sull'immagine della pagina
- **meglio** — la tabella lascia testo che la pagina stampa dentro una scheda,
  oppure sparisce una tabella che la pagina non stampa come tabella;
- **peggio** — lascia testo che la pagina stampa **dentro la tabella**, oppure
  sparisce una tabella che la pagina stampa;
- **neutro** — il resto.

**Passa se meglio > peggio.** **Veto**: nessuna tabella che la pagina stampa come
tabella deve sparire. DB p91 ne perde 8 righe su 13 ed è già contato come peggio;
se sparisse, il veto scatta.

## 5. Che cosa NON dice

- Non ripara le regioni che non sono né tabelle né schede: la prosa a due colonne
  (Dag p115, p310) e la scheda del personaggio (Dag p360) restano come sono, e il
  veto di `Esito_RiparazioneRegioneIR2_v1.md` resta aperto su di loro.
- Non porta il riconoscimento dalla struttura ripetuta né il nome della scheda
  come titolo: restano lavoro del ramo delle schede.
- **Non giudica le schede.** Se un riquadro sia una scheda lo decide quel modulo,
  e su DB p42 e p91 sbaglia. Qui si misura solo l'effetto sulle tabelle, e
  l'errore di DB p91 va riportato a quella chat.
