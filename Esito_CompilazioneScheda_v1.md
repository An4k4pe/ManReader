# La compilazione della scheda in YAML — esito

15 settembre 2026. Criterio: `Criterio_CompilazioneScheda_v1.md`. Pagine per
indice 0-based, stampata fra parentesi quadre (Daggerheart SRD non ne dichiara).

## 1. Che cosa c'e'

- **Prima lettura** (`stat_block_regions.structure_templates`, in `main_ir2` dopo
  `repeated_structures`): per struttura, in quante istanze compare ogni testo della
  parte a campi; si tengono i testi della maggioranza. Su DrM, 511 istanze: `size`
  451, `stamina` 453, `immunity` 440, `m`/`ight` 436, ma anche `0` 357 e `+2`
  355.
- **Seconda lettura** (`stat_block_fields.compile_fields`), regole nel modulo.
- **IR 2**: `StatBlockIR2` / `StatFieldIR2` nell'unione `StructureIR2`, kind
  `layout.stat_block`, serializzazione `"kind": "stat_block"`, validazione
  campi = primitive del nodo. Resa in `ir2_markdown.render_stat_block`.
- Tutto dietro `--schede-struttura`.

## 2. Predizioni

| | esito |
| --- | --- |
| P1 DrM idx 41 [35] | **regge**: le quattro schede con i dieci campi; Angulotl Cleaver 1S, 6, 4, 0, 2, 0, +2, 0, +1, 0 |
| P2 Daggerheart idx 38, Dire Wolf | **regge in parte**: Difficulty, Thresholds, HP, Stress, ATK, Claws, Motives & Tactics con «surround, trail»; **`Experience` resta fuori** -- non e' un'etichetta del modello (non tutti gli avversari ce l'hanno), la parte a campi finisce prima, e resta un paragrafo sotto il blocco |
| P3 Quickstart idx 29, Ragno Gigante | **regge**: Ferocia 2, Taglia Normale, Movimento 24, Armatura —, PF 36 |
| P4 senza flag identico | **regge**, §4 |

## 3. Cadute nello stesso giro, ognuna vista sui manuali

Il criterio del §1 del criterio e' stato scritto prima; queste sono le regole
della seconda lettura cambiate dopo averle viste fallire, e perche'.

| regola scritta prima | caduta su | sostituita da |
| --- | --- | --- |
| span sovrapposti in orizzontale = una parola | DrM, `Immunity:` e ` Poison 2` fusi (rumore 0,0006 pt); dopo la tolleranza, DB `Movimento:` su ` 24` sovrapposti di 0,36, piu' di `M` su ` ight` (0,24) | nessuna geometria: l'etichetta continua se il valore e' di soli `:` o e' seguito da un terzo stile; iniziale di un carattere + minuscole senza spazio |
| righe geometriche per le coppie impilate | DrM Pollywog e Animal, righe di altezza diversa fuse (`Size1S`) | per ogni etichetta ricorrente, lo span sovrapposto piu' vicino sopra o sotto che ricorre meno |
| parte a campi fino all'ultima etichetta della struttura | DrM, 65 etichette comprese quelle dei gradini dei tiri: Ajax, Bredbeddle e i box Malice compilavano capacita' intere; DB e Quickstart, la descrizione in prosa entrava come testo | fino all'ultima riga con un'etichetta del modello e non sotto di lei; senza etichette del modello, niente; le righe in testa senza campi restano paragrafo |
| riga che continua solo dentro la parte a campi | DB idx 116 [115], la seconda arma dei goblin va a capo sotto l'ultima etichetta | le righe dopo la parte a campi entrano solo se continuano l'ultimo valore |
| riga che continua per stile | DrM, la colonna di destra continuava la sinistra | anche sotto la coppia e sovrapposta a lei |

E una tabella che contiene righe della parte a campi non si costruisce piu': su
DrM Arixx `table_candidate` metteva `Size 2 | Speed 5` in griglia prima della
compilazione.

## 4. Misure

Giri con `--tabelle --schede-struttura` (Daggerheart idx 36-56, Quickstart intero,
DB idx 84-125, DrM idx 36-60). Blocchi YAML e blocchi con piu' di tre righe senza
etichetta:

| | blocchi | con testo sciolto |
| --- | --- | --- |
| Daggerheart | 151 | 10 |
| Quickstart | 5 | 0 |
| DB | 25 | 0 |
| DrM | 24 | 1 |

I 10 di Daggerheart vengono dal **riconoscimento**, non dalla compilazione: su idx
39 un «Mark a **Stress**» in grassetto dentro una capacita' conta come etichetta
ripetuta e apre un'istanza senza nome, che si porta dietro la scheda dopo. Nei
paragrafi non si vedeva; nel YAML si'. 17 schede senza nome su 151 nel giro.

**P4 regge.** Senza flag, con `--tabelle`, il `document.md` dei quattro giri e'
identico al byte all'uscita senza flag del commit `34913a5` (nessun blocco YAML).
Barra E-B (`scripts/check_eb.py`): 9 su 10, la sola differenza e' Fab idx 126, a
verbale. Suite: 1721 test, verdi.

## 5. Residui

- `gility` su DrM Arixx: la `A` del font dei glifi sta in un'altra riga di sorgente.
- La riga delle parole chiave di DrM (`Angulotl, Humanoid`) resta paragrafo sopra
  il blocco, perche' nell'ordine di lettura viene prima del primo campo; `Level` ed
  `EV` stanno nel blocco sotto `text`.
- `Diﬃ culty`: la legatura con lo spazio e' del testo di sorgente, come nei
  paragrafi.
- I nomi mancati (Bugbear Commander su DrM idx 59, RICOGNITORE e GUERRIERO su DB
  idx 91) sono del riconoscimento, gia' a verbale.
