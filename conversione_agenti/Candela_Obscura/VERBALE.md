# Verbale: conversione di *Candela Obscura — Core Rulebook* in Markdown

- Sorgente: `/home/an4k4pe/Documenti/KDrive/ManualiGdr/Candela Obscura - DP - Core Rulebook (OEF, 2023-11).pdf`
  (211 pagine, 64,4 MB, PDF testuale con albero di struttura).
- Lavoro svolto il 25 e 26 settembre 2026.
- Esecutore: Claude (Opus 5.5), che ha coordinato 12 sotto-agenti dello stesso modello per la revisione a vista.
- Nessun modello locale usato: né Ollama né `describer.py`.

Tutti i percorsi sono relativi a `~/Documenti/ManReader_prova/Candela_Obscura/`.
Tutti i numeri riportati sono stati misurati con i comandi e gli script indicati; nessuno è stimato.

## 1. Consegna

| Voce | Contenuto |
|---|---|
| `Candela_Obscura_Core_Rulebook.md` | file unico: 5816 righe, 85.864 parole (`wc -w`), 512 KB |
| `immagini/` | 162 immagini di contenuto alla risoluzione nativa del PDF, una per xref, nome `pNNN_KK` (pagina PDF, ordine sulla pagina), 141 MB |
| `sfondi_e_ripetuti/` | 114 file di arredo e asset ripetuti, ciascuno una sola volta, con `INDICE.md` (e `INDICE.json`): descrizione, xref, pagine in cui compare. 20 MB |
| `script/` | 7 script scritti apposta per questa conversione, più `classi_immagini.json` |
| `_lavoro/` | materiale intermedio: bozze, render, pagine riviste, log degli agenti, misure, confronti. 588 MB, eliminabile |

Composizione di `sfondi_e_ripetuti/`:

| Sottocartella | File | Contenuto |
|---|---|---|
| `sfondi/` | 34 | carte e texture sotto il testo |
| `ripetuti/` | 2 | pergamena di pagina e scheda del personaggio ripetuta |
| `decorazioni/` | 25 | sigilli e scarabocchi a penna ai margini, filetti, logotipo |
| `ombre/` | 53 | maschere d'ombra delle illustrazioni |

## 2. Script usati

Gli script del repository ManReader **non** sono stati usati: né `extractor.py` né `deduplicator.py`, né la pipeline IR, né `describer.py`. Del repository ho usato soltanto l'ambiente Python (`ManReader (Copia)/venv`, PyMuPDF 1.28.0, Pillow). Le memorie del progetto hanno però guidato alcune scelte:
- "Il clip non è l'asset": le immagini si estraggono dagli stream, non fotografando la pagina.
- "Punto elenco specifico del manuale": il glifo "7" riconosciuto come punto elenco.
- "Non si cancella, si tagga": l'arredo è archiviato, non buttato.
- "Numeri solo se misurati".

Script scritti apposta, tutti in `script/`:

| Script | Che cosa fa |
|---|---|
| `01_estrai_immagini_raw.py` | Estrae ogni immagine con xref una volta sola. Stream originale se non ha maschera (JPEG non ricompressi); PNG RGBA con la soft mask applicata se ce l'ha; PNG dal pixmap se MuPDF non restituisce lo stream. Estrae anche le immagini inline (xref 0). Scrive l'inventario delle occorrenze con bbox e SHA-1 dei pixel. |
| `02_bozza_testo.py` | Bozza Markdown pagina per pagina dal livello testo (`rawdict`): ruoli dal font, spazi ricostruiti dalle posizioni dei caratteri, a capo dei composti con trattino ricuciti. |
| `03_smista_immagini.py` | Copia le immagini nelle cartelle finali secondo `classi_immagini.json`, deduplica e scrive gli indici. |
| `04_verifica_copertura.py` | Misura di conservazione del testo tra bozza e pagine riviste. |
| `05_alt_text_editore.py` | Estrae dall'albero di struttura i 176 alt-text `/Figure` dell'editore, con la pagina. |
| `06_assembla.py` | Assembla le pagine nel file unico, aggiusta la gerarchia dei titoli, scrive `INDICE.md`, controlla i riferimenti alle immagini. |
| `07_confronto_alt.py` | Affianca le note scritte a vista e gli alt-text dell'editore. |

## 3. Procedimento, nell'ordine in cui è stato eseguito

### 3.1 Ricognizione del PDF
Con PyMuPDF ho letto metadati, segnalibri (4 livelli, completi), immagini per pagina e statistiche dei font. Ho renderizzato tutte le pagine a 90 dpi e ho guardato due mosaici di 4 pagine ciascuno (pp. 8, 13, 14, 26 e 31, 55, 73, 101).

Che cosa ho trovato:
- **Pagine e numerazione:** pagina 499×734 pt; il numero stampato è l'indice PDF meno 6, verificato: indice 8 → pagina 2, indice 13 → pagina 7.
- **Immagini:** 228 immagini con xref distinte. Una sola (xref 308, la pergamena) è usata 212 volte.
- **Ruoli dei font:**

| Font | Ruolo |
|---|---|
| Quelity-Bold 30 | titolo di capitolo |
| Quelity-Regular 16 | sezione |
| MrsEavesOT-Bold 13/14 | sottosezione |
| MrsEavesOT-Bold 12 | titolo di riquadro |
| Quelity-Bold 10 ruotato | testatina verticale |
| Quelity-Bold 14 in basso | numero di pagina |
| Dontheus, AntiquarianScribe, BakaToo, FilmotypeLaCrosse, Quentin, P22Cezanne, IM Fell, Vaderlands | calligrafici (note in-world) |
| JMHTypewriter | dattiloscritto |
| BodoniOrnamentsITCTT | "7" (167 volte) è il punto elenco del manuale; "=" (4 volte) il punto elenco di secondo livello |

- **Alt-text dell'editore:** l'editore ha incorporato alt-text in due modi:
  - nell'albero di struttura: 176 elementi `/Figure` con `/Alt`;
  - come span di testo di corpo enorme (322–571 pt) e larghezza nulla. Vedi il §3.3 per il difetto che ne è derivato.

### 3.2 Estrazione e classificazione delle immagini
1. `01_estrai_immagini_raw.py`: 228 xref distinti, 503 occorrenze, 53 immagini inline.
2. Ho guardato 7 fogli provini numerati (`_lavoro/sheet_0..5.png`, `inline_sheet.png`) e un controllo a 300 px di 16 casi dubbi (`check1.png`). Le 53 inline sono tutte maschere in scala di grigi delle ombre portate sotto le illustrazioni: arredo.
3. Ho classificato a mano (`script/classi_immagini.json`):

| Classe | Elementi | Che cosa sono |
|---|---|---|
| sfondi | 39 xref | pergamena, texture bianche 1920×1280, fogli strappati sotto il testo, listelli di carta ai margini della piega, velatura di glifi di p. 200 |
| decorazioni | 25 xref | sigilli e scarabocchi a penna di 16–100 px, filetti, schizzi d'inchiostro, logotipo "CANDELA OBSCURA" |
| contenuto | tutto il resto | |

4. Ricerca dei doppioni:
   - hash SHA-1 dei pixel: le texture bianche 3370, 4078, 6024 e 6151 sono identiche;
   - hash medio 16×16, poi differenza media dei pixel dopo il ridimensionamento. 308 e 386 sono identiche (differenza 0,0). 1085 e 1403 sono la stessa scheda del personaggio a due scale (differenza 2,4/255): unico asset di contenuto ripetuto, salvato una volta come `ripetuti/ripetuto_01.png` (la versione più grande). I fogli strappati simili fra loro (differenza 1,9–3,3) sono ritagli diversi della stessa carta: li ho tenuti tutti tra gli sfondi.
5. `03_smista_immagini.py` ha prodotto 162 immagini di contenuto e 114 file in `sfondi_e_ripetuti/`.

**Qualità:** nessuna immagine è ricampionata o ricompressa. I JPEG sono gli stream originali. Le immagini con trasparenza sono PNG RGBA senza perdita. Diversi schizzi a matita (per esempio `p137_01.png`) hanno sotto la trasparenza colori residui scuri: su fondo bianco coincidono con la pagina stampata (verificato affiancando file, file su bianco e render: `_lavoro/cmp137.png`), ma in un visualizzatore con fondo scuro appaiono neri o viola. Non li ho appiattiti su bianco, per non perdere l'alfa. Se serve, si fa con una riga di Pillow.

### 3.3 Bozza del testo
`02_bozza_testo.py` scrive `_lavoro/bozza/pNNN.md` (211 file). La prima versione aveva due difetti, corretti durante il lavoro:
- **Spazi mancanti** dopo le virgolette chiuse ("“fiction-first”TTRPG"). Misurato sui caratteri, lo spazio di VendettaOT vale circa 0,175 del corpo; la soglia di stacco è passata da 0,22 a 0,1 del corpo prima della revisione.
- **Alt-text e numeri di pagina filtrati male.** Il filtro guardava solo il primo span della riga. Alle pp. 27, 28, 29, 79, 116, 124 e 195 l'alt-text stava in mezzo a una riga di testo normale ed è finito nella bozza; alle pp. 116 e 124 anche il numero di pagina ("murders.110"). L'hanno scoperto e segnalato gli agenti, che l'hanno tolto dalle pagine finali. Ho corretto il filtro span per span e rigenerato la bozza come `_lavoro/bozza_v2/`, che differisce da `bozza/` solo in quelle 7 pagine (verificato con `cmp`) più i punti elenco del punto seguente.
- **Punti elenco:** dopo la revisione ho fatto emettere i glifi di BodoniOrnaments come `•` (171 occorrenze, contate con grep).

### 3.4 Revisione a vista, pagina per pagina (sotto-agenti)
- **Istruzioni:** ho scritto le regole comuni in `_lavoro/ISTRUZIONI_REVISIONE.md`:
  - il testo viene dalla bozza, non si ribatte;
  - l'ordine di lettura e le tabelle si prendono dal render a 120 dpi (`_lavoro/render120/`);
  - le note immagine si scrivono guardando il file dell'immagine;
  - si trascrive, marcandolo, il testo che sta solo dentro le immagini;
  - ogni intervento va registrato in un log.
- **Prova pilota:** un agente sulle pp. 13–24. Ho controllato l'uscita e ho verificato io, sull'immagine originale, la sua trascrizione dei tre biglietti di p. 13. Con le ambiguità che ha segnalato ho aggiunto a ISTRUZIONI una sezione "Decisioni dopo la prova pilota": riquadri senza titolo, esempi di gioco in corsivo, trascrizione estesa alle parti di scheda, `\` negli a capo, percorsi.
- **Undici agenti in parallelo** su pp. 1–12, 25–44, 45–60, 61–78, 79–96, 97–116, 117–136, 137–156, 157–176, 177–194, 195–211.
  - Quattro (25–44, 97–116, 117–136, 137–156) si sono interrotti per il limite d'uso dell'account. Dopo il ripristino li ho ripresi con il loro contesto e hanno completato l'intervallo. Prima di riprenderli ho controllato le pagine già scritte: residui della bozza, note immagine mancanti, glifi "7".
  - **Incidente:** gli agenti condividevano la cartella scratchpad. Almeno due script temporanei sono stati sovrascritti da un altro agente, e in un caso ne è uscito un `p071.md` vuoto, che l'agente ha rifatto. Chi l'ha notato ha ricontrollato le proprie pagine con un confronto parola per parola. Il controllo globale del §3.5 non trova pagine vuote o estranee.
- **Log:** 12 file in `_lavoro/log/`. Registrano, pagina per pagina, spazi corretti, paragrafi riuniti, testi presi dal render, trascrizioni con il conteggio delle parole e degli `[illeggibile]`, letture incerte e verifiche non fatte.
- **Correzioni mie** dopo la revisione, registrate nei log:
  - p. 14: la trascrizione della scheda ripetuta era anche a p. 8; a p. 14 l'ho sostituita con un rimando;
  - p. 50 e p. 89: due note riscritte (vedi il §3.6).

### 3.5 Verifica della conservazione del testo
- **Criterio, dichiarato prima della misura:** per pagina, copertura ≥ 0,99, cioè la quota delle parole della bozza (multinsieme) ritrovate nel finale. Le parole in più devono cadere dentro note, trascrizioni o tratti `<!-- da render -->`.
- **Due correzioni dello strumento dopo aver visto i dati.** Le dichiaro perché lo strumento è stato modificato dopo la misura:
  1. il "7" di punto elenco contava come parola persa su 20 pagine. Corretto alla fonte (§3.3, `•`);
  2. un marcatore `<!-- da render -->` su riga propria non veniva riconosciuto come valido per il blocco successivo (p. 142).
- **Risultato finale** (`_lavoro/copertura.txt`): parole della bozza 76.016, mancanti nel finale 16, copertura del documento 0,9998. Sei pagine sono sotto soglia, tutte per cause che ho verificato:

| Pagine | Causa |
|---|---|
| 96 / 97 | la linea temporale su doppia pagina è raccolta a p. 96 (97 → 0,000 per costruzione). Parole "mancanti" a p. 96: sillabe separate da un trattino morbido U+00AD ("cir­ cumstances") e "in-18C E" della calligrafia, ricomposte in "circumstances" e "-18 CE" |
| 131 | la calligrafia estratta a pezzi ("ov er", "w ar", "inquir e"), ricomposta |
| 141, 142 | lettere isolate di testo coperto da un foglio sovrapposto, rese `[illeggibile]` |
| 210 | voci dell'indice analitico che completano una sottolista di p. 209, spostate lì |

- **Limite:** la misura conta le parole e non verifica né l'ordine né la punteggiatura. Per l'ordine fanno fede la revisione degli agenti sui render e un mio controllo a campione: p. 105 confrontata col render, identica per ordine, struttura e testo.
- **Altri controlli di `06_assembla.py`:**
  - riferimenti a file inesistenti: 0;
  - immagini di contenuto senza nota: 0;
  - pagine mancanti: 0;
  - alt-text rimasti nel finale: 0 (grep sui 7 incipit noti).

### 3.6 Controllo indipendente delle note immagine
Gli alt-text dell'editore (`_lavoro/alt_editore.json`) non sono stati dati agli agenti: le istruzioni vietavano di leggerli. Li ho messi a confronto dopo, con `07_confronto_alt.py`; il risultato è in `_lavoro/confronto_alt.md`.
- **Criterio, fissato prima di leggere il confronto:**
  - **concorda:** stesso soggetto principale;
  - **discordante:** soggetto sbagliato;
  - **incompleta:** omette un elemento centrale nominato dall'alt-text.
- **Escluse dal conteggio:** le note delle pp. 27, 28, 29, 79, 116, 124 e 195. Gli agenti hanno visto l'alt-text finito nella bozza (§3.3), quindi per quelle il controllo non è indipendente.
- **Esito della mia lettura del confronto, sulle pagine con nota e alt-text:** tutte concordano, tranne 8 che ho segnalato: 3 possibili discordanze (pp. 71, 142, 168) e 5 incomplete (pp. 11, 50, 89, 147, 206). Le ho riguardate io sulle immagini originali (`_lavoro/check_note.png`):
  - **p. 50 — corretta:** la vista dal fondo di una fossa si vede, e la nota non la diceva;
  - **p. 89 — corretta:** l'emblema non ha "anelli su uno stelo";
  - **le altre sei — lasciate:** quello che vedo non smentisce la nota. La differenza è di interpretazione (p. 71: bacio o creatura che emerge dalla bocca) oppure riguarda dettagli che non distinguo (p. 168: le quattro braccia).
  - **p. 206:** l'alt-text parla di "astrolabe"; l'immagine stessa porta la scritta "Syphon 24-A.503", e la nota segue l'immagine.
  - **Non indipendenti:** le due correzioni sono nate dal confronto.

## 4. Convenzioni del file finale
- **Lingua:** testo in inglese come l'originale; note sulle immagini in italiano. I refusi dell'originale sono lasciati ("Lighkeeper", "Vastchasam", "as as").
- **Pagine:** `<!-- pdf p. N -->` segna l'inizio di ogni pagina del PDF.
- **Titoli:**
  - `#` capitolo, `##` sezione, `###` sottosezione, come nella tipografia.
  - In assemblaggio ho abbassato di un livello, **seguendo i segnalibri del PDF**, le sezioni che la tipografia compone come le sezioni ma che i segnalibri mettono al livello 3: 187 titoli. Sono i ruoli (pp. 26–30), le abilità (pp. 33–38), le domande di relazione (pp. 40–43), i 13 quartieri, i 13 siti di Oldfaire, i 9 luoghi e i 4 casi d'esempio.
  - Nei casi d'esempio "EXAMPLE SESSION" è figlio del caso.
- **Riquadri:** `> **TITOLO**` seguito dal testo citato; quelli senza titolo sono blockquote semplici.
- **Esempi di gioco:** paragrafi in corsivo.
- **Note in-world:** `> *[Nota manoscritta]*` e `*[Dattiloscritto]*`.
- **Tabelle:** GFM solo dove la pagina ha una griglia con intestazione: 4 (tre a p. 21, una a p. 45). Le griglie senza intestazione di pp. 196 e 203 sono elenchi.
- **Linea temporale (pp. 96–97):** un solo elenco cronologico a p. 96.
- **Immagini:** `*[Tipo: nota]* (percorso)`. Il file contiene 164 righe di nota:

| Tipo | Note |
|---|---|
| Illustrazione | 106 |
| Documento | 26 |
| Simbolo | 22 |
| Scheda | 8 |
| Mappa | 2 |

  Più 165 link, perché una nota lunga (p. 73) contiene un `[illeggibile]` annidato ed è comunque collegata.
- **Testo dentro le immagini:** `> *[Testo nell'immagine, trascritto a vista]*`. Sono 30 trascrizioni (lettere, giornali, moduli, biglietti, retro di copertina), con 54 `[illeggibile]` in tutto il file, mai completati per congettura. Sono letture a vista di un modello e i log segnano quelle incerte, per esempio "fresh"/"fesh" a p. 13, "Ezra" a p. 2 e "Iomene"/"lomene" a p. 91.
- **Testo preso dal render** perché assente dal livello testo: 6 marcatori `<!-- da render -->`. Tra questi le note manoscritte di p. 118 e p. 142, disegnate come tracciati.
- **Arredo:** una sola nota iniziale per sfondo, cornici, ombre e sigilli; il dettaglio è in `sfondi_e_ripetuti/INDICE.md`.

## 5. Che cosa non è fatto o resta incerto
- **Nessun confronto carattere per carattere** fra testo finale e pagina stampata. La conservazione è verificata solo come insieme di parole (§3.5), più la revisione a vista degli agenti e il mio campione di una pagina.
- **Testo in alfabeto inventato** (Ancient Fairen), a p. 54, 69, 101, 134, 136, 141–142, 156–157, 163 e 200. Non è trascritto: dove è un'immagine è detto nella nota, dove è disegnato sulla pagina c'è solo un commento HTML, invisibile in un EPUB. In particolare le 6 righe di glifi di p. 200 (xref 9151) le ho classificate come sfondo: un agente la considera contenuto in-world, ed è una scelta discutibile.
- **Grafica vettoriale** (non sono immagini): loghi di Darrington Press e Illuminated Worlds a p. 4, tracciato a sei cerchi dell'abilità Lifesaver a p. 36, filetti e cornici. Non è annotata.
- **Testo coperto da fogli sovrapposti** (pp. 13, 141, 142, 148): reso `[illeggibile]` o lasciato troncato come nel livello testo.
- **Gerarchia:** è una scelta difendibile ma non l'unica; il criterio è quello del §4.
- **Tempi:** il lavoro è stato interrotto una volta dal limite d'uso dell'account (quattro agenti fermati e poi ripresi).

## 6. Fase 2 (26 settembre): che cosa ho preso da ManReader

Ho confrontato i miei script con ManReader leggendo il codice del ramo `claude/asset-note-visibility-e14deb` e facendo girare su Candela le sue due pipeline, `main.py` e `main_ir2.py`. `main_ir2.py` si blocca sull'xref 280 (un JPEG CMYK). L'ho fatto girare attraverso un wrapper nello scratchpad, senza modificare il repository: ho aperto un'attività separata per correggerlo. Nei miei script ho portato due principi di ManReader, in `script/v2/`, senza toccare la consegna della fase 1.

**Asset: `misura_asset.py` e `classifica_asset.py`.**
- **Regole di ManReader:** contenuto su più pagine = ricorrente (`document_asset_policy`); lato minore sotto la lettera più piccola stampata = sotto scala (7,2 pt, misurata sul documento).
- **Segnali miei:** listello (rapporto dei lati ≥ 10), segno a margine (lato ≤ 5 volte il corpo), carta (densità di bordi < 0,09 con testo sopra). Tarati guardando Candela.
- **Criterio, fissato prima di applicare le regole:** nessuna immagine annotata come Illustrazione, Mappa, Documento o Scheda finisce in arredo; accordo con la classificazione a vista ≥ 95% sui 228 xref.
- **Risultato:**
  - solo le regole di ManReader: accordo 75,4%, nessun contenuto perso, 56 elementi d'arredo nel corpo;
  - con i miei segnali: accordo 95,6%, 3 contenuti finiti in arredo, di cui 2 gravi (p. 99, busta intestata, Documento; p. 206, piccola ruota blu, Illustrazione). **Criterio non soddisfatto.** Le soglie non sono state ritoccate.

**Testo: `bozza_testo_v2.py`.** Nessun nome di font nel codice. Il corpo, la gabbia del testo, l'arredo di testo (fuori dalla gabbia e ripetuto su più pagine), le famiglie di scrittura a mano (maggioranza delle righe ruotate), il font marcatore di elenco e le fasce dei titoli si misurano sul documento.
- **Misure ottenute:** corpo VendettaOT 12; arredo = testatina ruotata e numero di pagina; 6 famiglie a mano; marcatore BodoniOrnaments; titoli a 30, 16 e 14 pt.
- **Criterio, fissato prima:** titoli della versione rivista ritrovati ≥ 95%, titoli giusti su quelli emessi ≥ 90%, zero arredo di testo rimasto, 171 punti elenco.
- **Risultato:** 98,6%, 94,6%, 0 e 171 (la v1 cablata: 98,4%, 95,0%, 0 e 171). **Criterio soddisfatto.** Differenza con la v1: 182 righe etichettate "manoscritto" invece di 199; il dattiloscritto non viene più riconosciuto.
- **Limite:** misurato su un solo manuale, lo stesso su cui la v1 era stata cablata.

## 7. Fase 3 (26 settembre): efficienza, cioè meno revisione a vista

**Obiettivo:** ridurre le pagine che un agente deve rivedere. Il riferimento sono le pagine rivedute della fase 1 (`_lavoro/finale/`).

**`bozza_testo_v3.py`.** Rispetto alla fase 1:
- paragrafi ricostruiti a livello di riga, attraverso i blocchi PyMuPDF;
- correzioni meccaniche che prima facevano gli agenti: commenti di blocco, lineetta a fine riga, trattino morbido, spazi a larghezza zero, enfasi vuote;
- punto elenco come carattere di controllo: su Candela U+0007 nel corsivo del corpo, oltre al glifo "7" di BodoniOrnaments;
- corretto un errore dell'espressione che unisce le enfasi adiacenti (`** *`), presente anche nella v1;
- riquadri dalle cornici disegnate, con un vincolo: il primo paragrafo è un titolo, oppure tutti i paragrafi stanno in una colonna sola (le fasce di tabella di p. 21 restano escluse).

**`distanza_dal_finale.py`: pagine uguali al finale.** Dal finale si escludono note immagine, trascrizioni e blocchi da render.

| | Bozza della fase 1 | v3 |
|---|---|---|
| Pagine identiche | 94 | 121 |
| Somiglianza ≥ 0,99 | 153 | 168 |
| Somiglianza < 0,95 | 30 | 26 |

**`smistamento.py`: segnali calcolati senza guardare il finale.** Scrittura a mano, testo dentro un'immagine, righe a gruppi separati, cornice non resa, righe che finiscono con un numero, frammenti, ordine, elenco annidato.
- **Criterio, fissato prima:** segnalare tutte le pagine che differiscono dal finale, e non più del 40% delle pagine.
- **Non soddisfacibile:** le pagine che differiscono sono 90, cioè il 43%.
- **Soglia operativa, dichiarata dopo aver visto i dati:** somiglianza < 0,99, cioè 43 pagine.

| Variante dei segnali | Pagine segnalate | Prese (su 43) | Perse |
|---|---|---|---|
| v1 | 82 (39%) | 40 | pp. 26 (0,662), 61 (0,986), 205 (0,987) |
| v2 (*ordine* esteso a ogni salto verso l'alto > 3 corpi, più *elenco annidato*) | 94 (45%) | 42 | p. 205 (0,987) |

Le modifiche della v2 sono state fatte dopo aver visto gli errori della v1. Nessuna delle due varianti soddisfa insieme richiamo completo e tetto del 40%.
