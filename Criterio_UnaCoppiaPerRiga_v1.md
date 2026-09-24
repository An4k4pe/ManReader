# Criterio — una coppia per riga: la combinazione si misura sul blocco, non sulla riga

Dichiarato il 24 settembre 2026, **prima** della misura. Richiesta dell'utente:
«almeno due coppie su una riga non regge secondo me da un po', ma non si era mai
visto; questo è la prova che è così. Misura una coppia per riga».

## 0. La prova che è così

`Esito_SchedeSuManualiMaiToccati_v1.md` §3: su sei manuali mai toccati, **1.349
righe dichiarano un campo e 19 ne dichiarano due**. Guardata riga per riga, la
carta AREA di Wil idx 137 (stampata 138) dice la stessa cosa in chiaro:

```
«Sentieri: Baia di Aso, Isola Culla, La Sgretolona, Città-Stazione»   1 campo dichiarato
«Mostri: lotangwa, shulu xie, uopang, varithan, shakoi»               1 campo dichiarato
«Umani: CSA Sud, Villaggio di Sounung, Villaggio di Da-o»             1 campo dichiarato
```

Sono i campi di una scheda, e la regola «almeno due coppie su una riga» li
scarta tutti e tre.

## 1. Il punto di progetto, e l'indicazione dell'utente

Non è il cambio di una costante. Oggi l'unità della policy è la **combinazione
di etichette che stanno sulla stessa riga**: `{ferocia, taglia}`. Con un campo
per riga una combinazione su una riga non esiste — ne serve più d'una per
formarla, quindi l'unità deve cambiare.

La prima stesura di questo criterio spostava l'unità dalla riga al **blocco**:
l'insieme delle etichette di una corsa di righe consecutive. **L'utente ha
indicato un'altra strada, prima di qualunque misura**: «se prendiamo come blocco
una riga è più funzionante e visibile».

**L'unità resta la riga, e la combinazione può avere una sola etichetta.** Un
campo dichiarato che il documento ripete almeno **tre** volte e mette sempre
nello stesso posto è una riga di campi. Le due condizioni misurate non cambiano
— ripetizione e profilo di posizione — cambia solo che l'insieme può essere di
uno.

È più funzionante perché su sei manuali mai toccati 1.349 righe portano un campo
e 19 ne portano due. Ed è più visibile perché la cosa che si conta resta quella
che si vede sulla pagina: `Mostri:` è `Mostri:`, e non l'insieme che forma con i
suoi vicini.

**Le schede che somigliano a tabelle** — indicazione dell'utente, «ci sono schede
che sono simili a tabelle, come per DIE» — sono il caso da guardare per primo al
§3.C: su DIE le righe con campi dichiarati sono nomi di attacchi
(`['doppio-speciale', 'soffiodifuoco']`), e con l'unità sulla riga `{speciale}`
diventa una combinazione ammissibile. Che un impaginato somigli a una tabella
**non** lo rende una tabella, e il giudizio si fa sull'immagine.

## 2. La popolazione

DB, Apo, Dag — dove il meccanismo è stato costruito — e i sei mai toccati: Wil,
BiD, DIE, SV, Kul, Vil. Nove manuali, `--tabelle --schede-producer`.
Riferimenti: `output/resa/rete` per i primi quattro (lo stato con la rete
accesa) e `output/resa/maitoccati/senza-*` per gli altri cinque.

## 3. Che cosa deve succedere perché passi

**A. Dove il meccanismo già funzionava, non peggiora.** Su DB e Dag ogni tabella
che cambia si giudica sull'immagine: **passa se nessuna tabella vera perde
righe** e se le sei già giudicate — DB idx 87, 90, 97, 123; Dag idx 230, 359 —
restano come sono.

**B. Dove taceva, parla.** Almeno uno dei sei manuali mai toccati ammette
combinazioni, e le schede che riconosce, guardate sull'immagine, sono schede. Su
Wil mi aspetto `{sentieri, mostri, umani}`.

**C. Il rischio noto, misurato.** Gli elenchi con `Durata:`, `Costo:`,
`Prerequisiti:` ripetuti sono la forma che può passare per scheda. Se una
combinazione del genere viene ammessa, si guarda che cosa fa: se le sue righe
escono da una tabella che la pagina stampa come tabella, è il veto.

**D. Nessuna prosa tagliata.** Su ognuno dei nove manuali i paragrafi che
cominciano in minuscola non salgono.

**E. Barra.** Test verdi, Ruff pulito, `check_eb.py` 9 su 10 con la sola Fab
idx 126.

**Veto.** Una tabella che la pagina stampa come tabella perde righe perché una
scheda se le è prese.

## 4. La previsione, scritta prima di guardare

- **DB e Dag cambiano poco ma cambiano.** Le combinazioni si fondono, e blocchi
  che prima finivano alla riga di campi ora arrivano più lontano: mi aspetto
  qualche rottura di record in più, e qualche tabella che perde ancora qualche
  riga di scheda.
- **Wil parla**, e le 22 carte AREA vengono riconosciute dai campi invece che dal
  riquadro. Se succede, la rete del criterio precedente si può togliere.
- **Almeno uno dei sei ammette una combinazione che scheda non è.** Con 1.349
  righe a un campo, qualcosa di ripetuto e allineato che schede non è ci sarà:
  la domanda non è se accade, ma se fa danno.
