# Esito — il nucleo, v2: **passa**

Misura di `Criterio_NucleoCheSiContaInsieme_v2.md`, 25 settembre 2026, variante
`--schede-rete sempre`. Rese: `output/resa/nucleo2/{Dag,Wil}`; gli altri sette
manuali coincidono con la v1 (nuclei identici, verificato: la regola della scala
toglie `{rango2, rango3, rango4}` su Dag e `{#1, #2, #3}` su Wil, nient'altro).

## 1. I veti

| veto | esito |
| --- | --- |
| **A** il veto della v1 non c'è più | **sì** — Dag idx 324: 0 celle escono dalle tabelle delle armi |
| **B** i meglio della v1 restano | **sì** — DB idx 90 e 119, Dag idx 50 e 361, BiD idx 304, 24 carte AREA di Wil |
| **C** nessuna tabella vera perde righe | **sì**, su tutti e nove |
| **D** prosa tagliata | **sì con l'eccezione dichiarata**: un solo orfano nuovo, Wil idx 148, quello noto |
| **E** barra | **sì** — 1774 test verdi, Ruff pulito, E-B 9 su 10 con la sola Fab idx 126 |

## 2. Il conto contro lo stato di partenza

| manuale | tabelle | paragrafi | orfani |
| --- | --- | --- | --- |
| DB | 2 migliorate | 2817 → 2831 | 71 → 71 |
| Apo | invariato | = | = |
| Dag | 2 migliorate | 7686 → **7748** | 124 → 124 |
| Wil | **24 migliorate**, 0 peggiorate | 4819 → 4839 | 115 → 116 |
| BiD | 1 migliorata | 5721 → 5728 | 711 → 711 |
| DIE, SV, Kul, Vil | invariati | = | = |

Nessuna tabella peggiora, su nessun manuale.

## 3. Che cosa riconosce, e su quale fondamento

| manuale | nucleo | che cos'è |
| --- | --- | --- |
| DB | `abilità, ali, armatura, armi, dannobonus, ferocia, movimento, resistenza, taglia` | la scheda di Dragonbane, tutta |
| Dag | fra gli altri, 15 etichette dalle schede avversario | le schede avversario e d'ambiente |
| Wil | `sentieri, mostri, umani` | le carte AREA |
| BiD | `risorsedirilievo, territorio`; `edifici, scene, strade`; la scala degli esiti | le schede delle fazioni e dei distretti |
| Kul | `acume, fermezza, impeto, prudenza` | le caratteristiche |

La regola, per intero: una riga di campi dichiara almeno **una** coppia con i
due punti; un blocco è una corsa di righe di campi con almeno **due** etichette
distinte; è una scheda se porta almeno **due etichette di uno stesso nucleo** —
un gruppo che il documento conta insieme — e il nucleo non è una **scala**.
Nessuna soglia nuova: le due relazioni di conteggio sono quelle misurate il
14 settembre.

## 4. Che cosa resta

- **L'orfano di Wil idx 148**: la seconda riga del valore di `Mostri:` —
  «zaswang, ziziwen» — va a capo nella carta, e uscita dalla tabella non si
  riattacca al suo campo. È il ricongiungimento delle righe di continuazione
  dentro una scheda, e non dipende dai nuclei.
- **I nuclei falsi innocui**: Kul `{claudio, river, simone}` (i parlanti di un
  esempio di gioco), Vil `{0 segni … 4+ segni}` (una scala che la regola non
  riconosce perché `segno` e `segni` sono due radici). Nessuno dei due cambia
  una riga della resa.
- **DIE e SV non riconoscono niente.** L'utente ha indicato che su DIE ci sono
  schede simili a tabelle: i campi lì non si dichiarano con i due punti, o non
  si contano insieme, e questa regola non le vede.
- **La vecchia strada dei riquadri resta accesa accanto ai nuclei**: è un aiuto,
  non l'unica voce — una scheda si riconosce dai nuclei anche senza riquadro.
