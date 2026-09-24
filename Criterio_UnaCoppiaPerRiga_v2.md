# Criterio — una coppia per riga, v2: la struttura che si ripete è del blocco

Dichiarato il 24 settembre 2026, **prima** della misura. Indicazione dell'utente
dopo `Esito_UnaCoppiaPerRiga_v1.md`:

> «hai dimenticato di considerare che l'etichetta si deve ripetere in quella
> forma e sebbene uno per riga possa essere sufficiente una scheda è fatta da una
> struttura che ripete e nella tabella armi questo non c'è»

## 0. Che cosa avevo sbagliato

La v1 metteva l'unità sulla **riga**: un campo dichiarato, ripetuto tre volte e
sempre nello stesso posto, era una riga di campi. Con quella regola le celle
della colonna CARATTERISTICA delle tabelle delle armi di Daggerheart — ognuna un
`Versatile:`, un `Potente:`, un `Pesante:` — passavano, perché ognuna si ripete e
sta sempre alla stessa x. Ventitré pagine di Dag perdevano celle.

L'errore non era mettere una coppia per riga: era prendere **l'etichetta sola**
per la cosa che si ripete. Quello che si ripete in una scheda è la **struttura**:
un insieme di campi che stanno insieme.

## 1. La regola

- **Un blocco** è una corsa di righe consecutive che dichiarano almeno un campo,
  con il salto massimo di oggi (due righe). Una riga sola può essere un blocco.
- **La combinazione è l'insieme delle etichette del blocco**, e deve avere
  **almeno due etichette distinte**. Un'etichetta sola non è una struttura.
- Restano le due condizioni già misurate: la combinazione si ripete almeno
  **tre** volte, e un solo **profilo di posizione** ne copre la maggioranza. Il
  profilo si misura dal bordo sinistro del blocco.

«Almeno due coppie» non sparisce: **si sposta dalla riga al blocco**. È la
differenza fra `Sentieri:` / `Mostri:` / `Umani:` — tre righe, un campo ciascuna,
un blocco — e `Versatile:` dentro una cella, che è un blocco di uno.

## 2. Che cosa dice la misura di esplorazione

`output/resa/blocchi.py`, sulle strutture di blocco, prima di scrivere la regola:

| manuale | struttura | volte | che cos'è |
| --- | --- | ---: | --- |
| Wil | `{sentieri, mostri, umani}` | 36 | le carte AREA |
| DB | `{abilità, armatura, armi, dannobonus, movimento}` | 5 | le schede |
| DB | `{armatura, ferocia, movimento, taglia}` | 3 | le schede |
| Dag | `{difficoltà, impeti, potenzialiavversari}` | 18 | le schede d'ambiente |
| Dag | `{pesante}` | 17 | **una cella** della tabella delle armi |
| Dag | `{affidabile}` | 16 | **una cella** della tabella delle armi |
| Dag | `{esempio}`, `{suggerimento}` | 29, 27 | box di testo |
| Wil | `{passiva}` | 26 | voci di abilità |

Con la soglia di due etichette distinte, le prime quattro passano e le altre
quattro cadono. Le schede d'ambiente di Daggerheart, che nessuna versione
precedente vedeva, entrano.

## 3. La popolazione

Gli stessi nove manuali della v1: DB, Apo, Dag, Wil, BiD, DIE, SV, Kul, Vil,
`--tabelle --schede-producer`. Riferimenti: `output/resa/rete` per DB, Apo, Dag e
Wil; `output/resa/maitoccati/senza-*` per BiD, DIE, SV, Kul, Vil.

## 4. Che cosa deve succedere perché passi

**A. Il danno della v1 non c'è più.** Sul capitolo delle armi di Daggerheart
(Dag idx 116-130) nessuna cella esce dalla tabella.

**B. Dove taceva, parla, e sono schede.** Wil riconosce le carte AREA, e la
pagina si guarda sull'immagine.

**C. Le tabelle.** Ogni tabella che cambia si giudica sull'immagine: **meglio**
se esce una riga che la pagina stampa fuori dalla tabella, **peggio** se ne esce
una che la pagina stampa dentro. Passa se meglio ≥ peggio, e le sei già
giudicate non peggiorano.

**D. Nessuna prosa tagliata.** I paragrafi che cominciano in minuscola non
salgono su nessuno dei nove.

**E. Barra.** Test verdi, Ruff pulito, `check_eb.py` 9 su 10 con la sola Fab
idx 126.

**Veto.** Una tabella che la pagina stampa come tabella perde righe perché una
scheda se le è prese.

## 5. La previsione

- **A passa**: le celle delle armi sono blocchi di un'etichetta sola.
- **B passa**: Wil riconosce 36 carte AREA.
- **Dag guadagna le schede d'ambiente** (`{difficoltà, impeti, potenziali
  avversari}`, 18 volte) che prima non vedeva.
- **Il rischio che dichiaro adesso**: su DB la struttura `{1,2,3,4,5,6}` compare
  4 volte, ed è la riga `Tira un D6. 1: … 2: …` della tabella dei tesori. Ha sei
  etichette distinte, quindi la soglia non la ferma: deve fermarla il profilo di
  posizione, come nella v1 del requisito posizionale. Se non la ferma, la
  tabella dei tesori di DB idx 123 perde righe, e quello è il veto.
- **D è il veto più probabile**: `opens_a_record` trova i due punti su
  un'etichetta in mezzo alla riga, e con una coppia per riga i blocchi sono di
  più. La v1 aveva due orfani nuovi su nove manuali.
