# Criterio — se la policy tace, la vecchia strada dei riquadri resta accesa

Dichiarato il 24 settembre 2026, **prima** della misura. Richiesta dell'utente:
«fai la piccola».

## 0. Il difetto

`Esito_SchedeSuManualiMaiToccati_v1.md` §4: su Wil, `--schede-producer`
peggiora 22 tabelle. Non perché una regola nuova sbagli, ma perché la bandiera
**spegne** la vecchia strada dei riquadri dentro `run()` — la Resolution dovrebbe
sostituirla — e con la policy che non ammette nessuna combinazione nessuno la
sostituisce. Le carte AREA di Wilder restano senza riconoscimento, e i loro
`TRATTI` finiscono dentro la tabella `INGREDIENTI`.

## 1. La regola

La vecchia strada si spegne solo quando la policy ha **qualcosa da dire**: se
`stat_block_fields.combinations` è vuoto, `stat_block_regions` dentro `run()`
resta acceso.

Una riga di codice. Non cambia niente di ciò che la Resolution decide.

## 2. Che cos'è, e che cosa non è

**Non è un allargamento del dominio.** È il ripristino dello stato precedente
dove il meccanismo nuovo non parla: dove parla, la Resolution resta l'unica
voce.

**È un ponte, e va detto.** L'utente ha stabilito il 12 settembre che il
riquadro «può essere un elemento, ma non lo userei come unico discriminante».
Nella regola della Resolution il riquadro **non** discrimina: allarga soltanto
una scheda che i campi hanno già identificato. Nella vecchia strada, invece,
senza riquadro non c'è scheda — quindi il riquadro è necessario, cioè dominante.
Questo criterio la rimette in piedi **solo come rete**, e la sua vita finisce
quando «una coppia per riga» sarà misurata: se regge, la rete si toglie.

## 3. La misura

DB, Apo, Dag e Wil, `--tabelle --schede-producer`, contro:

- `output/resa/riquadri3` per DB, Apo, Dag (la v3, stato di `c37f428`);
- `output/resa/maitoccati/senza-Wil` per Wil.

## 4. Che cosa deve succedere perché passi

**A. Dove la policy parla, niente cambia.** DB e Dag identici a `riquadri3` byte
per byte.

**B. Dove la policy tace, torna lo stato di prima.** Wil identico a
`senza-Wil` byte per byte, cioè le 22 tabelle non peggiorano più. Apo identico a
`riquadri3`: la policy tace, ma la vecchia strada lì non trova niente, quindi
riaccenderla non cambia nulla.

**C. Barra.** Test verdi, Ruff pulito, `check_eb.py` 9 su 10 con la sola Fab
idx 126.

**Veto.** Se Apo cambia, la vecchia strada su Apocalisse trova schede dove non
ce ne sono, e riaccenderla non è gratis.

## 5. La previsione

A, B e C passano tutti, e le tre rese sono identiche byte per byte ai loro
riferimenti. È un ripristino, non una regola nuova: se qualcosa si muove fuori da
Wil, ho sbagliato a leggere le due diramazioni di `run()`.
