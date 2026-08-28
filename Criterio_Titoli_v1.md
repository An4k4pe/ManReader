# Criterio — i titoli, dalla dimensione del carattere e non dalle maiuscole

**Scritto prima di implementarlo.**

## 0. Che cosa deve chiudere, e l'errore che non va rifatto

Oggi i titoli escono **come prosa**: `Capitolo 6`, `**Cavaliere del Drago**`,
`creare un agente`. `Esito_Elenchi_v1.md` lo registrava, e
`Esito_ElencoNumerato_v1.md` ha mostrato che è la causa di **sette righe mancate**
su ventidue — titoli di sezione numerati che nessun meccanismo può prendere
finché la resa a titolo non esiste.

**L'errore da non rifare è scritto nel repo.** `markdown_builder._is_heading_text`
«promuove a titolo qualunque testo corto in maiuscolo **prima ancora di guardare
lo stile**», e sulla base di DB p.99 questo ha promosso a titolo una testatina
corrente. IR 2 esiste anche per non rifarlo.

> Questo criterio guarda **lo stile per primo**: la dimensione del carattere. Le
> maiuscole non compaiono nella regola.

## 1. La regola

**La misura**: la dimensione del **corpo** del documento è quella più frequente
**pesata per caratteri** — la stessa forma di `ir2_builder.body_font`, che pesa
per caratteri e non per primitive perché un font di titolo ha poche primitive
lunghe.

> Una riga sorgente è un **titolo** se:
>
> 1. la sua dimensione è **maggiore** di quella del corpo;
> 2. il suo blocco **non contiene nessuna riga alla dimensione del corpo**;
> 3. il suo blocco ha **al più due righe** non vuote;
> 4. il suo testo è **più lungo di un carattere**;
> 5. non è già escluso dal corpo come **arredo**.
>
> Il **livello** è il rango della sua dimensione fra quelle sopra il corpo del
> documento, dalla più grande: `#`, `##`, `###`… fino a `######`.

**Ogni condizione ha il suo fatto misurato, e nessuna è una taratura.**

- La **2** viene da Apo e Vil: il blocco del titolo contiene **anche la
  testatina** — `S E C O N D O AT TO` a 7,5 accanto a `Introduzione` a 46,4 — e
  chiedere che *tutte* le righe stiano sopra il corpo perdeva i titoli di quei due
  manuali. Chiedere che *nessuna* stia **al** corpo li recupera: 0 titoli
  diventano 3 su Vil.
- La **3** è «un titolo è un blocco suo, al più con un a capo». Su DrM ha portato
  i candidati da 130 a 53.
- La **4** sono i **capilettera**: su Fab `3`, `n`, `W` a corpo 30 sono la prima
  lettera ingrandita di un paragrafo. Un carattere solo non è un titolo, ed è un
  fatto e non una soglia.
- La **5** toglie i numeri di pagina, che in molti manuali sono **più grandi del
  corpo** — `152` su BiD, `216` su BoB, `[209]` su Lan — e che sono già arredo. È
  la ragione per cui questo stadio va **dopo** la politica dell'arredo e non prima.

**Il livello è un rango, non una soglia.** Non c'è una dimensione minima per `#`:
il documento ha le sue, si ordinano, e il rango è il livello. Un documento con
otto dimensioni sopra il corpo collassa le ultime su `######`, che è quanto
Markdown ha.

## 2. Che cosa NON entra nella regola, e perché

**Le maiuscole**, per la ragione del §0. **Il grassetto**, che questo progetto
rende già come grassetto e che su FWK marca `**Cavaliere del Drago**`: promuoverlo
a titolo sarebbe di nuovo dedurre la struttura dalla decorazione. **Il font**:
misurato, su alcuni manuali il titolo è nello stesso font del corpo.

## 3. Il difetto che so già di avere, e che va dichiarato prima

Sui manuali **densi di schede** la regola **sovraproduce**, e la causa non è la
regola:

| manuale | corpo misurato | candidati |
| --- | ---: | ---: |
| Kul | 8,0 | 88 |
| Wil | 10,0 | 63 |
| DrW | 7,5 | 58 |
| DrM | 7,5 | 53 |
| **Apo** | 11,6 | **3** |
| **Vil** | 11,6 | **3** |

Su DrM e DrW il corpo misurato è **7,5**, che non è la prosa: è il **testo di
scheda**, che in quei manuali è la maggior parte dei caratteri. La prosa sta a
10-12, cioè «sopra il corpo», e la regola la promuove a titolo.

> **È la terza volta in questo giro che le schede mostro fanno cadere un
> meccanismo**, e sempre per la stessa ragione: dentro una scheda le convenzioni
> tipografiche della prosa non valgono. `column_band` ne emetteva quattro colonne,
> gli elenchi ne facevano voci dai gradini di un tiro, e ora la dimensione del
> corpo la decidono loro.

Questo criterio **non prova a risolverlo**: lo misura e lo riporta. Il §5.B ne fa
una barra esplicita, così che il verdetto non lo nasconda dietro una media.

## 4. Il campione

**16 titoli riconosciuti** e **16 righe scartate che stanno sopra il corpo**,
estratti con seed **`20260926`**, dichiarato qui, da **tutti** i manuali che ne
producono, **dopo** l'esclusione dell'arredo.

Le due metà servono a cose diverse: la prima misura se promuove a torto, la
seconda se manca titoli veri. Il giro precedente ha mostrato che **l'errore stava
tutto nella seconda metà**, e un campione delle sole riconosciute avrebbe detto
«regge».

**Il materiale si costruisce dalla resa.** Per ogni voce si mostra la riga, il suo
livello proposto, e il paragrafo che la segue.

## 5. Pass/fail

### A. Veto — cade a una sola riga, in entrambe le direzioni

> Cade se **una sola** riga promossa a titolo non è un titolo, o se **una sola**
> riga scartata lo era.

Etichette: **titolo**, **non titolo**, **incerto**. Giudizio come
`Criterio_NumeroDedotto_v1.md` §4, seed di controllo **`20260927`**.

**Il canale `incerto` è la parte del protocollo che va rinforzata.** Tre giri di
fila l'etichettatore ha dato etichette nette e ha messo la riserva **in prosa** —
sull'arredo, sugli elenchi, sui numerati, e ogni volta erano proprio le voci che
decidevano. Il materiale di questo giro lo dirà in modo più forte: **una riserva
scritta accanto a un'etichetta netta viene contata come `incerto`**, non come
l'etichetta.

### B. La dispersione per manuale, che non si nasconde dietro la media

> Si riporta il numero di titoli **per manuale**, e il verdetto cita
> esplicitamente i quattro manuali densi di schede.

Non è una barra pass/fail: è un obbligo di riporto. Una media che desse «regge»
mentre Kul produce 88 titoli su dieci pagine sarebbe un verbale falso.

### C. La giunzione

> Per ogni titolo prodotto si guarda il paragrafo sopra e sotto. Cade se il testo
> attorno si legge peggio di prima.

Qui ha un bersaglio preciso: un titolo promosso **in mezzo a un paragrafo** lo
spezzerebbe in due, ed è il danno peggiore di questo meccanismo.

### D. Regressione

> Le barre già in piedi non devono peggiorare: `check_list_regression.py` e
> `check_numbered_lists.py` danno lo stesso risultato di prima.

### Se cade

- **A**, verso «promossa e non lo era»: la regola è troppo larga. Non si stringe a
  occhio nello stesso giro.
- **A**, verso «scartata e lo era»: si riporta quanto manca.
- **B** con numeri come quelli del §3: il fascicolo non sono i titoli, sono **le
  schede mostro come categoria**, e va aperto quello.

## 6. Che cosa resta fuori

- **Le schede mostro come categoria** (§3), che tre meccanismi di fila indicano.
- **I titoli di sezione numerati** di `Esito_ElencoNumerato_v1.md` §3: se questo
  criterio regge, quelle sette righe diventano titoli e la copertura del numerato
  si chiude da sé. **Non è una barra di questo criterio** — sarebbe misurare due
  cose insieme — ma è la ragione per cui vale la pena farlo ora.
- **La gerarchia**: i livelli vengono dal rango delle dimensioni, non da un
  albero. Un `###` dopo un `#` senza `##` in mezzo è possibile e non si corregge.

## 7. Debiti

Il codice che produce le tabelle del §0 e del §3 va committato **con** il
criterio.
