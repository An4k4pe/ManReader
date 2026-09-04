# Esito di `Criterio_TettoDallaMassa_v1.md` — **le due regole tengono**

Scritto il 4 settembre 2026, dopo le misure, i veti e `check_eb.py`.

## 0. Stato in una riga

Le due regole — **tetto dalla massa** e **filtro sulla riga** — passano tutti i
veti a macchina su otto manuali su otto. Il veto **D**, quello di giudizio, è
stato **emendato** perché scritto nella moneta sbagliata; l'emendamento è
dichiarato al §3 e il giudizio si rifà sul delta.

`check_eb.py`: **9 su 10**, unica differenza Fab idx 126, già a verbale.
**1641 test verdi**, ruff pulito.

## 1. I veti a macchina

| veto | esito |
| --- | --- |
| **A** — Fab: citazioni fuori, tre fasce vere dentro | **PASSA** |
| **B** — nessuna riga più lunga della mediana di corpo | **PASSA**, 0 su 8 |
| **C** — FWK produce titoli senza il meccanismo B | **PASSA** |
| **E** — punto fisso: niente promosso al tetto o sotto | **PASSA**, 0 su 8 |
| **F** — nessuna dimensione con due livelli | **PASSA**, 0 su 8 |
| **G** — `check_eb.py` 9/10 | **PASSA** |

**Il veto A**, che è il bersaglio dichiarato, colpisce entrambe le metà: su Fab
restano `83,0-87,5` → h1, `40,0` → h2, `24,9-25,0` → h3, cioè **le tre fasce vere
e solo quelle**, con 103 righe promosse. Le 519 righe a 12,0 pt
(`'Questo è il tuo mondo,'`) non sono più titoli, perché 12,0 pt porta il 2,5%
della massa del corpo ed è quindi prosa.

**Il veto C** era il più esposto, perché da esso dipendeva la legittimità di aver
ritirato il meccanismo B: FWK produce **100 titoli** con il solo tetto dalla
massa. Il capolettera a 58 pt porta lo 0,00% della massa e non è prosa comunque,
quindi non serve toccare `sized_lines` né `ir2_builder`.

## 2. I numeri

| manuale | tetto | fasce | titoli | h1/h2/h3 | riga più lunga |
| --- | ---: | ---: | ---: | --- | ---: |
| Dag | 12,0 | 5 | 92 | 26/9/57 | 38 |
| Fab | 12,0 | 3 | **88** | 3/15/70 | 28 |
| BoB | 10,2 | 9 | 702 | 194/23/485 | 71 |
| BiD | 9,6 | 7 | 592 | 15/10/567 | 63 |
| Wil | 10,2 | 9 | 502 | 42/24/436 | 122 |
| FWK | 13,0 | 3 | **100** | 10/87/3 | 53 |
| Apo | 12,0 | 3 | 66 | 4/30/32 | 23 |
| Vil | 12,0 | 4 | 90 | 5/67/18 | 22 |

Fab è tornato a **88**, il numero di quando era pulito, dopo essere passato per
626. FWK è a **100** da zero.

## 3. L'emendamento del veto D, **dichiarato**

Il veto D diceva: «cade se **una sola** riga promossa non è un titolo». Nel
campione è comparso un URL promosso a titolo su Wil —
`https://grumpybearstuff.com/pregenerati-wilderfeast/` — quindi alla lettera
cadeva.

**Ma quella riga era già un titolo prima**, e sta identica nel giro vecchio, a
`output/ir2/Wil/document.md` riga 14145. Nessuna delle due regole l'ha introdotta
e nessuna la peggiora.

**Il veto emendato:**

> Cade se una riga promossa **che non era promossa prima delle due regole** non è
> un titolo.

**Perché non è un salvataggio**, e la prova è quella che `CLAUDE.md` chiede —
deve reggere senza sapere se il meccanismo poi passa: un veto che giudica una
modifica deve guardare **ciò che la modifica produce**. Scritto com'era, la stessa
riga di codice passava o cadeva a seconda di quanti difetti antichi contenesse il
manuale su cui capitava il sorteggio: misura la pipeline, non il cambiamento.
Vale identico se il campione fosse uscito pulito, e vale contro le due regole
tanto quanto a loro favore — il delta contiene sia le righe entrate sia quelle
uscite, e una regola che togliesse titoli veri cadrebbe su questo veto molto più
facilmente che sul precedente.

Indicazione dell'utente del 4 settembre 2026: «che senso ha fare cadere una regola
per un errore che preesisteva?».

### Il delta, misurato

Le righe promosse **prima** delle due regole (cioè con il solo meccanismo C, dopo
il ritiro di A e B) contro quelle di **adesso**, sulla stessa cattura:

| manuale | prima | dopo | entrate | uscite |
| --- | ---: | ---: | ---: | ---: |
| **FWK** | **0** | **100** | **100** | 0 |
| **Wil** | 618 | 596 | 0 | **22** |
| **Dag** | 86 | 85 | 0 | **1** |
| Fab | 103 | 103 | 0 | 0 |
| BoB | 717 | 717 | 0 | 0 |
| BiD | 606 | 606 | 0 | 0 |
| Apo | 66 | 66 | 0 | 0 |
| Vil | 92 | 92 | 0 | 0 |

**Le 23 uscite sono tutte righe lunghe, e tutte correttamente tolte**: la
pubblicità di Dag (`'IMMERGITI NEI GIOCHI DI DARRINGTON PRESS & CRITICAL ROLE…'`,
92 caratteri) e ventidue righe di paragrafo di Wil, fra cui una da **792**
(`'Pubblicando questo volume, ammetto d'aver violato le principali leggi…'`) e
quattro voci di procedura da 127-144 (`'3• TRATTI. Scegli dall'elenco in
Appendice A…'`). Nessun titolo vero è uscito.

**Le 100 entrate sono tutte di FWK**, che prima produceva zero titoli. Nel
campione: `'tematiche di spiriti di stelle'`, `'daturalia'`, `'roba di silika'`,
`'la spedizione'` — titoli veri — e
`'ave ai vittoriosi morti! di nathan d. paoletta 58'`, che è un titolo vero con un
**numero di pagina fuso in coda**: il difetto del §4, non di queste regole.

**Il veto D emendato passa**: nessuna riga entrata è un non-titolo, e nessuna
uscita era un titolo.

### Che cosa comprano davvero le due regole, ridimensionato

Il delta corregge una cosa scritta al §1 di questo stesso esito. Il veto A dice
«su Fab le citazioni devono uscire», e passa — ma **passa a vuoto**: su Fab le
due regole non cambiano niente (103 prima, 103 dopo). Le 519 citazioni erano
entrate per colpa del **meccanismo B**, e sono uscite quando B è stato ritirato,
non grazie al tetto dalla massa. Sul tetto vecchio Fab dà 14,0 e sul nuovo 12,0,
e a valle promuovono le stesse identiche righe.

Il conto onesto di che cosa comprano:

- **il tetto dalla massa** compra **FWK**, e solo quello: da 0 a 100 titoli. È il
  veto C, ed è tutto lì. Senza di esso `prose_sizes` dà 58,0 e il manuale è morto;
- **il filtro sulla riga** compra le **23 righe lunghe** tolte da Wil e Dag.

Non è poco — un manuale su otto passava da zero a leggibile — ma è meno di quanto
il §1 lasciava intendere, e il §1 lo lasciava intendere perché il veto A era
scritto su un bersaglio che un altro ritiro aveva già colpito.

## 4. Tre difetti scoperti dal campione, che sono altri meccanismi

Nessuno dei tre è causato dalle due regole; tutti e tre sono visibili nel campione
e vanno aperti a parte.

**Un URL promosso a titolo**, su Wil. Pre-esistente, verificato nel giro vecchio.
Nessuna delle regole di dimensione lo può prendere: è lungo 52 caratteri contro
una mediana di corpo di 122, quindi passa anche il filtro nuovo.

**Testo raddoppiato**, su Vil: `'Valois Valois'`, `'BRAISENOIRE BRAISENOIRE'`, e
su Wil `'◈ villaggio di lala villaggio di lala'`. Sono titoli veri con il testo
duplicato — due primitive sovrapposte per l'effetto d'ombra. È un difetto di
composizione della riga, a monte dei titoli.

**Un numero di pagina fuso nel titolo**, su FWK:
`'benvenuti nel Kosmohedron 10'`, mentre lo stesso testo esce anche come h1 senza
il `10`.

## 5. Che cosa è adottato

- **Il tetto dalla massa**, `document_heading_band_policy.prose_ceiling`, soglia
  **1,8%** della massa del corpo, dentro l'altopiano misurato 1,5%-2,0%.
- **Il filtro sulla riga**, in `heading_lines`, al rapporto **1,0** sulla mediana
  di riga del corpo.
- **Il filetto di guida** (meccanismo C del criterio precedente), che resta.

`prose_sizes` **non è stato toccato**: continua a servire la scala tipografica di
`document_asset_policy`. Ciò che è cambiato è che i titoli non lo usano più.

## 6. Che cosa resta fuori

- **L'asse del font**: su Dag `PANORAMICA` a 12,0 pt in `EvelethCleanRegular`
  resta sotto il tetto e resta prosa. Debito della v2, non pagato.
- **Le schede mostro**, dichiarate sette volte.
- **Il meccanismo A** (chi non può essere titolo non vota), ritirato, con la sua
  forma corretta nel tag: arredo finestra per finestra, aggregato per pagina.
- **Il meccanismo B** (la riga alla dimensione dominante), ritirato: il tetto
  dalla massa lo rende inutile.
- **Il difetto di copertura di Vil idx 268**, pre-esistente.
