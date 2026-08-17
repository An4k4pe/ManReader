# Criterio di uscita — IR 2 minima, bersaglio Markdown

Scritto **prima** dell'implementazione e **prima** di estrarre il campione, e
committato insieme allo strumento che lo estrae
(`scripts/sample_ir2_verification_pages.py`). Il seed è nel commit: se fosse
scelto dopo aver visto le pagine, il criterio non varrebbe nulla.

Riferimento: `Proposta_IR2Minima_v3.md` (fuori dal repo, prassi di Milestone
33/34/35).

---

## 1. Che cosa questo criterio NON è

**Non è la milestone di uscita dallo shadow mode.** Quella richiede la lista di
`AGENTS.MD` §Migrazione, che include «callout e tabelle DB preservati» — con i
tipi di nodo di v0 né i callout né le tabelle sono preservabili. **Uscire dallo
shadow mode a v0 è impossibile**, e dire il contrario sarebbe un criterio che non
può fallire.

Questo criterio decide una cosa sola: **se lo stadio IR 2 minima, con il suo
emettitore Markdown, produca un Markdown che una persona riconosce come la
pagina.**

## 2. I due errori squalificanti

**E-A — contenuto perso.** Testo presente sulla pagina e assente dall'uscita.

Vale come guardia contro i bug, **non** come misura del progetto: la copertura è
garantita per costruzione dal costruttore IR 2 e verificata dal validatore, quindi
un contenuto perso può solo essere un difetto di implementazione. È dichiarato
qui perché non venga scambiato per la prova che lo stadio funziona.

**E-B — ordine sbagliato.** L'ordine emesso confrontato con un **riferimento
umano** su pagine **trascritte a mano**, scelte **prima** della misura.

È il metro che porta il peso, ed è il terzo invariante che manca al progetto da
sempre (`State.md:82`, `:144`, `:951-952`; `AGENTS.MD:683`). Senza di esso il
criterio sarebbe cieco all'ordine — l'invariante di conservazione è un multiset,
e un IR 2 perfetto e uno pessimo lo passano identici.

**Regola di pass/fail**: il giro regge se **zero** pagine presentano E-A e
**zero** presentano E-B. Errori di segmentazione in paragrafi si contano e si
riportano, ma non fanno fallire: v0 non ha titoli, callout né tabelle, e
giudicarlo su quelli significherebbe giudicarlo su un compito che non ha.

## 3. Escluso dal giudizio, dichiarato prima

**Il rumore da note d'asset** sulle pagine ricche di arredo. La rimozione
dell'arredo è dichiarata fuori perimetro (`Proposta_IR2Minima_v3.md` §6,
document-level), e far fallire questo stadio per una causa che non gli appartiene
sarebbe scorretto. Il numero di note si riporta, non concorre al pass/fail.

**L'assenza di titoli.** Decisione presa: v0 senza titoli, il criterio dei titoli
è milestone sua. Una pagina in cui un titolo esce come paragrafo **non** è un
errore ai fini di questo criterio.

## 4. Il campione

**Regola di estrazione, fissata qui e implementata in
`scripts/sample_ir2_verification_pages.py`:**

- **10 pagine**, da **almeno 4 manuali differenti**;
- estratte **uniformemente** dall'unione di tutte le pagine dei 16 manuali del
  corpus, pool **non condizionato**;
- **seed `20260818`**, dichiarato qui prima dell'estrazione;
- **escluse per costruzione** le pagine di sviluppo, cioè quelle già guardate
  mentre il meccanismo veniva costruito: DB idx 98 (p.99), DB idx 17 (p.18),
  Dag idx 83 (p.84), DB idx 52 (p.53), DrW idx 96 (p.97), Dag idx 163 (p.164),
  DB idx 49 (p.50);
- una pagina estratta che **non superi le guardie** dei producer (`rotation != 0`,
  `mediabox != cropbox`) o che **non contenga testo** viene scartata e sostituita
  dall'estrazione successiva; il numero di scarti si riporta;
- se le 10 pagine coprissero **meno di 4 manuali**, si continua a estrarre finché
  4 sono coperti, e l'estensione si riporta.

Le pagine di sviluppo **non fanno parte del campione** e non concorrono al
giudizio. `State.md` registra due volte su questo progetto la differenza fra
campione di sviluppo e campione cieco, e in un caso il secondo ha falsificato il
primo.

## 5. La domanda, fissata prima che il render esista

All'utente, su ciascuna pagina, con il render accanto:

> **Leggendo il Markdown, riconosci la pagina?** Cioè: il testo c'è tutto,
> è nell'ordine in cui lo leggeresti, e ogni immagine tolta è nominata dove
> stava.

Le tre parti corrispondono a E-A, E-B e alla nota d'asset. La terza si riporta ma
non fa fallire (§3).

## 6. Ordine delle operazioni, vincolante

1. Questo file e lo script vengono committati. *(fatto in questo commit)*
2. Il campione viene estratto e **le 10 pagine vengono scritte a verbale**.
3. Le pagine di riferimento per E-B vengono **trascritte a mano** — dall'utente,
   non dalla pipeline — e messe a verbale prima di eseguire lo stadio su di esse.
4. Solo allora l'implementazione viene eseguita sul campione e giudicata.

Invertire 3 e 4 renderebbe E-B una lettura post-hoc, che è il difetto che
`AGENTS.MD` §Regole operative punto 15 vieta esplicitamente.

## 7. Riserva dichiarata

**La trascrizione a mano è costosa e ne serve una per ogni pagina del campione.**
Se il costo risultasse insostenibile, la risposta **non** è ridurre E-B a un
confronto automatico contro la pipeline stessa — sarebbe di nuovo un criterio che
non può fallire. È ridurre il numero di pagine trascritte, dichiarandolo, e
accettare che il potere statistico ne risenta come è stato dichiarato per il
campione cieco di Milestone 37.
