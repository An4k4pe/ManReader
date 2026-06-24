# pdf_to_epub v1.1 — Convertitore PDF→EPUB per manuali GDR

Converte PDF di manuali GDR in EPUB leggibile e annotabile su qualsiasi
e-reader. Estrae separatamente tutto il materiale grafico (immagini raster,
illustrazioni vettoriali, tabelle) con descrizioni AI opzionali, e lascia
nell'EPUB un riferimento testuale al posto di ogni elemento.

---

## Struttura dei file del progetto

```
pdf_to_epub/
├── main.py          ← CLI; orchestrazione dell'intero flusso
├── config.py        ← dataclass con tutti i parametri di configurazione
├── extractor.py     ← estrazione testo / immagini raster / vettoriali / tabelle;
│                      clustering path vettoriali; filtro ripetizioni testo; lettura TOC
├── deduplicator.py  ← rilevamento asset grafici ripetuti (sfondi, ribbon, watermark);
│                      modalità interattiva e automatica
├── describer.py     ← descrizioni AI via Ollama locale (immagini e tabelle)
├── epub_builder.py  ← assemblaggio EPUB; rilevamento capitoli; rendering HTML
└── requirements.txt
```

---

## Struttura output

```
output/
├── NomeManuale.epub                     ← carica sull'e-reader
└── NomeManuale_extracted/
    ├── images/
    │   ├── NomeManuale_p5_img1.png      ← immagine raster (formato originale)
    │   ├── NomeManuale_p5_img1.txt      ← descrizione AI (se abilitata)
    │   └── ...
    ├── vectors/
    │   ├── NomeManuale_p8_vec1.svg      ← illustrazione vettoriale
    │   ├── NomeManuale_p8_vec1.txt      ← descrizione AI
    │   └── ...
    ├── tables/
    │   ├── NomeManuale_p12_tbl1.csv     ← tabella in CSV
    │   ├── NomeManuale_p12_tbl1.txt     ← descrizione AI
    │   └── ...
    └── backgrounds/
        ├── NomeManuale_p1_img1.png      ← sfondo/ribbon/watermark (una copia)
        └── ...                             non citato nell'EPUB
```

Nell'EPUB ogni immagine, vettoriale e tabella è sostituita da un blocco
di riferimento con il tipo, il path del file estratto e la descrizione AI.
Le tabelle vengono anche renderizzate inline come HTML `<table>`.
Gli asset marcati come "sfondo" non compaiono affatto nell'EPUB.

---

## Installazione (CachyOS / Arch con Fish shell)

```fish
python -m venv venv
source venv/bin/activate.fish
pip install -r requirements.txt
```

Per rientrare nelle sessioni successive:

```fish
cd /percorso/progetto && source venv/bin/activate.fish
```

### Backend locale Ollama

Per usare le descrizioni AI, avvia Ollama localmente e installa il modello configurato.

```fish
ollama serve
ollama pull gemma4:12b
```

---

## Workflow consigliato

```fish
# 1. Test rapido su 20 pagine, senza AI
python main.py manuale.pdf --columns 2 --pages 1-20 --no-ai

# Verifica in Calibre:
#   - testo nell'ordine giusto? (se no: prova --column-split 0.48)
#   - capitoli rilevati? (il programma stampa "TOC trovata" o "euristica font")
#   - intestazioni/piè di pagina rimossi?
#   - vettoriali estratti correttamente?

# 2. Conversione completa con AI
python main.py manuale.pdf --columns 2 --title "Nome Manuale" --author "Autore"
```

---

## Parametri completi

### Metadati

| Parametro  | Default   | Descrizione      |
| ---------- | --------- | ---------------- |
| `--title`  | nome file | Titolo nell'EPUB |
| `--author` | _(vuoto)_ | Autore           |

### Layout pagina

| Parametro             | Default | Descrizione                                          |
| --------------------- | ------- | ---------------------------------------------------- |
| `--columns`           | `1`     | Colonne: `1` o `2`                                   |
| `--column-split`      | auto    | Divisore colonne 0.0–1.0 (es. `0.5`). Auto se omesso |
| `--heading-threshold` | `1.3`   | Moltiplicatore font per titoli (fallback senza TOC)  |
| `--min-image-size`    | `80`    | Dimensione minima immagini raster in pixel           |

### Funzionalità

| Parametro            | Default    | Descrizione                                                     |
| -------------------- | ---------- | --------------------------------------------------------------- |
| `--no-tables`        | False      | Salta estrazione tabelle                                        |
| `--no-vectors`       | False      | Salta estrazione vettoriali                                     |
| `--no-ai`            | False      | Salta descrizioni AI                                            |
| `--ai-language`      | `italiano` | Lingua descrizioni AI                                           |
| `--no-dedup`         | False      | Disabilita rilevamento asset ripetuti                           |
| `--dedup-threshold`  | `0.15`     | Soglia ripetizione asset: >X% pagine → presentato come ripetuto |
| `--auto-background`  | False      | Salva automaticamente i ripetuti come sfondo (no prompt)        |
| `--no-filter`        | False      | Disabilita rimozione intestazioni/piè/filigrane testuali        |
| `--header-zone`      | `0.08`     | Zona header/footer come frazione altezza pagina                 |
| `--repeat-threshold` | `0.25`     | Soglia ripetizione per rimozione (>X% pagine)                   |
| `--pages`            | tutte      | Sottoinsieme pagine, es. `1-20` o `5`                           |

### Output / API

| Parametro  | Default    | Descrizione        |
| ---------- | ---------- | ------------------ |
| `--output` | `./output` | Cartella di output |

---

## Come funzionano le parti non ovvie

### Estrazione vettoriali

`page.get_drawings()` di PyMuPDF restituisce tutti i path vettoriali della
pagina (curve, rettangoli, linee). Una singola illustrazione può essere
composta da centinaia di path separati. Il programma:

1. Filtra i path irrilevanti: quelli che coprono >70% della larghezza o
   altezza della pagina (bordi, linee di separazione) e quelli con area <4pt².
2. Raggruppa i path rimanenti con un algoritmo union-find: se due bounding
   box espansi di 5pt si sovrappongono, appartengono allo stesso gruppo.
3. Scarta i gruppi con dimensione <50pt in larghezza o altezza.
4. Per ogni gruppo esporta la regione come SVG: crea un documento temporaneo
   di una pagina delle dimensioni della clip, ci mappa il contenuto PDF con
   `show_pdf_page()`, poi chiama `get_svg_image()`. Questo preserva la
   qualità vettoriale senza rasterizzare.

### Rilevamento capitoli

Legge prima l'outline (bookmarks) embedded nel PDF — la stessa struttura
visibile nel pannello segnalibri di Evince. Se presente, usa quei dati
direttamente. Fallback: blocchi con font ≥ 1.6× la mediana del documento.

### Filtro intestazioni e filigrane

Due passate su tutte le pagine. Firma di ogni blocco: `(zona_Y, testo_senza_cifre)`.
Zona header = top 8%, footer = bottom 8%, body = resto. Se la firma supera
la soglia (25% pagine per header/footer, 60% per body) il blocco viene rimosso.
Le cifre sono rimosse per gestire numeri di pagina variabili.

### Ordine di lettura doppia colonna

Cerca il gap orizzontale più ampio nella fascia centrale (25%–75% larghezza)
tra i centri X dei blocchi di testo. Quel gap è il gutter tra le colonne.
Poi ordina: colonna sinistra dall'alto, poi colonna destra dall'alto.

---

## Limitazioni note

**PDF scansionati**: testo non selezionabile → niente estrazione. Usa `ocrmypdf`
prima della conversione.

**Vettoriali decorativi**: separatori, cornici, bullet grafici potrebbero
essere estratti come vettoriali separati. Aumenta `--min-image-size` per
ignorarli (default 50pt; prova 100 o 150 per PDF molto decorati).

**Tabelle con celle unite**: pdfplumber ha difficoltà con merged cells.
Il testo viene comunque estratto, la struttura potrebbe non essere perfetta.

**Titolo capitolo non in cima alla pagina**: il fallback font non lo rileva
se è preceduto da un'immagine a piena larghezza. Con TOC embedded non c'è
questo problema.
