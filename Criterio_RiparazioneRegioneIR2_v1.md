# Criterio — le due riparazioni della regione tabella, collegate in IR 2

Dichiarato l'11 settembre 2026, **prima** della misura che decide.

## 0. Che cosa ripara, e da dove viene

Rilievo dell'utente sull'esito dei confini della Fase 2: **in tutte le tabelle
mostrate manca l'intestazione o l'ultima riga, e le righe lunghe escono tagliate**.

La causa, misurata su cinque pagine: la regione `table_candidate` viene da
pdfplumber `text/lines`, che conosce una riga **solo dove c'è un filetto o un
fondo disegnato**. La regione comincia sul primo e finisce sull'ultimo:

| pagina | dove si ferma la regione | che cosa resta fuori |
| --- | --- | --- |
| DB p9 | filetti da y609 a y697 | `D12 STIRPE` a y595, `12 Lupinide` a y700 |
| DB p120 | filetti da y149 a y597 | `D6 EFFETTO` a y135, `6 Lampadario` a y600 |
| DB p103 | ultimo filetto y462 | `6 Cervo` a y465 |
| Dag p131 | y700 | la riga `18` a y703 |
| Dag p284 | y707 | la riga `20` a y707 |

In x la regione si ferma dove il testo si allinea, e le righe più lunghe
sporgono: DB p60 sette righe fino a x517 contro una regione che finisce a x509,
DB p120 ventuno righe fino a x291 contro x251. IR 2 prende solo le righe
interamente dentro: il resto resta paragrafo.

**La soluzione esiste già, e non la riscrivo**: `repair_region_y` e
`repair_region_x` in `scripts/prototype_table_columns_and_rows.py`, dalla chat
delle tabelle di agosto 2026, parte della configurazione `--repair xy` di
`Criterio_TabellaNormale_v1.md`. **Non sono mai state collegate a IR 2**: il
builder di Milestone 39 usa la regione grezza. Questo criterio le collega.

## 1. La regola, come nel prototipo, e le tre differenze dichiarate

- **y**: una riga di tabella alla volta, sopra e sotto. Una riga le cui righe di
  sorgente stanno tutte in una colonna appartiene alla tabella; una che
  attraversa un confine la chiude. Corsa contigua, non selezione sparsa. La
  regione si ritira sulle righe tenute.
- **x**: una riga di sorgente che ha testo dentro la regione le appartiene, e la
  regione deve contenerla intera; si allarga finché nessuna sporge.

Tre differenze, tutte dichiarate qui:

1. **Si ammette con la stessa regola con cui si colloca**: `_column_of` sulle
   colonne di IR 2 (gutter di `column_band` più confini ammessi dalla Fase 2),
   non sulle colonne proprie del prototipo. È la lezione che il prototipo stesso
   scrive in `_respects`: ammissione e assegnazione diverse hanno già fatto
   sbagliare due volte.
2. **Righe di sorgente intere**, non le sole primitive col centro dentro: IR 2
   non spezza mai una riga di sorgente.
3. **y poi x ripetuti fino a un punto fisso**, non una passata sola. Su DB p120 una
   passata sola tiene dentro `6 Lampadario` e fuori i suoi punti elenco, che
   sporgono a destra: la riga uscirebbe spezzata fra tabella e paragrafi. E una
   riga che contiene testo già di un'altra tabella chiude la corsa.

Nessuna soglia nuova.

## 2. Che cosa ci si aspetta — esplorazione dichiarata

Ho eseguito il prototipo com'è (colonne sue, una passata) su sette pagine:
DB p9, p60, p103, p120; Dag p131, p198, p284. **Non ho guardato l'uscita di IR 2**,
che è ciò che il §4 decide.

**Recuperato, previsto**: DB p9 intestazione e ultima riga; DB p103 ultima riga;
DB p120 ultima riga con i suoi punti elenco, e le parti tagliate; DB p60 le parti
tagliate; Dag p284 l'ultima riga in due tabelle su tre.

**Non recuperato, dichiarato adesso**:

- le intestazioni scritte in **una riga sola a cavallo di due colonne** —
  `D6 NOME` (DB p11), `D20 IMPREVISTO MAGICO` (DB p60), `D6 EFFETTO` (DB p120).
  Nessun lavoro precedente spezza una riga di sorgente, e non lo invento qui;
- Dag p131, la riga `18`: in IR 2 la sua descrizione attraversa il gutter 310-324,
  che viene da un'altra banda (§4 di `Criterio_ConfiniFase2InIR2_v1.md`), e
  chiude la corsa.

**Rischio noto, misurato prima**: una riga corta di prosa **subito sopra** la
tabella, che cade in una colonna, viene assorbita. Dag p131 `avversario.`; ed è
ciò che ha fatto fallire Dag p198 nel campione cieco di
`Criterio_TabellaNormale_v1.md` — verificato: senza riparazione la tabella è
giusta, con la riparazione parte da `potete utilizzare:`.

**Secondo rischio — emendamento prima della misura.** La prima stesura diceva che
il piè di pagina, che il prototipo assorbe su DB p60 e Dag p131, in `main_ir2`
«è arredo ed esce prima». **Falso**, verificato nel codice prima di vedere
qualunque uscita: `run()` costruisce la pagina IR 2 e **solo dopo** riconosce i
nodi d'arredo, che toglie al momento di scrivere il markdown. Mentre si
costruiscono le tabelle il piè di pagina è una riga di sorgente come le altre.
Previsto quindi: su DB p60 `CAPITOLO 5 – MAGIA`, che sta subito sotto la tabella
e dentro una colonna, entra nell'ultima riga. Su Dag p131 no, perché la corsa si
ferma prima (la riga `18`). Non aggiungo una guardia non misurata: il conteggio
del §4.C lo vedrà, e la guardia — usare gli slot d'arredo, che `run()` conosce già
prima della costruzione — resta una scelta dell'utente.

## 3. La popolazione

DB, Apo e Dag **interi**, con `--tabelle`. Prima: `output/resa/fase2-dopo/`, lo
stato dopo `Criterio_ConfiniFase2InIR2_v1.md`. Dopo: il render nuovo. Si giudica
ogni tabella che cambia; se sono più di 40, tutte quelle delle pagine nominate
al §2 e poi una ogni *k* delle altre, in ordine di pagina, fino a 40.

## 4. Pass/fail

### A. Barra
Test verdi, ruff pulito, `scripts/check_eb.py --pdf-dir .` 9 su 10 con la sola
Fab idx 126 già a verbale.

### B. Nessuna primitiva esce da una tabella
Su ogni pagina, le primitive che le tabelle possedevano prima le possiedono
ancora dopo. Una sola violazione ferma tutto prima del giudizio.

### C. Il giudizio, sull'immagine della pagina
- **meglio** — la tabella ora contiene intestazione, ultima riga o fine di riga
  che la pagina stampa **dentro** la tabella;
- **peggio** — contiene testo che la pagina stampa **fuori** (una riga di prosa,
  un titolo, un piè di pagina), o divide una riga fra tabella e paragrafo;
- **neutro** — il resto.

**Passa se meglio > peggio.** **Veto**: nessuna regione assorbe un paragrafo —
due o più righe di prosa di seguito. È l'errore grande che l'utente non vuole;
una riga sola è un errore piccolo e conta come peggio.

## 5. Che cosa NON dice
- Non recupera le intestazioni a riga unica: servirebbe spezzare una riga di
  sorgente, regola che non esiste in nessun lavoro precedente.
- Non tocca i gutter di altre bande nella regione. La risposta esistente è la
  regola di colonna del prototipo stesso — un corridoio libero in **tutte** le
  righe della regione — che qui non si collega.
- Non dice che le tabelle siano buone: Milestone 39 resta caduta, `--tabelle`
  resta spento di default.
