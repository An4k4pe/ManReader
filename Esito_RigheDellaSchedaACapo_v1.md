# Esito — le righe della scheda vanno a capo

Misura di `Criterio_RigheDellaSchedaACapo_v1.md`, emendato al §5 e corretto al
§5.1 **prima** di questa misura. Rese: `output/resa/posizione` (prima),
`output/resa/acapo2` (dopo).

## 1. Il giro caduto, a verbale

La prima forma del §2 — «una riga che si apre con un'etichetta apre un
paragrafo» — e' stata misurata (`output/resa/acapo`) e **ha fatto cadere il suo
veto C**: su DB idx 69 (stampata 68) tagliava in due la frase «l'ondina può
lanciare ONDATA allo stesso livello di potere dell'incantesimo che / l'ha
evocata». Due pagine cambiate su DB, quattro paragrafi in piu', tre dei quali
tagli di prosa.

Diagnosi: `field_labels` rileva alternanze di stile, non campi. Su una riga
andata a capo con dentro una parola in grassetto chiama «etichetta» tutto il
testo che la precede, al bordo sinistro. La regola delle combinazioni non ne
soffre perche' un'etichetta inventata cosi' non si ripete tre volte; la regola
dei record, che guarda una riga sola, non aveva nessuna protezione.

L'emendamento e la sua correzione sono nel criterio, §5 e §5.1.

## 2. La misura dopo l'emendamento

| veto | esito |
| --- | --- |
| **A** i due difetti citati spariscono | **sì** |
| **B** le tabelle non si muovono | **sì** — 0 sparite, ridotte, cresciute o nuove su tutti e tre |
| **C** nessun paragrafo di prosa spezzato | **sì** |
| **D** barra E-B e test | **sì** — barra 9 su 10 con la sola Fab idx 126, già a verbale; 1729 test verdi |

```
DB:  posizione -> acapo2   uguali 70  ridotte 0  SPARITE 0  CRESCIUTE 0  nuove 0
Apo: posizione -> acapo2   uguali 16  ridotte 0  SPARITE 0  CRESCIUTE 0  nuove 0
Dag: posizione -> acapo2   uguali 63  ridotte 0  SPARITE 0  CRESCIUTE 0  nuove 0
```

**Il veto C, in numeri.** Un paragrafo che comincia in minuscola e' una frase
orfana, cioe' prosa tagliata. Il conteggio non si muove di uno:

| manuale | paragrafi | di cui aperti in minuscola |
| --- | --- | --- |
| DB | 2570 → 2570 | 64 → **64** |
| Apo | 1458 → 1458 | 38 → **38** |
| Dag | 6418 → **7275** | 108 → **108** |

Gli 857 paragrafi nuovi di Dag sono tutti aperture di record. DB e Apo non
cambiano di una riga: su quei due manuali le righe delle schede erano gia'
separate dal confine di blocco, e la regola non aggiunge niente. L'effetto e'
tutto sul bestiario di Daggerheart, 54 pagine.

## 3. Che cosa si legge adesso

Dag idx 230 (stampata 229), la scheda che il rilievo dell'utente indicava:

```
**Motivazioni e Tattiche:** Attirare le prede, divorare, sottometterle con il canto

**Diffi  coltà:** 14 | **Soglie:** 9/18 | **PF:** 5 | **Stress:** 3

**ATT:** +2 | **Mascella Disarticolata:** Mischia | 2d6+3 fi s

**Esperienza:** Repertorio di Canti +3

**CARATTERISTICHE**

***Ascoltatore Avvinto - Passiva:*** Se la sirena eff ettua un attacco base contro
un bersaglio *Incantato* dal suo canto, l'attacco infl igge **2d10+1** danni...

***Canto** Incantato**re - Azione:***** Spendete una Paura** per cantare
```

Prima, la riga `ATT:` stava in coda a `Difficoltà:` e l'intestazione di
`Canto Incantatore - Azione:` in coda al testo della caratteristica precedente.

## 4. Che cosa resta rotto su quella pagina, e non e' questo

- `MINOTAURO DEMOLITORE una canzone che infl uisce...`: il seguito di
  `Canto Incantatore` sta in un paragrafo dopo, preceduto dal titolo della
  colonna accanto. Ordine di lettura a due colonne.
- `SCINTILLANTE` / `GIOVANE` in fondo alla pagina, stessa causa.
- `**CARATTERISTICHE *Inesorabile (3) - Passiva:***` resta saldato per lo
  Scintillante mentre per la sirena `CARATTERISTICHE` sta da solo: la sorgente
  mette le due cose sulla stessa riga in un caso e no nell'altro.
