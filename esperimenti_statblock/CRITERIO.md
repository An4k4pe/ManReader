# Criterio, scritto prima di generare e prima di guardare qualunque numero

## Cosa questo test PUO' fare e cosa NON puo' fare

I manuali reali non sono in questo ambiente. Le pagine sono sintetiche e le
genero io. Quindi:

- **NON puo' confermare** che un metodo funzioni. Un generatore scritto da chi
  progetta il metodo incorpora le assunzioni del metodo: un esito positivo qui
  non e' evidenza, e' tautologia.
- **PUO' falsificare**: se un metodo sbaglia gia' su dati puliti costruiti in
  suo favore, e' morto al livello del meccanismo e non serve un PDF vero.
- **PUO' scoprire il costo**: cosa il metodo richiede davvero dai dati, e quali
  casi lo rompono.

Nessun numero prodotto qui va citato come accuratezza.

## Le pagine, decise adesso (avverse di proposito)

1. `bestiary` — 4 schede: NOME (12pt bold) + 5-7 righe `Etichetta: valore`
   (etichetta bold 9, valore tondo 9) + 0-2 righe di prosa.
2. `bestiary_var` — stesse schede ma lunghezze molto diverse fra loro.
3. `prose` — NEGATIVO: prosa continua con 3 etichette bold a inizio paragrafo.
4. `rules_list` — NEGATIVO DURO: 8 voci `Termine: definizione`, bold + tondo,
   strutturalmente identiche alle righe di una scheda ma senza riga-nome.
5. `headings` — NEGATIVO DURO: titoli di sezione **nello stesso stile del nome
   scheda** (12pt bold) seguiti da prosa.

Le pagine 4 e 5 esistono perche' rompano i metodi, non perche' li confermino.

## Criteri di falsificazione, per metodo

- **F1** — su `bestiary` e `bestiary_var`, se il metodo non recupera i confini
  esatti (riga di inizio e riga di fine di ogni scheda), il metodo e' morto al
  meccanismo.
- **F2** — su `prose`, `rules_list`, `headings`, se il metodo propone anche una
  sola scheda, il segnale non discrimina e il metodo ha bisogno di un'altra
  gamba. E' il criterio che conta di piu': i falsi positivi qui sono il modo in
  cui questi metodi falliscono sul serio.
- **F3** — scoperta di costo, non pass/fail: come va definita la chiave di
  stile di una riga che contiene span di stili diversi (nome + valore sulla
  stessa riga). Se una chiave per riga non e' definibile, l'inquadramento
  «stringa di simboli» e' sbagliato e va sostituito.

## Vincolo di onesta'

I detector si scrivono **prima** di eseguire e **non si ritoccano** dopo aver
visto i risultati. Se un detector va corretto, la correzione si dichiara come
tale e il risultato precedente resta a verbale.
