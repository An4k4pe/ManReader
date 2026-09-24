# Esito — la struttura del blocco: **risolve le armi, ma costa Daggerheart**

Misura di `Criterio_UnaCoppiaPerRiga_v2.md`, 24 settembre 2026. Nove manuali,
resa in `output/resa/struttura2`. Riferimenti: `output/resa/rete` (DB, Apo, Dag,
Wil) e `output/resa/maitoccati/senza-*` (BiD, DIE, SV, Kul, Vil).

## 1. L'indicazione dell'utente era giusta, e la misura la conferma

«Nella tabella armi questo non c'è». Con l'unità sul blocco e la soglia di due
etichette distinte, **le celle della tabella delle armi cadono tutte**: su Dag
nessuna tabella perde una riga, contro le 23 pagine danneggiate dalla v1.

Le strutture ammesse sono poche e quasi tutte giuste:

| manuale | strutture ammesse |
| --- | --- |
| DB | `{armatura, ferocia, movimento, taglia}`, `{armatura, armi, movimento}` |
| Dag | `{difficoltà, impeti, potenzialiavversari}` e altre tre |
| Wil | `{mostri, sentieri, umani}`, `{d, r}` |
| BiD | `{edifici, strade}`, `{successocritico, successoparziale(4/5), successopieno(6)}` |
| SV | `{abilitàdirilievo, giocatrice}` |
| Apo, DIE, Kul, Vil | **nessuna** |

**Il rischio dichiarato al §5 non si è avverato**: `{1,2,3,4,5,6}` della tabella
dei tesori di DB non è ammessa. L'ha fermata il profilo di posizione, come
previsto.

**Su Wil i tre campi si leggono**, ognuno sulla sua riga:

```
**Sentieri:** Baia di Aso, Isola Culla, La Sgretolona, Città-Stazione di Seabounty *(via treno)*.
**Mostri:** lotangwa, shulu xie, uopang, varithan, shakoi
**Umani:** CSA Sud, Villaggio di Sounung, Villaggio di Da-o
```

## 2. Ma il veto C cade, e il prezzo su Daggerheart è grosso

| veto | esito |
| --- | --- |
| **A** il danno della v1 non c'è più | **sì** — Dag: 60 tabelle uguali, 0 ridotte |
| **B** dove taceva parla, e sono schede | **sì** — Wil, `{mostri, sentieri, umani}` |
| **C** meglio ≥ peggio sulle tabelle | **CADE** — 1 meglio (DB idx 90), 21 peggio (Wil) |
| **D** nessuna prosa tagliata | **sì** — orfani invariati su tutti e nove |
| **E** barra | non eseguita: il veto ferma la misura |

**E c'è un costo che nessun veto sorvegliava: Dag perde 815 paragrafi.** La
sirena torna com'era prima del 20 settembre:

```
prima   **Motivazioni e Tattiche:** Attirare le prede, divorare…
        **Diffi coltà:** 14 | **Soglie:** 9/18 | **PF:** 5 | **Stress:** 3
        **ATT:** +2 | **Mascella Disarticolata:** Mischia | 2d6+3 fi s

adesso  SIRENA *Sicario di Rango …* **Motivazioni e Tattiche:** Attirare le prede…
        **Diffi coltà:** 14 | … | **Stress:** 3 **ATT:** +2 | **Mascella Disarticolata:** …
```

**La causa, precisa**: l'insieme del blocco di una scheda avversario contiene il
nome dell'arma — `mascella disarticolata`, `sferzata d'ali`, `lancia` — che
cambia a ogni creatura. L'insieme **esatto** non si ripete mai tre volte, quindi
nessuna scheda avversario viene riconosciuta.

**E i 21 peggioramenti di Wil** sono i `TRATTI` che rientrano nella tabella: la
carta AREA ha un fondo **raster**, quindi il riquadro non può allargare la
scheda, e la vecchia strada è spenta perché ora la policy parla.

## 3. Che cosa hanno stabilito le due misure, insieme

- **v1, unità sulla riga**: prende le celle di tabella. Troppo larga.
- **v2, unità sul blocco con insieme esatto**: perde le schede i cui campi
  variano. Troppo stretta.

Il punto giusto sta in mezzo, e ha già un nome in questo albero: le etichette che
**si contano insieme**. `stat_block_regions._bound_label_groups` lega due
etichette se compaiono insieme su almeno tre pagine e, dove la più rara compare,
hanno lo stesso conteggio nella maggioranza dei casi — misurato il 14 settembre
su Daggerheart, Dragonbane, DrM. Un nucleo che si ripete tollera che intorno ci
siano etichette variabili: `{difficoltà, soglie, pf, stress}` è il nucleo della
sirena, e `mascella disarticolata` gli sta accanto senza rompere la struttura.

È la strada che la diagnosi indica, e va dichiarata e misurata a parte.

## 4. Conseguenza

La regola si ritira: il codice torna a `e2d2f53`. Restano in albero
`output/resa/blocchi.py`, che misura le strutture di blocco, e questo verbale.
