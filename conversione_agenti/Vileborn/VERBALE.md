# Verbale: conversione di *Vileborn — Manuale base 1.0* in Markdown

- **Sorgente:** `/home/an4k4pe/Documenti/ManReader (Copia)/Vil.pdf` (272 pagine, 102 MB, in italiano, senza alt-text dell'editore).
- **Date:** lavoro svolto tra il 27 e il 28 settembre 2026.
- **Esecutore:** Claude (Opus 5.5), con sotto-agenti dello stesso modello; nessun modello locale.
- **Stessa procedura di Candela Obscura** (`../Candela_Obscura/VERBALE.md`), nella versione ottimizzata della fase 3. È il secondo manuale su cui la misuro.

Tutti i percorsi sono relativi a `~/Documenti/ManReader_prova/Vileborn/`. I numeri sono misurati; il loro comando o script è indicato.

## 1. Consegna

| Voce | Contenuto |
|---|---|
| `Vileborn_Manuale_base.md` | file unico: 7094 righe, 58.598 parole, 376 KB |
| `immagini/` | 78 illustrazioni a risoluzione nativa, una per xref (161 MB) |
| `sfondi_e_ripetuti/` | 161 file ciascuno una volta, con `INDICE.md`: 14 asset di contenuto ripetuti (con nota nel testo), 139 sfondi e fregi, 4 decorazioni, 4 ombre (123 MB) |
| `script/` | script usati; quelli ripresi da Candela sono adattati o estesi (§2) |
| `_lavoro/` | bozze, render, lotti, 19 log degli agenti, note immagine, misure. 478 MB, eliminabile |

**Contenuto del file:**
- 125 note immagine: 85 Illustrazione, 16 Oggetto, 12 Simbolo, 8 Documento, 4 Mappa;
- 13 trascrizioni di testo dentro le immagini;
- 105 tabelle GFM;
- 24 schede delle sfide con struttura fissa;
- 17 tratti presi dal render (`<!-- da render -->`);
- 73 titoli `#`.

## 2. Script

| Script | Origine | Ruolo |
|---|---|---|
| `01_estrai_immagini_raw.py` | Candela | estrazione a risoluzione nativa: maschera applicata, stream originali, immagini inline |
| `misura_asset.py`, `classifica_asset.py` | Candela, fase 2 | ricorrenza e scala (regole di ManReader) più i segnali listello, segno e carta |
| `03_smista_immagini.py` | Candela | cartelle finali, doppioni, indice |
| `bozza_testo_v2.py` | Candela, fase 2, **esteso qui** | ruoli del testo misurati sul documento |
| `bozza_testo_v3.py` | Candela, fase 3, **esteso qui** | montaggio dei paragrafi per riga, correzioni meccaniche, segnaposto immagine |
| `smistamento.py` | Candela, fase 3 | segnali per decidere quali pagine rivedere |
| `04_verifica_copertura.py` | Candela, adattato | conservazione del testo tra bozza e pagine rivedute |
| `assembla_vil.py` | nuovo | note al posto dei segnaposto, paragrafi spezzati tra pagine, file unico, controlli |

Del repository ManReader ho usato solo il `venv`. Le regole di ManReader (ricorrenza, scala del testo) sono state riscritte dentro i miei script, non importate.

## 3. Procedimento

### 3.1 Ricognizione
- **Struttura:** 272 pagine, 101 segnalibri tutti al livello 1. Il numero stampato è l'indice PDF meno 4, verificato sulle pp. 13, 32, 48, 148 e 222.
- **Immagini:** 245 immagini con xref più 7 inline.
- **Tipografia diversa da Candela:**
  - titoli allo stesso corpo del testo (Calluna-Bold 11,6) o più piccoli;
  - titoli spaziati lettera per lettera;
  - interlinea di 1,38 volte il corpo;
  - punto elenco dato dalla "h" del font NelsonOrnaments;
  - tabelle d6 e d12;
  - schede delle sfide.

### 3.2 La bozza non reggeva il secondo manuale: correzioni e verifica su Candela
Le regole nate su Candela hanno fallito su Vileborn in molti punti. Ogni correzione l'ho rimisurata su Candela, confrontando con le sue pagine rivedute. Le due regressioni trovate lungo la strada le ho corrette.

| Difetto su Vileborn | Causa | Correzione (ricavata dal documento) |
|---|---|---|
| righe di un paragrafo mai unite | interlinea fissa 1,3, cablata | interlinea misurata; limite = max(1,3 volte il corpo, 1,15 volte l'interlinea misurata) |
| titoli spaziati ("Q U A N D O") | tracking, con caratteri spazio o con distanze | spazi stretti tolti; le parole separate dagli spazi più larghi |
| titoli a corpo di testo non riconosciuti | le fasce dei titoli guardavano solo la dimensione | famiglie di titolazione: non corpo, righe brevi e isolate |
| "PERSONALITÀ" diventato `#` | confronto con i segnalibri senza pagina | segnalibro valido solo sulla sua pagina (±1), con il suo livello |
| 455 righe `#### h` | pallino di NelsonOrnaments letto come titolo | font i cui span sono quasi sempre un carattere solo = marcatore d'elenco |
| 306 riquadri, in gran parte falsi | regola di Candela "titolo a corpo di testo nello stesso blocco" | vale solo per stili di titolazione rari (≤ 5% delle pagine) |
| 116 titoli fatti solo da un numero | numerazione delle voci | fusi con il titolo che segue |
| sillabazioni ("e- saurimento", "Vi leborn") | a capo con trattino e spazi dentro parola | ricucitura con il vocabolario del documento; il trattino resta solo tra due parole vere |

**Tentativo scartato:** una regola per ricucire i trattini dentro la riga è stata provata e **tolta**. Su Candela fondeva composti inglesi veri ("turn-of-the-century", "detail-oriented").

**Verifica finale su Candela:** 0 pagine cambiate rispetto alla versione precedente della bozza, 168 pagine con somiglianza ≥ 0,99 come prima.

**Risultato su Vileborn, prima e dopo le correzioni:**

| Difetto | Prima | Dopo |
|---|---|---|
| righe `#### h` | 455 | 0 |
| riquadri `> **` | 306 | 43 |
| numeri isolati come titolo | 116 | 0 |
| sillabazioni "x- y" | 29 | 0 |

### 3.3 Immagini
- **Classificazione automatica di partenza** (`classifica_asset.py`):

| Classe | Immagini |
|---|---|
| contenuto | 86 |
| sotto la scala del testo | 73 |
| ricorrente | 51 |
| carta | 21 |
| segno | 10 |
| ombra | 7 |
| listello | 4 |

- **Verifica a vista** su fogli provini per ciascuna classe (`_lavoro/sheet_*.png`, `dubbi.png`). La regola "carta" su Vileborn scambiava per carta anche gli oggetti ritagliati su fondo trasparente: rosario, liuto, falce, fiala, mano, un dipinto. Tutte le correzioni sono elencate in `script/classi_immagini.json`, chiave `correzioni`:
  - 19 immagini riportate a contenuto;
  - 12 portate ad arredo: ombre, frammenti tagliati al bordo, loghi, la striscia 319 uguale alla 2174.
- **Doppioni di contenuto:** 14 gruppi in `ripetuti/`:
  - i 7 personaggi di p. 47 riusati nelle aperture dei Retaggi, accoppiati per differenza minima: 5 coppie tra 0,3 e 2,5/255, 2 coppie a 12 e 18 con ritaglio diverso, uguali a vista;
  - 3 ritratti ripetuti;
  - le 2 mappe dei risguardi e altri 2 ritratti.

  Gli oggetti delle Origini (anello, medaglione, monete, fazzoletto) sono lo stesso oggetto in più pagine, ma con ritagli e scale diversi (differenza 20–40/255). Li ho tenuti come immagini distinte, ciascuna con la sua nota.

### 3.4 Smistamento e campioni di controllo: l'ottimizzazione non ha retto
- **Smistamento:** ha segnalato 150 pagine su 272 (55%).
- **Primo campione di controllo:** 20 pagine non segnalate, seed 11. Criterio: al massimo 2 con correzioni. **Fallito**: secondo i resoconti degli agenti, tutte le pagine di controllo del primo giro hanno avuto correzioni. La causa erano i difetti sistematici della bozza del §3.2.
- **Secondo campione,** sulla bozza corretta: 15 pagine, seed 12. Stesso criterio. **Fallito**: 5 pagine su 15 con somiglianza < 0,99 (pp. 5, 106, 134, 199, 207), 6 identiche. Nessuna correzione riguardava testo mancante: erano dialoghi, blocchi delle Origini, livelli dei titoli, citazioni.
- **Esito:** ho applicato la strada sicura e **tutte** le 272 pagine sono state rivedute dagli agenti.
- **Lotti:**
  - 10 lotti sulle pagine segnalate più il primo campione (170 pagine);
  - 2 agenti per il secondo campione (15 pagine);
  - 5 lotti sulle 87 pagine restanti;
  - 1 agente per uniformare i dialoghi (8 pagine del primo giro);
  - 3 agenti per le 92 note immagine.
- **Separazione dei lavori:** gli agenti delle pagine non scrivono note sulle immagini. La bozza porta i segnaposto `*[IMMAGINE: …]*`, 125 su 125 occorrenze immagine-pagina. Le note vengono dagli agenti delle immagini (`_lavoro/note/lotto_*.json`, 92 su 92) e le inserisce `assembla_vil.py`.
- **Costo:** gli agenti hanno riportato in tutto 2.307.046 token (somma dei dati d'uso delle notifiche):

| Voce | Token |
|---|---|
| lotti del primo giro | 1.050.836 |
| immagini | 496.351 |
| secondo campione | 174.541 |
| pagine restanti | 513.808 |
| uniformazione dei dialoghi | 71.510 |

  Candela, 211 pagine: circa 1,7 milioni.

### 3.5 Uniformazione e assemblaggio
- **Uniformazione fra lotti,** meccanica e senza cambiare parole, registrata in `_lavoro/log/uniformazione_finale.md` e nel log del lotto 9:
  - 17 etichette sopra i titoli portate a grassetto;
  - 3 motti portati alla forma di maggioranza, il grassetto corsivo usato in 29 punti;
  - 10 pagine di doni del primo giro portate a `### DONI` / `#### N. NOME`;
  - p. 67 allineata alle altre aperture dei Retaggi;
  - 10 schede da `**Caselle:**` a `**Progressione:** … caselle (trigger alle caselle …)`.
- **Assemblaggio** (`assembla_vil.py`):
  - note inserite: 125;
  - paragrafi ricuciti tra pagine: 2;
  - segnaposto rimasti: 0; note mancanti: 0; riferimenti a file inesistenti: 0; immagini di contenuto senza nota: 0.

### 3.6 Conservazione del testo
`04_verifica_copertura.py` confronta le pagine rivedute con `bozza2`: copertura sul documento 0,9942, 297 parole "mancanti" su 51.153. Ho controllato l'elenco delle 44 pagine sotto la soglia di 0,99. Le mancanze sono:
- parole ricucite ("esauri"+"mento", "vile"+"born");
- "D 1 2" e "N °" ricomposti in "D12" e "N°";
- lettere spaziate ricomposte (p. 5);
- a p. 11, un blocco di testo che nel PDF è coperto e non si vede, messo dall'agente in un commento HTML.

Non ho trovato testo perso. Le parole in più sono le righe di progressione delle schede, lette dal render e marcate.

## 4. Che cosa resta incerto o non fatto
- **Maiuscoletto:** i termini di gioco in maiuscoletto (pulsione, retaggio oscuro, ferita…) non sono marcati. La bozza non porta questa informazione.
- **Elementi grafici senza nota:** il codice QR di p. 268, i loghi della quarta di copertina, il diagramma vettoriale a semicerchi di p. 96, alcune icone di dialogo in più rispetto ai segnaposto (per esempio pp. 105, 125, 131). Gli agenti le hanno segnalate nei log.
- **Livelli dei titoli:** coerenti dentro ogni capitolo dopo l'uniformazione, ma i segnalibri sono piatti. Alcune scelte restano giudizi degli agenti, per esempio `##` per le sezioni della Storia di Egas che sono anche segnalibri.
- **Righe di progressione delle schede:** lette dal render. Non esistono nel livello testo del PDF.
- **Note immagine senza un secondo parere:** Vileborn non ha alt-text dell'editore, quindi le note non hanno un controllo indipendente. 61 note su 92 portano un dubbio segnalato dall'agente in `_lavoro/note/`: nomi dei soggetti dedotti, immagini fuori pagina, doppie pagine.
- **Nessun confronto carattere per carattere col render:** la verifica è quella del §3.6, più i confronti bozza-finale degli agenti e il mio controllo a campione su p. 32 e p. 222.

## 5. Che cosa insegna questo secondo manuale
1. **Le regole della bozza nate su Candela non erano generali:** almeno sette hanno fallito su Vileborn. Correggerle ricavando le soglie dal documento, e verificando ogni volta Candela, ha tolto il lavoro di massa.
2. **Lo smistamento non ha retto su Vileborn.** Anche con la bozza corretta, un terzo delle pagine di controllo richiedeva correzioni di struttura. Su un manuale nuovo, rivedere tutte le pagine resta necessario, oppure serve una bozza molto più matura.
3. **La separazione tra pagine e immagini ha funzionato:** 92 note su 92, 125 segnaposto su 125, nessun conflitto tra agenti.
