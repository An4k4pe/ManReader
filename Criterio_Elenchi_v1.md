# Criterio — gli elenchi, con il marcatore desunto dal manuale

**Scritto prima di implementarlo.** Le barre del §5 sono fissate qui.

## 0. Che cosa deve chiudere, e che cosa ho già visto

Un elenco oggi esce come **un paragrafo solo**. Da FWK p.118, testuale:

```
*	 Fumante, sudata, calda. *	 Logora, malaticcia, disperata. *	 Di una
bellezza incredibile e idealizzata. *	 Incolta e selvaggia.
```

Quattro voci schiacciate su una riga, con il marcatore e la tabulazione lasciati
in mezzo al testo. `State.md` conta gli elenchi 4 su 20 del difetto misurato, ed
è il secondo per frequenza dopo la coppia etichetta-valore.

**Che cosa ho già misurato, e va dichiarato perché nessuno creda che questo
criterio sia scritto alla cieca.** 16 manuali, 20 pagine ciascuno, 17714 righe
sorgente. Il carattere che apre un elemento d'elenco **cambia da manuale a
manuale**, e spesso non è punteggiatura ma il codepoint di un font di simboli:

| carattere | manuali | righe |
| --- | --- | ---: |
| `✦` U+2726 | DB | 312 |
| `*` U+002A | DIE, FWK | 136 |
| `•` U+2022 | Dag, FW, FWK | 101 |
| `\x8b` U+008B | BoB | 53 |
| `\x90` U+0090 | BiD | 49 |
| `!` `@` `#` | DrM | 45 ciascuno |
| `¥` `£` `®` | DrW | 41 |
| `↳` U+21B3 | Apo, Vil | 20 |

> **Una lista cablata tipo `•*-` prenderebbe 3 manuali su 16.** È la ragione per
> cui questo criterio non ha un elenco di caratteri, e applica
> `AGENTS.MD` §soglie: la quantità si desume dal documento.

So anche che il discriminante del §1 **separa** sul materiale visto: i marcatori
stanno al 100% di occorrenze a inizio riga, mentre `!` di DrM sta al 60% e `®` di
DrW al 50% e cadono da soli. Non so — ed è ciò che questo criterio mette alla
prova — se separi anche dove non ho guardato, né se togliere il marcatore sia
lecito su tutti i casi.

## 1. La regola

### La misura, che non decide

Per ogni documento e per ogni carattere **non alfanumerico e non spazio**: quante
righe apre, e quante volte compare in tutto il testo. Nient'altro, nessuna
soglia. Sta in un modulo suo, come `document_text_recurrence_measurements`.

### La politica, che decide

> Un carattere è **marcatore d'elenco di quel documento** se:
>
> 1. è non alfanumerico e non spazio;
> 2. le sue occorrenze **a inizio riga** sono la **maggioranza** delle sue
>    occorrenze nel documento;
> 3. almeno **due righe dello stesso blocco sorgente** si aprono con esso.
>
> Righe consecutive dello stesso blocco che si aprono con un marcatore formano un
> **elenco**, una voce per riga.

**Nessun numero arbitrario, e va difeso punto per punto.** La *maggioranza* del
punto 2 non è tarata: è la soglia naturale fra «questo carattere vive a inizio
riga» e «questo carattere vive nel testo», ed è ciò che scarta `(` e `"`, che
aprono righe ma vivono in mezzo alle frasi. Il *due* del punto 3 non è tarato
nemmeno lui: è il minimo che fa di un elenco un elenco, e serve a impedire che un
carattere raro qualifichi con una riga sola e una occorrenza sola, cioè al 100%.

**Niente vincolo di spazio dopo il marcatore**, ed è misurato: DB scrive
`✦Effetto Pieno:` e Apo `↳Lisette, la viaggiatrice.` senza spazio, mentre BoB e
DrM usano una tabulazione. Richiedere lo spazio perdeva DB e Apo.

**Un carattere può essere marcatore *e* punteggiatura nello stesso manuale**, e
l'ho guardato prima di fissare la regola invece di scoprirlo dopo. Su DrM `!`
apre 45 righe come marcatore — `!\t 5 fire damage; m<1] weakened (save ends)` —
e compare in mezzo ad altre 29 come punto esclamativo vero: `Take Point!`,
`Advance!`, `I Am Fire! I Am Death!`. Sta al 60%, passa la maggioranza, ed è
**giusto** che passi: la regola tocca il carattere **solo a inizio riga dentro un
elenco**, e i punti esclamativi in mezzo alle frasi non li vede nemmeno.

È anche la ragione per cui il punto 2 dice «maggioranza» e non «tutte»: una
soglia al 100% avrebbe perso DrM, che è il manuale con i marcatori più strani —
`!`, `@` e `#`, tre in un manuale solo.

## 2. Che cosa succede al marcatore

> Il marcatore **esce dal testo** e la voce diventa `- `. Il carattere tolto va
> nel canale review, come tutto il resto: non viene distrutto, viene spostato.

È lo stesso trattamento dell'arredo — un elemento tipografico sostituito da ciò
che rappresenta — e l'utente l'ha già approvato per quel caso.

**Perché non tenerlo.** Tenerlo darebbe `- *	 Fumante, sudata, calda.`, che oltre
a essere illeggibile è **ambiguo per Markdown**: un `-` seguito da `*` e una
tabulazione può essere letto come elenco annidato. Un marcatore tenuto non è
neutro, è un secondo difetto.

**Il caso che può far cadere questa scelta, nominato prima di provarla.** Su FW
18 righe si aprono con `…`, e sono **contenuto**, non un marcatore:

```
… trascura doveri, responsabilità, obblighi.
… va su tutte le furie.
```

L'ellissi continua la frase della riga precedente. Passa il discriminante del §1 —
18 occorrenze su 18 a inizio riga — e toglierla lascerebbe `- trascura doveri`,
che ha perso il legame con ciò che lo precede. **Questo caso deve stare nel
campione**, ed è la ragione per cui il §5.A è a zero.

## 3. Il campione

**12 voci** con seed **`20260912`**, dichiarato qui, dai **dieci manuali mai
spesi** per questo lavoro. Un'unità campionata è **un elenco**, non una riga: è
ciò che la regola produce.

**Più i due casi nominati sopra, inclusi d'ufficio e non a sorteggio**: le righe
`…` di FW, e un elenco di DB (`✦`, il marcatore senza spazio). Sono i due casi
che so poter rompere la regola, e un campione che potesse non pescarli
misurerebbe la regola dove è comoda. Si contano **separati** dalle 12, perché non
sono estratti a caso e sommarli gonfierebbe il campione.

## 4. Come si giudica

Un agente cieco sull'esito atteso etichetta ogni voce; l'utente vede le contestate
più un terzo delle altre, sorteggiate con seed **`20260913`**, dichiarato qui.

Valgono le tre correzioni al protocollo di `Criterio_NumeroDedotto_v1.md` §4:
seed dichiarati prima, nessuna voce pre-decisa dall'utente prima di essergli
sottoposta, e **un dubbio in prosa è un `incerto`**.

Le etichette per questo criterio sono tre:

- **elenco** — le righe sono voci di un elenco e il marcatore è tipografia;
- **non elenco** — non è un elenco, o il carattere tolto era contenuto;
- **incerto**.

## 5. Pass/fail

### A. Veto di contenuto — cade a una sola voce

> Cade se **una sola voce** è giudicata `non elenco`, cioè se il carattere tolto
> portava significato o se le righe non erano un elenco.

Zero, per la ragione di sempre: l'errore è perdita di contenuto, e un carattere
tolto dal corpo è invisibile a chi legge. Il caso `…` di FW è nel campione
d'ufficio proprio per poterlo far cadere.

**Se cade solo sul caso `…`**: la regola non si butta, si cambia la politica del
§2 — il marcatore si **tiene** invece di essere tolto — e si rigiudica. Sono due
decisioni separate e vanno tenute separate: *dove sta un elenco* e *che fare del
marcatore*.

### B. Pavimento — quante righe smette di schiacciare

> Si contano le righe sorgente che si aprono con un marcatore e che oggi
> finiscono **dentro un paragrafo** insieme ad altre. La regola deve trasformarne
> in voci d'elenco almeno **tre quarti**.

Stessa barra dell'arredo, e per la stessa ragione: senza un pavimento la regola
nulla — non riconoscere nessun marcatore — passerebbe il veto a pieni voti,
perché non toglie niente e quindi non sbaglia niente. È il difetto che ha fatto
cadere la v2 dell'arredo.

### C. Veto di falso positivo — sui manuali, non sul campione

> Si stampano i marcatori trovati **per ognuno dei 16 manuali** e si guardano. Cade
> se la regola dichiara marcatore un carattere che nel manuale è punteggiatura.

**Il modello nullo, e ha i denti**: «ogni riga che comincia con un carattere non
alfanumerico è una voce d'elenco». Prenderebbe `"` — 151 righe su **12 manuali** —
e `(` su 11, che sono virgolette aperte e parentesi, non elenchi. Se il modello
nullo passasse questa barra, la barra sarebbe finta e il criterio va riscritto.

### D. La giunzione

> Per ogni elenco prodotto si guarda il paragrafo immediatamente **sopra e
> sotto**. Cade se il testo attorno si legge peggio di prima.

Stessa clausola dell'arredo, stesso strumento
(`scripts/check_furniture_junction.py`, che confronta due rese del prototipo).
Qui ha un bersaglio in più: la riga che **introduce** l'elenco — `• Comunica al
Mondo:` — non deve finire inghiottita nella prima voce.

### E. Il confronto E-B va emendato, e l'emendamento è dichiarato qui

`Criterio_UscitaIR2Minima_v2.md` E-B confronta i caratteri non-spazio dell'uscita
IR 2 con la base. **Togliere il marcatore lo rompe per costruzione.**

> L'emendamento: dal confronto si tolgono, **da entrambi i lati**, i marcatori
> che la politica ha dichiarato per quel documento.

È la stessa forma dell'emendamento già a verbale in
`Criterio_ParagrafoDaRiga_v1.md` §3 per la deidratazione del trattino — «un
trattino è un carattere non-spazio e riunire una parola lo cambia
legittimamente». Il precedente esiste, e questo criterio lo cita invece di
inventarsi un'eccezione.

**Se l'emendamento non basta** — cioè se dopo averlo applicato E-B fallisce
ancora — è un difetto della regola e non del confronto, e la regola si ferma.

## 6. Che cosa resta fuori

- **Elenchi annidati.** Un marcatore diverso a un rientro diverso è un elenco
  dentro un elenco; qui tutte le voci stanno allo stesso livello. Il rientro c'è
  nelle primitive e si potrà usare dopo.
- **Elenchi numerati** (`1.`, `a)`). Il discriminante del §1 non li vede, perché
  la cifra è alfanumerica e cambia a ogni voce. Servono un'altra misura.
- **La riga che introduce l'elenco** non diventa un titolo: resta il paragrafo che
  è. Promuoverla sarebbe la stessa invenzione che `markdown_builder` fa già e che
  IR 2 esiste per non fare.
- **I titoli**, che restano paragrafi. È un difetto visibile e vero — `Capitolo 6`
  e `**Cavaliere del Drago**` escono come prosa — ma è un fascicolo suo.
- **La coppia etichetta-valore**, che `State.md` mette al 69% del difetto
  misurato ed è il pezzo più grande ancora aperto.

## 7. Debiti

Il codice che produce la tabella del §0 va committato **con** il criterio:
`AGENTS.MD` §18, e questo debito è già stato iscritto due volte e pagato tardi
una volta.
