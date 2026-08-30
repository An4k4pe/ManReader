# Esito — l'emendamento **cade su Fab**, e il difetto di Vil resta aperto

**Stato in una riga**: l'emendamento fa quello per cui è scritto — su Vil le voci
d'elenco passano da **0 a 29**, su Apo da 6 a 11 — e ne produce **22 false** su Fab
e Dag. Il veto §3.A cade, l'emendamento è ritirato, e il difetto che l'utente ha
segnalato **resta**.

---

## 1. Prima di tutto, un errore di processo che ho commesso io

Il criterio dichiarava **un** emendamento: il glifo da solo sulla sua riga conta
come separato. L'ho implementato, e su Vil `h` è passato da **0 a 37 aperture** —
e **non è diventato marcatore lo stesso**, perché falliva la maggioranza: 37 su
82.

A quel punto ho aggiunto un **secondo** emendamento — §1b, il denominatore per
font — e l'ho scritto **dopo** aver visto perché il primo non bastava.

> È la cosa che il §4 di ogni criterio di questo progetto vieta: aggiungere una
> condizione nello stesso giro, dopo aver guardato. L'ho fatto, e va detto prima
> dei numeri, perché i numeri che seguono vengono da una regola scritta a metà
> misura.

Il §1b non era arbitrario — il commento della v1 diceva già che il denominatore
deve contare «questo carattere **in quel font**», e l'implementazione contava il
carattere in un font qualunque. Ma «avevo ragione» non è «l'ho dichiarato prima».

## 2. Le barre

| barra | esito |
| --- | --- |
| **B** — FWK resta a 136 voci | **passa, esattamente 136** |
| **C** — nessun marcatore perso | **passa, 16 su 16** |
| **D** — FW e DB invariati | **passa** |
| **E** — le regressioni di sempre | **invariate** (`check_list_regression` cadeva già su HEAD, ed è la caduta dichiarata da `Decisione_Annidamento_v1.md`) |
| **A** — veto sui caratteri nuovi | **CADE** |

## 3. Che cosa guadagna, e va guardato perché è il motivo per cui fa male ritirarlo

Voci d'elenco prodotte, sedici manuali, nessuna persa da nessuna parte:

| manuale | v1 | v2 | | manuale | v1 | v2 |
| --- | ---: | ---: | --- | --- | ---: | ---: |
| **Vil** | **0** | **29** | | Fab | 18 | 35 |
| **Apo** | 6 | **11** | | Dag | 27 | 32 |
| FWK | 136 | 136 | | DrM | 0 | 0 |
| gli altri dieci | | invariati | | | | |

Le 34 voci nuove di Vil e Apo sono **tutte vere**, una per una:

```
hEsplorare il tuo retaggio, cercando di controllarlo per tentare imprese
hUtilizzo. Richiede tempo e non è possibile quando si agisce a turno.
hEffetto. Se inalato, elimina lentamente tutte le ferite e i segni.
hDipendenza. Tira 1d12, se il risultato è 1 l'Oscurità segna 1 punto…
hL'assedio alla Rocca dell'Alba Cinerea, urlato da Marcheval prima di
```

**E su DrM restano zero**, pur avendo ammesso otto caratteri nuovi: le firme di
scala li filtrano a valle, esattamente come `Criterio_MarcatoreDaFont_v1.md` §2
diceva che avrebbero fatto. Quell'argomento regge ancora.

## 4. Perché cade

**Fab, 17 voci false:**

```
Ode  Olivia  Oona  Orion  Orne  Osira  Owen     ← `O` decorativa di un elenco di nomi
W ×6                                            ← l'ornamento in fondo alla pagina
n ×4
```

**Dag, 5 voci false**: `23`, `41`, `423` — voci il cui testo intero è un numero.

E il falsificatore è preciso: **la premessa del §1 è falsa su Fab**. Avevo scritto
che un glifo da solo sulla sua riga è separato da ciò che segue «più di quanto lo
sia uno seguito da spazio», e che le maiuscolette di FWK non entrano perché sono
tutte attaccate — vero, misurato, 30 su 30. Ma su Fab il **capolettera** `O` sta
su una riga sua, a corpo **77,1** contro un corpo di 10,0. Lo stesso caso che il
vincolo dello spazio proteggeva su FWK, su Fab passa dalla porta che ho aperto.

## 5. L'osservazione che rende la v3 breve — e che **non** ho applicato

I glifi falsi sono **più grandi del corpo**; quelli veri no:

```
Vil  'h'  10,0  su corpo 11,6    ← non più grande, ed è un pallino
Apo  'h'  10,0  su corpo 11,6    ← non più grande, ed è un pallino
Fab  'W'  15,0  su corpo 10,0    ← più grande
Fab  'n'  30,0  su corpo 10,0    ← più grande
Fab  '3'  30,2  su corpo 10,0    ← più grande
Fab  'O'  77,1  su corpo 10,0    ← più grande
```

Un pallino è **al più grande quanto il testo che marca**: è la sua funzione. Un
capolettera e un ornamento sono più grandi, ed è la loro.

**Ma non chiude Dag.** Lì i glifi falsi stanno a 8,0 su un corpo di 9,0, cioè non
sono più grandi, e le voci `23` e `423` passerebbero lo stesso. La condizione che
servirebbe per Dag è un'altra — una voce il cui testo intero è un numero non è una
voce — ed è una terza cosa.

Le riporto tutte e due come **osservazioni misurate**, non come condizioni
aggiunte. Aggiungerne una terza dopo averne già aggiunta una a metà giro sarebbe
il giro di rifinitura che il `CLAUDE.md` dice di fermare.

## 6. Che cosa resta

L'emendamento è ritirato: `document_line_start_measurements.py` e `ir2_builder.py`
tornano com'erano, e la resa di Vil resta quella che l'utente ha visto:

```
Gli effetti positivi di un dono si attivano istantaneamente. h
```

**Il difetto è aperto, diagnosticato per intero, e la strada per chiuderlo è
misurata.** Serve un giro suo, con le due condizioni dichiarate prima.
