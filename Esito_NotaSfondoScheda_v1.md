# La nota dello sfondo della scheda — esito (passo 3b)

Criterio: `Criterio_NotaSfondoScheda_v1.md`, registrato prima dei giri «dopo».
Base: l'uscita di 3a (`e05ebfa`), rigenerata da un worktree fermo a quel commit
sugli stessi intervalli -- Daggerheart SRD `36-56`, Dragonbane Quickstart intero,
DB `95-125`, con e senza `--tabelle`. Pagine per indice 0-based, stampata fra
parentesi quadre da `page.get_label()`.

## In breve

| | esito |
| --- | --- |
| S1, la condizione | **REGGE** in sei giri su sei: cambiano solo righe di nota, solo su pagine con una scheda con nome, e il testo dell'IR e' identico su tutte le pagine |
| S2, Daggerheart invariato | **REGGE**: 0 pagine cambiate, con e senza tabelle |
| S3, la nota cambiata e' la pergamena | **CADUTA al primo giro** (Pipistrelli); dopo la correzione del meccanismo, 6 note su Dragonbane, tutte pergamene. Vedi sotto |
| S4, DB | 3 note: il Cavaliere Brigante giusto, ATTRIBUTI DEI PNG pergamena di un box di regole, il Ragno Gigante **sbagliato** |
| S5, round trip | **REGGE**: `run()` lo verifica a ogni pagina, nessun errore in sei giri, 198 pagine rese |
| S6, E-B | **REGGE**: 9 identiche su 10, la sola differenza e' Fab idx 126, gia' a verbale |
| S7, test | 1706 verdi, 7 skipped (1698 di 3a + 8). Ruff pulito; BasedPyright pulito sui file toccati, salvo due errori preesistenti in `ir2_serialization.py` (`heading_level`, `marker`, 28 e 30 agosto) e le importazioni di `fitz`/`pdfplumber` che l'ambiente del worktree non risolve |

## S3 e' caduta, e che cosa e' caduto

Primo giro: 9 note in tutto, 7 su pergamene e **2 su illustrazioni**, Dragonbane
idx 31 [30] (il pipistrello, 492×592 pt) e DB idx 97 [96] (il ragno, 613×694 pt).
Su Dragonbane S3 cade su 1 scheda su 6.

**Non e' caduto il criterio, e' caduto un meccanismo ereditato da 3a.** Lo sfondo
e' il riquadro che vince la regione, e in 3a vinceva quello con piu' righe: la
regola era fatta per preferire la scheda intera al suo riquadro dei soli campi.
Misurato (`scripts/measure_stat_block_frames.py`): su Dragonbane idx 31 passano il
criterio due riquadri, entrambi col nome dentro, la pergamena con 28 righe e
l'illustrazione con **56**, che copre la scheda e anche il testo della stanza 5
accanto. Vinceva l'illustrazione. In 3a non si vedeva perche' il nome esce uguale,
ma la regione si portava dietro le righe di un'altra colonna.

Due regole misurate su tutte le 141 schede dei tre intervalli:

| | cosa sistema | cosa cambia d'altro |
| --- | --- | --- |
| **(1) vince il riquadro piu' stretto col nome; senza nome, il piu' ampio** | Pipistrelli | niente: e' l'unica regione su 141 con un'alternativa col nome |
| (2) un riquadro il cui bordo taglia una riga di testo non delimita una scheda | Pipistrelli (l'illustrazione taglia 32 righe, la pergamena 0) | toglie titolo e nota ad AZIONI e ATTRIBUTI DEI PNG (1 riga tagliata ciascuna) e sposta due regioni senza nome di DB (28 e 40 righe tagliate) |

Adottata la **(1)**: e' la variante che cambia meno, e fa della regione dei
Pipistrelli la scheda vera. La (2) resta qui con i suoi numeri: sulle schede
scelte le righe tagliate sono 0 in 139 casi su 143, e potrebbe servire come
guardia contro i box di regole, ma e' misurata su pagine gia' spese.

**Nessuna delle due sistema DB idx 97 [96].** Non e' un'illustrazione sopra una
scheda: e' una pagina-mostro senza riquadro di scheda. L'illustrazione copre
titolo, prosa in due colonne, il riquadro dei campi e meta' della tabella degli
attacchi, non taglia righe, ed e' l'unico riquadro col nome -- l'altro, quello
dei campi, il nome non lo contiene. Resta un **errore dichiarato**: la nota dice
«sfondo della scheda RAGNO GIGANTE» di un'illustrazione. Non ho trovato una
relazione che lo distingua senza tararla su quella pagina.

## I numeri, a codice definitivo

| | note cambiate | pergamene di schede | pergamene di box non scheda | immagini sbagliate |
| --- | --- | --- | --- | --- |
| Daggerheart 36-56 | 0 | -- | -- | -- |
| Dragonbane intero | 6 | 5: RAGNO GIGANTE, PIPISTRELLI VAMPIRO, GRUB, LA SIGNORA, IL WIGHT | 1: AZIONI (idx 13 [12]) | 0 |
| DB 95-125 | 3 | 1: IL CAVALIERE BRIGANTE | 1: ATTRIBUTI DEI PNG (idx 107 [106]) | 1: RAGNO GIGANTE (idx 97 [96]) |

Identici con e senza `--tabelle`. Le regioni e i nomi di 3a non cambiano con la
correzione: 130/130, 6/6, 7 regioni con 3 nomi, e il confronto non trova
nessuna riga cambiata che non sia una nota.

Verifica a vista dell'assistente: gli asset delle nove note aperti uno per uno, e
le nove pagine con il rettangolo dell'immagine sostituita.

**AZIONI e ATTRIBUTI DEI PNG** erano i falsi positivi gia' a verbale in 3a, dove
come titolo si leggevano bene. Nella nota diventano visibili: «sfondo della
scheda» di un box di regole. Resta aperto.

## Giudizio dell'utente: IN SOSPESO

12 settembre 2026, sul foglio delle nove pagine. Con le sue parole: «io non
userei gli sfondi come riferimento per le schede, e' una cosa specifica di DB»;
lo sfondo «puo' essere un elemento, ma come gia' visto in db lo stesso sfondo
serve anche per i box. Non lo userei come unico discriminante». E sul codice:
«tienila in sospeso finche' non abbiamo modo di verificare se e' universale».

**Il passo non entra nel ramo di lavoro.** Sta su
`claude/statblock-3b-nota-sfondo-in-sospeso`, commit unico, e il ramo delle
schede resta a 3a (`e05ebfa`). Ci resta anche la regola di scelta «vince il
riquadro piu' stretto col nome», che corregge una regione di 3a: fa parte dello
stesso giudizio sospeso, e va ripresa quando si lavora sul discriminante.

Tre fatti che il giudizio ha fatto emergere, e che valgono oltre questo passo:

- **DB e Dragonbane Quickstart sono lo stesso sistema.** `DB.pdf` cita Dragonbane
  su 20 pagine su 126, e il Ragno Gigante ha la stessa illustrazione. Dei tre
  intervalli di questo passo e di 3a, due sono Dragonbane: l'unico sistema
  diverso e' Daggerheart, e su Daggerheart questo passo non ha prodotto una nota.
  Gli emendamenti alla regola del nome di 3a sono stati trovati su DB, cioe'
  ancora su Dragonbane.
- **Lo sfondo della scheda e lo sfondo di un box di regole sono lo stesso
  oggetto** su Dragonbane: e' cosi' che AZIONI e ATTRIBUTI DEI PNG passano per
  schede. Il riquadro non basta come discriminante.
- **Il terzo manuale «sigillato» non e' fresco.**
  `Draw_Steel_Monsters_v1.01.pdf` ha la stessa dimensione al byte
  (101.631.407) di `DrM.pdf` del benchmark, che ha 385 pagine e per titolo
  «Draw Steel: Monsters», MCDM. Il file sigillato non e' stato aperto: il
  confronto e' su dimensione e metadati di `DrM.pdf`. DrM e' gia' stato usato da
  piu' milestone, anche sulle sue schede mostro.

## Per rifare

    git worktree add --detach <base> e05ebfa
    ./venv/bin/python <base>/main_ir2.py <pdf> --out <prima> --pages <intervallo> [--tabelle]
    ./venv/bin/python main_ir2.py <pdf> --out <dopo> --pages <intervallo> [--tabelle] --processi 1 2> <dopo>.log
    ./venv/bin/python scripts/compare_stat_block_notes.py <prima>/document.md <dopo>/document.md <dopo>.log
    ./venv/bin/python scripts/measure_stat_block_frames.py <pdf> <sigla> <idx da> <idx a>
    ./venv/bin/python scripts/check_eb.py --pdf-dir <cartella dei PDF>

## S6, E-B

`scripts/check_eb.py` sul codice definitivo: **9 identiche su 10**, 586 s. La
sola differenza e' **Fab idx 126**, con le lunghezze del verbale (base 797, nuovo
789), gia' spiegata dal 30 agosto 2026. Lo stesso esito sul codice prima della
correzione della regola di scelta.

## Aperto

DB idx 97 [96] e le pagine-mostro senza riquadro; i box di regole presi per
schede (AZIONI, ATTRIBUTI DEI PNG), per i quali la regola (2) e' il primo
candidato da misurare su pagine fresche; il cartiglio del nome e il riquadro
della tabella degli attacchi, che su Dragonbane restano «riquadro» e «immagine
inserita»; le righe dentro la scheda (3c).
