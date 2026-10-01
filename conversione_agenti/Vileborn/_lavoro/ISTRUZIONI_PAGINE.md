# Istruzioni per la revisione delle pagine: Vileborn (manuale base 1.0)

Radice: `/home/an4k4pe/Documenti/ManReader_prova/Vileborn/`. Tutti i percorsi sono relativi a qui.

Scopo: la bozza automatica diventa Markdown semantico, fedele alla pagina. Il manuale è in
**italiano** e il testo resta com'è. Le immagini **non** le descrivi tu: nella bozza ci sono già i
segnaposto `*[IMMAGINE: percorso]*`, e le note le scrive un altro agente.

## Materiale per la pagina N (tre cifre, 001–272, indice del PDF; il numero stampato è N-4)
- `_lavoro/bozza/pNNN.md`: bozza v3. Titoli, paragrafi ricuciti, elenchi (`- `), riquadri
  (`> **TITOLO**` + testo citato) e segnaposto immagine sono già tentati dallo script. È la
  **fonte del testo**.
- `_lavoro/render120/pNNN.png`: la pagina a 120 dpi, guardala con Read. È la **verità** per ordine
  di lettura, struttura, tabelle, livelli dei titoli. Per un dettaglio ritaglia con PIL, oppure
  ri-renderizza con PyMuPDF (`/home/an4k4pe/Documenti/ManReader (Copia)/venv/bin/python`, PDF
  `/home/an4k4pe/Documenti/ManReader (Copia)/Vil.pdf`, `page_index = N-1`).
- `_lavoro/smistamento.json`: perché la pagina è stata segnalata (`righe` = tabelle o griglie,
  `cornice` = riquadro non reso, `didasc` = testo dentro un'immagine, `ordine` = ordine sospetto,
  `frammenti`, `numeri`, `elenco`). Una lista vuota vuol dire che è una **pagina di controllo**:
  rivedila come le altre.

## Che cosa fai
Per ogni pagina del tuo lotto scrivi `_lavoro/finale/pNNN.md`, partendo da una copia della bozza.
Prima riga: `<!-- pdf p. N -->`.

1. **Il testo non si ribatte.** Sposta, unisci, dividi, formatta. Correzioni ammesse, **tutte a log**:
   spazi evidenti dal render, parola spezzata a fine riga ricucita male, un a capo diventato
   cambio di paragrafo. Il testo visibile nel render ma assente dalla bozza lo trascrivi, lo
   marchi con `<!-- da render -->` sulla riga prima e lo registri a log.
2. **Ordine di lettura**: colonne da sinistra a destra, poi dall'alto in basso. I riquadri e le
   colonne laterali ("SCEGLI QUESTA ORIGINE SE") vanno dopo il testo principale che accompagnano,
   mai in mezzo a un paragrafo.
3. **Non spostare testo tra pagine.** Un paragrafo che continua sulla pagina dopo resta spezzato:
   lo ricuce lo script di assemblaggio.
4. **Titoli**: `#` capitolo (coincide con un segnalibro del PDF: la bozza lo mette già), `##`
   sezione, `###` sottosezione, `####` titoletti minori. Controlla sul render la gerarchia reale.
   I numeri messi da soli come titolo ("#### 1") sono numerazioni di voci: uniscili al titolo
   della voce (`#### 1. SPREMERSI LE MENINGI`) o a un elenco numerato.
5. **Tabelle** (i d6, i d12, le tabelle a righe alterne): tabella GFM con intestazione, dalle
   parole della bozza. La didascalia della tabella ("PARTICOLARI FISICI") va come `####` subito
   sopra.
6. **Schede delle sfide** (mostri e avversari, capitolo Sfide): struttura fissa, uguale per tutte:
   ```
   ### NOME - TIPO
   *descrizione in corsivo*
   #### DIFFICOLTÀ
   *Aggiungi questi valori alla difficoltà delle prove.*
   | IMPETO | VOLONTÀ | ASCENDENTE | RAGIONE | PRECISIONE | SOTTERFUGIO |
   |---|---|---|---|---|---|
   | 0 | +1 | ... |
   #### DADO OSCURITÀ
   *Tiralo in ogni prova e racconta il risultato.*
   | D12 | Il poltergeist... |
   |---|---|
   | 8+ | ... |
   #### TRIGGER
   ...
   #### REGOLE SPECIALI
   paragrafi
   ```
   Il pallino di livello in alto a destra (cerchi pieni o vuoti) va come `**Livello:** 3/5` sotto il
   titolo, se si legge.
7. **Riquadri**: `> **TITOLO**` e testo citato; senza titolo, un blockquote semplice. Le citazioni
   in-world (virgolettate con la fonte) vanno come blockquote in corsivo con la fonte.
8. **Segnaposto immagine**: ogni `*[IMMAGINE: …]*` resta **esattamente una volta**. Puoi spostarlo
   nel punto giusto del flusso, **non** scriverci una nota. Se nel render vedi un'immagine di
   contenuto senza segnaposto, segnalalo a log e basta.
9. **Testo dentro le immagini** (scritte decorative, etichette): non è compito tuo. Se la bozza lo
   contiene come testo (`didasc`), lascialo dov'è e dillo a log.

## Log
`_lavoro/log/<lotto>.md`: una riga per ogni intervento diverso da riordino e formattazione
(`- p. N: che cosa — perché`). Per ogni **pagina di controllo** scrivi anche una riga
`- p. N (controllo): nessuna correzione` oppure l'elenco di cosa hai dovuto correggere.
In fondo i conteggi: pagine, tabelle, schede, testo preso dal render. Onestà: niente verifiche
dichiarate che non hai fatto.

## Lavoro
- Scrivi solo in `_lavoro/finale/` (le tue pagine), `_lavoro/log/` e nella tua cartella di lavoro
  `_lavoro/agenti/<lotto>/` (script temporanei **solo lì**: altri agenti lavorano in parallelo).
- Scrivi ogni pagina appena finita, così un'interruzione non fa perdere il lavoro fatto.

## Decisioni prese dopo il primo giro (valgono per tutte le pagine)
- **Bozza di partenza: `_lavoro/bozza2/pNNN.md`** (versione corretta). Il `finale/pNNN.md` di queste
  pagine è oggi una copia di bozza2: sovrascrivilo.
- Titoli senza cornice nel render sono titoli (`##`/`###`), **non** riquadri. Riquadro solo con cornice
  o fondo visibile.
- Etichette sopra il titolo (ORIGINE, RETAGGIO OSCURO, PERSONAGGI, CAMPAGNE…): riga in grassetto.
- Pagine delle Origini: `### QUANDO CREI IL TUO VILEBORN` con `#### APPROCCI`, `#### PERSONALITÀ`,
  `#### ADDESTRAMENTO` (come pp. 38, 40); capacità come `#### N. NOME`; colonna "SCEGLI QUESTA ORIGINE
  SE" dopo il testo, come riquadro.
- Doni: `#### N. NOME` seguito dai due paragrafi (effetto, "Tuttavia…").
- Dialoghi d'esempio con le icone dei personaggi: **una battuta per riga** (a capo con `\` o paragrafi
  separati), non fuse.
- Cronologie: `- **ANNO.** testo`.
- Schede: struttura fissa; riga `**Progressione:** N caselle (trigger alle caselle …)` letta dal render
  e marcata `<!-- da render -->`.
