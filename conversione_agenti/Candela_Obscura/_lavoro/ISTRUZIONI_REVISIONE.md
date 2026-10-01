# Istruzioni per la revisione a vista: Candela Obscura, Core Rulebook

Radice: `/home/an4k4pe/Documenti/ManReader_prova/Candela_Obscura/`. Tutti i
percorsi qui sotto sono relativi a questa radice.

Scopo: trasformare la bozza estratta automaticamente in Markdown semantico e
ben formattato. Il contenuto va preservato. Le immagini sono sostituite da note
brevi che dicono che cosa rappresentano. Il manuale è in **inglese**: il testo
resta in inglese. Le **note sulle immagini sono in italiano**.

## Materiale per ogni pagina N (N = indice PDF a tre cifre, 001–211)

- `_lavoro/bozza/pNNN.md`: testo estratto dal livello testo del PDF. È la
  **fonte del testo**. I commenti `<!-- blocco [x0,y0,x1,y1] -->` danno la
  posizione in punti (pagina 499×734). L'ordine dei blocchi è quello del
  content stream e **spesso non è l'ordine di lettura**.
  Etichette della bozza: `> [manoscritto]` (font calligrafici),
  `> [dattiloscritto]` (font da macchina da scrivere). Righe `> **...**` con il
  testo seguente citato = riquadro con titolo.
  Già tolti: testatina verticale, numero di pagina, alt-text incorporato.
- `_lavoro/render120/pNNN.png`: render della pagina a 120 dpi. È la **verità
  sull'ordine di lettura, la struttura e le tabelle**. Per leggere un dettaglio,
  ritaglia/ingrandisci con Python (PIL) oppure ri-renderizza la zona con PyMuPDF
  (`/home/an4k4pe/Documenti/ManReader (Copia)/venv/bin/python`, PDF:
  `/home/an4k4pe/Documenti/KDrive/ManualiGdr/Candela Obscura - DP - Core Rulebook (OEF, 2023-11).pdf`,
  `page_index = N-1`).
- `_lavoro/immagini_per_pagina.json`: chiave = N (stringa). Elenca le immagini
  di **contenuto** della pagina con il `file` finale (già copiato, risoluzione
  nativa), il `bbox` in punti e `ripetuto`. Sfondi, carte sotto il testo,
  ombre e scarabocchi a margine **non** ci sono: sono già archiviati in
  `sfondi_e_ripetuti/` e **non vanno annotati nel testo**.
  Un bbox con x negativo o oltre 499 indica un'immagine che attraversa la
  doppia pagina: annotala solo sulla pagina dove è elencata.
- `_lavoro/segnalibri.json`: segnalibri del PDF `[livello, titolo, pagina]`,
  utili per capire la gerarchia.

## Che cosa scrivere

Per ogni pagina del tuo intervallo scrivi `_lavoro/finale/pNNN.md`. La prima
riga è `<!-- pdf p. N -->`, poi il contenuto della pagina in ordine di lettura.
Pagine senza contenuto: solo il commento, più le note immagine se ci sono.

### Testo
1. **Il testo viene dalla bozza, non si ribatte.** Puoi spostarlo, unirlo o
   dividerlo e applicarvi la formattazione. Non riscriverlo, non riassumerlo,
   non tradurlo, non "correggerlo" per stile.
   Correzioni ammesse, **ognuna da registrare nel log**:
   - uno spazio mancante o in più evidente dal render;
   - un a capo che la bozza ha trasformato in cambio di paragrafo (succede
     quando il testo gira attorno a un'immagine).
2. Se una porzione di testo visibile nel render **manca nella bozza**:
   - se è testo dentro un'immagine, vedi sotto (trascrizione);
   - altrimenti trascrivila dal render, marcala con `<!-- da render -->` e
     registrala nel log.
3. Ordine di lettura: colonne da sinistra a destra, dall'alto in basso. I
   riquadri (sidebar) vanno dove cadono nel flusso, tra paragrafi, **mai a metà
   di un paragrafo**.
4. **Paragrafo spezzato tra due pagine**: si completa sulla pagina dove
   **comincia**, prendendo il seguito dall'inizio di `bozza/p(N+1).md`. Il
   frammento iniziale di una pagina che continua la precedente va quindi
   omesso. Vale anche al confine del tuo intervallo: all'ultima pagina guarda
   la bozza della successiva; alla prima, se comincia con un seguito, omettilo.
   Metti un commento `<!-- continua da p. N-1 -->` al posto del frammento
   omesso.

### Gerarchia
- `#` titolo di capitolo (grande, maiuscolo, Quelity 30pt, es. "THE CORE
  SYSTEM"; un titolo su due righe si unisce).
- `##` sezione (Quelity 16pt maiuscoletto, es. "DRIVES & ACTIONS").
- `###` sottosezione (MrsEaves bold 13–14pt, es. "Stakes").
- `####` per titoletti minori interni ai riquadri o alle schede, se servono.
- Testo in maiuscolo nei titoli: lascialo com'è.

### Riquadri, note in-world, tabelle
- **Riquadro con titolo** (cornice ornata):
  ```
  > **ON COLLABORATION AT THE TABLE**
  >
  > *testo…*
  ```
- **Note manoscritte in-world** (scritte a mano ai margini o sulle pagine):
  ```
  > *[Nota manoscritta]* testo…
  ```
  Per le parti dattiloscritte usa `*[Dattiloscritto]*`. Scritte a mano che
  sono solo **didascalie di uno schizzo** (es. "Minecart" accanto a un
  disegno) vanno dentro la nota dell'immagine, non come testo.
- **Tabelle**: tabella GFM quando la pagina mostra una griglia vera (righe ×
  colonne con intestazione). Ricomponila dal render usando le parole della
  bozza. Se una tabella attraversa due pagine, fai una tabella sola sulla
  pagina dove comincia.
- **Liste**: numerate o puntate come nella pagina.
- Una **linea temporale** o un altro impaginato grafico con date va reso come
  elenco ordinato cronologicamente: `- **-1605 CE** — testo`.
- Parti di scheda personaggio mostrate come testo (azioni, drive, abilità):
  struttura con titoletti e liste, non tabelle forzate.

### Immagini (solo quelle in `immagini_per_pagina.json`)
Nel punto del flusso dove sta l'immagine (o alla fine del paragrafo più
vicino) una riga a sé:

```
*[Illustrazione: castello gotico su un'altura, schizzo a matita]* ([immagini/p010_01.png](immagini/p010_01.png))
```

- Per scrivere la nota **guarda il file dell'immagine** (`file`), non solo il
  render. È una nota **breve**, 4–15 parole, in italiano, concreta: chi e che
  cosa, più la tecnica se è distintiva (acquerello, schizzo a matita, incisione,
  mappa). Esempi di tono: "guerriero in armatura", "panorama alieno",
  "investigatrice con lanterna in un vicolo, acquerello". Niente
  interpretazioni.
- Tipi: `Illustrazione`, `Mappa`, `Documento`, `Scheda` (estratti della scheda
  del personaggio), `Simbolo` (emblemi e sigilli delle organizzazioni, cerchi
  arcani).
- Se l'immagine contiene **didascalie a mano** nella bozza (etichette dello
  schizzo), aggiungile nella nota: `… (didascalie: "Minecart", "path for foot traffic")`.
- **Documenti con testo leggibile dentro l'immagine** (lettere, giornali,
  moduli, biglietti, volantini) che **non** è nella bozza: dopo la nota
  trascrivi il testo leggendolo dal file immagine a risoluzione nativa, così:
  ```
  *[Documento: ritaglio di giornale "Otherwhere Attack Imminent"]* ([immagini/p090_02.png](immagini/p090_02.png))
  > *[Testo nell'immagine, trascritto a vista]*
  > testo…
  ```
  Parole illeggibili: `[illeggibile]`. Non completare per congettura.
  Scritte in alfabeto inventato (glifi): non trascriverle, dillo nella nota
  ("iscrizione in alfabeto inventato").
- Una stessa immagine elencata più volte sulla stessa pagina: una nota sola.
- Immagine `ripetuto: true`: la nota la metti comunque, con il percorso
  indicato.

## Log obbligatorio
Scrivi `_lavoro/log/pAAA-pBBB.md` (il tuo intervallo), una riga per ogni
intervento diverso dal semplice riordino dei blocchi e dalla formattazione:
spazi corretti, paragrafi uniti o divisi, testo preso dal render, trascrizioni
da immagine (quante parole e quante `[illeggibile]`), dubbi irrisolti. Formato:
`- p. N: <che cosa> — <perché>`. In fondo metti un conteggio: pagine fatte,
note immagine scritte, tabelle, trascrizioni.
Onestà: se non hai controllato qualcosa, scrivilo. Non dichiarare verifiche
che non hai fatto.

## Non fare
- Non modificare file fuori da `_lavoro/finale/` e `_lavoro/log/`.
- Non usare modelli locali (Ollama, describer.py): le note le scrivi tu
  guardando le immagini.
- Non leggere gli alt-text incorporati nel PDF (albero di struttura /Alt):
  servono dopo come controllo indipendente delle tue note.

## Decisioni aggiunte dopo la prova pilota (pp. 13–24)
- **Riquadro senza titolo** (cornice semplice attorno a un elenco o a un
  gruppo di paragrafi): blockquote senza la riga del titolo.
- **Esempi di gioco** (paragrafi in corsivo rientrati, "Kat decides…"):
  paragrafi normali tutti in corsivo, **non** blockquote.
- **Trascrizione dalle immagini**: vale per ogni immagine che porta **testo di
  contenuto** leggibile e assente dalla bozza (documenti, parti di scheda,
  volantini, cartelli), non solo per le lettere. Non trascrivere un frammento
  ritagliato di un modulo già trascritto: dillo nella nota.
- **A capo dentro lettere e testi manoscritti trascritti**: `\` a fine riga.
- **Percorsi delle immagini**: esattamente il campo `file`, relativo alla
  radice (il file finale starà nella radice).
- Titoletti che fanno da didascalia a una tabella ("Example Body Scars"):
  `###`.
- Barrato visibile nel render: `~~parola~~`, e va nel log.
