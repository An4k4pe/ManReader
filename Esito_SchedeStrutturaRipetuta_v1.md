# Le schede dalla struttura ripetuta — esito

13-14 settembre 2026. Criterio del giro su DrM: `Criterio_SchedeDrM_v1.md`.
Pagine per indice 0-based, stampata fra parentesi quadre.

## 1. Il verdetto su DrM della regola dei riquadri: caduta

`main_ir2.py --tabelle --schede-struttura` con la regola di allora (riquadro +
campi fuori dalle colonne + struttura che ricorre), su tutte le 385 pagine di
Draw Steel: Monsters. 25 riquadri candidati, 10 tenuti: 5 illustrazioni sotto cui
passa la coda di una scheda e 5 box dei tesori. Nelle 10 pagine estratte col seed
`20260913` fra quelle senza schede, 5 sono piene di schede mostro (idx 109, 137,
214, 217, 244). **Causa**: le schede di Draw Steel non hanno un riquadro che le
racchiuda, e la regola cercava i confini nel riquadro. La predizione P1 del
criterio («trova schede») regge alla lettera e non dice niente.

Indicazione dell'utente: la struttura ripetuta e' la base, il riquadro solo un
aiuto; i box dei tesori sono schede se si ripetono e stanno vicino al resto.

## 2. Tre strade provate e chiuse prima di quella che regge

| strada | script | esito |
| --- | --- | --- |
| un gettone di struttura = etichetta o riga di uno stile presente su tre pagine | `esperimenti_statblock/istanze_ripetute.py` | quasi tutto e' «scheda»: 537 regioni su Daggerheart, 1432 su DrM |
| il metodo congelato `pila2.py` | `esperimenti_statblock/pila2.py` | su DrM 52 gruppi sovrapposti: la parte libera spezza ogni scheda in nuclei |
| riquadro + colonne + ricorrenza | `esperimenti_statblock/struttura_ricorrente.py` | cade su DrM (§1) |

## 3. La regola che regge: etichette che si contano insieme

`esperimenti_statblock/strutture_contate.py`, poi `stat_block_regions.py`
(`repeated_structures`, `stat_blocks_from_structures`).

- **Legame, senza soglie**: due etichette si contano insieme se compaiono insieme
  su almeno tre pagine e, sulle pagine della piu' rara, con lo stesso conteggio
  nella maggioranza dei casi. DrM, una pagina con 4 mostri: 4 Immunity, 4
  Movement, 4 Weakness, ma 11 Effect.
- **Istanze**: un'etichetta gia' vista che ricompare apre una scheda nuova; almeno
  due etichette diverse per istanza.
- **Tabella, non scheda**, dall'indicazione dell'utente «righe tutte ordinate»:
  ogni riga con un'etichetta sola, e ogni etichetta allineata ad almeno un'altra.
- **Nome**: fra gli stili presenti nella maggioranza degli spazi prima delle
  istanze, il piu' grande.

Due tentativi del test «tabella» caduti nello stesso giro: una colonna di
tabella allineata su una x sola (le armi scavalcano due tabelle affiancate) e una
cella a sinistra sulla riga (su una pagina a due colonne la cella a sinistra e'
la colonna accanto, e tutti gli avversari diventavano tabella).

Misure sui manuali interi, verita' una riga per scheda:

| | struttura principale | istanze | con la riga-verita' | fuse | nomi |
| --- | --- | --- | --- | --- | --- |
| Daggerheart (`thresholds`) | avversari + ambienti | 152 | 130 su 130 | 0 | 134 |
| Dragonbane Quickstart (`movimento`) | mostri | 5 | 5 | 0 | 5 su 5, Wight compreso |
| DB (`movimento`) | mostri + PNG | 29 | 24 su 25 | 0 | 16 |
| DrM (`weakness`) | mostri | 511 | 436 su 436 | 0 | 440 |

Strutture tenute che schede non sono: classi e domini su Daggerheart, AGI/COS/FOR
su DB. Strutture riconosciute come tabelle: proprieta' delle armi (Daggerheart),
abilita' della scheda personaggio e uscite delle stanze (Quickstart), box dei
tesori e frammenti di glifi (DrM).

## 4. In IR 2

Dietro `main_ir2.py --schede-struttura`: una prima passata raccoglie le righe di
tutte le pagine (`stat_block_line_facts_of_page`), le strutture si calcolano una
volta, la resa trova le istanze per pagina. `run()` e' stato fattorizzato in
`page_reading_facts` e `stat_block_inputs`, senza cambiare cio' che fa.

Il nome diventa titolo per **eccezione dichiarata nello script dei titoli**
(`document_heading_policy.structure_name_level`, decisione dell'utente del 13
settembre): i nomi stanno alla dimensione della prosa (Daggerheart 147 su 147 a
12,0 pt con il tetto a 12,0; Dragonbane a 10,0 come il corpo), gli altri filtri
dei titoli restano, e un titolo per dimensione non viene declassato.

Fra riquadri sovrapposti della regola di 3a vince ora il piu' stretto col nome
(Pipistrelli, Dragonbane idx 31; goblin, DB idx 116). Una tabella che attraversa
una scheda resta bloccata: la variante che le toglieva solo le righe della scheda
ricostruiva tabelle rotte ed e' stata ritirata.

Giro con tabelle (Daggerheart 36-56, Quickstart intero, DB 84-125, DrM 36-60): su
DrM 25 righe Weakness e titoli per quasi tutti i mostri (Ajax the Invincible,
Angulotl Cleaver, Clawfish, Arixx, Basilisk…), 2 mancati su pagine con due mostri
(idx 55, 59). **Giudizio dell'utente**: «con il riconoscimento direi che puo'
andare bene».

**Senza flag** l'uscita e' identica byte per byte a 3a su Daggerheart, Quickstart
e DrM; su DB cambia solo idx 92 (GRIFONE), per la regola del riquadro piu'
stretto: sparisce un titolo falso di prosa, e la tabella degli attacchi, che era
rotta, non si costruisce piu'.

## 5. Aperto

- **La fine della scheda**: vedi §6.
- **L'ordine dentro la scheda** (3c): su DrM le due meta' del blocco si mescolano
  e i valori restano staccati dalle etichette.
- Il segnale «da verificare» per le schede personaggio; le strutture di regole
  prese per schede; il verdetto su un sistema non ancora visto.

## 6. La fine della scheda (14 settembre 2026)

Domanda dell'utente: la struttura si ripete, poi c'e' una parte libera; dove
finisce la scheda e comincia la prosa?

**Gli stili non la separano**, misurato (`esperimenti_statblock/fine_scheda.py`):
l'ultima scheda della pagina, estesa finche' le righe sono in uno stile che sta in
maggioranza dentro le schede delimitate, si ferma subito su tre manuali su quattro,
perche' la parte libera usa gli stili della prosa.

**Regge: la scheda finisce a cio' che la interrompe** (`_block_tail` in
`stat_block_regions.py`): il nome di un'altra scheda, una riga alla dimensione di
una fascia di titolo del documento, il bordo del riquadro che la contiene quando
c'e', la scheda successiva, la fine della pagina. Le righe di un **riquadro
estraneo** -- almeno due righe, che non tocca ne' la scheda ne' un riquadro che la
tocca -- si saltano senza chiudere la scheda.

Tre correzioni nello stesso giro, ognuna vista sulle pagine disegnate:

| tentativo | caduto su |
| --- | --- |
| una riga dentro un riquadro che non contiene la scheda la chiude | le fasce di una riga dietro i nomi delle capacita' di DrM tagliavano le code; la pergamena degli attacchi dei Pipistrelli, che esce di 8 pt da quella della scheda, li lasciava fuori |
| il riquadro estraneo chiude la scheda | su DrM idx 43 il box laterale sta, nell'ordine di lettura, in mezzo alla scheda di Angulotl Wave, e ne tagliava la seconda meta' |

Verifica a vista sulle pagine disegnate (DrM idx 41, 43, 59; Daggerheart idx 38,
52; Quickstart idx 29, 31; DB idx 91, 116): le schede finiscono dove finiscono.
Resta il numero di pagina in coda all'ultima scheda di DrM, che l'arredo toglie
dal corpo; e su DB idx 91 il nome e' il titolo della pagina GOBLIN, con la
descrizione in prosa dentro la prima delle due varianti.

Diagnostica per pagina, fuori dall'IR: `schede.json` nella cartella della pagina.
