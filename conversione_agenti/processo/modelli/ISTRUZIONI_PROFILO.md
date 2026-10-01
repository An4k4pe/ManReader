# Profilo del manuale: resa dei glifi e decisioni di formato

Radice del manuale: `{RADICE}`. PDF: `{PDF}`. Python: `{PY}`.

I manuali usano font di simboli per punti elenco, icone di gioco e ornamenti. Lo script non può sapere che
cosa significa un glifo; tu sì, guardando gli esempi.

Materiale: `_lavoro/inventario_glifi.json`: per ogni carattere dei font di simboli, dove compare nella riga
(inizio, mezzo, fine, solo), quante volte, e tre esempi con pagina, contesto (il glifo è tra ⟦ ⟧) e bbox.

## Che cosa fai
1. Per ogni glifo guarda gli esempi e, se il senso non è evidente dal contesto, il render della zona
   (PyMuPDF, `get_pixmap(dpi=300, clip=fitz.Rect(bbox allargato))`).
2. Scrivi `profilo.json`:
   ```json
   {"_nota": "come l'hai ricavato", "glifi": {"carattere": "resa"}}
   ```
   Rese: `"•"` punto elenco; `""` ornamento da togliere; un'etichetta in grassetto se l'icona introduce un
   campo (`"**Distance:**"`); una lettera o parola se l'icona la rappresenta (`"M"`, `"WEAK"`). Esempio
   reale (Draw Steel): `o` → `**Distance:**`, `x` → `**Target:**`, `á`/`é`/`í` → `**≤11:**`/`**12–16:**`/`**17+:**`,
   `®` e `£` → ornamenti, `a<w` → `A < WEAK`.
3. Guarda 5-6 pagine rappresentative (capitoli diversi) e scrivi `decisioni.md`: le scelte di formato proprie
   di questo manuale che tutti i revisori devono applicare allo stesso modo (struttura delle schede o dei
   blocchi di regole ripetuti, resa di dialoghi, cronologie, etichette sopra i titoli, livelli dei titoli dove
   i segnalibri non bastano). Breve, a punti, con un esempio per ogni struttura ripetuta.

Nella risposta: glifi mappati, glifi dubbi, e il contenuto di decisioni.md in sintesi.
