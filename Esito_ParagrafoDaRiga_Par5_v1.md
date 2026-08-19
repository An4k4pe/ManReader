# Esito del §5 di `Criterio_ParagrafoDaRiga_v1.md` — **CADUTO**

Il §5 chiedeva il giudizio a vista su DrW p.97, Dag p.164, DB p.50, DB p.53 e
DB p.99, e diceva: *«Il giro regge se non compare nessuna pagina in cui la
segmentazione peggiora.»*

**Una pagina peggiora. Il criterio non regge.**

È il primo criterio pre-registrato di questa sessione che cade, ed è caduto
facendo esattamente ciò per cui era stato scritto: la clausola era rimasta non
scaricata alla chiusura della Milestone 38, e scaricarla ha prodotto un verdetto
negativo più un difetto di contratto.

---

## 1. Il verdetto, con la pagina

**DB p.99.** Le righe degli stat block si spezzano **per campo**. Sulla pagina
`Movimento: 8   Danno Bonus: —   PF: 8` è una riga sola con tre campi affiancati;
PyMuPDF la indicizza come tre righe distinte, e la regola spezza perché `Danno` e
`PF` cominciano in maiuscolo. In uscita diventano tre paragrafi separati.

Giudizio dell'utente: *«lo stat block spezzato preferirei non lo fosse, lo rende
più complesso da leggere»*. È un peggioramento della segmentazione, quindi §5
cade.

**Cosa invece migliora, e non va perso nel verdetto**: sulla stessa pagina il box
a rientro sospeso passa da quattro frammenti con le frasi tagliate a metà a tre
voci corrette, e le parole spezzate si ricompongono (`riani- mati` →
`rianimati`, `sopravvis- suto` → `sopravvissuto`, `a PERSUADERE .` →
`a PERSUADERE.`, `COS :` → `COS:`). La regola non è sbagliata sulla prosa: è
sbagliata dove il contenuto non è prosa.

Direzione indicata dall'utente: *«probabilmente dovremmo gestire una categoria
stat block»*.

## 2. Difetto di contratto trovato scaricando il §5

Su **DB p.53** il contratto rifiutava la pagina: `node_id must be unique within a
page`. L'ordinamento a bande separa il glifo di elenco dal suo testo — il pallino
in una banda, `Arrabbiato – INT` in un'altra — quindi la riga `b0007:l0001`
compare **due volte** nell'ordine di lettura. Tre righe su quella pagina.

Corretto in `f1878cc`: il `node_id` viene dal primo primitivo, che include lo
span. **La base fa lo stesso split**: viene dall'ordinamento, non da IR 2. Il
contratto l'ha soltanto reso visibile, rifiutando la pagina invece di emetterla
malformata.

Giudizio dell'utente: il caso appartiene a `column_band`, non a IR 2.

## 3. Due difetti su DrW p.97, e sono **la stessa causa**

Segnalati dall'utente come casi distinti e incomprensibili; sono uno.

- I tre valori del Power Roll finiscono incollati alla riga che li introduce:
  `Power Roll + Presence: á 2 holy damage; push 1 é 4 holy damage; push 2 …`
- `Main action` e `o Ranged 10` si uniscono.

**Causa unica**: i glifi dei badge sono caratteri **minuscoli** per la codifica.
Le tre righe sono davvero distinte (`b0007:l0001`, `l0002`, `l0003`) e cominciano
con `á` (U+00E1), `é`, `í`; il simbolo del bersaglio è la lettera `o`. La regola
«si va a capo se la successiva non comincia in minuscola» li legge come prosa che
continua, e la riga precedente finisce con `:`, che per decisione **non termina**
— la scelta che fa funzionare `Non-Mostri:`.

L'intuizione dell'utente era giusta nella sostanza (*«il glifetto davanti doveva
proteggerle»*) e sbagliata nel meccanismo: il glifo non protegge, perché **è** una
minuscola.

La guardia elenchi del §1 copre solo trattino e cifra, e qui i marcatori sono
glifi di un font simbolico. La riserva del §6 — *«la guardia elenchi non è stata
esercitata … va trattata come non verificata»* — era ben posta: esercitata, non
copre il caso reale.

Richiesta dell'utente per DrW: mantenere i badge `≤11`/`12-16`/`17+` e i simboli
di danno **in colonna**, che è un altro argomento a favore di un consumer per gli
stat block.

## 4. Dag p.164 — non è una regressione di IR 2

L'utente segnala che `TIRI DEGLI AVVERSARI` finisce fra `VANTAGGIO E SVANTAGGIO
DEI PNG` e `VANTAGGIO VS. DIFFICOLTÀ`, e chiede perché la regressione, dato che
il caso era stato risolto con le bande.

**Verificato: la correzione esiste, funziona, ed è spenta.** Con
`--interrupt-corridor drawings` la banda si spezza sui puntini e il titolo va al
posto giusto, seguito dal proprio testo (`bands=2->3`, uscita diversa). Senza, no.
`State.md` registra la decisione di Milestone 37: *«L'interruzione del corridoio
non viene adottata come pre-registrata e il flag resta spento di default: la metà
filetti regge ma risolve un caso solo, la metà `embedded_visual` annienta»*.

IR 2 riceve l'ordine dalla base, che è senza interruzione, quindi eredita il
difetto. **Non l'ha introdotto.** La domanda aperta è se accendere la sola metà
filetti: cambierebbe l'ordine, quindi la base di E-B andrebbe rigenerata **e
rigiudicata**, non solo rigenerata.

## 5. Rinviato su decisione dell'utente

La cura degli spazi: *«mi piacerebbe fossero più curati, ma credo sia un problema
per un altro momento»*.

## 6. Cosa NON si fa da qui

Il §7 del criterio dice: *«L'esito si scrive, e nessun altro giro viene proposto
dall'interno di questo.»* L'esito è scritto. Le quattro strade che si aprono —
categoria stat block, glifi come marcatori, interruzione da filetti, glifi
separati in `column_band` — non vengono proposte qui.
