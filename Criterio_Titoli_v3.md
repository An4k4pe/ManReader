# Criterio — i titoli, v3. Il blocco non è l'unità, la **riga** lo è

## 0. Che cosa cade della v2

`Esito_Titoli_v1.md`: precisione 100% su 16, **cinque titoli mancati**, e la causa
è una sola — il backend mette il titolo **nello stesso blocco della prosa che
introduce**, e le condizioni 2 e 3 del §1 lo scartano.

Rilievo dell'utente sulle pagine intere, che nomina i casi uno per uno: su BiD
`ridurre il sospetto`, `recuperare`, `alleviare lo stress`, `indulgere`,
`eccedere`; su Dag `QUANDO IL DISASTRO È IMMINENTE` e `INTRODURRE UN NUOVO
PERSONAGGIO`. Sono **palesemente più grandi del loro paragrafo** e finiscono fusi
nel testo come grassetti.

> «La discriminante del carattere maggiore rispetto al testo è fondamentale.»
> Indicazione dell'utente, ed è quella che questo criterio mette al centro
> togliendo di mezzo il blocco.

**E una cosa che il vincolo del blocco non stava facendo**, misurata prima di
toglierlo: **non teneva fuori le schede di DrM**. Su DrM le righe sopra la prosa
in blocchi che contengono prosa sono **zero**, perché le celle di scheda stanno a
dimensioni che sono esse stesse prosa. Il vincolo costava cinque titoli e non
comprava la protezione per cui l'avevo messo.

## 1. La regola

Invariato dalla v2: le **dimensioni di prosa** si riconoscono perché le loro
righe sono lunghe, col taglio al salto più grande fra le mediane. Invariato il
**livello** come rango.

Cambia la condizione sul blocco:

> Una riga sorgente è un **titolo** se:
>
> 1. la sua dimensione è **maggiore della più grande dimensione di prosa**;
> 2. nel suo blocco è **l'unica riga alla sua dimensione**;
> 3. il suo testo è più lungo di **un carattere**;
> 4. non è già escluso dal corpo come **arredo**.

La **2** sostituisce le due condizioni cadute — «il blocco non contiene prosa» e
«al più due righe». Non è un rilassamento generico: è **un'altra cosa**. Un titolo
è solo alla sua dimensione dentro il suo blocco; una cella di scheda o una riga di
tabella ha sorelle alla stessa dimensione.

Misurato sui casi mancati:

```
BiD 'recuperare'                      dim 14.0, blocco di 24 righe, 1 alla sua dimensione
BiD 'ridurre il sospetto'             dim 14.0, blocco di 24 righe, 1 alla sua dimensione
BiD 'ALLEVIARE LO STRESS'             dim 13.0, blocco di  9 righe, 1 alla sua dimensione
Dag 'QUANDO IL DISASTRO È IMMINENTE'  dim 11.0, blocco di 10 righe, 1 alla sua dimensione
Dag 'INTRODURRE UN NUOVO PERSONAGGIO' dim 11.0, blocco di  9 righe, 1 alla sua dimensione
```

E su BiD, delle righe sopra la prosa in blocchi con prosa, **10 sono sole alla
loro dimensione e 14 no**: la condizione separa, non ammette tutto.

### Che cosa la modifica aggiunge, misurato prima di eseguirla

| manuale | righe in più | esempi |
| --- | ---: | --- |
| Lan | 31 | `NEXUS MOD. "GHOUL"`, `PUPPETMASTER`, `SCHIERAMENTO COMPLETO` |
| Dag | 22 | `CONFLITTI SOCIALI`, `COMBATTIMENTO`, `Influenzare i PNG` |
| DB | 15 | `ANIMISMO`, `ELEMENTALISMO`, `MENTALISMO` |
| BiD | 10 | `arresto`, `morti irrequieti`, `acquisire una risorsa` |
| Kul | 3 | `GUADAGNARE SCIAGURA`, `ACCUMULARE SCIAGURA` |
| FWK | 1 | `"Ho una storia per voi" disse la favolista a` |
| **DrM, Wil, Fab** | **0** | |

**Un falso positivo è già visibile e va dichiarato**: l'epigrafe di FWK, una
citazione lunga a corpo display. Non aggiungo una condizione di lunghezza per
toglierla — le varianti di lunghezza desunte sono già cadute una volta
(`Criterio_Titoli_v2.md` §0) — e la lascio al veto.

## 2. Il titolo che va a capo è **un** titolo

> Righe consecutive dello stesso blocco, tutte titoli **della stessa
> dimensione**, formano **un solo** titolo, unite come si uniscono le righe di un
> paragrafo.

Difetto misurato: su Dag `FAR SALIRE DI LIVELLO IL` e `GRUPPO` stanno nello stesso
blocco a dimensione 12.0 e uscivano come **due** titoli. La v2 ammetteva il blocco
di due righe proprio per i titoli che vanno a capo, e poi li rendeva separati.

**Nota che questo interagisce con la condizione 2 del §1**: due righe alla stessa
dimensione nello stesso blocco non sono più «sole alla loro dimensione». Quindi la
condizione va letta **dopo** l'unione: prima si uniscono le righe consecutive di
pari dimensione, poi si conta.

## 3. Il campione, e una regola nuova sul suo confine

**16 righe promosse e 16 scartate**, seed **`20261003`**, materiale con la
**pagina intera** e **tutte** le occorrenze — le due correzioni imposte
dall'utente e dall'etichettatore sul giro precedente.

> **I manuali densi di schede escono dalla popolazione campionata, e si dichiara
> qui, prima del sorteggio.**

Nel giro precedente DrM ha dato **13 righe su 32** e **11 delle 11 «non titolo»**:
un manuale solo decideva un terzo del giudizio, su una categoria che il progetto
sa di non gestire e che tre meccanismi di fila hanno indicato. Indicazione
dell'utente: «finché non li risolviamo bisogna ignorarli o non introdurli nei
campioni».

**Dichiararlo prima è ciò che lo distingue dallo scartare i casi scomodi dopo**,
che è quello che `AGENTS.MD` §15 vieta. E il prezzo si paga per intero: ciò che la
regola fa su quei manuali **si riporta separatamente**, con i suoi numeri, nel §4.B
dell'esito. Non sparisce, esce dal conteggio del veto.

Fuori dal campione: **DrM**, **DrW**. Sono i due il cui corpo misurato è il testo
di scheda (7,5) invece della prosa.

## 4. Pass/fail

### A. Veto — cade a una sola riga, in entrambe le direzioni

> Cade se **una sola** riga promossa non è un titolo, o se **una sola** riga
> scartata lo era.

Etichette **titolo** / **non titolo** / **incerto**, seed di controllo
**`20261004`**. Resta il rinforzo del protocollo: **una riserva scritta accanto a
un'etichetta netta viene contata come `incerto`**.

### B. Regressione — i sedici della v2 devono restare titoli

> Le 16 righe che il giudizio precedente ha promosso e che sono state confermate
> titoli devono restare promosse.

È verità di riferimento già guadagnata, e impedisce che il rilassamento compri
copertura perdendo precisione altrove.

### C. La dispersione, e i due manuali esclusi

> Si riporta il numero di titoli per manuale, **e separatamente** quanti ne
> produce la regola su DrM e DrW.

### D. La giunzione

> Per ogni titolo prodotto si guarda il paragrafo sopra e sotto. Un titolo
> promosso **in mezzo a un paragrafo** lo spezzerebbe in due.

Qui il bersaglio è più vicino che nella v2: la condizione nuova promuove righe che
stanno **dentro** blocchi di prosa, che è esattamente dove quel danno vive.

### E. Regressione degli altri meccanismi

> `check_list_regression.py` e `check_numbered_lists.py` invariati.

### Se cade

- **A** verso «promossa e non lo era»: si riporta quale caso, e **non** si
  aggiunge una condizione nello stesso giro.
- **A** verso «scartata e lo era»: resta scoperto, e si nomina.
- **B**: il rilassamento ha rotto ciò che funzionava, e va ritirato.

## 5. Che cosa resta fuori

- **Le schede mostro come categoria**, ora anche formalmente fuori dal campione
  (§3). Il debito resta, e questo criterio lo rende visibile invece di lasciarlo
  inquinare i giudizi.
- **L'arredo in cima alla pagina** — `Capitolo 6`, `Scourge`, `PREMI START`, i
  numeri di capitolo. Fascicolo suo, con la misura già fatta: uno slot ricorrente
  che porta **lo stesso testo** è arredo ovunque stia, ed è la generalizzazione
  del ramo 1 che gia' non ha vincolo di posizione.
- **Il font come seconda via per i marcatori d'elenco**, che sblocca Fab.
- **La gerarchia**: i livelli restano ranghi di dimensione, non un albero.
