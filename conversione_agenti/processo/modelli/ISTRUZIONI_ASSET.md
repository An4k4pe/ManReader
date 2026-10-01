# Revisione della classificazione delle immagini

Radice del manuale: `{RADICE}`. PDF: `{PDF}`. Python: `{PY}`.

Lo script ha classificato ogni immagine distinta del manuale (per xref) in: `contenuto` (avrà una nota nel
testo), `ricorrente` (stesso contenuto su più pagine: sfondi, cornici, pannelli), `sotto_scala` (più sottile
della lettera più piccola), `carta` (pochi bordi e testo sopra), `segno` (piccolo, lato ≤ 5 corpi),
`listello` (lunghissimo e sottile), `ombra` (immagini inline). Le regole sono state tarate su due manuali e
sbagliano: su Vileborn "carta" prendeva gli oggetti ritagliati su fondo trasparente, e "ricorrente" conteneva
mappe e ritratti ripetuti che sono contenuto.

Materiale: fogli provini `_lavoro/{PROVINI}` (ogni miniatura ha xref e prima pagina), misure in
`_lavoro/v2/misure_asset.json`, classi in `_lavoro/v2/classi_auto.json`, file in `_lavoro/raw/`.

## Che cosa fai
1. Guarda **tutti** i fogli provini. Per i casi dubbi guarda il file e la pagina.
2. Criterio: **se l'immagine sparisse, il lettore perderebbe un'informazione o un'illustrazione?** Sì →
   contenuto. No (sfondo, carta sotto il testo, fregio, ombra, frammento tagliato al bordo, logo editoriale) →
   arredo.
3. Cerca i **doppioni di contenuto** (stessa illustrazione su più pagine, anche con xref diversi): confronta
   con PIL (differenza media dei pixel dopo ridimensionamento) e a vista.
4. Scrivi `script/classi_immagini.json` nel formato:
   ```json
   {"_nota": "...", "sfondo": {"xref": "descrizione breve"}, "decorazione": {"xref": "descrizione"},
    "doppi": [["xref", "xref"], ["xref_ripetuto_da_solo"]], "mappe": ["xref", ...],
    "correzioni": {"a_contenuto": [...], "a_arredo": {...}, "contenuto_ripetuto": [...]}}
   ```
   `sfondo`/`decorazione` = tutto l'arredo con xref (non serve elencare le ombre inline); tutto ciò che non è
   elencato è contenuto. `doppi` = gruppi di contenuto ripetuto (anche gruppi di un elemento per un
   contenuto con lo stesso xref su più pagine: va nella cartella dei ripetuti con la nota).
   `mappe` = le immagini di contenuto che sono **mappe** (anche piante e planimetrie). Il testo stampato
   sopra (nomi di luoghi, etichette) viene tolto dalla bozza insieme alla mappa: controlla sulla pagina
   che dentro il riquadro dell'immagine non ci sia testo che non sia un'etichetta della mappa.
5. Scrivi `arredo.md`: una frase che descrive l'arredo del manuale (sfondi, cornici, fregi) per la nota
   unica in testa al file.

Nella risposta: quante correzioni rispetto alla classificazione automatica, per regola, e i casi incerti.
