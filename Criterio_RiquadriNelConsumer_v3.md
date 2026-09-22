# Criterio — i riquadri nel consumer, v3: conta il contenuto, non il bordo

Dichiarato il 22 settembre 2026, **prima** della misura. Richiesta dell'utente
dopo `Esito_RiquadriNelConsumer_v2.md`: «sì, fai la v3».

## 0. Che cosa cambia

La v2 scarta un pezzo di riquadro se, all'altezza della scheda, **il pezzo**
scavalca un corridoio che la scheda non scavalca. Guarda dove sta il **bordo**
del riquadro, e per questo su Dag idx 214 (stampata 213) scarta tre riquadri di
schede vere: `column_band` ammette un corridoio a x 322-324, che è lo spazio fra
il bordo sinistro dei riquadri di destra (x 319) e il testo dentro (x ≈331).

La v3 cambia la terza condizione, e solo quella: non «il bordo del pezzo passa
dall'altra parte», ma «**dall'altra parte c'è testo del pezzo**».

## 1. La regola

Un pezzo non delimita una scheda se esiste un corridoio ammesso `g` tale che:

- `g` è all'altezza della scheda: gli intervalli verticali della proposta
  accettata `c` e di `g` si sovrappongono;
- `c` non scavalca `g`, cioè sta tutta da una parte;
- il pezzo contiene **almeno una riga di testo dall'altra parte** di `g`
  rispetto a `c`.

Dall'altra parte vuol dire: se `c` sta a sinistra (`c.x1 <= g.x0`), una riga con
il centro a destra di `g.x1`; se `c` sta a destra (`c.x0 >= g.x1`), una riga con
il centro a sinistra di `g.x0`.

Tutto il resto della v1 e della v2 resta identico: solo riquadri disegnati,
`split_frame` nei massimali, contenimento **per intero** della proposta, fra
pezzi annidati vince il più grande, identità dalla policy.

Nessuna soglia nuova: sono relazioni fra rettangoli e il centro di una riga, la
stessa appartenenza che usano `split_frame` e `column_band`.

## 2. Perché questa forma e non le due precedenti

| pagina | che cosa c'è oltre il corridoio, dentro il pezzo | v2 | v3 |
| --- | --- | --- | --- |
| DB idx 92, grifone | la tabella `D6 ATTACCO`, un'altra colonna di testo | scarta | **scarta** |
| Dag idx 214, i tre riquadri di destra | niente: solo il bordo del riquadro | scarta | **tiene** |
| Dag idx 228, 230, 326 | niente | tiene | tiene |

## 3. La popolazione

DB, Apo e Dag interi, `--tabelle --schede-producer`. Riferimenti:
`output/resa/unariga` (`a210405`), `output/resa/riquadri` (v1),
`output/resa/riquadri2` (v2).

## 4. Che cosa deve succedere perché passi

**A. Il grifone resta intero.** DB identico a `unariga` byte per byte.

**B. Dag identico alla v1** (`output/resa/riquadri`): tutti i miglioramenti della
v1, e Dag idx 214 recuperato rispetto alla v2.

**C. Le tabelle.** Rispetto a `unariga`: una sola cambia, la fantasma di Dag idx
228, e nessuna tabella vera perde righe.

**D. Nessuna prosa tagliata.** I paragrafi che cominciano in minuscola non salgono.

**E. Barra.** Test verdi, Ruff pulito, `check_eb.py` 9 su 10 con la sola Fab idx 126.

**Veto**, lo stesso dalla v1: se una tabella che la pagina stampa come tabella
perde righe perché un riquadro l'ha inglobata in una scheda, la regola si ritira.

## 5. La previsione

DB identico a `unariga`, Apo invariato, **Dag identico alla v1**. Se Dag
differisce dalla v1, c'è un pezzo che contiene testo oltre un corridoio e che la
v1 teneva: quella pagina si guarda per prima, e va giudicata sull'immagine come
il grifone.
