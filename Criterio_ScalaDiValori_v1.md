# Criterio — la scala di valori, e il blocco come unità di decisione

**Scritto prima di implementarlo.** Le barre del §4 sono fissate qui.

## 0. Che cosa deve chiudere

`Esito_Elenchi_v1.md`: il veto degli elenchi è caduto **9 voci su 14**, e le
cause sono tre. Questo criterio ne affronta **due**, e dichiara al §5 le altre.

| causa | voci | che cos'è |
| --- | ---: | --- |
| **scala di valori** | 6 | DrM: `!` `@` `#` sono `≤11`, `12-16`, `17+` |
| **glifo singolo** | 1 | DB: `✦ Punti Volontà: 3`, una riga per riquadro |
| subordinazione persa | 1 | FWK: sotto-opzioni appiattite — **fuori** |
| ellissi che continua la frase | 1 | FW `…` — **fuori** |

**L'errore di fondo, e non è una taratura.** La regola degli elenchi decide il
marcatore a livello di **documento** e poi marca **ogni** riga che si apre con
esso. Ma «questo carattere apre voci d'elenco *in questo manuale*» non implica
«queste righe *qui* sono un elenco».

> **Il documento dice quali caratteri sono candidati. Il blocco dice se questa
> occorrenza è un elenco.** È lo spostamento dell'unità di decisione, ed è la
> cosa che questo criterio propone.

**Che cosa ho già visto, dichiarato perché nessuno creda che sia scritto alla
cieca.** Su DrM p.182 i tre glifi stanno nello **stesso blocco** `b0004`, uno
ciascuno, sempre in quest'ordine:

```
!	 5 fire damage; m<1] weakened (save ends)
@	 9 fire damage; m<2] weakened (save ends)
#	 11 fire damage; m<3] weakened (save ends)
```

Sono in `DrawSteelGlyphs-Regular`. Non so — ed è ciò che questo criterio mette
alla prova — se la firma regga fuori da DrM, né se non spezzi gli elenchi veri.

## 1. La regola

La misura resta quella di `document_line_start_measurements`: quali caratteri
sono **candidati** in questo documento. Cambia che cosa se ne fa.

**L'unità è la corsa**, non il blocco: una sequenza massimale di righe che si
aprono con un candidato e che stanno **nello stesso blocco o in blocchi
consecutivi**.

> - **Scala di valori** — un blocco con due o più caratteri **distinti**,
>   ciascuno **una volta sola**, e la stessa tupla ordinata ricorre in **almeno un
>   altro blocco** del documento. Si guarda **per prima**, e un carattere che è
>   gradino di una scala **non è un marcatore in tutto il documento**.
> - **Elenco** — una corsa di **due o più** righe con lo **stesso** carattere.
> - **Né l'uno né l'altro** — tutto il resto, e in particolare una corsa di **una
>   riga sola**.
>
> Solo il secondo caso produce un elenco. Negli altri due il glifo **resta nel
> testo** e le righe restano paragrafi.

### Perché il gradino esce da tutto il documento, non solo dal suo blocco

**Emendamento scritto durante l'implementazione e prima del giudizio**, e va
dichiarato invece che infilato. La prima stesura toglieva i glifi di scala **solo
nei blocchi dove la scala compare per intero**. Non basta, misurato: su DrM una
pagina di minion ha **sei blocchi consecutivi con un solo `!` ciascuno** — il
tier `≤11` di sei creature diverse. Ognuno è una firma `('!',)`, che non è una
scala; ma sono blocchi consecutivi con lo stesso carattere, quindi la regola
delle corse ne farebbe **un elenco di sei voci**. È esattamente la voce 09 del
giudizio precedente, dove `2 damage` compare due volte senza che si capisca di
chi sia.

Se un carattere è gradino di una scala **da qualche parte** nel documento, in
quel documento porta valore, e non lo si promuove a pallino altrove.

Nota che la regola delle corse **da sola** già copre il caso della scheda intera:
`!`, `@`, `#` sono caratteri diversi, non fanno corsa fra loro, e tre corse di una
riga non sono elenchi. La firma serve al caso del minion, non a quello che l'ha
suggerita.

### Perché la corsa e non il blocco, e come l'ho scoperto

La prima stesura di questo criterio diceva «due o più righe **dello stesso
blocco**». Poi ho eseguito la misura del §6 su DB, e l'ha **refutata**: DB ha 312
blocchi che portano `✦`, **uno per blocco**, quindi la condizione avrebbe
dichiarato che DB non ha nessun elenco. È **esattamente la condizione che ha fatto
cadere `Criterio_Elenchi_v1.md`**, e la stavo rimettendo con un altro nome.

Guardate le pagine, i due casi si separano da soli:

| DB idx 60 — **elenco vero** | DB idx 13 — **righe di costo** |
| --- | --- |
| `✦Istantaneo:` (b0015) | `✦Punti Volontà: 3` (b0001) |
| `✦Round:` (b0016) | *sei righe di prosa, b0001* |
| `✦Intervallo:` (b0017) | `CAPACITÀ: SCONTROSO` (b0002) — **nessun marcatore** |
| `✦Periodo:` (b0018) | `✦Punti Volontà: —` (b0003) |
| `✦Concentrazione:` (b0019) | |

A sinistra i blocchi marcati sono **consecutivi**; a destra fra i due c'è un
blocco che non porta marcatore. Non serve contare le righe in mezzo — sarebbe una
soglia — basta guardare se la catena dei blocchi si interrompe.

Su FWK invece la corsa sta **dentro** un blocco solo (`****`), e su FW dentro due
(`b0011`, `b0012`, una colonna ciascuno). La corsa copre entrambe le forme, il
blocco da solo ne copriva una.

**Perché «ciascuno una volta sola».** È ciò che separa una scala da un elenco
annidato. Su FWK un blocco può contenere `•` per la voce che introduce e `*` per
le opzioni: i caratteri sono distinti, ma `*` si **ripete**, e una scala non
ripete i suoi gradini. Senza questa condizione l'annidamento di FWK sarebbe letto
come una scala e si perderebbero elenchi veri.

**Perché «ricorre in almeno un altro blocco».** Una scala è una convenzione del
documento, non un caso di un blocco. Due glifi diversi capitati una volta insieme
non sono una scala; `!` `@` `#` che tornano identici pagina dopo pagina lo sono.

**Perché «una corsa di una riga sola non è un elenco».** Chiude il caso di DB:
`✦ Punti Volontà: 3` è una riga per riquadro, e la stellina marca *questa è la
riga del costo*. La regola caduta contava due righe **per pagina e per
marcatore**, quindi due riquadri con una riga ciascuno la soddisfacevano. La
corsa no: fra i due riquadri c'è un blocco senza marcatore, e la catena si
spezza.

**Nessun numero nuovo.** Il *due* di «due o più» è il minimo che fa di un elenco
un elenco e di una scala una scala; l'*una volta sola*, il *ricorre altrove* e la
*consecutività dei blocchi* sono fatti, non soglie. In particolare **non** si
conta quante righe stanno fra due marcatori: quella sarebbe una soglia, e la
catena dei blocchi risponde alla stessa domanda senza sceglierla. Il font non entra nella regola: `DrawSteelGlyphs` ha
suggerito dove guardare, ma su FWK e Dag il marcatore è nel font del corpo, e una
regola sul font avrebbe separato i manuali sbagliati.

## 2. Che cosa succede a una scala

> **Niente.** Il glifo resta dove sta, le righe restano paragrafi.

Non si rende come coppia etichetta-valore, non si traduce `!` in `≤11`, non si
costruisce una tabella. Tradurre richiederebbe di sapere che cosa il glifo
*significa* in quel manuale, e quello non è scritto da nessuna parte nel PDF:
sarebbe invenzione, la stessa che `page_label` esiste per impedire.

**Riconoscere una scala serve a non rovinarla**, e in questo giro è tutto ciò che
deve fare. Che una scala meriti una resa propria è la domanda dopo, e ha bisogno
delle schede mostro come categoria — che `State.md` e la memoria del progetto
nominano da agosto e che non esiste ancora.

## 3. Il campione

**10 blocchi classificati `elenco`** e **10 classificati `scala`**, estratti con
seed **`20260919`**, dichiarato qui, dai manuali che ne producono. Se una classe
ne produce meno di 10 si giudicano tutti e il numero effettivo si riporta.

**D'ufficio, non a sorteggio**: un blocco tier di DrM, il riquadro `✦` di DB, e
**i quattro blocchi che `Esito_Elenchi_v1.md` §5 ha giudicato `elenco` veri** —
FWK `•` (voci 03 e 10), BoB `\x8b` (voce 05), FW `•` (voce 08). Questi ultimi
sono la barra di regressione del §4.B e hanno verità di riferimento già scritta.

**Il campione si costruisce dalla resa, non dalla sorgente.** Difetto del giro
scorso: il materiale mostrava le voci troncate a fine riga fisica perché lo
costruivo dalle righe sorgente, mentre il renderer unisce le continuazioni.
L'agente l'ha notato da solo.

## 4. Pass/fail

### A. Veto — cade a un solo blocco

> Cade se **un solo** blocco classificato `elenco` non è un elenco, o se **un
> solo** blocco classificato `scala` è invece un elenco vero.

Due direzioni, entrambe a zero, perché gli errori sono simmetrici e diversi:
chiamare elenco una scala **distrugge un valore**; chiamare scala un elenco
**lascia il glifo in mezzo al testo**, che è brutto ma visibile. Il secondo è
meno grave e resta comunque a zero, perché una barra che tollerasse il verso
comodo non misurerebbe niente.

Etichette: **elenco**, **scala di valori**, **nessuno dei due**, **incerto**.
Giudizio come `Criterio_NumeroDedotto_v1.md` §4 — agente cieco, poi l'utente
sulle contestate più un terzo, seed **`20260920`** — e **un dubbio in prosa è un
`incerto`**.

### B. Regressione — i quattro elenchi veri devono restare elenchi

> I quattro blocchi che il giudizio precedente ha dichiarato elenchi veri devono
> essere ancora classificati `elenco`. Cade se anche uno solo diventa `scala` o
> `nessuno dei due`.

È la barra che impedisce di comprare la precisione perdendo tutto: una regola che
non classificasse mai `elenco` passerebbe metà del veto A a pieni voti.

### C. Copertura della scala

> Nei blocchi tier di DrM — verità di riferimento: i blocchi che contengono
> `!`, `@` e `#` — la regola deve classificare `scala` almeno **tre quarti**.

Stessa barra di tre quarti dell'arredo e degli elenchi, e non si muove.

**Il modello nullo è la regola caduta**: «ogni blocco con due o più righe che si
aprono con un candidato è un elenco». Fallisce il veto A per costruzione — è ciò
che ha prodotto le 9 cadute su 14. La barra ha i denti senza doverlo dimostrare.

**Dichiarato**: DrM è insieme il manuale su cui ho visto la firma e quello su cui
il §4.C la misura. Non è indipendente, ed è per questo che la copertura è una
barra separata dal veto: **ciò che decide è il veto A**, su blocchi sorteggiati e
giudicati da chi non sa come sono stati scelti.

### D. La giunzione

> Per ogni blocco che cambia classificazione si guarda il paragrafo
> immediatamente sopra e sotto.

`scripts/check_furniture_junction.py`, che confronta due rese del prototipo.

### Se cade

- **A**, verso «scala che era elenco»: la firma è troppo larga e la regola non si
  spedisce.
- **A**, verso «elenco che non lo era»: restano cause che il blocco non vede, e
  vanno nominate prima di toccare la regola.
- **B**: la regola compra precisione perdendo elenchi veri. Non si ritocca la
  condizione per recuperarli — si riporta quanto si è perso.
- **C**: la firma non copre le scale che doveva coprire, e le schede mostro vanno
  affrontate come categoria invece che per glifo.

## 5. Che cosa resta fuori, con la ragione

**L'ellissi di FW (`…`).** Stesso glifo ripetuto, quindi per questa regola è un
elenco, e resta una caduta. Non è una svista: `…` non è né una scala né un glifo
singolo — è **contenuto che sembra un marcatore**, e nessuna proprietà di blocco
lo vede. La sua via è il §2 del criterio degli elenchi — tenere il marcatore
invece di toglierlo — che è una decisione separata e va presa separatamente.

**La subordinazione di FWK.** Le sotto-opzioni marcate `*` sotto un esito `7-9`
si appiattiscono al livello degli esiti. Il segnale che manca è il **rientro**,
che sta nelle primitive e che nessuno guarda. È l'annidamento, ed è un fascicolo
suo.

**La resa di una scala** (§2), e **le schede mostro come categoria**.

## 6. Debiti, e uno già pagato

`scripts/measure_block_marker_signature.py` è committato **con** questo criterio,
e non è una formalità: è la misura che ha refutato la prima stesura del §1 prima
che arrivasse al giudizio. Ecco che cosa dice, ed è la firma del §0:

| manuale | firma | blocchi | distinti | ripetuti |
| --- | --- | ---: | ---: | --- |
| DrM | `!@#` | 43 | 3 | no |
| DrM | `!` / `@` / `#` | 2 / 1 / 1 | 1 | no |
| FWK | `****`, `**`, `***`, `******` | 24 | 1 | sì |
| FWK | `*****•`, `••***•` | 4 | 2 | sì |
| DB | `✦` | 312 | 1 | no |

`!@#` in 43 blocchi, tre glifi distinti senza ripetizioni, è la scala. Le firme
di FWK hanno **ripetizioni**, quindi restano elenchi anche dove i caratteri sono
due. E i 312 blocchi di DB con un `✦` ciascuno sono la riga che ha mandato a
rifare il §1.

`AGENTS.MD` §18, e su questo progetto il debito è già stato iscritto tre volte e
pagato tardi una.
