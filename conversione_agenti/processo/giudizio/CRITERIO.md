# Giudizio a vista della misura della bozza (28 set 2026), scritto prima di estrarre il campione

Scopo: capire se il punteggio di valuta_bozza.py (somiglianza alle pagine rivedute dagli agenti) dice
qualcosa sulla qualità vera della bozza, e se le modifiche alle tabelle di oggi sono miglioramenti veri.

Campione, Vileborn, seed 20260928, punteggi nascosti a chi giudica:
- A: 6 pagine migliorate dalla modifica tabelle (vecchia e nuova bozza affiancate)
- B: le 4 pagine peggiorate (idem)
- C: 10 pagine a caso con punteggio >= 0,99
- D: 5 pagine a caso con punteggio < 0,95
Ordine delle pagine mescolato.

Voto per pagina: bozza corretta / difetti minori / sbagliata; per A e B anche: nuova meglio / uguale / peggio.

Criteri fissati ora:
- la misura è utile se in C almeno 8 su 10 sono "corretta" o "difetti minori" e in D almeno 4 su 5 "sbagliata";
  altrimenti il punteggio non va più usato come verdetto e il banco di prova va rifatto;
- la modifica tabelle è un miglioramento se in A almeno 5 su 6 "nuova meglio" e in B nessun "peggio"
  che tu giudichi grave.

## Esito (voti in voti.json, punteggi in chiave.json)
- C (>= 0,99): 10/10 corrette o difetti minori (6 corrette, 4 minori). D (< 0,95): 5/5 sbagliate.
  La misura regge agli estremi: criterio superato.
- A: 6/6 "nuova meglio". B: 4/4 "nuova meglio", mentre la misura le dava peggiorate: nella fascia
  0,93-0,99 la direzione del punteggio non è affidabile (il riveduto di riferimento ha i suoi errori:
  etichette di mappa come titoli, pp. 2 e 158). Modifica tabelle: miglioramento, criterio superato.
- Limite: chi giudicava vedeva quale bozza era la nuova (colonne etichettate), non era cieco.
- Difetto dominante nelle pagine sbagliate: ordine di lettura (pp. 19, 43, 111, 195; 8 da vedere).
- Preferenze dell'utente: riquadri come callout, non come blockquote; meno `##` nelle schede; tenere i
  livelli di rientro degli elenchi; le etichette delle mappe vanno tolte insieme alla mappa (corretto dall utente dopo il giudizio).
