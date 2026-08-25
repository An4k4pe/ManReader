# Criterio — l'uscita leggibile: stile, elenchi, arredo, box

Registrato prima dell'implementazione. Commit **senza codice** (`AGENTS.MD` §15).
Una pagina, come il §17 prescrive.

**Cinque cambiamenti sotto un criterio solo**, giudicati una volta alla fine.
Ieri un ciclo criterio-misura-verbale è costato una giornata; cinque ne
costerebbero cinque. Il rischio — se cade non si sa quale l'ha fatta cadere — si
mitiga riportando anche il diff per meccanismo, che è gratis.

## 1. Che cosa cambia

| # | cambiamento | perché, e con quale numero |
| --- | --- | --- |
| A | **stile inline** `bold`/`italic` portato dal nodo ed emesso in Markdown | 13 pagine su 20 lo chiedono (`Esito_FormaMancante_v1.md` §3); i tratti sono popolati da `8c9ba1e` e nessuno li legge |
| B | **elenchi** riconosciuti ed emessi come tali | 4 pagine su 20 lo chiedono; chiude anche le 2 sconfitte dell'A/B di ieri e il box di DB p.99 |
| C | **arredo** — intestazione corrente, numero di pagina, linguetta — fuori dal corpo | 5 pagine su 20 lo segnalano come difetto secondario |
| D | **note colorate a blocco** rese come box | regola dell'utente: niente colore in uscita, il colorato che è tutto il nodo diventa un box |
| E | **nota d'asset su pagina senza altro contenuto** resa nel corpo | Lan idx 192: il cancello di Milestone 38 toglie l'unica cosa che la pagina porta, ed è metà dell'obiettivo |

**Vincoli sul meccanismo**, invariati: ogni grandezza desunta dal documento, mai
un elenco di parole, di font o di colori. Il corpo — font, colore, estensione —
si desume dalla pagina come già fa `body_font`.

**C non cancella niente.** L'arredo esce dal corpo e va nel canale `review`, come
già fanno le note d'asset non accettate: nessuna esclusione silenziosa
(`AGENTS.MD` §Coverage).

## 2. Come si giudica

**Campione**: 20 pagine, seed `20260826`, dichiarato qui prima dell'estrazione.
Escluse per costruzione tutte le pagine già spese — i tre insiemi di
`sample_ir2_verification_pages.py` più le 40 di `Campione_FormaMancante_v1.md`.

**A/B cieco**, stessa macchina di `Criterio_RotturaParagrafo_v2.md`:
assegnazione estratta per pagina con seed `20260827`, chiave in un file non
aperto finché le risposte non sono date, una risposta per pagina — **A** · **B** ·
**uguali**.

> **Regge** se «nuovo» vince su almeno **10** pagine **e** «vecchio» vince su al
> più **2**. **Cade** altrimenti.

Stessa barra dell'ultimo giro, che ha retto con il vecchio esattamente sul tetto:
non è stata scelta per questo giro e non si tocca.

## 3. L'errore squalificante

> **Cade comunque** se su una sola pagina il testo non si conserva: il
> multiinsieme dei caratteri di **corpo più canale review**, spazi e trattini
> esclusi, dev'essere identico prima e dopo.

Il perimetro è corpo **più** review perché C sposta testo fra i due: confrontare
il solo corpo dichiarerebbe una perdita dove c'è uno spostamento, e nasconderebbe
una perdita vera dentro lo spostamento.

## 4. I controlli a vista

Uno per cambiamento, e **cadono il criterio se peggiorano**:

| pagina | che cosa guarda |
| --- | --- |
| DIE p.380 | le note rosse diventano box (D), e il corpo non peggiora |
| DB p.99 | gli elenchi e il box a rientro sospeso (B) |
| Fab p.248 | i pallini Wingdings (B, caso del font simbolico) |
| Lan idx 192 | la full art porta la sua nota (E) |

## 5. Che cosa resta fuori, dichiarato

**Le tabelle**, per decisione dell'utente: 3 pagine su 60, meccanismo senza
criterio, la cosa più complessa da implementare.

**L'ancoraggio** delle note a margine al paragrafo che commentano. L'utente lo
dichiara interessante e si accontenta del box: su DIE p.380 le quattro note
restano **tutte in cima**, dove l'ordine di lettura le mette, e il box risolve
«indistinguibile», non «nel posto sbagliato».

**Il titolo colorato** — una parola sola colorata che sia tutto il nodo — che la
regola di D renderebbe un box a torto. Distinguerlo è la domanda `text.heading`,
che `ir2_model.py:62` riserva a una milestone sua.

**La deduplica document-level** dell'arredo: C è page-local, e il segnale forte —
lo stesso testo alla stessa y su molte pagine — richiede un consumer che non
esiste.

**Il grassetto marcato solo nel nome del font** e non nei flag, limite già
dichiarato in `primitive_normalizer.font_traits_from_flags`.

## 6. Che cosa NON decide

Non decide l'uscita dallo shadow mode. Non riapre le tabelle. Non apre il
detector di marginalia come classificazione: C toglie dal corpo ciò che sta ai
bordi e lo mette in review, non dichiara che cosa sia. Non decide se
`text.heading` vada emesso.
