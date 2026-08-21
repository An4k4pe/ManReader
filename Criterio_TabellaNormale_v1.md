# Criterio — le tabelle **normali** escono giuste, con una configurazione sola

Registrato **prima** della misura e prima dell'estrazione del campione. Da
committare in un commit **senza codice** (`AGENTS.MD` §15).

Decide se il percorso tabella prosegue. Posizione di chi lo apre, dichiarata
entrando: **prima delle tabelle speciali vanno risolte con certezza e costanza
quelle normali** — indicazione dell'utente, non ipotesi di Chat A.

---

## 1. Che cos'è una tabella «normale», fissato prima di guardare

Una regione è una **tabella normale** se, a vista sul render, ha tutte queste
proprietà:

1. è **una** griglia rettangolare, non due affiancate che condividono le righe;
2. ogni riga della tabella corrisponde a **una voce**;
3. **nessuna cella si estende su più colonne** (niente righe unite a piena
   larghezza);
4. non ha **righe di raggruppamento** che fanno da titolo a un blocco di voci
   sotto di sé.

Sono ammesse: celle che vanno a capo; una riga d'intestazione; colonne di soli
numeri; colonne vuote.

Tutto il resto è **speciale** e **non concorre** a questo criterio. Le tre forme
speciali già osservate, nominate qui perché non vengano riclassificate dopo:

| forma | pagina osservata |
| --- | --- |
| tabelle affiancate che condividono le righe | SV idx 189 |
| righe unite a piena larghezza | Fab idx 280, Fab idx 272 |
| righe di raggruppamento | Lan idx 284 (ARTIGLIERIA, ASSALTO, …) |

## 2. La configurazione, fissata prima

**Una sola**, e va dichiarata prima di vedere il campione perché la misura non
diventi una scelta fra sette varianti:

```
--region text-lines --repair xy --bounds middle --rows spine --admit in-column
```

`text/lines` perché è la migliore delle quattro sorgenti sulle sette pagine di
sviluppo (corretta su quattro, contro una di `band` e due di `lines`), **ed è la
configurazione del producer già wired**: se regge, non serve un producer di
regioni nuovo.

Se qualcuno vuole cambiare configurazione dopo aver visto l'esito, serve un
criterio nuovo. Cambiarla qui sarebbe la lettura post-hoc che `AGENTS.MD` §15
vieta, e in questa sessione è già successo quattro volte per criteri scelti
iterando.

## 3. Il campione, e l'ordine dei passi

**Seed `20260822`**, dichiarato qui prima dell'estrazione.

1. Si estraggono **60 pagine** uniformemente dal pool dei 16 manuali. Escluse per
   costruzione le pagine di sviluppo di questa sessione: DB 75, Lan 118, Lan 40,
   Lan 109, Lan 284, Fab 52, Fab 272, Fab 280, Dag 136, Dag 194, SV 43, SV 189,
   Apo 46, Vil 166, Wil 244, DrM 267, FW 62, Fab 256.
2. Per ciascuna si producono **soltanto il render e le regioni proposte** dalle
   tre sorgenti, senza alcuna uscita Markdown.
3. **L'utente etichetta a vista**, prima di vedere qualunque tabella prodotta:
   per ogni regione, «normale» / «speciale» / «non è una tabella»; e per ogni
   pagina, se c'è una tabella che **nessuna** sorgente propone.
4. Solo allora si esegue la configurazione del §2 e si contano i §4 e §5.

Invertire 3 e 4 rende l'etichetta una lettura post-hoc. È il protocollo di
`Criterio_TabellaRisolvibile_v1.md` §4, che regge.

## 4. La regola di pass/fail — **una sola**

> **Regge** se, sulle regioni etichettate **normali**, almeno il **90%** produce
> una tabella che l'utente giudica corretta a vista.
>
> **Cade** sotto il 90%.

«Corretta» è fissato qui: ogni voce della pagina è una riga della tabella, ogni
valore è nella sua colonna, nessun testo della regione è finito fuori dalla
tabella, nessun testo estraneo è finito dentro. Non si richiede
l'intestazione — vedi §6.

Il 90% non è tarato: è la stessa barra di `Criterio_TabellaRisolvibile_v1.md` §5,
fissata lì prima di questa misura e per una domanda diversa.

## 5. Il conteggio che si riporta e non decide

**Falsi negativi**: pagine con una tabella normale che **nessuna sorgente
propone**. Si riporta e non fa fallire, perché questo criterio misura la qualità
di ciò che esce, non la copertura. Un numero alto qui è però la cosa che
deciderebbe il giro successivo, e va scritto anche se scomodo.

## 6. Limiti dichiarati prima

**L'intestazione non concorre.** Su DB idx 75 esce corretta, su Fab idx 52 si
fonde con la prosa sopra: è un difetto noto e non risolto, e includerlo qui
significherebbe misurare due cose e non saperne falsificare nessuna.

**Il campione è di regioni proposte, non di tabelle.** Una tabella che nessuna
delle tre sorgenti vede non entra nel denominatore del §4 — per questo esiste il
§5, che la conta a parte. Il criterio **non** può dire nulla sulla copertura.

**La spina non è provata.** Il modello di riga `spine` regge sulle cinque pagine
di sviluppo e ha **già sbagliato** su una non vista (Lan idx 284, riga di
raggruppamento), che il §1 classifica come speciale. Se cade il §4, la prima cosa
da guardare è se cade per la spina o per la regione, e i due casi vanno contati
separatamente **nell'esito**, non qui.

**Tre criteri di selezione della spina sono già caduti** — passo mediano più
largo, non-va-a-capo, bande y — e uno di regione (`--region auto`). Sono a
verbale nelle docstring di `scripts/prototype_table_columns_and_rows.py`. Questo
criterio non ne propone un quarto: fissa la configurazione migliore nota e la
mette alla prova.

## 7. Che cosa NON decide

Non decide se `table_candidate` vada modificato: la configurazione del §2 è la
sua, invariata. Non decide nulla sulle tre forme speciali del §1. Non riapre
`Criterio_TabellaInIR2_v1.md`, che resta caduto, né accende `--tables`.
