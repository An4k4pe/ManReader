# Note sulle immagini

Radice del manuale: `{RADICE}`. PDF: `{PDF}`. Python: `{PY}`.

Ogni immagine di contenuto è tolta dal testo e sostituita da una **nota breve** che dice che cosa mostrava;
uno script le inserisce al posto dei segnaposto. Le note sono in **italiano**; le trascrizioni nella lingua
dell'immagine.

## Per ogni immagine del lotto
1. Guarda il **file** a risoluzione nativa (Read) e la pagina dove compare (render con PyMuPDF,
   `page_index = pagina-1`, nella tua cartella di lavoro) per il contesto.
2. Scrivi:
   - `tipo`: `Illustrazione`, `Mappa`, `Documento`, `Simbolo` (emblemi, icone, stemmi), `Oggetto`, `Scheda`.
   - `nota`: 4-15 parole, concreta: chi o che cosa si vede, più la tecnica se distintiva. Niente
     interpretazioni; il nome del soggetto solo se la pagina lo dice.
   - `trascrizione`: solo se l'immagine contiene **testo di contenuto** (lettere, giornali, moduli, etichette di
     mappa, scritte decorative con parole). Esattamente com'è; `[illeggibile]` dove non leggi, **mai**
     completare per congettura, soprattutto nomi propri e cifre. Alfabeti inventati:
     `[iscrizione in alfabeto inventato]`. Altrimenti `null`.
   - `dubbi`: stringa o `null` (anche: "mi sembra arredo, non contenuto").
3. Salva dopo ogni immagine `_lavoro/note/{LOTTO}.json`: `{"percorso": {"tipo","nota","trascrizione","dubbi"}}`
   con i percorsi esattamente come nell'elenco. Script temporanei in `_lavoro/agenti/{LOTTO}/`.

Nella risposta finale: note, trascrizioni, dubbi (quanti), e i casi da guardare.
