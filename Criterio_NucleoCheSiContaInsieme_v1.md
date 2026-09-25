# Criterio — la scheda è un nucleo di etichette che il documento conta insieme

Dichiarato il 25 settembre 2026, **prima** della misura decisiva. Richiesta
dell'utente: «prosegui cercando una soluzione per questo, ho necessità di finire
il progetto; ricorda quale è l'obiettivo: un manuale human readable in markdown
con immagini estratte e sostituite da note».

## 0. Da dove arriva

Due misure hanno fissato i due bordi (`Esito_UnaCoppiaPerRiga_v1.md`, `_v2.md`):

- **unità sulla riga** — un'etichetta ripetuta nello stesso posto è un campo: prende
  le celle delle tabelle delle armi di Daggerheart (`Versatile:`, `Potente:`),
  23 pagine danneggiate. Troppo larga.
- **unità sul blocco, insieme esatto** — l'insieme delle etichette del blocco deve
  ripetersi identico: la sirena porta `mascella disarticolata`, che cambia a ogni
  creatura, e 815 paragrafi di Daggerheart si risaldano. Troppo stretta.

L'indicazione dell'utente che le tiene insieme: «una scheda è fatta da una
struttura che ripete, e nella tabella armi questo non c'è». La struttura che si
ripete non è l'insieme intero ma il suo **nucleo**.

## 1. La regola

1. **Riga di campi**: una riga che dichiara almeno **una** coppia etichetta/valore
   (i due punti). Un campo per riga basta: 1.349 righe su sei manuali mai toccati
   ne dichiarano uno, 19 ne dichiarano due.
2. **Blocco**: una corsa di righe di campi consecutive (salto massimo due righe,
   come oggi) che dichiara almeno **due etichette distinte**.
3. **Nucleo**: un gruppo di etichette dichiarate che il documento **conta
   insieme** — compaiono insieme su almeno tre pagine e, dove compare la più rara,
   hanno lo stesso conteggio nella maggioranza dei casi. È la regola di
   `stat_block_regions._bound_label_groups`, misurata il 14 settembre, applicata
   alle sole etichette **dichiarate**.
4. **Un blocco è una scheda se porta almeno due etichette dello stesso nucleo.**

Il nome dell'arma della sirena non rompe niente: sta nel blocco, fuori dal
nucleo. Una cella `Versatile:` è un blocco di un'etichetta sola e non ne porta
due di nessun nucleo.

**Il profilo di posizione non serve più**, e lo dico perché è la guardia che
proteggeva la tabella dei tesori di DB: `1:`, `2:`, `3:` non si contano insieme
su tre pagine, quindi non formano un nucleo.

## 2. Che cosa dice l'esplorazione, prima di scrivere la regola

`output/resa/nuclei.py`, sulle pagine che hanno deciso le misure precedenti:

| pagina | blocchi | esito |
| --- | --- | --- |
| Dag idx 120, tabella delle armi | 12, un'etichetta ciascuno | tutti **scartati** |
| Dag idx 230, la sirena | tre schede avversario, 6-7 etichette dal nucleo | **accettate** |
| Dag idx 326, il colosso | cinque schede | **accettate** |
| DB idx 90, il gigante | `Ferocia/Taglia/Movimento/Armatura/Armi` | **accettata** |
| DB idx 123, i tesori | 10 righe `Tira un D6. 1: … 2: …`, **0** dal nucleo | tutte **scartate** |
| Wil idx 137, carta AREA | `Sentieri/Mostri/Umani` | **accettata** |

I nuclei per manuale:

| manuale | nuclei |
| --- | --- |
| DB | **uno**: `abilità, ali, armatura, armi, dannobonus, ferocia, movimento, resistenza, taglia` |
| Dag | dieci, fra cui le schede avversario (15 etichette) e i **tratti delle armi** (17) |
| Wil | `{sentieri, mostri, umani}`; `{#1, #2, #3}` — **falso**, marcatori numerati |
| BiD | la scala degli esiti; `{edifici, scene, strade}`; altri tre |
| Kul | `{acume, fermezza, impeto, prudenza}`; `{claudio, river, simone}` — **falso**, parlanti di un esempio |
| Vil | `{0 segni … 4+ segni}` |
| DIE, SV, Apo | nessuno |

**Il nucleo dei tratti delle armi esiste**: `affidabile, brutale, massiccio…` si
contano insieme. Oggi non fa danno perché ogni cella è un blocco a sé. Se un
manuale mette due celle di tratti in righe consecutive, il blocco porta due
etichette dello stesso nucleo e passa: è il rischio da guardare.

## 3. Due varianti, misurate insieme

La vecchia strada dei riquadri (`stat_block_regions` dentro `run()`) oggi si
accende solo quando la policy tace (`Criterio_PolicyMutaNonSpegne_v1.md`). Con i
nuclei Wil **non** tace più, quindi la strada si spegne, e le carte AREA — il cui
fondo è raster, quindi la Resolution dei riquadri non può allargarle — rimettono i
`TRATTI` dentro la tabella `INGREDIENTI`. È successo nella v2, e lo prevedo qui.

- **A, `--schede-rete muta`**: la vecchia strada si accende solo se non c'è nessun
  nucleo. Il riquadro non decide mai niente.
- **B, `--schede-rete sempre`**: la vecchia strada resta accesa **accanto** ai
  nuclei, e le aree si sommano. Il riquadro aiuta ma non è l'unica voce: una
  scheda si riconosce dai nuclei anche senza riquadro, e il riquadro aggiunge
  solo dove c'è. Tocca il giudizio dell'utente del 12 settembre: «può essere un
  elemento, ma non lo userei come unico discriminante» — in B non è mai l'unico,
  ma è **un** discriminante.

## 4. La popolazione

Nove manuali: DB, Apo, Dag, Wil, BiD, DIE, SV, Kul, Vil. Variante A su tutti e
nove; variante B sui sei che hanno nuclei (DB, Dag, Wil, BiD, Kul, Vil) — sugli
altri tre A e B coincidono. Riferimenti: `output/resa/rete` (DB, Apo, Dag, Wil) e
`output/resa/maitoccati/senza-*` (gli altri cinque).

## 5. Che cosa deve succedere perché una variante passi

**A. Le armi restano intere.** Su Dag idx 116-130 nessuna cella esce da una tabella.

**B. Daggerheart resta leggibile.** Il numero di paragrafi di Dag non scende
rispetto a `rete`: la perdita di 815 della v2 non deve ripetersi. La sirena e il
colosso si guardano.

**C. Le tabelle.** Ogni tabella che cambia si giudica sull'immagine: **meglio** se
esce una riga che la pagina stampa fuori, **peggio** se ne esce una che la pagina
stampa dentro. Passa se meglio ≥ peggio, e le sei già giudicate non peggiorano.

**D. Nessuna prosa tagliata.** I paragrafi che cominciano in minuscola non
salgono su nessuno dei nove.

**E. Barra.** Test verdi, Ruff pulito, `check_eb.py` 9 su 10 con la sola Fab idx 126.

**Veto.** Una tabella che la pagina stampa come tabella perde righe perché una
scheda se le è prese.

## 6. La previsione

- **A passa in entrambe.** Le celle delle armi sono blocchi di un'etichetta.
- **B passa in entrambe.** Le schede avversario portano 6-7 etichette dal nucleo.
- **Su Wil la variante A peggiora le carte AREA** come la v2 — i `TRATTI`
  rientrano in tabella — e **la variante B no**.
- **D è il veto più probabile**: `opens_a_record` cerca i due punti su tutte le
  etichette della riga, e nella misura a una coppia per riga ha tagliato una frase
  su BiD e una su DIE. I nuclei riducono i blocchi rispetto a quella misura, ma non
  so se abbastanza.
