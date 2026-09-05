# Esperimenti sul rilevamento delle schede statistiche — esplorativi

**Non e' codice di produzione, non e' cablato, non importa nulla dal repo.**
Nessuna decisione architetturale e' stata presa qui. E' il verbale riproducibile
dei numeri discussi in sessione.

## Ordine di lettura

1. `CRITERIO.md` — scritto **prima** di generare i dati sintetici.
2. `synth.py`, `detect.py` — corpus sintetico e i quattro rilevatori
   pre-registrati (D1-D4).
3. `posthoc.py`, `confound.py`, `nocolon.py` — metodi progettati **dopo** aver
   visto i fallimenti, dichiarati come tali, piu' i due confondenti.
4. `pipeline.py` — il contratto zona -> ruoli -> assemblaggio verbatim ->
   verifica. **Il "modello" e' simulato con dizionari scritti a mano: nessuna
   chiamata a un LLM e' mai stata fatta in questi esperimenti.**
5. `schema.py`, `fit2.py` — induzione della forma dagli scheletri e schema
   usato come classificatore.
6. `CRITERIO_REALE.md` — scritto **prima** di aprire il PDF reale.
7. `real5.py` — la catena su Daggerheart SRD (68 pagine).
   `RISULTATI_DAGGERHEART.txt` e' la sua uscita.

## Esito sul manuale reale

148 schede attese (verita' costruita per via indipendente, ricerca testuale di
`Difficulty:` insensibile a spazi e legature), su 1022 zone candidate:

- 148 riconosciute, 0 rifiutate, 0 falsi positivi;
- due template indotti automaticamente: avversari (n=129, obbligatori
  `ATK, Difficulty, HP, Motives & Tactics, Stress, Thresholds`) e ambienti
  (n=17, obbligatori `Difficulty, Impulses, Potential Adversaries`);
- assegnazione al template: 129 avversari e 19 ambienti, zero incroci;
- il risultato regge togliendo `Difficulty` dallo schema, quindi non dipende
  dalla stringa che definisce anche la verita';
- copertura del testo delle pagine 37-55: 100% dalle zone, 97,3% dalle sole
  zone-scheda.

Nessun LLM, nessun vocabolario fornito, nessun font o etichetta cablati.

## Difetti misurati, non risolti

- **L'ordine di lettura e' un prerequisito, non un dettaglio.** Ordinando per
  `y` poi `x` su pagine a quattro colonne il rilevamento crolla da 148 a 58.
  Le schede si delimitano solo dentro la colonna.
- **Lo stile di corpo e' locale alla regione, non globale**: nel manuale il
  testo principale e' 9pt e le schede 8pt; assumere il corpo globale non
  estraeva un solo campo.
- 161 glifi in area privata (separatori) persi in estrazione sulle pagine
  delle schede: perdita di contenuto reale.
- 640 etichette indotte contengono uno spazio spurio da legatura
  (`Diffi culty`): serve una normalizzazione, e va **dichiarata**, perche'
  l'invariante di conservazione dei caratteri la rileva.
- Gli span adiacenti si concatenano senza spazio (`Action:Mark a Stress`).
