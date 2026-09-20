# Esito — una riga di campi sola basta: **passa**

Misura di `Criterio_SchedaDaUnaRigaSola_v1.md`, 20 settembre 2026.
Prima: `output/resa/producer`. Dopo: `output/resa/unariga`.
Riferimento: `output/resa/senza-riparo`, la strada vecchia committata in `d59a22f`.

## 1. La previsione era giusta, tutta

Il §4 diceva: «le tre tornano, le quattro no, e le tabelle non si muovono; mi
aspetto che il confronto con `senza-riparo` scenda da 9 paragrafi di differenza
a **6**, tutti dell'apostrofo».

| veto | esito |
| --- | --- |
| **A** le tre perdite vere tornano | **sì** — Dag idx 326, 333 e 335 spariscono dalla lista delle pagine cambiate |
| **B** le quattro dell'apostrofo restano perse | **sì** — Dag idx 36, 37, 359, 360 |
| **C** le tabelle non si muovono | **sì** |
| **D** nessuna rottura di prosa nuova | **sì** |
| **E** barra | **sì** — 1753 test verdi, Ruff pulito, barra E-B 9 su 10 con la sola Fab idx 126 |

```
producer     -> unariga   DB uguali 70   Apo uguali 16   Dag uguali 61
senza-riparo -> unariga   DB uguali 70   Apo uguali 16   Dag uguali 61
              (0 ridotte, 0 SPARITE, 0 CRESCIUTE, 0 nuove ovunque)
```

Contro la strada vecchia i paragrafi passano da 9 pagine cambiate a **4**, e da
9 paragrafi di differenza a 6:

```
DB:  2817 -> 2817   pagine cambiate 0
Apo: 1490 -> 1490   pagine cambiate 0
Dag: 7661 -> 7655   pagine cambiate 4
```

**Veto D in numeri.** I paragrafi che cominciano in minuscola — una frase
orfana, cioè prosa tagliata — non si muovono di uno fra le tre rese:

| manuale | vecchia | producer | unariga |
| --- | ---: | ---: | ---: |
| DB | 71 | 71 | **71** |
| Apo | 38 | 38 | **38** |
| Dag | 124 | 124 | **124** |

## 2. Che cosa era il minimo di due righe

Una **seconda guardia nel posto sbagliato**. Chiedeva al producer di distinguere
una scheda da una tabella, che è precisamente ciò che un producer non può fare:
la ripetizione nel documento non si vede da una pagina sola. A scartare le
proposte sbagliate è il consumer, e lo fa — la tabella dei tesori di DB idx 123
non perde una riga, con il minimo o senza.

Il prezzo del minimo era misurabile: i colossi di Daggerheart dichiarano
`Soglie: 11/22 | Stress: 6` su una riga che nella pagina sta da sola, e il
minimo le faceva sparire insieme alla loro rottura di paragrafo.

**Non è la regola che l'utente ha rifiutato.** L'11 settembre era caduta «una
**coppia** per riga»: accettare righe con un solo campo. Qui la riga deve
portarne due come prima; cambia solo quante righe servono a fare un blocco. Un
test lo fissa (`test_una_riga_con_una_coppia_sola_non_basta`).

## 3. Che cosa resta, e perché non si tocca

Le quattro pagine dell'apostrofo restano diverse dalla strada vecchia, e devono
restarlo. Su Dag idx 36, 37, 359 e 360 il producer trova **zero** righe di
campi: `Vista a Volo d'Uccello:` e `Privilegio dell'Ibrido:` sono
**un'etichetta sola**, e la strada vecchia le contava per due perché l'apostrofo
spezza lo span. La rottura di paragrafo che si perde era giusta per una ragione
sbagliata, e recuperarla vorrebbe dire rimettere l'artefatto.

Se quelle righe vanno recuperate, la strada è un'altra: riconoscere che
`Privilegio dell'Ibrido:` è **una** etichetta ricucendo gli span spezzati
dall'apostrofo. È un giro suo, da dichiarare e misurare a parte.

## 4. Correzione a verbale

`Esito_SchedeDalProducerAIR2_v1.md` §2 e §5, e il messaggio del commit `3d4a879`,
attribuiscono queste perdite alla nozione di riga e propongono di unire le righe
di sorgente sulla stessa banda orizzontale. **La causa non era quella**: su Dag
idx 326 `Dimensioni:` e `Segmenti:` sono righe impilate, non affiancate, e
nessuna banda le unirebbe. Era il minimo di due righe, una costante nel
producer.
