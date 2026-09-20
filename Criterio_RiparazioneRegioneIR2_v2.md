# Criterio — la riparazione della regione, rimisurata con le schede collegate

Dichiarato il 20 settembre 2026, **prima** della misura. Richiesta dell'utente:
«rimisura la riparazione scollegata».

## 0. Perché si rimisura

`Criterio_RiparazioneRegioneIR2_v1.md` è **caduto sul veto**: cinque regioni
assorbivano un paragrafo. La riparazione è però rimasta collegata, e tutto il
lavoro sulle schede è stato misurato sopra di lei — quindi il commit `b26d245`
la porta dentro con la caduta a verbale.

Due dei cinque casi del veto sono **schede**, e le schede adesso si riconoscono:

| caso del veto v1 | che cos'era | ora |
| --- | --- | --- |
| Dag idx 230 (stampata 229) | tabella **nuova** da tre schede avversario, piè di pagina compreso | la tabella sparisce per le schede |
| Dag idx 359 (stampata 358) | gran parte della scheda del compagno | la tabella si riduce per le schede |
| DB idx 43 (stampata 42) | le righe mancanti del riquadro AZIONI, due colonne di punti elenco | non è una scheda |
| Dag idx 116 (stampata 115) | la colonna destra della prosa esplicativa | non è una scheda |
| Dag idx 311 (stampata 310) | titolo `LA SCHEDA MADRE` e i paragrafi Fase 1 / Fase 2 | non è una scheda |

La domanda è se il veto scatti ancora, e su quante.

## 1. La misura

Stesso codice di `b26d245`, con la sola riga
`region = _repaired_region(seed_region, source_lines, unavailable)` sostituita da
`region = seed_region`.

- **prima** = `output/resa/senza-riparo`, la riparazione scollegata, le schede
  collegate;
- **dopo** = `output/resa/verifica`, cioè lo stato committato (identico byte a
  byte a `output/resa/acapo2`).

DB, Apo e Dag interi, `--tabelle --schede-campi`.

## 2. I veti e il giudizio restano quelli della v1

Copiati alla lettera dal §4 della v1, non riscritti:

- **A. Barra.** Test verdi, Ruff pulito, `check_eb.py` 9 su 10 con la sola Fab
  idx 126.
- **B. Nessuna primitiva esce da una tabella.** Una sola violazione ferma tutto.
- **C. Il giudizio**, sull'immagine della pagina: **meglio** se la tabella ora
  contiene intestazione, ultima riga o fine di riga che la pagina stampa
  **dentro**; **peggio** se contiene testo che la pagina stampa **fuori**, o se
  divide una riga fra tabella e paragrafo; **neutro** il resto.
  **Passa se meglio > peggio.**
  **Veto: nessuna regione assorbe un paragrafo** — due o più righe di prosa di
  seguito.

## 3. La previsione, scritta prima di guardare

**Il veto scatta ancora, su tre regioni invece di cinque.** DB idx 43, Dag idx
116 e Dag idx 311 non sono schede e niente in `b26d245` le tocca: le schede
agiscono solo dove una scheda è riconosciuta, e lì non c'è.

Dag idx 230 non dovrebbe più figurare come caso del veto perché la tabella non
esiste più affatto, né con la riparazione né senza. Dag idx 359 resta dubbio: la
tabella si riduce ma non sparisce, e la riparazione potrebbe ancora allargarla
sulla prosa.

**Se la previsione è giusta, il criterio cade di nuovo** e la conseguenza è
scollegare: un meccanismo che migliora venti tabelle e ne guasta tre assorbendo
paragrafi resta in albero con il suo verbale, non nella pipeline. Il codice non
si cancella, si tagga.

**Se invece il veto non scatta più**, la riparazione passa e resta collegata —
e allora quello che è cambiato non è la riparazione ma il fatto che tre dei
cinque casi non erano difetti suoi.

## 4. Che cosa questa misura NON decide

Non rimisura le venti tabelle migliorate: quelle la v1 le ha già giudicate, e il
criterio passa o cade sul veto, non sul conteggio.
