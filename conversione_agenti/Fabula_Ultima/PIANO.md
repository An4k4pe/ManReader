# Prova completa: Fabula Ultima (Fab.pdf, 362 pp.) — piano e criterio, scritti il 1 ott 2026 prima dei dati

## Domanda
Mettendo insieme tutto ciò che c'è (bozza del processo, ManReader IR 2, strumenti esterni, agenti) esce un
manuale Markdown + asset leggibile? Se no, l'utente valuta di passare a una wiki di LLM per regole e concetti.

## Criterio di successo (scelto dall'utente)
25 pagine estratte a caso (seme fissato e scritto qui prima dell'estrazione), affiancate al render del PDF.
L'utente le giudica: buona / difetti minori / sbagliata, e segnala contenuto perso o inventato.
**Riuscita se almeno 20 su 25 sono buone o con difetti minori e nessuna ha contenuto perso o inventato.**
Budget: nessun tetto; i token degli agenti si registrano comunque nel verbale.

## Fonti per ogni pagina, date all'agente di revisione
1. bozza del processo (`bozza_testo_v3.py` con profilo glifi): fonte del testo, come da RUNBOOK;
2. ManReader IR 2 (`main_ir2.py`, ramo asset-note-visibility-e14deb): tabelle e note d'asset;
3. Docling (CPU) e PaddleOCR-VL 1.6 (GPU): seconde opinioni su ordine di lettura e struttura;
4. il render della pagina, che resta la verità.
Regola invariata: il testo viene dallo strato di testo del PDF (bozza); le altre fonti suggeriscono ordine,
tabelle e struttura, non riscrivono parole. Parole presenti solo in una fonte esterna: si accettano solo se
visibili nel render, con `<!-- da render -->`.

## Misure secondarie (non decidono la riuscita)
- disaccordo bozza/strumento come smistamento: soglia 0,9 fissata ora, si misura contro le correzioni degli
  agenti (pagina corretta in modo sostanziale = rapporto bozza/finale < 0,95);
- token e tempo per fase.
