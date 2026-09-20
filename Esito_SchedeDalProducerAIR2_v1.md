# Esito — le schede dal producer a IR 2: **il veto B cade**, e la causa è quella dichiarata

Misura di `Criterio_SchedeDalProducerAIR2_v1.md`, 20 settembre 2026.
Prima: `output/resa/senza-riparo` (strada vecchia, `--schede-campi`, stato di
`d59a22f`). Dopo: `output/resa/producer` (strada nuova, `--schede-producer`).

## 1. I veti

| veto | esito |
| --- | --- |
| **A** l'uscita non cambia | **no** su Dag; **sì** su DB e Apo, identici byte a byte |
| **B** se cambia, meglio > peggio | **CADE**: 0 meglio, 9 peggio |
| **C** le sei tabelle già giudicate restano | **sì** |
| **D** barra | **sì** — 1752 test verdi, Ruff pulito, barra E-B 9 su 10 con la sola Fab idx 126 |
| **veto** la tabella dei tesori non perde righe | **regge** |

**Le tabelle non si muovono di una riga**, su nessuno dei tre manuali:

```
DB:  senza-riparo -> producer   uguali 70  ridotte 0  SPARITE 0  CRESCIUTE 0  nuove 0
Apo: senza-riparo -> producer   uguali 16  ridotte 0  SPARITE 0  CRESCIUTE 0  nuove 0
Dag: senza-riparo -> producer   uguali 61  ridotte 0  SPARITE 0  CRESCIUTE 0  nuove 0
```

Tutta la differenza sta nei **ritorni a capo dei record**: Dag perde 9 paragrafi
su 7 pagine, e ogni perdita è un'intestazione di record incollata alla riga
precedente. Nessuna in meglio.

## 2. Che cosa è caduto: la nozione di «riga», come dichiarato al §1

Il criterio lo scriveva prima di misurare: «sono due nozioni di riga diverse, e
possono dare combinazioni diverse. Se le danno, l'uscita cambia». Le danno.

**Tre perdite su nove** (Dag idx 326, 333, 335, i colossi) vengono da lì. Su idx
326 le righe di sorgente sono:

```
  7  coppie 1  Dimensioni: 29 metri di altezza, 20 metri di larghezza
  8  coppie 1  Segmenti: 2 Gambe, 2 Braccia, 1 Torace e 1 Testa
  9  coppie 2  Soglie: 11/22 | Stress: 6      <== l'unica riga di campi
```

La catena di lettura fonde 7 e 8 in **una** riga visiva da due coppie, e allora
le righe di campi sono due e fanno un gruppo. Il `source_observation_id` le
tiene separate, resta una riga sola, e il producer — che ne chiede due — non
propone niente.

**Sei perdite su nove** vengono invece da un **artefatto che la strada nuova
scarta ed è giusto che scarti**. La strada vecchia, su Dag, imparava 22
combinazioni; cinque sono apostrofi:

| combinazione appresa | da dove |
| --- | --- |
| `['ibrido', 'privilegiodell']` | `Privilegio dell'Ibrido:` |
| `['uccello', 'vistaavolod']` | `Vista a Volo d'Uccello:` |
| `[')-passiva', 'orda(']` | `Orda (…) - Passiva:` |
| `['1d10', 'avvelenata']` | — |
| `['cascata-reazione', 'distrutto']` | — |

L'apostrofo spezza lo span, `label_spans` conta due etichette dove ce n'è una, e
la coppia si ripete perché il testo si ripete. La strada nuova non le impara
perché chiede che l'etichetta **si dichiari** con i due punti, e
`Privilegio dell` non lo fa.

Il risultato è che quelle sei rotture erano **giuste per una ragione sbagliata**:
`Vista a Volo d'Uccello:` deve andare a capo, e ci andava perché un apostrofo
aveva finto un campo. Perderle peggiora l'uscita; tenerle avrebbe voluto dire
tenere l'artefatto.

## 3. Quello che la strada nuova guadagna, e che il veto non misura

- **Le combinazioni sono più pulite**: Apo passa da 1 a **0** (spariva
  `campagne + manualebase`, che è una frase in grassetto ripetuta, non una
  scheda); Dag da 22 a 17, cinque in meno e sono i cinque apostrofi; DB da 3 a 2.
- **La prima passata sparisce.** `--schede-campi` costava una passata intera del
  documento con pdfplumber per raccogliere le righe dell'ordine di lettura.
  `--schede-producer` misura sulle pagine già catturate.
- **Le schede sono un fatto della pagina**, non un argomento di funzione:
  `page_analysis.stat_block` le propone, `resolve_page_candidates` le decide
  contro la policy del documento, e chiunque altro può vederle.

## 4. Quello che NON si può fare adesso

Non ritocco il criterio, e non allargo il producer dopo aver visto dove il conto
non torna. La regola «almeno due righe con almeno due coppie» è la regola 2 del
modulo e l'utente ha già **rifiutato** l'alternativa «una coppia per riga» al
giudizio dell'11 settembre.

La strada resta dietro `--schede-producer`, la vecchia resta la predefinita, e
le due convivono come il §3 del criterio chiedeva.

## 5. Il giro successivo, se si vuole

La causa delle tre perdite vere è che il producer raggruppa righe di sorgente
mentre la scheda vive su righe **visive**. Una regola che unisce due righe di
sorgente che stanno sulla stessa banda orizzontale e' page-local, non ha bisogno
della catena di lettura, e recupererebbe quei tre casi. Va dichiarata e misurata
a parte: qui sarebbe un salvataggio.
