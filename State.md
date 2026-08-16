# ManReader — Stato progetto

## Versione corrente

**v0.22** — **Modalità I: implementazione incrementale**.

La progettazione globale è conclusa. La direzione architetturale A-0.2 e il piano di migrazione sono approvati; ogni task resta piccolo, verificabile, con file ammessi espliciti e senza commit automatici.

## Stato operativo

Le Milestone 1–35 sono completate. Cinque producer Milestone 13+ sono wired nel job:
`table_candidate` (Milestone 21, commit `93ee631`), `page_covering_visual`
(Milestone 23, commit `3bda611`), `page_edge_visual` (Milestone 24),
`embedded_visual` (Milestone 27, wired in Milestone 28) ed `interior_visual_frame`
(Milestone 30, wired in Milestone 31).
`run_job_page_analysis` ha una cache opportunistica non tracciata dal manifest
(Milestone 22, commit `fce90e2`) e apre selettivamente il
backend pdfplumber solo per i producer che lo richiedono (Milestone 23).
Restano rinviate a milestone future non ancora aperte né numerate: persistenza tracciata del
`PageAnalysis` prodotto, resume/batch multi-pagina, estensione di `CapturePageState`
per un secondo artifact, un consumer document-level di ricorrenza per `content_digest`
(vedi appunto sotto).

**Priorità aggiornata dopo Milestone 36 Fase A**: il producer `column_band` (contratto deciso
in Milestone 33, mai costruito, quattro punti bloccanti aperti) non è più un rinvio laterale
ma la precondizione del primo output leggibile della pipeline nuova. Vedi Milestone 36.

Diagnostica pre-milestone per column_band, non ancora una milestone aperta. **Stato in una riga, perché il resto è lungo e la conclusione non deve stare in fondo: il meccanismo NON è pronto per diventare un producer wired** — campione cieco fallito sul tipo di errore squalificante (falso negativo su regione multicolonna), e la precondizione da chiudere per prima è la segmentazione verticale, non la taratura dei parametri. Storia in quattro fasi: la prima e la seconda hanno prodotto misure, la terza è stata fermata senza produrne, la quarta ha prodotto il meccanismo attuale. **Aggiornamento al 16 agosto 2026, perché due dei tre elementi di quella riga non sono più veri come scritti**: la segmentazione verticale è stata chiusa dalla segmentazione gerarchica (riga 92), e il campione cieco fallito è quello del 12 agosto, sostituito da quello del 13 con zero falsi negativi e potere statistico dichiarato debole (riga 102). Sulle pagine verificate a vista il reading order a bande ora è corretto (DrW p.97, Dag p.164, DB p.50, giudicati dall'utente). Questo **non** dice che il meccanismo sia pronto per essere wired: nessun campione cieco è stato ripetuto dopo le modifiche di questa sessione, e il criterio di uscita della milestone continua a mancare del terzo invariante sull'ordine (riga 76).

Fase 1 (Proposta_ColumnBandProducer_v9/v10.md, Chat A, due giri di revisione Chat B completati): meccanismo basato su raggruppamento (block_index, line_index) (da TextPrimitive.source_observation_id, pymupdf_capture.py:123-125) seguito da assemblaggio di righe visive (\_assemble_visual_rows) e banding stile Milestone 32. v10 §11.6 registra una ritrattazione empirica: la premessa che il raggruppamento riducesse la sovra-fusione di \_cluster_rows (13,6%-45,7% delle righe, vedi sotto) è stata misurata falsa su DB/Fab/Kul — conteggi di sovra-fusione identici, non solo simili, fra vecchio e nuovo metodo. Causa: il merge transitivo per sovrapposizione verticale è invariante al pre-raggruppamento in sottoinsiemi già mutuamente connessi.

Fase 2 (sessione successiva, non ancora una Proposta_ColumnBandProducer_v11.md formale): meccanismo alternativo che non fa clustering di righe. Aggrega direttamente sui gruppi (block_index, line_index) su una griglia y fine (default 2pt), generalizzando \_persistent_gaps_for_rows (Milestone 32) da "per riga" a "per fetta y". Gruppo "attivo" per una fetta y se il suo inviluppo [y0,y1] la copre (non overlap esatto di bbox come \_cluster_rows, verificato scan_column_structure_diagnostics.py:323-345 — differenza non stressata da nessun caso reale, rischio architetturale aperto). Diagnostica pura, quattro script (prototype_column_gap_group_persistence.py e tre di supporto), non un producer, non wired, nessun RegionCandidate emesso. Quattro giri di revisione metodologica Chat B completati (Nota_ColumnBandProducer_GroupPersistence_v1.md → v4.md, nessuno nel repo). Casi empirici, tutti verificati con render o navigazione diretta del PDF (non solo con l'etichetta --page N, vedi sotto): tabelle con celle che vanno a capo (DB, due pagine, flicker del vecchio metodo assorbito in un column_count stabile); prosa giustificata a 2 colonne (Dag — **fallimento misurato, vedi il paragrafo dedicato sotto**: ai default il meccanismo restituisce column_count=1 su una pagina verificata a render come 2 colonne); lista numerata a 2 colonne con voci di lunghezza libera (Fab, column_count=2 trovato correttamente — refuta un'ipotesi di fallimento strutturale sollevata e poi ritrattata nella stessa sessione, v. sotto); controllo negativo su contenuto genuinamente a colonna singola (Fab, column_count=1 corretto, non un fallimento). Nessun criterio di fallimento è stato fissato prima delle misure, e i casi sono stati scelti durante l'analisi, non a priori: l'elenco qui sopra non è un campione e non va citato come evidenza a favore del meccanismo. La frase "nessun caso di fallimento genuino osservato finora", presente in questa sezione fino al commit 4e82de1, era falsa ed è stata ritirata — vedi il paragrafo seguente.

Rischio procedurale scoperto in questa fase, non un dettaglio: --page N in tutti gli script diagnostici (vecchi e nuovi) è un indice posizionale nel PDF (page_index = N - 1), non il numero di pagina stampato nel piè di pagina. Lo scostamento fra i due non è costante né prevedibile: +2 in alcuni punti verificati su DB/Dag/Fab, +12 su DIE, non lineare dove una sezione ha numerazione romana propria (DB, appendice). Questo scostamento ha causato un'inversione di attribuzione (non solo un'etichetta sbagliata) in un caso concreto: un risultato di fallimento attribuito inizialmente a una lista a 2 colonne era in realtà su una pagina diversa e genuinamente a colonna singola, dove il fallimento non esisteva — corretto solo dopo tre giri di revisione, con verifica diretta pagina per pagina (v. Nota_ColumnBandProducer_GroupPersistence_v3.md/v4.md changelog). Non esiste un modo affidabile via script per controllare sistematicamente la corrispondenza; resta un controllo manuale, caso per caso, prima di ogni misura che verrà citata come conclusione.

Fallimento misurato su Dag, e sua causa: due difetti indipendenti, nessuno dei due è una taratura. Pagina identificata correttamente prima di citarla: indice posizionale 84, numero stampato 82 (scostamento +2), verificata a render (`scripts/render_pymupdf_block_overlay.py`) come prosa giustificata a 2 colonne nella metà alta, con un'illustrazione a piena larghezza sotto. Il gutter reale è 9,8pt, a x=297,0 stabile in 19 fette y su 21 (`scripts/dump_raw_group_gaps.py`). Ai default il meccanismo restituisce column_count=1: **è un fallimento genuino**, non un caso limite. Sweep dei due parametri sulla pagina intera: a --min-gap-width 15pt l'esito resta column_count=1 per ogni --min-support-ratio da 0,60 a 0,20; a 9pt diventa column_count=2 solo da 0,40 in giù. Restringendo l'analisi con --y-window alla sola fascia delle due colonne (y 124-330) le due cause si separano: a 15pt l'esito resta column_count=1 anche con la finestra corretta (**prima causa: la soglia hardcoded è sopra il gutter reale, quindi blocca a prescindere**), mentre a 9pt con il --min-support-ratio al suo default di 0,6 l'esito è column_count=2 con support_ratio 0,968 — contro 0,682 sulla pagina intera (**seconda causa: il supporto è calcolato su tutta l'altezza pagina, e le due colonne ne occupano circa un quarto**). Conseguenza: il support ratio non è mal tarato, sembra mal tarato perché diluito dall'assenza di segmentazione verticale. Corretta quella, il suo default regge.

Struttura di colonna variabile dentro la stessa pagina, punto sollevato dall'utente e confermato dal caso Dag: il cambio di numero di colonne a metà pagina non è un caso particolare, è frequente — un titolo o un paragrafo introduttivo a colonna singola seguito da corpo multicolonna, o viceversa un'illustrazione a piena larghezza che interrompe. La pagina Dag sopra ne ha cinque zone e tre strutture diverse. Il meccanismo di Fase 2 assume implicitamente **una struttura di colonna per pagina**: `--y-window` esiste ma è manuale e di default copre tutta la pagina, e non c'è alcuna segmentazione verticale automatica. Finché quell'assunzione resta, ogni pagina a struttura mista diluisce il supporto e produce un falso column_count=1 senza fallire rumorosamente — cioè il modo peggiore di sbagliare. La segmentazione verticale va risolta prima della taratura di qualunque soglia, non dopo: è la causa di cui il problema della soglia è in parte un sintomo.

Misura sul corpus dell'assunzione "una struttura di colonna per pagina", 16 manuali, 4.988 pagine (`scripts/scan_intra_page_band_structure.py`, `scripts/summarize_intra_page_band_structure.py`). Sulle pagine che contengono almeno una banda genuinamente multicolonna, la regione multicolonna copre in mediana il **41-43%** dell'estensione di testo della pagina, e copre il 90% o più solo nel **2,7-3,5%** dei casi — cioè l'assunzione implicita del meccanismo di Fase 2 vale su circa una pagina su trenta fra quelle che dovrebbe riconoscere. Il **73-77%** di quelle pagine sta sotto il `--min-support-ratio` di default (0,6): calcolando il supporto sull'intera altezza pagina, il default non è raggiungibile su tre pagine su quattro. Dag p.84 non è un caso sfortunato, è il caso tipico. **Il risultato non dipende dal parametro libero**: ripetuto con filtro banda a 2, 3, 5 e 8 righe, mediana 0,41-0,43 e coda ≥0,9 fra 2,7% e 3,5% — è questa insensibilità, non il valore in sé, che lo rende citabile. Tre riserve, tutte nella stessa direzione: il denominatore è l'estensione del testo e non l'altezza pagina (contro l'altezza vera la copertura sarebbe minore); le bande vengono dal percorso di Milestone 32, la cui sovra-fusione nasconde confini fra bande invece di inventarne; nessuna delle due può gonfiare il risultato, entrambe lo comprimono. Conseguenza operativa: **la segmentazione verticale non è un miglioramento del meccanismo, è una sua precondizione.**

Misura scartata, registrata per non essere rifatta: il tasso di pagine con bande a `column_count` diverso (85,7% senza filtro) non va citato — dipende quasi interamente da `--min-rows-per-band`, crolla a 38,4% a due righe e a 2,5% a dieci, e la curva non ha ginocchio. Inoltre non cattura il caso Dag, dove a interrompere le colonne è un'illustrazione a piena larghezza che non produce alcuna banda di testo. La misura di copertura sopra la sostituisce.

Principio che ne discende, posizione dell'utente messa agli atti: le soglie geometriche non vanno fissate come costanti ma desunte dal documento. Il caso Dag mostra il modo di fallire specifico di una costante hardcoded scelta troppo alta — non produce errori vistosi, rende invisibile un'intera classe di documenti. `dump_raw_group_gaps.py` fornisce già il dato da cui una soglia si ricaverebbe (i gap grezzi per fetta y, senza binning né soglia). Non ancora fatto, non ancora proposto come meccanismo.

Provenienza delle misure di questi paragrafi: raccolte in sessione l'11 agosto 2026 con gli script di 786b547, prima mano, output in `output/diagnostics_column_band/` (non nel repo, rigenerabile). Il fallimento Dag e le sue due cause sono misurati; il principio sulle soglie è una posizione, non una misura.

Fase 3 (fermata dall'utente, nessun dato prodotto): erano giri di testing reali, mai eseguiti. Il ciclo diagnosi → proposta di un nuovo giro di test → nuova diagnosi ha continuato a girare senza che nessuno di quei giri venisse eseguito su PDF reali; l'utente l'ha fermata e ha sostituito la sessione con un prompt di ripartenza (`Prompt_NuovaChatA_ripartenza.md`, non nel repo) che riparte dai due punti aperti lasciati da Nota_ColumnBandProducer_GroupPersistence_v4.md §5. **Nessun risultato di Fase 3 esiste e nessuno va citato**: la fase non ha prodotto misure, solo test proposti. I due punti aperti che restano da misurare — un caso costruito apposta per stressare la differenza inviluppo-`[y0,y1]` contro overlap esatto di bbox (per esempio una didascalia multi-riga che PyMuPDF indicizza come una sola riga), e la ricerca su DB dell'artefatto di sovra-segmentazione di \_cluster_rows già trovato su Fab — non sono risolvibili rileggendo i dati già raccolti.

Fase 4 (`scripts/prototype_derived_column_bands.py`, sessione dell'11 agosto 2026): meccanismo con confini ricavati dal documento, che sostituisce entrambe le costanti di Fase 2. Non un producer, non wired, nessun RegionCandidate. L'idea è rovesciare la domanda: invece di chiedere "questo gap è largo almeno 15pt e persiste su almeno il 60% della pagina", si chiede quale intervallo x resta scoperto scendendo lungo y, e **l'estensione verticale del gutter è essa stessa il confine della banda**. Cade il support ratio (non c'è più un denominatore di pagina) e cade la soglia di larghezza (spazio fra parole e gutter non si distinguono per larghezza — 8pt su Dag — ma per persistenza verticale). Tre criteri di ammissione, nessuno dei quali è una soglia geometrica in punti: `too_few_lines`, meno di 2 righe distinte per lato, e i fianchi di solo testo **ruotato** non contano (`TextPrimitive.direction`. **Correzione di un'affermazione falsa** che questa sezione conteneva fino al commit 3211e66 ("già catturato da pymupdf_capture.py e mai usato prima"): il campo è usato in produzione da Milestone 6 — `_has_compatible_orientation` in page_analysis_text_hypotheses.py:74-95, chiamata a :55 e importata da page_analysis_side_band.py:18, con suite di test dedicata. Rilievo di Chat B, verificato da Chat A. Peggio dell'errore in sé: le due definizioni **divergono**. Milestone 6 ammette solo dx≈±1 e dy≈0 (e tratta `direction is None` come ammissibile); Fase 4 chiama ruotato tutto ciò che ha abs(dy)>abs(dx). Sul testo obliquo a 30° la prima dice non ammissibile e la seconda dice non ruotato. Fase 4 ha quindi introdotto una **seconda definizione di orientamento del testo** nella stessa pipeline, dove la prima è già ratificata. Va unificata sulla definizione di Milestone 6); `too_few_wordy_lines`, meno di 2 righe per lato che portino almeno 5 caratteri — vincolo tipografico proposto dall'utente: non si va a capo dopo una lettera o un articolo. Sostituisce una versione a **mediana** dei caratteri che era il difetto vero: su una pagina a elenco puntato PyMuPDF indicizza ogni marcatore come una riga di un carattere, e i marcatori trascinavano la mediana a 1; `too_short`, gutter più basso di 3 righe **della pagina**, con l'interlinea mediana misurata come unità.

Verifica di Fase 4 su 11 pagine ispezionate visivamente dall'utente, 11 esiti corretti su 11. Tenute: Dag p.84 e p.140 e DrW p.97 (due colonne), Vil p.75 e DIE p.105 (strutture a due parti per voce). Scartate: Lan p.84 (tabella), Fab p.139 e DrW p.216 (linguette di capitolo), Wil p.308 (callout), Kul p.106 (riga marginale decorativa), Fab p.262 (colonna singola). Il caso Dag p.84, su cui Fase 2 falliva a ogni combinazione di parametri, dà una banda sola y 126-312 con gutter largo 8pt. **Che la tabella di Lan p.84 venga scartata non è un difetto ma il comportamento corretto**: l'obiettivo di `column_band` è il reading order, e una tabella si legge per righe — trattare la sua colonna di numeri come banda di colonna produrrebbe un ordine di lettura sbagliato.

**Limite dichiarato, che vale più dell'11 su 11: quelle 11 pagine sono il campione di sviluppo, non un campione cieco.** Le ho scelte io, prima dai disaccordi fra i due meccanismi poi dalle celle di una distribuzione congiunta, e il meccanismo è stato tarato guardandole. "11 su 11" misura la coerenza col campione su cui è stato costruito, non l'accuratezza. Un campione casuale da un pool non condizionato non è mai stato estratto. Inoltre i due valori numerici (oggi 4 caratteri e 3 righe) **non sono derivati**: sono vincoli tipografici plausibili che le ancore confermano, ma li abbiamo scelti noi.

Misure di Fase 4 sull'intero corpus, 16 manuali, 4.988 pagine (`output/final_bands/`, `output/final_gutters/`, non nel repo, rigenerabili). 19.939 gutter grezzi, di cui accettati 5.160 (25,9%); scartati per `too_few_lines` 7.363 (36,9%), per `too_few_chars` 4.509 (22,6%), per `too_short` 2.907 (14,6%). Ne risultano 5.642 bande su 2.331 pagine. **Due numeri ora SPIEGATI: sono artefatti della segmentazione, non proprietà del corpus** (v. sotto, e la misura di Chat B che porta le bande a 3+ colonne da 100 a 6-7 correggendo solo `_segment_bands`). Vanno rimisurati dopo la correzione, non citati come dati sul corpus: la distribuzione di `column_count` ha una coda lunga (2 colonne 3.312 bande, 3 colonne 1.107, ma anche 4→614, 5→223, 6→156, 7→107) e l'estensione mediana di banda è 72pt con un minimo di 2pt, cioè molto più corta dei gutter che le generano. La causa probabile è la segmentazione, che taglia a ogni y dove cambia l'insieme dei gutter attivi e produce quindi schegge sottili; su Dag p.84 il risultato era una banda sola, sul corpus sono 2,4 bande per pagina. Non indagato, non verificato a render.

Lo scarto di Fase 4 è etichettato e riusabile, non buttato: `--emit gutters` emette ogni gutter con `reject_reason` e i conteggi, e le tre classi scartate hanno firme distinte già misurate sul corpus — firma tabella (pochi caratteri da un lato, molti dall'altro) 1.415 gutter, firma linguetta di capitolo (esattamente un fianco ruotato) 3.429, firma callout (due o più fianchi ruotati) 119. È materiale per il rilevamento di tabelle e callout, non prodotto per questo ma disponibile.

Confronto Fase 2 contro Fase 4 sul corpus, e perché non ordina i due meccanismi: senza filtri, su 4.988 pagine, entrambi trovano ≥2 colonne su 3.611 pagine, solo Fase 4 su 971, solo Fase 2 su **zero**. Alzando un filtro di estensione minima "solo Fase 2" cresce fino a 2.172, ma quel filtro può applicarsi solo a Fase 4 — Fase 2 non ha una nozione di estensione di banda, riporta sempre l'intera altezza pagina — quindi la crescita è un artefatto di una misura asimmetrica e non è evidenza a favore di Fase 2. Su sei pagine di disaccordo ispezionate a vista, Fase 2 ha sbagliato 3 volte su 3 nel gruppo dove trovava colonne che Fase 4 non vedeva: erano due bande di capitolo (BoB p.376, SV p.138) e un'immagine affiancata al testo (DIE p.176), riportate con `support_ratio` 1,0 e 0,937 — cioè **il confound side_band di Milestone 32, mai escluso finora, che Fase 2 accetta con la massima confidenza e che il criterio del testo ruotato di Fase 4 esclude**. Nell'altro gruppo Fase 4 trovava separazioni verticali reali su tutte e tre (Dag p.140 due colonne vere, Lan p.84 tabella, Wil p.308 callout), tutte con gutter fra 7 e 9pt, cioè sotto la soglia di 15pt che le rendeva invisibili a Fase 2.

Patologia di cattura scoperta in Fase 4, non risolvibile a valle e non quantificata. Su Kul p.233 posizionale (stampata 232, scostamento +1; glossario a tre colonne verificato a vista) il livello `dict` di PyMuPDF — quello che `pymupdf_capture.py:145` legge — restituisce 245 span larghi in mediana 1,8pt con testo `'.'`, mentre `rawdict` sullo stesso oggetto contiene 3.332 caratteri veri con geometria sana. Il testo esiste ed è selezionabile nel documento: è il livello da cui lo leggiamo a essere degenere, non il PDF. Questo colpisce **qualunque** meccanismo costruito su `(block_index, line_index)`, quindi anche Fase 1 e Fase 2 e tutte le misure che ne discendono. Quante pagine del corpus siano in queste condizioni non è stato misurato, ed è la misura da fare per prima: senza quel numero non si sa cosa significhino i dati già raccolti. **Il progetto ha già incontrato questa degenerazione e l'ha risolta**, con un rimedio diverso da `rawdict` e mai citato finora: `_recover_missing_text_blocks_from_block_hints` (extractor.py:2128, chiamata a :4206, pipeline legacy) recupera il testo da `get_text("blocks")` quando la struttura `dict` non produce un TextBlock utile, con una guardia contro i falsi recuperi. Rilievo di Chat B, verificato da Chat A. Nota che `rawdict` non ha una nozione di span diversa da `dict`: risolve la perdita di testo, non è ovvio che risolva l'indicizzazione (block_index, line_index). La forma giusta della domanda non è "passare a rawdict" ma se la cattura debba avere un **rilevatore di degenerazione** che segnali la condizione invece di produrre silenziosamente primitive degeneri. È una milestone a sé, non dentro il perimetro di column_band: tocca pymupdf_capture.py, colpisce tutti i producer già wired, e AGENTS.MD vieta di mescolare riorganizzazione e cambio funzionale.

Verifica di Fase 4 su campione CIECO, ed è il risultato che conta più dell'11 su 11. 16 pagine estratte a caso con seed dichiarato 20260812, stratificate sui sei esiti possibili del meccanismo e poi mescolate, da un pool non condizionato di 4.988 pagine; l'utente le ha giudicate a vista senza sapere cosa avesse deciso il meccanismo. **Criterio di accettazione registrato per iscritto prima di guardare**: regge se sbaglia al più 2 su 16 e nessuno degli errori è una pagina a due colonne dichiarata a colonna singola. Esito: 14 corrette, 2 errori, e **il criterio NON è soddisfatto** — il conteggio rientra ma uno dei due errori è esattamente il tipo squalificante. Le 11 pagine del campione di sviluppo davano 11 su 11 e non potevano mostrare nessuno dei due difetti: è la differenza fra campione di sviluppo e campione cieco, misurata su questo progetto.

Le due cause, diagnosticate. **DIE p.127 posizionale (stampata 115), due colonne con elenchi puntati, nessuna banda emessa**: il gutter esiste ed è da manuale — x 311-321, largo 10pt, alto 668pt, fiancheggiato da 102 righe a sinistra e 70 a destra — ma viene scartato da `too_few_chars` perché la *mediana* dei caratteri a sinistra è 1. PyMuPDF indicizza ogni marcatore di elenco (`◆`, `●`) come una riga a sé di un carattere, e su 102 gruppi i marcatori bastano a trascinare la mediana. **Il difetto non è il valore 5 ma la statistica**: con soglia 2, cioè il valore che i dati sostengono secondo la revisione di Chat B, questa pagina sarebbe stata scartata lo stesso. Test della correzione (massimo invece di mediana): DIE p.127 passa da 1 a 60 e viene tenuta, tabella/marginale/colonna singola restano scartate, ma **si riapre il falso positivo di Fab p.139** (linguetta, da 3 a 8). Uno risolto, uno rotto; per chiuderlo servirebbe una guardia sulla firma già disponibile (`right_rotated=1`), non misurata. **DrM p.87, colonna singola con scheda mostro, 4 bande fino a 4 colonne**: le pseudo-colonne della scheda hanno testo vero da entrambi i lati, quindi nessuna statistica sui caratteri le tocca — mediana 8, massimo 21. Le schede mostro sono frequenti in questi manuali e non sono tabelle: probabilmente serve una categoria propria, oggi inesistente.

Fatto emerso dalla costruzione del pool, non dalle misure: lo strato dei gutter scartati per `too_short` contiene **una sola pagina in tutto il corpus**, benché quel criterio scarti il 14,6% dei gutter. Il vincolo delle 3 righe colpisce quasi solo gutter che stanno su pagine decise comunque da altro. Non è un difetto, ma ridimensiona quanto quel parametro stia davvero decidendo.

Revisione architetturale indipendente (Chat B, Giro 2, sul commit 3211e66; il Giro 1 metodologico l'aveva preceduta sul solo testo). Verdetto: **non pronto per diventare una milestone aperta con un producer wired**. Sei difetti misurati da Chat B con misure proprie, incluso il primo campione casuale non condizionato di questa diagnostica: la x del gutter è calcolata su tutta la vita della catena e non sulla sua estensione dichiarata, quindi testo che sta *sotto* la fine del gutter ne erode la x (32,6% dei gutter accettati) e — poiché `_flanking_profile` usa la x finale — **cambia anche l'ammissione**, accoppiamento mai dichiarato; il 46,4% delle bande sono artefatti di sfalsamento y della segmentazione, non cambi di struttura, il che risponde alla domanda aperta su `column_count` e sull'estensione mediana di 72pt (**la causa è la segmentazione, non il corpus**); gli spazi di giustificazione *sono* già accettati come gutter (3,6%, casi verificati su DB p.120 e Wil p.160), smentendo il "caso non ancora cercato" dichiarato nella docstring; avendo rimosso `--min-gap-width` senza sostituirlo, **`--bin-width-x` è diventato la soglia di larghezza de facto** (3,4% dei gutter accettati è largo 1pt); `too_few_chars` a 5 cade in una distribuzione piatta fra 3 e 11 caratteri, con un solo picco reale a 1 carattere — l'argomento tipografico giustifica ≤2, non 5; il gutter attraversa vuoti verticali senza limite (fino a 29 righe su Lan p.253). `too_short` e `too_few_lines` superano invece la critica: il primo è un moltiplicatore adimensionale di una quantità misurata, il secondo un minimo di conteggio.

**Decisione bloccante RITIRATA** (era: "dove va la decisione tabella ≠ colonna", classificata come mestiere di Resolution perché `too_few_chars` scartava la colonna dei numeri di una tabella su DB p.18). **L'esempio portante era falso.** Verificato al quinto giro di revisione: su DB p.24 il gutter scartato a x 74-76 non è una colonna di tabella ma un rientro sospeso con span di soli spazi bianchi (`left_chars_median = 0`), della stessa classe dei falsi positivi già noti su DB p.120 e Wil p.160 — mentre le **vere** colonne di numeri della stessa pagina (x 329-337 e x 455-463, `left_chars_median = 1`) sono entrambe **accettate** come bande. Il criterio non stava classificando tabelle: ne accettava due e scartava un artefatto di cattura. Ritirata su decisione dell'utente. Se la questione va riaperta, serve un caso in cui il criterio scarti davvero una tabella, e finora non ne esiste uno misurato.

Resta invece aperto e non ritirato il fatto architetturale che l'aveva motivata: `AGENTS.MD` §Layout e candidati registra come **questione aperta, non come invariante**, se un producer possa filtrare i propri candidati per anticipare una decisione del consumer — con `column_band` da un lato e `embedded_visual` (già wired, filtra con soglie duplicate da altri due producer) dall'altro. Quella formulazione non dipendeva dall'esempio ritirato.

Criterio di uscita per `column_band`, finora inesistente e costruibile su Milestone 36 — che Chat A non aveva citato. `scripts/prototype_vertical_slice_page.py` è il consumer reale e contiene già invarianti eseguibili più la baseline da battere (l'ordinamento geometrico puro, misurato illeggibile su DB p.99). Buco da colmare: l'invariante di conservazione del contenuto è un multiset, quindi **cieco all'ordine** — un `column_band` perfetto e uno pessimo lo passano identici. Serve un terzo invariante che confronti l'ordine emesso con un riferimento umano su poche pagine trascritte a mano, scelte prima della misura.

Nota di metodo, registrata perché è un errore di processo ripetuto e non un dettaglio: le ultime iterazioni di Fase 4 (testo ruotato, criterio dei caratteri, mediana contro massimo) sono state proposte una dopo l'altra **senza che esistesse un criterio di accettazione**. Senza quello ogni misura genera la successiva e nulla dice di fermarsi — la stessa forma dell'avvitamento che aveva fatto fermare la Fase 3. Su un producer di *candidati*, per giunta, inseguire l'esattezza è un errore di categoria: un `RegionCandidate` è per contratto una proposta non approvata, e una quota di errori è dentro il budget del livello. La prossima azione che aggiunge informazione non è un'altra misura sul corpus ma collegare il prototipo alla fetta verticale e leggere un `page.md` su una pagina che sbaglia e una che indovina.

Test del reading order con e senza `column_band` (`scripts/compare_reading_order_with_column_bands.py`), cioè il consumer che Milestone 36 indica e che nessuna misura sui CSV può sostituire. Cambia **solo** l'ordinamento delle TextPrimitive: la baseline è `(y0, x0)` copiata invariata da `prototype_vertical_slice_page.py:219-220`, il ramo a bande divide le primitive in colonne dentro ogni banda ed emette una colonna per intero prima della successiva. Cattura, normalizzazione e regola di paragrafo identiche; conservazione del contenuto verificata a ogni esecuzione. Unico adattamento dichiarato: il cambio di colonna forza un paragrafo, senza il quale l'ultima riga di una colonna si fonderebbe con la prima della successiva e il confronto sarebbe truccato a sfavore del ramo a bande. Esito, giudicato a vista dall'utente: su Dag p.140 l'ordine è corretto; su DIE p.127 la baseline è illeggibile (colonne alternate riga per riga) e il ramo a bande è identico perché il meccanismo non emette nulla; disattivando il solo criterio dei caratteri, DIE p.127 produce una banda che copre 194 primitive su 195 e l'incolonnamento diventa corretto salvo la prima riga.

Ne segue un'asimmetria che il contratto rende non negoziabile e che finora non era stata scritta: **falso positivo e falso negativo non sono commensurabili.** Un falso positivo è recuperabile — il producer emette una banda che non esiste e Resolution la rifiuta, che è ciò per cui Resolution esiste. Un falso negativo su una regione multicolonna **non è recuperabile da nessun livello**: Resolution può accettare, rifiutare o lasciare irrisolto un candidato, non può emetterne uno mai prodotto, e il consumer produce testo illeggibile. Il criterio di accettazione di `column_band` quindi non va inventato, si deduce: i due tipi di errore vanno contati separatamente e solo il secondo è squalificante. È il motivo per cui il criterio pre-registrato del campione cieco distingueva quel tipo di errore, allora per intuizione.

Due difetti piccoli e localizzati emersi dal test, entrambi con correzione ovvia e nessuno dei due misurato: la banda si estende quanto il **gutter** invece che quanto il contenuto che lo fiancheggia, quindi la prima riga di DIE p.127 resta fuori (va estesa alla prima e all'ultima riga fiancheggiante); e il criterio dei caratteri deve usare il **massimo** invece della mediana, che su DIE p.127 recupera il caso ma riapre il falso positivo di Fab p.139 e richiede quindi una guardia sulla firma `right_rotated=1`.

Limite strutturale di `column_band`, non correggibile dentro `column_band`, misurato su DrW p.97. L'immagine occupa x 57-299 e y 45-386, cioè tutta la parte alta della colonna sinistra; il testo di sinistra va da y 394 a 761, quello di destra da y 46 a 652. La banda trovata (396-652) copre esattamente la fascia dove entrambe le colonne hanno testo, ed è corretta — **un gutter richiede testo da entrambe le parti, e per 340pt una delle due colonne è un'immagine**. Ma il reading order che ne esce è sbagliato lo stesso: il consumer emette prima la colonna destra alta (y minore), poi la banda, poi la colonna sinistra bassa, mentre l'ordine giusto è tutta la sinistra e poi tutta la destra. L'informazione mancante **esiste già in un altro producer** — `embedded_visual` e `interior_visual_frame`, entrambi già wired nella fetta verticale — e nessuno la usa per ordinare. **SUPERATO, e questo paragrafo descrive un meccanismo che non esiste più**: dopo l'allungamento dei gutter fin dove il corridoio è visibile, la banda di DrW p.97 non è `396-652` ma `y 0-784`, e la pagina esce con l'ordine corretto (tutta la sinistra, poi tutta la destra) senza che nessuno legga i producer visuali. Misurato nella sessione del 15-16 agosto 2026, dove era stato pre-registrato come predizione che il difetto persistesse.

Il caso DrW p.97 è quello che ha fatto emergere l'invariante ora scritto in `AGENTS.MD` §Layout e candidati (l'isolamento fra producer è voluto; la relazione fra candidati di producer diversi si decide in Resolution o nel consumer). Formulato dall'utente in questa sessione a partire da qui, e verificato: il repo lo praticava già in Milestone 24, 30 e 33 senza averlo mai enunciato. Conseguenza operativa che riguarda direttamente il lavoro fatto qui: **il confronto di reading order di questa sezione è incompleto**, perché collega `column_band` all'ordinamento ignorando gli altri quattro producer già wired nella fetta verticale. Il test corretto li usa tutti, ed è la prossima azione.

Due casi di prova sul reading order, giudicati a vista dall'utente, che separano ciò che funziona da ciò che resta rotto. **Dag p.164 posizionale (stampata 162): corretto.** Il meccanismo emette due bande, y 60-240 e y 508-654, e lascia fuori la fascia intermedia — che è genuinamente a colonna singola a piena larghezza. È il caso a struttura mista trattato bene. (Chat A aveva inizialmente riportato le 22 primitive fuori banda come un difetto, guardando il conteggio invece della pagina: era comportamento corretto.) **DB p.18 posizionale (stampata 16): rotto, e con una causa precisa.** Le bande escono y 488-610 a 3 colonne, 610-650 a 2, 650-668 a 3, 668-712 a 2 — colonne che alternano su fasce di 18-40pt. Il confine a y 610 cade nei 10pt fra la fine del paragrafo di prosa della colonna sinistra (y 607,5) e l'inizio del suo elenco puntato (y 618), e ci cade perché alla stessa altezza, **a destra**, finisce il gutter interno della tabella `D6 ATTREZZATURA`. La banda passa da 3 colonne a 2 e nel farlo taglia in due il flusso della colonna sinistra, che non è cambiata affatto. È il difetto di segmentazione (E1 del referto architetturale, 46,4% delle bande) nella sua forma peggiore: **un cambio di struttura su un lato affetta il contenuto dell'altro**. Su DB p.18 due delle quattro bande hanno un gutter solo, quindi l'estensione del consumer si applica — semplicemente non aiuta. (Una versione precedente di questa frase diceva che non poteva intervenire: sopravvalutazione, corretta.)

Segmentazione gerarchica (`_segment_tree` in `scripts/prototype_derived_column_bands.py`, `--emit tree`), che sostituisce le fasce y globali. Il difetto che chiude: una banda aveva estensione x implicitamente pari alla pagina, quindi un gutter interno a una tabella nella colonna destra tagliava il flusso della colonna sinistra (DB p.18, confine a y 610 fra la fine del paragrafo a 607,5 e l'inizio dell'elenco a 618). Ora i gutter massimali definiscono le bande di primo livello e ogni colonna riceve ricorsivamente i gutter contenuti in essa, con estensione x esplicita. Il test di subordinazione è una disgiunzione x più un confronto di estensione: nessuna soglia. **Criterio di successo fissato prima di scrivere il codice e superato**: ogni gutter accettato compare esattamente una volta nell'albero — 1.636 gutter su cinque manuali, zero pagine divergenti. Serviva perché le due correzioni ovvie (fondere le bande annidate, tenere i soli gutter massimali) riparano DB p.18 ma **scartano** il gutter subordinato, e su una pagina a 3 colonne sopra e 2 sotto perderebbero struttura vera in silenzio; la conservazione distingue la correzione dal trucco. Due difetti trovati e chiusi durante l'implementazione, entrambi su casi reali: i subordinati che nessuna banda può ospitare vanno ritrattati come massimali nella propria regione (la subordinazione è globale sulla pagina ma vale solo dove il padre esiste — DB p.83, tre tabelle impilate, il gutter più alto veniva eletto padre di tutte e le altre due restavano orfane), e un gutter va marcato quando entra in una colonna perché un subordinato con due padri possibili veniva emesso due volte.

Estensione delle bande, e la regola che l'ha sostituita. Il gutter avanza la propria `y1` solo dove entrambi i lati sono attivi insieme, quindi la banda si ferma dove le ultime righe delle due colonne smettono di sovrapporsi in y — su Dag p.164 lasciava fuori il testo sotto y 654, che appartiene alle colonne. La regola corretta, proposta dall'utente, è **proseguire finché il corridoio non viene attraversato**: la condizione di arresto è l'interruzione, non l'assenza di testo. Una formulazione intermedia di Chat A ("estendere fino a dove arriva il testo che fiancheggia il corridoio") è stata scartata perché usa l'assenza di prova come prova di assenza — se nessuno attraversa il corridoio la separazione continua a esistere anche dove i due lati tacciono. L'estensione è tenuta in campi separati (`span_y0`/`span_y1`) da quelli probatori (`y0`/`y1`), che restano la grandezza usata dai criteri di ammissione: allungare quelli gonfierebbe i conteggi di fianco e falserebbe `too_short`. Estendere era pericoloso finché le bande erano piatte perché il consumer assegnava ogni primitiva alla **prima** banda che la conteneva e una banda estesa svuotava le altre (misurato su 7 pagine dalla revisione architetturale); con l'albero l'assegnazione andava alla banda **più profonda** e il pericolo sembrava chiuso. **Non lo è più**: la regola è stata poi rovesciata in "vince l'esterna", e sotto quella regola una banda estesa svuota tutte le altre — cioè esattamente il pericolo descritto, in forma più forte. La giustificazione di sicurezza dell'estensione è quindi **decaduta** e va rifatta. Rilievo del sesto giro di revisione. **La premessa è però caduta a sua volta**: "vince l'esterna" è stato ritirato e "vince la più profonda" ripristinato (commit `7f839bc`, v. riga 106), quindi la giustificazione non è decaduta e non c'è niente da rifare. Questa frase resta a verbale solo perché il rilievo del sesto giro era corretto rispetto allo stato di allora.

Fondo pagina contro immagine di contenuto: l'informazione esiste già come candidato e non va ricavata. Il corridoio è attraversato anche da un'illustrazione a piena larghezza, ma la griglia è costruita sul solo testo, quindi su DB p.18 la banda si estende attraverso l'illustrazione (x 80-483, y -1..558). Contare qualunque visuale come interruzione non funziona: il fondo pagina (x -8..613, y -8..799) bloccherebbe tutto — è la stessa trappola di `--widen-bands`, dove i fondi rendevano tutto "occupato", vista dal lato opposto. **La distinzione però non va definita, va letta**: su DB p.18 `page_covering_visual` emette esattamente un candidato (x 0-612, y 0-791, il fondo) e `embedded_visual` ne emette 17, il primo dei quali è l'illustrazione (x 80-483, y 0-558). Entrambi i producer sono già wired, con soglie ratificate in Milestone 27 e 28. La regola che ne discende non ha parametri: **il corridoio è interrotto da testo che lo attraversa o da un `embedded_visual` che lo attraversa; un `page_covering_visual` non lo interrompe mai.** **RITIRATA, non implementata.** Il difetto era stato *dedotto* dal meccanismo ("il corridoio è attraversato ma la griglia conosce solo il testo") e non osservato: in tutta la sessione non è mai emersa una pagina che si legge male a causa di un'immagine. Dove la fascia dell'illustrazione è priva di testo, che la banda la attraversi o si fermi produce lo stesso identico markdown — sposta un confine che nessun consumer legge. E dove il testo c'è, interrompere è probabilmente il danno: misurati 167 casi su tre manuali di bande di primo livello che attraversano un'immagine larga con testo sopra **e** sotto, e — così affermava il commit — nella grande maggioranza sopra e sotto ci sono le stesse due colonne con lo stesso gutter — una struttura sola con una figura in mezzo. Interromperla la spezzerebbe, rimandando fuori banda il testo sottostante: si introdurrebbe un falso negativo, l'errore non recuperabile, per risolvere un problema mai osservato. Resta un caso teorico in cui servirebbe — colonne **diverse** sopra e sotto la stessa immagine — mai cercato: è quello da cercare, se si riapre, non l'immagine in generale. **Quella giustificazione quantitativa non regge**, verificata da una ricostruzione indipendente al sesto giro. Il numero 167 **non è riproducibile**: nel repo non esiste lo script che l'ha prodotto, il commit non dichiara né i tre manuali né la definizione di "immagine larga", e la ricostruzione dà 39 casi con una definizione (larghezza ≥60% della banda, altezza ≥3 righe) e 159 con un'altra (≥30%). Soprattutto **il numeratore non era mai stato dato**: "nella grande maggioranza" vale come due terzi o tre quarti — 29 casi su 39 (74,4%) con la prima definizione, 106 su 159 (66,7%) con la seconda — **non come quasi-totalità**. E il "caso teorico mai cercato" — colonne **diverse** sopra e sotto la stessa immagine — **esiste e vale circa un quarto dei casi**: DB p.90 (due colonne sopra, una sotto), DB p.22, DB p.125 (strutture proprio diverse ai due lati), Fab p.353. Quattro dei dieci casi divergenti sono però fondini con il testo sopra, non figure inserite nel flusso, e vanno scartati. **Conseguenza**: il ritiro regge sull'argomento qualitativo — dove la fascia dell'immagine non contiene testo, interrompere o attraversare produce lo stesso markdown, e una regola che nessun output distingue non va implementata — ma **non** sull'argomento quantitativo, che copriva proprio i casi con testo ai due lati. Su quel sottoinsieme resta un difetto misurato attorno al 25%, per il quale "l'immagine interrompe" non è la correzione giusta (sarebbe sbagliata sui tre quarti restanti): serve qualcosa che rilevi il **cambio di struttura**, e non è stato cercato. L'analisi resta a verbale perché i tre producer visuali sono disponibili e le loro uscite su DB p.18 sono misurate. È il caso che rende concreto l'invariante di `AGENTS.MD` §Layout e candidati in una direzione non ancora scritta: un consumer che prova a ricavare dai pixel un'informazione già disponibile come candidato reinventa peggio ciò che esiste, e viola la separazione tanto quanto un producer che filtra i propri candidati.

Rilievi del quinto giro di revisione, verificati da Chat A e corretti. **`too_few_lines` non scarta mai in esclusiva**: le righe "wordy" sono un sottoinsieme di quelle contate e usano lo stesso N, quindi il criterio è logicamente dominato — 0 scarti esclusivi su 19.939 gutter contro 1.814 di `too_few_wordy_lines` e 3.012 di `too_short`. Resta come etichetta ma non decide nulla, ed è `too_short` a imporre davvero "una colonna ha più di una riga": l'estensione mediana di un gutter è 1,01 righe di pagina a una riga fiancheggiante, 2,03 a due, quindi i due criteri misurano la stessa cosa in unità diverse. **Il minimo di larghezza ai bordi aveva margine zero**: 18 colonne vere stanno fra 15,0 e 16,0 caratteri, e il modo basso viene quasi tutto da un solo manuale (159 casi su 162 dalla linguetta di Fab). Portato da 15 a 10 — le ancore restano identiche, il corpus perde 3 casi su 11.846 — perché l'errore che produceva era un falso negativo, quello non recuperabile. **Il confronto di reading order era truccato**: la correzione dell'ordinamento per riga visiva era stata applicata al solo ramo a bande e non alla baseline, con 17-85% di primitive spostate a seconda della pagina; su DIE p.127 l'85% del guadagno apparente veniva da quella correzione e non dalle bande. Aggiunta una terza uscita `order_baseline_lines.md`, baseline con la sola correzione di riga e nessuna banda, che è il termine di paragone equo.

Stato del consumer ad albero (`--use-tree` in `scripts/compare_reading_order_with_column_bands.py`) sulle pagine di prova, con i numeri veri e non solo quelli buoni: Dag p.164 63 primitive su 76 dentro una banda, DB p.18 67 su 71, **DrW p.97 107 su 171 — peggiorato** rispetto al widening piatto (171 su 171), che però era misurato rotto per altre ragioni; DIE p.127 era a 0 su 195 per il difetto della mediana, **ora risolto**: 194 su 195. Nessuna di queste pagine è stata riverificata a vista dopo l'ultima modifica.

Campione cieco del 13 agosto 2026, messo agli atti perché finora esisteva solo negli artefatti rigenerabili. 16 pagine estratte **uniformemente** da 5.201 (seed 20260813, nessuna stratificazione): Dag 48, DrW 40, SV 136, Kul 141, BiD 297, DIE 45, Dag 171, BoB 417, Vil 223, Fab 318, SV 233, Dag 62, Wil 295, Wil 288, DrW 314, DB 24. Criterio registrato prima: regge se nessun falso negativo su regione multicolonna reale; i falsi positivi si contano ma non fanno fallire. Esito giudicato a vista dall'utente: **zero falsi negativi**. **Tre limiti dichiarati.** È stato giudicato con i parametri di allora (M=5, larghezza di bordo 15) e da allora il meccanismo è cambiato quattro volte: **una pagina su sedici cambia esito**, Vil p.223. Il potere statistico è debole — 16 pagine con zero errori limitano il tasso di falso negativo solo sotto il 17%, e le pagine che contengono davvero una regione multicolonna sono 8, quindi il limite reale è circa il 31%: "zero falsi negativi" è compatibile con un meccanismo che ne sbaglia uno su quattro. E il campione precedente (seed 20260812, stratificato) era **fallito** sul tipo di errore squalificante: questo lo sostituisce, non lo smentisce.

Il parametro `--min-flanking-chars` è passato da 5 a 3 a 4 in due giorni, ed è la storia più istruttiva del giro. La revisione propose 2 misurando sulle proprie sei ancore; 2 rompe Lan p.84, tabella 1d20, perché i numeri a due cifre contano come righe con parole e la colonna dei numeri diventa una banda. Chat A portò a 3 dichiarando che "3, 4 e 5 danno risultati identici su tutte e sedici": **vero sulle ancore di sviluppo, falso sulle sedici del campione cieco** — M=3 rompe Vil p.223 nello stesso identico modo, e con esso circa dodici pagine del bestiario Vil che ripetono la stessa tabella di dadi (misurato dal sesto giro: 56 gutter recuperati fra M=5 e M=3 su quattro manuali, il 75% con il lato povero largo meno di un quarto dell'altro). Portato a 4, e **poi riportato a 5 dopo aver ispezionato a vista le undici pagine che 4 aggiunge rispetto a 5** — l'unica verifica che nessuno aveva fatto. Nessuna delle tre giudicate dall'utente è un recupero utile: Vil p.149 è una timeline con i numeri a sinistra e non due colonne; **Dag p.117 prende una colonna di una tabella e non le sorelle**; Fab p.188 separa colonne di elenchi. **Conclusione, che non è una taratura: il criterio non discrimina la classe giusta.** Una soglia che accetta una colonna di tabella e ne rifiuta le sorelle non sta misurando la proprietà che crede, e i casi che 4 aggiunge stanno dallo stesso lato di quelli che tiene pur essendo cose opposte; cercare il valore migliore fra 4 e 5 significherebbe tarare su casi che si comportano in modo contrario. Tornato a 5, il valore più conservativo fra quelli che non rompono nulla di noto. La distinzione numeri-di-tabella contro colonne-di-prosa **non è ottenibile contando caratteri** e resta a chi ha gli strumenti per farla. Tre volte di fila la soglia è stata scelta su un campione troppo piccolo e corretta dal successivo; la quarta volta è stata chiusa guardando le pagine invece di misurarle.

Regola dell'assegnazione: **vince la banda più PROFONDA**, ripristinata dopo essere stata rovesciata in "vince l'esterna" e poi corretta dall'utente. I due argomenti con cui Chat A l'aveva rovesciata erano entrambi sbagliati. Il primo — che la banda esterna desse lettura per righe sulle tabelle — è falso (dà lettura per colonne al gutter più esterno), ma la correzione vera è che **la domanda era mal posta**: `column_band` non deve leggere le tabelle, deve dire dove sono i confini di colonna, e se una regione è una tabella la gestisce il consumer di tabelle **aiutato da questi gutter**. Giudicare il meccanismo su quanto legge male una tabella significava giudicarlo su un compito che non ha; i sette gutter annidati di DB p.76 non sono una patologia ma **la descrizione corretta di una tabella a nove colonne**. Il secondo — che una banda estesa "rubi" le primitive alle figlie — era una formulazione confusa: la regola non sottrae nulla, sceglie soltanto quale struttura di colonne ordina una primitiva. Il pericolo dello svuotamento veniva dalle bande **piatte** con "vince la prima", dove non esisteva gerarchia; con l'albero non si presenta. Era la paura di un problema trasportata dove era già risolto. Nella formulazione dell'utente: le bande più profonde definiscono quali sono le colonne maggiori, e se dentro ne compaiono altre sono tabelle o gutter subordinati — materiale per chi di dovere, non un ordine da imporre qui.

Il difetto del 25% sulle bande che attraversano un'immagine **è chiuso: non esiste**, e le due misure che lo sostenevano erano entrambe invalide. La prima marcava "divergente" ogni caso in cui il gutter è dimostrato da un solo lato dell'immagine — cioè proprio la situazione in cui l'estensione fa il suo lavoro (DB p.90, scheda mostro verificata a vista: l'ordine prodotto coincide con quello indicato a mano dall'utente). La seconda, costruita per correggere la prima cercando strutture con gutter **propri e a x diverse** ai due lati, ha prodotto 14 casi su tre manuali di cui quattro ispezionati a vista dall'utente: **in nessuno c'è un'immagine che attraversa un gutter**. Due difetti nella misura: confrontava la coordinata iniziale invece della sovrapposizione (DB p.29 e p.48 sono lo stesso gutter misurato un po' diverso), e soprattutto ricalcolava i gutter applicando `_reject_reason` ma **non** il minimo di larghezza ai bordi, che vive in `_segment_tree` — quindi i "gutter sopra l'immagine" di Fab p.75 e p.123 erano le linguette di capitolo, che la pipeline vera scarta correttamente come `edge_strip` (x 365-378 e 367-378, verificato). Su queste pagine il meccanismo si comporta bene; era la misura a scavalcare il criterio che le esclude. La ricostruzione classificava come "divergente" ogni caso in cui il gutter è dimostrato da un solo lato dell'immagine. Su DB p.90 — scheda mostro, verificata a vista dall'utente — sotto l'immagine la colonna destra non ha testo, quindi il gutter lì non è dimostrato e il caso viene marcato divergente; ma la lettura corretta resta due colonne, la sinistra prosegue da sola, e l'ordine prodotto **coincide con quello indicato dall'utente**. La misura contava come difetti proprio i casi in cui l'estensione fa il suo lavoro. Resta la formulazione che l'utente ha dato dell'estensione, ed è il modello e non l'espediente: **prolungare le bande attraverso gli spazi vuoti consecutivi è ciò che fa chi legge una colonna** — non ci si ferma dove l'altra colonna tace.

Non risolto da nessuna delle quattro fasi: overlap banda/table_candidate (punto bloccante 2 di Milestone 33, ora con tre casi concreti: sommari, liste numerate con icona, e la possibile sovrapposizione fra lista a 2 colonne e table_candidate mai misurata su questo meccanismo); il confound side_band (mai escluso dalla diagnostica di colonna, noto da Milestone 32); due casi isolati con coordinate anomale su Fab.pdf p.2; se i punti di riferimento del vecchio metodo usati per giudicare la Fase 2 (es. DB p.76/p.113) contengano artefatti di sovra-segmentazione analoghi a quello trovato su Fab (una riga di lista classificata per errore come titolo da \_cluster_rows) — non cercato specificamente su DB.

Cosa NON rifare, chiuso con misura o con ispezione e da non riaprire senza un fatto nuovo. **Non tarare `--min-flanking-chars`**: ha fatto il giro 5 → 2 → 3 → 4 → 5 con tre correzioni, e la conclusione non è un valore ma una proprietà del criterio — non discrimina la classe giusta, accetta una colonna di tabella e ne rifiuta le sorelle (Dag p.117, ispezionata). **Non far decidere a `column_band` se una regione è una tabella**: non è il suo compito, deve dire dove sono i confini di colonna, e i gutter che trova sono materiale per il consumer di tabelle. **Non implementare la regola "l'immagine interrompe il corridoio" nella forma geometrica**: non «copre l'intervallo x del gutter», che è stata implementata e misurata nella sessione del 15-16 agosto 2026 e annienta le bande (73,6% toccate, DB p.50 da 83 primitive in banda a 0). La causa è nota e non è che le immagini non debbano interrompere: sul testo stampato **sopra** un'illustrazione l'attraversamento geometrico non dice nulla sulla lettura. Il discriminante misurato è il testo che vive dentro il bbox — chiusure di riquadro 0, fondi 21-63 su DB p.50. **Non riassemblare geometricamente le righe di testo**: vengono dalla sorgente, `(block_index, line_index)`, ed è la seconda volta che l'utente lo corregge. **Non aprire una quinta fase diagnostica**: le fasi 3 e 4 si sono avvitate esattamente così, e l'azione che aggiunge informazione è leggere un `page.md`, non produrre un altro CSV.

L'interruzione da filetto legge ora la classificazione invece di ridedurla, su decisione dell'utente contro un'obiezione di Chat A che era mal posta. Chat A aveva presentato la cosa come «ripara un difetto solo»: **falso**, e la confusione era fra casi *verificati a vista* (uno) e frequenza *misurata* (47 bande su 277). L'argomento dell'utente: non è detto che valga solo lì, rende `column_band` più completo e più vicino a come legge una persona, e costa soltanto andare a leggere che in quella posizione un altro modulo ha già segnalato qualcosa. `_corridor_blockers` chiama `dump_drawing_cluster_diagnostics` e prende `bbox or degenerate_bbox` dei cluster più bassi della riga di testo più bassa, invece di filtrare le `DrawingPrimitive` grezze. **Effetto misurato, migliore del previsto**: le bande toccate scendono da 47 a 42 (15,2%) e il taglio massimo da 25,2pt a **1,3pt**, perché il clustering di Milestone 26 fonde già i filetti vicini e una pila di righine diventa un cluster più alto della riga, che smette di essere blocker. Su Dag p.24 le bande passano da 11→50 a **11→11**: lo sminuzzamento che Chat A aveva riportato come danno sparisce. Restano invariati Dag p.164 (riparata), DB p.29 (2→12, righe di tabella) e DrW p.97 (zero blocker, uscita identica). **Il difetto su Dag p.24 non esisteva**: il paragrafo introduttivo spezzato da contenuto dell'altra colonna, riportato due volte da Chat A come costo della regola, era un bug della rilegatura dei figli in `_split_bands_at_crossings` — cercava il pezzo di padre contenente il **punto medio** della figlia e, non trovandolo, azzerava `parent_id` e `depth`. La premessa era falsa, perché la subordinazione è una disgiunzione x più un confronto di estensione e una figlia può estendersi oltre il padre: su Dag p.24 appiattiva tre bande annidate, e con esse la regola «vince la banda più profonda», **senza che nessuna interruzione fosse avvenuta** (151 blocker, zero attraversanti). Trovato perché l'uscita cambiava con zero attraversamenti, cosa che non può essere. Corretto: la genealogia si tocca solo quando il padre è stato davvero spezzato, e un figlio non viene mai orfanato — si riaggancia al pezzo che lo copre di più in y. Dopo la correzione Dag p.24 esce **identica**, cioè la regola non tocca quella pagina, e sul campione non resta nessun danno osservato.

Decisioni aperte dopo la sessione del 15-16 agosto 2026, in aggiunta a quelle sotto: **l'interruzione da immagine resta chiusa e non c'è più un caso che la richieda.** L'unico argomento a favore era il glifo che chiude i riquadri su DB p.50, ma lì `column_band` separa già i due box da solo — bande y 94-514 e y 526-750, con il secondo riquadro a y 518,8-689,4 secondo `interior_visual_frame` — e la pagina è giudicata corretta senza alcuna interruzione. Restano quindi: DB p.50 già corretta, Dag p.164 che è un **disegno** e non un'immagine, DB p.46 e Dag p.31 che la regola **danneggia**. Si tiene chiusa per lo stesso criterio con cui l'utente l'aveva ritirata la prima volta: nessuna pagina ha mostrato che serva. Il discriminante misurato (un'immagine interromperebbe solo dove non vive testo: chiusure di riquadro 0 caratteri, fondi 21-63) resta a verbale per il giorno in cui una pagina lo richieda, **non** è un lavoro aperto; **CHIUSA** quella sui cluster scartati, su decisione dell'utente («registrare la posizione di una cosa scartata non ci costa molto, e se è x >> y può essere significativa»): `page_analysis_drawing_cluster_diagnostics.py` emette ora `degenerate_bbox`, `degenerate_width` e `degenerate_height` per i cluster che `_visible_bbox` scarta. Chiave **nuova** e non `bbox` riempito, di proposito: `bbox` continua a significare "unione visibile con area positiva", e i due producer che leggono questa diagnostica scartano le voci con `excluded_reason` non nullo prima ancora di guardarlo. Criterio dichiarato prima e verificato: le uscite di `embedded_visual` e `interior_visual_frame` devono restare identiche — hash uguale su 3.385 candidati, cinque manuali per 40 pagine. L'aspetto separa da solo le due classi senza soglie: su Dag p.164 i filetti orizzontali escono 480,4×0,00 e 236,2×0,00 (`w/h` infinito), quelli verticali 0,00×8,02. **Non** «il reading order fra riquadri viene da `interior_visual_frame`», formulazione scartata dall'utente perché significherebbe implementare le bande dentro quel producer: il reading order non è mestiere di un producer. Quello che esiste già è il **fatto** che lì c'è un riquadro, emesso come candidato; a metterlo in relazione con le bande è il consumer, come `AGENTS.MD` §Layout e candidati prescrive.

Decisioni aperte al termine della sessione del 15 agosto 2026, tutte fuori dal perimetro del meccanismo. Se aprire la milestone `column_band` e con quale criterio di uscita: la base c'è in Milestone 36 e in `scripts/prototype_vertical_slice_page.py`, ma il suo invariante di conservazione è un multiset e quindi **cieco all'ordine** — un `column_band` perfetto e uno pessimo lo passano identici, e serve un terzo invariante che confronti l'ordine emesso con un riferimento umano su poche pagine trascritte a mano. La distinzione tabella/prosa, emersa come precondizione di più di un difetto e che appartiene a un altro producer; `table_candidate` non è utilizzabile come discriminatore perché emette candidati anche sulle pagine di prosa (misurato su Dag p.140 e DrW p.97), che è il problema del tasso di base già noto da Milestone 35. E l'unificazione delle due definizioni di orientamento del testo, quella di Milestone 6 e quella introdotta in Fase 4, che divergono sul testo obliquo.

Giunzione con la fetta verticale, sessione del 15-16 agosto 2026. Criterio pre-registrato e committato **prima** dell'implementazione e prima di guardare qualunque output (`Criterio_GiunzioneFettaVerticale_v1.md`, commit `eecbc8e`; il commit non contiene nulla della giunzione, ed è la prova della precedenza che alla riga 102 mancava). Chiude il buco che le righe 78 e 88 indicavano da due angoli: il confronto di reading order aveva le bande e non i producer, la fetta aveva i cinque producer e non le bande — **disgiunti**, verificato su `compare_reading_order_with_column_bands.py:62-69` contro `prototype_vertical_slice_page.py:64-84`. `--emit-order-variants` scrive `page_lines.md` e `page_bands.md` accanto a `page.md`, che resta invariato: precondizione P0 verificata byte per byte su DB p.99, 25 file asset inclusi.

**La riga tipografica viene dalla sorgente, non da un riassemblaggio geometrico.** Rilievo dell'utente, ed è la seconda volta che correggeva lo stesso punto. `pymupdf_capture.py:123-125` emette una primitiva per span e scrive la riga nell'id (`text:b{block}:l{line}:s{span}`); `_group_visual_lines` la scartava e la ricostruiva per sovrapposizione delle y, confrontando ogni candidato **solo contro il primo** elemento della riga. Non era solo ridondante, era sbagliato: fondeva righe di blocchi diversi — Dag p.48 54 righe geometriche contro 75 di sorgente, 21 fusioni; Dag p.164 50 contro 75, 25 fusioni. Su Dag p.48 il titolo `SOTTOCLASSI DEL RANGER` finiva nella stessa "riga" del corpo, e **una riga a cavallo di due colonne non è assegnabile a nessuna banda**: è la sovra-fusione di `_cluster_rows` (riga 30) ricomparsa nel consumer. Il caso che quella funzione citava a propria difesa non la difendeva: i sette span di Dag p.48 a y 410,89-411,01 sono un'unica riga di sorgente (`b8:l2`) e ordinati per `x0` dentro quella riga danno il testo corretto — il difetto veniva dalla **y** del sort globale, non dalla x. Sostituita da `_source_text_lines`; l'implementazione geometrica è conservata in `scripts/inspect_span_line_identity.py`, che è il verbale della sostituzione e continua a rimisurare la vecchia contro la nuova. Ordine dentro la riga: `span_index`, che diverge da `x0` in 2 righe multi-span su 6.335 (0,03%, cinque manuali), quindi la scelta non è portante. **Conseguenza sui dati già a verbale**: i giudizi a vista delle righe 80 e 90 e i conteggi della riga 100 vengono tutti dal percorso con l'assemblaggio difettoso.

Esiti della giunzione, contro le due predizioni registrate prima. **DrW p.97 esce corretta, e la predizione che restasse sbagliata è fallita** — ma per una ragione che è un aggiornamento del dossier, non una sorpresa: la banda non è più `396-652` come dice la riga 86, è **y 0-784**, tutta la pagina. L'estensione la porta attraverso la fascia dell'immagine e con un gutter unico l'ordine sinistra-poi-destra viene da sé. È l'effetto voluto della correzione con cui l'utente aveva allungato i gutter fin dove il corridoio è visibile. **Dag p.164 tiene ma mostra un difetto nuovo**: la banda 1 è `y 0-324` (non `60-240` come dice la riga 90 — le bande si sono allungate) e ci cade dentro `TIRI DEGLI AVVERSARI` a y 301,8, il titolo a piena larghezza della fascia centrale, che finisce in coda alla colonna sinistra invece che dopo entrambe.

Interruzione del corridoio, secondo criterio pre-registrato (`Criterio_InterruzioneCorridoio_v1.md`, commit `db11ff8`, anch'esso senza implementazione). Regola nella formulazione dell'utente: **attraversa il corridoio → lo interrompe; lo costeggia → no**, dove attraversare è coprire per intero l'intervallo x del gutter. La regola «l'immagine interrompe il corridoio» era stata ritirata (riga 96) perché nessuno aveva mostrato un caso reale in cui servisse; il caso ora esiste, ma **non è un'immagine**: i puntini di Dag p.164 sono `DrawingPrimitive` ad altezza 0,00 e larghi 480pt, né testo né immagine, e `embedded_visual` non li emette. Implementata **nel consumer** e non nel producer, perché combinare candidati di producer diversi è mestiere del consumer (`AGENTS.MD` §Layout e candidati, ratificato in Milestone 24 e 30): `column_band` non è toccato e la regola può solo spezzare ciò che il producer ha già emesso. Spezza e non tronca, perché troncare manderebbe fuori banda ciò che sta sotto l'interruzione e dove le colonne proseguono sarebbe un falso negativo. Entrambe le predizioni hanno tenuto: DrW p.97 identica byte per byte (20 blocker, zero attraversanti), Dag p.164 spezzata a y 287,19 con il titolo che va al posto giusto.

**Due numeri di Chat A da non riusare, corretti alla fonte.** Primo: «17% di bande toccate» era il raggio dei soli filetti, mentre la regola come pre-registrata include anche i candidati `embedded_visual` — con entrambi è **74,7%** (207 bande su 277, quattro manuali per 60 pagine). Secondo: «accorciamento mediano 141pt, massimo 657pt» era sbagliato due volte, perché lo script contava come pezzi di una banda anche quelli delle sue figlie (fino a tagli **negativi**, DB p.3 a −128pt) e usava una semantica di troncamento mentre l'implementazione spezza. Corretto tracciando `origin_band_id` sui pezzi invece di risalire per contenimento (`scripts/scan_corridor_interruption_impact.py`). **Attribuzione, che è il risultato utile: solo filetti 47 bande su 277 (17,0%) con taglio massimo 25,2pt; solo `embedded_visual` 204 su 277 (73,6%) con taglio massimo 708pt.** Le demolizioni vengono tutte dai candidati visuali.

Verifica a vista del campione, regola di estrazione fissata prima di guardare: 3 tagli massimi più 3 a caso con seed 20260815, dalla sola metà filetti — Dag 24, DrW 3, Dag 25, DB 13, Dag 8, DB 29. Su tutte e sei **nessuna primitiva esce dalle bande** (138→138, 90→90, 195→195, 80→80, 180→180, 91→91): il falso negativo da espulsione verso `(y0, x0)` non si presenta. La frammentazione è forte in conteggio (Dag p.24 da 11 a 50 bande) ma l'overlay grafico (`scripts/render_corridor_interruption_overlay.py`) mostra che è **confinata**: su DB p.29 le 12 bande sono le righe della tabella `D20 CIMELIO`, spezzate dalle campiture di sfondo, e la colonna sinistra non viene toccata perché quelle campiture non coprono il gutter esterno — su una tabella la lettura per righe non è un difetto. **Correzione di una lettura di Chat A**: la frammentazione era stata riportata come danno sulla base di Dag p.24, che è una scheda personaggio e quindi caotica di suo (rilievo dell'utente); il campione non mostra lo stesso danno altrove, e «è un danno» era più forte del dato. L'overlay rende anche visibile quanto della raccolta sia inerte: Dag p.24 ha 203 blocker di cui solo 19 attraversanti.

**Perché la metà `embedded_visual` non è utilizzabile, e non è che le immagini non debbano interrompere.** Le demolizioni hanno una causa sola, verificata a vista su due manuali: su DB p.46 il rosso copre tutta l'illustrazione a piena pagina, ma il testo `TERRENO`/`Impervio` **è stampato sopra** quell'illustrazione e le due colonne proseguono; identico su Dag p.31 con l'illustrazione del bardo e il blocco `MAESTRIA`. Su un filetto non ci sta sopra niente, quindi attraversare **è** interrompere; su un'illustrazione il testo ci sta sopra, quindi l'attraversamento geometrico non dice nulla sulla lettura. Il difetto è nel test «copre l'intervallo x», non nella regola dell'utente.

**Il discriminante, dato dall'utente su DB p.50 e confermato dai conteggi.** Il glifo allungato che chiude i riquadri è un'interruzione **utile**, senza la quale la pagina non si legge. Contando quanto testo vive dentro il bbox di ciascun candidato `embedded_visual` di quella pagina, i due gruppi si separano senza sovrapposizione: le chiusure dei box (490×40 a y 455-495, 504×18 a y 665-705) hanno **zero** testo dentro; i fondi di pergamena (530×400, 505×386, 507×171) ne hanno **63, 62 e 21**. Ne segue che un'immagine dovrebbe interrompere il corridoio **solo se in quella fascia non vive testo**. Non implementato: sarebbe il terzo giro dentro lo stesso giro. Da notare che l'informazione sul riquadro esiste già come candidato e non andrebbe dedotta dalle chiusure — `interior_visual_frame` (Milestone 30) emette su DB p.50 il riquadro `x 52,7-559,5 y 518,8-689,4` con 21 primitive dentro.

**Il paragrafo viene dal blocco della sorgente, non dalla geometria** (`Criterio_ParagrafoDaBlocco_v1.md`, commit `177f52c`, senza implementazione). Terza volta che l'utente corregge lo stesso schema, ed è una sua posizione permanente: la ricostruzione geometrica del testo ha già fallito altre volte, si usa **solo come posizionamento o controllo della posizione**, il testo deve arrivare da dove lo salva PyMuPDF. L'id di osservazione porta tutti e tre i livelli — `text:b{block}:l{line}:s{span}` — e ne usavamo due su tre. Verificato che il blocco **sia** il paragrafo: su DB p.53 `b3` è un paragrafo di prosa su tre righe, `b4`-`b7` sono quattro voci di elenco, una per blocco. La regola precedente confrontava le y di due primitive consecutive, e su DB p.53 uno span **senza testo** con bbox più alto della riga (630,5-644,0 contro 631,3-642,9) faceva da ponte fra una voce e la successiva, emettendone tre su una riga sola — regressione trovata dall'utente («anche nel test senza gap è rotta, mentre prima andava»), confermata contro lo script pre-sessione. La correzione applicata prima («una primitiva senza testo non fa da termine di paragone») è stata **tolta insieme alla deduzione**: era una pezza sul sintomo di una regola che non doveva esserci. Le tre definizioni (`_build_markdown_body`, `_ordered_markdown_body`, `_render`) sono tenute identiche di proposito.

Verifica del cambio con un invariante nuovo e più forte di quello di Milestone 36. **I2 — nessun riordino**: il cambio tocca dove si va a capo, non l'ordine, quindi la **sequenza** dei caratteri non-spazio letta a nastro deve restare identica carattere per carattere. Copre esattamente il buco che la riga 76 segnala nell'invariante di conservazione, che è un multiset e quindi cieco all'ordine. **Superata su tutte le pagine provate e su tutte e tre le varianti**: DB p.53 (2.695 caratteri), Dag p.164 (4.144), DrW p.97 (2.132), DB p.50 (2.996), DB p.99 (1.230). **P0 è stato cambiato di proposito e dichiarato**: `page.md` non è più byte-identico, perché usava la stessa regola difettosa e tenercela avrebbe voluto dire conservare un artefatto di Milestone 36 che sappiamo sbagliato; può cambiare **solo** nelle interruzioni di paragrafo, e I2 è la prova.

Esito, ed è il fatto che orienta il resto: **dove l'ordine è giusto il blocco dà il paragrafo giusto, dove è sbagliato smette di nasconderlo.** Su DB p.99 `page_bands.md` emette la prosa della colonna sinistra come un paragrafo unico e coerente; `page.md`, che ordina per `(y0, x0)` puro, passa da 27 a 45 paragrafi perché le due colonne si alternano riga per riga e il blocco cambia a ogni riga. La regola geometrica incollava quelle righe in un blob unico, nascondendo l'alternanza. I 45 frammenti sono la resa onesta di un ordinamento che Milestone 36 aveva già dichiarato illeggibile, non una regressione.

Difetto strutturale di `_segment_tree` trovato su DB p.53, **preesistente e non causato da questa sessione** (`scripts/prototype_derived_column_bands.py` non è toccato da `619f4f8` in poi). La subordinazione decide su x senza chiedere una sovrapposizione reale in y, e la figlia eredita come estensione x la **colonna del padre**. Su DB p.53 la banda del box `LESIONI GRAVI` (y 46-176, gutter 295-314) diventa figlia della banda della tabella (y 120-582, gutter 167-178) e ne eredita `x0 = 178` — un confine che nel box non esiste: 5 primitive del box lo scavalcano di netto, e **4 su 17 hanno il centro sotto 178**, quindi cadono fuori dalla banda del box e finiscono in quella della tabella. Il testo del box si legge male in **entrambe** le versioni, con e senza interruzione. Rilievo dell'utente, che aveva chiesto perché ci fosse un taglio verticale dove non c'è nessun gutter, e aveva collegato la cosa alla questione dell'ereditarietà. **I gutter invece sono corretti**: su quella pagina il meccanismo trova 295-314 nel box e 299-314 in `CONDIZIONI`, cioè esattamente dove le due colonne si separano — sembravano assenti solo perché `render_corridor_interruption_overlay.py` non li disegnava affatto e `render_gutter_tree_overlay.py` li disegna in verde sopra un riquadro verde. Il primo ora li disegna. **Conseguenza sul giudizio del giro dell'interruzione**: la regressione di DB p.53 non è attribuibile alla regola, che si limita a smascherare questo difetto — senza spezzamento la banda del box finiva prima di tutto per un caso fortunato (il suo `y0` sta sopra ogni altra cosa), con lo spezzamento si riaggancia a un pezzo di tabella e ci finisce dentro.

**La subordinazione si decide sui probatori** (`Criterio_SubordinazioneProbatoria_v1.md`, commit `29f6021`, senza implementazione). Primo cambio di questa sessione dentro `column_band` stesso. `_is_subordinate` aveva tre condizioni e ne misurava due sullo stesso asse in modi diversi: la seconda (chi è più esteso) sui probatori, la terza (si sovrappongono) sullo span. La terza passa ai probatori — una condizione, nessuna soglia. Il motivo è quello che `_GapRect` già documenta: lo span dice fin dove si **presume** che la separazione continui, `y0`/`y1` dove è **dimostrata**, e «questa struttura sta dentro quella» è una claim strutturale che deve poggiare sulla dimostrazione.

Esiti, contro le tre predizioni registrate prima, tutte tenute. **G1, la porta, regge**: zero gutter spariti senza etichetta, gli stessi 4 scartati come `edge_strip` (le linguette di Fab) prima e dopo, su cinque manuali per 60 pagine. **G2, la hard rule dell'utente resa contabile — nessun confine x di banda dentro il bbox di una primitiva che la banda contiene — scende da 178 a 109 tagli, e da 25 a 22 pagine**; in nessun caso sale. Le bande passano da 298 a 310, che è l'effetto atteso: un gutter che smette di essere subordinato diventa massimale e genera bande proprie. Su DB p.53 il box `LESIONI GRAVI` è ora banda di primo livello (`x 0-612`, gutter 295-314) e **0 delle sue 17 primitive** finiscono nella banda della tabella, contro 4 prima; l'uscita emette la colonna sinistra intera, poi la destra, poi la tabella. DrW p.97, DB p.50 e Dag p.164 invariate, come predetto.

**Tre errori di misura di Chat A in questo giro, tutti sul metro e non sul meccanismo**, registrati perché il primo avrebbe fatto fallire la porta prima ancora di cambiare qualcosa. G1 misurata contando quante volte la stringa x di un gutter comparisse fra le righe dell'albero: falso allarme, perché `_segment_bands` ripete lo stesso gutter in ogni fascia y che attraversa. Poi misurata su `tree_status != "band"`: secondo falso allarme, perché `edge_strip` è uno scarto **etichettato** e non una sparizione. La misura buona è la terza, e sta in `scripts/verify_band_tree_invariants.py`.

Buco localizzato in `page_analysis_drawing_cluster_diagnostics.py`, trovato rispondendo a una domanda dell'utente sui vettoriali. La funzione **li trova e li classifica già**: su Dag p.164 restituisce 9 cluster, 7 etichettati `tiny`, e il filetto dei puntini è fra quelli. Ma per i cluster esclusi emette `bbox: None` — **li classifica e ne butta la geometria**, quindi nessuno a valle può usarli. La causa esatta sono due meccanismi distinti che colpiscono lo stesso oggetto: `_classify_eligibility` lo marca `tiny` perché `area < 4.0`, e `_visible_bbox` ne butta la geometria perché rifiuta `y0 >= y1`. È il motivo per cui la regola del consumer ha dovuto tornare alle `DrawingPrimitive` grezze e ridedurre «più basso della riga più bassa» invece di leggere una classificazione che esiste. **Chiuso**: v. la decisione sopra, `degenerate_bbox` registra ora la posizione senza toccare `bbox`.

Esito dei due giri, giudicato a vista dall'utente. **`page_bands.md` funziona**, con le pagine di prova verificate direttamente: DrW p.97, Dag p.164 e DB p.50 (83 primitive su 88 in banda). L'interruzione del corridoio **non viene adottata come pre-registrata** e il flag `--interrupt-corridor` resta spento di default: la metà filetti regge ma risolve un caso solo, la metà `embedded_visual` annienta (DB p.50 passa da 83 primitive in banda a **0**). Nessun producer, contratto o wiring è stato modificato in nessuno dei due giri.

Diagnostica non wired, nessuna modifica a producer, contratti o wiring in nessuna delle quattro fasi — stesso standard delle altre milestone esplorative. Tutti gli script delle quattro fasi — Fase 1 e Fase 2 in 786b547 (dieci script; nessuno per Fase 3, che non ne ha prodotti), Fase 4 e gli script di confronto e di misura nei commit successivi — stanno sullo stesso branch di lavoro e arrivano su main insieme a questa sezione. **Correzione**: una versione precedente di questa frase citava 786b547 come se fosse già su main e distingueva da esso gli script "non ancora su main"; la distinzione non esisteva, 786b547 è il primo commit del branch. Rilievo di Chat B, verificato.

**Decisione aperta e bloccante, mai messa per iscritto prima d'ora.** `AGENTS.MD` §Migrazione e
shadow mode prescrive che lo shadow mode abbia "criteri di equivalenza **e una milestone di
uscita**". I criteri di equivalenza sono elencati lì; la milestone di uscita **non esiste in
nessun punto di `State.md` o `AGENTS.MD`** — non è stata rinviata, non è mai stata scritta.
Lo stato reale dopo 35 milestone: cinque producer wired, una sola regola di Resolution, nessuna
persistenza del `PageAnalysis` prodotto, nessuno stadio asset, nessuna IR 2, renderer intoccati.
La pipeline nuova non è in grado di produrre una singola pagina di output, e le decisioni
rinviate (precedenza fra regole di Resolution, stadio asset, contratto `column_band`) vengono
discusse in astratto. È lo stesso metodo che le otto falsificazioni registrate sotto Milestone 35
hanno screditato sui manuali, applicato all'architettura.

Milestone 24 ha ratificato la relazione fra `layout.page_edge_visual` e
`layout.side_band` (singleton e local-fragment): restano due producer indipendenti,
nessuna unificazione di contratto — operano su primitive di tipo diverso (`text` vs.
`image`/`drawing`) e la co-occorrenza reale è rara (<1% delle pagine su 5 manuali
interi testati, 1381 pagine). La relazione resta lavoro futuro di Resolution/consumer
(invariante `State.md`: "Resolution è l'unico livello che può accettare, rifiutare o
lasciare irrisolto un candidato"), con una nota di design: quando quel lavoro verrà
aperto, distinguere contenuto reale (es. testo di intestazione capitolo contenuto in
una fascia decorativa) da coincidenza di margine (overlap geometrico presente ma di
magnitudo trascurabile, es. un bullet decorativo che sfiora il bordo di uno sfondo)
richiederà una soglia sul rapporto fra overlap e dimensione del candidato più piccolo,
non un booleano overlap/disjoint — coerente con la scelta di Milestone 16 di non
esporre containment/ratio in `measure_co_referenced_page_candidate_pair`.

Appunto per una futura passata di raffinamento (non aperta, non numerata):
`layout.page_covering_visual` non distingue geometricamente sfondo ripetuto da
illustrazione unica (regola page-local, nessuna visibilità sul documento). Verificato su
tre manuali reali: `ImageOccurrencePrimitive.content_digest` (già in
`primitive_model.py`, popolato da `pymupdf_capture.py`/`primitive_normalizer.py` via
`get_image_info(hashes=True)`) permette di raggruppare le candidate per identità di
contenuto — digest su decine/centinaia di pagine (spesso a passo 2) è sfondo; digest su
una pagina, o poche non sistematiche, è candidato a illustrazione unica. Un futuro
consumer document-level nello stile di `measure_document_candidate_kind_occurrences`
(Milestone 12), raggruppato per `content_digest`, non richiederebbe modifiche di schema
per il caso immagine. `DrawingPrimitive` non ha invece alcun campo di identità
(`primitive_model.py`): non bloccante nei tre manuali testati, perché lo sfondo
ricorrente è sempre risultato un'immagine raster; le candidate `drawing` erano rare,
concentrate su coppie di pagine adiacenti, coerenti con spread illustrativi doppi.

**Sanatoria (Milestone 35, retroattiva)**: gli script che hanno prodotto la verifica sopra
(`verify_page_covering_visual_content_digest_recurrence.py`, tre manuali) e la sua
controparte per `page_edge_visual` (`verify_page_edge_visual_content_digest_recurrence.py`,
stesso approccio, i suoi numeri non sono riportati in questa nota) non erano stati
committati all'epoca — trovati non tracciati durante il riordino di Milestone 35,
committati ora in `ecb5b72`.

Appunto per una futura passata di raffinamento (non aperta, non numerata):
il progetto originale (pipeline legacy) distingueva già immagini raster e vettoriali
(`ImageBlock`/`VectorBlock`, `extractor.py`). Potrebbe essere utile, in un futuro
non immediato, permettere di salvare le immagini raster estratte in alta qualità o
di preferire un'estrazione vettoriale quando disponibile, invece della sola
rasterizzazione attuale. Nessuna decisione presa, nessun impatto sul lavoro corrente.

Appunto per una futura passata di raffinamento (non aperta, non numerata):
la verifica su manuali reali di Milestone 26 (`dump_drawing_cluster_diagnostics`)
mostra che `dispersion_ratio` basso ha due cause strutturalmente opposte,
indistinguibili senza ispezione visiva. Su Kul p.169/p.167 un'unica illustrazione
xilografica densa (fregio floreale di apertura capitolo) viene frammentata dal
clustering in piu' cluster separati (margine 5pt insufficiente a riunirla): dispersion
bassa per spazio negativo naturale dell'incisione, non per errore di fusione. Su DB
p.125 (scheda personaggio) decine di piccole icone decorative non correlate (diamanti
di spunta accanto a ogni abilita', fregi a nastro) vengono invece incatenate in un
unico cluster nominale da 68 membri via transitivita' del union-find, coprendo quasi
l'intera pagina: qui la dispersion bassa segnala un vero bridging fra elementi
scollegati. Una soglia fissa uniforme su `dispersion_ratio` non basta a separare i due
casi; un eventuale raffinamento futuro (parametro sul margine, limite sulla lunghezza
della catena, o altro) andrebbe informato da altri esempi reali, non solo da questi
due. Nessuna decisione presa, nessun impatto sul modulo Milestone 26 (resta
diagnostica pura, corretta per lo scopo dichiarato).

La pipeline legacy, IR, Markdown ed EPUB restano autorevoli. I nuovi contratti lavorano in shadow mode e non producono ancora decisioni editoriali, IR o output finale.

## Pipeline legacy e baseline da preservare

Pipeline attiva:

```text
PDF
→ extractor.py
→ PageData / TextBlock / ImageBlock / VectorBlock / TableBlock
→ ir_builder.py
→ DocumentIR 1.0
→ markdown_builder.py
→ Markdown
```

L'EPUB resta legacy/parzialmente IR-first. Restano non-regressione:

- callout DB region-first e callout affiancati;
- tabelle DB e rimozione del testo tabellare duplicato;
- reading order DB stabilizzato, incluso `MONETE`/`CIMELIO`;
- immagini readable e classificazione clutter `decorative`/`structural`;
- dropcap unresolved senza invenzione di testo;
- IR 1, Markdown corrente ed EPUB legacy invariati.

`PageData` è legacy, non raw canonico: può servire solo come riferimento di non-regressione, adapter diagnostico o fallback temporaneo.

## Architettura target approvata

```text
PDF snapshot
→ BackendPageCapture
→ NormalizedPrimitivePage
→ PageAnalysis
→ DocumentAnalysis
→ Resolution
→ ResolvedSemanticDocument
→ DocumentIR 2
→ renderer Markdown / EPUB
```

Confini invarianti:

```text
osservazione backend
≠ primitive normalizzate
≠ layout
≠ candidati
≠ semantica
≠ politica editoriale
≠ IR
≠ rendering
```

- Raw e primitive normalizzate sono immutabili; i derivati dichiarano input, configurazione, versione e generation ID.
- `LayoutRegion` è un fatto strutturale; `RegionCandidate` è una proposta page-local non approvata, non ownership, coverage, ranking, confidence o decisione.
- `layout.side_band` è strutturale; `marginalia` è un possibile ruolo semantico successivo.
- Resolution è l'unico livello che può accettare, rifiutare o lasciare irrisolto un candidato.
- Nessuna esclusione o rimozione di contenuto è silenziosa. Markdown ed EPUB dovranno consumare IR validata, non reinterpretare il PDF.

## Milestone completate — sintesi

Milestone 1–5 completate. Hanno consolidato:

- capture backend-neutral e primitive normalizzate canoniche;
- adapter PyMuPDF shadow, normalizzazione deterministica e dump diagnostici locali;
- workspace/job minimo: snapshot verificato, manifest versionato, capture progress e resume per pagina;
- `PageAnalysis` schema `1.2`, provenance page-level, validazione cross-model, serializzazione e store JSON;
- producer root pagina e visible primitive extent, più diagnostica shadow `analysis`.

I dettagli storici di file, test e commit sono disponibili nei commit precedenti e nelle versioni pregresse di `State.md`.

Milestone 6–19 completate. Dettaglio narrativo completo spostato in `State_Archive.md`
(Parte 1) — non necessario per le decisioni correnti, i contratti restano vigenti e
descritti in forma permanente in `AGENTS.MD`. Hanno consolidato, in ordine:

- Milestone 6: candidate `layout.side_band` (producer singleton e local-fragment,
  entrambi congelati come baseline diagnostiche, non detector affidabili) e un primo
  substrato geometrico page-local puro (`PrimitivePairMeasurements`,
  `measure_primitive_pair`, stage diagnostici `primitive-pair`/`primitive-neighborhood`,
  producer `layout.page_covering_visual` e `layout.page_edge_visual`);
- Milestone 7: misure page-local pure e non decisionali fra candidate esistenti e
  primitive non-candidate (`CandidatePageContextMeasurements`,
  `CandidateExtentRelationMeasurements`), senza identificare corpo pagina, colonne,
  tabelle o marginalia;
- Milestone 8: contratto `DocumentAnalysis` — contenitore document-local immutabile,
  puro e versionato, al più una `PageAnalysis` per pagina, documenti parziali ammessi;
- Milestone 9: `DocumentSourceAttestation` e `attest_pymupdf_document_source` — identità
  verificata di una precisa sequenza di byte, `source_id` e `page_count` letti dagli
  stessi byte, PyMuPDF-only;
- Milestone 10: costruzione attestata di `DocumentAnalysis` a partire
  dall'attestazione di Milestone 9;
- Milestone 11: `BoundDocumentAnalysis` — binding in memoria, per identità, delle
  `PageAnalysis` di un documento;
- Milestone 12: inventario document-local delle candidate per structural kind;
- Milestone 13–19: infrastruttura page-local per correnti di analisi co-riferite —
  collezione (`BoundCoReferencedPageAnalyses`, Milestone 13), binding alla pagina
  normalizzata (Milestone 14), riferimento page-scoped a una candidate
  (`CoReferencedPageCandidateReference`, Milestone 15), misure geometriche fra due
  candidate co-riferite (Milestone 16), flusso diagnostico (Milestone 17), misure degli
  insiemi di primitive referenziate (Milestone 18) e diagnostica delle relazioni fra
  quegli insiemi (Milestone 19) — un sottosistema chiuso, non esteso da lavoro
  successivo alla sua chiusura.

## Milestone 20 — TableCandidateProducer (producer tabelle, configurazione unica `text_lines`) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 21 — wiring del primo producer nel job (esecuzione runtime, senza persistenza) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 22 — cache opportunistica del PageAnalysis — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 23 — wiring del secondo producer nel job (page_covering_visual, apertura selettiva del backend) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 24 — wiring del terzo producer nel job (page_edge_visual, ratifica

side_band/page_edge_visual) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 25 — diagnostica pura per visuali interne (interior-visual-diagnostics) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 26 — diagnostica di clustering geometrico per DrawingPrimitive (drawing-cluster-diagnostics) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 27 — producer per visuali interne (embedded_visual, no wiring) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 28 — wiring del quarto producer nel job (embedded_visual) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 29 — diagnostica esplorativa per riquadri di testo (box-like interior visual) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 30 — producer per riquadri di testo (layout.interior_visual_frame, no wiring) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 31 — wiring del quinto producer nel job (interior_visual_frame) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 32 — diagnostica esplorativa per struttura colonne (column-structure-diagnostics) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 33 — contratto per le bande di colonne (decisione architetturale, no build) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 34 — Resolution: design (Modalità P) e prima regola (deduplicazione IVF/EV) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 35 — diagnostica di clustering vettoriale: filtro mancante, colore, frequenza — completata

Artefatto di origine: `3e10304` (diagnostica esplorativa `scan_table_candidate_visual_area_coverage.py`,
mai attribuito prima — assente sia dalla chiusura di Milestone 34 sia dalle prime versioni di
questa). Design in `Proposta_Milestone35_ClusteringColorDiagnostics_v1.md`..`v10.md` e
`Chiusura_Milestone35.md` (non nel repo, stessa prassi di Milestone 33/34), sette giri di
revisione Chat B integrati, ogni citazione verificata prima di integrare. Commit:
`610031c` (`scan_table_candidate_visual_area_coverage.py`), `d50eaee`
(`scan_embedded_visual_interior_visual_frame_twin_diagnostics.py`,
`summarize_milestone35_measures.py`), `c3742e1` (`inspect_milestone35_population_structure.py`),
`615db35` (fix chiave di join), `af821e7` (colonne `dispersion_ratio`/`avg_stroke_width`/
`is_closed_share`, opzione `--pages`), `63d4c25` (oracolo, rigenerato con `csv.writer` dopo
malformazione — v. nota sotto), `0a185a4`/`230c7fe` (test callout), `2fda096` (chiusura).

**Esito**: la premessa che ha originato la milestone (quattro pagine Lancer con un cluster
`embedded_visual` privo di gemello `interior_visual_frame`, lette come "pannelli decorativi
impilati") è stata **falsificata per ispezione visiva diretta**, non dalle quattro misure (i)-(iv)
originariamente previste — nessuno dei tre esiti previsti in §Criteri di chiusura si è verificato
alla lettera; la milestone chiude per falsificazione della premessa per via esterna alle misure, un
quarto esito non contemplato dai criteri originali, non da ricondurre a uno dei tre (in particolare:
non equivale all'esito 2, che richiedeva sotto-cluster color-partizionati fuori range o senza
testo — non osservato, criterio 1 è risultato 79/80 positivo). Tre delle quattro pagine sono box di
regole/stat-block a sfondo colorato, la quarta è lo sfondo a righe di una tabella dati reale —
nessuna è un pannello decorativo. Le misure (i)-(iv), eseguite comunque sui 7 manuali disponibili
(80 cluster target), non discriminano: criterio 3 (assenza di testo come causa) 0/80; criterio 1
(79/80) soddisfatto alla lettera ma non discriminante — un caso confermato falso (Dag p.24, scheda
personaggio) passa gli stessi filtri numerici di un caso confermato vero (Kul p.42, cornice
decorativa).

**Nessuna milestone di progettazione di un criterio di clustering per colore si apre**: oltre alla
non-discriminazione sopra, D5 quantifica il rischio già segnalato per pag. 119 (fondo zebra) — un
futuro criterio di clustering per colore, applicato senza eccezioni, produrrebbe 4-12 sotto-
candidati spuri per cluster sulle quattro pagine di origine (p.37 7 fill/7 stroke; p.114 8/12; p.119
5/4; p.131 4/7), la ragione concreta per cui la linea non viene aperta, non solo la decisione.

`dispersion_ratio` (Milestone 26): il gap osservato su etichette corrette (modulo/tabella ≤2.324,
decorativo ≥2.860) reggeva solo su n=2 dal lato decorativo, stesso manuale — verificato sul
controesempio già noto di `State.md` (Kul, illustrazione xilografica frammentata dal clustering;
indice 0-based 166/168, offset dedotto per tentativi con verifica visiva del contenuto, non
documentato in precedenza — analogo all'offset già noto per Lan, +2 pagine di frontespizio non
numerate). 72 cluster vettoriali reali su quelle pagine, `dispersion_ratio` 0.051–1.062 (mediana
0.773), tutti bassi quanto i moduli UI — **ma nessuno di questi 72 è nella fascia `above_max` che
questa milestone indaga** (0/150 righe totali, raster incluso). Il controesempio dimostra quindi che
`dispersion_ratio` basso ha due cause opposte su cluster piccoli/frammentati, non che il segnale
fallisca specificamente nella fascia d'uso dei cluster fuori tetto d'area — distinzione che non
cambia la conclusione operativa (n=2 era comunque insufficiente per una soglia) ma cambia lo stato
epistemico: il segnale non è escluso nella fascia rilevante, resta non provato.

Test di fattibilità (domanda dell'utente, indipendente da Chat B): il rilevatore di callout della
pipeline legacy (`ir_builder.py`, `_merge_callout_blocks`, pattern testuale titolo maiuscolo breve +
corpo ≥40 caratteri, riprodotto localmente solo nella logica stringa) separa 7 casi su 9
dell'oracolo secondo la mappatura `modulo_ui_*`/`tabella_zebra` → pattern atteso presente,
`pannello_decorativo*` → pattern atteso assente. **Concordanza valutata post-hoc sullo stesso
insieme di 9 casi**, dopo rimozione di un fallback (concatenazione testo del bbox) che produceva un
falso positivo su Kul p.0 — non una stima fuori campione. Falso negativo (DB p.124 ×2) spiegato
strutturalmente: modulo a campi vuoti, nessun paragrafo di corpo per costruzione. Non un
discriminante pronto — un candidato per un futuro producer, non deciso qui.

Bug trovato e corretto in corso di lavoro, non specifico di questa milestone: `cluster_id`/
`primitive_id` (`primitive_normalizer.py:141`, `_primitive_id` deriva l'id dall'`observation_id`)
non sono univoci nel manuale, solo nella pagina — qualunque aggregazione cross-pagina che usi
`cluster_id` da solo come chiave rischia di fondere sotto-cluster di pagine diverse. Nota per futuri consumer.

Fuori scope, invariato: nessuna regola di Resolution su `layout.table`×`layout.embedded_visual`/
`layout.interior_visual_frame` (`Proposta_ResolutionDesign_v3.md` §8.2.2) — questa milestone
forniva evidenza, non l'ha trovata a supporto di una regola specifica basata su colore/clustering.
Non decisa: proposta di regola di processo per `AGENTS.MD` (ispezione visiva preventiva prima di
progettare una diagnostica attorno a un'assunzione sul contenuto delle pagine) — rimandata a
discussione separata.

**Milestone chiusa in `2fda096`.**

**Riconsiderazione del tetto d'area (`_DEFAULT_MAX_AREA_RATIO`, 0.28) — scartata su
evidenza.** L'opzione C della proposta v1, scartata al primo giro senza riesame, è
stata riesaminata puntualmente dopo la chiusura, senza scrivere codice, rieseguendo
`scripts/scan_interior_visual_frame_diagnostics.py` (Milestone 29) con
`--min-area-ratio 0.28 --max-area-ratio 0.70` su tutti e sette i manuali. I quattro
casi d'origine sono confermati e riproducibili (Lan p.114 `0.2832`, p.37 `0.2851`,
p.131 `0.2979`, p.119 `0.5890`), ma la separazione che suggerivano non esiste nella
popolazione: 407 righe con testo contenuto cadono fra `0.283` e `0.589` sui sette
manuali (dag 139, fab 91, lan 50, vil 44, db 43, apo 37, kul 3), con distribuzione
continua e senza salti (35/31/42/102/47/56/74/29/24/10 per fascia da `0.28` a `0.70`).
Anche la fetta `0.2832`–`0.2979`, che contiene tre dei quattro casi, contiene almeno
altre quattro pagine Lancer mai citate (p.163 `0.2836`, p.59 `0.2919`, p.295 `0.2932`,
p.329 `0.2975`): i "quattro casi con separazione ampia" erano quattro di almeno sette
nella stessa fascia, dello stesso manuale. Non esiste quindi un valore di
`max_area_ratio` che ammetta i box confermati ed escluda il resto, e nessun valore
sarebbe meno arbitrario di `0.28`. Il volume non è l'argomento: su DB il tetto attuale
produce 966 candidate (2552 righe nel range, 120 pagine) e la fascia alta ne
aggiungerebbe 51, +5%. L'argomento è l'assenza di separazione. `dispersion_ratio` non
separa neppure qui (p.119, caso da escludere, `1.3473`, in mezzo a p.160 `1.2991`,
p.164 `1.2268`, p.168 `1.1243`), coerentemente con la conclusione già registrata sopra.
Osservazione non promossa a criterio, n=4: `contained_text_area_ratio` va nella
direzione opposta all'intuizione (i due box `0.7637`/`0.7009`, il terzo `0.4528`, la
tabella zebra da escludere la più bassa, `0.2967`; mediana della popolazione `0.1638`).
Asimmetria strutturale da tenere presente: Apo, Fab e Vil non hanno alcuna riga
vettoriale nella fascia (0 su 37/114/57), Lan 39, Dag 30, DB 7, Kul 2 — un eventuale
tetto futuro non potrebbe essere unico per i due rami. Nota di processo: la premessa
era vera sui quattro casi ispezionati e falsa sulla popolazione, stesso schema di
errore della premessa d'origine di questa milestone nella sua variante statistica;
è emersa al primo giro di Modalità P, prima di qualunque riga di codice, per il costo
di sette esecuzioni dello script già committato.

Massa irrisolta di embedded_visual: ripetizione geometrica e identità di contenuto — entrambe scartate su evidenza. Campione casuale riproducibile di 280 pagine (40 per manuale, 7 manuali, seed 20260802, scripts/sample_resolution_prototype_pages.py): 3917 candidate embedded_visual irrisolte, di cui 2671 (68,2%) in gruppi di almeno 3 bbox identiche, IC95 bootstrap per pagina 60,6–73,7%. L'aggregato si dissolve alla disaggregazione: Kul 93,6% (1570 irrisolte), Fab 72,1% (1353), DB 27,8% (756), Vil 23,1% (52), Lan 8,9% (45), Dag e Apo 0,0% (90 e 51). Kul ha 11 sole forme distinte e la dominante 284.9×5.2 compare 27 volte per pagina su 26 pagine su 40: da sola Kul vale il 55% della massa "ripetuta" del campione. L'ispezione visiva (regola 14) mostra che la firma unifica cose opposte: su Kul è il fondo a righe della pagina, su Fab sono le icone degli oggetti nelle tabelle di equipaggiamento — contenuto da preservare, non arredamento — e sulla stessa pagina di Fab convivono icone e filetti di riga con firma di ripetizione identica. ImageOccurrencePrimitive.content_digest è stato testato come discriminante alternativo (scripts/inspect_image_content_digest_recurrence.py) e non separa: Kul 284.9×5.2 dà 1 digest su 27 occorrenze e 108 occorrenze su 4/4 pagine, le icone Fab 20.9×20.9 danno 12 digest su 12 occorrenze come atteso, ma i filetti Fab 56.0×1.0 danno 21 digest su 27 occorrenze e 231.0×1.0 ne danno 9 su 9 — arredamento che non condivide identità. Le fasce di tabella di DB sono raster e danno 2 digest su 4 occorrenze a p.33, 4 su 4 a p.53. Nessuna milestone si apre. Resta valido, e rafforzato da una seconda conferma indipendente dopo Milestone 23, il solo uso stretto già annotato in §Stato operativo: un consumer document-level per content_digest limitato all'arte raster ripetuta identica. La lacuna di identità su DrawingPrimitive non è stata esercitata: tutti i casi osservati erano raster.

Copertura fra producer delle candidate embedded_visual irrisolte — primo esito parzialmente positivo, non ratificato. Fino a qui il confronto fra producer era stato osservato solo fra embedded_visual e interior_visual_frame: il prototipo di Milestone 34 costruisce due producer su cinque, quindi table_candidate, page_covering_visual e page_edge_visual non erano mai entrati in una CoReferencedPageAnalyses reale. scripts/measure_cross_producer_candidate_coverage.py costruisce tutti e cinque i producer wired sulla stessa NormalizedPrimitivePage, li lega con il sottosistema Milestone 13-19, applica resolve_page_candidates e misura, per ogni candidate embedded_visual rimasta unresolved, la frazione della propria area coperta dalla candidate più sovrapposta di ciascun altro producer. Eseguito sulle 120 pagine di Kul/Fab/DB già estratte nel campione casuale da 280 (seed 20260802), senza riestrazione. Candidate prodotte: embedded_visual 4110, interior_visual_frame 431, page_covering_visual 122, table_candidate 71, page_edge_visual 61; 3679 embedded_visual restano irrisolte. Il risultato grezzo — 96,6% coperte a ≥0,9 — è degenere: page_covering_visual produce circa una candidate per pagina (41 su 40 pagine Kul, 39 su 40 Fab, 42 su 40 DB, presente su 116 pagine su 120) e per costruzione delle proprie soglie (visible_width_ratio >= 0.95 e visible_height_ratio >= 0.95) contiene ogni altra candidate della pagina, quindi la sua copertura non porta informazione. Correzione post-hoc, dichiarata come tale e non pre-registrata: escluso page_covering_visual dal calcolo, la copertura a ≥0,9 diventa Kul 0,0% (IC95 bootstrap per pagina 0,0–0,0%), Fab 68,8% (48,5–80,5%), DB 34,0% (27,1–40,3%); considerando il solo table_candidate, Fab 53,3% (34,3–63,2%) e DB 18,0% (12,4–23,0%). La predizione registrata prima dell'esecuzione era confermata su Kul (nessun altro producer vede il fondo rigato; table_candidate non scatta su nessuna delle 40 pagine) e su Fab, fallita su DB, dove le fasce di tabella erano attese coperte da table_candidate a ≥0,9 e lo sono per meno di un quinto. Osservazione non prevista e rilevante: su Fab il 40,6% delle irrisolte è coperto a ≥0,9 da interior_visual_frame — sono candidate senza gemello IVF a insieme di primitive identico, quindi fuori dalla regola unica di Milestone 34, ma geometricamente contenute in un riquadro IVF. È un secondo tipo di relazione fra candidate, contenimento senza identità, misurabile con i contratti Milestone 13-19 già scritti e oggi non toccato da alcuna regola. Il calcolo di sovrapposizione in linea è stato riverificato su Fab p.284 contro measure_co_referenced_page_candidate_overlap_ratio (Milestone 34): 300 coppie, 0 discordanze. Nessuna milestone si apre. Conclusione operativa: il confronto fra producer è informativo, ma non è il primo passo — finché page_covering_visual promuove a candidate lo sfondo del 97% delle pagine, qualunque misura di copertura va corretta a mano per non essere dominata da lui. La precondizione è distinguere sfondo ricorrente da illustrazione unica, cioè il consumer document-level per content_digest già annotato in §Stato operativo, che riceve qui la sua terza gamba empirica dopo Milestone 23 e dopo il caso Kul (1 digest, 108 occorrenze su 4 pagine su 4). Solo dopo ha senso rimisurare la copertura fra producer, e in quel caso il contenimento interior_visual_frame ⊃ embedded_visual è la relazione da guardare per prima.

Appunto per una futura passata di raffinamento (non aperta, non numerata):
misura esplorativa sul rumore raster, 16 manuali reali, nessun codice di produzione
toccato. La pipeline nuova conta **collocazioni** (`ImageOccurrencePrimitive` è per
occorrenza) mentre la pipeline legacy conta **immagini** (`get_images` per xref più
`rects[0]`, più deduplica MD5 document-scoped in `_extract_images`): il divario è di
uno o due ordini di grandezza. Raggruppando per `content_digest` — campo già presente
e popolato via `get_image_info(hashes=True)`, zero mancanti su 27.437 occorrenze
misurate — Kul passa da 8774 occorrenze a 107 asset distinti (collasso 82×), DB da
3534 a 991 (3,6×), Fab da 15129 a 4411 (3,4×). Il collasso è quindi forte su un
manuale su tre e non è il meccanismo dominante.

Il filtro raster del legacy (`config.min_image_width/height = 80` px, unico scarto
applicato a `_extract_images`) è **inutilizzabile** sotto l'obiettivo "ogni immagine
diventa una nota": su Fab elimina 258 digest con dimensione intrinseca 16×16 px che sono le icone degli
oggetti nelle tabelle equipaggiamento, cioè contenuto. L'asse dimensionale resta però
reale: `intrinsic_width`/`intrinsic_height` sono già sul contratto di
`ImageOccurrencePrimitive` e nessun producer li guarda.

Ipotesi verificata e falsificata, poi riformulata. La prima formulazione — filetti e
immagini si distinguono per forma, con lato minore in PIXEL ≤16 e aspetto ≥4 — è stata
falsificata secondo un criterio registrato prima dell'esecuzione, l'esistenza di una valle
di densità stabile fra editori (`scripts/inspect_aspect_density_valley.py`): quattro
manuali su sei analizzabili hanno una valle, a 1,83 / 3,67 / 29,34 / 83,0, dispersione 45×
contro una soglia di caduta di 4×. Sull'asse del lato minore, su tutti gli asset senza
prefiltro, dieci manuali su sedici hanno una valle, da 1,5 a 558 px, dispersione 362×. Le
valli non sono nemmeno lo stesso fenomeno: due sono bin vuoti in dati radi, una cade fra
due picchi entrambi quadrati. Difetto di impostazione trovato dall'utente e non da Chat A:
la dimensione in pixel intrinseci è una proprietà di come l'editore ha esportato il file,
non dell'oggetto sulla pagina.

Riformulazione: lato minore in PUNTI diviso il corpo del testo, incrociato con il rapporto
d'aspetto (`scripts/inspect_image_typographic_shape.py`, 16 manuali). Il corpo è stimato
dalla moda delle `font_size` della pagina stessa, quindi il criterio resta funzione pura di
una singola `NormalizedPrimitivePage`: nessun passaggio documentale, nessuna interferenza
con la cache di Milestone 22, con l'ordine di esecuzione o con la persistenza rinviata da
Milestone 21. La prima versione dello script stimava però il corpo accumulando le
`font_size` su tutto il documento, cioè normalizzava sul corpo del MANUALE mentre
l'argomento che sosteneva è pagina-locale — difetto trovato dalla revisione Chat B, non da
Chat A, e dello stesso genere di quello che aveva ucciso l'asse in pixel: un riferimento
sbagliato scambiato per quello giusto, annidato stavolta dentro l'argomento con cui quel
tipo di errore veniva respinto. Corretto e rimisurato. **Effetto pratico piccolo**: la
dispersione del corpo dentro un manuale è al massimo 1,12× fra p10 e p90, e su sette
manuali su sedici è esattamente 1,00, quindi le due normalizzazioni danno quasi lo stesso
risultato. Sulla mappa page-local le due cose che il filtro legacy a 80 px confondeva
restano in regioni diverse: le icone degli oggetti di Fab sono intorno a 2 corpi con
aspetto 1,0, i suoi filetti ≤0,2 corpi con aspetto ≥8 (2126 asset, 6712 occorrenze); il
fondo rigato di Kul, che in punti assoluti sembrava anomalo a 5,2 pt, normalizzato sta
nella fascia banda con aspetto 52 e 8210 occorrenze.

Due cose emerse solo dalla versione corretta. La prima: i cali osservati rispetto alla
mappa documentale non sono riclassificazioni ma **esclusioni**. Le immagini su pagine dove
il corpo non è stimabile (meno di 20 primitive testuali) prima ricevevano comunque una
regione usando il corpo del manuale, adesso non ne ricevono nessuna — e sono una quota non
trascurabile: Lan 69 occorrenze su 157 (44%), DIE 96 su 377 (25%), Vil 104 su 663 (16%),
BoB 113 su 750 (15%), DB 264 su 3534 (7%), Fab 35 su 15129 (0,2%). Le pagine senza testo di
corpo sono le tavole a piena pagina, cioè proprio dove stanno le illustrazioni grandi: non
è che il corpo di pagina sia una stima peggiore, è che su una classe intera di pagine non
esiste. Limite dell'impostazione page-local non previsto da nessuno dei tre. La seconda:
l'unico spostamento non spiegato da esclusioni è su Fab, circa 280 asset passati da
`filetto` a `banda`, tutti sul confine `0,2 corpi` scelto a mano; Fab ha corpo che oscilla
fra 9 e 10 punti e le cose vicine a un confine arbitrario migrano appena il denominatore si
muove. Conferma diretta del rilievo Chat B sui confini: la struttura grossa della mappa è
robusta, i suoi bordi non sono difendibili come numeri, solo come descrizione di zone.

A cosa serve, misurato invece che supposto
(`scripts/inspect_page_local_lines_vs_tables.py`, 40 pagine per manuale, seed 20260803).
Prima misura: la quota di linee e bande che cade per almeno metà della propria area dentro
un `table_candidate` della stessa pagina — Fab 738/982 (75%),
DrW 92/151 (61%), DrM 31/53 (58%), DB 12/16 (75%).
Letta da sola sembrava dire che le linee confermano le tabelle. **Non lo dice.**
Il controllo di permutazione (ogni linea ricollocata a caso sulla stessa
pagina, venti ripetizioni, stesso calcolo) mostra che l'atteso per caso è alto: Fab 50%,
DrM 49%, DB 46%, DrW 33%. L'arricchimento reale è quindi Fab 1,5×, DrW 2,0×, DrM 1,4×,
e nessuno raggiunge il 3× registrato come soglia prima dell'esecuzione. Quattro manuali
sono addirittura sotto 1, e Wil sta a 0,2× — le sue linee cadono dentro le tabelle MENO
del caso, essendo bordi e cornici sistematicamente dove le tabelle non sono. Il censimento
completo di DB (126 pagine, nessun campionamento) corregge il suo dato da 75% con 2,7× su
16 linee a 60% con 1,3× su 120: l'aneddoto era rumore. **L'affermazione che le linee
corroborino le tabelle è ritirata**; resta un arricchimento debole ma reale, dell'ordine
di 1,5× su 982 linee, che è troppo poco per fondarci una regola di Resolution.

Avvertenza generale, che è la cosa più utile emersa da questa misura e vale oltre questo
giro: l'atteso per caso è così alto perché i `table_candidate` sono enormi, coprendo da un
terzo a due terzi dell'area delle pagine dove compaiono. **Qualunque misura di
contenimento geometrico contro `table_candidate` è quindi quasi priva di informazione se
non accompagnata dal tasso di base.** Vale anche per `§8.2.2`, la relazione
`layout.table` × IVF/EV lasciata aperta da Milestone 34, che è esattamente una misura di
contenimento contro quelle stesse candidate. Il repository conteneva già l'avvertimento,
nella docstring di `scan_table_candidate_visual_area_coverage.py` ("a tiny box fully inside
a huge table candidate gives overlap_ratio near 1.0"), e Chat A ci è cascata lo stesso: il
rilievo è arrivato dalla revisione Chat B.

Quello che questa misura NON tocca: la capacità del criterio di forma di identificare le
linee, che poggia sulla mappa tipografica su 16 manuali e sulle 48 celle di provino a
campionamento casuale (DrW e Kul, nessun falso positivo osservato). Il tasso di base
riguarda l'uso delle linee a valle, non il loro riconoscimento. Controllo negativo su Kul
invariato: 1252 linee, zero `table_candidate` su 40 pagine — il fondo rigato non è
struttura di tabella, e per quel manuale il controllo di permutazione non ha nulla contro
cui girare.

Verifica visiva con provino a contatto e campionamento casuale su DrW e Kul, 48 celle:
tutto arredamento, nessun contenuto. Filetti sotto i titoli, righe di guida dell'indice,
campi da compilare della scheda, barre di margine, fondo rigato.
`scripts/render_image_asset_contact_sheet.py` è stato corretto: ordinava per frequenza e
mostrava quindi solo arredamento per costruzione, difetto trovato dalla revisione Chat B e
non da Chat A. L'ispezione precedente su Fab, Vil e Wil era limitata ai 24 digest più
frequenti per manuale e non misurava la precisione della regione ma solo quella dei suoi
elementi più frequenti; una previsione di Chat A su Wil era risultata sbagliata e corretta
dal provino (l'asset 38×16 px non erano i numeri dei passaggi ma il bordo della cornice).

Limiti dichiarati. Dal 2% al 22% delle pagine non ha un corpo stimabile (meno di 20
primitive testuali) e lì il criterio non si applica: su DB sono 124 immagini, circa il 12%
delle sue occorrenze. La corroborazione al 58-75% include gli indici, che pdfplumber con
la strategia `text_lines` legge legittimamente come tabelle: quanto pesino non è stato
separato. Le regioni "bollino" e "sottile" restano miste e la forma lì non decide: gli
angoli di cornice di Wil hanno la stessa firma di un'icona di contenuto. Il rilevatore di
valli è stato cambiato dopo il fallimento del primo, quindi quel passaggio è post-hoc e
vale una tacca meno di uno pre-registrato. Le pagine con `rotation != 0` o
`mediabox != cropbox` erano escluse senza contatore dalle prime due diagnostiche: la
misura successiva le ha contate e sono **zero** su tutti e sedici i manuali. Anomalia
annotata e non indagata: su SV il producer `table_candidate` ha scartato due candidate con
bbox fuori dai limiti di pagina (`y0 = -7,01` su pagina alta 652).

La revisione Chat B aveva dato verdetto **non ratificare, non aprire milestone**, con tre
misure richieste: la prima è stata eseguita e ha falsificato la formulazione in pixel; le
altre due (provino stratificato, aspetto intrinseco contro aspetto di collocazione)
decadono con essa e restano da rifare se la formulazione tipografica verrà proposta.
Vincolo architetturale emerso dalla stessa revisione e tuttora valido: una regola di forma
in Resolution dovrebbe girare **dopo** le regole relazionali, non prima, perché i bordi
che classificherebbe come arredamento sono anche l'evidenza geometrica su cui devono
lavorare `§8.2.2` e il contenimento `interior_visual_frame ⊃ embedded_visual`. Nessuna
milestone è aperta, nessuna soglia è ratificata, nessun producer o contratto è stato
modificato.

Script: `scripts/inspect_document_image_asset_inventory.py`,
`scripts/inspect_image_shape_axis.py`, `scripts/inspect_aspect_density_valley.py`,
`scripts/inspect_image_typographic_shape.py`,
`scripts/inspect_page_local_lines_vs_tables.py`,
`scripts/render_image_asset_contact_sheet.py`.

Falsi negativi, misurati (`scripts/render_image_asset_contact_sheet.py`, ora capace di
filtrare sullo spessore relativo e non solo sui pixel, campionamento casuale con seed).
Il criterio sbaglia **solo per difetto e solo su arredamento**: in 72 celle ispezionate su
tre manuali non è comparso un solo contenuto catturato, mentre molto arredamento sfugge.
La causa è la richiesta di aspetto ≥8, che lascia passare le cose sottili ma corte.

Su Fab la regione "bollino" (38 asset) contiene due popolazioni distinte: le icone dei tipi
di danno e degli oggetti, `13×12` fino a `16×16` px, 1,06–1,44 corpi, 21-38 occorrenze
ciascuna — contenuto, correttamente risparmiato; e granelli degeneri, `1×1` px a 0,11 corpi
con 60 occorrenze, `4×2` px a 0,22 con 40 — arredamento, non catturato. La regione
"sottile" (351 asset) è quasi tutta a 0,22 corpi: schegge di bordo di cella con aspetto fra
2 e 8, arredamento, non catturato. Un caso isolato e notevole: `83×12` px, 1,20 corpi, è la
frase "I confini sono un inganno della mente" composta **come immagine**, cioè testo che
diventa asset. Su Wil il complemento (108 asset) è interamente arredamento: angoli e
segmenti delle cornici, 0,33–1,26 corpi.

La correzione ovvia — rilassare l'aspetto tenendo un limite di spessore — funziona dentro
Fab, dove l'arredamento sfuggito sta a 0,11–0,35 corpi e il contenuto a 1,06–1,44, due
popolazioni nettamente separate. **Non funziona fra manuali**: su Wil l'arredamento sfuggito
sta a 0,33–1,26 corpi, cioè esattamente dove su Fab sta il contenuto. Un limite tarato su
Fab cancellerebbe le icone dei tipi di danno se applicato a Wil. Settima occorrenza dello
stesso schema: separa dentro un manuale, non fra manuali.

Bilancio del criterio di forma, completo su entrambi i lati: precisione alta (72 celle
casuali su tre manuali, nessun contenuto catturato); copertura parziale e non quantificata
globalmente (su Fab sfuggono almeno 389 asset fra bollino e sottile, su Wil 108, quasi tutti
arredamento); modo di fallire conservativo, cioè quello giusto, perché lascia rumore invece
di cancellare contenuto; non estendibile con una soglia unica. Le tre misure chieste dalla
revisione Chat B sono state eseguite tutte: la prima ha falsificato l'asse in pixel, la
seconda ha ritirato la corroborazione delle tabelle, la terza è questa.

Contenimento `interior_visual_frame ⊃ embedded_visual` — ritirato su criterio pre-registrato.
La sola relazione che `State.md` indicava come "da guardare per prima" è stata sottoposta al
controllo di permutazione che le due misure precedenti non avevano, con criterio di
falsificazione registrato per iscritto prima dell'esecuzione (`Prereg_ContenimentoIVF_EV_v1.md`,
non nel repo, stessa prassi di Milestone 33/34/35): ritiro se l'arricchimento è < 3× **su Fab**,
cioè sul manuale da cui l'affermazione è nata. Misura su tutti e sette i manuali del campione
casuale già registrato (280 pagine, 40 per manuale, seed 20260802), con
`scripts/measure_cross_producer_candidate_coverage.py` esteso di un controllo di permutazione
opt-in (`--permutations`, default 0: l'output preesistente resta identico byte per byte,
verificato). Due nulli: A ricolloca ogni candidate irrisolta a caso sulla pagina preservando
larghezza e altezza, B preserva `y0`/`y1` e randomizza solo `x`; le candidate degli altri
producer restano immobili e `resolve_page_candidates` non viene mai rieseguito sulla geometria
permutata. Zero candidate non ricollocabili su sette manuali.

Fab sta a **1,94×** (nullo A) e **1,24×** (nullo B): sotto la barra su entrambi, quindi la
ritrattazione non dipende da quale nullo si creda. Gli altri: DB 2,63×/1,43× (756 irrisolte),
Dag 3,21×/1,65× (90), Vil 7,06×/1,14× (52), Apo e Kul osservato 0,0%, Lan escluso per n<50 e
comunque a 0,0% osservato contro 13,0% atteso per caso. I conteggi di irrisolte per manuale
coincidono esattamente con quelli già registrati sopra, quindi la misura originale è
riproducibile: è la sua interpretazione a cadere, non il suo dato.

Due cose che il criterio non chiedeva e che pesano più del suo esito. La prima: **il 40,6% di
Fab non era una statistica di popolazione ma due pagine.** p.317 (248 candidate coperte) e p.354
(247) valgono 495 delle 549 totali, il 90%; solo 13 pagine su 40 hanno una singola candidate
coperta; IC95 bootstrap per pagina 5,5%–62,7%. Vil è peggio: il suo 11,5% e il suo 7,06% vengono
da una pagina sola (p.123, 6 su 6). Terza occorrenza dello stesso errore dopo il campione
ordinato per frequenza e dopo il 75% di DB sgonfiato a 60% dal censimento completo. La seconda:
**la direzione della debolezza del nullo, dichiarata ignota in pre-registrazione, ora è
misurata.** Il nullo B dà sistematicamente un tasso permutato più alto del nullo A su tutti i
manuali: IVF ed EV si concentrano nelle stesse fasce verticali, quindi il nullo uniforme
sottostima il caso e ogni arricchimento calcolato su di esso è gonfiato. Il numero difendibile è
quello del nullo B, e lì il massimo su sette manuali è 1,65×.

Segnale opposto, coerente con Wil a 0,2× nella misura linee/tabelle: su Lan le irrisolte reali
cadono dentro i riquadri IVF allo 0,0% contro un atteso per caso del 13,0%. L'arredamento sta
sistematicamente dove le cornici non sono.

Nota di metodo, la più riutilizzabile di questo giro: il criterio pre-registrato vincolava
**Fab**, non "due manuali qualsiasi". Una lettura post-hoc degli stessi identici dati avrebbe
dichiarato l'esito positivo, su Dag (3,21×) e Vil (7,06×), entrambi sopra 3× e sopra le soglie
di n e di tasso osservato. Pre-registrare non basta: il criterio deve vincolare il caso da cui
l'affermazione è nata, altrimenti si sposta la domanda invece di rispondere.

Nessuna milestone si apre, nessuna soglia è ratificata, nessun producer o contratto è
modificato. Ottava caduta consecutiva, e in una variante più stretta delle precedenti: non
separa fra manuali, e su Fab non separa nemmeno fra pagine — separa due pagine dalle altre
trentotto.

## Milestone 36 — fetta verticale end-to-end su una pagina — Fase A completata, Fase B non eseguita

Design in `Proposta_Milestone36_FettaVerticale_v1..v4.md` (non nel repo, stessa prassi di
Milestone 33/34/35). Due giri di revisione Chat B **disgiunti** — metodologico prima,
architetturale poi, con letture separate: formato nuovo, adottato dopo che un giro unico è
costato ~54.000 token in ingresso e che i contributi decisivi di Chat B, storicamente, sono
quasi tutti metodologici e non richiedono il repository.

Obiettivo: il percorso più sottile da un PDF a un frammento markdown con note che
referenziano immagini estratte su disco, attraverso i contratti già esistenti. Prima volta in
35 milestone che la pipeline nuova produce un output leggibile da un essere umano.

`scripts/prototype_vertical_slice_page.py` compone capture → normalize → i cinque producer →
co-reference (Milestone 13-19) → `resolve_page_candidates`, ed emette `page.md`,
`assets_index.csv`, `review.md` e i file asset. Nessun producer nuovo, nessun contratto,
nessun wiring nel job; la pipeline legacy non è importata né invocata.

Due invarianti **auto-verificati a ogni esecuzione**, con uscita `4` su fallimento:
conservazione del contenuto testuale come multiset di caratteri non-spazio (cieco all'ordine
di proposito, perché `page_analysis_model.py` nega esplicitamente il reading order alle
righe 189-190, 192-193, 195-196), e integrità dei riferimenti. Il criterio di uscita è
eseguibile dall'artefatto, non valutato a occhio da chi legge l'output.

Esecuzione reale su DB.pdf p.99: 30 occorrenze, 25 asset distinti, 6 note nel corpo, 24 voci
in revisione, 1230 caratteri non-spazio conservati, rapporto note/parole 0,027.

**Risultato principale, che riordina le priorità: il reading order richiede il producer
`column_band`.** Il testo emesso con ordinamento geometrico puro (`y0`, poi `x0`) concatena
riga per riga le due colonne del corpo, ed è illeggibile. La regola editoriale reale —
colonna sinistra fino a un'interruzione, poi destra, poi di nuovo sinistra riprendendo sotto
l'interruzione, con l'incolonnamento che cambia alle interruzioni — presuppone esattamente la
segmentazione in bande a conteggio di colonne stabile costruita da Milestone 32 e il
contratto deciso da Milestone 33 (`proposed_structural_kind="layout.column_band"` più misura
satellite). Quel producer non esiste, e Milestone 33 ha lasciato quattro punti bloccanti. La
proposta di Milestone 36 classificava `column_band` come "fuori dalla catena": l'artefatto
reale dice che è la prima cosa di cui la catena ha bisogno. È il motivo per cui la fetta è
stata costruita invece di continuare a decidere sulla carta, e ha risposto al primo run.

**JPEG 2000: la transcodifica a PNG o WebP è indispensabile.** `extract_image(xref)`
restituisce lo stream come è memorizzato nel PDF, senza transcodifica: DB.pdf archivia le sue
immagini in JPEG 2000, quindi gli asset estratti per xref escono in `.jpx`. Le immagini non
sono destinate alla lettura sul dispositivo — vanno in una cartella a parte e sono solo
referenziate dal markdown — ma il `.jpx` non è apribile dai visualizzatori di immagini
correnti su Windows e Linux, quindi la cartella risulterebbe inutilizzabile per lo scopo per
cui esiste. Requisito registrato, non opzionale: gli asset raster vanno transcodificati in
PNG o WebP. Non deciso qui quale dei due, né dove avvenga la conversione.

**Correzione a un resoconto di implementazione**, registrata perché il numero era già
circolato: gli asset di DB p.99 sono **13 estratti via `xref` e 12 via `rasterized_clip`**,
non 12 e 13 come riportato in prima battuta. Nessuna contraddizione con le 13 occorrenze a
`xref == 0`: occorrenze e identità sono entità distinte, le 17 occorrenze risolvibili
collassano in 13 asset e le 13 inline in 12.

Il fallback `rasterized_clip` è una proprietà dei PDF e non un difetto del nostro lookup:
verificato che `get_images(full=True)` restituisce 17 voci su 13 xref distinti, cioè non
trova un solo xref in più di quelli che `get_image_info(hashes=True, xrefs=True)` già
risolve — le restanti sono immagini inline, che non esistono come risorsa. Confronto poi
chiuso anche sugli insiemi: `solo in get_images` e `solo in get_image_info` entrambi vuoti.
Le immagini inline non estraibili sono tutte piccole (≤580×176 px intrinseci, per lo più
304×80 e 336×52: etichette e bandelle), mentre le illustrazioni grandi
(1244×1616, 845×1155, 509×809) passano correttamente per xref.
La rasterizzazione a 72 dpi del ritaglio degrada quindi elementi minori, non l'arte.
Quando `extraction_method = rasterized_clip`, i byte su disco **non**
corrispondono al `digest` sotto cui sono indicizzati: la sostituzione è registrata in
`assets_index.csv`, mai silenziosa.

**Buco nella regola di processo, non violazione.** `AGENTS.MD` §Aggiornamento documenti
impone di committare lo script che produce un numero citato, e lo script c'è. Ma
`scripts/inspect_document_image_asset_inventory.py` accetta `--pdf` come **singolo file per
invocazione** e anche l'intervallo di pagine è runtime (`--first-page`, `--last-page`), con
`--json-output` opzionale e non committato: lo scope della misura «zero mancanti su 27.437
occorrenze» su 16 manuali è il risultato di sedici o più invocazioni di cui non resta
traccia. La regola copre l'**esistenza** dello script, non la **tracciabilità delle
invocazioni**. Nessuna decisione presa qui su come chiuderlo.

Fase B (esecuzione sulle 280 pagine del campione, tassonomia dei fallimenti, distribuzione
del rapporto note/parole) **non è stata eseguita**: è un passo separato, previsto dalla
proposta e non ancora fatto. Restano fuori scope: producer nuovi, contratti, wiring nel job,
modifiche ai renderer, IR 2, regole di Resolution. L'emettitore diagnostico **non è** il
punto di partenza del renderer IR-first: una sua eventuale promozione è una decisione da
prendere esplicitamente, e nulla in questa milestone la costituisce.

Appunto per una futura passata di raffinamento (non aperta, non numerata): le schede statistiche mostro nel bestiario (es. DB.pdf, GUERRIERO/ARCIERE/CAMPIONE, riquadro a colonne non allineate) non sono table_candidate (nessuna griglia regolare, verificato per ispezione visiva) né riconducibili a un riquadro puramente visivo (embedded_visual/interior_visual_frame): contengono testo strutturato a campi etichetta:valore da preservare, reso oggi con sfondo decorativo che andrebbe rimosso in resa, mantenendo la struttura leggibile. Nessuna decisione presa: possibile candidato per un futuro structural_kind dedicato o per un trattamento di rendering separato dalla classificazione geometrica. Tocca il quarto punto bloccante di Milestone 33 (structural_kind unico vs. distinzione corpo/struttura interna).

<!-- FINE DI State.md — se non leggi questa riga, la tua copia è troncata: fermati e dillo -->
