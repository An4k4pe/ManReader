# Criterio — l'arredo ricorrente: due regole misurate, nessuna scelta

Sostituisce la v1, non eseguita. **Questo documento non sceglie la regola**: ne
porta due, entrambe misurate sugli stessi sei manuali, con i loro profili
d'errore, e mette la scelta dove non sia una quinta lettura dei dati da parte di
chi le ha scritte.

Cinque formulazioni sono già cadute in progettazione, tutte tarate su ciò che
avevo davanti. È la ragione per cui questa volta la scelta non è mia.

## 1. Che cosa è comune alle due

L'unità è lo **slot** di `document_text_recurrence_measurements` — posizione
quantizzata, relativa alla pagina — e la soglia di ricorrenza è **25% delle
pagine**, che è `repetition_threshold` di `extractor.filter_repeated_blocks`,
in produzione nel legacy e protetto come non-regressione. Non è un numero mio.

Ciò che esce **non viene distrutto**: il nodo resta — `ir2_validate` esige la
copertura — e cambia la resa, con l'arredo in `review_ir2.md` dallo stesso
cancello delle note d'asset non accettate.

## 2. Regola A — la fascia

> Uno slot esce se sta nell'**8% inferiore** della pagina ed è ricorrente.

Anche l'8% è del legacy (`header_footer_zone`). La fascia è **solo la bassa**, e
questa è una scelta mia: la fascia alta tira dentro corpo su tre manuali su sei
(`ABILITÀ SPECIALI DELLA CERBERUS` su SV, `ASCIA A CATENA` su Lan, `ARTEFICE` e
prosa su Fab).

**Misurato su sei manuali, 50 pagine ciascuno:**

| | |
| --- | --- |
| contenuto tolto | **zero, su tutti e sei** |
| voci d'arredo prese | SV 2, Wil 2, DIE 5, DB 3, Lan 7, Fab 3 |
| che cosa perde | i titoli correnti **in cima** (Lan: `Attrezzatura per Piloti`, `4`) e le **linguette verticali** (SV: `3 // Astronavi ed Equipaggio`) |

## 3. Regola B — l'elemento

> Uno slot esce se è ricorrente, **stretto** — larghezza mediana non superiore
> alla riga di sorgente mediana del documento — e **costante**, con deviazione
> relativa della larghezza fra pagine ≤ 0,15.

Nessuna fascia. Il referente della larghezza è desunto dal documento, non fissato.
Il segnale è che un numero di pagina è sempre della stessa misura perché è sempre
due o tre cifre, mentre una riga di corpo cambia larghezza a ogni pagina.

**Misurato sugli stessi sei manuali:**

| manuale | arredo preso | contenuto tolto |
| --- | --- | --- |
| SV | 3, **inclusa la linguetta verticale** | 0 |
| DIE | 5 | 0 |
| Lan | 9, **inclusi i titoli in cima** | 0 |
| Wil | 2 | 0 |
| DB | 2, ne perde 1 (`CAPITOLO 7 – BESTIARIO`, largo 1,31) | 0 |
| **Fab** | 9 | **2** |

**Il fallimento di Fab, con la causa.** Prende `Questo reame è una non-` (1,00 di
riga, varianza 0,07) e `Alcune Furie si addestrano` (1,00, 0,12): le sue colonne
sono strette e **giustificate**, quindi ogni riga piena ha esattamente la
larghezza della colonna e varianza quasi nulla — lo stesso profilo di un titolo
corrente.

**E stringere non ripara**: portare la larghezza sotto 0,5 esclude le due righe
di Fab ma perde le filigrane, che su DIE valgono 0,90 e su DB 1,00. Non esiste un
taglio unico su questi dati, ed è il motivo per cui questo documento non ne
propone uno.

## 4. La domanda che la revisione deve decidere

**Quale regola si esegue** — A, B, o una terza che nessuna delle due suggerisce —
e con quale argomento che non sia «separa meglio sulle sei che ho guardato».

Elementi per deciderla, e sono tutti a verbale sopra: A non sbaglia mai ma vede
meno; B vede di più e sbaglia su un manuale su sei; l'errore di B è **perdita di
contenuto**, che `State.md` ratifica come non commensurabile con la mancata
copertura.

Chi decide consideri anche che le sei pagine su cui entrambe sono state misurate
sono **spese**: qualunque numero qui è coerenza col campione di progettazione,
non accuratezza.

## 5. Come si giudica la regola scelta, qualunque sia

**Campione**: 12 pagine da 6 manuali, seed `20260828`, dichiarato prima
dell'estrazione. Escluse per costruzione tutte le pagine già spese **e le 50
pagine per manuale del §2-§3**, aggiunte allo script prima di estrarre.

**Due etichettatori, gerarchia dichiarata.** Un **agente** riceve il render nudo
e l'elenco di ciò che la regola toglie, **senza sapere quale meccanismo l'abbia
prodotto né quale esito sia atteso**, e per ogni voce dice `arredo` o
`contenuto`. **L'utente decide**, e guarda le voci contestate più un campione
casuale delle altre. L'agente limita il lavoro umano e dà un secondo parere, non
il verdetto: un modello che valida ciò che un modello ha scritto non è una
verifica. L'accordo fra i due si riporta.

> **Regge** se nessuna voce tolta è giudicata `contenuto` dall'utente.
> **Cade** alla prima.

Barra a zero perché l'errore è perdita di contenuto. Si riporta e non decide:
quante voci d'arredo restano nel corpo, cioè la copertura sacrificata.

## 6. L'errore squalificante

> **Cade comunque** se il multiinsieme dei caratteri dei nodi `text.paragraph`,
> **corpo più review**, non è identico prima e dopo.

Limite dichiarato: l'unione coglie la cancellazione, non la **retrocessione** —
un contenuto spostato in review passa questo controllo. È il §5 a coglierlo, ed è
la ragione della barra a zero.

## 7. Che cosa resta fuori

L'anticipazione ai producer: la misura esiste prima dell'analisi di pagina e
nessun producer la consulta; se togliere rumore ai producer paghi **non è
misurato**, e `AGENTS.MD` dichiara aperta la questione se un producer possa
filtrare su un criterio altrui. La deduplica degli asset grafici
(`deduplicator.py`). Qualunque classificazione: non esiste un `kind`
«intestazione», e la regola dice dove uno slot ricorre, non che cosa sia.
