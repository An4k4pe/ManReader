# Criterio — l'arredo ricorrente esce dal corpo

Registrato prima dell'implementazione del consumer. Commit **senza codice**.
Una pagina, §17.

## 1. La regola, e da dove vengono i suoi due numeri

> Uno **slot** ricorrente esce dal corpo se sta nella **fascia bassa** della
> pagina ed è occupato su almeno il **25%** delle pagine del documento.

Lo slot è l'unità di `document_text_recurrence_measurements`, già committata:
posizione quantizzata, relativa alla pagina.

**I due numeri non sono miei.** Sono quelli di `extractor.filter_repeated_blocks`
— `header_footer_zone=0.08`, `repetition_threshold=0.25` — che risolve lo stesso
problema nella pipeline legacy, è in produzione da tempo ed è protetto da
`AGENTS.MD` §Baseline come non-regressione. Riusarli invece di sceglierne di
nuovi è l'unica cosa che impedisce a questa regola di essere un fit: quattro
formulazioni mie sono cadute prima di questa, tutte tarate su ciò che avevo
davanti.

**Una scelta invece è mia, e va dichiarata**: la fascia è **solo quella bassa**,
non entrambe. Misurato su sei manuali (50 pagine ciascuno): la fascia bassa
toglie **zero contenuto** su tutti e sei; quella alta tira dentro corpo su tre —
`ABILITÀ SPECIALI DELLA CERBERUS` su SV, `ASCIA A CATENA, RETE MUSCOLARE
SINTETICA` su Lan, `ARTEFICE` e prosa su Fab. Il prezzo è che i titoli correnti
in cima si perdono: Lan tiene `Attrezzatura per Piloti`. È il verso giusto in cui
sbagliare — `State.md` ratifica che falso positivo e falso negativo non sono
commensurabili, e qui il falso positivo perde contenuto.

## 2. Che cosa succede a ciò che esce

**Niente viene distrutto.** Il nodo continua a esistere — `ir2_validate` esige
che ogni primitiva sia coperta — e a cambiare è la **resa**: l'arredo non entra
nel corpo e compare in `review_ir2.md`, esattamente come le note d'asset che
Resolution non ha accettato. Stesso cancello, `is_rendered_in_body`.

## 3. Come si giudica

**Campione**: 12 pagine da 6 manuali, seed `20260828`, dichiarato qui prima
dell'estrazione. Escluse per costruzione tutte le pagine già spese, e **le 50
pagine per manuale su cui la regola è stata progettata** (§1), che vanno
aggiunte alle esclusioni dello script **prima** di estrarre.

**Due etichettatori, e la gerarchia è dichiarata.**

1. Un **agente** riceve, per ogni pagina, il render nudo e l'elenco di ciò che la
   regola toglie — **senza sapere quale meccanismo l'ha prodotto né quale esito
   sia atteso** — e per ogni voce dice `arredo` o `contenuto`.
2. **L'utente decide**, e guarda: tutte le voci su cui l'agente dice `contenuto`
   o dichiara incertezza, più un campione casuale di quelle che dice `arredo`.

L'agente serve a limitare il lavoro umano e a fornire un secondo parere, **non a
dare il verdetto**: un modello che valida il meccanismo che un modello ha scritto
non è una verifica. L'accordo fra i due si riporta come dato.

## 4. La regola di pass/fail

> **Regge** se **nessuna** voce tolta è giudicata `contenuto` dall'utente.
>
> **Cade** alla prima.

Barra a zero e non a una percentuale: la regola è progettata per la precisione, e
il §1 ha già pagato la copertura per averla. Una regola che perde contenuto non è
una regola conservativa mal tarata, è una regola sbagliata.

**Si riporta e non decide**: quante voci d'arredo restano nel corpo — la
copertura mancata, che il §1 dichiara di sacrificare e che va quantificata invece
che assunta.

## 5. L'errore squalificante

> **Cade comunque** se il testo non si conserva: il multiinsieme dei caratteri
> dei nodi `text.paragraph`, **corpo più review**, identico prima e dopo.

Il perimetro è unito perché la regola sposta fra i due. Limite dichiarato, ed è
lo stesso che la revisione indipendente ha sollevato sul criterio precedente:
l'unione coglie la **cancellazione**, non la **retrocessione** — un contenuto
spostato in review passa questo controllo. È il §4 a coglierlo, non questo, ed è
la ragione per cui il §4 ha barra zero.

## 6. Che cosa resta fuori

I **titoli correnti in cima**, per la scelta del §1. La **linguetta di capitolo
verticale**, che non è ricorrente per slot perché ruotata e lunga.
L'**anticipazione ai producer**: la misura esiste prima dell'analisi di pagina,
ma nessun producer la consulta — se togliere rumore ai producer paghi non è
misurato, e `AGENTS.MD` dichiara aperta la questione se un producer possa
filtrare su un criterio altrui. La **deduplica degli asset grafici**, che è
`deduplicator.py` e riguarda immagini.

## 7. Che cosa NON decide

Non classifica: non esiste un `kind` «intestazione». La regola dice «questo slot
ricorre in fondo alla pagina», e il consumer non lo rende nel corpo. Non apre il
detector di marginalia: non c'è nessun candidato e nessun ruolo semantico. Non
tocca `side_band`, congelato. Non decide l'uscita dallo shadow mode.
