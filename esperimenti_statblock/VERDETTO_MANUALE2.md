# Validazione su un secondo manuale — Dragonbane Quickstart (ITA, 47 pagine)

Eseguito `pila.py` **congelato**, senza modifiche e senza che mi fosse detta
l'etichetta ricorrente. Il verdetto e' **fallimento**, per tre cause
indipendenti. Nessuna e' stata corretta prima di scrivere questo file.

## Verita' di riferimento, per via indipendente
Ogni scheda mostro Dragonbane porta `Ferocia:` una volta. Occorrenze: pagine
indice 29, 31, 33, 35 -> **4 schede mostro**. Formato reale (pag. 29):

    RAGNO GIGANTE                      <- Hideout-Bold 10.0, colore 6175001
    Ferocia: 2   Taglia: Normale       <- etichette in grassetto, 2 campi/riga
    Movimento: 24  Armatura: —  PF: …  <- 3 campi sulla stessa riga
    ATTACCHI MOSTRUOSI + tabella d6

## Causa 1 — troppe poche istanze (il limite gia' previsto)
`MIN_RICORRENZA` congelato a 5. `Ferocia` compare **4** volte: sotto soglia,
scartata. Il principio su cui poggia il metodo — la frequenza separa lo schema
dal contenuto — non ha nulla su cui lavorare con 4 istanze.

Non e' una sorpresa: e' esattamente la fragilita' misurata e committata
**prima** di vedere questo manuale (`SENSIBILITA.txt`, commit `ffcfec9`): «la
robustezza scala con il numero di istanze del template meno numeroso» e «un
manuale con poche istanze di un template lo perde, e lo perde in silenzio».

E lo ha perso **in silenzio**: il metodo ha riportato 16 gruppi e 34 etichette
di schema, tutte nomi di abilita' delle schede personaggio (Acrobazia, Archi,
Artigianato...), senza mai segnalare di aver mancato un template.

## Causa 2 — regressione: una sola etichetta per riga
`etichetta()` in `pila.py` prende **il primo span** della riga. Ma il formato
mette 2-3 campi sulla stessa riga. Conseguenza misurata:

| etichetta | occorrenze viste | vere |
| --- | --- | --- |
| Ferocia | 4 | 4 |
| Taglia | **0** | 4 |
| Armatura | **1** | 4 |
| PF | **3** | 4 |
| Movimento | 7 | 4 (le altre 3 da testo di regole) |

Una su cinque ammessa, e per il motivo sbagliato. E' una **regressione** che ho
introdotto io scrivendo `pila.py`: la versione precedente (`real5.py`) estraeva
piu' coppie etichetta/valore per riga, e su Daggerheart era indispensabile
(`Difficulty: 12 | Thresholds: 4/8 | HP: 3`). Semplificando l'ho persa.

**Correggerla non avrebbe salvato il test**: con l'estrazione multipla ogni
etichetta arriverebbe a 4 occorrenze, ancora sotto la soglia di 5. La Causa 1
resta.

## Causa 3 — il separatore di colonne frantuma una pagina a colonna singola
`COL_GAP = 30.0` su una pagina di 612pt **a colonna unica** produce 2-4
«colonne» spurie, perche' elementi centrati o rientrati distano piu' di 30pt dal
margine del corpo:

| pagina | «colonne» dedotte | nome del mostro | campi | esito |
| --- | --- | --- | --- | --- |
| 29 | 4 (x=60,134,222,300) | x=133,8 | x=85,0 | **colonne diverse** |
| 31 | 3 | x=62,4 | x=85,0 | stessa |
| 33 | 2 | x=271,8 | x=85,0 | **colonne diverse** |
| 35 | 3 | x=280,1 | x=303,3 | stessa |

Su 2 schede su 4 il nome finisce in una colonna diversa dai propri campi:
anche con le etichette ammesse, la pila di testa non avrebbe mai potuto
raggiungerlo. La costante 30pt era tarata su un impaginato a quattro colonne
larghe 250pt e non e' trasferibile.

## Cosa questo test ha e non ha validato
- **Non ha validato la pila di testa**, che era l'oggetto della prova: non e'
  mai stata esercitata, perche' il prerequisito (le etichette di schema) e'
  fallito a monte.
- **Ha validato la previsione di fragilita'** fatta e committata prima: il
  metodo perde i template poco numerosi, e li perde senza rumore.
- Ha rivelato due difetti che il primo manuale non poteva rivelare: la
  regressione sull'estrazione multipla per riga, e la non trasferibilita' del
  separatore di colonne.

## Conseguenze, da decidere e non decise qui
1. **La regola di non-perdita diventa urgente, non piu' rinviabile.** Un metodo
   che non trova un template deve dirlo. Serve una misura di copertura: quanto
   testo del documento non e' spiegato da nessuno schema, e dove si concentra.
   Con 4 schede su un documento intero, quel residuo sarebbe stato evidente.
2. **La soglia di ricorrenza va separata dalla dimensione di gruppo.** Legarle
   era una scelta di coerenza interna difendibile, ma impedisce per costruzione
   di vedere un template di 4 elementi. Serve un criterio che ammetta template
   piccoli senza ammettere rumore: probabilmente la co-occorrenza (queste 5
   etichette compaiono **insieme**, sempre, in 4 regioni vicine) invece del
   conteggio della singola etichetta.
3. **Il separatore di colonne va derivato**, come tutto il resto: da un profilo
   di proiezione verticale del testo, non da una distanza in punti.
4. **L'estrazione multipla per riga va ripristinata** e messa a test.

## Regola rispettata
Nessuna costante e' stata toccata dopo aver visto questi risultati, e nessuna
riesecuzione «aggiustata» e' stata presentata. Il terzo manuale, quando ci sara',
dovra' validare le correzioni sopra, non questo giro.
