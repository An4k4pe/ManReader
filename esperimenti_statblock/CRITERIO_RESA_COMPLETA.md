# La resa consumando tutti i producer — criterio scritto PRIMA

Il giro precedente ne consumava **uno su sei** (`column_band`) e si vedeva.
Bersaglio: il Markdown.

## La diagnosi da cui parte, misurata prima di scrivere il criterio
Il «testo schiacciato» non e' il renderer: e' l'**ordine di lettura**. Sul
Dragonbane Quickstart, 3.977 primitive su 4.532 (87,8%) cadono dentro una banda;
le altre no, e finiscono ordinate per y, cioe' con le colonne interlacciate riga
per riga. **14 pagine su 47 non producono nessuna banda.** Pagina indice 28 ne
produce 2 e copre 46 primitive su 98: e' la pagina che l'utente ha visto
schiacciata. I «numeri a caso» sono celle di tabella che si infilano nella prosa
per lo stesso motivo.

## Cosa si costruisce
1. **Tutti e sei i producer wired** consumati: `column_band` (ordine),
   `table_candidate` (tabelle), `embedded_visual` e `interior_visual_frame`
   (riquadri), `page_covering_visual` e `page_edge_visual` (sfondi e bordi).
2. **I confini della scheda dal riquadro disegnato**, non dalla pila di testa:
   l'estensione della regione e' l'insieme delle righe dentro il riquadro.
   Il rilevatore dice DOVE ci sono campi, il riquadro dice DOVE FINISCE.
3. **Le tabelle delimitate** come regione propria, verbatim, con la nota.
4. **Le note degli asset**: sfondo di pagina, fasce di bordo e immagini raster
   diventano una nota che dice cosa sostituiscono; le raster con xref
   risolvibile vengono estratte in una cartella e referenziate.
5. **L'ordine di lettura dichiarato**: una pagina con righe fuori dalle bande
   porta una nota che lo dice, col conteggio. Il testo interlacciato non e' un
   errore da nascondere: e' una cosa che la pipeline non sa ancora fare, e la
   regola del progetto e' che non si sbaglia in silenzio.

## Cosa NON si fa
- Nessuna modifica al renderer, ai producer, alle loro soglie.
- Nessuna tabella Markdown vera: servirebbero le celle, e il contratto dice che
  un candidato tabella non produce il CSV definitivo prima di Resolution. La
  tabella esce verbatim e delimitata. **Misuro** se l'estrazione celle di
  pdfplumber sarebbe senza perdita, cosi' il prossimo giro ha il dato.
- Niente nota per ogni singolo cluster vettoriale: su una pagina ce ne sono
  decine, una nota ciascuno sarebbe un muro. Si contano e si riporta il numero.
- Niente wiring, niente Resolution, niente terzo manuale.

## Predizioni registrate
- **S1 — conservazione.** I caratteri non-spazio dei blocchi di CONTENUTO (non
  delle note, che sono aggiunte dichiarate e marcate) restano identici a quelli
  delle primitive. Condizione di accettazione.
- **S2 — i confini dal riquadro.** Sulle 4 pagine di scheda il blocco comincia
  sulla riga del nome: predico **4 su 4** (era 2 su 4 con la pila di testa).
  Su pagina 29 il riquadro copre solo i campi, quindi la tabella degli attacchi
  esce come regione separata subito dopo: e' l'esito atteso, non un fallimento.
- **S3 — la frase spezzata sparisce.** Il taglio a meta' di «Liberarsi richiede
  di superare un tiro / di FOR con un castigo» non deve piu' esserci, perche'
  l'estensione non la decide piu' la testa successiva.
- **S4 — l'onesta' costa.** Le pagine con nota di ordine di lettura saranno
  molte: predico **piu' di 30 su 47**, perche' solo poche pagine hanno tutte le
  righe dentro le bande. Se la nota compare quasi ovunque va detto che il
  problema vero e' li', non nella resa.

## Criterio di accettazione
S1 e' la condizione. S2, S3 e S4 si riportano: dicono quanto la resa e' pronta.
Se S2 fallisce, il riquadro non basta a dare i confini e va detto senza
aggiustare soglie.
