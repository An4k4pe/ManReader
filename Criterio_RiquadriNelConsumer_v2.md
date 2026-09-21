# Criterio — i riquadri nel consumer, v2: il riquadro non si allunga nell'altra colonna

Dichiarato il 21 settembre 2026, **prima** della misura. Richiesta dell'utente,
dopo `Esito_RiquadriNelConsumer_v1.md`: «sì, fai la v2».

## 0. Che cosa cambia rispetto alla v1

La v1 è caduta su un solo caso, e il veto era nella moneta giusta: su DB idx 92
(stampata 91), il grifone, un candidato di riquadro `(54,117)-(550,382)` attraversa
le due colonne della pagina, contiene per intero la scheda accettata della colonna
sinistra, e la regola l'ha preso per confine — portandosi via la tabella degli
attacchi della colonna destra.

La v2 aggiunge una condizione sola alla regola della v1. Tutto il resto — per
intero, massimali, riquadri solo disegnati, identità dalla policy — resta
identico.

## 1. La condizione, e come è nata

**Un pezzo di riquadro non delimita una scheda se, all'altezza della scheda,
scavalca un corridoio fra colonne che la scheda stessa non scavalca.**

In termini di rettangoli, per un corridoio ammesso `g` di `column_band` e una
proposta accettata `c` contenuta nel pezzo `f`:

- `g` è all'altezza della scheda: gli intervalli verticali di `c` e di `g` si
  sovrappongono;
- `f` scavalca `g`: `f.x0 < g.x0` e `f.x1 > g.x1`;
- `c` non scavalca `g`.

Se tutte e tre valgono per almeno un corridoio, il pezzo non delimita. Il senso:
alla sua altezza, la scheda sta da una parte del corridoio e il riquadro si
allunga nell'altra colonna — è un pannello di pagina, non il riquadro della
scheda.

I corridoi sono quelli **ammessi** (`column_band_gutter_rows`, `reject_reason`
nullo): un fatto della pagina, calcolato dalla pagina sola. Nessuna soglia nuova.

**La forma semplice non funziona, misurato prima.** «Il riquadro non attraversa
un corridoio» scarterebbe schede vere: `column_band` ammette corridoi larghi un
punto dentro le schede di Daggerheart — x 340-341 dentro GUERRA IN SCATOLA (Dag
idx 228), x 329-330 dentro la sirena (Dag idx 230), dove si allineano i rientri
delle liste numerate e delle caratteristiche. È lo stesso difetto per cui le
pseudo-colonne di una scheda hanno fatto cadere `column_band` ad agosto. Quei
corridoi non sono all'altezza della riga di campi, oppure la scheda stessa li
scavalca, e la forma precisa li lascia passare.

**La condizione è stata formata guardando cinque pagine** — DB idx 92; Dag idx
326, 228, 230 — con `output/resa/corridoi2.py`: il riquadro del grifone scartato,
tutti gli undici riquadri delle schede di Daggerheart tenuti. Una regola formata
su cinque pagine non è verificata da quelle cinque: lo decide la misura qui
sotto, sui tre manuali interi, e dopo il test sui manuali mai toccati.

## 2. La popolazione

DB, Apo e Dag interi, `--tabelle --schede-producer`, con il resolver collegato
come nella v1 e la strada dei riquadri dentro `run()` spenta. Riferimenti:
`output/resa/unariga` (senza riquadri nel consumer, `a210405`) e
`output/resa/riquadri` (la v1).

## 3. Che cosa deve succedere perché passi

**A. Il grifone torna intero.** DB idx 92 identico a `unariga`.

**B. I miglioramenti della v1 restano.** I colossi — Dag idx 326, 333, 334, 335,
336 — e Dag idx 228 come in `riquadri`.

**C. Le tabelle.** Ogni tabella che cambia rispetto a `unariga` si guarda
sull'immagine: **meglio** se esce una riga che la pagina stampa fuori dalla
tabella, **peggio** se ne esce una che la pagina stampa dentro. Passa se meglio ≥
peggio, e nessuna delle sei tabelle già giudicate peggiora.

**D. Nessuna prosa tagliata.** I paragrafi che cominciano in minuscola non salgono.

**E. Barra.** Test verdi, Ruff pulito, `check_eb.py` 9 su 10 con la sola Fab
idx 126.

**Veto**, lo stesso della v1: se una tabella che la pagina stampa come tabella
perde righe perché un riquadro l'ha inglobata in una scheda, la regola si ritira.

## 4. La previsione, scritta prima di guardare

- **DB identico a `unariga`**, byte per byte: la v1 aveva cambiato su DB solo
  il grifone, e la v2 ne scarta il riquadro.
- **Dag identico a `riquadri`**: su Daggerheart nessun riquadro di scheda che ho
  visto si allunga nell'altra colonna.
- **Apo invariato.**

Se Dag differisce da `riquadri`, c'è un riquadro di scheda che la condizione
scarta e che non ho visto: quello è il caso da guardare per primo.
