# Esito di `Criterio_TestatinaCorrente_v1.md` — **23 su 25, e la voce che cade era mia**

**Stato in una riga**: 25 voci giudicate, **23 arredo, 1 contenuto, 1 incerto**.
Il veto §4.A cade a una sola voce, e quella voce non era un difetto della regola
ma della sua implementazione: identificavo la testatina **per testo** e la
toglievo **per posizione**.

---

## 1. Il verdetto

Tutte le voci che il ramo produce sui 16 manuali — 25 in tutto, nessun
campionamento.

| | |
| --- | ---: |
| arredo | **23** |
| contenuto | **1** |
| incerto | 1 |

L'etichettatore le ha riconosciute una per una descrivendone la composizione, e
la distribuzione conferma che il vincolo di posizione andava tolto:

- **testatine in alto**: `Fortuna & Sciagura`, `Capitolo 5`, `Il Mondo`, `SCOURGE`
- **piè di pagina**: `DIE: IL GIOCO DI RUOLO`, `Capitolo 3: Condurre una
  Sessione`, `PRIMO ATTO`, `SECONDO ATTO`, `CAPITOLO 5 – MAGIA`, `8. BESTIARIO`,
  `GIOCARE`
- **linguette verticali sui bordi**: `CAPITOLO`, `HORUS`, `TALENT`, `PREMI START`,
  `4 // L'INCARICO`, `DRAW STEEL` ×2, `DOWNTIME`
- **filigrane d'acquisto**: quattro, su DB, DIE, Fab e Lan

E ha visto la distinzione che il criterio si era dato: su Kul «il titolo vero
della pagina sta sotto, in nero», su Lan «`HORUS` compare anche come titolo vero:
qui giudico l'occorrenza ripetuta».

## 2. La voce che cade, e perché è colpa mia

**Voce 01, Vil.** Lo slot (13,11) porta:

```
idx 128, 135, 137, 143   'G I O C A R E'            ← la testatina
idx 131                  'DONI'                      ← titolo di sezione
idx 133                  'PULSIONI'
idx 138                  'DOVERE'
idx 126                  '4. NARRATE I RISULTATI'    … e altri nove
```

La regola trova `G I O C A R E` concentrato a quello slot — **correttamente** — e
poi io toglievo **lo slot intero**, che porta via tredici titoli di sezione.

Il §1 del criterio dice «un **testo** è testatina». L'implementazione toglieva
posizioni.

> **È la seconda volta che faccio questo errore nello stesso giro.** La clausola
> del verticale identificava una primitiva e toglieva il suo slot, e su Fab
> portava via la prosa che passava per lo stesso punto. Identificare per una cosa
> e togliere per un'altra è il difetto, non il criterio.

**Corretto**: il ramo torna coppie **(testo, slot)**, e l'esclusione confronta
**testo e posizione insieme**. Un titolo di sezione che passa per lo stesso punto
resta; un'occorrenza dello stesso testo altrove nella prosa resta.

Verificato dopo la correzione: su Vil `DONI` e `PULSIONI` restano nel corpo,
`G I O C A R E` va in review. E i casi nominati dall'utente restano tolti —
`Scourge` su FWK, `PREMI START` su Fab, `Fortuna & Sciagura` su Kul.

> **Il giudizio va rifatto sulla versione corretta**, come per la clausola del
> verticale: le 23 voci giudicate arredo restano un indizio forte, non un
> verdetto. Ma la voce che faceva cadere il veto non è più prodotta.

## 3. La voce `incerto`

Voce 07: il render assegnato è un'illustrazione a piena pagina e l'etichettatore
non ha trovato testo, «anche con stiramento di contrasto e CLAHE sulle bande
scure». Ha rifiutato di decidere invece di indovinare.

È la terza volta di fila che il canale `incerto` viene usato per quello che è. E
segnala un difetto del materiale: il render di una voce dev'essere una pagina in
cui quella voce **si vede**.

## 4. Che cosa il giudizio conferma del criterio

**La barra §4.C tiene**: `Stamina` di DrM, `Psionic` di DrW e `Percepire` di DB —
il contenuto che la clausola A distruggeva — restano tutti nel corpo. È la barra
che separa questa clausola da quella ritirata, ed è passata.

**La barra §4.B tiene per i casi che esistevano**: `Capitolo 6` e `Scourge` su
FWK, `PREMI START` e `CAPITOLO` su Fab, `Fortuna & Sciagura` su Kul escono tutti.

`Vileborn` su Apo **non era una testatina** e il criterio sbagliava a chiederlo:
55 occorrenze su 53 slot, è il nome dei personaggi usato nel testo. La regola lo
rifiuta, ed è il comportamento giusto.

**BoB e Wil a zero sono un fatto**, verificato prima del giudizio: su BoB nessun
testo compare su un quarto delle pagine, su Wil ciò che ricorre sono le etichette
della scheda d'area, sparse su 18-30 slot.

## 5. Conseguenza

Il criterio **non è scaricato**, ma per una ragione diversa dal solito: la regola
ha fatto il suo mestiere su 23 voci su 25, e l'unica caduta è stata prodotta dalla
mia implementazione, non dalla regola.

Corretta l'implementazione, il giudizio va rifatto. È il costo di aver sbagliato
due volte lo stesso passaggio.

## 6. Verifiche

Suite **1472** test, un solo fallimento, quello ambientale già a verbale.
