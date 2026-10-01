# Consultazioni di ManReader prima di cambiare gli script

Una voce per modifica: problema, dove si è cercato, che cosa c'era, che cosa se n'è fatto.

## 28 set 2026: parole spezzate con l'enfasi in mezzo (`**Vile**- **born**`, `*Ambienta zione*`)
- Cercato: `sillabazion|soft hyphen|trattino morbido|dehyphen` in tutti i `.py`/`.md` di ManReader.
- Trovato: `epub_builder._dehyphenate`: unisce `x- y` solo con minuscole ai due lati, senza vocabolario e
  senza enfasi. `State.md` dice che la resa delle parole "appartiene al vero producer di markdown, che non
  esiste".
- Esito: niente da riprendere, la regola della bozza (`vocab_join`) ne è già un sovrainsieme. Estesa a
  lineetta tra enfasi e a spazio con un pezzo raro. Misura v9: Vileborn identiche 88 → 93, Candela e Draw
  Steel invariati.

## 28 set 2026: paragrafi dal rientro di prima riga
- Consultati: `Criterio_ParagrafoDaRiga_v1`, `Criterio_RotturaParagrafo_v2` / `ir2_builder.breaks_paragraph`.
- Esito: la regola del blocco (rompere al cambio di blocco salvo minuscola nel font del corpo) provata e
  tolta (peggiorava); il rientro misurato sui tre manuali (Candela 1/431, Vileborn 24/363, Draw Steel
  0/2996) non è uno stile di questi manuali, la regola resta spenta. Nessun guadagno.

## 28 set 2026: intestazione e didascalia delle tabelle
- Consultati: `Criterio_TabellaNormale_v1.md`, `scripts/prototype_table_columns_and_rows.py`
  (worktree `table-region-producer-005fb8`): `repair_region_y` (intestazione e ultima riga fuori dalla
  regione), `build_rows_from_spine`, `bounds_from_gutters`.
- Esito: adattata l'idea di `repair_region_y` (le intestazioni sopra la regione, una per colonna, si
  riprendono); non ripresi `spine` e `gutters` perché la diagnosi su Vileborn non trova errori di righe o
  colonne dopo la riparazione dell'intestazione (forma uguale 30 → 34 su 49 pagine con tabelle).
  Aggiunte: intestazione vuota quando la prima riga non si distingue (grassetto o maiuscolo), didascalia
  breve sopra la tabella → `####`. Misura v10c: Vileborn ≥0,99 178 → 188, identiche 93 invariate,
  <0,95 35 → 37 (due mappe con tabella falsa preesistente), Candela e Draw Steel invariati.

## Prima di questo registro (sessioni precedenti)
- Marcatori `h` di Vileborn: ManReader li risolveva (`Criterio_MarcatoreDaFont_v3`,
  `document_list_policy.py`); riscritti da zero nella bozza senza controllare. È l'errore che ha portato
  a questa regola.

## 28 set 2026: ordine di lettura (colonne laterali lette prima del testo, Vil pp. 19, 43, 111, 195)
- Consultati: `page_analysis_column_band.py` (Milestone 37, wired), `scripts/prototype_vertical_slice_page.py`
  (`_tree_rows_from_contract`), `scripts/compare_reading_order_with_column_bands.py` (`_tree_aware_order`),
  `Criterio_InterruzioneCorridoio_v1` (`--interrupt-corridor`), State.md §column_band.
- Ripreso **senza riscriverlo**: `script/ordine_manreader.py` chiama il producer e l'ordinatore di ManReader.
- Usato così com'è peggiorava molto (Vileborn ≥0,99 188 → 169): legge per colonne le voci a due parti
  (p. 75, limite noto anche in ManReader: `--interrupt-corridor` lascia la pagina identica), le tabelle
  (p. 167) e, fuori dalle bande, ordina per geometria e stacca i pallini d'elenco (p. 15).
- Adattamento: base = ordine della sorgente; ManReader dice dove sono le colonne; una banda si riordina solo
  se nella sorgente le sue colonne sono contigue; una banda intrecciata (tabella) è un blocco che tiene la
  sorgente; a pari altezza prima la riga più a sinistra. Scartato prima: inizi di paragrafo allineati
  (su Vil p. 19 la colonna laterale è sulla stessa griglia della cronologia).
- Misura v11d: Vileborn ≥0,99 188 → 204, <0,95 37 → 16, nessuna pagina peggiorata; Candela e Draw Steel
  senza perdite ≥0,99. Acceso per default (`MANREADER_ORDINE=0` lo spegne).

## 28 set 2026: callout
- Consultato: `markdown_builder._render_callout` (`> [!TIPO] titolo`, `>`, corpo). Ripreso il formato, tipo NOTE.

## 28 set 2026: etichette delle mappe
- Scartata una regola geometrica/di lunghezza (toglieva copertina, p. 60, aperture di capitolo): la mappa la
  riconosce l'agente degli asset (`mappe` in classi_immagini.json), la bozza toglie il testo dentro.
- Coerente con State.md §column_band: "sul testo stampato sopra un'illustrazione l'attraversamento
  geometrico non dice nulla sulla lettura".
