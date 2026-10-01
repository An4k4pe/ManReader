# Istruzioni per le note sulle immagini: Vileborn

Radice: `/home/an4k4pe/Documenti/ManReader_prova/Vileborn/`.

Il manuale (italiano) viene convertito in Markdown; ogni immagine di contenuto è sostituita da una
**nota breve** che dice che cosa mostrava. Tu scrivi le note; uno script le inserirà al posto dei
segnaposto `*[IMMAGINE: percorso]*`.

## Per ogni immagine del tuo lotto (`_lavoro/lotti.json`, chiave `lotti_immagini`, il tuo numero)
1. Guarda il **file** a risoluzione nativa (Read). Guarda anche il render della pagina dove compare
   (`_lavoro/render120/pNNN.png`, NNN dal campo `pagine`) per capire il contesto: di quale origine,
   retaggio, sfida o luogo si parla.
2. Scrivi:
   - `tipo`: `Illustrazione`, `Mappa`, `Documento`, `Simbolo` (emblemi, icone, stemmi) o
     `Oggetto` (oggetti illustrati delle origini: anelli, monete, strumenti).
   - `nota`: italiano, 4-15 parole, concreta: chi o che cosa si vede, più la tecnica se è
     distintiva. Niente interpretazioni. Puoi nominare il soggetto se la pagina lo dice
     (es. "la Camminaspiriti, donna dai capelli ricci avvolta in veli viola").
   - `trascrizione`: solo se l'immagine contiene **testo di contenuto** (scritte, etichette di mappa,
     parole decorative come "CADAVERI AMBULANTI CHE PUZZANO DI MORTE"). Trascrivi esattamente;
     `[illeggibile]` dove non leggi, **mai** completare per congettura, soprattutto nomi propri.
     Alfabeti inventati: `[iscrizione in alfabeto inventato]`. Altrimenti `null`.
   - `dubbi`: stringa, o `null`.
3. Un'immagine che ti sembra **arredo** (sfondo, fregio, macchia, pezzo tagliato) invece che
   contenuto: nota comunque, e scrivilo in `dubbi`.

## Uscita
`_lavoro/note/lotto_<n>.json`: un oggetto `{ "percorso": {"tipo":…, "nota":…, "trascrizione":…, "dubbi":…}, … }`
con i percorsi esattamente come nel lotto. Salvalo man mano (riscrivi il file dopo ogni
immagine), così un'interruzione non fa perdere il lavoro. Script temporanei solo in
`_lavoro/agenti/immagini_<n>/`. In fondo alla risposta: quante note, quante trascrizioni,
quanti dubbi.
