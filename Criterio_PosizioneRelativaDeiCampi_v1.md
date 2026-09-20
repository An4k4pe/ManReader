# Criterio — la posizione relativa dei campi

**20 settembre 2026.** Emenda il meccanismo misurato in
`Esito_SchedaControLaTabella_v1.md`, che riconosce una scheda dalle **righe di
campi**: righe che portano insieme una combinazione di etichette ripetuta almeno
tre volte nel documento.

## 1. Che cosa manca

L'indicazione dell'utente era, parola sua: «non basta che ci siano, devono
essere nella stessa posizione relativa». Il meccanismo consegnato controlla solo
il **contenimento** della combinazione (`field_line_indices` in
`stat_block_field_lines.py`): se le etichette ci sono, la riga e' una riga di
campi, ovunque stiano. La posizione relativa non e' mai stata guardata, benche'
`LineFacts.label_starts` la porti gia' — x0 di ogni etichetta e larghezza media
di un suo carattere.

La conseguenza misurata: su DB idx 123 (stampata 122) la combinazione appresa e'
`{tiraund6.1, 2, 3, 4, 5}` — i numeri delle opzioni di un D6 dentro le celle
della tabella dei tesori. Sette righe della tabella escono e le celle restano
vuote. L'utente: «la tabella citata non risponde ai requisiti per essere una
sheet, non ha le etichette in una posizione relativa rilevante».

## 2. La regola

Una combinazione e' ammessa come combinazione **di scheda** solo se le sue
occorrenze mettono le etichette **nello stesso posto**.

Il posto di un'etichetta e' il suo scostamento dal bordo sinistro della riga,
diviso per la larghezza media di un carattere dell'etichetta e arrotondato
all'intero: un numero adimensionale, che non cambia se il manuale e' composto a
un corpo diverso. Il **profilo** di un'occorrenza e' la sequenza di quei numeri
nell'ordine delle etichette.

Una combinazione e' ammessa quando **un solo profilo copre la maggioranza** delle
sue occorrenze. «La maggioranza» non e' una soglia nuova: e' la stessa forma che
`_bound_label_groups` usa gia' in `stat_block_regions.py` per legare due
etichette, «lo stesso conteggio nella maggioranza dei casi».

Il filtro sta sulla **combinazione**, non sulla singola riga. Una scheda con un
impaginato anomalo — le creature evocate di DB alle pagine 67-69, con `PF` piu' a
sinistra — resta una scheda: e' la struttura a dover essere posizionale, non ogni
sua istanza. Filtrare riga per riga perderebbe quelle tre.

## 3. Che cosa deve succedere perche' passi

Resa di DB, Apo e Dag con `--schede-campi`, confrontata con `output/resa/unione`
(lo stesso meccanismo senza il requisito posizionale) tramite
`output/resa/unione_confronto.py`.

**A. Il difetto sparisce.** La tabella di DB idx 123 (stampata 122) torna come in
`output/resa/riparo`: le sette righe rientrano, nessuna cella si svuota.

**B. Le cinque buone restano.** Restano invariate rispetto a `unione` le
modifiche su Dag idx 230 (tabella sparita) e su DB idx 87, 90, 97 e Dag idx 359
(tabelle ridotte).

**C. Nessuna tabella nuova o cresciuta** su nessuno dei tre manuali.

**D. Apo resta intatto.**

**E. La barra E-B** resta 9 su 10 con la sola Fab idx 126 diversa, e i test
restano verdi.

**Veto.** Se cade A, il requisito posizionale non e' quello che separa i due
casi e va ripensato. Se cade B, il requisito e' troppo stretto e mangia le
schede vere: in quel caso va guardato **quale** delle cinque cade e perche',
prima di ritirarlo.

## 4. Quello che questo criterio NON fa

Non tocca i ritorni a capo. Le righe di scheda che tornano nel flusso del testo
si saldano ancora fra loro — su Dag idx 230 l'intestazione della seconda
caratteristica della sirena finisce in coda al paragrafo della prima — ed e' un
difetto separato, da dichiarare e misurare a parte.

Non trasforma le schede in un producer. Le aree si calcolano ancora in
`main_ir2.py` e si passano a `build_page_ir2` da un canale laterale: nella lista
dei `page_analysis_*.py` un producer di schede non esiste. L'utente lo ha messo
in coda: «per ora facciamo funzionare sheet, poi lo integrerai».
