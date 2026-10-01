# Proposta v3 — la regione tabella: che cosa la v2 sosteneva e perché era troppo forte

Modalità P. **Non committare**: le proposte stanno fuori dal repo (prassi di
Milestone 33, 34, 38, 39).

Questa versione non propone lavoro nuovo. **Rettifica** due affermazioni della v2
che nel frattempo sono state misurate su un campione cieco e non reggono nella
forma in cui erano scritte, e registra il perimetro reale di ciò che è stato
costruito dopo.

---

## 1. Che cosa sosteneva la v2, e con quale base

`Proposta_RegioneTabella_v2.md`, 20 agosto. Tre affermazioni:

| § | affermazione | base |
| --- | --- | --- |
| §0 | il difetto è la **riga**, non la regione | 5 tabelle vere, `tables=1/1` su cinque, Markdown utilizzabile su quattro |
| §3 | «**I gutter non sono il problema, misurato**» | le stesse 5 |
| §5 | «Fuori scope, dichiarato: **un producer nuovo di regioni**» | conseguenza delle prime due |

La v2 aveva già dichiarato il limite del proprio campione — «7 pagine, 6 manuali,
tutte già spese; non è un campione» — ma le tre affermazioni sono state poi citate
senza quel limite.

## 2. Che cosa dice la misura cieca

`Criterio_TabellaNormale_v1.md`, pre-registrato il 21 agosto e **eseguito**
(`Esito_TabellaNormale_v1.md`). Ha provato **esattamente la tesi della v2**: la
regione com'è (`--region text-lines`, la configurazione del producer wired) più il
lavoro nuovo sulle righe (`--rows spine`, riparazioni, confini dal centro).

Campione cieco di 60 pagine, seed `20260822` dichiarato prima, etichette dategli
dall'utente a vista prima di qualunque uscita del codice. **3 tabelle normali.**

| pagina | uscita | causa |
| --- | --- | --- |
| BiD pag228 | **1 colonna**, nessuna tabella | **regione** |
| Dag pag198 | la regione parte da `potete utilizzare:`, che è prosa | **regione** |
| Wil pag59 | 2 colonne, 4 righe che fondono più voci ciascuna | **riga** |

**Zero su tre.** E **due delle tre cause sono la regione.**

## 3. Le due rettifiche

**Il §3 della v2 è ritirato nella sua forma assoluta.** «I gutter non sono il
problema» era misurato su cinque tabelle **scelte perché erano tabelle ben
delimitate**, dove la regione capitava giusta. La formulazione che regge sui dati
di adesso è:

> Su tabelle già ben delimitate la regione non è il difetto e la riga sì. Dove la
> delimitazione è sbagliata — **2 tabelle cieche su 3** — la regione è il difetto
> principale, e nessun lavoro sulle righe la recupera.

**Il §5 della v2 è ritirato.** «Un producer nuovo di regioni fuori scope» era la
conseguenza del §3. Caduto il §3 nella forma assoluta, cade anche il divieto: il
lavoro sulla regione **non era fuori perimetro**, e va tolta la contraddizione fra
quella riga e ciò che è stato costruito dopo.

Resta vero — e va tenuto — che la v2 aveva ragione sul **peso relativo**: su una
tabella ben delimitata il difetto residuo è la riga, e le quattro forme che la v2
nomina (cella che va a capo, righe che si fondono, intestazione fuori dal bordo
superiore, testo che sfugge dai bordi laterali) sono tutte reali e due di esse
sono state chiuse dal lavoro successivo.

## 4. Che cosa è stato costruito, e che cosa gli manca

`scripts/prototype_table_max_columns.py` — **la settima sorgente di regione**.
Meccanismo proposto dall'utente: si cerca l'insieme di gutter più numeroso che
regge, e le bande che quei gutter attraversano **sono** la tabella; poi si estende
con due regole (nessun gutter incontra testo; almeno una cella fra due gutter
contiene testo), con i gutter che si restringono invece di spezzare la regione.

Su 16 tabelle vere ne produce **13 corrette**, e sulle pagine che l'utente aveva
tracciato a mano i gutter coincidono con i suoi: DB pag76 otto su otto, Lan pag19
sei su sei, BoB pag239 il suo.

**Quel «13 su 16» non è una misura.** Sei regolazioni sono state aggiunte una per
pagina su sei di quelle stesse pagine — il fondo che non blocca, il visivo con
testo dentro, `embedded_visual` per i frammenti, l'esclusione del testo ruotato,
il confine di banda sull'interlinea, la pienezza come spareggio. È un **fit**, e
un numero fuori campione **non esiste**.

**E il meccanismo non ha un criterio.** È l'unica delle sette sorgenti di regione
mai sottoposta a una regola scritta prima. Rilievo della revisione indipendente,
accettato.

## 5. Che cosa la misura cieca dice del meccanismo nuovo

Scansione di 120 pagine, seed `20260823`, esclusioni dichiarate:

- **107 pagine su 120 producono una regione.** Il problema del tasso di base che
  `State.md` registra da Milestone 35 è intatto.
- Il filtro sulla pienezza al 100% ne lascia **16**, di cui **10 a due colonne**.
- Di cinque aperte fra quelle a due colonne, **quattro non sono tabelle**: prosa a
  due colonne, riquadri di scheda affiancati, due elenchi puntati, un elenco in cui
  il «gutter» separa il pallino dal testo.
- **E l'indicatore di pienezza è un artefatto**: è calcolato sulla finestra seme e
  riportato invariato dopo l'estensione. Ricalcolato sulla regione emessa, la
  separazione fra corrette e sbagliate **sparisce**.

Il difetto dominante è **uno solo**, misurato su quattro pagine: la regione
**attraversa il gutter di pagina** e lo adotta come colonna di tabella.

## 6. Il perimetro reale, dichiarato adesso

**Non c'è più una contraddizione fra documenti.** C'è un meccanismo che funziona
su tabelle vere, non ha un criterio, ha un difetto dominante identificato e un
indicatore di qualità che va rifatto.

**Che cosa serve prima di chiamarlo un risultato**, in quest'ordine:

1. un criterio pre-registrato con l'etichettatura a vista prima di qualunque
   conteggio, su un campione **di tabelle** — 60 pagine uniformi ne contengono tre,
   quindi il campione va costruito diversamente;
2. l'indicatore ricalcolato sulla regione emessa (candidato: il **minimo** fra le
   colonne, non la media);
3. il vincolo che impedisce alla regione di attraversare il gutter di pagina, per
   il quale **non esiste ancora una regola che scatti** — cinque forme provate.

## 7. Che cosa questa v3 non decide

Non decide se il prossimo giro debba stare sulle tabelle. Quella scelta si fa
contro l'obiettivo — un Markdown leggibile a occhio — e i numeri per farla sono
nel `Prompt_ChatNuova_v1.md`, non qui.
