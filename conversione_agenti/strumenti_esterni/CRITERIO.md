# Criterio: Marker e Docling contro la bozza di ManReader_prova (scritto il 30 set 2026, prima dei dati)

**Scopo.** Capire se Marker (datalab) o Docling (IBM) possono sostituire o alimentare la bozza
(`processo/script/bozza_testo_v3.py`) nel produrre Markdown semantico + asset referenziati.

**Pagine.** Le pagine rivedute del banco di prova (`_lavoro/finale/pNNN.md`), 10 per manuale
(Candela, Vileborn, Draw Steel): 5 "difficili" (bozza v15_titoli1 < 0,95) e 5 "facili" (bozza >= 0,99),
estratte con seme fisso 0 prima di lanciare gli strumenti.

**Misure.**
- A (forma + contenuto): la stessa `norm` + `SequenceMatcher.ratio` di `valuta_bozza.py`; ai file degli
  strumenti si tolgono solo i link a immagini.
- B (solo contenuto): sequenza di parole, tolta ogni marcatura Markdown/HTML, ratio sulle parole.
  Serve a separare "testo sbagliato" da "convenzione di formato diversa" (callout, livelli dei titoli).

**Accettazione.**
- Uno strumento è candidato **a base** se, in almeno 2 manuali su 3, la mediana B sulle pagine difficili
  supera quella della bozza e sulle facili non perde più di 0,01.
- Altrimenti si valuta **per componente** (ordine di lettura, tabelle, asset/immagini, titoli), a vista.
- Il giudizio finale su almeno 3 pagine per strumento è a vista, non dai numeri.
- CPU soltanto (niente carico GPU: vedi hardware instabile).

## Secondo giro (30 set 2026, scritto prima dei dati): modelli visivi in GPU

Stesse 30 pagine, stesse misure A e B, stesso criterio di accettazione. Strumenti: PaddleOCR-VL-1.6 (pipeline
con layout, backend VL su llama.cpp in GPU), MinerU (backend migliore che gira su questa GPU AMD), e se il tempo
regge GLM-OCR / dots.ocr su llama.cpp a pagina intera.
In più, perché qui il testo viene **rigenerato dai pixel**: conto le parole inventate, cioè le parole dell'uscita
assenti sia dal testo del PDF della pagina sia dalla pagina riveduta. Un valore alto esclude lo strumento come
sorgente del testo anche se B è buono; resterebbe utilizzabile al massimo per l'ordine e la struttura.
Sorveglianza: temperatura e carico GPU durante i giri (hardware instabile sotto carico, fix non verificato).
