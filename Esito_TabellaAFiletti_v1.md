# Esito — una tabella è ciò che i filetti risolvono: **il veto scatta**

Misura di `Criterio_TabellaAFiletti_v1.md`, 25 settembre 2026. Nove manuali resi
con i predefiniti, in `output/resa/filetti/`.

## 1. Il conto

| manuale | tabelle prima → dopo | sparite |
| --- | --- | ---: |
| DB | 70 → 57 | 13 |
| Apo | 16 → 14 | 2 |
| Dag | 60 → 43 | 17 |
| Wil | 107 → 86 | 21 |
| BiD | 53 → 25 | 28 |
| DIE | 138 → **0** | 138 |
| SV | 31 → 11 | 20 |
| Kul | 2 → 0 | 2 |
| Vil | 51 → 30 | 21 |

262 tabelle sparite. Nessuna tabella tenuta cambia.

## 2. Il giudizio, sull'immagine

**Fantasmi, cioè meglio** — la pagina non stampa nessuna tabella:

| pagina | che cos'è |
| --- | --- |
| Dag stampata 107 | due colonne di prosa |
| DB stampata 42 | la scatola AZIONI, un elenco in cornice |
| Dag stampata 14 | le opzioni di classe |
| Dag stampata 310 | prosa e diagrammi |
| Dag stampata 49 | la scheda del compagno |
| Dag stampata 351, 361; DB stampata 123 | **moduli da compilare**: schede personaggio, la scheda madre |
| DIE stampata 23 | una mappa di avanzamento a triangoli |
| Apo stampata 10 | una cronologia: date a sinistra, prosa lunga a destra |

**Grigi** — elenchi di tratti valutati con pallini o triangoli, più scheda che
tabella di dati: BiD stampata 259 (`Benessere`, `Sicurezza`, `Influenza`), SV
stampata 305 (`Ricchezza`, `Crimine/Consorzio`, `Livello di tecnologia`).

**Tabelle vere perse — il veto:**

| pagina | che cosa | perché la strategia a filetti non la vede |
| --- | --- | --- |
| DIE stampata 61 | `POSIZIONI DA COMBATTIMENTO`: termine in grassetto, descrizione, un filetto fra le righe | **solo filetti orizzontali**, nessun bordo verticale |
| Wil stampata 146 (e altre carte AREA) | `INGREDIENTI`: `STILE \| NOME \| EFFETTO` | righe separate da **puntini**, nessun bordo verticale |
| DB stampata 13 | metà sinistra di `D10 PROFESSIONE` | le griglie a filetti ci sono, piene al 100%, ma la regione a testo è **larga 21 punti** — solo la colonna dei numeri — e il loro centro le cade fuori |

## 3. Che cosa è caduto

La strategia a filetti di pdfplumber trova una cella solo dove ci sono bordi **in
entrambe le direzioni**. Le tabelle a griglia completa e quelle a righe
ombreggiate — i rettangoli danno i bordi verticali — le trova tutte: armi, tesori,
D6 ATTACCO. Le tabelle segnate **solo in orizzontale** no, e sono una forma
comune: su DIE è la forma di tutte le tabelle di definizioni, che l'utente aveva
indicato come «schede simili a tabelle».

Il criterio aveva scritto il rischio: «una tabella vera senza filetti né righe
ombreggiate … la strategia a filetti non la trova». Il rischio vero è più largo:
basta che manchino i bordi **verticali**.

## 4. Esplorazione per la prossima forma

`output/resa/forma_righe.py`, sulle regioni a testo delle pagine giudicate:

| gruppo | caratteri per cella | righe di testo per cella, max |
| --- | --- | --- |
| fantasmi di **prosa** (Dag 107, DB 42, Dag 310, Dag 49, Apo 10) | **91-303** | 14-24 |
| **moduli e diagrammi** (Dag 351, DB 123, DIE 23, Dag 14) | 8-27 | 3-20 |
| tabelle **vere** (armi, tesori, D6, ingredienti, definizioni, D10) | **15-40** | 3-14 |

Due strade, ed è una decisione:

- **i filetti come unica voce** (questa v1): toglie tutti i fantasmi, moduli e
  diagrammi compresi, ma perde le tabelle segnate solo in orizzontale.
- **i filetti OPPURE celle corte**: tiene una regione se i filetti la risolvono,
  oppure se le sue celle sono corte come quelle di una tabella; toglie solo i
  fantasmi di prosa. Moduli e diagrammi restano tabelle — brutte, ma non
  peggiori di adesso — e nessuna tabella vera si perde. Serve un confine fra 40 e
  91 caratteri, e va ricavato dal documento, non fissato: le soglie in questo
  progetto non si cablano.

## 5. Conseguenza

La regola si ritira come dichiarato. `page_analysis.ruled_table`, la regola nel
consumer e i loro test restano in albero; in `run()` l'interruttore
`TABELLE_A_FILETTI` è spento.
