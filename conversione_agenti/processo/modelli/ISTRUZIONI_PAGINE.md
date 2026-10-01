# Revisione delle pagine

Radice del manuale: `{RADICE}` (percorsi relativi a qui). PDF: `{PDF}`. Python: `{PY}` (PyMuPDF, PIL).

Scopo: la bozza automatica diventa Markdown semantico fedele alla pagina. Il testo resta nella lingua
originale ({LINGUA}). Le immagini **non** le descrivi tu: la bozza ha i segnaposto `*[IMMAGINE: percorso]*`,
le note le scrive un altro agente.

## Materiale per la pagina N (tre cifre, indice del PDF)
- `_lavoro/bozza/pNNN.md`: **fonte del testo**. Paragrafi, titoli, elenchi, tabelle, riquadri e glifi sono già
  tentati dallo script.
- La pagina renderizzata: se `_lavoro/render120/pNNN.png` non c'è, creala con PyMuPDF
  (`fitz.open(PDF)[N-1].get_pixmap(dpi=120).save(...)`) nella tua cartella di lavoro. È la **verità** per
  ordine, struttura, tabelle, livelli dei titoli.
- `_lavoro/smistamento.json`: perché la pagina è segnalata (`righe` tabelle/griglie, `cornice`, `didasc`
  testo in un'immagine, `ordine`, `frammenti`, `numeri`, `elenco`); vuota = pagina di controllo.
- Segnalibri del PDF: `fitz.open(PDF).get_toc()` → `[livello, titolo, pagina]`.

## Regole
1. **Il testo non si ribatte.** Sposta, unisci, dividi, formatta. Correzioni di testo solo se evidenti dal
   render (spazi, parola spezzata a fine riga), **tutte a log**. Testo visibile nel render ma assente dalla
   bozza: trascrivilo, `<!-- da render -->` sulla riga prima, a log. Lo script di validazione confronta
   le parole con la bozza: una parola persa senza motivo fa rifare il lotto.
2. **Ordine di lettura**: colonne da sinistra a destra, poi dall'alto in basso; riquadri e colonne laterali
   dopo il testo che accompagnano, mai a metà paragrafo. Non spostare testo tra pagine (i paragrafi spezzati
   li ricuce l'assemblaggio).
3. **Titoli**: livello dal segnalibro se esiste (livello L → L cancelletti), altrimenti dalla gerarchia
   visibile; niente salti di più di un livello. Etichette sopra un titolo (ORIGINE, CAPITOLO 3…): riga in
   grassetto. Numeri isolati resi come titolo: uniscili al titolo della voce (`#### 1. NOME`).
4. **Tabelle**: GFM per le griglie vere; la bozza le ricompone quando le celle sono allineate: controlla righe,
   colonne e intestazione sul render. Didascalia della tabella in grassetto subito sopra.
5. **Riquadri**: solo con cornice o fondo visibile: `> **TITOLO**` e testo citato (senza titolo: blockquote
   semplice). Un titolo senza cornice è un titolo, non un riquadro. Citazioni in-world: blockquote in corsivo
   con la fonte.
6. **Elenchi**: come nella pagina; voci con etichetta (`**Etichetta:** testo`) una per riga/paragrafo.
   Dialoghi d'esempio: una battuta per riga.
7. **Glifi**: `[glifo:X]` nella bozza è un simbolo del manuale senza resa nel profilo: se il render lo rende
   evidente, sostituiscilo con una resa breve tra parentesi quadre (`[icona: d10]`) e annotalo a log.
8. **Segnaposto immagine**: ognuno resta **esattamente una volta** (la validazione lo controlla); puoi
   spostarlo nel punto giusto, non scriverci note.
9. Schede, blocchi di regole ripetuti (mostri, abilità, incantesimi): struttura **identica** per tutte, come
   da `decisioni.md` se c'è; altrimenti titolo + tabelle per le righe di valori + paragrafi con etichetta.

## Consegna
- `_lavoro/finale/pNNN.md` per ogni pagina del lotto, prima riga `<!-- pdf p. N -->`, scritta appena finita.
- `_lavoro/log/{LOTTO}.md`: per ogni pagina `- p. N: nessuna correzione` oppure l'elenco delle correzioni
  (testo / struttura / estrazione); in fondo i conteggi. Onestà: niente verifiche dichiarate e non fatte.
- Script temporanei solo in `_lavoro/agenti/{LOTTO}/` (altri agenti lavorano in parallelo).
- Nella risposta finale: pagine fatte, correzioni ricorrenti della bozza, scelte di formato da uniformare.
