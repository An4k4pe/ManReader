# I confini ammessi da Resolution dentro IR 2 — criterio pre-registrato

Milestone 44 ha prodotto due cose e non le ha collegate a niente: i confini di
colonna che Resolution ammette dentro le tabelle, e un ordinamento per righe.
Questo giro collega la **prima**.

## Cosa NON serve, e va detto subito
La seconda **non va collegata**: `ir2_builder.build_table` raggruppa gia' le
righe di tabella per sovrapposizione verticale delle righe di sorgente, con lo
stesso meccanismo di `table_row_reading_order.py` e con un'uscita migliore --
una griglia di celle invece di un ordine. Collegare anche quella sarebbe una
seconda implementazione della stessa cosa, che questo progetto ha gia' pagato.
Il modulo resta come contratto verificato dai suoi test, non come consumatore.

## L'innesto, uno solo
`scripts/prototype_ir2_page.py` costruisce `TableRegionInput.gutter_x_intervals`
prendendo **solo** i gutter delle bande ammesse (`ColumnBandMeasurements`).
`main_ir2.py` importa da li', quindi il punto e' unico e vale per il documento
intero. Si aggiungono i confini che `resolve_column_boundaries` ammette.

Nessuna soglia, nessun criterio nuovo: gli intervalli arrivano gia' decisi.

## Il difetto che dovrebbe togliere
Il corridoio fra la colonna dei numeri di dado e la descrizione e' scartato da
`too_few_wordy_lines`, quindi non arriva a IR 2, quindi `column_bounds` non lo
conosce: i numeri e il testo finiscono nella **stessa cella**, oppure la regione
non ha due confini e `build_table` non produce nessuna tabella.

## Predizioni registrate
- **Q1** — su DB indice 103 (stampata 102), tabella IMPREVISTI: la tabella
  guadagna una colonna e i numeri D20 stanno in una **cella propria**. Se dopo la
  modifica la griglia e' identica, l'innesto non ha effetto e va detto.
- **Q2 — non-regressione, ed e' la condizione.** Sulle pagine dove Resolution non
  ammette nessun confine il Markdown prodotto dev'essere **identico byte a byte**
  a quello di prima. Verificato eseguendo `main_ir2.py` su un intervallo di
  pagine prima e dopo, e confrontando le uscite.
- **Q3** — il costo: `column_band_gutter_rows` ricalcola i corridoi, quindi il
  lavoro di `column_band` per pagina raddoppia. Predico un aumento **misurabile**
  del tempo per pagina, e lo dichiaro invece di nasconderlo; se superasse il
  doppio del tempo totale, l'innesto va rifatto condividendo il calcolo.

## Criterio di accettazione
Q2 e' la condizione: **una sola pagina che cambia dove Resolution non ha ammesso
niente e la modifica non e' adottabile**. Q1 dice se serve a qualcosa. Q3 si
riporta in ogni caso.

Nessun default si sposta, il legacy non viene toccato, e i test esistenti di
`ir2_builder` e `ir2_table` devono restare verdi senza essere modificati.
