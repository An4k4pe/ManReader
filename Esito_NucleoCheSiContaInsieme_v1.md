# Esito — il nucleo che si conta insieme, v1: **il veto scatta su una scala**

Misura di `Criterio_NucleoCheSiContaInsieme_v1.md`, 25 settembre 2026. Rese in
`output/resa/nucleo/{muta,sempre}-*`.

## 1. Il conto

| manuale | muta | sempre | paragrafi | orfani |
| --- | --- | --- | --- | --- |
| DB | 2 ridotte | 2 ridotte | 2817 → 2831 | 71 → 71 |
| Apo | invariato | — | = | = |
| Dag | 3 ridotte | 3 ridotte | 7686 → **7763** | 124 → 123 |
| Wil | **21 cresciute**, 15 ridotte | **0 cresciute**, 24 ridotte | 4819 → 4839 (sempre) | 115 → **116** (sempre) |
| BiD | 1 ridotta | 1 ridotta | 5721 → 5728 | 711 → 711 |
| DIE, SV, Kul, Vil | invariati | invariati | = | = |

## 2. Il giudizio, sull'immagine

| pagina | che cosa esce dalla tabella | giudizio |
| --- | --- | --- |
| DB idx 90, il gigante | `Armi:`, campo della scheda | **meglio** |
| DB idx 119 | una riga di prosa narrativa | **meglio** |
| Dag idx 50 e 361, schede del compagno | le opzioni di `ADDESTRAMENTO`; la pagina non stampa tabelle | **meglio** |
| BiD idx 304, schede delle fazioni | `Territorio:`, il seguito di `PNG:`; l'unica tabella è il riquadro degli orologi | **meglio** |
| Wil, 24 carte AREA (sempre) | `Sentieri:`, `Mostri:`, `Umani:` e i `TRATTI` | **meglio** |
| Wil, 21 carte AREA (muta) | i `TRATTI` **entrano** in tabella | **peggio** |
| **Dag idx 324 (stampata 323)** | celle di due tabelle di armi | **VETO** |

## 3. Il veto

Dag idx 324 stampa due tabelle vere, `ARMI PRIMARIE` e `ARMI SECONDARIE`, con
intestazione `NOME | TRATTO | PORTATA | DANNO | IMPUGNATURA | CARATTERISTICA`.
La colonna DANNO impila in una cella quattro righe:

```
Rango 1: 1d6+2 fis
Rango 2: 1d6+5 fis
Rango 3: 1d6+8 fis
Rango 4: 1d6+11 fis
```

Il documento conta davvero insieme `{rango2, rango3, rango4}` — ogni arma li ha —
quindi è un nucleo, e il blocco ne porta più di due. Quindici celle escono dalla
tabella. È **esattamente il rischio dichiarato al §2 del criterio**: «se un
manuale mette due celle in righe consecutive, il blocco porta due etichette dello
stesso nucleo e passa».

## 4. Che cosa è caduto

Non il nucleo: la sua definizione è troppo generosa su un punto preciso.
`Rango 1:` … `Rango 4:` non sono **campi diversi**: sono la stessa parola con un
numero che sale — una **scala**. Anche il nucleo falso di Wil, `{#1, #2, #3}`, è
una scala. I campi di una scheda sono nomi diversi: `Ferocia`, `Taglia`,
`Movimento`; `Sentieri`, `Mostri`, `Umani`; `Territorio`, `Risorse di Rilievo`.

## 5. Le due varianti

**sempre** è migliore di **muta** su Wil, dove decide tutto: 24 carte AREA
migliorano invece di 21 peggiorare. Sugli altri manuali coincidono.

Costa un orfano: su Wil idx 148 la seconda riga del valore di `Mostri:` —
«zaswang, ziziwen» — va a capo nella carta, esce dalla tabella, e non si
riattacca al suo campo. Il veto D è scritto stretto — «non salgono» — e sale di
uno.

## 6. Conseguenza

La v1 cade sul veto. La v2 esclude le scale e usa la variante **sempre**:
`Criterio_NucleoCheSiContaInsieme_v2.md`.
