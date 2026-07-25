# ManReader — Workflow Chat A, Chat B e Zed agent

## Versione: 2.0

Documento comune per progettazione, diagnostica, implementazione e revisione del progetto ManReader.

L'obiettivo è mantenere una sola linea decisionale, impedire refactor non progettati e usare Zed agent solo su task implementativi già definiti.

## 1. Due modalità di lavoro

### Modalità P — progettazione globale

Usare quando il problema riguarda:

- architettura complessiva;
- confini dei moduli;
- refactor di più sottosistemi;
- modello dati;
- workspace;
- profili;
- GUI;
- AI locale;
- strategia di migrazione;
- scelte tecnologiche.

In questa modalità:

- non si preparano commit funzionali;
- Zed agent non riceve task progettuali;
- Chat A produce la proposta;
- Chat B la revisiona criticamente;
- le decisioni vengono consolidate in un documento;
- `State.md` viene aggiornato quando cambia la fase.

### Modalità I — implementazione incrementale

Usare solo dopo che l'architettura o il comportamento richiesto sono stati approvati.

In questa modalità:

- ogni task ha un solo obiettivo;
- i file ammessi e vietati sono espliciti;
- sono obbligatori test, diff e stato git;
- Chat A decide se committare;
- Zed agent non fa commit.

## 2. Ruoli

### Chat A — fonte decisionale

In Modalità P:

- guida la progettazione;
- definisce obiettivi e non-obiettivi;
- integra benchmark e vincoli;
- decide le alternative;
- produce il documento architetturale;
- integra o rifiuta le osservazioni di Chat B;
- dichiara quando la progettazione è sufficientemente matura.

In Modalità I:

- identifica il livello del problema;
- restringe lo scope;
- prepara il task finale;
- revisiona diff, test e output;
- decide accettazione o rifiuto;
- autorizza il commit, che resta eseguito dall'utente.

Chat A è sempre la fonte di verità.

### Chat B — analisi e revisione indipendente

Chat B può avere due incarichi distinti.

#### B-Diagnostica

- analizza log, output, PDF, IR e diff;
- verifica ipotesi;
- produce dati e casi sintetici;
- non decide il commit.

#### B-Architettura

- revisiona criticamente la proposta di Chat A;
- cerca complessità inutile, failure mode e incoerenze;
- propone semplificazioni;
- distingue decisioni bloccanti da decisioni rinviabili;
- non sostituisce Chat A e non avvia implementazione.

Chat B non deve limitarsi a confermare la proposta.

### Zed agent — esecutore

Zed agent:

- modifica solo i file autorizzati;
- lavora su task già ristretti;
- non decide l'architettura;
- non allarga lo scope;
- non fa commit;
- mostra diff, test e stato finale.

Un refactor può essere ampio nel risultato complessivo, ma ogni step affidato all'agent deve essere previsto dal piano approvato e rimanere verificabile.

## 3. Regole permanenti

- leggere sempre `State.md` e `AGENTS.MD`;
- elaborazione locale, nessun cloud obbligatorio nel core;
- nessuna invenzione del contenuto mancante;
- niente hardcode su manuale, pagina, filename, titolo o parola come soluzione primaria;
- output generati non committati;
- niente `git add .`;
- nessun commit automatico;
- dipendenze nuove solo con motivazione;
- Ruff, BasedPyright e test obbligatori per i commit di codice;
- builder e GUI non devono reinterpretare direttamente il PDF;
- AI locale opzionale e vincolata da contratti dati;
- profili e decisioni devono essere persistenti e tracciabili.

La regola storica “niente refactor aggressivi” diventa:

> nessun refactor ampio non progettato; i refactor approvati sono ammessi solo con piano di migrazione, compatibilità e commit scomposti.

## 4. Flusso Modalità P

1. Chat A legge fonti, benchmark e codice rilevante.
2. Chat A produce una proposta strutturata.
3. Chat B esegue una revisione indipendente.
4. Chat A integra le osservazioni e registra le decisioni.
5. Le decisioni ancora aperte vengono classificate:
   - bloccanti;
   - rinviabili;
   - sperimentali.
6. Si definiscono criteri di uscita dalla progettazione.
7. Si aggiornano `State.md`, `AGENTS.MD` e questo workflow se necessario.
8. Solo allora si prepara il piano di migrazione.
9. Il primo commit deve essere strutturale, limitato e senza cambio funzionale salvo decisione esplicita.

Output della Modalità P:

- documento architetturale;
- decision record;
- schema dati;
- piano di migrazione;
- piano test;
- rischi e rollback;
- primo micro-step approvato.

## 5. Flusso Modalità I

1. Analizza log, diff e output.
2. Identifica il vero livello del bug.
3. Conferma una regressione o un requisito approvato.
4. Definisci uno scope singolo.
5. Prepara test e criteri di accettazione.
6. Affida il task a Zed agent o implementalo manualmente.
7. Revisiona diff, test e output reale.
8. Rispondi con:
   - `ACCETTA E COMMITTA`;
   - `NON COMMITTARE: correggere questi punti`;
   - `SCOPE TROPPO LARGO: dividere in sotto-task`.
9. Aggiorna `State.md` a fine milestone o cambio di fase.

## 6. Quando non usare Zed agent

Non affidare all'agent task come:

- progetta la nuova architettura;
- rendi universale il layout;
- scegli la GUI;
- definisci il profilo dei manuali;
- refactor completo di `extractor.py`;
- sistema tutti i callout;
- migliora genericamente le tabelle.

Prima devono esistere:

- decisione approvata;
- interfacce;
- file coinvolti;
- comportamento atteso;
- strategia di compatibilità;
- test.

## 7. Template Chat A — progettazione

```text
Sei Chat A Architettura per ManReader.

Leggi State.md, AGENTS.MD e le fonti del benchmark.

Non modificare codice.
Non preparare commit.
Non usare Zed agent.

Compito:
- definire il problema e i non-obiettivi;
- proporre alternative;
- confrontarle con i campioni reali;
- definire dati, moduli, persistenza e workflow;
- indicare rischi e decisioni bloccanti;
- produrre un documento sottoponibile a Chat B.

Output:
1. visione;
2. principi;
3. pipeline;
4. modelli dati;
5. persistenza;
6. GUI/CLI;
7. AI;
8. migrazione;
9. test;
10. decisioni aperte.
```

## 8. Template Chat B — revisione architetturale

```text
Sei Chat B Revisione Architetturale per ManReader.

Non modificare codice.
Non preparare commit.
Non limitarti a confermare Chat A.

Compito:
- revisionare la proposta;
- cercare complessità, coupling, failure mode e rischi di migrazione;
- verificare compatibilità con benchmark e vincoli;
- proporre semplificazioni;
- classificare le decisioni bloccanti.

Output:
A. punti solidi;
B. criticità;
C. failure mode;
D. semplificazioni;
E. decisioni bloccanti;
F. architettura minima sufficiente;
G. verdetto.
```

## 9. Template Zed agent — implementazione

```text
Leggi prima State.md e AGENTS.MD.

Non fare commit.

Obiettivo:
[un solo obiettivo concreto già approvato]

Decisione architetturale di riferimento:
[documento/sezione]

File ammessi:
- [file]

Non toccare:
- [file]
- output/
- workspace generati
- file diagnostici

Richiesta:
1. [azione]
2. [azione]
3. [azione]

Compatibilità:
- [comportamento legacy da preservare]
- [schema o interfaccia da non rompere]

Test:
- ruff check [file]
- basedpyright [file]
- python -m unittest [test mirati]
- python -m unittest

Prima di riportare l'esito:
- git add -- [file ammessi elencati sopra] (mai `git add .`, mai file fuori lista)
- git diff --cached --stat
- git diff --cached

Accettazione:
- [criterio verificabile]
- nessun hardcode;
- nessuna regressione nota;
- mostra `git add`/`git diff --cached` come sopra, test e `git status --short`.
```

File nuovi (mai tracciati) non compaiono in `git diff` semplice: senza `git add` esplicito sui soli file ammessi, Chat A non ha un diff reale da rivedere e deve rileggere i file interi, più lento e più soggetto a distrazioni. Lo staging richiesto qui è solo locale, per generare un diff leggibile: non è un commit e non sostituisce la regola permanente "niente `git add .`" né "nessun commit automatico" (§3) — resta vietato aggiungere file fuori dalla lista "File ammessi".

## 10. Review diff in Chat A

Fornire:

```text
git status --short
git diff --stat
git diff -- [file]
git diff --cached --stat    (se i file sono nuovi/staged da Zed agent, §9)
git diff --cached           (se i file sono nuovi/staged da Zed agent, §9)

Test eseguiti:
[...]

Run manuale:
[...]

Output/controlli:
[...]

Dubbi:
[...]
```

Chat A decide. L'utente esegue il commit.

## 11. Aggiornamento delle fonti

Aggiornare `State.md`:

- a fine milestone;
- quando cambia la fase;
- quando una decisione architetturale diventa vincolante;
- prima di aprire una nuova Chat A che deve ripartire da un contesto pulito.

Aggiornare `AGENTS.MD` quando cambiano:

- responsabilità permanenti dei moduli;
- regole AI;
- qualità e toolchain;
- vincoli di implementazione;
- pipeline target approvata.

Aggiornare questo workflow quando cambiano:

- ruoli Chat A/Chat B;
- passaggio progettazione/implementazione;
- uso di Zed agent;
- criteri di review.
